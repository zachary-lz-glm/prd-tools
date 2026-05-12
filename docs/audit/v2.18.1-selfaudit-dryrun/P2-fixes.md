# P2 修复清单

> **前置**：P0、P1 全部做完。P2 属于可读性/可维护性改进，可选做。每个 FIX 独立 commit，prefix `refactor(audit-p2): [P2-x] ...`。

## P2-1 — SKILL.md 执行步骤编号 1-17 与 gate ID 0-9 不对应

### 问题
SKILL.md "执行步骤" 段落用 1-17 编号，gate 系统用 0-9.x。两套编号系统无映射。

### 证据
- `SKILL.md:316-359` — numbered steps 1-17
- `.claude/commands/prd-distill.md:35` — gate step IDs

### 修复
在 SKILL.md "执行步骤" 段落添加注释："以下编号为逻辑描述顺序，对应 gate step IDs 见 command.md。"

### verify
```bash
grep "gate step IDs\|逻辑描述顺序" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### commit
```
refactor(audit-p2): [P2-1] SKILL.md execution steps add gate ID reference
```

## P2-2 — 00-directory-structure.md 文件列表不完整

### 问题
00-directory-structure.md 缺少 spec/ai-friendly-prd.md、context/prd-quality-report.yaml、context/query-plan.yaml 等多个文件。

### 证据
- `00-directory-structure.md:33-53` — distill 目录列表
- `output-contracts.md:9-60` — 更完整的列表

### 修复
以 output-contracts.md 为 SSOT，更新 00-directory-structure.md 目录列表。或在 00-directory-structure.md 添加注释："完整文件列表以 output-contracts.md 为准。"

### verify
```bash
grep "ai-friendly-prd" plugins/prd-distill/skills/prd-distill/references/schemas/00-directory-structure.md
```

### commit
```
refactor(audit-p2): [P2-2] directory structure doc add output-contracts SSOT note
```

## P2-3 — "辅助层"概念未正式定义

### 问题
output-contracts.md 多处使用 "辅助层" 标注（query-plan, context-pack, final-quality-gate, prd-quality-report），但未定义辅助层的行为差异。

### 证据
- `output-contracts.md:312,926,940,960` — "辅助层定位" 出现 4 处

### 修复
在 output-contracts.md 顶部术语表添加定义："辅助层产出：必须存在且通过 gate 校验，但不是用户的首要阅读目标。"

### verify
```bash
grep "辅助层产出\|辅助层定义" plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```

### commit
```
refactor(audit-p2): [P2-3] define auxiliary layer concept in output-contracts.md
```

## P2-4 — step 文件 self-check 格式不一致

### 问题
step-02-classify.md 使用 [M] verify: expect: 格式，step-04-portal.md 的 [M] 缺 verify/expect，step-01-parse.md 无 Self-Check 段落。

### 证据
- `step-04-portal.md:63` — `[M] portal.html 渲染完成后...` (无 verify/expect)
- `step-01-parse.md` — 无 Self-Check 段落

### 修复
1. step-04-portal.md 添加 verify/expect 对
2. step-01-parse.md 添加 Self-Check 段落（覆盖 _ingest/ 文件完整性）

### verify
```bash
grep -c "verify:" plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md plugins/prd-distill/skills/prd-distill/steps/step-04-portal.md
```

### commit
```
refactor(audit-p2): [P2-4] normalize step file self-check format
```

## P2-5 — 禁止行为列表 50+ 过长（attention dilution）

### 问题
跨 SKILL.md、workflow.md、command.md 的 "禁止/不得/MUST NOT" 约 50+ 条，LLM 难以全部跟踪。

### 证据
- SKILL.md 约 30+ 条禁止
- workflow.md + command.md 另有 20+

### 修复
在 SKILL.md 中添加 "Hard Constraints Reference" 段落，将关键禁止项（<10 条）提炼为简表，其余标注为 "详见 workflow.md 对应步骤"。

### verify
```bash
grep "Hard Constraints Reference\|关键禁止" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### commit
```
refactor(audit-p2): [P2-5] consolidate prohibition list into hard constraints reference
```

## P2-6 — source_blocks 字段类型不一致（string[] vs object[]）

### 问题
03-context.md 定义 source_blocks 为 object array `{block_id, type}`，output-contracts.md 为 plain array，step-01-parse.md 示例为 string array。

### 证据
- `03-context.md:104-107` — object array
- `output-contracts.md:651-652` — plain array
- `step-01-parse.md:132` — string array `["document.md:L10-16"]`

### 修复
统一为 03-context.md 的 object 格式（更结构化）。更新 output-contracts.md 和 step-01-parse.md 示例。

### verify
```bash
grep -A2 "source_blocks:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```

### commit
```
refactor(audit-p2): [P2-6] source_blocks type unified to object array
```

## P2-7 — deprecated score 字段永久双轨

### 问题
output-contracts.md 标注 `score` 为 deprecated，但 distill-quality-gate.py 仍接受 `score` 和 `overall_score`，无移除计划。

### 证据
- `output-contracts.md:221` — "score (int, 0-100, 已废弃)"
- `distill-quality-gate.py:156` — `(overall_score|score)`

### 修复
在 gate 中添加 warning：当只有 `score` 没有 `overall_score` 时输出 deprecation warning。

### verify
```bash
grep "deprecat" scripts/distill-quality-gate.py
```

### commit
```
refactor(audit-p2): [P2-7] add deprecation warning for score field in gate
```

## P2-8 — 产物缺可选文件 (tables/, conversion-warnings.md)

### 问题
00-directory-structure.md 声明 _ingest/tables/ 和 _ingest/conversion-warnings.md，但产物中不存在。

### 证据
- Agent C: 目录中不存在这些文件

### 修复
在 00-directory-structure.md 标注这些为 "（可选，无表格/无警告时不生成）"。

### verify
```bash
grep "可选\|optional" plugins/prd-distill/skills/prd-distill/references/schemas/00-directory-structure.md
```

### commit
```
refactor(audit-p2): [P2-8] mark tables/ and conversion-warnings as optional
```

## P2-9 — OQ 伪问题 (OQ-PRD-003)

### 问题
report.md OQ-PRD-003 问 "券张数 1-0 疑为 typo"，但 report 正文已确认 "应为 1-9"。伪问题。

### 证据
- Agent C: report.md 正文已包含答案

### 修复
在 step-03-confirm.md 或 output-contracts.md report 模板中添加指引："OQ 必须是真正的未解决问题。如果 report 正文已给出推断结论，应列为 Assumption 而非 OQ。"

### verify
```bash
grep "Assumption\|真正的未解决" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```

### commit
```
refactor(audit-p2): [P2-9] add OQ quality guideline to report template
```

## P2-10 — evidence.yaml 字段名漂移（kind→type, summary→desc）

### 问题
03-context.md schema 定义 kind, locator, summary，但产物用 type, desc（无 locator）。

### 证据
- `03-context.md`: kind, locator, summary
- Agent C: 产物用 type, desc

### 修复
统一 03-context.md evidence schema 为产物实际格式（type, desc），或标注 v4.0 为 aspirational。

### verify
```bash
grep -A5 "kind:\|type:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md | head -10
```

### commit
```
refactor(audit-p2): [P2-10] align evidence schema field names with artifact reality
```
