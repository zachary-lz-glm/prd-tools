# PRD Distill 三段式使用说明

本文说明后续如何使用 PRD Tools 的推荐流程：

```text
/reference
-> /prd-distill spec
-> /prd-distill report
-> confirm report
-> /prd-distill plan
```

目标是让 AI 先读懂 PRD，再结合当前项目做影响分析，最后在用户确认理解正确后生成技术计划。

## 什么时候先跑 reference

如果当前项目还没有 `_prd-tools/reference/`，建议先跑：

```text
/reference
```

`/reference` 会先进入模式选择，不会默认直接构建。

推荐选项：

| 场景 | 选择 |
|------|------|
| 首次建设项目知识库 | F→A 全量构建 |
| 只有历史 PRD/技术方案，暂不想构建 reference | F only |
| 已熟悉项目结构，想快速重建 | A only |
| 已有 reference，想检查是否过期 | B2 健康检查 |
| 已有 reference，想基于 diff 更新 | B 增量更新 |
| prd-distill 后想回流经验 | E 反馈回流 |

重要原则：

- reference 是项目长期知识库。
- reference 的 deep analysis 不建议拆成多个独立小任务。
- 可以保留阶段 gate，但 Phase 2 应作为一次完整项目建模来做，再统一去重和边界检查。

## 三段式 distill 总览

### 1. spec：把原始 PRD 变成 AI-friendly PRD

命令：

```text
/prd-distill spec <PRD 文件路径或粘贴文本>
```

这个阶段只关注 PRD 本身。

主要产物：

```text
_prd-tools/distill/<slug>/
├── _ingest/
├── spec/ai-friendly-prd.md
└── context/
    ├── evidence.yaml
    ├── prd-quality-report.yaml
    └── requirement-ir.yaml
```

你应该检查：

- PRD 是否被完整读取。
- 图片和表格是否有遗漏。
- `Open Questions` 是否合理。
- P0/P1 requirement 是否有 acceptance criteria。
- `missing_confirmation` 是否被标出来，而不是被 AI 补脑。

不应该期待：

- 不会生成最终 report。
- 不会生成 plan。
- 不会直接改代码。

### 2. report：分析当前项目会怎么受影响

命令：

```text
/prd-distill report <slug>
```

这个阶段开始读取当前项目上下文：

- `_prd-tools/reference/`
- `_prd-tools/reference/index/`
- 源码
- 技术方案/API 文档，如有

主要产物：

```text
_prd-tools/distill/<slug>/
├── report.md
└── context/
    ├── query-plan.yaml
    ├── context-pack.md
    ├── graph-context.md
    ├── layer-impact.yaml
    └── contract-delta.yaml
```

report 应回答：

- 这个 PRD 到底会影响哪些层。
- 关键代码文件和符号在哪里。
- 哪些字段、枚举、schema、endpoint、event 会变。
- 哪些契约需要 owner 确认。
- 哪些需求有歧义、冲突或阻塞。
- 哪些结论是高置信度，哪些只是推断。

report 生成后，流程必须暂停，等待用户确认。

### 3. confirm：确认 report 是否符合预期

如果 report 看起来正确，回复：

```text
approved
```

系统应写入：

```text
_prd-tools/distill/<slug>/context/report-confirmation.yaml
```

内容类似：

```yaml
schema_version: "1.0"
status: "approved"
confirmed_by: "user"
approved_sections:
  - "requirements"
  - "layer_impact"
  - "contract_delta"
  - "open_questions"
revision_requests: []
blocked_reason: ""
```

如果 report 有问题，回复：

```text
needs_revision: 影响范围漏了 BFF contract，请补充 xxx 接口
```

或：

```text
blocked: PRD 缺少券批次和预算规则，先暂停
```

规则：

- `approved` 才能进入 plan。
- `needs_revision` 必须回到 spec/report 上游修正。
- `blocked` 不生成 plan。

### 4. plan：生成最终技术方案

命令：

```text
/prd-distill plan <slug>
```

前置条件：

```text
context/report-confirmation.yaml status: approved
```

主要产物：

```text
_prd-tools/distill/<slug>/
├── plan.md
├── portal.html
└── context/
    ├── readiness-report.yaml
    ├── final-quality-gate.yaml
    └── reference-update-suggestions.yaml
```

plan 应回答：

- 按什么顺序改。
- 每个任务对应哪个 REQ-ID / IMP-ID / AC-ID。
- 目标文件和函数是什么。
- 验证命令是什么。
- 哪些项只能 handoff 或 owner 确认。
- 回滚和 QA 怎么做。

plan 不应该：

- 重新解释原始 PRD。
- 绕过 report 重新编造影响范围。
- 把 `missing_confirmation` 写成确定实现任务。
- 直接进入 code。

## 推荐日常流程

首次项目：

```text
/reference
# 选择 F→A 全量构建

/prd-distill spec docs/my-prd.docx
/prd-distill report <slug>
# 阅读 report.md，确认影响范围
approved
/prd-distill plan <slug>
```

已有 reference 的项目：

```text
/reference
# 选择 B2 健康检查，确认 reference 可用

/prd-distill spec docs/my-prd.docx
/prd-distill report <slug>
approved
/prd-distill plan <slug>
```

report 不符合预期：

```text
/prd-distill report <slug>
needs_revision: report 漏掉了管理后台页面和 BFF 字段映射
# 修正 report 上游 context 后重新生成 report
approved
/prd-distill plan <slug>
```

PRD 信息不足：

```text
/prd-distill spec docs/my-prd.docx
/prd-distill report <slug>
blocked: 缺少接口 owner 和字段 required 规则
```

## 判断每阶段是否合格

### spec 合格

- `spec/ai-friendly-prd.md` 有 13 个章节。
- P0/P1 requirement 有 acceptance criteria。
- 不确定项进入 Open Questions。
- `context/requirement-ir.yaml` 能追溯到 AI-friendly PRD 的 REQ-ID。

### report 合格

- 影响层和能力面清楚。
- 关键文件/符号有 evidence。
- 契约变化有 producer / consumer / alignment_status。
- 低置信度项和阻塞项没有被隐藏。
- 用户能判断“AI 是否理解正确”。

### plan 合格

- `report-confirmation.yaml` 是 approved。
- 每个实现任务都有 REQ-ID / IMP-ID / AC-ID。
- 每个 MODIFY/DELETE 有 code anchor 或 fallback reason。
- 每个任务有验证方式。
- 不包含未经确认的确定任务。

## 常见问题

### 为什么不直接 `/prd-distill` 一次跑完？

因为 report 是 AI 对需求和项目影响的理解。如果 report 错了，plan 大概率也错。三段式把错误拦在 plan 之前。

### spec 阶段为什么不读源码？

spec 的职责是把 PRD 规范化。过早读源码会让 AI 把实现猜测混进需求定义，导致后续 trace 不清晰。

### report 和 plan 有什么区别？

report 回答“当前项目会受什么影响，风险在哪里”。

plan 回答“在已确认影响分析基础上，怎么改、怎么测、怎么交付”。

### reference 要不要也拆成多个命令？

不建议拆太碎。reference 是长期知识库构建，需要整体项目建模。保留 mode selection 和大阶段 gate 即可，deep analysis 应尽量作为 consolidated pass。

### 什么时候可以进入 code？

当前不建议把 code 放进默认流程。先让 `plan.md`、`readiness-report.yaml`、后续 `agent-pack/` 稳定，再交给 coding agent 执行。
