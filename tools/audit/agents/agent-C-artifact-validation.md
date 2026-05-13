# Agent C: Artifact Validation (产物验证)

You are validating actual prd-tools output artifacts against their declared contracts, schemas, and workflow specifications.

## Activation Condition

This agent runs ONLY if:
- `--artifact-path` is provided and the path exists, OR
- A `_prd-tools/` directory is found in the current working tree.

If neither condition is met, output:

```
STATUS: SKIPPED
REASON: No artifacts found
SUGGESTION: Run /prd-distill or /reference first to generate artifacts, then re-run /self-audit --artifact-path <path>
```

And stop. Do NOT fabricate or simulate artifacts.

## Scope

Artifact path: {{ARTIFACT_PATH}}
Target plugin: {{PLUGIN_SCOPE}}

## Validation Checks

### C-1: File Existence

For the target plugin, verify all expected output files exist:

**prd-distill** (within `_prd-tools/distill/<slug>/`):
- `_ingest/source-manifest.yaml`
- `_ingest/document.md`
- `_ingest/document-structure.json`
- `_ingest/evidence-map.yaml`
- `_ingest/extraction-quality.yaml`
- `spec/ai-friendly-prd.md`
- `context/evidence.yaml`
- `context/requirement-ir.yaml`
- `context/layer-impact.yaml` (if report stage)
- `context/contract-delta.yaml` (if report stage)
- `report.md` (if report stage)
- `plan.md` (if plan stage)

**reference** (within `_prd-tools/reference/`):
- `project-profile.yaml`
- `01-codebase.yaml`
- `02-coding-rules.yaml`
- `03-contracts.yaml`
- `04-routing-playbooks.yaml`
- `05-domain.yaml`
- `index/manifest.yaml` (if full build)

### C-2: Contract Compliance

Only `prd-distill` has `.contract.yaml` files (4 contracts: ai-friendly-prd, contract-delta, layer-impact, requirement-ir) in `plugins/prd-distill/skills/prd-distill/references/contracts/`. The `reference` plugin has no contracts — skip C-2 entirely when `PLUGIN_SCOPE == reference`.

For each artifact that has a corresponding `.contract.yaml`:

1. Run: `python3 scripts/validate-artifact.py --contract <contract_path> --artifact <artifact_path>`
2. Report pass/fail and any rule violations.

### C-3: Path/Line Number Validation

For `plan.md` and `report.md`:
1. Extract all file path references (e.g., `src/foo/bar.ts:L42`).
2. For each reference, verify the file exists at the specified path (relative to the project where artifacts were generated).
3. If a line number is given, verify the referenced content exists at approximately that line.

### C-4: OQ (Open Questions) Quality

For `report.md`:
1. Extract all open questions (typically in the last section).
2. For each OQ, evaluate:
   - Is it a genuine unknown, or could it be resolved from existing evidence?
   - Is it actionable (does it suggest what information is needed)?
   - Is it tagged with severity/confidence?
3. Flag OQs that appear to be "pseudo-questions" (already answered elsewhere in the report).

### C-5: IR Trace Chain Integrity

For `context/requirement-ir.yaml`:
1. For each requirement, verify `ai_prd_req_id` references a section that exists in `spec/ai-friendly-prd.md`.
2. Verify `evidence.source_blocks` or `evidence.source_block_ids` reference block IDs that exist in `_ingest/document-structure.json` or `_ingest/evidence-map.yaml`.
3. Verify `source` field is one of: `explicit`, `inferred`, `missing_confirmation`.

### C-6: Field Name Spot Check

Compare field names in actual artifacts against field names in:
- `plugins/<plugin>/skills/<plugin>/references/contracts/*.contract.yaml`
- `plugins/<plugin>/skills/<plugin>/references/schemas/*.md`
- Gate script expectations (field names in regexes and dict lookups)

Report any field that exists in the artifact but not in the schema, or vice versa.

## Output Format

For each finding, output:

```
FINDING-C-<N>:
  severity: <P0|P1|P2>
  category: <missing_file|contract_violation|invalid_path|oq_quality|ir_trace_broken|field_name_mismatch>
  location: <artifact file path>
  description: <what is wrong>
  evidence: <exact content showing the problem>
  impact: <what this means for the consumer of this artifact>
  fix_hint: <how to fix the artifact or the contract/schema>
```

Severity guide:
- **P0**: Artifact has fabricated paths, broken trace chains, or missing critical files.
- **P1**: Artifact has contract violations or quality issues that degrade reliability.
- **P2**: Artifact has minor inconsistencies or style issues.

## Constraints

- Only READ artifacts. Do NOT modify them.
- If `validate-artifact.py` is not available or fails, report as a tooling gap (not an artifact issue).
- For path validation, check relative to the project root where the artifacts were generated (may be a different repo than prd-tools).
- Do NOT judge business correctness of requirements. Focus on structural/format compliance.
- Work in the repo root. Artifact paths are as specified in `ARTIFACT_PATH`.
