#!/bin/sh
set -e

# S3 Files NFS マウントの所有者を appuser に変更する。
# NFS は UID 1000 (appuser) での書き込みを拒否するため、root で chown してから gosu で降格する。
# S3 Files が root_squash の場合は効果なし（boto3 フォールバックが必要になる）。
for dir in /mnt/wiki /mnt/raw; do
    if [ -d "$dir" ]; then
        chown appuser:appuser "$dir" 2>/dev/null || true
    fi
done

exec gosu appuser uv run python /app/src/entrypoint.py "$@"
