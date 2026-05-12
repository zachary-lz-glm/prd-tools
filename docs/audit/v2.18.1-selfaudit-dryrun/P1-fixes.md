# P1 修复清单

> **前置**：P0 全部做完并通过验证。每个 FIX 独立 commit。commit prefix: `fix(audit-p1): [P1-x] ...`

## P1-1 — requirement-ir 输入源矛盾 + schema-artifact 漂移

### 问题
workflow.md Step 1.5 说 "Step 2 必须读取 spec/ai-friendly-prd.md 作为主输入"，但 Step 2 自身说 "主输入：_ingest/document.md"。同时 03-context.md 描述 requirement-ir 为 "原始 PRD 的结构化 IR"，output-contracts.md 描述为 "AI-friendly PRD 的结构化 IR"。实际产物字段与 schema v5.0 严重漂移（10 个 schema 必填字段缺失）。

### 证据
- `workflow.md:272` — "Step 2 必须读取 spec/ai-friendly-prd.md 作为主输入"
- `workflow.md:284-285` — "主输入：_ingest/document.md（原始 PRD 全文）"
- `03-context.md:71` — "Requirement IR 是原始 PRD 的结构化 IR"
- `output-contracts.md:619` — "Requirement IR 是 AI-friendly PRD 的结构化 IR"
- Agent C: 产物缺少 statement, priority, intent, business_entities, rules, target_layers, confirmation, confidence, risk_flags；多出 type, block_ref, description, layer_impact

### 修复
1. 统一 workflow.md Step 2 主输入描述为 "_ingest/document.md 为主输入，spec/ai-friendly-prd.md 为 REQ-ID 索引"
2. 统一 03-context.md 和 output-contracts.md 的描述措辞
3. 评估 03-context.md requirement-ir schema v5.0 是否为 aspirational；如是，更新 schema 文档为 v1.0 实际格式

### verify
```bash
grep -n "主输入" plugins/prd-distill/skills/prd-distill/workflow.md | head -5
grep -n "Requirement IR 是" plugins/prd-distill/skills/prd-distill/references/output-contracts.md plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md
```

### commit
```
fix(audit-p1): [P1-1] requirement-ir input source and schema description alignment
```

## P1-2 — layer-impact contract 假阳性（impacts vs capability_areas）

### 问题
layer-impact.contract.yaml 检查 `layers.*.impacts` 但实际产物使用 `layers.*.capability_areas`。contract validator 因找不到 `impacts` 键而跳过检查，产生假 PASS。同时 03-context.md schema 定义 dict-keyed layers，但产物用 list-of-dicts。

### 证据
- `plugins/prd-distill/skills/prd-distill/references/contracts/layer-impact.contract.yaml` — `each: "layers.*.impacts"`
- Agent C: 产物结构为 `layers: [{layer: "bff", capability_areas: [...]}]`
- `03-context.md`: `layers: {frontend: {impacts: [...]}, bff: {impacts: [...]}}`

### 修复
1. 更新 layer-impact.contract.yaml 将 `each: "layers.*.impacts"` 改为 `each: "layers.*.capability_areas"`
2. 同步更新 03-context.md layer-impact schema 或标注 v5.0 为 aspirational

### verify
```bash
grep "impacts\|capability_areas" plugins/prd-distill/skills/prd-distill/references/contracts/layer-impact.contract.yaml
```

### commit
```
fix(audit-p1): [P1-2] layer-impact contract use capability_areas not impacts
```

## P1-3 — plan.md 长度指引冲突（300-600 vs 300-700）

### 问题
step-03-confirm.md 内部自相矛盾：写作规则说 "建议总长度控制在 300-600 行"，self-check 说 "plan.md 长度在 300-700 行范围内"，output-contracts.md 也说 300-700。

### 证据
- `steps/step-03-confirm.md:186` — "建议总长度控制在 300-600 行"
- `steps/step-03-confirm.md:214` — "plan.md 长度在 300-700 行范围内"
- `references/output-contracts.md:546` — "建议总长度控制在 300-700 行"

### 修复
统一为 300-700：更新 step-03-confirm.md:186 为 "建议总长度控制在 300-700 行"。

