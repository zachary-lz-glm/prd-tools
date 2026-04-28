# prd-distill 工作流

## 目标

把 PRD 蒸馏为工程可执行的中间表示和计划：

```text
PRD + tech docs + reference + code
  -> evidence.yaml
  -> requirement-ir.yaml
  -> layer-impact.yaml
  -> contract-delta.yaml
  -> dev-plan.md
  -> qa-plan.md
  -> reference-update-suggestions.yaml
  -> distilled-report.md
```

主流程对前端、BFF、后端通用；层差异只通过 `references/layer-adapters.md` 的适配器生效。

## 步骤 0：准备输入

读取或收集：

- PRD：`.docx | .md | pasted text`。
- 技术方案 / API 文档：可选，但多层或后端相关需求强烈建议读取。
- `_reference/`：优先 v3；若只有旧版 `05-mapping.yaml`，兼容读取并在回流建议里提示迁移。
- 目标代码库：用于代码锚定。

如果 PRD 是 docx，按可用工具转换为文本；转换失败时提示用户提供 md/text。

创建输出目录：

```text
_output/prd-distill/<slug>/
```

## 步骤 1：证据台账

先建立 `evidence.yaml`，后续所有判断只引用 evidence id。

证据类型：

- `prd`
- `tech_doc`
- `code`
- `git_diff`
- `negative_code_search`
- `human`
- `api_doc`
- `reference`

格式见 `references/output-contracts.md`。

规则：

- PRD 原文证据要能定位章节、页码、标题或段落。
- 源码证据要能定位文件和符号；尽量带行号。
- 搜不到也是证据，用 `negative_code_search`，记录 query 和搜索范围。

## 步骤 2：Requirement IR

将 PRD 转成 `requirement-ir.yaml`。

每个 requirement 必须包含：

- `id`
- `title`
- `intent`
- `change_type`
- `business_entities`
- `rules`
- `acceptance_criteria`
- `target_layers`
- `evidence`
- `confidence`

原则：

- 业务规则、字段、枚举、限制、互斥、数量上限、流程差异都要拆成可追踪 requirement。
- 不要把实现方案直接混进 IR；实现影响放到 layer impact。
- 不确定项进入 `open_questions`。

## 步骤 3：Layer Impact

读取目标层适配器：

- frontend / BFF / backend 单层：生成对应 impacts。
- multi-layer：每层各生成 impacts，并合并进一个 `layer-impact.yaml`。

每个 impact 必须说明：

- requirement_id
- layer
- concern
- target 文件/模块/接口/组件
- current_state
- planned_delta
- risks
- evidence
- confidence

ADD/MODIFY/DELETE/NO_CHANGE 必须由源码或负向搜索支撑。

## 步骤 4：Contract Delta

多层、接口、schema、事件、外部权益/券/支付/审计等需求必须生成 `contract-delta.yaml`。

每个 contract 记录：

- producer
- consumers
- contract_surface
- request_fields
- response_fields
- alignment_status
- checked_by
- evidence

判断：

- `aligned`：生产者和消费者都有证据。
- `needs_confirmation`：PRD/技术方案有描述，但某层源码或文档未确认。
- `blocked`：字段、枚举、required、时序或责任归属冲突。
- `not_applicable`：确认为单层内部变化。

## 步骤 5：计划

生成 `dev-plan.md`：

- 按层分组。
- 每个任务引用 requirement_id、impact_id、contract_id。
- 标注建议修改文件、实现顺序、风险、人工确认项。
- 不直接写代码，除非用户明确要求进入实现。

生成 `qa-plan.md`：

- PRD 验收场景。
- 层内测试。
- 契约测试。
- 回归场景。
- 边界/互斥/权限/批量/预览/审计等矩阵。

QA case 必须追溯到 `requirement_id` 或 `contract_id`。

## 步骤 6：Reference 回流

生成 `reference-update-suggestions.yaml`：

```yaml
version: "3.0"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_reference/05-routing.yaml"
    summary: ""
    evidence: ["EV-001"]
    priority: "high | medium | low"
    proposed_patch: ""
```

触发条件：

- PRD 出现 reference 没有的术语、枚举、路由、契约或场景。
- reference 说已实现但源码不存在，或源码存在但 reference 缺失。
- 本次需求能作为高价值 golden sample。

## 步骤 7：蒸馏报告

`distilled-report.md` 是给人看的汇总：

1. 需求摘要
2. Requirement IR 汇总
3. 分层影响
4. 契约差异和阻塞项
5. 开发计划
6. QA 计划
7. 需人工确认问题
8. Reference 回流建议

报告里不要隐藏低置信度项；低置信度是价值，不是瑕疵。

## 暂停条件

遇到以下情况暂停并说明：

- PRD 无法读取且用户没有提供文本。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据，且无法通过源码或负向搜索补齐。

## 执行规则

1. 先证据，后结论。
2. IR 描述业务意图，impact 描述代码影响，contract 描述跨层接口。
3. 业务规则不能只靠前端守。
4. 多层需求必须给契约计划。
5. 每个输出都要能回溯 evidence。
6. 完成后简要告知输出路径和最重要的阻塞/风险。
