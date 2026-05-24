#!/usr/bin/env bash
# ecr_push.sh
# agent-runtime Docker イメージをビルドして ECR へ push し、WikiRuntimeStack を更新する。
# 前提: WikiInfraStack がデプロイ済みで ECR リポジトリが存在すること。

set -euo pipefail

ACCOUNT_ID=650251713555
REGION=ap-northeast-1
REPO_NAME=ai-agents-wiki-runtime
AWS_PROFILE_NAME=dev

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/../agent-runtime"
INFRA_DIR="${SCRIPT_DIR}/../infra"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

# git SHA を image-revision として使用（git 管理外なら timestamp にフォールバック）
IMAGE_REVISION="$(git -C "${SCRIPT_DIR}" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

# ECR ログイン
echo "=== Logging in to ECR ==="
aws ecr get-login-password \
    --region "${REGION}" \
    --profile "${AWS_PROFILE_NAME}" \
  | docker login --username AWS --password-stdin \
      "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Docker ビルド & push
echo "=== Building Docker image: ${REPO_NAME}:latest ==="
docker build -t "${REPO_NAME}:latest" "${RUNTIME_DIR}"

echo "=== Pushing ${ECR_URI}:latest ==="
docker tag "${REPO_NAME}:latest" "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"

echo "Done: ${ECR_URI}:latest (rev: ${IMAGE_REVISION})"

# WikiRuntimeStack を image-revision を渡して更新（description 変更で差分を強制）
echo ""
echo "=== Deploying WikiRuntimeStack (image-revision=${IMAGE_REVISION}) ==="
cd "${INFRA_DIR}"
AWS_PROFILE="${AWS_PROFILE_NAME}" \
CDK_DEFAULT_ACCOUNT="${ACCOUNT_ID}" \
CDK_DEFAULT_REGION="${REGION}" \
  uv run cdk deploy WikiRuntimeStack \
    --require-approval never \
    --context "image-revision=${IMAGE_REVISION}"
