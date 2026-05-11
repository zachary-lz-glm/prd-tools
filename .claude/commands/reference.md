# /reference

You are running the PRD Tools `reference` workflow. This command is a thin compatibility wrapper for clients or model gateways that do not reliably auto-trigger Claude Code skills.

Before doing any project analysis, you MUST read and follow:

1. `.claude/skills/reference/SKILL.md`
2. `.claude/skills/reference/workflow.md`

## Workflow State

Before each step, read `_prd-tools/build/reference-workflow-state.yaml`. If it does not exist, create it after Phase 0. After each step completes, update it with the step name, output files, and timestamp. The next step MUST read this state file before proceeding — do not rely on memory.

## Execution Order (HARD CONSTRAINTS)

Source code reads MAY run in parallel. Artifact generation MUST be sequential.

Phase 2 deep analysis is strictly ordered — read `steps/step-02-deep-analysis.md` as one complete file, execute 5 stages sequentially:

1. Stage 1: `01-codebase.yaml`
2. Stage 2: `02-coding-rules.yaml` (must read 01 first)
3. Stage 3: `03-contracts.yaml` (must read 01, 02 first)
4. Stage 4: `04-routing-playbooks.yaml` (must read 01, 02 first)
5. Stage 5: `05-domain.yaml` + `00-portal.md` (must read 01–04 first)
6. After all 5 stages: run "去重检查" and "确定性验证"
7. render `portal.html` with `.prd-tools/scripts/render-reference-portal.py`
8. build Evidence Index with `.prd-tools/scripts/build-index.py`
9. run `.prd-tools/scripts/reference-quality-gate.py --root .`
10. run `.prd-tools/scripts/reference-workflow-gate.py --root .`

**Do NOT use background agents for artifact generation.** Only source code reading may be parallelized.

## Completion Definition

/reference is complete ONLY when ALL of the following are true:

1. `reference-quality-gate.py` exits with code 0 (pass or warning)
2. `reference-workflow-gate.py` exits with code 0 (pass or warning)
3. The final response includes:
   - `reference-workflow-gate.py` result
   - `reference-quality-gate.py` result
   - Index manifest summary (entity count, edge count, term count)

Do not claim /reference is complete if any gate exits with code 2. Do not claim /reference is complete if index files are missing.

## Hard Gates

- Do not handwrite `portal.html`.
- Do not skip `_prd-tools/reference/index/`.
- Do not generate `02-coding-rules.yaml` before `01-codebase.yaml` exists.
- Do not generate `03-contracts.yaml` before `02-coding-rules.yaml` exists.
- Do not generate `04-routing-playbooks.yaml` before `03-contracts.yaml` exists.
- Do not generate `05-domain.yaml` before `04-routing-playbooks.yaml` exists.
- Do not split step-02-deep-analysis.md into separate reads — read it as one complete file.

Now continue with the user's `/reference` request.
