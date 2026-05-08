#!/usr/bin/env bash
# status.sh — Generate a local PRD Tools status summary and dashboard.
#
# Usage:
#   bash .prd-tools/status.sh [project-root]
#
# Outputs:
#   _prd-tools/STATUS.md
#   _prd-tools/dashboard/index.html

set -euo pipefail

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"
cd "$TARGET"

OUT_DIR="_prd-tools"
DASHBOARD_DIR="$OUT_DIR/dashboard"
STATUS_MD="$OUT_DIR/STATUS.md"
DASHBOARD_HTML="$DASHBOARD_DIR/index.html"

mkdir -p "$OUT_DIR" "$DASHBOARD_DIR"

now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
project_name="$(basename "$TARGET")"

yaml_value() {
  local file="$1"
  local key="$2"
  [ -f "$file" ] || return 0
  awk -v key="$key" '
    $0 ~ "^[[:space:]]*" key ":[[:space:]]*" {
      sub("^[[:space:]]*" key ":[[:space:]]*", "", $0)
      gsub(/^"|"$/, "", $0)
      print $0
      exit
    }
    $0 ~ "^[[:space:]]*" key "=[[:space:]]*" {
      sub("^[[:space:]]*" key "=[[:space:]]*", "", $0)
      gsub(/^"|"$/, "", $0)
      print $0
      exit
    }
  ' "$file"
}

section_yaml_value() {
  local file="$1"
  local section="$2"
  local key="$3"
  [ -f "$file" ] || return 0
  awk -v section="$section" -v key="$key" '
    $0 ~ "^" section ":" { in_section=1; next }
    in_section && $0 ~ "^[^[:space:]][^:]*:" { exit }
    in_section && $0 ~ "^[[:space:]]+" key ":[[:space:]]*" {
      sub("^[[:space:]]+" key ":[[:space:]]*", "", $0)
      gsub(/^"|"$/, "", $0)
      print $0
      exit
    }
  ' "$file"
}

count_yaml_list_items() {
  local file="$1"
  local section="$2"
  [ -f "$file" ] || { echo 0; return; }
  awk -v section="$section" '
    $0 ~ "^" section ":" { in_section=1; next }
    in_section && $0 ~ "^[^[:space:]][^:]*:" { exit }
    in_section && $0 ~ "^[[:space:]]+-[[:space:]]" { count++ }
    END { print count + 0 }
  ' "$file"
}

html_escape() {
  sed \
    -e 's/&/\&amp;/g' \
    -e 's/</\&lt;/g' \
    -e 's/>/\&gt;/g' \
    -e 's/"/\&quot;/g'
}

status_class() {
  case "$1" in
    pass|ready|available|exists|current|true|ok) echo "good" ;;
    warning|warn|missing|stale|unknown) echo "warn" ;;
    fail|blocked|false|unavailable) echo "bad" ;;
    *) echo "neutral" ;;
  esac
}

version="unknown"
if [ -f ".prd-tools-version" ]; then
  version="$(yaml_value ".prd-tools-version" "version")"
  version="${version:-unknown}"
fi

skills_status="missing"
if [ -d ".claude/skills/reference" ] && [ -d ".claude/skills/prd-distill" ]; then
  skills_status="available"
fi

legacy_notes=()
[ -d "_reference" ] && legacy_notes+=("_reference legacy output exists")
[ -d "_output" ] && legacy_notes+=("_output legacy output exists")
[ -f ".claude/commands/reference.md" ] && legacy_notes+=(".claude/commands/reference.md legacy alias exists")
[ -d ".claude/skills/build-reference" ] && legacy_notes+=(".claude/skills/build-reference legacy skill exists")

reference_status="missing"
[ -d "$OUT_DIR/reference" ] && reference_status="exists"

quality_file="$OUT_DIR/build/quality-report.yaml"
quality_status="$(yaml_value "$quality_file" "overall_status")"
quality_status="${quality_status:-unknown}"
quality_score="$(yaml_value "$quality_file" "score")"
quality_score="${quality_score:-unknown}"
warning_count="$(count_yaml_list_items "$quality_file" "warnings")"

