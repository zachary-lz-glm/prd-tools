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

# ── Step 1: Install uv (Python dependency manager) ────────────────

echo "==> [1/5] Checking uv (Python dependency manager)..."

if command -v uv &>/dev/null; then
  echo "    uv already installed: $(uv --version 2>/dev/null || echo 'ok')"
else
  echo "    Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
  # Source the shell env so uv is available in this script
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

# ── Step 2: Install GitNexus runtime (npx or bun) ────────────────

echo "==> [2/5] Checking GitNexus runtime..."

MCP_CMD=""
MCP_ARGS=""

if command -v npx &>/dev/null; then
  MCP_CMD="npx"
  MCP_ARGS='["-y","gitnexus@latest","serve","--mcp"]'
  echo "    npx available — GitNexus will use Node.js"
elif command -v bun &>/dev/null; then
  MCP_CMD="bunx"
  MCP_ARGS='["--bun","gitnexus@latest","mcp"]'
  echo "    bun available — GitNexus will use Bun"
else
  echo "    Neither npx nor bun found. Installing bun..."
  curl -fsSL https://bun.sh/install | bash 2>/dev/null
  export PATH="$HOME/.bun/bin:$PATH"
  if command -v bun &>/dev/null; then
    MCP_CMD="bunx"
    MCP_ARGS='["--bun","gitnexus@latest","mcp"]'
    echo "    bun installed — GitNexus will use Bun"
  else
    echo "    WARNING: bun installation failed. GitNexus (graph) will not be available." >&2
    echo "    Install manually: curl -fsSL https://bun.sh/install | bash" >&2
  fi
fi

# ── Step 3: Install Graphify (knowledge graph) ────────────────────

echo "==> [3/5] Checking Graphify (knowledge graph)..."

GRAPHIFY_INSTALLED=false

if command -v graphify &>/dev/null; then
  echo "    graphify already installed"
  GRAPHIFY_INSTALLED=true
else
  echo "    Installing graphify via uv..."
  uv tool install graphifyy 2>/dev/null
  if command -v graphify &>/dev/null; then
    echo "    graphify installed"
    GRAPHIFY_INSTALLED=true
  else
    echo "    WARNING: graphify installation failed." >&2
    echo "    Install manually: uv tool install graphifyy" >&2
  fi
fi

if [ "$GRAPHIFY_INSTALLED" = true ]; then
  # graphify install creates ~/.claude/skills/graphify/SKILL.md and registers in CLAUDE.md
  graphify install 2>/dev/null && echo "    Graphify skill registered" || echo "    WARNING: graphify install failed (skill not registered)" >&2
fi

# ── Step 4: Download and install prd-tools skills ────────────────

echo "==> [4/5] Downloading prd-tools..."

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

SRC_DIR="$TMP_DIR/prd-tools-2.0/plugins"
VERSION_FILE="$TMP_DIR/prd-tools-2.0/VERSION"
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
EOF

# ── Step 5: Configure GitNexus MCP server ─────────────────────────

echo "==> [5/5] Configuring GitNexus MCP server..."

if [ -n "$MCP_CMD" ]; then
  MCP_CONFIG="$CLAUDE_CONFIG_DIR/.mcp.json"

  # Read existing config or start fresh
  if [ -f "$MCP_CONFIG" ]; then
    # Merge gitnexus into existing config (preserve other servers)
    python3 -c "
import json, sys
try:
    with open('$MCP_CONFIG') as f:
        config = json.load(f)
except:
    config = {}
if 'mcpServers' not in config:
    config['mcpServers'] = {}
config['mcpServers']['gitnexus'] = {
    'command': '$MCP_CMD',
    'args': $MCP_ARGS
}
with open('$MCP_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
print('    Configured: gitnexus MCP server ($MCP_CMD)')
" 2>/dev/null || echo "    WARNING: Could not update $MCP_CONFIG. Add gitnexus manually." >&2
  else
    # Create new config
    mkdir -p "$CLAUDE_CONFIG_DIR"
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
    echo "    Created: $MCP_CONFIG (gitnexus via $MCP_CMD)"
  fi
else
  echo "    Skipped: No GitNexus runtime available"
fi

# ── Done ──────────────────────────────────────────────────────────

echo ""
echo "========================================="
echo "  prd-tools v$TOOL_VERSION installed!"
echo "========================================="
echo ""
echo "Runtime:"
echo "  uv:         $(command -v uv 2>/dev/null || echo 'NOT FOUND')"
echo "  GitNexus:   ${MCP_CMD:-NOT CONFIGURED}"
echo "  Graphify:   $(command -v graphify 2>/dev/null || echo 'NOT FOUND')"
echo ""
echo "Skills:"
echo "  /build-reference  —  Build domain knowledge (with graph)"
echo "  /prd-distill      —  Distill PRD document (with Vision)"
echo "  /graphify         —  Knowledge graph from code/docs"
echo ""
echo "Image analysis:"
echo "  Set OPENAI_API_KEY or ANTHROPIC_AUTH_TOKEN to enable LLM Vision"
echo ""
