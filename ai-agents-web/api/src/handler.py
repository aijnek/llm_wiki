from __future__ import annotations

import base64
import decimal
import json
import logging
import os
import re
import time
import uuid
from urllib.parse import unquote_plus

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
RUNTIME_ARN = os.environ.get("RUNTIME_ARN", "")
PROCESSOR_FUNCTION_NAME = os.environ.get("PROCESSOR_FUNCTION_NAME", "")
RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME", "")
SESSIONS_TABLE_NAME = os.environ.get("SESSIONS_TABLE_NAME", "")
WIKI_BUCKET_NAME = os.environ.get("WIKI_BUCKET_NAME", "")
WIKI_INDEX_TABLE_NAME = os.environ.get("WIKI_INDEX_TABLE_NAME", "")

# 会話履歴の TTL: 7日
HISTORY_TTL_SECONDS = 7 * 24 * 60 * 60
# 送信する履歴の上限メッセージ数（user+assistant で 1 ターン = 2 件）
MAX_HISTORY_MESSAGES = 20


def websocket_handler(event, context):
    """API Gateway WebSocket handler — $connect / $disconnect / $default."""
    route_key = event["requestContext"]["routeKey"]

    if route_key in ("$connect", "$disconnect"):
        return {"statusCode": 200}

    # $default: parse prompt, dispatch processing asynchronously
    connection_id = event["requestContext"]["connectionId"]
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]

    try:
        body = json.loads(event.get("body") or "{}")
        prompt = body.get("prompt", "").strip()
        # フロントエンドが発番したセッション ID。未指定時はフォールバックで新規生成（後方互換）
        session_id = body.get("sessionId", "").strip() or str(uuid.uuid4())
    except (json.JSONDecodeError, AttributeError):
        prompt = ""
        session_id = str(uuid.uuid4())

    if not prompt:
        _post(connection_id, domain, stage, {"type": "error", "message": "prompt is required"})
        return {"statusCode": 400}

    boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=PROCESSOR_FUNCTION_NAME,
        InvocationType="Event",  # async — returns immediately, avoids 29s API GW limit
        Payload=json.dumps({
            "connectionId": connection_id,
            "domainName": domain,
            "stage": stage,
            "prompt": prompt,
            "sessionId": session_id,
        }).encode("utf-8"),
    )

    return {"statusCode": 200}


def processor_handler(event, context):
    """Async processor — invoke AgentCore Runtime, post result back via WebSocket."""
    connection_id = event["connectionId"]
    domain = event["domainName"]
    stage = event["stage"]
    prompt = event["prompt"]
    # フロントエンドが発番したセッション ID を引き継ぐ（未指定時はフォールバック）
    session_id = event.get("sessionId") or str(uuid.uuid4())

    logger.info("START connection_id=%s prompt=%r session_id=%s", connection_id, prompt, session_id)

    try:
        # ① DynamoDB から会話履歴をロード
        history = _load_history(session_id)
        logger.info("history loaded: %d messages", len(history))

        runtime_client = boto3.client(
            "bedrock-agentcore",
            region_name=REGION,
            config=Config(read_timeout=800, connect_timeout=10),  # ストリーミング中のツール実行を考慮して延長
        )
        logger.info("invoking AgentCore Runtime arn=%s", RUNTIME_ARN)
        # ② 履歴を payload に含めて Runtime へ invoke
        response = runtime_client.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps({"prompt": prompt, "history": history}).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )

        # SSE ストリームを逐次読み込んでチャンクごとに WebSocket へ転送する。
        # これにより WebSocket のアイドルタイムアウト（10分）を継続リセットできる。
        # ③ チャンクを WS 転送しつつ assistant 応答を蓄積する
        chunk_count = 0
        full_response_parts: list[str] = []
        for line in response["response"].iter_lines():
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data: "):
                continue
            try:
                data = json.loads(line_str[6:])
            except json.JSONDecodeError:
                continue
            if data.get("type") == "chunk" and data.get("text"):
                text = data["text"]
                _post(connection_id, domain, stage, {"type": "message", "content": text})
                full_response_parts.append(text)
                chunk_count += 1
        logger.info("streaming done: %d chunks posted", chunk_count)
        _post(connection_id, domain, stage, {"type": "done"})
        logger.info("DONE")

        # ④ 正常終了後に user/assistant ターンを DynamoDB へ保存
        full_response = "".join(full_response_parts)
        if full_response:
            _save_history(session_id, prompt, full_response, history)
        else:
            logger.warning("empty response, skipping history save")

    except Exception as e:
        logger.error("ERROR: %r", e)
        try:
            _post(connection_id, domain, stage, {"type": "error", "message": str(e)})
        except Exception as post_err:
            logger.error("failed to post error: %r", post_err)


