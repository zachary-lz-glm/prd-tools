#!/usr/bin/env bash
# 一次性安装 git hooks
# 用法: scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="${REPO_ROOT}/scripts/hooks/pre-commit"
HOOK_DST="${REPO_ROOT}/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SRC" ]; then
  echo "ERROR: ${HOOK_SRC} 不存在" >&2
  exit 1
fi

# 备份已有 hook
if [ -L "$HOOK_DST" ]; then
  rm "$HOOK_DST"
elif [ -f "$HOOK_DST" ]; then
  mv "$HOOK_DST" "${HOOK_DST}.bak.$(date +%s)"
  echo "已备份原有 pre-commit hook"
fi

ln -s "../../scripts/hooks/pre-commit" "$HOOK_DST"
echo "已安装 pre-commit hook: .git/hooks/pre-commit -> scripts/hooks/pre-commit"
