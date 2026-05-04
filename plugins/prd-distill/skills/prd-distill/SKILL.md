---
name: prd-distill
description: 将 PRD 和可选技术文档先做稳定读取与质量检查，再蒸馏为有证据支撑的 report、plan、questions 和 artifacts，包括 Requirement IR、Layer Impact、Contract Delta、开发/测试/契约计划和 reference 回流建议，适用于前端、BFF、后端项目。
---

# prd-distill

Claude Code 中可通过 `/prd-distill` 使用。

## 这个 skill 是做什么的

`prd-distill` 负责把单个 PRD 转成工程可执行的计划。它先做 PRD ingestion，使用 MarkItDown 把原始 `.docx/.md/.txt/.pdf/.pptx/.xlsx/.html` 转成可追溯的结构化输入，再结合 `_reference/` 和源码完成分析。

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

- PRD：`.docx`、`.md`、`.txt`、`.pdf`、`.pptx`、`.xlsx`、`.html` 或用户粘贴文本。
- 可选技术方案、API 文档、接口定义。
- 当前项目源码路径。
- 当前项目 `_reference/`。
- 可选历史分支、diff、已有实现或相关问题说明。

PRD 读取规则：

- 如果输入是文件，优先运行 `scripts/ingest_prd.py` 生成 `_output/prd-distill/<slug>/prd-ingest/`。
- 如果用户只粘贴文本，手工创建同等语义的 ingestion 证据：来源、段落定位、质量说明。
- 使用 MarkItDown (microsoft/markitdown) 作为文件转换后端，支持 docx/pdf/pptx/xlsx/html 等格式。
- 如果设置了 `OPENAI_API_KEY` 环境变量，自动启用 LLM Vision 分析 PRD 中的图片内容（流程图、截图、设计稿）。
- `.md/.txt` 保留原文行号和 markdown 图片引用。
- 图片、截图、流程图、复杂表格如果没有 LLM Vision 或人工确认，不能作为高置信度需求依据。

## 输出

正式蒸馏输出到：

