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

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

app = BedrockAgentCoreApp()

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

async def run_agent(prompt: str) -> AsyncIterator[str]:
    """
    Agent SDK を使ってプロンプトを実行し、テキストチャンクを yield する。

    戻り値は AsyncIterator[str] なので呼び出し側は:
        async for chunk in run_agent(prompt):
            print(chunk, end="", flush=True)
    のように使う。

    将来の BedrockAgentCoreApp 対応時もこの関数シグネチャは変えない。
    """
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY または CLAUDE_CODE_OAUTH_TOKEN が設定されていません。"
            "実行前に export ANTHROPIC_API_KEY=sk-ant-... または"
            " export CLAUDE_CODE_OAUTH_TOKEN=... を行ってください。"
        )

    system_prompt = _build_system_prompt()

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        cwd=str(WIKI_ROOT),
        permission_mode="bypassPermissions",  # コンテナ内ではファイル操作を自動承認
    )

    async def _generate() -> AsyncIterator[str]:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text
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

@app.entrypoint
async def agent_invocation(payload: dict, context) -> dict:
    """
    BedrockAgentCoreApp が受け取る HTTP ハンドラ。
    ペイロード形式: {"input": {"prompt": "..."}} または {"prompt": "..."}
    """
    input_data = payload.get("input", {})
    prompt = input_data.get("prompt", payload.get("prompt", ""))

    if not prompt:
        return {"output": {"error": "prompt が空です"}}

    stream = await run_agent(prompt)
    chunks: list[str] = []
    async for chunk in stream:
        chunks.append(chunk)

    return {"output": {"message": "".join(chunks)}}


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
