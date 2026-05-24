#!/usr/bin/env bash
# verify.sh
# Phase 2.6 デプロイ後の総合ヘルスチェック。以下の順序で確認する:
#   1. CloudFormation スタックの状態確認（WikiInfraStack / WikiRuntimeStack）
#   2. ECR に :latest イメージが存在するか確認
#   3. S3 バケットにデータが存在するか確認
#   4. AgentCore Runtime の疎通確認（invoke_runtime.py を呼び出す）
#
# 使い方:
#   ./scripts/verify.sh             # ステップ 1-3 のみ（インフラ確認）
#   ./scripts/verify.sh --invoke    # ステップ 1-4（Runtime 呼び出しも含む）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"

REGION=ap-northeast-1
AWS_PROFILE_NAME=dev
ACCOUNT_ID=650251713555
ECR_REPO=ai-agents-wiki-runtime

INVOKE="${1:-}"
PASS=0
FAIL=0

_ok()   { echo "  [OK]  $*"; PASS=$((PASS+1)); }
_fail() { echo "  [NG]  $*" >&2; FAIL=$((FAIL+1)); }

# ---------------------------------------------------------------------------
# Step 1: CloudFormation スタック状態
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Step 1: CloudFormation スタック状態"
echo "============================================================"

for STACK in WikiInfraStack WikiRuntimeStack; do
  STATUS=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws cloudformation describe-stacks \
    --stack-name "${STACK}" \
    --region "${REGION}" \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

  if [[ "${STATUS}" == "CREATE_COMPLETE" || "${STATUS}" == "UPDATE_COMPLETE" ]]; then
    _ok "${STACK}: ${STATUS}"
  else
    _fail "${STACK}: ${STATUS} (期待値: CREATE_COMPLETE / UPDATE_COMPLETE)"
  fi
done

# ---------------------------------------------------------------------------
# Step 2: ECR イメージ確認
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Step 2: ECR :latest イメージ確認"
echo "============================================================"

IMAGE_TAG=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws ecr describe-images \
  --repository-name "${ECR_REPO}" \
  --image-ids imageTag=latest \
  --region "${REGION}" \
  --query 'imageDetails[0].imageTags[0]' \
  --output text 2>/dev/null || echo "")

if [[ "${IMAGE_TAG}" == "latest" ]]; then
  PUSHED_AT=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws ecr describe-images \
    --repository-name "${ECR_REPO}" \
    --image-ids imageTag=latest \
    --region "${REGION}" \
    --query 'imageDetails[0].imagePushedAt' \
    --output text)
  _ok "ECR ${ECR_REPO}:latest (pushed: ${PUSHED_AT})"
else
  _fail "ECR ${ECR_REPO}:latest が見つかりません。ecr_push.sh を実行してください。"
fi

# ---------------------------------------------------------------------------
# Step 3: S3 データ確認
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Step 3: S3 バケット データ確認"
echo "============================================================"

WIKI_BUCKET=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws cloudformation describe-stacks \
  --stack-name WikiInfraStack \
  --region "${REGION}" \
  --query 'Stacks[0].Outputs[?OutputKey==`WikiBucketName`].OutputValue' \
  --output text 2>/dev/null || echo "")

RAW_BUCKET=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws cloudformation describe-stacks \
  --stack-name WikiInfraStack \
  --region "${REGION}" \
  --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
  --output text 2>/dev/null || echo "")

for BUCKET_VAR in WIKI_BUCKET RAW_BUCKET; do
  BUCKET="${!BUCKET_VAR}"
  if [[ -z "${BUCKET}" ]]; then
    _fail "${BUCKET_VAR}: バケット名を取得できませんでした"
    continue
  fi

  COUNT=$(AWS_PROFILE=${AWS_PROFILE_NAME} aws s3 ls "s3://${BUCKET}/" \
    --region "${REGION}" --recursive \
    2>/dev/null | wc -l | tr -d ' ')

  if [[ "${COUNT}" -gt 0 ]]; then
    _ok "s3://${BUCKET}/ — ${COUNT} オブジェクト"
  else
    _fail "s3://${BUCKET}/ — オブジェクトが 0 件。s3_sync.sh を実行してください。"
  fi
done

# ---------------------------------------------------------------------------
# Step 4: AgentCore Runtime 疎通確認（--invoke 指定時のみ）
# ---------------------------------------------------------------------------
if [[ "${INVOKE}" == "--invoke" ]]; then
  echo ""
  echo "============================================================"
  echo " Step 4: AgentCore Runtime 疎通確認"
  echo "============================================================"
  cd "${INFRA_DIR}"
  if uv run python "${SCRIPT_DIR}/invoke_runtime.py"; then
    _ok "AgentCore Runtime 呼び出し成功"
  else
    _fail "AgentCore Runtime 呼び出し失敗"
  fi
fi

# ---------------------------------------------------------------------------
# サマリー
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Summary: ${PASS} passed / ${FAIL} failed"
echo "============================================================"

if [[ ${FAIL} -gt 0 ]]; then
  exit 1
fi
