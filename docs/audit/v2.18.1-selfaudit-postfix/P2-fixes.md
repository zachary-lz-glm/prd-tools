# P2 修复清单

> **前置**：P0、P1 全部做完。P2 属于可维护性改进，可选做。每个 FIX 独立 commit，prefix `refactor(audit-p2): [P2-x] ...`。

## P2-1 — workflow.md graph_evidence_refs / graph_context_refs 未写入任何 schema

### 问题
workflow.md 引用 `graph_evidence_refs`（layer-impact、contract-delta 上下文）和 `graph_context_refs`（reference-update-suggestions），但这些字段不存在于 03-context.md 或 output-contracts.md 的任何 schema 中。

### 证据
- `workflow.md:511,575` — `graph_evidence_refs`
- `workflow.md:648` — `graph_context_refs: []`
- 03-context.md、output-contracts.md — 无此字段

### 修复
将这些字段添加到对应的 schema 文件，或在 workflow.md 标注为 aspirational。

### commit
```
refactor(audit-p2): [P2-1] document graph_evidence_refs and graph_context_refs as aspirational
```

## P2-2 — 文件过长 attention decay

### 问题
workflow.md 869 行 + output-contracts.md 1020 行 + SKILL.md 406 行。已添加 per-step loading guidance 但仍存在 attention pressure。

### 证据
- workflow.md: 869 行, step-02-deep-analysis.md: ~161 行

### 修复
在 step-02-deep-analysis.md 的各 stage 间添加 "PAUSE: verify stage N before proceeding" 标记。

### commit
```
refactor(audit-p2): [P2-2] add pause markers between stages in step-02-deep-analysis
```

## P2-3 — SKILL.md report stage 允许产物列表缺 context-pack.md

### 问题
SKILL.md Stage 2 allowed outputs 不包含 `context/context-pack.md`，但 step 3.5 会生成此文件。

### 证据
- `SKILL.md:46-52` — 无 `context/context-pack.md`
- `command.md:122` — Step 3.5 生成 `context/context-pack.md`

### 修复
在 SKILL.md Stage 2 allowed outputs 中添加 `context/context-pack.md`。

### commit
```
refactor(audit-p2): [P2-3] add context-pack.md to SKILL.md report stage outputs
```

## P2-4 — reference step-05-portal step ID 5 不在 command.md 或 SKILL.md

### 问题
step-05-portal.md 使用 `current_step: 5`，但 reference 的 command.md 和 SKILL.md step ID 列表只到 step 4。Step 5 未在 step ID 列表中。

### 证据
- `step-05-portal.md:2` — `current_step: 5`
- `.claude/commands/reference.md:59` — Step IDs 无 5

### 修复
在 command.md 和 SKILL.md 添加 step 5，或调整 step-05-portal.md 的 step ID。

### commit
```
refactor(audit-p2): [P2-4] add reference step 5 portal to command and SKILL step IDs
```

## P2-5 — contract-delta schema_version 03-context.md "2.0" vs output-contracts "4.0"

### 问题
03-context.md 的 contract-delta schema_version 为 "2.0"，output-contracts.md 为 "4.0"。

### 证据
- `03-context.md:194` — `schema_version: "2.0"`
- `output-contracts.md:781` — `schema_version: "4.0"`

### 修复
统一为 output-contracts.md 的值（更新 03-context.md）。

### commit
```
refactor(audit-p2): [P2-5] align contract-delta schema_version across files
```

## P2-6 — contract-delta sample requirement_id "IR-001" (stale) vs "REQ-001"

### 问题
output-contracts.md contract-delta 示例中 requirement_id 为 "IR-001"，应为 "REQ-001"。

### 证据
- `output-contracts.md:794` — `requirement_id: "IR-001"`
- 其他文件统一使用 `REQ-XXX` 格式

### 修复
更新 output-contracts.md:794 为 `requirement_id: "REQ-001"`，同步到 reference。

### commit
```
refactor(audit-p2): [P2-6] fix contract-delta sample requirement_id from IR-001 to REQ-001
```

## P2-7 — SKILL.md report-confirmation template 与 workflow.md 不一致

