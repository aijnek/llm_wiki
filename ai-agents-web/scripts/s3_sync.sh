#!/usr/bin/env bash
# s3_sync.sh
# ローカルの ai-agents/wiki/ と ai-agents/raw/ を S3 バケットに同期する。
# 初回デプロイ後の初期データ投入と、手動更新に使う。
#
# 使い方:
#   ./scripts/s3_sync.sh            # ローカル → S3（アップロード、デフォルト）
#   ./scripts/s3_sync.sh --down     # S3 → ローカル（ダウンロード）
#
# 前提: WikiInfraStack がデプロイ済みであること

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_AGENTS_DIR="${SCRIPT_DIR}/../../ai-agents"
STACK_NAME=WikiInfraStack
REGION=ap-northeast-1
AWS_PROFILE_NAME=dev

DIRECTION="${1:-}"

# CloudFormation outputs からバケット名を取得
echo "=== Getting bucket names from CloudFormation ==="
WIKI_BUCKET=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query 'Stacks[0].Outputs[?OutputKey==`WikiBucketName`].OutputValue' \
  --output text)

RAW_BUCKET=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
  --output text)

if [[ -z "${WIKI_BUCKET}" || -z "${RAW_BUCKET}" ]]; then
  echo "ERROR: バケット名を取得できませんでした。WikiInfraStack がデプロイ済みか確認してください。" >&2
  exit 1
fi

echo "WikiBucket: ${WIKI_BUCKET}"
echo "RawBucket:  ${RAW_BUCKET}"

if [[ "${DIRECTION}" == "--down" ]]; then
  # S3 → ローカル（バックアップ取り戻し用）
  echo ""
  echo "=== [DOWN] s3://${WIKI_BUCKET}/ → ${AI_AGENTS_DIR}/wiki/ ==="
  AWS_PROFILE=${AWS_PROFILE_NAME} aws s3 sync \
    "s3://${WIKI_BUCKET}/" \
    "${AI_AGENTS_DIR}/wiki/" \
    --region "${REGION}"

  echo ""
  echo "=== [DOWN] s3://${RAW_BUCKET}/ → ${AI_AGENTS_DIR}/raw/ ==="
  AWS_PROFILE=${AWS_PROFILE_NAME} aws s3 sync \
    "s3://${RAW_BUCKET}/" \
    "${AI_AGENTS_DIR}/raw/" \
    --region "${REGION}"

  echo ""
  echo "Download sync complete."
else
  # ローカル → S3（デフォルト: アップロード）
  echo ""
  # S3 Files はバケット全体をマウントするためルートに同期する
  echo "=== [UP] ${AI_AGENTS_DIR}/wiki/ → s3://${WIKI_BUCKET}/ ==="
  AWS_PROFILE=${AWS_PROFILE_NAME} aws s3 sync \
    "${AI_AGENTS_DIR}/wiki/" \
    "s3://${WIKI_BUCKET}/" \
    --region "${REGION}"

  echo ""
  echo "=== [UP] ${AI_AGENTS_DIR}/raw/ → s3://${RAW_BUCKET}/ ==="
  AWS_PROFILE=${AWS_PROFILE_NAME} aws s3 sync \
    "${AI_AGENTS_DIR}/raw/" \
    "s3://${RAW_BUCKET}/" \
    --region "${REGION}"

  echo ""
  echo "Upload sync complete."
  echo "  s3://${WIKI_BUCKET}/"
  echo "  s3://${RAW_BUCKET}/"
fi
