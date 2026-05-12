# Selfcheck 覆盖缺口分析

## 基线结果

| Check | Status | Message |
|---|---|---|
| C1 | pass | all contracts parse |
| C2 | pass | all required_top_level fields documented |
| C3 | pass | all sampled artifacts pass |
| D1 | pass | 2 workflow.md file(s) clean |
| D2 | pass | all yaml blocks clean |
| D3 | pass | all step references resolve |
| D4 | warn | 4 within-skill gate gap(s) |
| D5 | pass | all step tags aligned |
| D6 | pass | all numbered lists sequential |
| S1 | pass | all python files compile |
| S2 | pass | yaml usage consistent with imports |
| S3 | pass | step-gate defaults aligned or parameterized |
| S4 | pass | all gate scripts respond to --help |
| X1 | pass | workflow step ids match gate table |
| X4 | pass | all 5 locations at 2.18.1 |

## 覆盖分析

| Finding | Covered by | or NOT COVERED |
|---|---|---|
| P0-1 (contract-delta schema drift in 03-context.md) | **NOT COVERED** — C2 checks required_top_level in output-contracts.md, not in schemas/*.md | |
| P0-2 (report.md section count 11 vs 12) | **NOT COVERED** — no check validates report section count consistency across files | |
| P0-3 (step-03 bypasses report-confirmation) | **NOT COVERED** — D4 checks gate mentions in docs, not execution flow consistency | |
| P0-4 (step file vs gate ID mapping) | X1 partially (checks workflow step IDs in STEP_TABLE), but NOT the step-file ↔ gate mapping | |
| P0-5 (step 2.6 numbering vs execution) | X1 partially (checks step IDs exist), but NOT execution order correctness | |
| P0-6 (IR trace chain broken) | C3 partially (validates artifact), but NOT cross-file trace chain integrity | |
| P1-1 (requirement-ir input contradiction) | **NOT COVERED** — no check for cross-file description consistency | |
| P1-2 (layer-impact contract false pass) | **NOT COVERED** — C1 only checks YAML parses, not that contract path matches artifact structure | |
| P1-3 (plan.md length conflict) | **NOT COVERED** — no check for numeric range consistency across files | |
| P1-4 (step 3.6 no gate) | X1 partially — checks workflow step IDs exist in gate table | |
| P1-5 (step 7 no execution position) | X1 partially — step 7 IS in STEP_TABLE but not in command.md | |
| P1-6 (step numbering vs order) | **NOT COVERED** | |
| P1-7 (step-01 must_not_produce contradiction) | **NOT COVERED** | |
| P1-8 (query-plan underspecified) | **NOT COVERED** | |
| P1-9 (report-confirmation format drift) | **NOT COVERED** | |
| P1-10 (readiness field name drift) | **NOT COVERED** | |
| P1-11 (gate severity inconsistency) | **NOT COVERED** — no cross-gate consistency check | |
| P1-12 (project-profile fallback) | **NOT COVERED** | |
| P1-13 (workflow.md too long) | **NOT COVERED** — not automatable | |
| P2-1 ~ P2-10 | Mostly **NOT COVERED** — P2 issues are documentation quality, not structural | |

## 新增 Check 建议

### NEW-CHECK-1
- **category**: cross
- **description**: Schema files (03-context.md, 05-readiness.md) 与 output-contracts.md 之间的字段名/顶层键一致性检查
- **rationale**: Catches P0-1, P1-2, P1-10, P2-6, P2-10
- **pseudo_code**: For each schema in schemas/*.md, extract YAML code blocks. For corresponding output-contracts.md section, extract YAML code blocks. Compare field names (top-level keys, nested keys). Report mismatches.

### NEW-CHECK-2
- **category**: docs
- **description**: report.md section count consistency check across step files, workflow.md, output-contracts.md, and schemas/04-report-plan.md
- **rationale**: Catches P0-2
- **pseudo_code**: Extract section lists from step-03-confirm.md, workflow.md Step 8, output-contracts.md report section, 04-report-plan.md. Count sections. If counts differ, report mismatch with file locations.

### NEW-CHECK-3
- **category**: cross
- **description**: Contract `each:` path matches actual artifact structure (for at least one sample artifact)
- **rationale**: Catches P1-2 (layer-impact contract checks `impacts` but artifact has `capability_areas`)
- **pseudo_code**: For each contract.yaml with `each:` rules, if an artifact exists at the declared path, extract the actual key structure and verify the `each:` path resolves to non-empty data.

### NEW-CHECK-4
- **category**: docs
- **description**: Numeric range consistency check (same concept, same numbers across files)
- **rationale**: Catches P1-3 (plan.md length 300-600 vs 300-700)
- **pseudo_code**: Extract numeric ranges (e.g., "300-600", "300-700") from step files and output-contracts.md. For the same artifact, verify ranges match.

### NEW-CHECK-5
- **category**: cross
- **description**: Gate severity consistency check — same condition should have same severity across all gates
- **rationale**: Catches P1-11
- **pseudo_code**: For each condition checked by multiple gate scripts, compare the severity level assigned. Report mismatches.

### NEW-CHECK-6
- **category**: docs
- **description**: Step file must_not_produce vs output list contradiction check
- **rationale**: Catches P1-7
- **pseudo_code**: For each step file, extract must_not_produce list and output/artifact list. Flag items appearing in both.

### NEW-CHECK-7
- **category**: cross
- **description**: command.md stage step list vs DISTILL_STEP_ORDER vs workflow.md step headings three-way consistency
- **rationale**: Catches P1-4, P1-5 (partially — would have caught missing steps)
- **pseudo_code**: Extract step IDs from command.md stages, DISTILL_STEP_ORDER in gate script, and workflow.md headings. Diff the three sets. Report phantom and missing IDs per source.
