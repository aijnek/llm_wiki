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
| 2.5 | AgentCore Runtime 定義 + ECR push + cdk deploy | infra/ |
| 3 | API Lambda + WebSocket | api/ |
| 4 | Next.js Frontend | frontend/ |

## infra/ — CDK (Python / uv)

```
infra/
├── app.py              ← CDK アプリエントリポイント
├── cdk.json            ← "app": "uv run python app.py"
├── pyproject.toml      ← uv 管理
└── stacks/
    └── wiki_infra_stack.py  ← VPC / S3 / ECR / IAM
```

### デプロイ手順

```bash
cd infra
uv sync

# 初回のみ: CDK bootstrap
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=<account> CDK_DEFAULT_REGION=ap-northeast-1 \
  cdk bootstrap

# デプロイ
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=<account> CDK_DEFAULT_REGION=ap-northeast-1 \
  cdk deploy
```

### 生成されるリソース

| リソース | 説明 |
|---|---|
| VPC (10.0.0.0/16) | 2 AZ × private isolated subnet。NAT なし |
| S3 VPC Gateway Endpoint | VPC → S3 を無料・プライベート経路で接続 |
| S3: WikiBucket | wiki/ 永続化。versioning 有効 |
| S3: RawBucket | raw/ 原本。versioning 有効 |
| ECR: ai-agents-wiki-runtime | agent-runtime Docker イメージ置き場 |
| IAM Role: AgentCoreRole | AgentCore Runtime 実行ロール（S3 RW + ECR pull）|

## 既存 ai-agents/ との関係

- `../ai-agents/` は**一切変更しない**
- ローカル版 Claude Code スキル (`/ingest`, `/query`, `/lint`) はローカルで従来通り動く
- Web版はスキル定義のコピーを持ち、AgentCore Runtime 上で独立して動作する
