# Selfcheck 覆盖缺口分析

## Selfcheck 基线

| ID | Category | Status | Description |
|----|----------|--------|-------------|
| C1 | contracts | pass | all contract YAML files parse |
| C2 | contracts | pass | required_top_level documented in output-contracts |
| C3 | contracts | warn | dive-bff snapshot not found |
| D1 | docs | pass | workflow.md no duplicate headings |
| D2 | docs | pass | yaml blocks no smart quotes |
| D3 | docs | pass | step file references resolve |
| D4 | docs | warn | 4 within-skill gate gaps |
| D5 | docs | pass | current_step matches filename prefix |
| D6 | docs | pass | numbered lists sequential |
| S1 | scripts | pass | all python files compile |
| S2 | scripts | pass | yaml imports consistent |
| S3 | scripts | pass | tool-version defaults aligned |
| S4 | scripts | pass | gate --help works |
| X1 | cross | pass | workflow step IDs in STEP_TABLE |
| X4 | cross | pass | VERSION lockstep across 5 files |

**总计**: 14 pass · 1 warn · 0 fail

## Per-finding 覆盖分析

| Merged ID | Covered? | By which check | Note |
|-----------|----------|---------------|------|
| P0-1 | NO | — | duplicate YAML key 不被任何 check 检测 |
| P1-1 | NO | — | schema 字段名不在 output-contracts 中不被检测 |
| P1-2 | NO | — | contract vs schema 字段名漂移不被检测 |
| P1-3 | NO | — | 跨文件 description drift 不被检测 |
| P1-4 | PARTIAL | X1 | X1 检查 step ID 在 gate table 中存在，但不检查 execution sequence |
| P1-5 | NO | — | SKILL.md step sequence 不被检测 |
| P1-6 | NO | — | 同 P1-5 |
| P1-7 | NO | — | §11/§12 引用漂移不被检测 |
| P1-8 | NO | — | 跨 schema 文件字段名不一致不被检测 |
| P2-1 | NO | — | aspirational 字段不被检测 |
| P2-2 | NO | — | 文件长度/attention decay 不被检测 |
| P2-3 | NO | — | SKILL.md allowed outputs 不被检测 |
| P2-4 | NO | — | reference step ID 缺失不被检测 |
| P2-5 | NO | — | schema_version 跨文件不一致不被检测 |
| P2-6 | NO | — | sample value drift 不被检测 |
| P2-7 | NO | — | 模板重复/漂移不被检测 |
| P2-8 | NO | — | step file 内容完整性不被检测 |
| P2-9 | NO | — | § 引用漂移不被检测 |
| P2-10 | NO | — | verify 命令路径不被检测 |
| P2-11 | NO | — | step ID 格式不一致不被检测 |
| P2-12 | NO | — | contract required_top_level 完整性不被检测 |
| P2-13 | NO | — | SKILL.md 内容完整性不被检测 |

**覆盖率: 1/22 (4.5%)** — 仅 P1-4 被 X1 部分覆盖。

## 新增 check 建议

### NEW-CHECK-D7: 检测 YAML 模板中的重复 key

```
category: docs
description: SKILL.md and workflow.md YAML templates have no duplicate keys
rationale: Catches P0-1 (duplicate blocked_reason)
suggested_id: D7
pseudo_code: |
  For each YAML code block in SKILL.md and workflow.md:
    Parse as YAML (tolerating template placeholders)
    If duplicate keys detected → fail
```

### NEW-CHECK-D8: SKILL.md step sequences match command.md

```
category: docs
description: SKILL.md stage step sequences match command.md execution order
rationale: Catches P1-5, P1-6, P2-3 (SKILL.md missing steps/outputs)
suggested_id: D8
pseudo_code: |
  Extract step sequences from SKILL.md stages
  Extract step sequences from command.md stages
  Compare: every step in command.md stage must appear in SKILL.md stage
  Report mismatches
```

### NEW-CHECK-C4: Schema field names consistent across schema files

```
category: contracts
description: Field names in 03-context.md schemas match output-contracts.md
rationale: Catches P1-1, P1-2, P1-8, P2-5 (cross-schema field name drift)
suggested_id: C4
pseudo_code: |
  For each artifact defined in both 03-context.md and output-contracts.md:
    Extract field names from YAML blocks in both files
    Compare: field names must match exactly
    Report mismatches with file:line references
```

### NEW-CHECK-X5: Section references (§N) consistent across files

```
category: cross
description: §N references in SKILL.md, workflow.md, output-contracts.md are consistent
rationale: Catches P1-7, P2-9 (§11/§12 drift after section count change)
suggested_id: X5
pseudo_code: |
  Define SSOT section map from 04-report-plan.md
  For each §N reference in SKILL.md, workflow.md, output-contracts.md:
    Verify §N points to the correct section per SSOT
  Report mismatches
```

### NEW-CHECK-X6: command.md step IDs match all stage sequences

```
category: cross
description: Every step ID in command.md list appears in at least one stage sequence
rationale: Catches P1-4, P2-11 (orphaned step IDs)
suggested_id: X6
pseudo_code: |
  Extract all step IDs from command.md Step IDs line
  Extract all step IDs from stage sequences
  Any ID in the full list but not in any sequence → warn
```
