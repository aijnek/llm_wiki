#!/usr/bin/env bash
# deploy.sh
# Phase 2.5 フルデプロイスクリプト。以下の順序で実行する:
#   1. WikiInfraStack デプロイ（VPC / S3 / ECR / IAM）
#   2. Docker イメージのビルド & ECR push
#   3. WikiRuntimeStack デプロイ（AgentCore Runtime 定義）
#
# 使い方:
#   ./scripts/deploy.sh
#
# 前提:
#   - AWS_PROFILE=dev で ap-northeast-1 にアクセスできること
#   - docker がインストール済みであること
#   - CDK bootstrap 済みであること（未の場合は deploy.sh 内コメントを参照）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"

CDK_ENV=(
  "AWS_PROFILE=dev"
  "CDK_DEFAULT_ACCOUNT=650251713555"
  "CDK_DEFAULT_REGION=ap-northeast-1"
)

# ---------------------------------------------------------------------------
# 初回のみ: CDK bootstrap が必要な場合は以下を手動実行してください
#   env "${CDK_ENV[@]}" cdk bootstrap
# ---------------------------------------------------------------------------

echo "============================================================"
echo " Step 1: WikiInfraStack deploy (VPC / S3 / ECR / IAM)"
echo "============================================================"
cd "${INFRA_DIR}"
env "${CDK_ENV[@]}" uv run cdk deploy WikiInfraStack --require-approval never

echo ""
echo "============================================================"
echo " Step 2: Docker build & ECR push"
echo "============================================================"
"${SCRIPT_DIR}/ecr_push.sh"

echo ""
echo "============================================================"
echo " Step 3: WikiRuntimeStack deploy (AgentCore Runtime)"
echo "============================================================"
cd "${INFRA_DIR}"
env "${CDK_ENV[@]}" uv run cdk deploy WikiRuntimeStack --require-approval never

echo ""
echo "All done."