### verify
```bash
grep -n "300-600\|300-700" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
```

### commit
```
fix(audit-p1): [P1-3] plan.md length guidance unified to 300-700
```

## P1-4 — step 3.6 Critique Pass 无 gate enforcement

### 问题
workflow.md 定义 "步骤 3.6: Critique Pass (Two-Pass Critic)" 要求在 steps 1.5, 2, 3.2, 4 之后执行。但 3.6 不在 command.md step ID 列表中，无 gate 校验。LLM 按 command.md 执行时会跳过所有 critique pass。

### 证据
- `workflow.md:504-543` — "步骤 3.6: Critique Pass"
- `.claude/commands/prd-distill.md:35` — Step IDs 不含 3.6

### 修复
在 command.md 和 SKILL.md 的 step ID 列表中添加 "3.6"（critique pass 作为可选步骤，标记为 advisory）。

### verify
```bash
grep "3.6" .claude/commands/prd-distill.md
```

### commit
```
fix(audit-p1): [P1-4] add step 3.6 critique to command step IDs as advisory
```

## P1-5 — step 7 Reference Update 无执行位置

### 问题
Step 7 (Reference 回流) 在 workflow.md 和 STEP_TABLE 中有定义，但不在 command.md 任何 stage 的步骤列表中，也不在 DISTILL_STEP_ORDER 中。LLM 无法确定何时执行此步骤。

### 证据
- `workflow.md:610-651` — "步骤 7：Reference 回流"
- `.claude/commands/prd-distill.md:24` — plan stage: "5->6->8.5->8.6->9" (无 7)

### 修复
在 command.md plan stage 步骤列表中加入 step 7（位于 step 6 之后）。

### verify
```bash
grep -A2 "plan:" .claude/commands/prd-distill.md
```

### commit
```
fix(audit-p1): [P1-5] add step 7 to plan stage execution order
```

## P1-6 — step 编号 vs 执行顺序不一致

### 问题
Step 8 (Report) 在 step 5 (Plan) 之前执行。Numbering 暗示 5 在 8 之前。LLM 按编号顺序阅读时会困惑。

### 证据
- command.md: spec stage 0→1→1.5→2, report stage 2.5→...→4→8→8.1, plan stage 5→6→8.5→8.6→9

### 修复
在 workflow.md 顶部添加醒目注释："Step numbers are logical IDs, NOT execution order. Follow the three-stage execution sequence from command.md."

### verify
```bash
grep "logical IDs\|NOT execution order" plugins/prd-distill/skills/prd-distill/workflow.md
```

### commit
```
fix(audit-p1): [P1-6] add step numbering caveat to workflow.md header
```

## P1-7 — step-01-parse must_not_produce 与输出矛盾

### 问题
step-01-parse.md:6 列 `context/requirement-ir.yaml` 在 must_not_produce 中，但同文件 Goal 和 Execution 段落又说要产出此文件。

### 证据
- `steps/step-01-parse.md:6` — `must_not_produce: context/requirement-ir.yaml`
- `steps/step-01-parse.md:73` — requirement-ir.yaml 列为输出
- `steps/step-01-parse.md:106` — "产出 context/requirement-ir.yaml"

### 修复
从 must_not_produce 列表中移除 `context/requirement-ir.yaml`。

### verify
```bash
grep "must_not_produce" plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md
```

### commit
```
fix(audit-p1): [P1-7] remove requirement-ir from step-01 must_not_produce
```

## P1-8 — query-plan.yaml phases 未充分说明

### 问题
workflow.md Step 2.6 定义 query-plan.yaml 的三个 phase (seed_anchors, impact_hints, p0_requirements) 但未说明每个 phase 条目的结构。

### 证据
- `workflow.md:373-380` — phases 定义为空数组，仅有单行注释

### 修复
添加注释说明 query-plan.yaml 由 context-pack.py 脚本自动生成，LLM 不需要手写。如需手写，每个 entry 为 string。

### verify
```bash
grep -A3 "query-plan" plugins/prd-distill/skills/prd-distill/workflow.md | head -5
```

