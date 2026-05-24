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

| フェーズ | 内容 | ディレクトリ | 状態 |
|---|---|---|---|
| 1 | scaffold + agent-runtime ローカル検証 | agent-runtime/ | ✅ 完了 |
| 1.5 | BedrockAgentCoreApp ラッパー導入・ローカル HTTP 疎通確認 | agent-runtime/ | ✅ 完了 |
| 2 | AWS CDK infra — VPC / S3 / ECR / IAM | infra/ | ✅ 完了 |
| 2.5 | AgentCore Runtime CDK 定義・S3 Files BYO・ECR push スクリプト | infra/ | ✅ 完了 |
| 2.6 | cdk deploy・S3 初回 sync・AWS 上での疎通確認 | infra/ | ✅ 完了 |
| 3 | API Lambda + WebSocket | api/ | ✅ 完了 |
| 4.1 | Next.js scaffold + Chat UI（WebSocket 接続・プロンプト送受信） | frontend/ | ✅ 完了 |
| 4.2 | Ingest UI + presigned URL エンドポイント | frontend/, api/ | ✅ 完了 |
| 5 | WebSocket ストリーミング | api/, agent-runtime/ | ✅ 完了 |
| 6 | マルチターン会話 | api/, agent-runtime/, frontend/, infra/ | 📋 計画中 |
| 7 | Wiki 閲覧（S3 Markdown 一覧 + Obsidian リンク レンダラ） | frontend/, api/ | 未着手 |
| 8 | Amplify Hosting デプロイ（CDK + 環境変数設定） | infra/, frontend/ | 未着手 |

### Phase 5: WebSocket ストリーミング

AgentCore Runtime からのチャンクをリアルタイムで WebSocket に転送する。

| サブフェーズ | 内容 |
|---|---|
| 5.1 | `BedrockAgentCoreApp` のストリーミングレスポンス対応を調査（`@app.entrypoint` が AsyncGenerator / StreamingResponse を返せるか確認） |
| 5.2 | `entrypoint.py` の `agent_invocation` を NDJSON 逐次レスポンス対応に変更（チャンクを1行ずつ yield） |
| 5.3 | `processor_handler` をレスポンス行単位読み込み → チャンクごと WS 送信（`{"type":"message","content":"..."}` × N → `{"type":"done"}`）に変更 |
| 5.4 | CDK・Lambda 更新（依存ライブラリ追加が必要な場合）・deploy・エンドツーエンド疎通確認 |

### Phase 6: マルチターン会話

会話セッションを維持し、前のやりとりを踏まえた回答を実現する。

| サブフェーズ | 内容 |
|---|---|
| 6.1 | DynamoDB にセッションテーブル追加（CDK）。項目: `{sessionId (PK), messages: [{role, content}], ttl}` |
| 6.2 | フロントエンドでセッション ID 生成・WS メッセージに含める（`{ prompt, sessionId }`）。「新しい会話」ボタン追加 |
| 6.3 | `websocket_handler` → `processor_handler` でセッション ID を受け渡し、DynamoDB から履歴をロード・保存 |
| 6.4 | Claude Agent SDK の `query` が `messages` パラメータをサポートするか調査。`run_agent` / `agent_invocation` をマルチターン対応に変更（非対応の場合は system prompt への履歴埋め込みで代替） |

## infra/ — CDK (Python / uv)

```
infra/
├── app.py              ← CDK アプリエントリポイント
├── cdk.json            ← "app": "uv run python app.py"
├── pyproject.toml      ← uv 管理
└── stacks/
    ├── wiki_infra_stack.py   ← VPC / S3 / ECR / IAM（WikiInfraStack）
    ├── wiki_runtime_stack.py ← AgentCore Runtime（WikiRuntimeStack）
    └── wiki_api_stack.py     ← Lambda + WebSocket API（WikiApiStack）
```

### ⚠️ CDK Bootstrap のセキュリティ注意事項

CDK Bootstrap はデフォルトで `CloudFormationExecutionRole`（AdministratorAccess 付き）を作成する。
これにより **PowerUser でも CloudFormation 経由で IAM ロール作成等の Admin 操作が可能になる**（権限昇格パス）。

| 環境 | 対応方針 |
|---|---|
| **開発** | デフォルト bootstrap を許容（アカウント分離で局所化） |
| **本番** | `--cloudformation-execution-policies` に最小権限ポリシーを指定し AdministratorAccess を避ける |

Bootstrap 自体は `iam:CreateRole` 等が必要なため **PowerUserAccess では実行できず 403 エラーになる**。
admin 相当のプロファイルで一回だけ実行すること。Bootstrap 完了後は PowerUser で `cdk deploy` できる。

