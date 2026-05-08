#!/usr/bin/env bash
# doctor.sh — Diagnose prd-tools external dependencies. Reports only.
#
# Modes:
#   (default)         report status, exit 0 regardless
#   --strict          exit 1 if any required check fails
#   --strict-all      exit 1 if required or enhanced checks fail
#   --fix             interactively run fix commands (each confirmed)
#
# Checks: installed skills, legacy command aliases, uv, markitdown,
#         runtime, Vision API key, proxy hint, project graph.
#
# See docs/adr/0008-安装脚本职责拆分.md.

set -uo pipefail

STRICT=0
STRICT_ALL=0
FIX=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --strict-all) STRICT=1; STRICT_ALL=1 ;;
    --fix)    FIX=1 ;;
    -h|--help)
      sed -n '1,15p' "$0"; exit 0 ;;
  esac
done

# ── colors ────────────────────────────────────────────────────────
if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_BAD=$'\033[31m'; C_WARN=$'\033[33m'; C_DIM=$'\033[2m'; C_R=$'\033[0m'
else
  C_OK=""; C_BAD=""; C_WARN=""; C_DIM=""; C_R=""
fi

ISSUES=0
ENHANCEMENTS=0
declare -a FIXES=()

ok()    { printf "  %s✅%s %-12s %s\n"  "$C_OK"  "$C_R" "$1" "$2"; }
bad()   { printf "  %s❌%s %-12s %s\n"  "$C_BAD" "$C_R" "$1" "$2"; ISSUES=$((ISSUES+1)); [ -n "${3:-}" ] && FIXES+=("$3") && printf "  %s   → %s%s\n" "$C_DIM" "$3" "$C_R"; }
warn()  { printf "  %s⚠️%s  %-12s %s\n" "$C_WARN" "$C_R" "$1" "$2"; [ -n "${3:-}" ] && printf "  %s   → %s%s\n" "$C_DIM" "$3" "$C_R"; }
enhance(){ printf "  %s⚠️%s  %-12s %s\n" "$C_WARN" "$C_R" "$1" "$2"; ENHANCEMENTS=$((ENHANCEMENTS+1)); [ -n "${3:-}" ] && FIXES+=("$3") && printf "  %s   → %s%s\n" "$C_DIM" "$3" "$C_R"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          prd-tools 依赖诊断              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "必需项："

# ── 1. local install ──────────────────────────────────────────────
GLOBAL_LEGACY_SKILL="$HOME/.claude/skills/build-reference"

if [ -f ".prd-tools-version" ]; then
  ok "version" "$(head -1 .prd-tools-version 2>/dev/null)"
else
  warn "version" "未发现 .prd-tools-version（可能未通过 install.sh 安装）"
fi

if [ -d ".claude/skills/reference" ] && [ -d ".claude/skills/prd-distill" ]; then
  ok "skills" "reference / prd-distill 已安装（/reference 由 skill name 提供）"
else
  if [ -d ".claude/skills/build-reference" ]; then
    bad "skills" "检测到旧 skill 目录 build-reference，请重新安装迁移到 reference" \
        "重新运行 prd-tools install.sh"
  else
    bad "skills" "缺少 .claude/skills/reference 或 prd-distill" \
        "重新运行 prd-tools install.sh"
  fi
fi

if [ -f ".claude/commands/reference.md" ]; then
  warn "command" "检测到旧命令 alias：.claude/commands/reference.md，可删除；/reference 由 skill name 提供" \
       "rm -f .claude/commands/reference.md && rmdir .claude/commands 2>/dev/null || true"
else
  ok "command" "未发现旧 .claude/commands/reference.md alias"
fi

if [ -f ".prd-tools/status.sh" ]; then
  ok "status" ".prd-tools/status.sh 已安装"
else
  warn "status" "未发现 .prd-tools/status.sh（可选 dashboard 生成器）" \
       "重新运行 prd-tools install.sh"
fi

if [ -d "$GLOBAL_LEGACY_SKILL" ]; then
  bad "legacy" "检测到全局旧 skill：$GLOBAL_LEGACY_SKILL，会让 /build-reference 继续可用" \
      "rm -rf '$GLOBAL_LEGACY_SKILL'"
else
  ok "legacy" "未发现全局 build-reference 旧 skill"
fi

# ── 2. uv ─────────────────────────────────────────────────────────
if command -v uv &>/dev/null; then
  ok "uv" "$(uv --version 2>/dev/null | head -1) ($(command -v uv))"
else
  bad "uv" "未安装" "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

echo ""
echo "增强项："

# ── 3. markitdown ─────────────────────────────────────────────────
if command -v markitdown &>/dev/null; then
  ok "markitdown" "$(command -v markitdown)"
else
  enhance "markitdown" "未安装（只能稳定处理 md/txt 或粘贴文本）" \
          'uv tool install --upgrade "markitdown[all]" --with markitdown-ocr    # ocr 是插件，要用 --with'
fi

# ── 4. Vision API key ─────────────────────────────────────────────
if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then
  ok "api-key" "ANTHROPIC_AUTH_TOKEN 已设置"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
  ok "api-key" "OPENAI_API_KEY 已设置"
else
  enhance "api-key" "未配置 Vision Key（MarkItDown OCR 不可用）" \
          "export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx    # 加到 ~/.zshrc 持久化"
fi

# ── 5. project graph readiness ────────────────────────────────────
echo ""
echo "项目就绪度："

if [ -d "_prd-tools/reference" ]; then
  ok "reference" "_prd-tools/reference 已存在"
else
  warn "reference" "还没有项目知识库" \
       "/reference"
fi

# ── 6. uv mirror (SOCKS proxy env) ────────────────────────────────
# SOCKS proxy only works for curl; npm/uv do not support SOCKS.
# uv: needs a PyPI mirror to install markitdown without proxy.

if [ -n "${http_proxy:-${HTTP_PROXY:-}}" ]; then
  P="${http_proxy:-${HTTP_PROXY:-}}"
  if [[ "$P" == socks* ]]; then
    if [ -f "$HOME/.config/uv/uv.toml" ] && grep -q 'aliyun\.\|tuna\.\|pypi\.org/simple' "$HOME/.config/uv/uv.toml" 2>/dev/null; then
      MIRROR_UV=1
    elif [ -n "${UV_INDEX_URL:-}" ]; then
      MIRROR_UV=1
    else
      MIRROR_UV=0
    fi

    if [ "$MIRROR_UV" -eq 1 ]; then
      ok "uv-mirror" "PyPI mirror configured (SOCKS proxy bypassed)"
    else
      warn "uv-mirror" "SOCKS proxy (${P}) does not work with uv; PyPI mirror not configured"
      FIXES+=("mkdir -p ~/.config/uv && cat > ~/.config/uv/uv.toml << 'UV_EOF'\n[[index]]\nurl = \"https://mirrors.aliyun.com/pypi/simple\"\ndefault = true\nUV_EOF")
      printf "  %s   -> mkdir -p ~/.config/uv && cat > ~/.config/uv/uv.toml << 'EOF'\n      [[index]]\n      url = \"https://mirrors.aliyun.com/pypi/simple\"\n      default = true\n      EOF%s\n" "$C_DIM" "$C_R"
    fi
  else
    ok "proxy" "$P"
  fi
fi

# ── 汇总 ──────────────────────────────────────────────────────────
echo ""
if [ "$ISSUES" -eq 0 ]; then
  echo "  ${C_OK}必需项已就绪。${C_R}"
  if [ "$ENHANCEMENTS" -gt 0 ]; then
    echo "  ${C_WARN}${ENHANCEMENTS} 项增强能力未就绪；基础流程仍可运行，会按能力降级。${C_R}"
  fi
  echo ""
  echo "  ${C_DIM}下一步：${C_R}"
  echo "  ${C_DIM}1. 关闭并重新打开 Claude Code，新 skills 才会加载${C_R}"
  echo "  ${C_DIM}2. /reference                 # 构建项目知识库${C_R}"
  echo "  ${C_DIM}3. /prd-distill               # 蒸馏 PRD -> plan + tasks${C_R}"
  echo "  ${C_DIM}4. bash .prd-tools/status.sh  # 生成 _prd-tools/STATUS.md + dashboard${C_R}"
else
  echo "  ${C_BAD}发现 $ISSUES 项需要修复。${C_R}"
  echo "  可执行：bash $0 --fix    # 交互式逐条修"
fi
echo ""

# ── --fix 交互式修复 ──────────────────────────────────────────────
if [ "$FIX" -eq 1 ] && [ "${#FIXES[@]}" -gt 0 ]; then
  echo "  修复模式：每条命令会先确认。"
  echo ""
  for cmd in "${FIXES[@]}"; do
    echo "  $ $cmd"
    read -r -p "  执行？[y/N] " ans </dev/tty || ans=""
    case "${ans:-N}" in
      y|Y) bash -c "$cmd" || echo "  ${C_BAD}命令执行失败${C_R}" ;;
      *)   echo "  跳过" ;;
    esac
    echo ""
  done
fi

# ── exit code ─────────────────────────────────────────────────────
if [ "$STRICT" -eq 1 ] && [ "$ISSUES" -gt 0 ]; then
  exit 1
fi
if [ "$STRICT_ALL" -eq 1 ] && [ "$ENHANCEMENTS" -gt 0 ]; then
  exit 1
fi
exit 0