### commit
```
fix(audit-p1): [P1-8] clarify query-plan.yaml is script-generated
```

## P1-9 — report-confirmation revision_requests 格式漂移

### 问题
SKILL.md 定义 revision_requests 为空数组 `[]`，未定义条目结构。workflow.md 定义了条目结构 `section/issue/expected_change`。

### 证据
- `SKILL.md:282` — `revision_requests: []`
- `workflow.md:703-705` — `revision_requests: - section: '' issue: '' expected_change: ''`

### 修复
在 SKILL.md 中补充 revision_requests 的条目结构定义。

### verify
```bash
grep -A3 "revision_requests" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### commit
```
fix(audit-p1): [P1-9] add revision_requests structure to SKILL.md
```

## P1-10 — readiness 字段名 task_executability vs plan_quality

### 问题
readiness-report.yaml 的 YAML 字段名是 `task_executability`，但评分表标签是 `plan_quality`。LLM 按表生成时可能用 `plan_quality` 作为字段名。

### 证据
- `05-readiness.md:21` — `task_executability: 0` (YAML 字段)
- `05-readiness.md:50` — `| plan_quality | 15 |` (表标签)
- `output-contracts.md:856` — `task_executability: 0`
- `output-contracts.md:885` — `| plan_quality | 15 |`

### 修复
统一为 `task_executability`（更精确）：更新两个文件中的表标签 `plan_quality` 为 `task_executability`。

### verify
```bash
grep "plan_quality\|task_executability" plugins/prd-distill/skills/prd-distill/references/schemas/05-readiness.md plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```

### commit
```
fix(audit-p1): [P1-10] readiness table label unified to task_executability
```

## P1-11 — gate severity 不一致（layer-impact anchors）

### 问题
distill-quality-gate.py 将 layer-impact 缺少 code_anchors 视为 `warning`，但 distill-workflow-gate.py 视为 `fail`。同一产物可能过 quality gate 但 fail workflow gate。

### 证据
- `scripts/distill-quality-gate.py:194` — `status = 'warning'`
- `scripts/distill-workflow-gate.py:262` — `status = 'fail'`

### 修复
统一为 `warning`（产物结构正确，只是不够完善）。更新 distill-workflow-gate.py:262。

### verify
```bash
grep -n "has_code_anchors\|has_fallback" scripts/distill-quality-gate.py scripts/distill-workflow-gate.py
```

### commit
```
fix(audit-p1): [P1-11] unify layer-impact anchor severity to warning
```

## P1-12 — project-profile.yaml 无 fallback 规则

### 问题
step-02-classify.md 引用 project-profile.yaml 的 build_output_dirs 来决定扫描目录，但未说明文件不存在时如何处理。

### 证据
- `steps/step-02-classify.md:66` — "按项目实际 project-profile.yaml 的 build_output_dirs 决定"

### 修复
在 step-02-classify.md 添加 fallback 规则："如果 project-profile.yaml 不存在或缺少 build_output_dirs，默认扫描 build/ 和 dist/（如存在）"。

### verify
```bash
grep -A2 "project-profile\|build_output_dirs\|fallback" plugins/prd-distill/skills/prd-distill/steps/step-02-classify.md
```

### commit
```
fix(audit-p1): [P1-12] add project-profile.yaml fallback rule
```

## P1-13 — workflow.md 853 行过长（attention decay）

### 问题
workflow.md 853 行 + output-contracts.md 1015 行，合计 1800+ 行指令在 LLM 上下文中同时加载。后段步骤的指令质量可能因 attention decay 下降。

### 证据
- `workflow.md`: 853 lines
- `output-contracts.md`: 1015 lines

### 修复
在 workflow.md 顶部添加 per-step 加载指引："每个 step 只需加载 workflow.md 对应段落 + step 文件 + output-contracts.md 对应 schema 段，不需要全文加载。"

### verify
```bash
grep "per-step\|不需要全文" plugins/prd-distill/skills/prd-distill/workflow.md
```

### commit
```
fix(audit-p1): [P1-13] add per-step loading guidance to reduce attention decay
```