詳細: `infra/CLAUDE.md`

### フルデプロイ（Phase 3 時点）

ECR repo 作成 → Docker push → Runtime → API の順序依存を解決するため、`deploy.sh` で一括実行する。

```bash
# 初回のみ: CDK bootstrap（admin プロファイルで実行）
cd infra
AWS_PROFILE=<admin> CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 \
  uv run cdk bootstrap

# Step 1: フルデプロイ（infra → ECR push → runtime → api の順）
./scripts/deploy.sh

# Step 2: ローカル wiki/raw → S3 初回 sync
./scripts/s3_sync.sh

# Step 3: デプロイ後ヘルスチェック（スタック状態 / ECR / S3 オブジェクト確認）
./scripts/verify.sh

# Step 4: Runtime 呼び出し疎通確認（--invoke で実際に LLM を呼ぶ）
./scripts/verify.sh --invoke

# Step 5: WebSocket API 疎通確認
cd infra && uv run python ../scripts/verify_ws.py
```

S3 の逆方向 sync（S3 → ローカル）:
```bash
./scripts/s3_sync.sh --down
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

# Step 4: Lambda + WebSocket API
AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 \
  uv run cdk deploy WikiApiStack --require-approval never
```

### 生成されるリソース

| スタック | リソース | 説明 |
|---|---|---|
| WikiInfraStack | VPC (10.0.0.0/16) | Public + Private subnet × 2 AZ、NAT Gateway × 1 |
| WikiInfraStack | S3 VPC Gateway Endpoint | VPC → S3 を無料・プライベート経路で接続 |
| WikiInfraStack | S3: WikiBucket | wiki/ 永続化。versioning 有効 |
| WikiInfraStack | S3: RawBucket | raw/ 原本。versioning 有効 |
| WikiInfraStack | S3 Files: WikiFileSystem + MountTargets + AccessPoint | WikiBucket を NFS マウントするファイルシステム |
| WikiInfraStack | S3 Files: RawFileSystem + MountTargets + AccessPoint | RawBucket を NFS マウントするファイルシステム |
| WikiInfraStack | ECR: ai-agents-wiki-runtime | agent-runtime Docker イメージ置き場 |
| WikiInfraStack | IAM Role: AgentCoreRole | AgentCore Runtime 実行ロール（S3 RW + ECR pull + SSM read + s3files:*）|
| WikiInfraStack | IAM Role: S3FilesRole | S3 Files sync ロール（elasticfilesystem.amazonaws.com 用）|
| WikiRuntimeStack | AgentCore Runtime: ai_agents_wiki_runtime | /mnt/wiki・/mnt/raw を S3 Files BYO マウント済み |
| WikiApiStack | Lambda: OrchestratorFn | WebSocket メッセージを受けて ProcessorFn を非同期 invoke |
| WikiApiStack | Lambda: ProcessorFn | AgentCore Runtime を呼び出し WS に結果を返送（タイムアウト 10 分） |
| WikiApiStack | API GW WebSocket: ai-agents-wiki-ws | wss://... エンドポイント（prod ステージ） |

> **NAT Gateway**: Runtime コンテナから Anthropic API（外部）への outbound のために NAT Gateway 1 台を常時起動（約 $32/月）。

### API キー管理（SSM Parameter Store）

AgentCore Runtime は起動時に SSM から `ANTHROPIC_API_KEY` または `CLAUDE_CODE_OAUTH_TOKEN` を取得します。

```bash
# 初回登録（sk-ant-api03- の場合は ANTHROPIC_API_KEY、sk-ant-oat の場合は OAuth トークン）
AWS_PROFILE=dev aws ssm put-parameter \
  --name "/ai-agents-wiki/anthropic-api-key" \
  --value "YOUR_API_KEY_OR_OAUTH_TOKEN" \
  --type SecureString \
  --region ap-northeast-1

# 更新
AWS_PROFILE=dev aws ssm put-parameter \
  --name "/ai-agents-wiki/anthropic-api-key" \
  --value "NEW_KEY" \
  --type SecureString \
  --region ap-northeast-1 \
  --overwrite
```

`entrypoint.py` が起動時に自動判別します: `sk-ant-oat` で始まれば `CLAUDE_CODE_OAUTH_TOKEN`、それ以外は `ANTHROPIC_API_KEY` にセット。

## 既存 ai-agents/ との関係

- `../ai-agents/` は**一切変更しない**
- ローカル版 Claude Code スキル (`/ingest`, `/query`, `/lint`) はローカルで従来通り動く
- Web版はスキル定義のコピーを持ち、AgentCore Runtime 上で独立して動作する
