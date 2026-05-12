# P1 修复清单

> **前置**：P0 全部做完并通过验证。每个 FIX 独立 commit。commit prefix: `fix(audit-p1): [P1-x] ...`

## P1-1 — output-contracts.md requirement-ir meta 缺 primary_source 字段

### 问题
workflow.md Step 2 和 requirement-ir.contract.yaml 都要求 `meta.primary_source`，但 output-contracts.md 的 requirement-ir schema meta 块没有定义此字段。LLM 按 schema 生成会漏掉该字段，导致 gate 失败。

### 证据
- `workflow.md:358` — "`meta.primary_source` must be set to `_ingest/document.md`"
- `scripts/contracts/requirement-ir.contract.yaml:7-9` — 检查 `meta.primary_source`
- `output-contracts.md:634-640` — meta 块无 `primary_source`

### 修复
1. 在 `output-contracts.md:634` 的 meta 块中添加 `primary_source: "_ingest/document.md"`
2. 同步到 `plugins/reference/skills/reference/references/output-contracts.md`

### relates_to
dryrun A-2/A-10/A-24（前次未修到 output-contracts schema 层）

### verify
```bash
grep "primary_source" plugins/prd-distill/skills/prd-distill/references/output-contracts.md
diff plugins/prd-distill/skills/prd-distill/references/output-contracts.md plugins/reference/skills/reference/references/output-contracts.md
```

### commit
```
fix(audit-p1): [P1-1] add primary_source to output-contracts requirement-ir meta schema
```

## P1-2 — layer-impact output-contracts schema 仍用 impacts（前次修复引入的不一致）

### 问题
前次 P1-2 修复将 contract 从 `impacts` 改为 `capability_areas`，但 output-contracts.md 的 layer-impact schema 仍使用 `layers.frontend.impacts` 格式。contract 和 schema 不匹配。

### 证据
- `contracts/layer-impact.contract.yaml` — `each: "layers.*.capability_areas"`
- `output-contracts.md:720-752` — 使用 `layers.frontend.impacts` / `layers.bff.impacts`

### 修复
1. 更新 `output-contracts.md` layer-impact schema，将 `impacts` 改为 `capability_areas`
2. 同步到 reference 插件的 output-contracts.md

### relates_to
dryrun P1-2 (capability_areas 修复的残留)

### verify
```bash
grep "impacts" plugins/prd-distill/skills/prd-distill/references/output-contracts.md | grep -i layer
# 预期：无 impacts 出现在 layer-impact 上下文中
```

### commit
```
fix(audit-p1): [P1-2] sync output-contracts layer-impact schema to capability_areas
```

## P1-3 — reference mode description drift between SKILL.md and mode-selection.schema.md

### 问题
SKILL.md 描述模式使用不同措辞：`B2 = health check` vs schema `B2 = Lightweight + cross-validation`；`C = quality gate` vs schema `C = Contract-only reference`。

### 证据
- `plugins/reference/skills/reference/SKILL.md:73-74` — "B2 = health check", "C = quality gate"
- `plugins/reference/skills/reference/references/mode-selection.schema.md:31-32` — 不同的描述

### 修复
统一为 schema 文件的措辞，更新 SKILL.md。

### verify
```bash
grep "health check\|quality gate" plugins/reference/skills/reference/SKILL.md
# 预期：无旧描述出现
```

### commit
```
fix(audit-p1): [P1-3] align reference mode descriptions across SKILL.md and schema
```

## P1-4 — Critique Pass (Step 3.6) orphaned from all execution sequences

### 问题
Step 3.6 在 workflow.md 有完整定义，在 gate STEP_TABLE 和 step ID 列表中存在，但不在 command.md 或 SKILL.md 任何 stage 的执行序列中。LLM 永远不会触发 critique pass。

### 证据
- `workflow.md:520-559` — 完整的 Step 3.6 定义
- `command.md:65` — report stage 序列无 3.6
- `SKILL.md:44` — report stage 序列无 3.6

### 修复
在 command.md 和 SKILL.md 的 report stage 中，在 Step 4 后添加 3.6（advisory），或标注为 "可选：如果 workflow.md 3.6 段被加载则执行"。

### verify
```bash
grep "3.6" .claude/commands/prd-distill.md | grep -v "Step IDs"
```

### commit
```
fix(audit-p1): [P1-4] add step 3.6 critique pass to report stage execution order
```

