from __future__ import annotations

import json
import logging
import os
import time
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
RUNTIME_ARN = os.environ.get("RUNTIME_ARN", "")
PROCESSOR_FUNCTION_NAME = os.environ.get("PROCESSOR_FUNCTION_NAME", "")
RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME", "")
SESSIONS_TABLE_NAME = os.environ.get("SESSIONS_TABLE_NAME", "")

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
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


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
