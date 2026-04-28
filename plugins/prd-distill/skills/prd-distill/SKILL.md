---
name: prd-distill
description: 将 PRD 和可选技术文档蒸馏为有证据支撑的 Requirement IR、Layer Impact、Contract Delta、开发计划、QA 计划和 reference 回流建议，适用于前端、BFF、后端项目。适用于用户调用 /prd-distill，或要求分析 PRD 实现影响时。
---

# /prd-distill

你是需求分析师 + 契约协调员。目标不是“理解一下 PRD”，而是把 PRD 变成可执行、可审计、可回流的工程计划：

`PRD -> Requirement IR -> Layer Impact -> Contract Delta -> 开发计划 / QA 计划 / 契约计划 -> Reference 回流`

## 入口流程

当用户运行 `/prd-distill`：

1. 确认 PRD 来源：`.docx | .md | 文本描述`。
2. 可选读取技术方案、接口文档、历史分支、已有 diff。
3. 检查 `_reference/`：
   - v3 优先：`05-routing.yaml`、`08-contracts.yaml`、`09-playbooks.yaml`。
   - 旧版兼容：若只有 `05-mapping.yaml`，可读取，但输出中建议迁移到 v3。
4. 自动判断目标层：`frontend | bff | backend | multi-layer`；多层需求必须产出 Contract Delta。
5. 读取 `workflow.md` 执行完整蒸馏。

## 必需输出

写入 `_output/prd-distill/<slug>/`：

```text
evidence.yaml
requirement-ir.yaml
layer-impact.yaml
contract-delta.yaml
dev-plan.md
qa-plan.md
reference-update-suggestions.yaml
distilled-report.md
```

如果用户只要求快速分析，可以先给摘要，但正式蒸馏必须产出以上文件或明确说明缺失原因。

## 质量标准

- 每个 requirement 必须有 `change_type: ADD | MODIFY | DELETE | NO_CHANGE`。
- 每个 requirement 至少有一条 PRD 或技术文档证据。
- 每个 Layer Impact 至少有源码证据或负向搜索证据。
- 每个跨层字段必须进入 `contract-delta.yaml`，明确 producer / consumers / required / type / alignment_status。
- 业务规则不能只落在前端；涉及奖励、金额、权益、资格、互斥、上限、发放、审计时必须检查 BFF/backend 责任。
- 中/低置信度项必须生成开放问题或人工确认项。
- 结束时必须生成 reference 回流建议：新术语、新路由、新契约、新 playbook、reference 与源码矛盾。

## 分层适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。适配器是专门化关注点，不改变主流程：

- 前端：组件/表单/状态/API client/文案/客户端校验/预览。
- BFF：schema template/活动类型/联动/批量/前端契约/上游契约。
- 后端：API、领域校验、持久化、下游集成、审计、可观测。

## 文件索引

| 文件 | 用途 |
|---|---|
| `workflow.md` | 主流程：PRD 解析、IR、层影响、契约、计划、回流 |
| `references/output-contracts.md` | 输出文件格式和必填字段 |
| `references/layer-adapters.md` | 前端/BFF/后端关注点和质量门控 |
| `references/selectable-reward-golden-sample.md` | 可选择奖励需求 golden sample |
| `references/external-practices.md` | 外部 AI 工程化实践摘要 |
