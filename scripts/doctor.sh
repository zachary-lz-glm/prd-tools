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
echo "║        prd-tools  doctor                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. uv ─────────────────────────────────────────────────────────
if command -v uv &>/dev/null; then
  ok "uv" "$(uv --version 2>/dev/null | head -1) ($(command -v uv))"
else
  bad "uv" "not installed" "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ── 2. markitdown ─────────────────────────────────────────────────
if command -v markitdown &>/dev/null; then
  ok "markitdown" "$(command -v markitdown)"
else
  bad "markitdown" "not installed (PRD docx/pdf reading unavailable)" \
      'uv tool install "markitdown[all]" && uv tool install markitdown-ocr'
fi

# ── 3. graphify ───────────────────────────────────────────────────
if command -v graphify &>/dev/null; then
  ok "graphify" "$(command -v graphify) (package: graphifyy)"
else
  bad "graphify" "not installed (semantic graph unavailable)" \
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
  ok "gitnexus-rt" "$GN_RUNTIME available ($(command -v $GN_RUNTIME))"
  # Probe whether the gitnexus package can actually load. Do not block.
  if [ "$GN_RUNTIME" = "npx" ]; then
    if timeout 15 npx -y gitnexus@latest --version &>/dev/null; then
      ok "gitnexus" "package reachable via npm"
    else
      warn "gitnexus" "package fetch failed (network/registry?)" \
           "npx -y gitnexus@latest --version    # to see the error"
    fi
  fi
else
  bad "gitnexus-rt" "neither npx nor bunx in PATH" \
      "curl -fsSL https://bun.sh/install | bash    # or install Node.js"
fi

# ── 5. .mcp.json ──────────────────────────────────────────────────
MCP_FILE="$HOME/.claude/.mcp.json"
if [ -f "$MCP_FILE" ] && grep -q '"gitnexus"' "$MCP_FILE" 2>/dev/null; then
  ok "mcp-config" "gitnexus declared in $MCP_FILE"
else
  warn "mcp-config" "gitnexus NOT declared in $MCP_FILE" \
       "add the snippet printed at the bottom of this report"
fi

# ── 6. Vision API key ─────────────────────────────────────────────
if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then
  ok "api-key" "ANTHROPIC_AUTH_TOKEN set"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
  ok "api-key" "OPENAI_API_KEY set"
else
  bad "api-key" "no Vision key (PRD image OCR + graphify --mode deep disabled)" \
      "export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx    # add to ~/.zshrc to persist"
fi

# ── 7. proxy advisory ─────────────────────────────────────────────
if [ -n "${http_proxy:-${HTTP_PROXY:-}}" ]; then
  P="${http_proxy:-${HTTP_PROXY:-}}"
  if [[ "$P" == socks* ]]; then
    warn "proxy" "$P (curl-only; npm/uv don't honor SOCKS)" \
         "set an HTTP proxy or a PyPI/npm mirror if uv/npm fetches fail"
  else
    ok "proxy" "$P"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────
echo ""
if [ "$ISSUES" -eq 0 ]; then
  echo "  ${C_OK}All required tools available.${C_R}"
else
  echo "  ${C_BAD}$ISSUES issue(s) found.${C_R}"
fi
echo ""

# MCP snippet (always printed when missing) ------------------------
if [ ! -f "$MCP_FILE" ] || ! grep -q '"gitnexus"' "$MCP_FILE" 2>/dev/null; then
  cat <<'SNIP'
  Add this to ~/.claude/.mcp.json (merge into existing mcpServers):

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

# ── --fix interactive run ─────────────────────────────────────────
if [ "$FIX" -eq 1 ] && [ "${#FIXES[@]}" -gt 0 ]; then
  echo "  Fix mode: each command will be confirmed before running."
  echo ""
  for cmd in "${FIXES[@]}"; do
    echo "  $ $cmd"
    read -r -p "  run? [y/N] " ans </dev/tty || ans=""
    case "${ans:-N}" in
      y|Y) bash -c "$cmd" || echo "  ${C_BAD}command failed${C_R}" ;;
      *)   echo "  skipped" ;;
    esac
    echo ""
  done
fi

# ── exit code ─────────────────────────────────────────────────────
if [ "$STRICT" -eq 1 ] && [ "$ISSUES" -gt 0 ]; then
  exit 1
fi
exit 0
