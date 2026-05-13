# /reference

You are running the PRD Tools `reference` workflow. This command is a thin compatibility wrapper for clients or model gateways that do not reliably auto-trigger Claude Code skills.

Before doing any project analysis, you MUST read and follow:

1. `.claude/skills/reference/SKILL.md`
2. `.claude/skills/reference/workflow.md`

## Human Mode Selection Gate（硬约束 — 先选模式再构建）

Before running the full workflow, you MUST inspect the current `_prd-tools/`
state and ask the user to choose a Reference mode, unless the user explicitly
specified the mode in the prompt.

First inspect:

```bash
ls -la _prd-tools _prd-tools/reference _prd-tools/build 2>/dev/null
```

Then present this mode selection and WAIT for the user's choice:

1. **全量构建（Recommended when no reference exists）**
   - 先执行 Mode F 上下文收集，再执行 Mode A 全量构建。
   - 适合首次建设或希望尽量提升业务语义质量。
2. **仅上下文收集**
   - 只执行 Mode F，产出 `_prd-tools/build/context-enrichment.yaml`。
   - 不立即构建完整 reference。
3. **直接全量构建**
   - 跳过 Mode F，直接执行 Mode A。
   - 适合用户已经熟悉项目结构，或想快速重建。
4. **健康检查 / 增量更新 / 反馈回流**
   - 已有 reference 时可选择 B2 / B / E。
5. **Chat about this**
   - 仅讨论，不执行构建。

Rules:

- If `_prd-tools/reference/` does not exist, recommend option 1 but do not auto-run it.
- If `_prd-tools/reference/` exists, summarize current files and ask whether to run B2 health check, B incremental update, A rebuild, or E feedback ingest.
- Do not proceed from mode selection to artifact generation until the user confirms a mode.
- Once the user confirms a mode, record it by running:

```bash
python3 .prd-tools/scripts/reference-step-gate.py --confirm-mode <MODE> --root .
```

Valid modes: `F_then_A`, `F_only`, `A_only`, `B`, `B2`, `C`, `E`

## Step Gate (硬约束 — 每步执行前必须通过)

Before executing any phase/stage, you MUST run the step gate script:

```bash
python3 .prd-tools/scripts/reference-step-gate.py --step <step_id> --root . --write-state
```

Step IDs: `0`, `1`, `2a`, `2b`, `2c`, `2d`, `2e`, `3`, `3.5`, `3.6`, `4`

If the step gate exits with code 2 (FAIL):
- **STOP immediately** — do not proceed.
- Read the error message — it tells you exactly which prerequisite is missing.
- If the error is "MODE SELECTION REQUIRED", run `--confirm-mode <mode>` first.
- If the error is "ORDERING ERROR" and you need to re-run a step, add `--allow-rerun`.
- Complete the missing prerequisite first, then re-run the step gate.
- Only proceed after exit code 0 (PASS).

## Workflow State

Before each step, read `_prd-tools/build/reference-workflow-state.yaml`. If it does not exist, create it after Phase 0. After each step completes, update it with the step name, output files, and timestamp. The next step MUST read this state file before proceeding — do not rely on memory.

## Execution Order (HARD CONSTRAINTS)

Source code reads MAY run in parallel. Artifact generation MUST be sequential.

**Before each phase/stage, run the step gate. If it fails, stop and fix the prerequisite.**

Phase 2 deep analysis is strictly ordered — read `steps/step-02-deep-analysis.md` as one complete file, execute 5 stages sequentially:

1. Stage 1: `01-codebase.yaml`
   ⚙ Gate: `reference-step-gate.py --step 2a`
2. Stage 2: `02-coding-rules.yaml` (must read 01 first)
   ⚙ Gate: `reference-step-gate.py --step 2b`
3. Stage 3: `03-contracts.yaml` (must read 01, 02 first)
   ⚙ Gate: `reference-step-gate.py --step 2c`
4. Stage 4: `04-routing-playbooks.yaml` (must read 01, 02 first)
   ⚙ Gate: `reference-step-gate.py --step 2d`
5. Stage 5: \`05-domain.yaml\` (must read 01–04 first)
   ⚙ Gate: `reference-step-gate.py --step 2e`
6. After all 5 stages: run "去重检查" and "确定性验证"
8. build Evidence Index with `.prd-tools/scripts/build-index.py`
   ⚙ Gate: `reference-step-gate.py --step 3.5`
9. run `.prd-tools/scripts/reference-quality-gate.py --root .`
   ⚙ Gate: `reference-step-gate.py --step 3.6`
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

- Do not skip `_prd-tools/reference/index/`.
- Do not generate `02-coding-rules.yaml` before `01-codebase.yaml` exists.
- Do not generate `03-contracts.yaml` before `02-coding-rules.yaml` exists.
- Do not generate `04-routing-playbooks.yaml` before `03-contracts.yaml` exists.
- Do not generate `05-domain.yaml` before `04-routing-playbooks.yaml` exists.
- Do not split step-02-deep-analysis.md into separate reads — read it as one complete file.
- **Before each phase/stage, run `reference-step-gate.py` with the step ID. If exit code is 2, stop and complete the missing prerequisite before proceeding.**

Now continue with the user's `/reference` request.