```text
_output/prd-distill/<slug>/
├── prd-ingest/
│   ├── source-manifest.yaml
│   ├── document.md
│   ├── document-structure.json
│   ├── evidence-map.yaml
│   ├── media/
│   ├── media-analysis.yaml
│   ├── tables/
│   ├── extraction-quality.yaml
│   └── conversion-warnings.md
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

`prd-ingest/` 是 PRD 原始读取结果，`artifacts/` 是证据链和机器可读中间结果，用于审计、复盘和知识回流。

## 输出文件边界

| 文件 | 用途 | 不应该放什么 |
|---|---|---|
| `prd-ingest/source-manifest.yaml` | 原始 PRD 文件的路径、格式、大小、hash、读取方式 | 不写需求结论 |
| `prd-ingest/document.md` | 从 PRD 转出的可读 markdown，是后续拆需求的主输入 | 不手工补充 PRD 没有的信息 |
| `prd-ingest/document-structure.json` | 段落、表格、图片等结构块和定位 | 不写业务判断 |
| `prd-ingest/evidence-map.yaml` | PRD 块级证据 id，供 `artifacts/evidence.yaml` 引用或映射 | 不放源码证据 |
| `prd-ingest/media/` | 从 PRD 抽出的图片、截图、流程图原文件 | 不改图、不重命名成业务结论 |
| `prd-ingest/media-analysis.yaml` | 图片语义分析状态；默认标记待 vision 或人工确认 | 不在没有证据时推断图片含义 |
| `prd-ingest/tables/` | 抽出的表格 markdown，便于单独核对 | 不修正原表格内容 |
| `prd-ingest/extraction-quality.yaml` | 读取质量门禁：是否缺文本、是否有图片未分析、是否有复杂表格 | 不写开发计划 |
| `prd-ingest/conversion-warnings.md` | 给人看的转换风险列表 | 不替代 `questions.md` |
| `report.md` | 渐进式披露：需求摘要→变更明细表→字段清单→校验规则→开发Checklist→契约风险→Questions | 不展开完整 YAML 证据链（见 artifacts） |
| `plan.md` | 可执行的开发操作手册：精确到文件路径+行号，checklist 格式，QA 矩阵 | 不复制 PRD 原文，不替代代码实现 |
| `questions.md` | 阻塞问题、低置信度假设、需要 owner 确认的事项 | 不放普通备注或已确认结论 |
| `artifacts/evidence.yaml` | 证据台账：PRD、技术方案、源码、负向搜索、人工确认 | 不下结论 |
| `artifacts/requirement-ir.yaml` | 结构化需求：业务意图、规则、验收条件、变更类型 | 不写文件级实现细节 |
| `artifacts/layer-impact.yaml` | 分层影响：目标层、能力面、当前状态、计划变化、风险 | 不维护字段级跨层契约 |
| `artifacts/contract-delta.yaml` | 契约差异：producer、consumer、字段、required、type、alignment_status | 不写开发顺序或 QA case |
| `artifacts/reference-update-suggestions.yaml` | reference 回流建议：新术语、新契约、新 playbook、矛盾、golden sample | 不直接修改 `_reference/` |

## 执行步骤

1. 确认 PRD 来源和目标项目路径。
2. 对 PRD 执行 ingestion：
   - 文件输入优先运行 `python3 <skill>/scripts/ingest_prd.py <prd> --out _output/prd-distill/<slug>/prd-ingest`。
   - 读取 `prd-ingest/extraction-quality.yaml`；`status: block` 时暂停。
   - 有图片、截图、流程图或复杂表格时，检查 `media-analysis.yaml` 和 `conversion-warnings.md`，未确认内容必须进入 `questions.md`。
3. 读取 `_reference/`：
   - 优先读取 v4 文件：`project-profile.yaml`、`03-contracts.yaml`、`04-routing-playbooks.yaml`。
   - 兼容读取 v3.1 文件：`contracts.yaml|08-contracts.yaml`、`playbooks.yaml|09-playbooks.yaml`、`05-routing.yaml`、`06-glossary.yaml`、`07-business-context.yaml`。
4. 建立 `artifacts/evidence.yaml`，先映射 ingestion 证据，再补充技术方案、源码、负向搜索、reference 证据。
5. 将 `prd-ingest/document.md` 拆成 `artifacts/requirement-ir.yaml`。
6. 按能力面生成 `artifacts/layer-impact.yaml`。
7. 多层、接口、schema、event、权益、券、奖励、支付、审计、异步等场景生成 `artifacts/contract-delta.yaml`。
8. 生成 `plan.md`，合并开发计划、QA 计划和契约对齐计划。
9. 生成 `questions.md`，集中列出阻塞问题和 owner 确认项。
10. 生成 `report.md`，给人一屏可读结论。
11. 生成 `artifacts/reference-update-suggestions.yaml`，供 build-reference 反馈回流。

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
- 每个 requirement 的 PRD 证据优先来自 `prd-ingest/evidence-map.yaml` 或更强的人工/vision/OCR 证据。
- 每个 layer impact 至少有源码证据或负向搜索证据。
- `prd-ingest/extraction-quality.yaml` 如果是 `warn`，必须在 `report.md` 或 `questions.md` 中暴露影响。
- 业务关键规则不能只靠前端守。
- 中低置信度项必须进入 `questions.md`。
- 不确定就标 `confidence: low`，不要补脑。
- 不直接修改 `_reference/`，只生成回流建议。

## 图谱增强（可选）

当 GitNexus 或 Graphify 可用时，prd-distill 做轻量级补充查询，**不做图谱全量扫描**。图谱数据的主要消费者是 build-reference。

| 场景 | 图谱工具 | 查询类型 |
|------|---------|---------|
| 代码影响范围评估 | GitNexus | `mcp__gitnexus__impact` 获取受影响符号和爆炸半径，写入 impact 条目的 `affected_symbols` |
| 业务规则约束检查 | Graphify | `/graphify path` 追踪业务关联，`/graphify explain` 获取设计原理，写入 impact 条目的 `business_constraints` |
| 契约 consumer 发现 | GitNexus | `mcp__gitnexus__route_map` / `api_impact` 补充 consumer 信息 |

图谱不可用时完全回退到源码 Read + rg/glob，不影响 prd-distill 核心流程。

如果 `_output/graph/graph-sync-report.yaml` 存在且 provider available，优先读取图谱证据作为辅助输入。图谱结论仍然需要 EV-xxx 审计证据支撑。

## 暂停条件

遇到以下情况应暂停并说明：

- PRD 无法读取，且用户没有提供文本。
- PRD ingestion 的 `extraction-quality.yaml` 为 `status: block`。
- PRD 的关键要求只存在于图片/截图/流程图中，但没有 vision/OCR 或人工确认。
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
