#!/usr/bin/env bash
# PRD Tools 发版脚本
# 用法: scripts/release.sh [OPTIONS] [VERSION]
#
# OPTIONS:
#   --dry-run     只看会改什么，不写文件
#   --no-tag      不创建 git tag
#   --no-edit     不打开编辑器
#   -h, --help    显示用法
#
# VERSION:
#   显式版本号如 "2.5.0"，或 bump 关键字: patch / minor / major
#   默认: patch

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ==================== 参数解析 ====================

DRY_RUN=false
NO_TAG=false
NO_EDIT=false
VERSION_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --no-tag)   NO_TAG=true; shift ;;
    --no-edit)  NO_EDIT=true; shift ;;
    -h|--help)
      head -12 "$0" | tail -10 | sed 's/^# \?//'
      exit 0
      ;;
    *)          VERSION_ARG="$1"; shift ;;
  esac
done

# ==================== 辅助函数 ====================

die() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

dry_info() {
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] $*"
  fi
}

# 读取 VERSION 文件（去除空白）
read_version() {
  tr -d '[:space:]' < "${REPO_ROOT}/VERSION"
}

# 校验 semver 格式
validate_semver() {
  echo "$1" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'
}

# 解析版本号
parse_version() {
  local v="$1"
  IFS='.' read -r major minor patch <<< "$v"
  echo "$major $minor $patch"
}

# ==================== Step 0: 前置检查 ====================

info "Step 0: 前置检查"

# git repo
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || die "不在 git 仓库中"

# jq
command -v jq > /dev/null || die "需要 jq。安装: brew install jq"

# 工作树干净（dry-run 不要求）
if [ "$DRY_RUN" = false ]; then
  git diff --quiet || die "工作树有未提交修改，请先 commit 或 stash"
  git diff --cached --quiet || die "暂存区有未提交修改，请先 commit"
fi

# VERSION 存在
[ -f "${REPO_ROOT}/VERSION" ] || die "VERSION 文件不存在"

# 5 处版本一致
current=$(read_version)
for plugin in build-reference prd-distill; do
  pv=$(jq -r '.version' "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json" 2>/dev/null || echo "MISSING")
  [ "$pv" = "$current" ] || die "版本不一致: ${plugin}/plugin.json='${pv}', VERSION='${current}'"
done
m0=$(jq -r '.plugins[0].version' "${REPO_ROOT}/.claude-plugin/marketplace.json")
m1=$(jq -r '.plugins[1].version' "${REPO_ROOT}/.claude-plugin/marketplace.json")
[ "$m0" = "$current" ] || die "版本不一致: marketplace.json[0]='${m0}', VERSION='${current}'"
[ "$m1" = "$current" ] || die "版本不一致: marketplace.json[1]='${m1}', VERSION='${current}'"

info "当前版本: ${current}，5 处版本一致 ✓"

# ==================== Step 1: 计算新版本 ====================

info "Step 1: 计算新版本"

bump="${VERSION_ARG:-patch}"

if validate_semver "$bump"; then
  # 显式版本号
  new="$bump"
elif [ "$bump" = "patch" ] || [ "$bump" = "minor" ] || [ "$bump" = "major" ]; then
  # 自动递增
  read -r major minor patch <<< "$(parse_version "$current")"
  case "$bump" in
    patch) new="$major.$minor.$((patch + 1))" ;;
    minor) new="$major.$((minor + 1)).0" ;;
    major) new="$((major + 1)).0.0" ;;
  esac
else
  die "无效的版本参数: ${bump}（使用 patch/minor/major 或显式版本号如 2.5.0）"
fi

validate_semver "$new" || die "版本号格式无效: ${new}"

info "新版本: ${current} → ${new}"

# ==================== Step 2: 确定 commit 范围 ====================

info "Step 2: 确定 commit 范围"

last_tag=$(git describe --tags --match='v[0-9]*' --abbrev=0 2>/dev/null || true)
if [ -n "$last_tag" ]; then
  range="${last_tag}..HEAD"
  commit_count=$(git log --oneline "${range}" | wc -l | tr -d ' ')
  info "上个 tag: ${last_tag}，范围: ${range}（${commit_count} 个 commit）"
else
  range="HEAD"
  commit_count=$(git log --oneline | wc -l | tr -d ' ')
  info "没有历史 tag，使用全部历史（${commit_count} 个 commit）"
fi

# ==================== Step 3: 解析 git log 并分类 ====================

info "Step 3: 解析 git log"

