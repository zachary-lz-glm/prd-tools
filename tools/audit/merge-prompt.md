# Audit Merge Phase

You have received findings from three agents (A, B, and optionally C). Your job is to merge, deduplicate, categorize by root cause, assign priorities, analyze selfcheck coverage gaps, and produce the final FIX documents.

## Input

- Agent A findings: `FINDING-A-*` list
- Agent B findings: `FINDING-B-*` list
- Agent C findings: `FINDING-C-*` list (or SKIPPED status)
- Selfcheck baseline: JSON output from `python3 tools/selfcheck/run.py --all --format json`

## Step 1: Root Cause Deduplication

Agents often find the same issue from different angles. Group findings by root cause:

| Root Cause Type | Description | Example |
|----------------|-------------|---------|
| `copy_drift` | Same fact in multiple files, diverged during iteration | SKILL.md says "score:", workflow says "overall_score:" |
| `script_as_schema` | Python script output format is the de facto schema, undocumented | document-structure.json uses `id` but docs say `block_id` |
| `gate_template_mismatch` | Workflow template teaches one format, gate checks another | Template: `## §1 Overview`, Gate regex: `^## Overview` |
| `hardcoded_values` | Gate/utility scripts have hardcoded project-specific values | KEY_ANCHOR_FILES in final-quality-gate.py |
| `missing_fix_hint` | Gate reports failure without suggesting how to fix | Gate says "missing field X" but not which file to edit |
| `structural_gap` | Missing file, step, or section that should exist | No step for generating document-structure.json |
| `artifact_quality` | Output artifact has quality issues (only from Agent C) | Fabricated file path in plan.md |

For each group:
1. List all contributing findings (e.g., "FINDING-A-3 + FINDING-B-7 + FINDING-C-2 → same root cause").
2. Assign a single merged FIX ID: `P0-<N>`, `P1-<N>`, or `P2-<N>` (numbered sequentially within each priority).
3. Use the highest severity among contributing findings as the merged severity.
4. If agents disagree on severity for the same root cause, use the higher severity.

## Step 2: Priority Assignment

| Priority | Criteria | Commit prefix |
|----------|----------|---------------|
| P0 | Flow-breaking: LLM gets stuck, produces wrong output, or gate always fails on valid artifacts | `fix(audit-p0)` |
| P1 | Quality degradation: Suboptimal but not broken output; reliability reduced | `fix(audit-p1)` |
| P2 | Maintainability: Does not affect current execution; makes future iteration riskier | `refactor(audit-p2)` |

## Step 3: Selfcheck Coverage Gap Analysis

For each merged finding, check: would any existing selfcheck (D1-D6, S1-S4, C1-C3, X1, X4) have caught this?

| Check | What it covers |
|-------|----------------|
| D1 | No duplicate headings in workflow.md |
| D2 | No smart quotes in yaml blocks |
| D3 | Step file references exist |
| D4 | Gate mentions consistency across docs |
| D5 | current_step matches step file name |
| D6 | Number list no duplicate numbering |
| S1 | Python scripts compile |
| S2 | yaml import before yaml usage |
| S3 | tool-version reads VERSION file |
| S4 | Gate --help works |
| C1 | Contract YAML parseable |
| C2 | required_top_level in output-contracts.md |
| C3 | validate-artifact on snapshot |
| X1 | workflow step IDs in STEP_TABLE |
| X4 | VERSION lockstep across 5 files |

- If a finding IS catchable: note which check covers it.
- If a finding is NOT catchable: design a new selfcheck recommendation.

For each recommended new check:
```
NEW-CHECK-<N>:
  category: <docs|scripts|contracts|cross>
  description: <one-line description>
  rationale: <which finding(s) this would catch>
  suggested_id: <next available ID in category>
  pseudo_code: |
    <brief description of what the check function would do>
```

## Step 4: Output Generation

Write files to `docs/audit/<version>/` following the format specified in `tools/audit/output-schema.md`.

Read `tools/audit/output-schema.md` for the exact structure of each file. Key requirements:

### README.md
- Version, date, plugin scope
- Document split table linking to sub-files
- FIX overview table with ID, one-liner, priority, estimated change
- Execution principles (one FIX at a time, verify after each, independent commits)
- Conventions (commit prefix rules, version rules, do-not-touch list)
- Acceptance criteria (selfcheck target: 0 fail)

### context-for-ai.md
- Why this audit was needed (what iteration prompted it)
- How the audit was done (3 agents, methodology)
- Systemic root causes discovered (categorized)
- Impact on fix execution (what NOT to do)
- Version snapshot table

### P0/P1/P2-fixes.md
Each FIX entry MUST include:
1. Header: `## <FIX-ID> — <one-line description>`
2. 问题: Clear description of what is wrong
3. 证据: `file:line` references with code/text snippets showing the mismatch
4. 修复: Step-by-step fix instructions (grep to locate, then what to change)
5. relates_to (optional): Cross-references to related fixes
6. verify: Bash command that MUST exit 0 if fix is correct
7. commit: Conventional commit message template

### verify-checklist.md
Three tiers:
- **minimal_verify**: Run after each individual FIX
- **batch_verify**: Run after each priority batch
- **regression_verify**: `python3 tools/selfcheck/run.py --all`

### selfcheck-delta.md
1. Selfcheck baseline result table (from JSON output)
2. Per-finding coverage analysis: covered by which check, or NOT COVERED
3. New check recommendations

## Constraints

- Do NOT modify any findings' severity during merge (only upgrade if multiple findings compound).
- Every merged finding MUST retain references to its source agent findings.
- Do NOT invent findings that no agent reported.
- Output is in Chinese where v2.18.1 audit used Chinese, English for technical content.