def get_session_handler(event, context):
    """HTTP API handler — GET /sessions/{sessionId}"""
    try:
        path_params = event.get("pathParameters") or {}
        session_id = (path_params.get("sessionId") or "").strip()
    except Exception:
        session_id = ""

    if not session_id:
        return _http_response(400, {"error": "sessionId is required"})

    messages = _load_history(session_id)
    return _http_response(200, {"messages": messages})


def presign_handler(event, context):
    """HTTP API handler — POST /presign-upload"""
    try:
        body = json.loads(event.get("body") or "{}")
        filename = body.get("filename", "").strip()
        content_type = body.get("content_type", "application/octet-stream").strip()
    except (json.JSONDecodeError, AttributeError):
        return _http_response(400, {"error": "invalid JSON"})

    if not filename or "/" in filename or "\\" in filename or filename.startswith("."):
        return _http_response(400, {"error": "invalid filename"})

    s3 = boto3.client("s3", region_name=REGION)
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": RAW_BUCKET_NAME,
            "Key": filename,
            "ContentType": content_type,
        },
        ExpiresIn=900,
    )
    return _http_response(200, {"url": url})


def _load_history(session_id: str) -> list[dict]:
    """DynamoDB からセッションの会話履歴をロードする。テーブル未設定時や項目不在時は空リスト。"""
    if not SESSIONS_TABLE_NAME:
        return []
    try:
        ddb = boto3.resource("dynamodb", region_name=REGION)
        table = ddb.Table(SESSIONS_TABLE_NAME)
        resp = table.get_item(Key={"sessionId": session_id})
        messages = resp.get("Item", {}).get("messages", [])
        # 直近 MAX_HISTORY_MESSAGES 件に絞って送信サイズを抑制
        return messages[-MAX_HISTORY_MESSAGES:]
    except Exception as e:
        logger.warning("failed to load history session_id=%s: %r", session_id, e)
        return []


def _save_history(
    session_id: str,
    user_prompt: str,
    assistant_response: str,
    prior_messages: list[dict],
) -> None:
    """会話ターンを DynamoDB へ保存する。保存失敗は警告ログのみで握りつぶす（レスポンスへの影響を避けるため）。"""
    if not SESSIONS_TABLE_NAME:
        return
    try:
        messages = list(prior_messages) + [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response},
        ]
        # 上限超過分は古い方から削除
        messages = messages[-MAX_HISTORY_MESSAGES:]

        ddb = boto3.resource("dynamodb", region_name=REGION)
        table = ddb.Table(SESSIONS_TABLE_NAME)
        table.put_item(Item={
            "sessionId": session_id,
            "messages": messages,
            "updatedAt": int(time.time()),
            "ttl": int(time.time()) + HISTORY_TTL_SECONDS,
        })
        logger.info("history saved session_id=%s messages=%d", session_id, len(messages))
    except Exception as e:
        logger.warning("failed to save history session_id=%s: %r", session_id, e)


def _http_response(status: int, body: dict) -> dict:
    def _default(obj: object) -> object:
        if isinstance(obj, decimal.Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False, default=_default),
    }


# ============================================================
# Wiki Index ハンドラ群
# ============================================================

