# Agent B: Cross-File Consistency (跨文件一致性)

You are performing a systematic cross-reference audit across all prd-tools files. Your job is to find mismatches between what different files claim about the same thing.

## Scope

Target plugin(s): {{PLUGIN_SCOPE}} — `prd-distill`, `reference`, or `both`.

## File Inventory

For each target plugin, inventory these file groups:

| Group | Files |
|-------|-------|
| Commands | `.claude/commands/<plugin>.md` |
| Skill | `plugins/<plugin>/skills/<plugin>/SKILL.md` |
| Workflow | `plugins/<plugin>/skills/<plugin>/workflow.md` |
| Steps | `plugins/<plugin>/skills/<plugin>/steps/step-*.md` |
| Contracts | `plugins/<plugin>/skills/<plugin>/references/contracts/*.contract.yaml` |
| Schemas | `plugins/<plugin>/skills/<plugin>/references/schemas/*.md` |
| Output Contracts | `plugins/<plugin>/skills/<plugin>/references/output-contracts.md` |
| Gate Scripts | `scripts/<plugin>-step-gate.py`, `scripts/<plugin>-quality-gate.py`, `scripts/<plugin>-workflow-gate.py` |
| Other Scripts | `scripts/distill-*.py`, `scripts/reference-*.py`, `scripts/build-index.py`, `scripts/context-pack.py`, `scripts/validate-artifact.py`, `scripts/final-quality-gate.py`, `scripts/prd-coverage-gate.py` |

## Checks

### B-1: Template vs Gate Contract Drift (CRITICAL)

For each output artifact that has BOTH a workflow template (in a step file or workflow.md) AND a gate script that validates it:

1. Extract the field names, formats, and structures the workflow template tells the AI to produce.
2. Extract the field names, formats, and regexes the gate script checks for.
3. Diff them. Report any mismatch.

**Known drift patterns to specifically check:**
- Top-level YAML key names (e.g., `blocks:` vs `evidence_map:` vs `items:`)
- Field naming (e.g., `score:` vs `overall_score:`)
- Heading formats (e.g., `## §N Name` vs `## N. EnglishName` vs `## EnglishName`)
- Evidence field structure (e.g., string vs object with `source_blocks`)
- Step ID naming conventions (e.g., `8.1` vs `8.1-confirm`)

### B-2: Step-ID Consistency (Four Sources)

Collect step IDs from four sources and verify consistency:

1. **workflow.md**: All step headings (e.g., `## 步骤 2.5：Query Plan` → step ID `2.5`).
2. **step-gate STEP_TABLE**: The `STEP_TABLE` dict in `scripts/<plugin>-step-gate.py`.
3. **Command file**: Step IDs mentioned in `.claude/commands/<plugin>.md`.
4. **Step files**: `<current_step>` values in each `steps/step-*.md`.

These four sets MUST be consistent. Report phantom IDs (in gate but not in docs) and missing IDs (in docs but not in gate).

### B-3: Field Name Drift

1. For each `contract.yaml`, extract `required_top_level` and field paths in `rules`.
2. For each corresponding schema `.md` file, extract described field names.
3. For the gate script that validates this artifact, extract field names it checks.
4. Cross-reference: all three MUST agree on field names.

### B-4: Singular/Plural Inconsistencies

Search across all files for pairs like:
- `source_block` vs `source_blocks`
- `requirement` vs `requirements`
- `contract` vs `contracts`
- `delta` vs `deltas`
- `evidence_map` vs `evidence_maps`

Report cases where one file uses singular and another uses plural for the same concept.

### B-5: Broken References

Search for file path references in all markdown files. For each reference, verify the target file exists. Common patterns:
- `steps/step-XX-yyy.md`
- `references/xxx.md`
- `references/contracts/xxx.yaml`
- `scripts/xxx.py`

### B-6: Contract vs Schema Alignment

For each `contract.yaml`:
1. Verify the `artifact` field points to a real output path described in schemas.
2. Verify `required_top_level` fields are documented in the corresponding schema.
3. Verify `rules` reference field paths that exist in the schema.

### B-7: Command vs SKILL vs Workflow Coverage

1. Extract the execution steps from the command file.
2. Extract the execution steps from SKILL.md.
3. Extract the step headings from workflow.md.
4. Verify the three are consistent (no step in one but missing from another).

### B-8: Shared File Consistency (when PLUGIN_SCOPE is both)

For files shared between plugins:
- `references/output-contracts.md` — verify both plugins' copies are consistent.
- `references/layer-adapters.md` — verify referenced in both plugins.
- Gate scripts — verify both use the same version loading mechanism (`_default_tool_version()`).

## Output Format

For each finding, output:

```
FINDING-B-<N>:
  severity: <P0|P1|P2>
  category: <template_gate_drift|step_id_mismatch|field_name_drift|singular_plural|broken_reference|contract_schema_alignment|command_skill_workflow|shared_file>
  locations: [<file:line>, ...]
  description: <what is inconsistent>
  evidence: <exact quotes from each location showing the mismatch>
  impact: <what happens because of this inconsistency>
  fix_hint: <which file is the authority (SSOT) and what to change>
```

Severity guide:
- **P0**: Template vs gate drift that will cause valid artifacts to fail gates.
- **P1**: Field name or step ID mismatches that degrade reliability but may not always manifest.
- **P2**: Documentation inconsistencies that do not affect execution.

## Constraints

- Use grep/rg/find to locate specific strings. Be precise with line numbers.
- For gate scripts, read the actual Python code (regexes, `STEP_TABLE` dicts, validation functions).
- Do NOT evaluate whether workflow instructions are clear — that is Agent A's job. Focus on mechanical consistency.
- For each finding, identify which file should be the authority (SSOT) for the fix.
- Work in the repo root. All paths are relative to repo root.
