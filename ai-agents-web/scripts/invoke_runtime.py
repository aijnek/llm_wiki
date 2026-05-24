#!/usr/bin/env python3
"""
invoke_runtime.py
Bedrock AgentCore Runtime を boto3 経由で呼び出し、疎通確認を行う。

使い方:
    uv run python scripts/invoke_runtime.py
    uv run python scripts/invoke_runtime.py "インデックスの一覧を教えてください"

前提:
    - WikiRuntimeStack がデプロイ済みであること
    - AWS_PROFILE=dev で ap-northeast-1 に疎通できること
    - uv sync 済み (boto3 が入っていること)
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

import boto3

REGION = "ap-northeast-1"
AWS_PROFILE = "dev"
STACK_NAME_INFRA = "WikiInfraStack"
STACK_NAME_RUNTIME = "WikiRuntimeStack"


def get_cfn_output(cf_client, stack_name: str, key: str) -> str:
    """CloudFormation スタックの Output 値を取得する。"""
    resp = cf_client.describe_stacks(StackName=stack_name)
    outputs = resp["Stacks"][0].get("Outputs", [])
    for o in outputs:
        if o["OutputKey"] == key:
            return o["OutputValue"]
    raise KeyError(f"CloudFormation output '{key}' not found in stack '{stack_name}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentCore Runtime 疎通確認")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="wikiのインデックス（index.md の目次）を教えてください",
        help="エージェントに送るプロンプト（デフォルト: index.md の内容確認）",
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=AWS_PROFILE, region_name=REGION)
    cf_client = session.client("cloudformation")

    # --- Runtime ARN を CloudFormation から取得 ---
    print("=== Getting AgentCore Runtime ARN from CloudFormation ===")
    try:
        runtime_arn = get_cfn_output(cf_client, STACK_NAME_RUNTIME, "AgentCoreRuntimeArn")
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("WikiRuntimeStack がデプロイ済みか確認してください。", file=sys.stderr)
        sys.exit(1)

    print(f"Runtime ARN: {runtime_arn}")

    # --- AgentCore Runtime を呼び出す ---
    runtime_client = session.client("bedrock-agentcore")

    runtime_session_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": args.prompt}).encode("utf-8")

    print(f"\nPrompt: {args.prompt}")
    print(f"Session ID: {runtime_session_id}")
    print("\n=== Invoking AgentCore Runtime ===")

    try:
        response = runtime_client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=runtime_session_id,
            payload=payload,
            contentType="application/json",
            accept="application/json",
        )
    except Exception as e:
        print(f"\nERROR: Runtime 呼び出しに失敗しました: {e}", file=sys.stderr)
        print(
            "\n[ヒント] 以下を確認してください:\n"
            "  1. WikiRuntimeStack のデプロイが完了している\n"
            "  2. ECR に :latest イメージが push 済み\n"
            "  3. AgentCore Runtime の Status が READY になっている\n"
            "     (AWS Console > Bedrock > AgentCore > Runtimes で確認)\n"
            "  4. boto3 のバージョンが bedrock-agentcore に対応している\n"
            "     (pip install --upgrade boto3)",
            file=sys.stderr,
        )
        sys.exit(1)

    # レスポンスを表示（response['response'] は StreamingBody）
    print("\n=== Response ===")
    stream = response.get("response")
    if hasattr(stream, "read"):
        body = stream.read().decode("utf-8")
    else:
        body = str(stream)

    try:
        parsed = json.loads(body)
        output = parsed.get("output", {})
        message = output.get("message", body)
        print(message)
    except (json.JSONDecodeError, AttributeError):
        print(body)

    print("\n=== Invocation successful ===")


if __name__ == "__main__":
    main()
