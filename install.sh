#!/usr/bin/env bash
set -euo pipefail

REPO="zachary-lz-glm/prd-tools"
BRANCH="v2.0"
TARGET="${1:-.}"

# Resolve to absolute path
TARGET="$(cd "$TARGET" && pwd)"

CLAUDE_SKILLS_DIR="$TARGET/.claude/skills"
CLAUDE_CONFIG_DIR="$HOME/.claude"
TMP_DIR="$(mktemp -d)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        prd-tools  one-click install      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Proxy detection ────────────────────────────────────────────────

# Auto-detect system proxy for curl (critical in corporate networks)
if [ -z "${http_proxy:-}" ] && [ -z "${HTTP_PROXY:-}" ]; then
  # Check common macOS/Linux proxy configs
  _SYS_PROXY=""
  if [ -f "$HOME/.config/proxy" ]; then
    _SYS_PROXY="$(head -1 "$HOME/.config/proxy" 2>/dev/null)"
  fi
  # Try to detect proxy from networksetup (macOS)
  if [ -z "$_SYS_PROXY" ] && command -v networksetup &>/dev/null; then
    _SYS_PROXY="$(networksetup -getwebproxy Wi-Fi 2>/dev/null | awk '/Enabled: Yes/{getline; getline; print "http://"$2":"$1}' | head -1)"
    if [ -z "$_SYS_PROXY" ]; then
      _SYS_PROXY="$(networksetup -getwebproxy Ethernet 2>/dev/null | awk '/Enabled: Yes/{getline; getline; print "http://"$2":"$1}' | head -1)"
    fi
  fi
  if [ -n "$_SYS_PROXY" ]; then
    export http_proxy="$_SYS_PROXY"
    export https_proxy="$_SYS_PROXY"
    echo "  Auto-detected proxy: $_SYS_PROXY"
    echo ""
  fi
fi

# Ensure curl uses proxy
if [ -n "${http_proxy:-}" ] || [ -n "${HTTP_PROXY:-}" ]; then
  echo "  Using proxy: ${http_proxy:-${HTTP_PROXY:-set}}"
  echo ""
fi

# ── Status tracking ────────────────────────────────────────────────

MCP_CMD=""
MCP_ARGS=""
GITNEXUS_STATUS="missing"
GRAPHIFY_STATUS="missing"
MARKITDOWN_STATUS="missing"
GITNEXUS_INDEXED=false

# ── Step 1/7: Install uv (Python dependency manager) ───────────────

echo "==> [1/7] Checking uv (Python dependency manager)..."

if command -v uv &>/dev/null; then
  echo "    uv already installed: $(uv --version 2>/dev/null || echo 'ok')"
else
  echo "    Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if command -v uv &>/dev/null; then
    echo "    uv installed: $(uv --version)"
  else
    echo "    ERROR: uv installation failed." >&2
    echo "    Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
  fi
fi

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# ── Step 2/7: Install MarkItDown (document reader) ─────────────────

echo "==> [2/7] Checking MarkItDown (PDF/DOCX/PPTX reader)..."

if command -v markitdown &>/dev/null; then
  echo "    markitdown already installed"
  MARKITDOWN_STATUS="ok"
else
  echo "    Installing markitdown via uv (with OCR support)..."
  if ! uv tool install "markitdown[all]" 2>/dev/null; then
    echo "    WARNING: markitdown installation failed." >&2
  fi
  if ! uv tool install markitdown-ocr 2>/dev/null; then
    echo "    WARNING: markitdown-ocr installation failed; document conversion may still work without image OCR." >&2
  fi
  if command -v markitdown &>/dev/null; then
    echo "    markitdown installed (with OCR support)"
    MARKITDOWN_STATUS="ok"
  else
    echo "    WARNING: markitdown installation failed." >&2
    echo "    Install manually: uv tool install markitdown" >&2
  fi
fi

# ── Step 3/7: Install GitNexus runtime (npx or bun) ────────────────

echo "==> [3/7] Checking GitNexus runtime..."

if command -v npx &>/dev/null; then
  MCP_CMD="$(command -v npx)"
  MCP_ARGS='["-y","gitnexus@latest","mcp"]'
  echo "    npx available — GitNexus will use Node.js"
