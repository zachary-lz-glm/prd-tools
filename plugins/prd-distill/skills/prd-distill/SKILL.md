---
name: prd-distill
description: 将 PRD 和可选技术文档蒸馏为有证据支撑的 report、plan、questions 和 artifacts，包括 Requirement IR、Layer Impact、Contract Delta、开发/测试/契约计划和 reference 回流建议，适用于前端、BFF、后端项目。
---

# prd-distill

Claude Code 中可通过 `/prd-distill` 使用；Codex 中通过“使用 prd-distill skill ...”触发。

## 这个 skill 是做什么的

`prd-distill` 负责把单个 PRD 转成工程可执行的计划。

它不是简单总结 PRD，而是结合 `_reference/` 和源码，回答五个问题：

1. PRD 到底新增、修改、删除或不改变哪些需求点。
2. 这些需求分别影响前端、BFF、后端的哪些能力面。
3. 哪些字段、枚举、schema、endpoint、event 或外部接口需要跨团队对齐。
4. 开发应该按什么顺序做，QA 应该覆盖哪些场景。
5. 本次需求暴露了哪些新知识，需要回流到 `_reference/`。

## 什么时候使用

使用场景：

- 拿到新 PRD，需要评估影响范围和开发计划。
- 需要将 PRD 拆成前端/BFF/后端任务。
- 需要提前识别接口字段、schema、event、外部系统契约风险。
- 需要输出 QA 矩阵、回归范围和人工确认问题。
- 需要把本次需求沉淀为后续可复用的 reference 更新建议。

不要使用的场景：

- 没有 PRD、需求文本或任何可分析输入。
- 用户明确要求直接实现代码，而不是先做 PRD 分析。
- 当前没有源码，也没有 reference，且用户不接受低置信度输出。

## 输入

优先收集：

- PRD：`.docx`、`.md`、PDF 转文本或用户粘贴文本。
- 可选技术方案、API 文档、接口定义。
- 当前项目源码路径。
- 当前项目 `_reference/`。
- 可选历史分支、diff、已有实现或相关问题说明。

如果 PRD 是 `.docx`，按当前环境可用工具转换为文本。转换失败时，要求用户提供 markdown 或文本版。

## 输出

正式蒸馏输出到：

```text
_output/prd-distill/<slug>/
├── report.md
├── plan.md
├── questions.md
└── artifacts/
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

用户默认阅读前三个文件：

- `report.md`：结论报告。
- `plan.md`：开发、测试、契约对齐合并计划。
- `questions.md`：阻塞问题和 owner 确认项。

`artifacts/` 是证据链和机器可读中间结果，用于审计、复盘和知识回流。

## 输出文件边界

| 文件 | 用途 | 不应该放什么 |
|---|---|---|
| `report.md` | 给人看的结论摘要：需求、影响范围、关键风险、阻塞问题 | 不展开完整证据链，不写所有实现细节 |
| `plan.md` | 开发任务、QA 矩阵、契约对齐任务、建议顺序 | 不复制 PRD 原文，不替代代码实现 |
| `questions.md` | 阻塞问题、低置信度假设、需要 owner 确认的事项 | 不放普通备注或已确认结论 |
| `artifacts/evidence.yaml` | 证据台账：PRD、技术方案、源码、负向搜索、人工确认 | 不下结论 |
| `artifacts/requirement-ir.yaml` | 结构化需求：业务意图、规则、验收条件、变更类型 | 不写文件级实现细节 |
| `artifacts/layer-impact.yaml` | 分层影响：目标层、能力面、当前状态、计划变化、风险 | 不维护字段级跨层契约 |
| `artifacts/contract-delta.yaml` | 契约差异：producer、consumer、字段、required、type、alignment_status | 不写开发顺序或 QA case |
| `artifacts/reference-update-suggestions.yaml` | reference 回流建议：新术语、新契约、新 playbook、矛盾、golden sample | 不直接修改 `_reference/` |

## 执行步骤

1. 确认 PRD 来源和目标项目路径。
2. 读取 `_reference/`：
   - 优先读取 `project-profile.yaml`、`contracts.yaml|08-contracts.yaml`、`playbooks.yaml|09-playbooks.yaml`。
   - 兼容读取 `05-routing.yaml`、`06-glossary.yaml`、`07-business-context.yaml`。
3. 建立 `artifacts/evidence.yaml`，后续结论只引用 evidence id。
4. 将 PRD 拆成 `artifacts/requirement-ir.yaml`。
5. 按能力面生成 `artifacts/layer-impact.yaml`。
6. 多层、接口、schema、event、权益、券、奖励、支付、审计、异步等场景生成 `artifacts/contract-delta.yaml`。
7. 生成 `plan.md`，合并开发计划、QA 计划和契约对齐计划。
8. 生成 `questions.md`，集中列出阻塞问题和 owner 确认项。
9. 生成 `report.md`，给人一屏可读结论。
10. 生成 `artifacts/reference-update-suggestions.yaml`，供 build-reference 反馈回流。

## 能力面适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。

路径只是候选，最终以能力面证据为准：

- 前端：`ui_route`、`view_component`、`form_or_schema`、`state_flow`、`client_contract`、`content_i18n`、`client_validation`。
- BFF：`edge_api`、`schema_or_template`、`orchestration`、`transform_mapping`、`frontend_contract`、`upstream_contract`。
- 后端：`api_surface`、`application_service`、`domain_model`、`validation_policy`、`persistence_model`、`async_event`、`external_integration`。

## 契约规则

以下场景必须检查或生成 Contract Delta：

- 影响超过一层。
- 新增或修改 request、response、schema、event、payload、DB 字段。
- 涉及权益、券、奖励、支付、预算、审计、异步事件、外部系统。
- 前端/BFF/后端任一层只是展示、透传或假设支持，但 owner 未确认。

`alignment_status` 使用规则：

- `aligned`：producer 和 consumer 都有证据。
- `needs_confirmation`：PRD 有描述，但某层源码、文档或 owner 未确认。
- `blocked`：字段、枚举、required、时序或责任归属冲突。
- `not_applicable`：确认是单层内部变化。

## 质量规则

必须遵守：

- 先证据，后结论。
- 每个 requirement 至少有 PRD 或技术文档证据。
- 每个 layer impact 至少有源码证据或负向搜索证据。
- 业务关键规则不能只靠前端守。
- 中低置信度项必须进入 `questions.md`。
- 不确定就标 `confidence: low`，不要补脑。
- 不直接修改 `_reference/`，只生成回流建议。

## 暂停条件

遇到以下情况应暂停并说明：

- PRD 无法读取，且用户没有提供文本。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据，且无法通过源码或负向搜索补齐。

## 需要读取的参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整 PRD 蒸馏时 |
| `references/output-contracts.md` | 需要确认输出格式和字段边界时 |
| `references/layer-adapters.md` | 判断前端/BFF/后端能力面时 |
| `references/selectable-reward-golden-sample.md` | 需要复杂需求样例校准时 |
| `references/external-practices.md` | 需要解释设计依据时 |

## 完成标准

完成后不要只说“已分析”。必须说明：

- 输出目录路径。
- `report.md` 中最重要的结论。
- `questions.md` 中最重要的阻塞项。
- 是否存在 `needs_confirmation` 或 `blocked` 的契约。
- 是否生成 reference 回流建议。
