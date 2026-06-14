"""
AI Agents Wiki — Agent Runtime エントリポイント

Claude Agent SDK を使ってスキル定義を動かす最小実装。
将来 Bedrock AgentCore Runtime の BedrockAgentCoreApp ラッパーに置き換える前提で、
コアロジックを run_agent() に切り出している。
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import boto3

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    StreamEvent,
    TextBlock,
    query,
)

app = BedrockAgentCoreApp()


def _load_api_key_from_ssm() -> None:
    """ANTHROPIC_API_KEY_SSM_NAME が設定されている場合、SSM から API キーを取得して環境変数に設定する。
    sk-ant-oat01- で始まる OAuth トークンは CLAUDE_CODE_OAUTH_TOKEN に設定する。
    """
    ssm_name = os.environ.get("ANTHROPIC_API_KEY_SSM_NAME")
    if not ssm_name:
        return
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return
    region = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.get_parameter(Name=ssm_name, WithDecryption=True)
    value = resp["Parameter"]["Value"].strip()
    if value.startswith("sk-ant-oat"):
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = value
    else:
        os.environ["ANTHROPIC_API_KEY"] = value


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# このファイルの親ディレクトリ (agent-runtime/) を基準にパスを解決
_RUNTIME_ROOT = Path(__file__).parent.parent

# skills/ ディレクトリ: ingest.md / query.md / lint.md を格納
SKILLS_DIR = _RUNTIME_ROOT / "skills"

# wiki/ と raw/ はコンテナ実行時に S3 Files BYO でマウントされる想定。
# ローカル開発時はデフォルトとして agent-runtime/ の兄弟ディレクトリを参照する。
WIKI_ROOT = Path(os.environ.get("WIKI_ROOT", str(_RUNTIME_ROOT.parent.parent / "ai-agents")))

# ---------------------------------------------------------------------------
# システムプロンプトの組み立て
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    """
    skills/ 以下の Markdown ファイルをすべて読み込み、
    スキル定義を含むシステムプロンプトを組み立てる。

    スキルは Claude Code の slash command 相当の指示として埋め込む。
    """
    if not SKILLS_DIR.is_dir():
        raise FileNotFoundError(f"skills/ ディレクトリが見つかりません: {SKILLS_DIR}")

    skill_blocks: list[str] = []
    for md_file in sorted(SKILLS_DIR.glob("*.md")):
        skill_name = md_file.stem  # e.g. "ingest", "query", "lint"
        content = md_file.read_text(encoding="utf-8").strip()
        skill_blocks.append(f"## /{skill_name}\n\n{content}")

    if not skill_blocks:
        raise RuntimeError(f"skills/ にスキル定義 (*.md) が見つかりません: {SKILLS_DIR}")

    skills_section = "\n\n---\n\n".join(skill_blocks)

    return f"""\
あなたは AI Agents Wiki の管理エージェントです。
以下のスキル定義に従ってユーザーのリクエストを処理してください。

# スキル定義

{skills_section}

# 作業ディレクトリ
- wiki: {WIKI_ROOT}/wiki/
- raw:  {WIKI_ROOT}/raw/

