# context/ YAML Schemas

## context/graph-context.md

```markdown
# 代码搜索上下文：<需求名称>

## 1. PRD 概念到代码路由
| REQ | 查询词 | 命中流程/模块 | 关键文件 | 置信度 |

## 2. 函数级上下文
### GCTX-001 <symbol/process>
- 查询来源：REQ-001 / 字段 / 接口 / 业务实体
- 符号：`SymbolName`
- 位置：`path/to/file.go:123`
- 类型：function | method | class | route | schema
- 角色：entrypoint | validator | transformer | persistence | external_call | consumer
- 调用方：`CallerA`, `CallerB`
- 被调用方：`CalleeA`, `CalleeB`
- 影响半径：模块/函数/route consumer 列表
- 计划用途：modify | add-nearby | verify-no-change | regression-scope
- 证据：EV-xxx

## 3. API / Contract Consumers
| Route/Contract | Producer | Consumers | Consumer 字段访问 | Shape 风险 |

## 4. 搜索未命中
| Query | Scope | Result | 结论 |
```

规则：

- `graph-context.md` 是 plan/report 的前置上下文，不是最终报告。
- **必须生成**：列出所有代码搜索查询和结果。
- 源码确认的符号、调用链、route consumer 可以作为 high-confidence 代码线索。
- 所有 GCTX 条目必须被 `plan.md` 或 `report.md` 消费，未消费要说明原因。

## context/evidence.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
items:
  - id: "EV-001"
    kind: "prd | tech_doc | code | git_diff | negative_code_search | human | api_doc | reference"
    source: "/abs/path/or/url"
    locator: "page/section/line/symbol/query"
    summary: ""
    confidence: "high | medium | low"
```

规则：

- 搜索确认"不存在"时，使用 `negative_code_search`。
- `human` 只用于用户明确确认的事实；可记录确认人和时间。
- 原文引用保持短小，优先用摘要 + 精确定位。

## context/requirement-ir.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
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

## context/layer-impact.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
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

## context/contract-delta.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
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

## context/reference-update-suggestions.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_prd-tools/reference/04-routing-playbooks.yaml"
    summary: ""
    current_repo_scope:
      authority: "single_repo"
      action: "apply_to_current_repo | record_as_signal | needs_owner_confirmation"
    owner_to_confirm: []
    team_reference_candidate: false
    team_scope:
      type: "contract | domain_term | playbook | decision | routing_signal | golden_sample"
      related_repos: []
      aggregation_status: "candidate | confirmed | rejected | not_applicable"
    evidence: ["EV-001"]
    priority: "high | medium | low"
    confidence: "high | medium | low"
    proposed_patch: ""
```

生成规则：

- 当前仓可由源码、技术文档或 owner 确认的事实，`current_repo_scope.action` 才能是 `apply_to_current_repo`。
- 跨仓契约、上下游 owner、团队级术语只作为 `record_as_signal` 或 `needs_owner_confirmation`，并填写 `owner_to_confirm`。
- `team_reference_candidate: true` 只表示未来团队知识库候选，不代表 `/prd-distill` 或 `/reference` 会自动同步到团队级知识库。
