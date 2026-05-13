#!/usr/bin/env bash
# install.sh — Install prd-tools skills into a target project.
#
# Scope: only what this repo OWNS (reference / prd-distill skills,
# version marker).
#
# See docs/adr/0008-安装脚本职责拆分.md for rationale.

set -euo pipefail

REPO="zachary-lz-glm/prd-tools"
BRANCH="${PRD_TOOLS_BRANCH:-v2.0}"
USE_REMOTE="${PRD_TOOLS_REMOTE:-0}"
TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

CLAUDE_SKILLS_DIR="$TARGET/.claude/skills"
CLAUDE_COMMANDS_DIR="$TARGET/.claude/commands"
GLOBAL_CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
PRD_TOOLS_DIR="$TARGET/.prd-tools"
PRD_TOOLS_SCRIPTS_DIR="$PRD_TOOLS_DIR/scripts"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          prd-tools 安装                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 选择源码 ────────────────────────────────────────────────────
if [ "$USE_REMOTE" != "1" ] && [ -d "$SCRIPT_DIR/plugins" ] && [ -f "$SCRIPT_DIR/VERSION" ]; then
  ARCHIVE_ROOT="$SCRIPT_DIR"
  echo "==> 使用本地 prd-tools checkout：$ARCHIVE_ROOT"
else
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
fi

# ── 复制 skills ─────────────────────────────────────────────────
mkdir -p "$CLAUDE_SKILLS_DIR"
echo "==> 安装 skills 到 $CLAUDE_SKILLS_DIR"
for skill in reference prd-distill; do
  src="$ARCHIVE_ROOT/plugins/$skill/skills/$skill"
  if [ -d "$src" ]; then
    rm -rf "$CLAUDE_SKILLS_DIR/$skill"
    cp -r "$src" "$CLAUDE_SKILLS_DIR/$skill"
    echo "    已安装 skill：$skill"
  else
    echo "    警告：源码包内未找到 $skill" >&2
  fi
done
if [ -d "$CLAUDE_SKILLS_DIR/build-reference" ]; then
  rm -rf "$CLAUDE_SKILLS_DIR/build-reference"
  echo "    已清理旧 skill：build-reference"
fi
if [ -d "$GLOBAL_CLAUDE_SKILLS_DIR/build-reference" ]; then
  rm -rf "$GLOBAL_CLAUDE_SKILLS_DIR/build-reference"
  echo "    已清理全局旧 skill：build-reference"
fi

# ── 复制运行时辅助脚本 ─────────────────────────────────────────
# Skills 在目标项目内执行，因此确定性辅助脚本也必须安装到目标项目。
mkdir -p "$PRD_TOOLS_SCRIPTS_DIR"
echo "==> 安装 runtime scripts 到 $PRD_TOOLS_SCRIPTS_DIR"
for script in _gate_fixhint.py build-index.py context-pack.py final-quality-gate.py reference-quality-gate.py distill-quality-gate.py reference-workflow-gate.py distill-workflow-gate.py render-reference-portal.py render-distill-portal.py distill-step-gate.py reference-step-gate.py workflow_state.py prd-coverage-gate.py validate-artifact.py team-reference-aggregate.py team-reference-inherit.py ingest-docx.py; do
  src="$ARCHIVE_ROOT/scripts/$script"
  if [ -f "$src" ]; then
    cp "$src" "$PRD_TOOLS_SCRIPTS_DIR/$script"
    chmod +x "$PRD_TOOLS_SCRIPTS_DIR/$script" 2>/dev/null || true
    echo "    已安装脚本：$script"
  else
    echo "    警告：源码包内未找到 scripts/$script" >&2
  fi
done

# ── 复制 portal 模板 ─────────────────────────────────────────────
# Portal HTML 由渲染脚本+模板生成，模板必须安装到目标项目。
mkdir -p "$PRD_TOOLS_DIR/assets"
echo "==> 安装 portal 模板到 $PRD_TOOLS_DIR/assets"
for skill in reference prd-distill; do
  src="$ARCHIVE_ROOT/plugins/$skill/skills/$skill/assets/portal-template.html"
  case "$skill" in
    reference) dst="reference-portal-template.html" ;;
    prd-distill) dst="distill-portal-template.html" ;;
  esac
  if [ -f "$src" ]; then
    cp "$src" "$PRD_TOOLS_DIR/assets/$dst"
    echo "    已安装模板：$dst (from $skill)"
  else
    echo "    警告：源码包内未找到 $skill/assets/portal-template.html" >&2
  fi
done

# ── 复制 slash command 兼容入口 ─────────────────────────────────
# Skills 是主入口；commands 是薄 wrapper，用于兼容不稳定触发 skill 的客户端/中转环境。
mkdir -p "$CLAUDE_COMMANDS_DIR"
echo "==> 安装 slash command wrappers 到 $CLAUDE_COMMANDS_DIR"
for command in reference prd-distill; do
  src="$ARCHIVE_ROOT/.claude/commands/$command.md"
  if [ -f "$src" ]; then
    cp "$src" "$CLAUDE_COMMANDS_DIR/$command.md"
    echo "    已安装命令：/$command"
  else
    echo "    警告：源码包内未找到 .claude/commands/$command.md" >&2
  fi
done

# ── Version marker ────────────────────────────────────────────────
TOOL_VERSION="unknown"
[ -f "$ARCHIVE_ROOT/VERSION" ] && TOOL_VERSION="$(tr -d '[:space:]' < "$ARCHIVE_ROOT/VERSION")"
cat > "$TARGET/.prd-tools-version" <<EOF
version=$TOOL_VERSION
installed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
source=github.com/$REPO
branch=$BRANCH
install_source=$([ "$ARCHIVE_ROOT" = "$SCRIPT_DIR" ] && echo "local" || echo "remote")
EOF

# ── 完成 ────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "  prd-tools v$TOOL_VERSION skills 安装完成"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 关闭并重新打开 Claude Code，新 skills 才会加载。"
echo ""
echo ""
echo "  2. 运行 /reference 构建项目知识库。"
echo ""
