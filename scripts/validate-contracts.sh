#!/usr/bin/env bash
# Deterministic contract drift checks for PRD Tools.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

errors=0

fail() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

check_absent() {
  local pattern="$1"
  shift
  local label="$1"
  shift
  local matches
  matches=$(rg -n "$pattern" "$@" 2>/dev/null || true)
  if [ -n "$matches" ]; then
    fail "${label}"
    echo "$matches" >&2
  fi
}

current_contract_files=(
  "README.md"
  "OUTPUT_READING_GUIDE.md"
  "docs/graph-evidence-guide.md"
  "plugins/prd-distill/skills/prd-distill/SKILL.md"
  "plugins/prd-distill/skills/prd-distill/workflow.md"
  "plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md"
  "plugins/prd-distill/skills/prd-distill/agents/openai.yaml"
  "plugins/build-reference/skills/build-reference/references/output-contracts.md"
  "plugins/prd-distill/skills/prd-distill/references/output-contracts.md"
)

check_absent 'questions\.md.*(默认|生成|读|输出|不替代|清单|阻塞|owner|证据链|artifacts)' \
  "questions.md must not be described as a current standalone output; use report.md §11." \
  "${current_contract_files[@]}"

check_absent 'graph_source:' \
  "Use graph_sources: [] instead of graph_source:." \
  "plugins/build-reference/skills/build-reference/workflow.md" \
  "plugins/build-reference/skills/build-reference/references/reference-v4.md"

check_absent 'uv tool install graphify([^y]|$)' \
  "Graphify package install command should use official package graphifyy; CLI command remains graphify." \
  "install.sh" "README.md" "docs/graph-evidence-guide.md" "plugins"

if ! cmp -s \
  "plugins/prd-distill/skills/prd-distill/references/output-contracts.md" \
  "plugins/build-reference/skills/build-reference/references/output-contracts.md"; then
  fail "The shared output-contracts.md copies must stay identical across both plugins."
fi

if [ "$errors" -gt 0 ]; then
  echo "Contract validation failed (${errors} issue(s))." >&2
  exit 1
fi

echo "Contract validation passed ✓"
