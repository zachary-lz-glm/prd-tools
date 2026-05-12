# context/ YAML Schemas

## context/graph-context.md

```markdown
# 代码搜索上下文：<需求名称>

## 1. PRD 概念到代码路由
| REQ | ai_prd_req_id | 查询词 | 命中流程/模块 | 关键文件 | 置信度 |

## 2. 函数级上下文
### GCTX-001 <symbol/process>
- requirement_id：REQ-001
- impact_id：IMP-FE-001（如已确定）
- ai_prd_req_id：REQ-001
- 查询来源：REQ-001 / 字段 / 接口 / 业务实体
- 符号：`SymbolName`
- 位置：`path/to/file.go:123`
- 类型：function | method | class | route | schema
- 角色：entrypoint | validator | transformer | persistence | external_call | consumer
- 调用方：`CallerA`, `CallerB`
- 被调用方：`CalleeA`, `CalleeB`
- 影响半径：模块/函数/route consumer 列表
- 计划用途：modify | add-nearby | verify-no-change | regression-scope
- 证据来源：graph | rg | reference | inferred
- 证据：EV-xxx
- 置信度：high | medium | low

## 3. Code Anchor 汇总
| Anchor ID | Layer | File | Symbol | Line | Type | REQ | IMP | Source | Confidence |

## 4. API / Contract Consumers
| Route/Contract | Producer | Consumers | Consumer 字段访问 | Shape 风险 |

## 5. 搜索未命中
| Query | Scope | Result | 结论 |
```

规则：

- `graph-context.md` 是 plan/report 的前置上下文，不是最终报告。
- **必须生成**：列出所有代码搜索查询和结果。
- 源码确认的符号、调用链、route consumer 可以作为 high-confidence 代码线索。
- 所有 GCTX 条目必须被 `plan.md` 或 `report.md` 消费，未消费要说明原因。
- 每个 GCTX entry 必须引用 `requirement_id`、`impact_id`（如已确定）、`ai_prd_req_id`、`layer`、`code_anchor id/file/symbol/line`、`confidence`、`evidence source`。
- 每个 code anchor 必须说明是由 rg、GitNexus/reference、源码阅读还是推断得到。
- 低置信度 anchor 必须进入 report 风险或 plan 假设。

## context/evidence.yaml

> **单一权威源原则**：evidence.yaml 是所有下游产物（requirement-ir、layer-impact、contract-delta、report、plan）引用的**唯一 evidence 账本**。`_ingest/evidence-map.yaml` 仅用于 ingestion 追溯，不得被下游直接引用。

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
items:
  - id: "EV-001"
    type: "prd | tech_doc | code | git_diff | negative_code_search | human | api_doc | reference"
    source: "/abs/path/or/url"
    desc: ""
    confidence: "high | medium | low"
```

规则：

- 搜索确认"不存在"时，使用 `negative_code_search`。
- `human` 只用于用户明确确认的事实；可记录确认人和时间。
- 原文引用保持短小，优先用摘要 + 精确定位。

## context/requirement-ir.yaml

Requirement IR 是原始 PRD 的结构化 IR。每条 requirement 必须能追溯到 `_ingest/document.md` 的 source_blocks 和 `spec/ai-friendly-prd.md` 的 REQ-ID。

```yaml
schema_version: "5.0"
tool_version: "<tool-version>"
meta:
  id: ""
  title: ""
  source_docs: []
  primary_source: "_ingest/document.md"
  ai_prd_source: "spec/ai-friendly-prd.md"
  target_layers: ["frontend", "bff", "backend"]
  overall_confidence: "high | medium | low"