# --- パース・変換ユーティリティ ---

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """YAML frontmatter を簡易パースして (dict, body) を返す。
    管理された単純構造（文字列・リスト値のみ）を前提とし、外部依存なしで処理する。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    fm: dict[str, object] = {}
    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            # インライン配列: [foo, bar, baz]
            fm[k] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        else:
            fm[k] = v.strip("\"'")
    return fm, body


def _extract_wikilinks(body: str) -> list[tuple[str, str | None]]:
    """[[target]] と [[target|label]] を抽出して (target, label_or_None) のリストを返す。"""
    return [
        (m.group(1).strip(), m.group(2).strip() if m.group(2) else None)
        for m in re.finditer(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", body)
    ]


def _slugify_key(key: str) -> str:
    """S3 オブジェクトキーを slug へ変換（.md 拡張子除去）。"""
    return key[:-3] if key.endswith(".md") else key


def _folder_of(slug: str) -> str:
    """slug のフォルダ部分を返す。トップレベルは 'root'。"""
    return slug.split("/")[0] if "/" in slug else "root"


def _basename_of(slug: str) -> str:
    return slug.split("/")[-1]


def _is_excluded(key: str) -> bool:
    """インデックス対象外キーの判定。"""
    return (
        key.startswith(".obsidian/")
        or key == "log.md"
        or not key.endswith(".md")
    )


def _read_s3_text(bucket: str, key: str) -> str | None:
    """S3 オブジェクトをテキストで取得。失敗時は None。"""
    try:
        resp = boto3.client("s3", region_name=REGION).get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8")
    except Exception as e:
        logger.warning("s3 get_object failed bucket=%s key=%s: %r", bucket, key, e)
        return None


def _validate_wiki_slug(slug: str) -> bool:
    """パストラバーサルや不正 slug を弾く。"""
    return bool(slug) and ".." not in slug and not slug.startswith("/") and not slug.startswith(".")


def _encode_cursor(lek: dict) -> str:
    return base64.b64encode(json.dumps(lek, ensure_ascii=False).encode()).decode()


def _decode_cursor(cursor: str) -> dict | None:
    try:
        return json.loads(base64.b64decode(cursor.encode()).decode())
    except Exception:
        return None


def _get_wiki_table():
    return boto3.resource("dynamodb", region_name=REGION).Table(WIKI_INDEX_TABLE_NAME)


def _facet_increment(tbl, sk: str, delta: int) -> None:
    """FACET カウンタを atomic ADD で増減する。"""
    try:
        tbl.update_item(
            Key={"PK": "FACET", "SK": sk},
            UpdateExpression="ADD #cnt :delta",
            ExpressionAttributeNames={"#cnt": "count"},
            ExpressionAttributeValues={":delta": delta},
        )
    except Exception as e:
        logger.warning("facet update failed sk=%s delta=%d: %r", sk, delta, e)


def _resolve_bare_link_ddb(basename: str, tbl) -> str | None:
    """bare wikilink（パス区切りなし）を DDB の NAME# レコードで slug へ解決する。"""
    try:
        resp = tbl.get_item(Key={"PK": f"NAME#{basename}", "SK": "RESOLVE"})
        item = resp.get("Item")
        return str(item["slug"]) if item else None
    except Exception as e:
        logger.warning("bare link resolution failed basename=%s: %r", basename, e)
        return None


