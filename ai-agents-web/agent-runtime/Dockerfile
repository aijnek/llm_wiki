# AI Agents Wiki — Agent Runtime
#
# ビルド: docker build -t ai-agents-web-runtime .
# 実行:   docker run --rm -e ANTHROPIC_API_KEY=sk-ant-... ai-agents-web-runtime "プロンプト"
#
# 将来は Bedrock AgentCore Runtime の BedrockAgentCoreApp ラッパーへ移行する前提。
# ENTRYPOINT / CMD はそのまま維持し、ラッパーのみ差し替える。

FROM python:3.13-slim

# --- システム依存 -----------------------------------------------------------
# git は claude-agent-sdk が内部で呼ぶ可能性があるため追加
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# --- uv のインストール -------------------------------------------------------
# /usr/local/bin に配置して全ユーザーから使えるようにする
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

# --- 非 root ユーザーの作成 --------------------------------------------------
# --dangerously-skip-permissions は root では動作しないため非 root が必須
RUN useradd -m -u 1000 appuser

# --- 作業ディレクトリ --------------------------------------------------------
WORKDIR /app
RUN chown appuser:appuser /app

USER appuser

# --- 依存インストール（レイヤーキャッシュ最適化）---------------------------
# pyproject.toml と uv.lock だけ先にコピーしてインストール
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# --- アプリケーションコード --------------------------------------------------
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser skills/ ./skills/

# --- 環境変数 ----------------------------------------------------------------
# ANTHROPIC_API_KEY は実行時に渡す（ハードコード禁止）
# WIKI_ROOT はコンテナ内の S3 Files BYO マウントポイントに合わせて上書き可能
ENV WIKI_ROOT=/mnt

# --- エントリポイント --------------------------------------------------------
ENTRYPOINT ["uv", "run", "python", "src/entrypoint.py"]
# デフォルト引数なし（引数は docker run ... "プロンプト" で渡す）
