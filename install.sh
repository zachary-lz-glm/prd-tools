#!/usr/bin/env bash
set -euo pipefail

REPO="zachary-lz-glm/prd-tools"
BRANCH="main"
TARGET="${1:-.}"

# Resolve to absolute path
TARGET="$(cd "$TARGET" && pwd)"

SKILLS_DIR="$TARGET/.claude/skills"
TMP_DIR="$(mktemp -d)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "==> Installing prd-tools skills to: $SKILLS_DIR"

# Download archive
echo "==> Downloading from GitHub..."
curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP_DIR"

# Copy skills
mkdir -p "$SKILLS_DIR"

SRC_DIR="$TMP_DIR/prd-tools-$BRANCH/plugins"

for skill in build-reference prd-distill; do
  src="$SRC_DIR/$skill/skills/$skill"
  dst="$SKILLS_DIR/$skill"
  if [ -d "$src" ]; then
    cp -r "$src" "$dst"
    echo "    Installed: $skill"
  else
    echo "    WARNING: $skill not found in archive" >&2
  fi
done

echo "==> Done!"
echo ""
echo "Usage in Claude Code:"
echo "  /build-reference  —  Build domain knowledge"
echo "  /prd-distill      —  Distill PRD document"