### 问题
SKILL.md report-confirmation 模板有 pre-filled 示例值，workflow.md 有空模板值。两者应统一。

### 证据
- `SKILL.md:298-303` — 有示例值 + 重复 blocked_reason
- `workflow.md:708-723` — 空模板

### 修复
以 workflow.md 为 SSOT，将 SKILL.md 改为引用 workflow.md 而非重复。

### commit
```
refactor(audit-p2): [P2-7] deduplicate report-confirmation template, reference workflow.md
```

## P2-8 — step-01-parse.md 声称覆盖 gate steps 0,1,1.5,2 但正文只覆盖 0 和 2

### 问题
step-01-parse.md 的 current_step 包含 0, 1, 1.5-afprd, 1.5-quality, 2，但执行段落仅描述 PRD ingestion（step 0）和 requirement IR（step 2）。Step 1 和 Step 1.5 的指令在 workflow.md 中而非 step 文件中。

### 证据
- `step-01-parse.md:3` — `current_step: 0, 1, 1.5-afprd, 1.5-quality, 2`
- `step-01-parse.md` body — 无 Step 1 (Evidence Ledger) 或 Step 1.5 (AI-friendly PRD) 指令

### 修复
在 step-01-parse.md 添加交叉引用："For Step 1, see workflow.md Step 1. For Step 1.5, see workflow.md Step 1.5."

### commit
```
refactor(audit-p2): [P2-8] add cross-references in step-01-parse for steps 1 and 1.5
```

## P2-9 — output-contracts.md warn 级别项指向 §11（应为 §12）

### 问题
output-contracts.md 中一处 warn 级别风险要求写入 §11，应为 §12。

### 证据
- `output-contracts.md:125` — "必须在 report.md §11 中暴露风险"
- `workflow.md:115` — 正确使用 §12

### 修复
更新 output-contracts.md:125 为 §12，同步到 reference。

### commit
```
refactor(audit-p2): [P2-9] update output-contracts warn reference from §11 to §12
```

## P2-10 — step-04-portal verify 命令使用相对路径

### 问题
step-04-portal.md self-check 的 verify 命令使用 `portal.html`（相对路径），从 repo root 执行会失败。

### 证据
- `step-04-portal.md:65` — `grep ... portal.html`

### 修复
使用完整路径 `_prd-tools/distill/<slug>/portal.html` 或添加路径说明。

### commit
```
refactor(audit-p2): [P2-10] use full distill path in step-04-portal verify command
```

## P2-11 — command.md report stage "8.1" vs step IDs "8.1-confirm"

### 问题
command.md subcommand table (line 23) 使用 "8.1" 而 step ID 列表和 gate 使用 "8.1-confirm"。

### 证据
- `.claude/commands/prd-distill.md:23` — "Steps 2.5→...→8.1"
- `.claude/commands/prd-distill.md:35` — Step IDs 列表使用 "8.1-confirm"

### 修复
统一为 "8.1-confirm"。

### commit
```
refactor(audit-p2): [P2-11] normalize 8.1 to 8.1-confirm in command.md subcommand table
```

## P2-12 — layer-impact contract 缺 schema_version in required_top_level

### 问题
layer-impact.contract.yaml 的 required_top_level 只有 `layers`，缺少 `schema_version`。

### 证据
- `contracts/layer-impact.contract.yaml:4` — `required_top_level: [layers]`
- `output-contracts.md:718-719` — schema 有 `schema_version: "5.0"`

### 修复
在 contract 的 required_top_level 中添加 `schema_version`。

### commit
```
refactor(audit-p2): [P2-12] add schema_version to layer-impact contract required_top_level
```

## P2-13 — SKILL.md lists 3.5/3.6 in step IDs but never describes them

### 问题
SKILL.md step ID 列表包含 3.5 和 3.6，但 SKILL.md 正文中未描述这两个步骤的功能。

### 证据
- `SKILL.md:83` — step IDs 包含 3.5, 3.6
- `SKILL.md` body — 无 3.5 或 3.6 的说明段落

### 修复
在 SKILL.md 中为 3.5 和 3.6 添加简短说明。

### commit
```
refactor(audit-p2): [P2-13] add brief descriptions for steps 3.5 and 3.6 in SKILL.md
```
