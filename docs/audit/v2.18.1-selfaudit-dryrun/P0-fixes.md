# P0 修复清单

> **执行原则**：按 P0-1 → P0-6 顺序做。每个 FIX 一个独立 commit。遇到现状与文档描述不一致先停下回报。

## P0-1 — contract-delta 03-context.md 残留 "contracts" 顶层键 + 缺 meta/requirement_id/layer

### 问题
v2.18.1 P0R2-6 修复了 contract-delta.contract.yaml 和 output-contracts.md，将顶层键统一为 `deltas` 并增加 meta/requirement_id/layer。但 `03-context.md` 的 contract-delta schema 未同步更新，仍用 `contracts` 顶层键且缺少 meta/requirement_id/layer 字段。

### 证据
- `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md:197` — `contracts:` (旧键)
- `plugins/prd-distill/skills/prd-distill/references/output-contracts.md:777` — `deltas:` (已修)
- `plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml:9` — `required_top_level: [meta, schema_version, deltas]`
- Agent C 实际产物也用 `deltas`，且含 meta/requirement_id/layer

### 修复
1. `grep -n "contracts:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md` 定位
2. 将 03-context.md:197 的 `contracts:` 改为 `deltas:`
3. 在 `deltas:` 之前添加 `meta:` 块（含 primary_source, ai_prd_source, requirement_ir_ref）
4. 在每个 delta 条目中添加 `requirement_id` 和 `layer` 字段

### relates_to
v2.18.1 P0R2-6 (partial residual)

### verify
```bash
grep -n "contracts:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md && echo "FAIL: still uses contracts" || echo "OK: contracts removed"
grep -n "requirement_id" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md | head -3
grep -n "deltas:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md | head -1
```

### commit
```
fix(audit-p0): [P0-1] contract-delta 03-context.md sync to deltas + meta/requirement_id/layer
```

## P0-2 — report.md 章节数 11 vs 12 漂移（4 处定义不一致）

### 问题
report.md 章节列表在 4 个文件中有不同定义：output-contracts.md 和 step-03-confirm.md 定义 11 个章节（无 PRD 质量摘要），而 04-report-plan.md 和 workflow.md Step 8 定义 12 个章节（含 §2 PRD 质量摘要）。LLM 按不同来源会产出不同结构的 report.md。

### 证据
- `plugins/prd-distill/skills/prd-distill/references/output-contracts.md:338-399` — 11 sections, §1 需求摘要 → §2 影响范围
- `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md:42-97` — 11 sections, self-check 检查 "11 个章节"
- `plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md:12-82` — 12 sections, 含 §2 PRD 质量摘要
- `plugins/prd-distill/skills/prd-distill/workflow.md:654-668` — 12 sections, 含 §2 PRD 质量摘要
- `scripts/distill-quality-gate.py:242-243` — 检查 PRD quality section 存在

### 修复
以 04-report-plan.md + workflow.md 为 SSOT（12 sections）：
1. 更新 output-contracts.md report.md 模板，在 §1 后插入 §2 PRD 质量摘要，后续章节重编号
2. 更新 step-03-confirm.md:42-97 章节列表为 12 个
3. 更新 step-03-confirm.md:207 self-check 从 "11 个章节" 改为 "12 个章节"
4. 更新 workflow.md:71 中 "§11 必须暴露" → "§12 必须暴露"

### verify
```bash
grep -c "PRD 质量摘要" plugins/prd-distill/skills/prd-distill/references/output-contracts.md plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md plugins/prd-distill/skills/prd-distill/workflow.md
```

### commit
```
fix(audit-p0): [P0-2] report.md section count unified to 12 with PRD quality summary
```

## P0-3 — step-03-confirm.md 绕过 report-confirmation gate

### 问题
step-03-confirm.md 的输出列表包含 report.md 和 plan.md，但未在两者之间设置 report-confirmation 暂停。workflow.md Step 8.1 要求 report 生成后暂停等用户确认，command.md 也说 "STOP after Step 8.1"。但 step-03 文件一次性产出两者，绕过了这个关键 gate。

### 证据
- `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md:20-24` — outputs: report.md, plan.md, reference-update-suggestions.yaml (一起列出)
- `plugins/prd-distill/skills/prd-distill/workflow.md:673-717` — Step 8.1 要求暂停等确认
- `.claude/commands/prd-distill.md:77` — "STOP after Step 8.1: Ask user to confirm report."

### 修复
在 step-03-confirm.md 中添加显式指令：
1. 在 report.md 生成后、plan.md 生成前插入 "HARD STOP: 生成 report-confirmation.yaml，暂停等用户确认"
2. 仅当 status: approved 时才继续 plan.md 生成
3. 将输出列表改为两段式：先 report.md + report-confirmation.yaml，再 plan.md

### verify
```bash
grep -A5 "report-confirmation" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md | head -10
grep -c "HARD STOP" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
```

### commit
```
fix(audit-p0): [P0-3] step-03-confirm add report-confirmation hard stop before plan
```

## P0-4 — step 文件编号 01-04 与 gate step IDs 0-9.x 无映射

