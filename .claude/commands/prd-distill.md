# /prd-distill

You are running the PRD Tools `prd-distill` workflow. This command is a thin compatibility wrapper for clients or model gateways that do not reliably auto-trigger Claude Code skills.

Before analyzing the PRD, you MUST read and follow:

1. `.claude/skills/prd-distill/SKILL.md`
2. `.claude/skills/prd-distill/workflow.md`

## Workflow State

Before each step, read `_prd-tools/distill/<slug>/workflow-state.yaml`. If it does not exist, create it after Step 0. After each step completes, update it with the step name, output files, and timestamp. The next step MUST read this state file before proceeding — do not rely on memory.

## Execution Order (HARD CONSTRAINTS)

Source code reads MAY run in parallel. Artifact generation MUST be sequential.

Steps are strictly ordered — each step depends on the previous step's output:

1. Step 0: PRD Ingestion → `_ingest/document.md`
2. Step 1: Evidence Ledger → `context/evidence.yaml`
3. Step 1.5: AI-friendly PRD → `spec/ai-friendly-prd.md` + `context/prd-quality-report.yaml`
4. Step 2: Requirement IR → `context/requirement-ir.yaml` (must read afprd first)
5. Step 2.5: Query Plan → `context/query-plan.yaml` (if index exists)
6. Step 3: Layer Impact → `context/graph-context.md` + `context/layer-impact.yaml`
7. Step 4: Contract Delta → `context/contract-delta.yaml`
8. Step 5: Plan → `plan.md`
9. Step 6: Readiness → `context/readiness-report.yaml`
10. Step 8: Report → `report.md`
11. Step 8.5: Final Quality Gate → `context/final-quality-gate.yaml`
12. Step 8.6: Distill Completion Gate → run `distill-quality-gate.py`
13. Step 9: Portal HTML → render with `render-distill-portal.py`

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
- Do not handwrite `portal.html`.
- Do not generate `context/requirement-ir.yaml` before `spec/ai-friendly-prd.md` exists.
- Do not generate `context/layer-impact.yaml` before `context/requirement-ir.yaml` exists.

Now continue with the user's `/prd-distill` request.
