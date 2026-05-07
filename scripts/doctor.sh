#!/usr/bin/env bash
# doctor.sh — Diagnose prd-tools external dependencies. Reports only.
#
# Modes:
#   (default)         report status, exit 0 regardless
#   --strict          exit 1 if any check fails
#   --fix             interactively run fix commands (each confirmed)
#
# Checks: uv, markitdown, graphify, gitnexus runtime, Vision API key,
#         proxy hint, .mcp.json status.
#
# See docs/adr/0008-安装脚本职责拆分.md.

set -uo pipefail

STRICT=0
FIX=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
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
declare -a FIXES=()

ok()    { printf "  %s✅%s %-12s %s\n"  "$C_OK"  "$C_R" "$1" "$2"; }
bad()   { printf "  %s❌%s %-12s %s\n"  "$C_BAD" "$C_R" "$1" "$2"; ISSUES=$((ISSUES+1)); [ -n "${3:-}" ] && FIXES+=("$3") && printf "  %s   → %s%s\n" "$C_DIM" "$3" "$C_R"; }
warn()  { printf "  %s⚠️%s  %-12s %s\n" "$C_WARN" "$C_R" "$1" "$2"; [ -n "${3:-}" ] && printf "  %s   → %s%s\n" "$C_DIM" "$3" "$C_R"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          prd-tools 依赖诊断              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. uv ─────────────────────────────────────────────────────────
if command -v uv &>/dev/null; then
  ok "uv" "$(uv --version 2>/dev/null | head -1) ($(command -v uv))"
else
  bad "uv" "未安装" "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ── 2. markitdown ─────────────────────────────────────────────────
if command -v markitdown &>/dev/null; then
  ok "markitdown" "$(command -v markitdown)"
else
  bad "markitdown" "未安装（PRD 的 docx/pdf 无法解析）" \
      'uv tool install "markitdown[all]" && uv tool install markitdown-ocr'
fi

# ── 3. graphify ───────────────────────────────────────────────────
if command -v graphify &>/dev/null; then
  ok "graphify" "$(command -v graphify)（包名 graphifyy）"
else
  bad "graphify" "未安装（业务语义图谱不可用）" \
      "uv tool install graphifyy && graphify install"
fi

# ── 4. gitnexus runtime ───────────────────────────────────────────
GN_RUNTIME=""
if command -v npx &>/dev/null; then
  GN_RUNTIME="npx"
elif command -v bunx &>/dev/null; then
  GN_RUNTIME="bunx"
fi

if [ -n "$GN_RUNTIME" ]; then
  ok "gitnexus-rt" "$GN_RUNTIME 可用（$(command -v $GN_RUNTIME)）"
  if [ "$GN_RUNTIME" = "npx" ]; then
    if timeout 15 npx -y gitnexus@latest --version &>/dev/null; then
      ok "gitnexus" "npm 可拉到 gitnexus 包"
    else
      warn "gitnexus" "拉包探测失败（网络/registry 问题，但不阻断使用）" \
           "npx -y gitnexus@latest --version    # 看具体报错"
    fi
  fi
else
  bad "gitnexus-rt" "PATH 中既没有 npx 也没有 bunx" \
      "curl -fsSL https://bun.sh/install | bash    # 或安装 Node.js"
fi

# ── 5. .mcp.json ──────────────────────────────────────────────────
MCP_FILE="$HOME/.claude/.mcp.json"
if [ -f "$MCP_FILE" ] && grep -q '"gitnexus"' "$MCP_FILE" 2>/dev/null; then
  ok "mcp-config" "$MCP_FILE 已声明 gitnexus"
else
  warn "mcp-config" "$MCP_FILE 未声明 gitnexus" \
       "把下方 JSON 片段合并进去"
fi

# ── 6. Vision API key ─────────────────────────────────────────────
if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then
  ok "api-key" "ANTHROPIC_AUTH_TOKEN 已设置"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
  ok "api-key" "OPENAI_API_KEY 已设置"
else
  bad "api-key" "未配置 Vision Key（PRD 图片 OCR 和 graphify --mode deep 不可用）" \
      "export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx    # 加到 ~/.zshrc 持久化"
fi

# ── 7. proxy advisory ─────────────────────────────────────────────
if [ -n "${http_proxy:-${HTTP_PROXY:-}}" ]; then
  P="${http_proxy:-${HTTP_PROXY:-}}"
  if [[ "$P" == socks* ]]; then
    warn "proxy" "$P（仅对 curl 生效，npm/uv 不走 SOCKS）" \
         "如果 uv/npm 拉包失败，改用 HTTP 代理或配 PyPI/npm 镜像"
  else
    ok "proxy" "$P"
  fi
fi

# ── 汇总 ──────────────────────────────────────────────────────────
echo ""
if [ "$ISSUES" -eq 0 ]; then
  echo "  ${C_OK}所有必需工具已就绪。${C_R}"
else
  echo "  ${C_BAD}发现 $ISSUES 项需要修复。${C_R}"
  echo "  可执行：bash $0 --fix    # 交互式逐条修"
fi
echo ""

# MCP snippet（缺失时打印） ----------------------------------------
if [ ! -f "$MCP_FILE" ] || ! grep -q '"gitnexus"' "$MCP_FILE" 2>/dev/null; then
  cat <<'SNIP'
  把下面的内容合并到 ~/.claude/.mcp.json（注意 mcpServers 已存在则合并而非覆盖）：

  {
    "mcpServers": {
      "gitnexus": {
        "command": "npx",
        "args": ["-y", "gitnexus@latest", "mcp"],
        "env": {"npm_config_registry": "https://registry.npmjs.org"}
      }
    }
  }

SNIP
fi

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
exit 0
