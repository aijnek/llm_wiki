# infra/ — CDK 作業ガイド（コーディングエージェント向け）

## 実行環境

- AWS プロファイル: `dev`（PowerUserAccess）
- アカウント: 650251713555 / リージョン: ap-northeast-1
- Python 実行: `uv run` を使うこと（`python` 直打ち禁止）
- CDK 実行例: `AWS_PROFILE=dev CDK_DEFAULT_ACCOUNT=650251713555 CDK_DEFAULT_REGION=ap-northeast-1 uv run cdk <command>`

## スタック構成

| スタック | 役割 |
|---|---|
| `WikiInfraStack` | VPC / S3 / ECR / IAM — 基盤リソース |
| `WikiRuntimeStack` | Bedrock AgentCore Runtime 定義（WikiInfraStack の出力に依存） |

デプロイ順序: WikiInfraStack → ECR push → WikiRuntimeStack（`scripts/deploy.sh` で一括実行）

---

## ⚠️ セキュリティ: CDK Bootstrap の権限昇格リスク

### 何が起きているか

CDK Bootstrap はデフォルトで `CloudFormationExecutionRole`（**AdministratorAccess** 付き）を作成する。
これにより次の権限昇格パスが生まれる:

```
PowerUserAccess（IAM 操作不可）
  → CDK stack に「AdminAccess 付き IAM ロールを作れ」と書いて cdk deploy
  → CloudFormation が CloudFormationExecutionRole（AdministratorAccess）として実行
  → 結果: PowerUser が直接できない IAM 操作を CloudFormation 経由で達成できてしまう
```

### Bootstrap の実行権限

PowerUserAccess では `iam:CreateRole` 等が禁止されているため、`cdk bootstrap` を実行すると IAM ロール作成のステップで **403 エラーになり失敗する**。Bootstrap は admin 相当の権限を持つプロファイルで実行すること。

Bootstrap が一度成功すれば、以後の `cdk deploy` は PowerUser で実行できる（CloudFormation が CFN execution role として動くため）。

### 開発環境での許容判断

このプロジェクトでは **開発アカウント専用** と割り切って、デフォルト bootstrap（CFN execution role = AdministratorAccess）を使用している。
理由: 開発速度・利便性を優先、アカウント分離によりリスクを局所化。

### 本番環境での対処（将来フェーズで必須）

本番アカウントでは bootstrap 時に `--cloudformation-execution-policies` でこのスタックに必要な最小権限ポリシーを指定し、AdministratorAccess を持つ CFN execution role を作らないこと:

```bash
# 例: このプロジェクト専用の最小権限ポリシーを事前に作成し、それを指定する
cdk bootstrap \
  --cloudformation-execution-policies arn:aws:iam::<account>:policy/WikiCdkDeployPolicy
```

`WikiCdkDeployPolicy` には、このスタックが実際に必要とするサービス（EC2/VPC・S3・ECR・IAM・BedrockAgentCore）の操作権限だけを含める。AdministratorAccess は含めない。

### エージェントへの指示

- `cdk bootstrap` を提案・実行するときは admin 権限が必要であることを確認すること
- 本番環境向けの CDK bootstrap を提案するときは、必ず `--cloudformation-execution-policies` に最小権限ポリシーを指定するよう案内すること
- デフォルト bootstrap（AdministratorAccess）を本番アカウントに適用するコードを書かないこと

---

## synthesizer の選択

現在の `app.py` は標準 synthesizer（Bootstrap ロール経由）を使用している。
理由: 将来 Lambda アセット追加時に対応できること。

`CliCredentialsStackSynthesizer` は Bootstrap 不要だが、「PowerUser の現在の権限に依存する」「Lambda/Docker アセットを CDK が管理できなくなる」制限がある。変更を提案する場合はこれらの含意を必ず説明すること。
