# AI Agents Web

LLM Wikiのウェブサービス版。ローカルの `../ai-agents/` を完全に温存したまま、同じスキル定義をAWS上のBedrock AgentCore Runtime で動かす。

## アーキテクチャ概要

```
[Next.js (Amplify)] → [API Gateway] → [Lambda: orchestrator]
                                              │
                                   [Bedrock AgentCore Runtime]
                                   ・microVM per session
                                   ・Agent SDK (Python)
                                   ・/mnt/wiki → S3 Files BYO
                                   ・/mnt/raw  → S3 Files BYO
```

詳細設計: `/Users/aijnek/.claude/plans/local-llm-wiki-web-aws-claude-agent-sdk-melodic-mochi.md`

## ディレクトリ構成

```
ai-agents-web/
├── README.md              ← このファイル
├── infra/                 ← AWS CDK（第2フェーズ）
├── agent-runtime/
│   ├── Dockerfile
│   ├── pyproject.toml     ← uv管理
│   ├── src/
│   │   └── entrypoint.py  ← Agent SDK エントリポイント
│   └── skills/            ← sync-skills.sh でコピーされたスキル定義
├── api/                   ← Lambda / API Gateway（第2フェーズ）
├── frontend/              ← Next.js（第3フェーズ）
└── scripts/
    └── sync-skills.sh     ← ローカルスキル定義を skills/ へ同期
```

## ローカル開発手順

### 前提条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) インストール済み
- Docker インストール済み
- `ANTHROPIC_API_KEY` 環境変数を設定すること

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### セットアップ

```bash
# 1. スキル定義を同期（ローカルの ai-agents/.claude/commands/ からコピー）
./scripts/sync-skills.sh

# 2. 依存インストール
cd agent-runtime
uv sync

# 3. ローカル疎通テスト（ANTHROPIC_API_KEY 必須）
# 引数でプロンプトを渡す
uv run python src/entrypoint.py "wikiにあるReActの情報を教えて"
# 標準入力からプロンプトを渡す
echo "ReActとは何か" | uv run python src/entrypoint.py

# WIKI_ROOT を明示する場合（デフォルトは ../ai-agents/）
WIKI_ROOT=/path/to/wiki uv run python src/entrypoint.py "質問"
```

### Docker ビルド・実行

```bash
cd agent-runtime
docker build -t ai-agents-web-runtime .

# コンテナ実行（ANTHROPIC_API_KEY を渡す場合）
# -v で ai-agents/ ディレクトリをコンテナの /mnt にマウントする（必須）
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v "$(pwd)/../../ai-agents:/mnt" \
  ai-agents-web-runtime "ReActとは何か"

# コンテナ実行（CLAUDE_CODE_OAUTH_TOKEN を渡す場合）
# Claude.ai の認証トークンを使って AgentCore Runtime を動かす方法。
# トークンは `claude /oauth-token` または ~/.claude/.credentials.json から取得できる。
docker run --rm \
  -e CLAUDE_CODE_OAUTH_TOKEN="$(cat ~/.claude/.credentials.json | python3 -c 'import sys,json; print(json.load(sys.stdin)["claudeAiOauth"]["accessToken"])')" \
  -v "$(pwd)/../../ai-agents:/mnt" \
  ai-agents-web-runtime "ReActとは何か"

# 環境変数をファイルで管理する場合（.env は .gitignore に追加すること）
# .env の例:
#   CLAUDE_CODE_OAUTH_TOKEN=eyJ...
docker run --rm \
  --env-file .env \
  -v "$(pwd)/../../ai-agents:/mnt" \
  ai-agents-web-runtime "ReActとは何か"
```

> **認証方式の優先順位**  
> `ANTHROPIC_API_KEY` と `CLAUDE_CODE_OAUTH_TOKEN` はどちらか一方を設定すれば動作する。  
> 両方設定した場合、Claude Agent SDK は `ANTHROPIC_API_KEY` を優先して使用する。

### スキルの更新

`../ai-agents/.claude/commands/` でスキル定義を更新した後:

```bash
./scripts/sync-skills.sh
```

その後 Docker イメージを再ビルドすること。

## フェーズ別作業

| フェーズ | 内容 | ディレクトリ |
|---|---|---|
| 1 (完了) | scaffold + agent-runtime ローカル検証 | agent-runtime/ |
| 1.5 (完了) | BedrockAgentCoreApp ラッパー導入・ローカル HTTP 疎通確認 | agent-runtime/ |
| 2 (完了) | AWS CDK infra — VPC / S3 / ECR / IAM | infra/ |
| 2.5 (完了) | AgentCore Runtime CDK 定義・S3 Files BYO・ECR push スクリプト | infra/ |
| 2.6 | cdk deploy・S3 初回 sync・AWS 上での疎通確認 | infra/ |
| 3 | API Lambda + WebSocket | api/ |
| 4 | Next.js Frontend | frontend/ |

## infra/ — CDK (Python / uv)

```
infra/
├── app.py              ← CDK アプリエントリポイント
├── cdk.json            ← "app": "uv run python app.py"
├── pyproject.toml      ← uv 管理
└── stacks/
    ├── wiki_infra_stack.py   ← VPC / S3 / ECR / IAM（WikiInfraStack）
    └── wiki_runtime_stack.py ← AgentCore Runtime（WikiRuntimeStack）
```

### フルデプロイ（Phase 2.6）

ECR repo 作成 → Docker push → Runtime 定義の順序依存を解決するため、`deploy.sh` で一括実行する。

```bash
# 初回のみ: CDK bootstrap
cd infra
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 \
  uv run cdk bootstrap

# フルデプロイ（infra → ECR push → runtime の順）
./scripts/deploy.sh
```

### 個別デプロイ

```bash
cd infra
uv sync

# Step 1: インフラ（ECR リポジトリ等）
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 \
  uv run cdk deploy WikiInfraStack --require-approval never

# Step 2: Docker イメージをビルドして ECR へ push
./scripts/ecr_push.sh

# Step 3: AgentCore Runtime
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 \
  uv run cdk deploy WikiRuntimeStack --require-approval never
```

### 生成されるリソース

| スタック | リソース | 説明 |
|---|---|---|
| WikiInfraStack | VPC (10.0.0.0/16) | 2 AZ × private isolated subnet。NAT なし |
| WikiInfraStack | S3 VPC Gateway Endpoint | VPC → S3 を無料・プライベート経路で接続 |
| WikiInfraStack | S3: WikiBucket | wiki/ 永続化。versioning 有効 |
| WikiInfraStack | S3: RawBucket | raw/ 原本。versioning 有効 |
| WikiInfraStack | ECR: ai-agents-wiki-runtime | agent-runtime Docker イメージ置き場 |
| WikiInfraStack | IAM Role: AgentCoreRole | AgentCore Runtime 実行ロール（S3 RW + ECR pull）|
| WikiRuntimeStack | AgentCore Runtime | BedrockAgentCore Runtime（コンテナベース）|

> **ネットワーク補足**: Runtime は private isolated subnet に配置されるため、Anthropic API（外部）への outbound に NAT Gateway が必要。
> NAT Gateway を追加する場合は `wiki_infra_stack.py` の `nat_gateways=0` → `1` に変更（約 $32/月）。

## 既存 ai-agents/ との関係

- `../ai-agents/` は**一切変更しない**
- ローカル版 Claude Code スキル (`/ingest`, `/query`, `/lint`) はローカルで従来通り動く
- Web版はスキル定義のコピーを持ち、AgentCore Runtime 上で独立して動作する
