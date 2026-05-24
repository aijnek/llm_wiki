#!/usr/bin/env python3
"""
verify_ws.py
WikiApiStack (WebSocket API) の疎通確認スクリプト。

使い方:
    uv run python scripts/verify_ws.py
    uv run python scripts/verify_ws.py "ReActとは何か"

前提:
    - WikiApiStack がデプロイ済みであること
    - websockets パッケージが入っていること（uv add websockets）
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import boto3
import websockets

REGION = "ap-northeast-1"
AWS_PROFILE = "dev"
STACK_NAME = "WikiApiStack"


def get_ws_url() -> str:
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=REGION)
    cf = session.client("cloudformation")
    resp = cf.describe_stacks(StackName=STACK_NAME)
    for o in resp["Stacks"][0].get("Outputs", []):
        if o["OutputKey"] == "WsApiUrl":
            return o["OutputValue"]
    raise KeyError("WsApiUrl not found in WikiApiStack outputs")


async def query(ws_url: str, prompt: str) -> None:
    print(f"Connecting to {ws_url}")
    async with websockets.connect(ws_url) as ws:
        print(f"Connected. Sending prompt: {prompt!r}")
        await ws.send(json.dumps({"prompt": prompt}))

        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "message":
                print("\n=== Response ===")
                print(msg.get("content", ""))
            elif msg_type == "done":
                print("\n=== Done ===")
                break
            elif msg_type == "error":
                print(f"\n=== Error ===\n{msg.get('message', '')}", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"[unknown msg] {msg}")


def main() -> None:
    parser = argparse.ArgumentParser(description="WebSocket API 疎通確認")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="wikiのインデックス（index.md の目次）を教えてください",
    )
    args = parser.parse_args()

    ws_url = get_ws_url()
    asyncio.run(query(ws_url, args.prompt))


if __name__ == "__main__":
    main()