def _build_link_map(
    raw_links: list[tuple[str, str | None]],
    tbl,
    name_to_slug: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """wikilink リストからリンクマップと解決済み slug リストを構築する。
    name_to_slug が渡された場合は DDB 参照不要（reindex 時のインメモリ解決）。"""
    link_map: dict[str, str] = {}
    resolved_slugs: list[str] = []
    seen: set[str] = set()
    for raw_target, _ in raw_links:
        if raw_target in seen:
            continue
        seen.add(raw_target)
        if "/" in raw_target:
            # パス形式 → slug はそのまま（存在検証なし）
            slug_resolved = raw_target
        elif name_to_slug is not None:
            slug_resolved = name_to_slug.get(_basename_of(raw_target), "")
        else:
            slug_resolved = _resolve_bare_link_ddb(raw_target, tbl) or ""
        link_map[raw_target] = slug_resolved
        if slug_resolved:
            resolved_slugs.append(slug_resolved)
    return link_map, resolved_slugs


# --- インデックス書き込みコア ---

def _index_page_impl(
    slug: str,
    fm: dict,
    body: str,
    tbl,
    name_to_slug: dict[str, str] | None = None,
) -> None:
    """1ページ分の DDB インデックスを構築する（upsert＋差分更新）。"""
    title = str(fm.get("title") or _basename_of(slug))
    page_type = str(fm.get("type") or "")
    entity_type = str(fm.get("entity_type") or fm.get("entityType") or "")
    tags_raw = fm.get("tags") or []
    if isinstance(tags_raw, str):
        tags_raw = [t.strip() for t in tags_raw.split(",") if t.strip()]
    tags: list[str] = [str(t) for t in tags_raw]

    folder = _folder_of(slug)
    basename = _basename_of(slug)

    raw_links = _extract_wikilinks(body)
    link_map, resolved_slugs = _build_link_map(raw_links, tbl, name_to_slug)

    # 既存 META を読んで差分用データを取得
    try:
        old_resp = tbl.get_item(Key={"PK": f"PAGE#{slug}", "SK": "META"})
        old_item = old_resp.get("Item") or {}
    except Exception:
        old_item = {}

    old_tags: set[str] = set(old_item.get("tags") or [])
    old_out_slugs: set[str] = set(old_item.get("outLinkSlugs") or [])
    old_title: str = str(old_item.get("title") or "")
    new_tags: set[str] = set(tags)
    new_out_slugs: set[str] = set(resolved_slugs)
    is_new_page = not old_item

    now = int(time.time())

    # 1. PAGE META をアップサート
    tbl.put_item(Item={
        "PK": f"PAGE#{slug}",
        "SK": "META",
        "slug": slug,
        "title": title,
        "type": page_type,
        "entityType": entity_type,
        "tags": tags,
        "folder": folder,
        "linkMap": link_map,
        "outLinkSlugs": list(new_out_slugs),
        "updatedAt": now,
    })

    # 2. FOLDER ポインタ（タイトルが変わった場合は古い SK を削除）
    new_folder_sk = f"{title}#{slug}"
    if old_title and old_title != title:
        old_folder_sk = f"{old_title}#{slug}"
        try:
            tbl.delete_item(Key={"PK": f"FOLDER#{folder}", "SK": old_folder_sk})
        except Exception:
            pass
    tbl.put_item(Item={
        "PK": f"FOLDER#{folder}",
        "SK": new_folder_sk,
        "slug": slug,
        "title": title,
        "type": page_type,
    })

    # 3. NAME 解決レコード
    tbl.put_item(Item={
        "PK": f"NAME#{basename}",
        "SK": "RESOLVE",
        "slug": slug,
    })

    # 4. FACET — フォルダは新規ページ時のみ +1
    if is_new_page:
        _facet_increment(tbl, f"FOLDER#{folder}", 1)

    # 5. TAG ポインタ差分
    for tag in new_tags - old_tags:
        tbl.put_item(Item={
            "PK": f"TAG#{tag}",
            "SK": slug,
            "slug": slug,
            "title": title,
            "type": page_type,
        })
        _facet_increment(tbl, f"TAG#{tag}", 1)
    for tag in old_tags - new_tags:
        tbl.delete_item(Key={"PK": f"TAG#{tag}", "SK": slug})
        _facet_increment(tbl, f"TAG#{tag}", -1)

    # 6. BACKLINK 逆エッジ差分
    for target_slug in new_out_slugs - old_out_slugs:
        tbl.put_item(Item={
            "PK": f"BACKLINK#{target_slug}",
            "SK": slug,
            "sourceSlug": slug,
            "sourceTitle": title,
        })
    for target_slug in old_out_slugs - new_out_slugs:
        tbl.delete_item(Key={"PK": f"BACKLINK#{target_slug}", "SK": slug})

    logger.info("indexed slug=%s tags=%s outLinks=%d", slug, tags, len(new_out_slugs))


def _delete_page_ddb(slug: str, tbl) -> None:
    """削除されたページの DDB インデックスをすべて後始末する。"""
    try:
        old_resp = tbl.get_item(Key={"PK": f"PAGE#{slug}", "SK": "META"})
        old_item = old_resp.get("Item") or {}
    except Exception:
        return

    if not old_item:
        return

    folder = str(old_item.get("folder") or _folder_of(slug))
    title = str(old_item.get("title") or _basename_of(slug))
    old_tags: list[str] = list(old_item.get("tags") or [])
    old_out_slugs: list[str] = list(old_item.get("outLinkSlugs") or [])
    basename = _basename_of(slug)

    # PAGE META 削除
    tbl.delete_item(Key={"PK": f"PAGE#{slug}", "SK": "META"})
    # FOLDER ポインタ削除
    tbl.delete_item(Key={"PK": f"FOLDER#{folder}", "SK": f"{title}#{slug}"})
    _facet_increment(tbl, f"FOLDER#{folder}", -1)
    # NAME 解決レコード削除（このページが主体の場合のみ）
    try:
        name_resp = tbl.get_item(Key={"PK": f"NAME#{basename}", "SK": "RESOLVE"})
        name_item = name_resp.get("Item") or {}
        if str(name_item.get("slug", "")) == slug:
            tbl.delete_item(Key={"PK": f"NAME#{basename}", "SK": "RESOLVE"})
    except Exception:
        pass
    # TAG ポインタ削除
    for tag in old_tags:
        tbl.delete_item(Key={"PK": f"TAG#{tag}", "SK": slug})
        _facet_increment(tbl, f"TAG#{tag}", -1)
    # BACKLINK 逆エッジ削除
    for target_slug in old_out_slugs:
        tbl.delete_item(Key={"PK": f"BACKLINK#{target_slug}", "SK": slug})

    logger.info("deleted index slug=%s", slug)


# --- 公開ハンドラ ---

def index_object_handler(event, context):
    """S3 イベント駆動 Indexer — ObjectCreated / ObjectRemoved で差分更新する。"""
    if not WIKI_BUCKET_NAME or not WIKI_INDEX_TABLE_NAME:
        logger.warning("wiki env not configured, skipping")
        return

    tbl = _get_wiki_table()

    for record in event.get("Records", []):
        event_name: str = record.get("eventName", "")
        key = unquote_plus(record["s3"]["object"]["key"])
        logger.info("s3 event eventName=%s key=%s", event_name, key)

        if _is_excluded(key):
            logger.info("excluded key=%s", key)
            continue

        slug = _slugify_key(key)

        if event_name.startswith("ObjectRemoved"):
            _delete_page_ddb(slug, tbl)
        else:
            # ObjectCreated:* (Put / Copy / CompleteMultipartUpload)
            text = _read_s3_text(WIKI_BUCKET_NAME, key)
            if text is None:
                logger.warning("could not read s3 key=%s", key)
                continue
            fm, body = _parse_frontmatter(text)
            _index_page_impl(slug, fm, body, tbl)


def reindex_handler(event, context):
    """全件再構築 — aws lambda invoke で手動実行する。
    S3 の全 .md を走査し、インメモリ name_to_slug マップで bare リンクを解決する。
    既存インデックスは upsert で上書き（削除済みページの stale エントリは残る）。"""
    if not WIKI_BUCKET_NAME or not WIKI_INDEX_TABLE_NAME:
        logger.warning("wiki env not configured, skipping")
        return {"error": "wiki env not configured"}

    s3 = boto3.client("s3", region_name=REGION)
    tbl = _get_wiki_table()

    # --- ステップ 1: 全 .md キーを収集 ---
    all_keys: list[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=WIKI_BUCKET_NAME):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not _is_excluded(key):
                all_keys.append(key)
    logger.info("reindex: found %d .md files", len(all_keys))

    # --- ステップ 2: frontmatter だけ読んで name_to_slug マップを構築 ---
    page_data: dict[str, tuple[dict, str]] = {}  # key → (fm, body)
    name_to_slug: dict[str, str] = {}

    for key in all_keys:
        text = _read_s3_text(WIKI_BUCKET_NAME, key)
        if text is None:
            continue
        slug = _slugify_key(key)
        fm, body = _parse_frontmatter(text)
        page_data[key] = (fm, body)
        basename = _basename_of(slug)
        if basename in name_to_slug:
            logger.warning("basename conflict: %s → %s (previously %s)", basename, slug, name_to_slug[basename])
        name_to_slug[basename] = slug

    # --- ステップ 3: 全ページをインデックス（インメモリ解決を使用） ---
    for key, (fm, body) in page_data.items():
        slug = _slugify_key(key)
        try:
            _index_page_impl(slug, fm, body, tbl, name_to_slug=name_to_slug)
        except Exception as e:
            logger.error("reindex failed slug=%s: %r", slug, e)

    result = {"indexed": len(page_data)}
    logger.info("reindex complete: %s", result)
    return result


# --- Wiki 読み取りハンドラ ---

def wiki_read_handler(event, context):
    """HTTP API handler — /wiki/* 読み取りエンドポイント群をまとめて処理する。"""
    if not WIKI_INDEX_TABLE_NAME:
        return _http_response(503, {"error": "wiki index not configured"})

    raw_path: str = event.get("rawPath") or event.get("path") or ""
    qs: dict[str, str] = event.get("queryStringParameters") or {}
    path_params: dict[str, str] = event.get("pathParameters") or {}

    tbl = _get_wiki_table()

    if raw_path == "/wiki/facets":
        return _wiki_facets(tbl)
    elif raw_path == "/wiki/pages":
        return _wiki_pages(qs, tbl)
    elif raw_path.startswith("/wiki/page/"):
        slug = path_params.get("proxy") or raw_path[len("/wiki/page/"):]
        return _wiki_page(slug, tbl)
    elif raw_path.startswith("/wiki/backlinks/"):
        slug = path_params.get("proxy") or raw_path[len("/wiki/backlinks/"):]
        cursor = qs.get("cursor")
        return _wiki_backlinks(slug, cursor, tbl)
    else:
        return _http_response(404, {"error": "not found"})


def _wiki_facets(tbl) -> dict:
    """GET /wiki/facets → { folders:[str], tags:[{tag, count}] }"""
    try:
        resp = tbl.query(KeyConditionExpression=Key("PK").eq("FACET"))
    except Exception as e:
        logger.error("facets query failed: %r", e)
        return _http_response(500, {"error": str(e)})

    folders: list[str] = []
    tags: list[dict] = []
    folder_order = ["concepts", "entities", "sources", "root"]

    for item in resp.get("Items", []):
        sk: str = str(item.get("SK", ""))
        count = int(item.get("count", 0))
        if count <= 0:
            continue
        if sk.startswith("FOLDER#"):
            folders.append(sk[len("FOLDER#"):])
        elif sk.startswith("TAG#"):
            tags.append({"tag": sk[len("TAG#"):], "count": count})

    # フォルダを既定順にソート（未知フォルダはアルファベット順で末尾に）
    folders.sort(key=lambda f: (folder_order.index(f) if f in folder_order else len(folder_order), f))
    tags.sort(key=lambda t: (-t["count"], t["tag"]))

    return _http_response(200, {"folders": folders, "tags": tags})


def _wiki_pages(qs: dict[str, str], tbl) -> dict:
    """GET /wiki/pages?folder=<f>|tag=<t>&cursor=<c>&limit=<n>
    フォルダ別またはタグ別のページポインタをページネーション付きで返す。"""
    folder = qs.get("folder", "").strip()
    tag = qs.get("tag", "").strip()
    cursor_str = qs.get("cursor", "")
    limit = min(int(qs.get("limit", "30")), 100)

    if not folder and not tag:
        return _http_response(400, {"error": "folder or tag is required"})

    pk = f"FOLDER#{folder}" if folder else f"TAG#{tag}"
    lek = _decode_cursor(cursor_str) if cursor_str else None

    try:
        kwargs: dict = {
            "KeyConditionExpression": Key("PK").eq(pk),
            "Limit": limit,
        }
        if lek:
            kwargs["ExclusiveStartKey"] = lek
        resp = tbl.query(**kwargs)
    except Exception as e:
        logger.error("pages query failed pk=%s: %r", pk, e)
        return _http_response(500, {"error": str(e)})

    pages = [
        {
            "slug": str(item.get("slug", "")),
            "title": str(item.get("title", "")),
            "type": str(item.get("type", "")),
            "folder": _folder_of(str(item.get("slug", ""))),
        }
        for item in resp.get("Items", [])
        if item.get("slug")
    ]
    next_lek = resp.get("LastEvaluatedKey")
    next_cursor = _encode_cursor(next_lek) if next_lek else None

    return _http_response(200, {"pages": pages, "cursor": next_cursor})


def _wiki_page(slug: str, tbl) -> dict:
    """GET /wiki/page/{slug+} → { slug, frontmatter, markdown, linkMap }"""
    if not _validate_wiki_slug(slug):
        return _http_response(400, {"error": "invalid slug"})

    # DDB からメタ取得
    try:
        meta_resp = tbl.get_item(Key={"PK": f"PAGE#{slug}", "SK": "META"})
        meta = meta_resp.get("Item")
    except Exception as e:
        logger.error("meta get_item failed slug=%s: %r", slug, e)
        return _http_response(500, {"error": str(e)})

    if not meta:
        return _http_response(404, {"error": f"page not found: {slug}"})

    # S3 から本文取得
    key = slug + ".md"
    markdown = _read_s3_text(WIKI_BUCKET_NAME, key)
    if markdown is None:
        return _http_response(404, {"error": f"page content not found: {slug}"})

    # frontmatter を本文から分離（S3 本文はそのまま含む）
    fm, body = _parse_frontmatter(markdown)

    return _http_response(200, {
        "slug": str(meta.get("slug", slug)),
        "frontmatter": {
            "title": str(meta.get("title", "")),
            "type": str(meta.get("type", "")),
            "entityType": str(meta.get("entityType", "")),
            "tags": list(meta.get("tags") or []),
        },
        "markdown": body,
        "linkMap": dict(meta.get("linkMap") or {}),
    })


def _wiki_backlinks(slug: str, cursor_str: str | None, tbl) -> dict:
    """GET /wiki/backlinks/{slug+}?cursor=<c> → { backlinks:[{sourceSlug, sourceTitle}], cursor }"""
    if not _validate_wiki_slug(slug):
        return _http_response(400, {"error": "invalid slug"})

    lek = _decode_cursor(cursor_str) if cursor_str else None
    limit = 30

    try:
        kwargs: dict = {
            "KeyConditionExpression": Key("PK").eq(f"BACKLINK#{slug}"),
            "Limit": limit,
        }
        if lek:
            kwargs["ExclusiveStartKey"] = lek
        resp = tbl.query(**kwargs)
    except Exception as e:
        logger.error("backlinks query failed slug=%s: %r", slug, e)
        return _http_response(500, {"error": str(e)})

    backlinks = [
        {
            "sourceSlug": str(item.get("sourceSlug", "")),
            "sourceTitle": str(item.get("sourceTitle", "")),
        }
        for item in resp.get("Items", [])
    ]
    next_lek = resp.get("LastEvaluatedKey")
    next_cursor = _encode_cursor(next_lek) if next_lek else None

    return _http_response(200, {"backlinks": backlinks, "cursor": next_cursor})


def _post(connection_id: str, domain: str, stage: str, data: dict) -> None:
    try:
        boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=f"https://{domain}/{stage}",
            region_name=REGION,
        ).post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "GoneException":
            logger.warning("WebSocket connection gone connection_id=%s", connection_id)
        else:
            raise
