# 输出契约 v2.2

这些契约由 `/build-reference` 和 `/prd-distill` 共用。字段名保持英文，方便机器稳定解析；说明文字使用中文，方便团队阅读。

## 默认输出视图

正式蒸馏默认写入：

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

用户默认只需要读 `report.md`、`plan.md`、`questions.md`。`prd-ingest/` 是原始文档读取层，`artifacts/` 是给 AI、审计、回流和高级排查使用的证据链。

兼容旧版输出文件名：

| v2.0 | v2.1+ |
|---|---|
| `distilled-report.md` | `report.md` |
| `dev-plan.md` + `qa-plan.md` | `plan.md` |
| `evidence.yaml` | `artifacts/evidence.yaml` |
| `requirement-ir.yaml` | `artifacts/requirement-ir.yaml` |
| `layer-impact.yaml` | `artifacts/layer-impact.yaml` |
| `contract-delta.yaml` | `artifacts/contract-delta.yaml` |
| `reference-update-suggestions.yaml` | `artifacts/reference-update-suggestions.yaml` |

## prd-ingest/

`prd-ingest/` 解决“PRD 到底被 AI 读成了什么”的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。

| 文件 | 用途 | 边界 |
|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、大小、hash、生成时间、读取方式 | 不写需求摘要或实现判断 |
| `document.md` | 转换后的可读 markdown，作为 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `document-structure.json` | 段落、标题、表格、图片等结构块，含 block id 和 locator | 不写业务语义结论 |
| `evidence-map.yaml` | PRD 块级证据，供 `artifacts/evidence.yaml` 映射 | 不放源码、diff、reference 证据 |
| `media/` | 抽出的图片、截图、流程图原文件 | 不修改图片内容 |
| `media-analysis.yaml` | 图片分析状态；默认 `needs_vision_or_human_review` | 没有 vision/OCR/人工确认时不推断图片含义 |
| `tables/` | 单独抽出的表格 markdown | 不修复原表格，只保留转换结果 |
| `extraction-quality.yaml` | 读取质量门禁：`pass | warn | block`、统计、风险 | 不写开发计划 |
| `conversion-warnings.md` | 给人看的转换风险 | 不替代 `questions.md` |

`extraction-quality.yaml` 示例：

```yaml
schema_version: "1.0"
status: "pass | warn | block"
stats:
  paragraphs: 0
  tables: 0
  media: 0
quality_gates: []
warnings: []
rules:
  - "Do not infer requirements from images unless media-analysis has human or vision evidence."
```

质量规则：

- `block`：暂停蒸馏，要求用户提供 markdown/text，或接入 OCR/layout/vision。
- `warn`：允许继续，但必须在 `report.md` 或 `questions.md` 中暴露风险。
- 图片、截图、流程图里的信息，没有 vision/OCR/人工确认时，只能作为待确认问题，不能作为高置信度结论。

## report.md

给人看的结论，优先一屏可读：

1. 需求一句话摘要。
2. 影响范围：命中的层、能力面、关键文件/模块。
3. 关键结论：新增/修改/不改什么。
4. 契约风险：只列阻塞或需确认的契约。
5. Top open questions。
6. 输出索引：指向 `plan.md` 和 `artifacts/`。

## plan.md

合并开发、QA、契约对齐计划，避免用户在多个文件间跳转：

- 范围和假设。
- 建议实现顺序。
- 分层任务：前端 / BFF / 后端，只展示命中的层。
- 契约对齐任务。
- QA 矩阵和回归重点。
- 风险和回滚/观测建议。

每个任务引用 `REQ-*`、`IMP-*` 或 `CONTRACT-*`。

## questions.md

只放阻塞问题、需 owner 确认的问题和低置信度假设：

- 问题。
- 影响的输出或开发任务。
- 建议 owner。
- 需要的证据。
- 当前建议默认策略。

## evidence.yaml

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
items:
  - id: "EV-001"
    kind: "prd | tech_doc | code | git_diff | negative_code_search | human | api_doc | reference"
    source: "/abs/path/or/url"
    locator: "page/section/line/symbol/query"
    summary: ""
    confidence: "high | medium | low"
```

规则：

- 搜索确认“不存在”时，使用 `negative_code_search`。
- `human` 只用于用户明确确认的事实；可记录确认人和时间。
- 原文引用保持短小，优先用摘要 + 精确定位。

## requirement-ir.yaml

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
meta:
  id: ""
  title: ""
  source_docs: []
  target_layers: ["frontend", "bff", "backend"]
  overall_confidence: "high | medium | low"
requirements:
  - id: "REQ-001"
    title: ""
    intent: ""
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    business_entities: []
    rules: []
    acceptance_criteria: []
    target_layers: []
    evidence: ["EV-001"]
    confidence: "high | medium | low"
    risk_flags: []
open_questions:
  - id: "Q-001"
    question: ""
    blocked_outputs: []
    owner: "product | frontend | bff | backend | qa"
```

Requirement IR 只描述业务意图和可验收规则，不写文件级实现细节。

## layer-impact.yaml

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
layers:
  frontend:
    impacts:
      - id: "IMP-FE-001"
        requirement_id: "REQ-001"
        change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
        surface: "ui_route | view_component | form_or_schema | client_contract | edge_api | schema_or_template | api_surface | domain_model | ..."
        target: ""
        current_state: ""
        planned_delta: ""
        dependencies: []
        risks: []
        evidence: ["EV-001"]
        confidence: "high | medium | low"
  bff:
    impacts: []
  backend:
    impacts: []
quality_gates: []
```

`surface` 使用 `layer-adapters.md` 中定义的能力面名称。

## contract-delta.yaml

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
contracts:
  - id: "CONTRACT-EXAMPLE"
    name: ""
    producer: "frontend | bff | backend | external"
    consumers: ["frontend", "bff", "backend", "external"]
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    contract_surface: "endpoint | schema | event | payload | db_table | external_api"
    request_fields:
      - name: ""
        change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
        required: false
        type: ""
        source: "prd | tech_doc | code | inferred"
        notes: ""
    response_fields: []
    alignment_status: "aligned | needs_confirmation | blocked | not_applicable"
    checked_by: ["frontend", "bff"]
    evidence: ["EV-001"]
alignment_summary:
  status: "aligned | needs_confirmation | blocked | not_applicable"
  blockers: []
  next_actions: []
```

以下场景必须生成 Contract Delta：多层协作、API/schema 变化、下游系统集成、权益/券/支付/奖励链路、审计 payload、异步事件。

## reference-update-suggestions.yaml

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_reference/05-routing.yaml"
    summary: ""
    evidence: ["EV-001"]
    priority: "high | medium | low"
    proposed_patch: ""
```
