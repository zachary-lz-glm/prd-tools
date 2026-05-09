#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cmd="${1:-}"
case_id="${2:-}"
arg3="${3:-}"
arg4="${4:-}"

case "$cmd" in
  list)
    for d in "$ROOT_DIR/benchmarks/cases"/*/; do
      [ -d "$d" ] && basename "$d"
    done
    ;;

  lint)
    python3 "$SCRIPT_DIR/benchmark_score.py" --lint
    ;;

  score)
    if [ -z "$case_id" ] || [ -z "$arg3" ]; then
      echo "Usage: scripts/benchmark.sh score <case-id> <output-dir>"
      exit 1
    fi
    python3 "$SCRIPT_DIR/benchmark_score.py" \
      --case "$ROOT_DIR/benchmarks/cases/${case_id}" \
      --output "$arg3"
    ;;

  oracle)
    if [ -z "$case_id" ] || [ -z "$arg3" ]; then
      echo "Usage: scripts/benchmark.sh oracle <case-id> <output-dir>"
      exit 1
    fi
    oracle_file="$ROOT_DIR/benchmarks/cases/${case_id}/oracle.yaml"
    if [ ! -f "$oracle_file" ]; then
      echo "Error: oracle.yaml not found at $oracle_file" >&2
      exit 1
    fi
    python3 "$SCRIPT_DIR/benchmark_score.py" \
      --oracle "$oracle_file" \
      --output "$arg3"
    ;;

  compare)
    if [ -z "$case_id" ] || [ -z "$arg3" ] || [ -z "$arg4" ]; then
      echo "Usage: scripts/benchmark.sh compare <case-id> <baseline-version> <output-dir>"
      exit 1
    fi
    python3 "$SCRIPT_DIR/benchmark_score.py" \
      --case "$ROOT_DIR/benchmarks/cases/${case_id}" \
      --baseline "$ROOT_DIR/benchmarks/baselines/${arg3}/${case_id}" \
      --output "$arg4"
    ;;

  save-baseline)
    if [ -z "$case_id" ] || [ -z "$arg3" ] || [ -z "$arg4" ]; then
      echo "Usage: scripts/benchmark.sh save-baseline <case-id> <version> <output-dir>"
      exit 1
    fi
    target="$ROOT_DIR/benchmarks/baselines/${arg3}/${case_id}"
    mkdir -p "$target"
    cp "${arg4}/report.md" "$target/" 2>/dev/null || true
    cp "${arg4}/plan.md" "$target/" 2>/dev/null || true
    cp "${arg4}/context/readiness-report.yaml" "$target/" 2>/dev/null || true
    python3 "$SCRIPT_DIR/benchmark_score.py" \
      --case "$ROOT_DIR/benchmarks/cases/${case_id}" \
      --output "$arg4" \
      --write-scores "$target/scores.yaml"
    echo "Baseline saved: ${arg3}/${case_id}"
    ;;

  *)
    echo "Usage:"
    echo "  scripts/benchmark.sh list"
    echo "  scripts/benchmark.sh lint"
    echo "  scripts/benchmark.sh score <case-id> <output-dir>"
    echo "  scripts/benchmark.sh oracle <case-id> <output-dir>"
    echo "  scripts/benchmark.sh compare <case-id> <baseline-version> <output-dir>"
    echo "  scripts/benchmark.sh save-baseline <case-id> <version> <output-dir>"
    exit 1
    ;;
esac
