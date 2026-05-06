#!/usr/bin/env bash
# 一次性安装 git hooks
# 用法: scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for hook in pre-commit post-commit; do
  HOOK_SRC="${REPO_ROOT}/scripts/hooks/${hook}"
  HOOK_DST="${REPO_ROOT}/.git/hooks/${hook}"

  if [ ! -f "$HOOK_SRC" ]; then
    echo "WARNING: ${HOOK_SRC} 不存在，跳过" >&2
    continue
  fi

  # 备份已有 hook（非符号链接）
  if [ -L "$HOOK_DST" ]; then
    existing_target="$(readlink "$HOOK_DST")"
    if [ "$existing_target" = "../../scripts/hooks/${hook}" ]; then
      echo "${hook} 已经是指向 scripts/hooks/${hook} 的符号链接 ✓"
      continue
    fi
    rm "$HOOK_DST"
  elif [ -f "$HOOK_DST" ]; then
    mv "$HOOK_DST" "${HOOK_DST}.bak.$(date +%s)"
    echo "已备份原有 ${hook} hook"
  fi

  ln -s "../../scripts/hooks/${hook}" "$HOOK_DST"
  echo "已安装 ${hook} hook: .git/hooks/${hook} -> scripts/hooks/${hook}"
done