latest_distill_dir=""
if [ -d "$OUT_DIR/distill" ]; then
  latest_distill_dir="$(find "$OUT_DIR/distill" -mindepth 1 -maxdepth 1 -type d -print 2>/dev/null \
    | while IFS= read -r dir; do
        ts="$(stat -f %m "$dir" 2>/dev/null || stat -c %Y "$dir" 2>/dev/null || echo 0)"
        printf "%s\t%s\n" "$ts" "$dir"
      done \
    | sort -rn \
    | head -1 \
    | cut -f2-)"
fi

latest_slug="none"
readiness_file=""
readiness_status="not_available"
readiness_score="unknown"
readiness_decision="unknown"
blocked_count="0"
needs_confirmation_count="0"
task_count="0"

if [ -n "$latest_distill_dir" ]; then
  latest_slug="$(basename "$latest_distill_dir")"
  readiness_file="$latest_distill_dir/readiness-report.yaml"
  if [ -f "$readiness_file" ]; then
    readiness_status="$(yaml_value "$readiness_file" "status")"
    readiness_status="${readiness_status:-unknown}"
    readiness_score="$(yaml_value "$readiness_file" "score")"
    readiness_score="${readiness_score:-unknown}"
    readiness_decision="$(yaml_value "$readiness_file" "decision")"
    readiness_decision="${readiness_decision:-unknown}"
    blocked_count="$(count_yaml_list_items "$readiness_file" "blocked")"
    needs_confirmation_count="$(count_yaml_list_items "$readiness_file" "needs_confirmation")"
  fi
  if [ -d "$latest_distill_dir/tasks" ]; then
    task_count="$(find "$latest_distill_dir/tasks" -maxdepth 1 -type f -name 'T-*.md' 2>/dev/null | wc -l | tr -d ' ')"
  fi
fi

next_actions=()
if [ "$skills_status" != "available" ]; then
  next_actions+=("Run prd-tools install.sh for this project.")
fi
if [ "$reference_status" != "exists" ]; then
  next_actions+=("Run /reference to build the project knowledge base.")
fi
if [ "$latest_slug" = "none" ]; then
  next_actions+=("Run /prd-distill on a PRD to generate readiness, plan, and tasks.")
elif [ "$readiness_status" = "not_available" ]; then
  next_actions+=("Regenerate latest /prd-distill output to include readiness-report.yaml.")
elif [ "$readiness_status" != "pass" ]; then
  next_actions+=("Resolve latest distill risks before coding.")
fi
if [ "${#legacy_notes[@]}" -gt 0 ]; then
  next_actions+=("Clean legacy outputs or rerun install.sh to remove old aliases.")
fi

if [ "${#next_actions[@]}" -eq 0 ]; then
  next_actions+=("Project is ready. Use report.md and plan.md for the next PRD review.")
fi

write_list_md() {
  local item
  for item in "$@"; do
    printf -- "- %s\n" "$item"
  done
}

