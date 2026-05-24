#!/usr/bin/env bash
# ecr_push.sh
# agent-runtime Docker イメージをビルドして ECR へ push する。
# 前提: WikiInfraStack がデプロイ済みで ECR リポジトリが存在すること。

set -euo pipefail

ACCOUNT_ID=650251713555
REGION=ap-northeast-1
REPO_NAME=ai-agents-wiki-runtime
AWS_PROFILE_NAME=dev
TAG="${1:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/../agent-runtime"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

# skills/ を最新に同期してからビルドする
echo "=== Syncing skills ==="
"${SCRIPT_DIR}/sync-skills.sh"

# ECR ログイン
echo "=== Logging in to ECR ==="
aws ecr get-login-password \
    --region "${REGION}" \
    --profile "${AWS_PROFILE_NAME}" \
  | docker login --username AWS --password-stdin \
      "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Docker ビルド
echo "=== Building Docker image: ${REPO_NAME}:${TAG} ==="
docker build -t "${REPO_NAME}:${TAG}" "${RUNTIME_DIR}"

# タグ付けと push
echo "=== Pushing ${ECR_URI}:${TAG} ==="
docker tag "${REPO_NAME}:${TAG}" "${ECR_URI}:${TAG}"
docker push "${ECR_URI}:${TAG}"

echo "Done: ${ECR_URI}:${TAG}"
