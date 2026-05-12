# /self-audit

You are running the PRD Tools self-audit workflow. This audits prd-tools itself (not user projects).

Before starting, you MUST read and follow:

1. `tools/audit/SKILL.md` — the skill definition
2. `tools/audit/agents/agent-A-static-walkthrough.md` — Phase 1 Agent A
3. `tools/audit/agents/agent-B-cross-file-consistency.md` — Phase 1 Agent B
4. `tools/audit/agents/agent-C-artifact-validation.md` — Phase 1 Agent C (conditional)
5. `tools/audit/merge-prompt.md` — Phase 2 merge
6. `tools/audit/output-schema.md` — Phase 3 output format

## Parameter Parsing

Parse the user's input to extract:

| Parameter | Flag | Default |
|-----------|------|---------|
| Plugin | `--plugin` or first arg | `all` |
| Version | `--version` | read from `VERSION` file |
| Artifact path | `--artifact-path` or `<path>` arg | auto-detect `_prd-tools/` |
| Skip selfcheck | `--skip-selfcheck` | false |

Examples:
- `/self-audit` → all plugins, auto-detect artifacts, run selfcheck
- `/self-audit --plugin prd-distill` → only prd-distill plugin
- `/self-audit --plugin reference --artifact-path ../dive-bff/_prd-tools/`
- `/self-audit --version 2.19.0`

## Execution Order (HARD CONSTRAINTS)

### Phase 0: Baseline

1. Read `VERSION` file (or use `--version` if provided).
2. Run selfcheck baseline (unless `--skip-selfcheck`):
   ```bash
   python3 tools/selfcheck/run.py --all --format json
   ```
   Capture JSON output as `SELFCHECK_BASELINE`.
3. Create output directory `docs/audit/<version>/`.
4. Auto-detect artifacts: search for `_prd-tools/` directories within 3 levels of the repo root.
   ```bash
   find . -name "_prd-tools" -type d -maxdepth 3 2>/dev/null
   ```
5. Determine `PLUGIN_SCOPE`: `prd-distill`, `reference`, or `both`.
6. Determine `ARTIFACT_PATH`: resolved path or empty string.

### Phase 1: Three Agents (parallel)

Launch three Agent tool calls in parallel:

- **Agent A** (subagent_type: general-purpose): Reads `tools/audit/agents/agent-A-static-walkthrough.md`. Executes static walkthrough for `PLUGIN_SCOPE`.
- **Agent B** (subagent_type: general-purpose): Reads `tools/audit/agents/agent-B-cross-file-consistency.md`. Executes cross-file consistency scan for `PLUGIN_SCOPE`.
- **Agent C** (conditional):
  - If `ARTIFACT_PATH` is non-empty and exists: launch Agent C with `tools/audit/agents/agent-C-artifact-validation.md`.
  - If no artifacts found: **SKIP Agent C** entirely. Note "Agent C: SKIPPED (no artifacts)" in the merge input.

**Agent prompts are self-contained**. Each agent reads its own prompt file and executes independently. Do NOT share intermediate state between agents during Phase 1. Pass `PLUGIN_SCOPE` and `ARTIFACT_PATH` as context in each agent's prompt.

### Phase 2: Merge

After all agents complete (or Agent C is skipped), read `tools/audit/merge-prompt.md` and execute:
1. Collect findings from Agent A, B, C.
2. Deduplicate by root cause.
3. Assign P0/P1/P2 priorities.
4. Analyze selfcheck coverage gaps (compare findings vs `SELFCHECK_BASELINE` checks).

### Phase 3: Output

Read `tools/audit/output-schema.md` and write output files to `docs/audit/<version>/`:

- `README.md` — overview table + execution principles
- `context-for-ai.md` — audit background + methodology + root causes
- `P0-fixes.md` — P0 FIX documents
- `P1-fixes.md` — P1 FIX documents
- `P2-fixes.md` — P2 FIX documents
- `verify-checklist.md` — per-FIX verification commands
- `selfcheck-delta.md` — selfcheck coverage gap analysis

## Do NOT

- Do NOT modify any prd-tools source files (this is a read-only audit).
- Do NOT run `/prd-distill` or `/reference` as part of the audit.
- Do NOT modify `VERSION`, `CHANGELOG.md`, `plugin.json`, or `marketplace.json`.
- Do NOT run `scripts/release.sh`.
- Do NOT create or modify `_prd-tools/` directories.

## Completion

After Phase 3, report to the user:
- Audit version and scope (which plugins).
- Selfcheck baseline result (pass/warn/fail counts).
- Agent A/B/C findings count.
- Merged & deduplicated counts by priority (P0/P1/P2).
- Selfcheck coverage gap count.
- Output directory path.

Now continue with the user's `/self-audit` request.
