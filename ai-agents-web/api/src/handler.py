from __future__ import annotations

import json
import os
import uuid

import boto3

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
RUNTIME_ARN = os.environ.get("RUNTIME_ARN", "")
PROCESSOR_FUNCTION_NAME = os.environ.get("PROCESSOR_FUNCTION_NAME", "")
RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME", "")


def websocket_handler(event, context):
    """API Gateway WebSocket handler — $connect / $disconnect / $default."""
    route_key = event["requestContext"]["routeKey"]

    if route_key in ("$connect", "$disconnect"):
        return {"statusCode": 200}

    # $default: parse prompt, dispatch processing asynchronously
    connection_id = event["requestContext"]["connectionId"]
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]

    try:
        body = json.loads(event.get("body") or "{}")
        prompt = body.get("prompt", "").strip()
    except (json.JSONDecodeError, AttributeError):
        prompt = ""

    if not prompt:
        _post(connection_id, domain, stage, {"type": "error", "message": "prompt is required"})
        return {"statusCode": 400}

    boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=PROCESSOR_FUNCTION_NAME,
        InvocationType="Event",  # async — returns immediately, avoids 29s API GW limit
        Payload=json.dumps({
            "connectionId": connection_id,
            "domainName": domain,
            "stage": stage,
            "prompt": prompt,
        }).encode("utf-8"),
    )

    return {"statusCode": 200}


def processor_handler(event, context):
    """Async processor — invoke AgentCore Runtime, post result back via WebSocket."""
    connection_id = event["connectionId"]
    domain = event["domainName"]
    stage = event["stage"]
    prompt = event["prompt"]

    try:
        runtime_client = boto3.client("bedrock-agentcore", region_name=REGION)
        response = runtime_client.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            runtimeSessionId=str(uuid.uuid4()),
            payload=json.dumps({"prompt": prompt}).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )

        raw = response["response"].read().decode("utf-8")
        try:
            parsed = json.loads(raw)
            message = parsed.get("output", {}).get("message", raw)
        except (json.JSONDecodeError, AttributeError):
            message = raw

        _post(connection_id, domain, stage, {"type": "message", "content": message})
        _post(connection_id, domain, stage, {"type": "done"})

    except Exception as e:
        try:
            _post(connection_id, domain, stage, {"type": "error", "message": str(e)})
        except Exception:
            pass


def presign_handler(event, context):
    """HTTP API handler — POST /presign-upload"""
    try:
        body = json.loads(event.get("body") or "{}")
        filename = body.get("filename", "").strip()
        content_type = body.get("content_type", "application/octet-stream").strip()
    except (json.JSONDecodeError, AttributeError):
        return _http_response(400, {"error": "invalid JSON"})

    if not filename or "/" in filename or "\\" in filename or filename.startswith("."):
        return _http_response(400, {"error": "invalid filename"})

    s3 = boto3.client("s3", region_name=REGION)
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": RAW_BUCKET_NAME,
            "Key": filename,
            "ContentType": content_type,
        },
        ExpiresIn=900,
    )
    return _http_response(200, {"url": url})


def _http_response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def _post(connection_id: str, domain: str, stage: str, data: dict) -> None:
    boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=f"https://{domain}/{stage}",
        region_name=REGION,
    ).post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
    )