# 解析 commits，输出格式: category|hash|subject
# $1: commit range
# $2: path filter prefix（空 = 全部）
parse_commits() {
  local range="$1"
  local filter_prefix="$2"

  # 先获取 commit hash 列表
  local hashes
  hashes=$(git log --format="%h" "$range" 2>/dev/null)

  [ -z "$hashes" ] && return

  for hash in $hashes; do
    local subject
    subject=$(git log -1 --format="%s" "$hash")

    # 路径过滤
    if [ -n "$filter_prefix" ]; then
      local files
      files=$(git diff-tree --no-commit-id --name-only -r "$hash" 2>/dev/null || true)
      if ! echo "$files" | grep -q "$filter_prefix"; then
        continue
      fi
    fi

    # 按 conventional commit 前缀分类
    local cat="Changed"
    if echo "$subject" | grep -qE '^feat'; then
      cat="Added"
    elif echo "$subject" | grep -qE '^fix'; then
      cat="Fixed"
    fi

    echo "${cat}|${hash}|${subject}"
  done
}

# 三个 changelog 的 entries
root_entries=$(parse_commits "$range" "")
br_entries=$(parse_commits "$range" "plugins/build-reference/")
pd_entries=$(parse_commits "$range" "plugins/prd-distill/")

# ==================== Step 4: 生成 CHANGELOG 草稿 ====================

info "Step 4: 生成 CHANGELOG 草稿"

today=$(date +%Y-%m-%d)

# 从 entries 生成一个 changelog section
generate_section() {
  local version="$1"
  local date="$2"
  local entries="$3"

  local has_content=false

  echo "## [${version}] - ${date}"
  echo ""

  for cat in Added Changed Fixed Removed; do
    lines=$(echo "$entries" | grep "^${cat}|" | cut -d'|' -f3- || true)
    if [ -n "$lines" ]; then
      has_content=true
      echo "### ${cat}"
      echo "$lines" | while IFS= read -r line; do
        [ -n "$line" ] && echo "- ${line}"
      done
      echo ""
    fi
  done

  if [ "$has_content" = false ]; then
    echo "### Changed"
    echo "- (待补充)"
    echo ""
  fi
}

root_section=$(generate_section "$new" "$today" "$root_entries")
br_section=$(generate_section "$new" "$today" "$br_entries")
pd_section=$(generate_section "$new" "$today" "$pd_entries")

if [ "$DRY_RUN" = true ]; then
  dry_info "=== Root CHANGELOG ==="
  echo "$root_section"
  dry_info "=== build-reference CHANGELOG ==="
  echo "$br_section"
  dry_info "=== prd-distill CHANGELOG ==="
  echo "$pd_section"
fi

# ==================== Step 5: 更新文件 ====================

info "Step 5: 更新文件"

# 备份
BACKUP_DIR=""
if [ "$DRY_RUN" = false ]; then
  BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/prd-tools-release.XXXXXX")
  cp "${REPO_ROOT}/VERSION" "$BACKUP_DIR/"
  cp "${REPO_ROOT}/.claude-plugin/marketplace.json" "$BACKUP_DIR/marketplace.json"
  cp "${REPO_ROOT}/plugins/build-reference/.claude-plugin/plugin.json" "$BACKUP_DIR/build-reference-plugin.json"
  cp "${REPO_ROOT}/plugins/prd-distill/.claude-plugin/plugin.json" "$BACKUP_DIR/prd-distill-plugin.json"
  cp "${REPO_ROOT}/CHANGELOG.md" "$BACKUP_DIR/root-CHANGELOG.md"
  cp "${REPO_ROOT}/plugins/build-reference/CHANGELOG.md" "$BACKUP_DIR/build-reference-CHANGELOG.md"
  cp "${REPO_ROOT}/plugins/prd-distill/CHANGELOG.md" "$BACKUP_DIR/prd-distill-CHANGELOG.md"
  info "备份已保存到 ${BACKUP_DIR}"
fi

# 插入 CHANGELOG 条目（在 --- 或文件头之后）
insert_changelog_entry() {
  local file="$1"
  local entry="$2"

  if [ "$DRY_RUN" = true ]; then
    dry_info "会在 ${file} 插入新条目"
    return
  fi

  # 找到第一个 --- 分隔符或 ## 标题，在其后插入
  # 使用 awk 在第一个 --- 或 ## 之前的位置插入
  local tmp="${file}.tmp"
  awk -v entry="$entry" '
    BEGIN { inserted = 0 }
    /^---/ && !inserted { print; print ""; print entry; inserted = 1; next }
    /^## / && !inserted { print entry; print; inserted = 1; next }
    { print }
  ' "$file" > "$tmp" && mv "$tmp" "$file"
}