## P1-5 — SKILL.md report stage 序列缺少 step 3.5

### 问题
前次 P0-5 将 step 2.6 重命名为 3.5 并更新了 command.md，但未同步 SKILL.md 的 report stage 序列。SKILL.md 仍显示 "2.5 → 3.1 → 3.2 → 4 → 8 → 8.1-confirm"。

### 证据
- `SKILL.md:44` — "Steps: 2.5 → 3.1 → 3.2 → 4 → 8 → 8.1-confirm"（缺 3.5）
- `command.md:65` — "Steps: 2.5 → 3.1 → 3.2 → 3.5 → 4 → 8 → 8.1-confirm"（有 3.5）

### 修复
更新 SKILL.md report stage 序列为 "2.5 → 3.1 → 3.2 → 3.5 → 4 → 8 → 8.1-confirm"。

### relates_to
dryrun P0-5 (step 2.6→3.5 重命名的残留)

### verify
```bash
grep "2.5.*3.1.*3.2.*3.5" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### commit
```
fix(audit-p1): [P1-5] add step 3.5 to SKILL.md report stage sequence
```

## P1-6 — SKILL.md plan stage 序列缺少 step 7

### 问题
前次 P1-5 将 step 7 加入 command.md plan stage，但未同步 SKILL.md。

### 证据
- `SKILL.md:59` — "Steps: 5 → 6 → 8.5 → 8.6 → 9"（缺 7）
- `command.md:81` — "Steps: 5 → 6 → 7 → 8.5 → 8.6 → 9"（有 7）

### 修复
更新 SKILL.md plan stage 序列为 "5 → 6 → 7 → 8.5 → 8.6 → 9"。

### relates_to
dryrun P1-5 (step 7 加入的残留)

### verify
```bash
grep "5.*6.*7.*8.5.*8.6.*9" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### commit
```
fix(audit-p1): [P1-6] add step 7 to SKILL.md plan stage sequence
```

## P1-7 — SKILL.md 多处 §11 引用应为 §12（12 章节模板更新残留）

### 问题
前次 P0-2 将 report.md 从 11 章节更新为 12 章节（新增 §2 PRD 质量摘要），更新了 workflow.md 的 §11→§12 引用，但 SKILL.md 仍有多处 §11 引用指向阻塞问题/暴露项。新模板中 §11 = Top Open Questions，§12 = 阻塞问题与待确认项。

### 证据
- `SKILL.md:208` — "§11 阻塞项"
- `SKILL.md:248` — "report.md §11 暴露"
- `SKILL.md:250` — "report.md §11"
- `SKILL.md:396` — "report.md §11 最重要阻塞项"
- `SKILL.md:351` — "report.md §11 必须暴露"

### 修复
将 SKILL.md 中所有指向"阻塞问题/暴露/风险"的 §11 引用更新为 §12。

### relates_to
dryrun P0-2 (12 章节更新的残留)

### verify
```bash
grep -n "§11" plugins/prd-distill/skills/prd-distill/SKILL.md
# 预期：仅出现在 §11 = Top Open Questions 的正确上下文中
```

### commit
```
fix(audit-p1): [P1-7] update SKILL.md §11 references to §12 for blocker items
```

## P1-8 — evidence.yaml 字段名漂移（前次 P2-10 修复引入的反向不一致）

### 问题
前次 P2-10 将 03-context.md evidence schema 从 `kind/locator/summary` 改为 `type/desc`（对齐实际 LLM 产物），但未同步 output-contracts.md（仍用 `kind/locator/summary`）。现在两个 schema 文件不一致。

### 证据
- `03-context.md:56-58` — `type:`, `desc:`（已改）
- `output-contracts.md:614-617` — `kind:`, `locator:`, `summary:`（未改）

### 修复
以 03-context.md 的 `type/desc` 为准（匹配实际 LLM 产物），更新 output-contracts.md evidence schema。同步到 reference 插件。

### relates_to
dryrun P2-10 (evidence schema 对齐的残留)

### verify
```bash
grep "kind:" plugins/prd-distill/skills/prd-distill/references/output-contracts.md | grep -i "prd\|tech_doc\|code"
# 预期：无 kind 字段在 evidence 上下文中
```

### commit
```
fix(audit-p1): [P1-8] sync output-contracts evidence schema to type/desc
```