requirements:
  - id: "REQ-001"
    ai_prd_req_id: "REQ-001"
    title: ""
    statement: ""
    priority: "P0 | P1 | P2"
    source: "explicit | inferred | missing_confirmation"
    intent: ""
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    business_entities: []
    rules: []
    acceptance_criteria:
      - id: "AC-001"
        statement: ""
        source: "explicit | inferred | missing_confirmation"
        testability: "testable | partial | not_testable"
    target_layers: []
    evidence:
      summary: ""
      location: ""
      source_blocks:
        - block_id: ""
          type: "text | table | media | list"
      source_block_ids: []
      evidence_ids: ["EV-001"]
    open_question_refs: []
    confirmation:
      status: "confirmed | needs_confirmation | blocked"
      reason: ""
      suggested_owner: "PM | FE | BFF | BE | QA | Unknown"
    planning:
      eligibility: "ready | assumption_only | blocked"
      rule: ""
    confidence: "high | medium | low"
    risk_flags: []
open_questions:
  - id: "Q-001"
    question: ""
    blocked_outputs: []
    owner: "product | frontend | bff | backend | qa"
```

### Source 继承规则

- `source` 必须继承 `spec/ai-friendly-prd.md` 的 source 标记。
- AI-friendly PRD 中 `explicit` 的 REQ → requirement-ir `source` 必须为 `explicit`，`planning.eligibility` 可为 `ready`。
- AI-friendly PRD 中 `inferred` 的 REQ → requirement-ir `source` 必须为 `inferred`，`planning.eligibility` 默认为 `assumption_only`（除非 report/questions 明确标注确认路径）。
- AI-friendly PRD 中 `missing_confirmation` 的 REQ → requirement-ir `source` 必须为 `missing_confirmation`，`planning.eligibility` 必须为 `blocked`，`confirmation.status` 必须为 `blocked`。

### 降级规则

- 如果 acceptance_criteria 缺失或 `testability: not_testable`，`planning.eligibility` 不能为 `ready`。
- `missing_confirmation` 必须进入 `open_question_refs`。
- `inferred` 不能直接进入确定开发 checklist，只能作为 `assumption_only`。
- report.md 和 plan.md 只能消费 `planning.eligibility` 为 `ready` 的确定实现项。`assumption_only` / `blocked` 必须进入问题、风险或前置确认。

Requirement IR 只描述业务意图和可验收规则，不写文件级实现细节。

## context/layer-impact.yaml

```yaml
schema_version: "5.0"
tool_version: "<tool-version>"
layers:
  frontend:
    impacts:
      - id: "IMP-FE-001"
        requirement_id: "REQ-001"
        ai_prd_req_id: "REQ-001"
        requirement_source: "explicit | inferred | missing_confirmation"
        planning_eligibility: "ready | assumption_only | blocked"
        change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
        surface: "ui_route | view_component | form_or_schema | client_contract | edge_api | schema_or_template | api_surface | domain_model | ..."
        target: ""
        current_state: ""
        planned_delta: ""
        code_anchors:
          - id: "ANCHOR-001"
            layer: "frontend | bff | backend | unknown"
            file: ""
            symbol: ""
            line_start: 0
            line_end: 0
            anchor_type: "route | component | api | schema | model | service | config | test | unknown"
            evidence: ""
            confidence: "high | medium | low"
            source: "graph | rg | reference | inferred"
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

强绑定规则：

- 每个 IMP 必须引用 `requirement_id`，并继承 `ai_prd_req_id`、`requirement_source`、`planning_eligibility`。
- `planning_eligibility=blocked` 的 requirement 不得生成确定性实现 IMP，只能生成风险/待确认影响。
- `ready` 的 MODIFY/DELETE IMP 必须至少有一个 `code_anchor`，除非明确写入 fallback reason。
- ADD IMP 可以没有已有 `code_anchor`，但必须写 `target` surface 和 proposed location。
- `code_anchor.source=inferred` 时，不得作为唯一 high confidence 证据。

`surface` 使用 `layer-adapters.md` 中定义的能力面名称。

## context/contract-delta.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
meta:
  primary_source: "<原始 PRD 路径>"
  ai_prd_source: "spec/ai-friendly-prd.md"
  requirement_ir_ref: "context/requirement-ir.yaml"
deltas:
  - id: "CONTRACT-EXAMPLE"
    producer: "frontend | bff | backend | external"
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    requirement_id: "REQ-001"
    layer: "frontend | bff | backend | external"
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
