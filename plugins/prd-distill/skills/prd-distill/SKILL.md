---
name: prd-distill
description: 将 PRD 和可选技术文档蒸馏为有证据支撑的 report、plan、questions 和 artifacts，包括 Requirement IR、Layer Impact、Contract Delta、开发/测试/契约计划和 reference 回流建议，适用于前端、BFF、后端项目。
---

# prd-distill

Claude Code 中可通过 `/prd-distill` 使用；Codex 中通过“使用 prd-distill skill ...”触发。

你是需求分析师 + 契约协调员。目标不是“理解一下 PRD”，而是把 PRD 变成可执行、可审计、可回流的工程计划：

`PRD -> report -> plan -> questions -> artifacts(IR/Impact/Contract) -> Reference 回流`

## 入口流程

当用户运行 `/prd-distill`，或在 Codex/Agent 中要求使用 prd-distill skill：

1. 确认 PRD 来源：`.docx | .md | 文本描述`。
2. 可选读取技术方案、接口文档、历史分支、已有 diff。
3. 检查 `_reference/`：
   - v3.1 优先：`project-profile.yaml`、`contracts.yaml|08-contracts.yaml`、`playbooks.yaml|09-playbooks.yaml`。
   - v3 兼容：`05-routing.yaml`、`08-contracts.yaml`、`09-playbooks.yaml`。
   - 旧版兼容：若只有 `05-mapping.yaml`，可读取，但输出中建议迁移到 v3。
4. 自动判断目标层和能力面：`frontend | bff | backend | multi-layer`；多层或契约变化必须产出 Contract Delta。
5. 读取 `workflow.md` 执行完整蒸馏。

## 必需输出

写入 `_output/prd-distill/<slug>/`：

```text
report.md
plan.md
questions.md
artifacts/
├── evidence.yaml
├── requirement-ir.yaml
├── layer-impact.yaml
├── contract-delta.yaml
└── reference-update-suggestions.yaml
```

如果用户只要求快速分析，可以先给摘要，但正式蒸馏必须产出以上文件或明确说明缺失原因。

## 质量标准

- 每个 requirement 必须有 `change_type: ADD | MODIFY | DELETE | NO_CHANGE`。
- 每个 requirement 至少有一条 PRD 或技术文档证据。
- 每个 Layer Impact 至少有源码证据或负向搜索证据。
- 每个跨层字段必须进入 `artifacts/contract-delta.yaml`，明确 producer / consumers / required / type / alignment_status。
- 业务规则不能只落在前端；涉及奖励、金额、权益、资格、互斥、上限、发放、审计时必须检查 BFF/backend 责任。
- 中/低置信度项必须生成开放问题或人工确认项。
- 结束时必须生成轻量 `report.md`、合并计划 `plan.md`、确认项 `questions.md` 和 reference 回流建议。

## 能力面适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。路径只是候选，最终以能力面证据为准：

- 前端：ui_route、view_component、form_or_schema、state_flow、client_contract 等。
- BFF：edge_api、schema_or_template、orchestration、transform_mapping、frontend/upstream_contract 等。
- 后端：api_surface、application_service、domain_model、validation_policy、persistence_model、async_event 等。

## 文件索引

| 文件 | 用途 |
|---|---|
| `workflow.md` | 主流程：PRD 解析、人类报告、计划、确认项、artifacts、回流 |
| `references/output-contracts.md` | report、plan、questions、artifacts 输出格式 |
| `references/layer-adapters.md` | 前端/BFF/后端能力面和质量门控 |
| `references/selectable-reward-golden-sample.md` | 可选择奖励需求 golden sample |
| `references/external-practices.md` | 外部 AI 工程化实践摘要 |
