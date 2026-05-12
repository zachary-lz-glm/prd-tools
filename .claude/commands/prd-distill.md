# /prd-distill

You are running the PRD Tools `prd-distill` workflow — now a **three-stage command**:

```text
/prd-distill spec <prd-file-or-text>   → PRD parsing + structured requirements
/prd-distill report <slug>             → impact analysis report (requires confirmation)
/prd-distill plan <slug>               → technical plan (requires approved report)
```

Before analyzing the PRD, you MUST read and follow:

1. `.claude/skills/prd-distill/SKILL.md`
2. `.claude/skills/prd-distill/workflow.md`

## Subcommand Recognition

Identify which stage the user wants:

| Input | Stage | Behavior |
|-------|-------|----------|
| `/prd-distill spec foo.docx` | spec | Run Steps 0→1→1.5→2 only. Do NOT generate `report.md` or `plan.md`. |
| `/prd-distill report <slug>` | report | Run Steps 2.5→3.1→3.2→3.5→4→8→8.1. Generate `report.md` but NOT `plan.md`. Stop and ask user to confirm. |
| `/prd-distill plan <slug>` | plan | Run Steps 5→6→8.5→8.6→9. Must check `context/report-confirmation.yaml` has `status: approved`. |
| `/prd-distill <PRD>` (no subcommand) | guided entry | Start with spec, then prompt user to continue with report, then confirm, then plan. Do NOT auto-generate plan. |

## Step Gate (硬约束 — 每步执行前必须通过)

Before executing any step, you MUST run the step gate script:

```bash
python3 .prd-tools/scripts/distill-step-gate.py --step <step_id> --distill-dir _prd-tools/distill/<slug> --repo-root . --write-state
```

Step IDs: `0`, `1`, `1.5-afprd`, `1.5-quality`, `2`, `2.5`, `3.1`, `3.2`, `3.5`, `3.6`, `4`, `8`, `8.1-confirm`, `5`, `6`, `7`, `8.5`, `8.6`, `9`

If the step gate exits with code 2 (FAIL):
- **STOP immediately** — do not proceed with the step.
- Read the error message — it tells you exactly which prerequisite is missing.
- If the error is "ORDERING ERROR" and you need to re-run a step, add `--allow-rerun`.
- Complete the missing prerequisite step first, then re-run the step gate.
- Only proceed after the step gate exits with code 0 (PASS).

## Workflow State

Before each step, read `_prd-tools/distill/<slug>/workflow-state.yaml`. If it does not exist, create it after Step 0. After each step completes, update it with the step name, output files, and timestamp. The next step MUST read this state file before proceeding — do not rely on memory.

## Three-Stage Workflow (HARD CONSTRAINTS)

### Stage 1: spec

Steps: 0 → 1 → 1.5-afprd → 1.5-quality → 2

Allowed outputs:
- `_ingest/*`
- `spec/ai-friendly-prd.md`
- `context/evidence.yaml`
- `context/prd-quality-report.yaml`
- `context/requirement-ir.yaml`

**MUST NOT produce**: `report.md`, `plan.md`, `portal.html`, `context/readiness-report.yaml`, `context/final-quality-gate.yaml`

### Stage 2: report

Steps: 2.5 → 3.1 → 3.2 → 3.5 → 4 → 8 → 8.1-confirm

Allowed outputs:
- `context/query-plan.yaml` (if index exists)
- `context/graph-context.md`
- `context/layer-impact.yaml`
- `context/contract-delta.yaml`
- `report.md`
- `context/report-confirmation.yaml`

**MUST NOT produce**: `plan.md`, `portal.html`, `context/readiness-report.yaml`, `context/final-quality-gate.yaml`

**STOP after Step 8.1**: Ask user to confirm report. Write `context/report-confirmation.yaml` with user's response.

### Stage 3: plan

Steps: 5 → 6 → 7 → 8.5 → 8.6 → 9

**Prerequisite**: `context/report-confirmation.yaml` must exist with `status: approved`.

If report is not approved (`needs_revision` or `blocked`):
- Do NOT generate `plan.md`.
- For `needs_revision`: go back to fix upstream artifacts (AI-friendly PRD, Requirement IR, Layer Impact, Contract Delta).
- For `blocked`: stop the workflow.

Allowed outputs:
- `plan.md`
- `context/readiness-report.yaml`
- `context/final-quality-gate.yaml`
- `portal.html`

## Execution Order (HARD CONSTRAINTS)

Source code reads MAY run in parallel. Artifact generation MUST be sequential.

Steps are strictly ordered — each step depends on the previous step's output.
**Before each step, run the step gate. If it fails, stop and fix the prerequisite.**

### spec 阶段

