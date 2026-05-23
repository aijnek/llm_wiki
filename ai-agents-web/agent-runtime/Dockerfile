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
# 公式インストールスクリプト経由で最新版を取得
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# --- 作業ディレクトリ --------------------------------------------------------
WORKDIR /app

# --- 依存インストール（レイヤーキャッシュ最適化）---------------------------
# pyproject.toml と uv.lock だけ先にコピーしてインストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# --- アプリケーションコード --------------------------------------------------
COPY src/ ./src/
COPY skills/ ./skills/

# --- 環境変数 ----------------------------------------------------------------
# ANTHROPIC_API_KEY は実行時に渡す（ハードコード禁止）
# WIKI_ROOT はコンテナ内の S3 Files BYO マウントポイントに合わせて上書き可能
ENV WIKI_ROOT=/mnt

# --- エントリポイント --------------------------------------------------------
ENTRYPOINT ["uv", "run", "python", "src/entrypoint.py"]
# デフォルト引数なし（引数は docker run ... "プロンプト" で渡す）