### 问题
4 个 step 文件使用 01-04 编号，但 gate 系统使用 0, 1, 1.5-afprd, 1.5-quality, 2, 2.5, 3.1, 3.2, 4, 8, 8.1-confirm, 5, 6, 8.5, 8.6, 9 等编号。两者之间无映射表。step-01 覆盖 steps 0+1+1.5+2，step-02 覆盖 steps 2.5+3.1+3.2+4，step-03 覆盖 steps 8+8.1+5+6+7+8.5+8.6。LLM 无法从 step 文件名推断应传什么 gate ID。

### 证据
- `plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md:3` — `<current_step>1</current_step>` (但实际覆盖 0,1,1.5,2)
- `scripts/distill-step-gate.py:259-263` — `DISTILL_STEP_ORDER` 使用 0-9.x 编号
- `.claude/commands/prd-distill.md:35` — Step IDs 列表不含 2.6, 3.6, 7

### 修复
在 workflow.md 顶部添加映射表：

```markdown
## Step 文件 ↔ Gate Step ID 映射

| Step 文件 | 覆盖的 Gate Step IDs |
|---|---|
| step-01-parse.md | 0, 1, 1.5-afprd, 1.5-quality, 2 |
| step-02-classify.md | 2.5, 3.1, 3.2, 3.6, 4 |
| step-03-confirm.md | 8, 8.1-confirm, 5, 6, 7, 8.5, 8.6 |
| step-04-portal.md | 9 |
```

同时在每个 step 文件头部更新 `<current_step>` 为覆盖的完整列表。

### verify
```bash
grep -A6 "Step 文件.*Gate Step ID" plugins/prd-distill/skills/prd-distill/workflow.md | head -8
```

### commit
```
fix(audit-p0): [P0-4] add step file to gate step ID mapping table in workflow.md
```

## P0-5 — step 2.6 Context Pack 编号与执行顺序矛盾

### 问题
workflow.md 定义 "步骤 2.6: Context Pack" 编号为 2.6，暗示在 2.5 和 3 之间执行。但文本说 "在步骤 3（Layer Impact）完成后...生成"，实际执行顺序是 step 3 之后。同时 step 2.6 不在 command.md step ID list 中，无 gate enforcement。

### 证据
- `plugins/prd-distill/skills/prd-distill/workflow.md:382-388` — "步骤 2.6: Context Pack"
- `plugins/prd-distill/skills/prd-distill/workflow.md:386` — "在步骤 3（Layer Impact）完成后"
- `.claude/commands/prd-distill.md:35` — Step IDs 不含 2.6

### 修复
1. 将 workflow.md 中 "步骤 2.6" 重命名为 "步骤 3.5"（反映实际执行顺序：在 3.x 之后、4 之前）
2. 更新 command.md 和 SKILL.md 的 step ID 列表加入 "3.5"
3. 更新 distill-step-gate.py DISTILL_STEP_ORDER 加入 "3.5"（位于 "4" 之前）

### verify
```bash
grep -n "步骤 2.6\|步骤 3.5\|step 2.6\|step 3.5" plugins/prd-distill/skills/prd-distill/workflow.md
grep "3.5" .claude/commands/prd-distill.md scripts/distill-step-gate.py
```

### commit
```
fix(audit-p0): [P0-5] rename step 2.6 to 3.5 and add to gate system
```

## P0-6 — IR 追溯链断裂（4 个 REQ-ID 在 ai-friendly-prd.md 中无标题锚点）

### 问题
requirement-ir.yaml 中 3 条 requirement 引用了 4 个 REQ-ID（REQ-008, REQ-009, REQ-ALERT-001, REQ-SUPP-001），这些 ID 在 spec/ai-friendly-prd.md 中无对应的 `### REQ-*` 标题。追溯链从 requirement-ir 到 ai-friendly-prd 断裂。

### 证据
- `context/requirement-ir.yaml` — 引用 REQ-008, REQ-009, REQ-ALERT-001, REQ-SUPP-001
- `spec/ai-friendly-prd.md` — 仅有 REQ-001 到 REQ-007 和 REQ-010 的标题锚点
- 内容实际存在于 PRD 正文中（§7-§10），只是缺少 REQ-* 标题锚点

### 修复
这是产物质量问题（在 dive-bff 产物中），不可直接修改产物。应修改 prd-tools 指令：
1. 在 step-01-parse.md 或 workflow.md Step 1 中明确要求 "每个 REQ-ID 必须在 ai-friendly-prd.md 中有对应的 `### REQ-XXX` 标题"
2. 在 ai-friendly-prd.contract.yaml 中增加规则：检查所有 requirement-ir 引用的 REQ-ID 在 ai-friendly-prd.md 中存在标题锚点

### verify
```bash
# 验证指令已更新
grep -n "REQ-ID.*标题锚点\|标题.*REQ-XXX" plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md plugins/prd-distill/skills/prd-distill/workflow.md
```

### commit
```
fix(audit-p0): [P0-6] enforce REQ-ID heading anchors in ai-friendly-prd generation
```
