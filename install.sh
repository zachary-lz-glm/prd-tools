#!/usr/bin/env bash
# install.sh — Install prd-tools skills and commands into a target project.
#
# Scope: only what this repo OWNS (build-reference / prd-distill skills,
# /reference command, version marker). External tools (uv, MarkItDown,
# Graphify, GitNexus, API keys) are NOT touched here — run `prd-tools-doctor`
# afterwards to check and fix those.
#
# See docs/adr/0008-安装脚本职责拆分.md for rationale.

set -euo pipefail

REPO="zachary-lz-glm/prd-tools"
BRANCH="v2.0"
TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

CLAUDE_SKILLS_DIR="$TARGET/.claude/skills"
CLAUDE_COMMANDS_DIR="$TARGET/.claude/commands"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          prd-tools 安装                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Proxy (curl only) ─────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/scripts/lib/detect_proxy.sh" ]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/scripts/lib/detect_proxy.sh"
  detect_proxy_for_curl
fi

# ── 下载源码 ────────────────────────────────────────────────────
echo "==> 下载 prd-tools ($BRANCH 分支)..."
ARCHIVE_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"
if ! curl -fsSL --connect-timeout 10 --max-time 60 "$ARCHIVE_URL" \
     | tar -xz -C "$TMP_DIR" 2>/dev/null; then
  echo "" >&2
  echo "错误：从 GitHub 下载源码失败。" >&2
  echo "" >&2
  echo "兜底方案 — 用 git 克隆后再本地安装：" >&2
  echo "  git clone --depth 1 -b $BRANCH https://github.com/$REPO.git /tmp/prd-tools" >&2
  echo "  bash /tmp/prd-tools/install.sh $TARGET" >&2
  exit 1
fi

ARCHIVE_ROOT="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"
if [ -z "$ARCHIVE_ROOT" ] || [ ! -d "$ARCHIVE_ROOT/plugins" ]; then
  echo "错误：下载的源码包结构异常。" >&2
  exit 1
fi

# ── 复制 skills ─────────────────────────────────────────────────
mkdir -p "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
echo "==> 安装 skills 到 $CLAUDE_SKILLS_DIR"
for skill in build-reference prd-distill; do
  src="$ARCHIVE_ROOT/plugins/$skill/skills/$skill"
  if [ -d "$src" ]; then
    rm -rf "$CLAUDE_SKILLS_DIR/$skill"
    cp -r "$src" "$CLAUDE_SKILLS_DIR/$skill"
    echo "    已安装 skill：$skill"
  else
    echo "    警告：源码包内未找到 $skill" >&2
  fi
done

# ── 复制命令 ────────────────────────────────────────────────────
COMMAND_SRC="$ARCHIVE_ROOT/.claude/commands/reference.md"
if [ -f "$COMMAND_SRC" ]; then
  cp "$COMMAND_SRC" "$CLAUDE_COMMANDS_DIR/reference.md"
  echo "    已安装命令：/reference"
fi

# ── 复制 doctor 脚本到本地 ────────────────────────────────────
DOCTOR_SRC="$ARCHIVE_ROOT/scripts/doctor.sh"
if [ -f "$DOCTOR_SRC" ]; then
  mkdir -p "$TARGET/.prd-tools"
  cp "$DOCTOR_SRC" "$TARGET/.prd-tools/doctor.sh"
  if [ -d "$ARCHIVE_ROOT/scripts/lib" ]; then
    mkdir -p "$TARGET/.prd-tools/lib"
    cp -r "$ARCHIVE_ROOT/scripts/lib/." "$TARGET/.prd-tools/lib/"
  fi
  chmod +x "$TARGET/.prd-tools/doctor.sh"
  echo "    已安装 doctor：$TARGET/.prd-tools/doctor.sh"
fi

# ── Version marker ────────────────────────────────────────────────
TOOL_VERSION="unknown"
[ -f "$ARCHIVE_ROOT/VERSION" ] && TOOL_VERSION="$(tr -d '[:space:]' < "$ARCHIVE_ROOT/VERSION")"
cat > "$TARGET/.prd-tools-version" <<EOF
version=$TOOL_VERSION
installed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
source=github.com/$REPO
branch=$BRANCH
EOF

# ── 完成 ────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "  prd-tools v$TOOL_VERSION skills 安装完成"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 检查外部依赖（uv / MarkItDown / Graphify / GitNexus / API Key）："
echo "       bash $TARGET/.prd-tools/doctor.sh"
echo "     按表里的 → 命令逐条修复，或直接交互式修："
echo "       bash $TARGET/.prd-tools/doctor.sh --fix"
echo ""
echo "  2. 关闭并重新打开 Claude Code，新 skills 才会加载。"
echo ""
echo "  3. 运行 /reference 构建项目知识库。"
echo ""