insert_changelog_entry "${REPO_ROOT}/CHANGELOG.md" "$root_section"
insert_changelog_entry "${REPO_ROOT}/plugins/build-reference/CHANGELOG.md" "$br_section"
insert_changelog_entry "${REPO_ROOT}/plugins/prd-distill/CHANGELOG.md" "$pd_section"

# 更新版本号
if [ "$DRY_RUN" = true ]; then
  dry_info "VERSION: ${current} → ${new}"
  dry_info "plugins/build-reference/.claude-plugin/plugin.json: ${current} → ${new}"
  dry_info "plugins/prd-distill/.claude-plugin/plugin.json: ${current} → ${new}"
  dry_info ".claude-plugin/marketplace.json: 两个插件 ${current} → ${new}"
else
  # VERSION
  echo "$new" > "${REPO_ROOT}/VERSION"

  # plugin.json
  for plugin in build-reference prd-distill; do
    jq --arg v "$new" '.version = $v' \
      "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json" \
      > "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json.tmp" && \
    mv "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json.tmp" \
       "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json"
  done

  # marketplace.json
  jq --arg v "$new" '.plugins[0].version = $v | .plugins[1].version = $v' \
    "${REPO_ROOT}/.claude-plugin/marketplace.json" \
    > "${REPO_ROOT}/.claude-plugin/marketplace.json.tmp" && \
  mv "${REPO_ROOT}/.claude-plugin/marketplace.json.tmp" \
     "${REPO_ROOT}/.claude-plugin/marketplace.json"

  info "5 处版本号已更新为 ${new} ✓"
fi

# ==================== dry-run 到此结束 ====================

if [ "$DRY_RUN" = true ]; then
  dry_info "没有修改任何文件。"
  exit 0
fi

# ==================== Step 6: 人工审核 ====================

if [ "$NO_EDIT" = false ]; then
  info "Step 6: 打开编辑器审核 CHANGELOG..."
  info "请检查分类和措辞，保存后关闭编辑器继续。"
  ${EDITOR:-vi} \
    "${REPO_ROOT}/CHANGELOG.md" \
    "${REPO_ROOT}/plugins/build-reference/CHANGELOG.md" \
    "${REPO_ROOT}/plugins/prd-distill/CHANGELOG.md"
  info "编辑器已关闭。"
fi

# ==================== Step 7: 提交后校验 ====================

info "Step 7: 提交后校验"

final_version=$(read_version)
[ "$final_version" = "$new" ] || die "VERSION 被修改为 '${final_version}'，期望 '${new}'"

for plugin in build-reference prd-distill; do
  pv=$(jq -r '.version' "${REPO_ROOT}/plugins/${plugin}/.claude-plugin/plugin.json")
  [ "$pv" = "$new" ] || die "${plugin}/plugin.json 版本 '${pv}'，期望 '${new}'"
done

m0=$(jq -r '.plugins[0].version' "${REPO_ROOT}/.claude-plugin/marketplace.json")
m1=$(jq -r '.plugins[1].version' "${REPO_ROOT}/.claude-plugin/marketplace.json")
[ "$m0" = "$new" ] || die "marketplace.json[0] 版本 '${m0}'，期望 '${new}'"
[ "$m1" = "$new" ] || die "marketplace.json[1] 版本 '${m1}'，期望 '${new}'"

info "版本校验通过 ✓"

# ==================== Step 8: 提交 + tag ====================

info "Step 8: 提交"

git add \
  "${REPO_ROOT}/VERSION" \
  "${REPO_ROOT}/.claude-plugin/marketplace.json" \
  "${REPO_ROOT}/plugins/build-reference/.claude-plugin/plugin.json" \
  "${REPO_ROOT}/plugins/prd-distill/.claude-plugin/plugin.json" \
  "${REPO_ROOT}/CHANGELOG.md" \
  "${REPO_ROOT}/plugins/build-reference/CHANGELOG.md" \
  "${REPO_ROOT}/plugins/prd-distill/CHANGELOG.md"

git commit -m "release: v${new}"

if [ "$NO_TAG" = false ]; then
  git tag -a "v${new}" -m "Release v${new}"
  info "已创建 tag: v${new}"
fi

info "发版完成: v${current} → v${new} ✓"
info ""
info "下一步:"
info "  git push origin v2.0 --tags"
info ""
if [ -n "$BACKUP_DIR" ]; then
  info "备份位置: ${BACKUP_DIR}"
fi