1. Step 0: PRD Ingestion → `_ingest/` (document.md, source-manifest.yaml, document-structure.json, evidence-map.yaml, extraction-quality.yaml, media/, media-analysis.yaml)
   ⚙ Gate: `distill-step-gate.py --step 0`
2. Step 1: Evidence Ledger → `context/evidence.yaml`
   ⚙ Gate: `distill-step-gate.py --step 1`
3. Step 1.5: AI-friendly PRD → `spec/ai-friendly-prd.md` + `context/prd-quality-report.yaml`
   ⚙ Gate: `distill-step-gate.py --step 1.5-afprd` then `--step 1.5-quality`
4. Step 2: Requirement IR → `context/requirement-ir.yaml` (must include meta.primary_source and evidence.source_blocks)
   ⚙ Gate: `distill-step-gate.py --step 2`

### report 阶段

5. Step 2.5: Query Plan → `context/query-plan.yaml` (if index exists)
   ⚙ Gate: `distill-step-gate.py --step 2.5`
6. Step 3.1: Graph Context → `context/graph-context.md`
   ⚙ Gate: `distill-step-gate.py --step 3.1`
7. Step 3.2: Layer Impact → `context/layer-impact.yaml`
   ⚙ Gate: `distill-step-gate.py --step 3.2`
8. Step 3.5: Context Pack → `context/context-pack.md`
   ⚙ Gate: `distill-step-gate.py --step 3.5`
9. Step 4: Contract Delta → `context/contract-delta.yaml`
   ⚙ Gate: `distill-step-gate.py --step 4`
9. Step 8: Report → `report.md`
   ⚙ Gate: `distill-step-gate.py --step 8`
10. Step 8.1: Report Review Gate → `context/report-confirmation.yaml`
   ⚙ Gate: `distill-step-gate.py --step 8.1-confirm`
   **STOP** — ask user to confirm report. Do NOT proceed to plan until approved.

### plan 阶段 (requires approved report)

11. Step 5: Plan → `plan.md`
   ⚙ Gate: `distill-step-gate.py --step 5`
12. Step 6: Readiness → `context/readiness-report.yaml`
   ⚙ Gate: `distill-step-gate.py --step 6`
13. Step 7: Reference 回流 → `context/reference-update-suggestions.yaml`
   ⚙ Gate: `distill-step-gate.py --step 7`
14. Step 8.5: Final Quality Gate → `context/final-quality-gate.yaml`
   ⚙ Gate: `distill-step-gate.py --step 8.5`
15. Step 8.6: Distill Completion Gate → run `distill-quality-gate.py`
   ⚙ Gate: `distill-step-gate.py --step 8.6`
16. Step 9: Portal HTML → render with `render-distill-portal.py`
   ⚙ Gate: `distill-step-gate.py --step 9`

**Do NOT use background agents for artifact generation.** Only source code reading may be parallelized.

## Completion Definition

/prd-distill is complete ONLY when ALL of the following are true:

1. `distill-quality-gate.py` exits with code 0 (pass or warning)
2. `distill-workflow-gate.py` exits with code 0 (pass or warning)
3. The final response includes:
   - `distill-workflow-gate.py` result
   - `distill-quality-gate.py` result
   - Readiness report summary

Do not claim /prd-distill is complete if any gate exits with code 2.

## Hard Gates

- Generate `spec/ai-friendly-prd.md` before `context/requirement-ir.yaml`.
- `context/requirement-ir.yaml` must contain `ai_prd_req_id`.
- Ready MODIFY/DELETE work must be connected to layer-impact code anchors or an explicit fallback reason.
- If `_prd-tools/reference/index/` exists, run `.prd-tools/scripts/context-pack.py`.
- Generate `context/final-quality-gate.yaml`.
- Render `portal.html` with `.prd-tools/scripts/render-distill-portal.py`.
- Run `.prd-tools/scripts/distill-quality-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`.
- Run `.prd-tools/scripts/distill-workflow-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`.
- **Do not generate final `plan.md` before `context/report-confirmation.yaml` exists with `status: approved`.**
- Do not handwrite `portal.html`.
- Do not generate `context/requirement-ir.yaml` before `spec/ai-friendly-prd.md` exists.
- Do not generate `context/layer-impact.yaml` before `context/requirement-ir.yaml` exists.
- **Before each step, run `distill-step-gate.py` with the step ID. If exit code is 2, stop and complete the missing prerequisite before proceeding.**
- **spec stage MUST NOT produce `report.md` or `plan.md`.**
- **report stage MUST NOT produce `plan.md`.**
- **plan stage MUST NOT re-interpret original PRD — only consume approved report and context.**

Now continue with the user's `/prd-distill` request.