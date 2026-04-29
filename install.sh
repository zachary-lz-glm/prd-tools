#!/usr/bin/env bash
set -euo pipefail

REPO="zachary-lz-glm/prd-tools"
BRANCH="main"
TARGET="${1:-.}"

# Resolve to absolute path
TARGET="$(cd "$TARGET" && pwd)"

CLAUDE_SKILLS_DIR="$TARGET/.claude/skills"
TMP_DIR="$(mktemp -d)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "==> Installing prd-tools skills to: $TARGET"

# Download archive
echo "==> Downloading from GitHub..."
ARCHIVE_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"

if ! curl -fsSL --connect-timeout 10 --max-time 60 "$ARCHIVE_URL" | tar -xz -C "$TMP_DIR" 2>/dev/null; then
  echo ""
  echo "ERROR: Download from GitHub failed (network issue?)" >&2
  echo "" >&2
  echo "Fallback — clone via git and install locally:" >&2
  echo "  git clone --depth 1 https://github.com/$REPO.git /tmp/prd-tools" >&2
  echo "  mkdir -p \"\$PWD/.claude/skills\"" >&2
  echo "  cp -r /tmp/prd-tools/plugins/build-reference/skills/build-reference \"\$PWD/.claude/skills/\"" >&2
  echo "  cp -r /tmp/prd-tools/plugins/prd-distill/skills/prd-distill \"\$PWD/.claude/skills/\"" >&2
  exit 1
fi

# Copy skills
mkdir -p "$CLAUDE_SKILLS_DIR"

SRC_DIR="$TMP_DIR/prd-tools-$BRANCH/plugins"
VERSION_FILE="$TMP_DIR/prd-tools-$BRANCH/VERSION"
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

cat > "$TARGET/.prd-tools-version" <<EOF
version=$TOOL_VERSION
installed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
source=github.com/$REPO
branch=$BRANCH
EOF

echo "==> Done!"
echo "==> Version: $TOOL_VERSION"
echo ""
echo "Usage in Claude Code:"
echo "  /build-reference  —  Build domain knowledge"
echo "  /prd-distill      —  Distill PRD document"