elif command -v bun &>/dev/null; then
  if command -v bunx &>/dev/null; then
    MCP_CMD="$(command -v bunx)"
    MCP_ARGS='["--bun","gitnexus@latest","mcp"]'
    echo "    bun available — GitNexus will use Bun"
  else
    echo "    WARNING: bun found but bunx is missing. GitNexus (graph) will not be available." >&2
  fi
else
  echo "    Neither npx nor bun found. Installing bun..."
  if curl -fsSL https://bun.sh/install | bash 2>/dev/null; then
    export PATH="$HOME/.bun/bin:$PATH"
    if command -v bunx &>/dev/null; then
      MCP_CMD="$(command -v bunx)"
      MCP_ARGS='["--bun","gitnexus@latest","mcp"]'
      echo "    bun installed — GitNexus will use Bun"
    else
      echo "    WARNING: bun installation completed but bunx is missing. GitNexus (graph) will not be available." >&2
    fi
  else
    echo "    WARNING: bun installation failed. GitNexus (graph) will not be available." >&2
    echo "    Install manually: curl -fsSL https://bun.sh/install | bash" >&2
  fi
fi

# ── Step 4/7: Install Graphify (knowledge graph) ────────────────────

echo "==> [4/7] Checking Graphify (knowledge graph)..."

GRAPHIFY_INSTALLED=false

if command -v graphify &>/dev/null; then
  echo "    graphify already installed (CLI command; official PyPI package is graphifyy)"
  GRAPHIFY_INSTALLED=true
else
  echo "    Installing Graphify via uv (official package: graphifyy, CLI: graphify)..."
  if ! uv tool install graphifyy 2>/dev/null; then
    echo "    WARNING: graphify installation failed." >&2
  fi
  if command -v graphify &>/dev/null; then
    echo "    graphify installed"
    GRAPHIFY_INSTALLED=true
  else
    echo "    WARNING: graphify installation failed." >&2
    echo "    Install manually: uv tool install graphifyy" >&2
  fi
fi

if [ "$GRAPHIFY_INSTALLED" = true ]; then
  graphify install 2>/dev/null && echo "    Graphify skill registered" || echo "    WARNING: graphify install failed (skill not registered)" >&2
  GRAPHIFY_STATUS="ok"
fi

# ── Step 5/7: Download and install prd-tools skills ────────────────

echo "==> [5/7] Downloading prd-tools..."

ARCHIVE_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"

if ! curl -fsSL --connect-timeout 10 --max-time 60 "$ARCHIVE_URL" | tar -xz -C "$TMP_DIR" 2>/dev/null; then
  echo "" >&2
  echo "ERROR: Download from GitHub failed (network issue?)" >&2
  echo "" >&2
  echo "Fallback — clone via git and install locally:" >&2
  echo "  git clone --depth 1 https://github.com/$REPO.git /tmp/prd-tools" >&2
  echo "  cp -r /tmp/prd-tools/plugins/*/skills/* $CLAUDE_SKILLS_DIR/" >&2
  exit 1
fi

mkdir -p "$CLAUDE_SKILLS_DIR"

ARCHIVE_ROOT="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"
if [ -z "$ARCHIVE_ROOT" ] || [ ! -d "$ARCHIVE_ROOT/plugins" ]; then
  echo "ERROR: Downloaded archive has unexpected structure." >&2
  exit 1
fi

SRC_DIR="$ARCHIVE_ROOT/plugins"
VERSION_FILE="$ARCHIVE_ROOT/VERSION"
TOOL_VERSION="unknown"
if [ -f "$VERSION_FILE" ]; then
  TOOL_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
fi

for skill in build-reference prd-distill; do
  src="$SRC_DIR/$skill/skills/$skill"
  if [ -d "$src" ]; then
    dst="$CLAUDE_SKILLS_DIR/$skill"
    rm -rf "$dst"
    cp -r "$src" "$dst"
    echo "    Installed: $skill"
  else
    echo "    WARNING: $skill not found in archive" >&2
  fi
done