{
  cat <<EOF
# PRD Tools Status

Generated: \`$now_utc\`

## 1. Project Readiness

| Item | Status | Detail |
|---|---|---|
| Project | $project_name | \`$TARGET\` |
| Installed Version | $version | \`.prd-tools-version\` |
| Skills | $skills_status | reference / prd-distill |
| Reference | $reference_status | \`_prd-tools/reference/\` |
| Reference Quality | $quality_status | score: $quality_score, warnings: $warning_count |

## 2. Latest Distill

| Item | Value |
|---|---|
| Slug | $latest_slug |
| Readiness | $readiness_status |
| Score | $readiness_score |
| Decision | $readiness_decision |
| Blockers | $blocked_count |
| Needs Confirmation | $needs_confirmation_count |
| Tasks | $task_count |

## 3. Legacy Signals

EOF
  if [ "${#legacy_notes[@]}" -eq 0 ]; then
    echo "- No legacy outputs or command aliases detected."
  else
    write_list_md "${legacy_notes[@]}"
  fi
  cat <<EOF

## 4. Next Actions

EOF
  write_list_md "${next_actions[@]}"
  cat <<EOF

## 5. Files

- Dashboard: \`_prd-tools/dashboard/index.html\`
- Reference quality: \`_prd-tools/build/quality-report.yaml\`
- Latest readiness: \`${readiness_file:-none}\`
EOF
} > "$STATUS_MD"

legacy_html="$(printf "%s\n" "${legacy_notes[@]:-No legacy outputs or command aliases detected.}" | html_escape | awk '{print "<li>" $0 "</li>"}')"
actions_html="$(printf "%s\n" "${next_actions[@]}" | html_escape | awk '{print "<li>" $0 "</li>"}')"

cat > "$DASHBOARD_HTML" <<EOF
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PRD Tools Status - $project_name</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #667085;
      --line: #d9dee8;
      --good: #137a4b;
      --good-bg: #e8f6ef;
      --warn: #9a5b00;
      --warn-bg: #fff4dd;
      --bad: #b42318;
      --bad-bg: #fde8e7;
      --neutral: #475467;
      --neutral-bg: #eef2f7;
      --accent: #2457c5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    header, main { max-width: 1120px; margin: 0 auto; padding: 24px; }
    header { padding-top: 32px; }
    h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }
    .metric-label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
    .metric-value { font-size: 24px; font-weight: 700; overflow-wrap: anywhere; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 13px;
      font-weight: 650;
      overflow-wrap: anywhere;
    }
    .good { color: var(--good); background: var(--good-bg); }
    .warn { color: var(--warn); background: var(--warn-bg); }
    .bad { color: var(--bad); background: var(--bad-bg); }
    .neutral { color: var(--neutral); background: var(--neutral-bg); }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-top: 1px solid var(--line); padding: 10px 8px; vertical-align: top; }
    th { color: var(--muted); font-size: 13px; font-weight: 650; }
    code { background: #eef2f7; padding: 2px 5px; border-radius: 4px; }
    ul { margin: 0; padding-left: 20px; }
    li + li { margin-top: 6px; }
    .two-col { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 12px; }
    .footer { color: var(--muted); font-size: 13px; margin-top: 18px; }
    @media (max-width: 860px) {
      header, main { padding: 18px; }
      .grid, .two-col { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>PRD Tools Status</h1>
    <p>$project_name · generated at $now_utc</p>
  </header>
  <main>
    <section class="grid">
      <div class="panel">
        <div class="metric-label">Reference</div>
        <div class="metric-value"><span class="badge $(status_class "$reference_status")">$reference_status</span></div>
      </div>
      <div class="panel">
        <div class="metric-label">Reference Quality</div>
        <div class="metric-value">$quality_score</div>
        <p><span class="badge $(status_class "$quality_status")">$quality_status</span></p>
      </div>
      <div class="panel">
        <div class="metric-label">Latest Readiness</div>
        <div class="metric-value">$readiness_score</div>
        <p><span class="badge $(status_class "$readiness_status")">$readiness_status</span></p>
      </div>
      <div class="panel">
        <div class="metric-label">Needs Confirmation</div>
        <div class="metric-value">$needs_confirmation_count</div>
        <p>blockers: $blocked_count</p>
      </div>
    </section>

    <section>
      <div class="panel">
        <h2>Latest Distill</h2>
        <table>
          <tbody>
            <tr><th>Slug</th><td>$latest_slug</td></tr>
            <tr><th>Decision</th><td>$readiness_decision</td></tr>
            <tr><th>Tasks</th><td>$task_count</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="two-col" style="margin-top:12px">
      <div class="panel">
        <h2>Next Actions</h2>
        <ul>
          $actions_html
        </ul>
      </div>
      <div class="panel">
        <h2>Legacy Signals</h2>
        <ul>
          $legacy_html
        </ul>
      </div>
    </section>

    <p class="footer">Text summary: <code>_prd-tools/STATUS.md</code></p>
  </main>
</body>
</html>
EOF

cat <<EOF
PRD Tools status generated
  Markdown: $TARGET/$STATUS_MD
  Dashboard: $TARGET/$DASHBOARD_HTML
EOF
