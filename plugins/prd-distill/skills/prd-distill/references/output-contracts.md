# 输出契约 v2.1

这些契约由 `/build-reference` 和 `/prd-distill` 共用。字段名保持英文，方便机器稳定解析；说明文字使用中文，方便团队阅读。

## 默认输出视图

正式蒸馏默认写入：

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

用户默认只需要读 `report.md`、`plan.md`、`questions.md`。`artifacts/` 是给 AI、审计、回流和高级排查使用的证据链。

兼容旧版输出文件名：

| v2.0 | v2.1 |
|---|---|
| `distilled-report.md` | `report.md` |
| `dev-plan.md` + `qa-plan.md` | `plan.md` |
| `evidence.yaml` | `artifacts/evidence.yaml` |
| `requirement-ir.yaml` | `artifacts/requirement-ir.yaml` |
| `layer-impact.yaml` | `artifacts/layer-impact.yaml` |
| `contract-delta.yaml` | `artifacts/contract-delta.yaml` |
| `reference-update-suggestions.yaml` | `artifacts/reference-update-suggestions.yaml` |

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
tool_version: "2.1.0"
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
tool_version: "2.1.0"
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
tool_version: "2.1.0"
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
tool_version: "2.1.0"
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
tool_version: "2.1.0"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_reference/05-routing.yaml"
    summary: ""
    evidence: ["EV-001"]
    priority: "high | medium | low"
    proposed_patch: ""
```
