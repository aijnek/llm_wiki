#!/usr/bin/env bash
# sync-skills.sh
# ../ai-agents/.claude/commands/*.md を agent-runtime/skills/ へコピーする。
# git submodule や symlink は使わず、明示的なコピーで ai-agents/ への依存を断ち切る。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/../../ai-agents/.claude/commands"
DEST_DIR="${SCRIPT_DIR}/../agent-runtime/skills"

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "ERROR: Source directory not found: ${SRC_DIR}" >&2
  exit 1
fi

mkdir -p "${DEST_DIR}"

echo "Syncing skills from ${SRC_DIR} → ${DEST_DIR}"
cp -v "${SRC_DIR}"/*.md "${DEST_DIR}/"
echo "Done."