# Write version marker
cat > "$TARGET/.prd-tools-version" <<EOF
version=$TOOL_VERSION
installed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
source=github.com/$REPO
branch=$BRANCH
runtime_uv=$(command -v uv 2>/dev/null || echo "not_found")
runtime_gitnexus=$MCP_CMD
runtime_graphify=$(command -v graphify 2>/dev/null || echo "not_found")
runtime_graphify_package=graphifyy
runtime_markitdown=$(command -v markitdown 2>/dev/null || echo "not_found")
EOF

# ── Step 6/7: Configure GitNexus MCP + Index project ───────────────

echo "==> [6/7] Configuring GitNexus and indexing project..."

# Configure MCP server
if [ -n "$MCP_CMD" ]; then
  MCP_CONFIG="$CLAUDE_CONFIG_DIR/.mcp.json"

  if [ -f "$MCP_CONFIG" ]; then
    python3 -c "
import json, sys
try:
    with open('$MCP_CONFIG') as f:
        config = json.load(f)
except:
    config = {}
if 'mcpServers' not in config:
    config['mcpServers'] = {}
_gitnexus_env = {}
if '$MCP_CMD'.endswith('npx'):
    _gitnexus_env['npm_config_registry'] = 'https://registry.npmjs.org'
config['mcpServers']['gitnexus'] = {
    'command': '$MCP_CMD',
    'args': $MCP_ARGS,
    'env': _gitnexus_env
}
with open('$MCP_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
print('    Configured: gitnexus MCP server ($MCP_CMD)')
" 2>/dev/null || echo "    WARNING: Could not update $MCP_CONFIG. Add gitnexus manually." >&2
  else
    mkdir -p "$CLAUDE_CONFIG_DIR"
    if [[ "$MCP_CMD" == *npx ]]; then
      cat > "$MCP_CONFIG" <<MCPJSON
{
  "mcpServers": {
    "gitnexus": {
      "command": "$MCP_CMD",
      "args": $MCP_ARGS,
      "env": {"npm_config_registry": "https://registry.npmjs.org"}
    }
  }
}
MCPJSON
    else
      cat > "$MCP_CONFIG" <<MCPJSON
{
  "mcpServers": {
    "gitnexus": {
      "command": "$MCP_CMD",
      "args": $MCP_ARGS
    }
  }
}
MCPJSON
    fi
    echo "    Created: $MCP_CONFIG (gitnexus via $MCP_CMD)"
  fi
else
  echo "    Skipped MCP config: No GitNexus runtime available"
fi

# GitNexus: full code structure graph (AST-based)
if [ -n "$MCP_CMD" ] && [ -d "$TARGET/.git" ]; then
  echo "    Indexing with GitNexus (AST-based code structure)..."
  if [[ "$MCP_CMD" == *npx ]]; then
    if npm_config_registry=https://registry.npmjs.org "$MCP_CMD" -y gitnexus@latest analyze "$TARGET" 2>&1 | tail -5; then
      echo "    GitNexus: code structure indexed"
      GITNEXUS_INDEXED=true
      GITNEXUS_STATUS="ok"
    else
      echo "    WARNING: GitNexus indexing failed" >&2
    fi
  elif [[ "$MCP_CMD" == *bunx ]]; then
    if "$MCP_CMD" --bun gitnexus@latest analyze "$TARGET" 2>&1 | tail -5; then
      echo "    GitNexus: code structure indexed"
      GITNEXUS_INDEXED=true
      GITNEXUS_STATUS="ok"
    else
      echo "    WARNING: GitNexus indexing failed" >&2
    fi
  fi
elif [ -z "$MCP_CMD" ]; then
  echo "    GitNexus skipped: no runtime available"
else
  echo "    GitNexus skipped: not a git repo"
fi

# Graphify: code structure extraction (no LLM; full business graph via /graphify in Claude Code)
if [ "$GRAPHIFY_INSTALLED" = true ] && [ -d "$TARGET/.git" ]; then
  echo "    Extracting code structure with Graphify..."
  if graphify update "$TARGET" 2>/dev/null; then
    echo "    Graphify: code structure extracted (run /graphify in Claude Code for LLM-enhanced business graph)"
  else
    echo "    Graphify: structure extraction failed (run /graphify in Claude Code for full graph)"
  fi
fi

# ── Step 7/7: Health check + API key ───────────────────────────────

echo "==> [7/7] Health check..."

echo ""
echo "========================================="
echo "  prd-tools v$TOOL_VERSION installed!"
echo "========================================="
echo ""
echo "Runtime:"
echo "  uv:         $(command -v uv 2>/dev/null || echo 'NOT FOUND')"
GITNEXUS_LABEL="${MCP_CMD:-NOT CONFIGURED}"
[ "$GITNEXUS_INDEXED" = true ] && GITNEXUS_LABEL="${GITNEXUS_LABEL} (indexed)"
echo "  GitNexus:   $GITNEXUS_LABEL"
echo "  Graphify:   $(command -v graphify 2>/dev/null || echo 'NOT FOUND')"
echo "  MarkItDown: $(command -v markitdown 2>/dev/null || echo 'NOT FOUND')"
echo ""
echo "Skills:"
echo "  /build-reference  —  Build domain knowledge (with graph)"
echo "  /prd-distill      —  Distill PRD document (with Vision)"
echo "  /graphify         —  Knowledge graph from code/docs"
echo ""

# Report issues
ISSUES=0

# Check API keys for LLM Vision (PRD image OCR and Graphify deep semantic graph)
VISION_KEY=""

if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then
  VISION_KEY="ANTHROPIC_AUTH_TOKEN"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
  VISION_KEY="OPENAI_API_KEY"
fi

if [ "$GITNEXUS_STATUS" != "ok" ]; then
  ISSUES=$((ISSUES + 1))
  echo "  ❌ GitNexus: FAILED — code structure graph unavailable"
  if [ -z "$MCP_CMD" ]; then
    echo "     Fix: curl -fsSL https://bun.sh/install | bash && rerun install.sh"
  else
    echo "     Fix: rerun install.sh to retry indexing"
  fi
fi

if [ "$GRAPHIFY_STATUS" != "ok" ]; then
  ISSUES=$((ISSUES + 1))
  echo "  ❌ Graphify: FAILED — business semantic graph unavailable"
  echo "     Fix: uv tool install graphifyy"
fi

if [ "$MARKITDOWN_STATUS" != "ok" ]; then
  ISSUES=$((ISSUES + 1))
  echo "  ❌ MarkItDown: FAILED — PRD document reading (PDF/DOCX/PPTX) unavailable"
  echo "     Fix: uv tool install markitdown"
fi

if [ "$ISSUES" -gt 0 ]; then
  echo ""
  echo "  ⚠️  $ISSUES tool(s) failed. prd-tools will work but with reduced capability."
  echo "     Fix the issues above and rerun: bash install.sh $TARGET"
  echo ""
fi

# API key check — interactive prompt for LLM Vision (PRD image OCR and Graphify deep semantic graph)
if [ -z "$VISION_KEY" ]; then
  echo "  ⚠️  No API key found for LLM Vision."
  echo "     PRD image OCR and Graphify deep semantic extraction may be disabled."
  echo "     PRD images will be marked as 'needs_vision_or_human_review'."
  echo ""
  echo "  Step 7 can save an ANTHROPIC_AUTH_TOKEN now, or you can skip and set it later:"
  echo "     export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx"
  echo "     # If PRD image OCR uses an OpenAI-compatible vision endpoint, also set:"
  echo "     export ANTHROPIC_BASE_URL=https://your-provider.example/v1"
  echo "     # Or use OPENAI_API_KEY / OPENAI_BASE_URL instead."
  echo ""
  USER_ANTHROPIC_TOKEN=""
  if [ -t 0 ]; then
    read -p "  Enter ANTHROPIC_AUTH_TOKEN (or press Enter to skip): " USER_ANTHROPIC_TOKEN
  else
    echo "  Non-interactive shell detected; skipping API key prompt."
    echo ""
  fi
  if [ -n "$USER_ANTHROPIC_TOKEN" ]; then
    export ANTHROPIC_AUTH_TOKEN="$USER_ANTHROPIC_TOKEN"
    # Persist to shell profile
    PROFILE_FILE=""
    if [ -f "$HOME/.zshrc" ]; then
      PROFILE_FILE="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
      PROFILE_FILE="$HOME/.bashrc"
    fi
    if [ -n "$PROFILE_FILE" ]; then
      sed -i.bak '/^export ANTHROPIC_AUTH_TOKEN=/d' "$PROFILE_FILE" 2>/dev/null
      echo "export ANTHROPIC_AUTH_TOKEN=\"$USER_ANTHROPIC_TOKEN\"" >> "$PROFILE_FILE"
      rm -f "$PROFILE_FILE.bak"
      echo "  ✅ ANTHROPIC_AUTH_TOKEN saved to $PROFILE_FILE"
    fi
    echo "  ℹ️  LLM Vision / Graphify deep extraction can use ANTHROPIC_AUTH_TOKEN"
    echo ""
  else
    echo "  Skipped. Set later with: export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx"
    echo ""
  fi
else
  echo "  ℹ️  LLM Vision / Graphify deep extraction can use $VISION_KEY"
  echo ""
fi

# Final summary
TOOLS_OK=true
[ "$GITNEXUS_STATUS" != "ok" ] && TOOLS_OK=false
[ "$GRAPHIFY_STATUS" != "ok" ] && TOOLS_OK=false
[ "$MARKITDOWN_STATUS" != "ok" ] && TOOLS_OK=false

if [ "$TOOLS_OK" = true ]; then
  echo "  ✅ All tools installed. Ready to use /build-reference and /prd-distill."
  echo ""
fi

# Write a human-readable runtime contract so users can see which enhanced
# capabilities are active before they run the skills.
GRAPHIFY_HTML="$TARGET/graphify-out/graph.html"
GRAPHIFY_REPORT="$TARGET/graphify-out/GRAPH_REPORT.md"
GITNEXUS_INDEX="$TARGET/.gitnexus"
cat > "$TARGET/.prd-tools-runtime.yaml" <<EOF
schema_version: "1.0"
generated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
target: "$TARGET"
tools:
  markitdown:
    status: "$MARKITDOWN_STATUS"
    command: "$(command -v markitdown 2>/dev/null || echo "not_found")"
    purpose: "PRD document conversion; image OCR requires a vision-capable API key"
  gitnexus:
    status: "$GITNEXUS_STATUS"
    command: "${MCP_CMD:-not_configured}"
    indexed: $GITNEXUS_INDEXED
    index_path: "$GITNEXUS_INDEX"
    purpose: "code graph, call chains, impact analysis"
  graphify:
    status: "$GRAPHIFY_STATUS"
    package: "graphifyy"
    command: "$(command -v graphify 2>/dev/null || echo "not_found")"
    graph_path: "$TARGET/graphify-out/graph.json"
    visual_page: "$GRAPHIFY_HTML"
    report: "$GRAPHIFY_REPORT"
    purpose: "business semantic graph from code, docs, screenshots, diagrams"
next_steps:
  - "Close and reopen Claude Code to activate GitNexus MCP from ~/.claude/.mcp.json."
  - "If you skipped Step 7 API key input, set ANTHROPIC_AUTH_TOKEN before running /prd-distill on image-heavy PRDs or /graphify . --mode deep."
  - "Run /build-reference to generate _reference/ and _output/graph/GRAPH_STATUS.md."
  - "Run /graphify . --mode deep when you want the full LLM-enhanced business graph."
EOF

echo "  Runtime status written: $TARGET/.prd-tools-runtime.yaml"
if [ -f "$GRAPHIFY_HTML" ]; then
  echo "  Graphify visual page: $GRAPHIFY_HTML"
elif [ "$GRAPHIFY_STATUS" = "ok" ]; then
  echo "  Graphify visual page will appear after: /graphify . --mode deep"
  echo "     Expected path: $GRAPHIFY_HTML"
fi

# Restart reminder
echo "  ⚡ IMPORTANT: Close and reopen Claude Code to activate GitNexus MCP server."
echo "     MCP config was written to ~/.claude/.mcp.json."
echo "     After reopening, /build-reference and /prd-distill can use GitNexus MCP tools."
echo ""
echo "  🔑 API key note:"
echo "     PRD image OCR and Graphify deep semantic extraction need a vision-capable key."
echo "     Step 7 accepts ANTHROPIC_AUTH_TOKEN interactively; otherwise set it before use:"
echo "       export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx"
echo "     For OpenAI-compatible vision endpoints, also set ANTHROPIC_BASE_URL or use OPENAI_API_KEY."
echo ""
