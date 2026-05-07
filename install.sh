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
echo "║        prd-tools  install                ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Proxy (curl only) ─────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/scripts/lib/detect_proxy.sh" ]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/scripts/lib/detect_proxy.sh"
  detect_proxy_for_curl
fi

# ── Download archive ──────────────────────────────────────────────
echo "==> Downloading prd-tools ($BRANCH)..."
ARCHIVE_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"
if ! curl -fsSL --connect-timeout 10 --max-time 60 "$ARCHIVE_URL" \
     | tar -xz -C "$TMP_DIR" 2>/dev/null; then
  echo "" >&2
  echo "ERROR: GitHub archive download failed." >&2
  echo "" >&2
  echo "Fallback — clone via git, then copy manually:" >&2
  echo "  git clone --depth 1 -b $BRANCH https://github.com/$REPO.git /tmp/prd-tools" >&2
  echo "  bash /tmp/prd-tools/install.sh $TARGET" >&2
  exit 1
fi

ARCHIVE_ROOT="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"
if [ -z "$ARCHIVE_ROOT" ] || [ ! -d "$ARCHIVE_ROOT/plugins" ]; then
  echo "ERROR: Downloaded archive has unexpected structure." >&2
  exit 1
fi

# ── Copy skills ───────────────────────────────────────────────────
mkdir -p "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
echo "==> Installing skills to $CLAUDE_SKILLS_DIR"
for skill in build-reference prd-distill; do
  src="$ARCHIVE_ROOT/plugins/$skill/skills/$skill"
  if [ -d "$src" ]; then
    rm -rf "$CLAUDE_SKILLS_DIR/$skill"
    cp -r "$src" "$CLAUDE_SKILLS_DIR/$skill"
    echo "    Installed: $skill"
  else
    echo "    WARNING: $skill not found in archive" >&2
  fi
done

# ── Copy commands ─────────────────────────────────────────────────
COMMAND_SRC="$ARCHIVE_ROOT/.claude/commands/reference.md"
if [ -f "$COMMAND_SRC" ]; then
  cp "$COMMAND_SRC" "$CLAUDE_COMMANDS_DIR/reference.md"
  echo "    Installed command: /reference"
fi

# ── Copy doctor script (so users have it locally) ─────────────────
DOCTOR_SRC="$ARCHIVE_ROOT/scripts/doctor.sh"
if [ -f "$DOCTOR_SRC" ]; then
  mkdir -p "$TARGET/.prd-tools"
  cp "$DOCTOR_SRC" "$TARGET/.prd-tools/doctor.sh"
  if [ -d "$ARCHIVE_ROOT/scripts/lib" ]; then
    mkdir -p "$TARGET/.prd-tools/lib"
    cp -r "$ARCHIVE_ROOT/scripts/lib/." "$TARGET/.prd-tools/lib/"
  fi
  chmod +x "$TARGET/.prd-tools/doctor.sh"
  echo "    Installed doctor: $TARGET/.prd-tools/doctor.sh"
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

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "  prd-tools v$TOOL_VERSION skills installed"
echo "========================================="
echo ""
echo "Next:"
echo "  1. Check external dependencies:"
echo "       bash $TARGET/.prd-tools/doctor.sh"
echo "     (verifies uv / MarkItDown / Graphify / GitNexus / API key)"
echo ""
echo "  2. Restart Claude Code so the new skills load."
echo ""
echo "  3. Run /reference to build the project knowledge base."
echo ""