すべての応答は日本語で行ってください。
英語の固有名詞（ReAct, Tool Use, GPT 等）はそのまま使ってください。
"""


# ---------------------------------------------------------------------------
# コアロジック: run_agent()
# ---------------------------------------------------------------------------

def _build_conversation_context(history: list[dict]) -> str:
    """会話履歴をプロンプト先頭に埋め込むテキストブロックを生成する。

    Args:
        history: [{"role": "user"|"assistant", "content": "..."}] の配列。

    Returns:
        「これまでの会話」ブロックのテキスト。履歴が空なら空文字列。
    """
    if not history:
        return ""
    lines = ["# これまでの会話", ""]
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            lines.append(f"ユーザー: {content}")
        elif role == "assistant":
            lines.append(f"アシスタント: {content}")
    lines.append("")
    return "\n".join(lines)


async def run_agent(
    prompt: str,
    history: list[dict] | None = None,
) -> AsyncIterator[str]:
    """
    Agent SDK を使ってプロンプトを実行し、テキストチャンクを yield する。

    Args:
        prompt: 今回のユーザー入力。
        history: 過去の会話ターン [{"role": "user"|"assistant", "content": "..."}]。
                 None または空リストの場合はシングルターンとして動作（CLI 後方互換）。

    戻り値は AsyncIterator[str] なので呼び出し側は:
        async for chunk in run_agent(prompt):
            print(chunk, end="", flush=True)
    のように使う。
    """
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY または CLAUDE_CODE_OAUTH_TOKEN が設定されていません。"
            "実行前に export ANTHROPIC_API_KEY=sk-ant-... または"
            " export CLAUDE_CODE_OAUTH_TOKEN=... を行ってください。"
        )

    system_prompt = _build_system_prompt()

    # 会話履歴があればプロンプト先頭に前置する（SDK 非依存のテキスト埋め込み方式）
    context = _build_conversation_context(history or [])
    full_prompt = f"{context}# 今回のリクエスト\n{prompt}" if context else prompt

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        cwd=str(WIKI_ROOT),
        permission_mode="bypassPermissions",  # コンテナ内ではファイル操作を自動承認
        include_partial_messages=True,  # トークン単位のストリーミングを有効化
    )

    async def _generate() -> AsyncIterator[str]:
        async for message in query(prompt=full_prompt, options=options):
            if isinstance(message, StreamEvent):
                # content_block_delta イベントからテキストを逐次 yield
                event = message.event
                if (
                    event.get("type") == "content_block_delta"
                    and event.get("delta", {}).get("type") == "text_delta"
                ):
                    text = event["delta"].get("text", "")
                    if text:
                        yield text
            elif isinstance(message, AssistantMessage):
                # StreamEvent で既にストリーミング済みのため内容はスキップ
                pass
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    error_detail = (message.errors or [])
                    raise RuntimeError(
                        f"エージェント実行エラー: {error_detail}"
                    )
                # ResultMessage はストリーム終端。コスト情報をデバッグ出力
                if message.total_cost_usd is not None:
                    print(
                        f"\n[debug] cost=${message.total_cost_usd:.4f} "
                        f"turns={message.num_turns}",
                        file=sys.stderr,
                    )

    return _generate()


# ---------------------------------------------------------------------------
# AgentCore Runtime エントリポイント（HTTP POST /invocations）
# ---------------------------------------------------------------------------

def _resolve_prompt(prompt: str) -> str:
    """スラッシュコマンド形式を自然言語の指示に変換する。

    claude_agent_sdk の query() はスラッシュコマンドを Claude Code の
    組み込みコマンドとして解釈しようとするため、自然言語に変換してから渡す。

    スラッシュコマンドでない通常の質問は /query として扱い、wiki 参照を明示する。
    """
    if not prompt.startswith("/"):
        # 通常の質問は wiki を参照してから答えるよう明示的に指示する
        return (
            f"wiki の内容をもとに次の質問に回答してください。"
            f"まず wiki/index.md を読んで関連ページを特定し、該当ページを読んでから回答してください。"
            f"wiki に情報がない場合は「wiki には記録がない」と明示してください。\n\n質問: {prompt}"
        )
    parts = prompt.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    if cmd == "/ingest":
        return f"raw/{args} を wiki に取り込んでください" if args else "raw/ 内の未処理ファイルを wiki に取り込んでください"
    if cmd == "/query":
        return args if args else "wiki の内容を教えてください"
    if cmd == "/lint":
        return "wiki のヘルスチェックを実行してください"
    return prompt


@app.entrypoint
async def agent_invocation(payload: dict, context):
    """
    BedrockAgentCoreApp が受け取る HTTP ハンドラ。
    ペイロード形式: {"input": {"prompt": "...", "history": [...]}} または {"prompt": "...", "history": [...]}

    async generator として yield することで BedrockAgentCoreApp が SSE ストリーミングで送出する。
    ProcessorFn が iter_lines() でチャンクを受け取り WebSocket に流すことで、
    アイドルタイマーがリセットされ続け WebSocket タイムアウトを回避できる。
    """
    _load_api_key_from_ssm()
    input_data = payload.get("input", {})
    prompt = input_data.get("prompt", payload.get("prompt", ""))
    # ProcessorFn が DynamoDB からロードした会話履歴を受け取る（未指定時は空＝シングルターン）
    history: list[dict] = input_data.get("history", payload.get("history", []))

    if not prompt:
        yield {"type": "error", "text": "prompt が空です"}
        return

    prompt = _resolve_prompt(prompt)
    stream = await run_agent(prompt, history=history)
    async for chunk in stream:
        yield {"type": "chunk", "text": chunk}


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------

async def _main() -> None:
    """
    標準入力またはコマンドライン引数からプロンプトを受け取り、
    ストリーミングで標準出力に応答を出力する。

    使い方:
        uv run python src/entrypoint.py "wikiにあるReActの情報を教えて"
        echo "wikiにあるReActの情報を教えて" | uv run python src/entrypoint.py
    """
    # 引数優先、なければ標準入力から読む
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    else:
        print("使い方: uv run python src/entrypoint.py <プロンプト>", file=sys.stderr)
        print("または: echo '<プロンプト>' | uv run python src/entrypoint.py", file=sys.stderr)
        sys.exit(1)

    if not prompt:
        print("エラー: プロンプトが空です。", file=sys.stderr)
        sys.exit(1)

    stream = await run_agent(prompt)
    async for chunk in stream:
        print(chunk, end="", flush=True)

    # 最終改行
    print()


def main() -> None:
    """同期ラッパー（ENTRYPOINT から呼ばれる）。"""
    asyncio.run(_main())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 引数あり → CLI モード（後方互換）
        main()
    else:
        # 引数なし → HTTP サーバーモード（AgentCore Runtime / ローカル疎通テスト）
        app.run()
