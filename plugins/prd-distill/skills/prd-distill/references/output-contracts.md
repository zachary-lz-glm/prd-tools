# 输出契约 v2.4

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

`prd-ingest/` 解决"PRD 到底被 AI 读成了什么"的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。

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

渐进式披露（Progressive Disclosure）：同一文件内从结论到细节逐层展开，不需要跳到其他文件就能获取核心信息。

### 结构模板

```markdown
# 需求分析报告：<需求名称>

## 1. 需求摘要（30秒决策）
一句话摘要 + 变更类型统计（ADD/MODIFY/DELETE/NO_CHANGE 各几项）。

## 2. 影响范围
命中的层、能力面、关键文件/模块（表格形式）。

## 3. 关键结论
新增/修改/不改什么，每个结论带 REQ-ID 和代码路径引用。

## 4. 变更明细表（核心可操作内容）
| ID | 变更描述 | 类型 | 目标文件 | 验证来源 |
列出所有 IMP-* 项，精确到文件路径，标注 code_verified / reference_only。

## 5. 字段清单（按功能模块分组）
| 字段 | 类型 | 必填 | 来源 | 契约ID |
从 requirement-ir 和 contract-delta 中提取，按业务模块分组。

## 6. 校验规则
| ID | 规则描述 | 错误文案/提示 | 目标文件 |
从 requirement-ir.rules 中提取可验证的校验规则。

## 7. 开发 Checklist（可直接执行）
- [ ] 1. <具体操作>（<目标文件>）— REQ-001, IMP-001
- [ ] 2. <具体操作>（<目标文件>）— REQ-002, IMP-002
...
按建议实现顺序排列，每项标注关联的 REQ/IMP/CONTRACT。

## 8. 契约风险
只列 alignment_status 为 needs_confirmation 或 blocked 的契约。

## 9. Top Open Questions
最多5个最关键的阻塞问题，带 Q-ID。

---
*详细证据链见 artifacts/*，按需展开*
```

### 写作规则

- **自然语言为主**，避免纯 YAML/JSON 格式；用 Markdown 表格提高可扫描性。
- **具体到文件路径**：每个变更项都带目标文件路径（如 `model/business_object/xxx/`）。
- **关联 ID**：每个条目引用 REQ-*/IMP-*/CONTRACT-*，方便跳到 artifacts 查证。
- **不隐藏低置信度**：低置信度项用 ⚠ 标注，进入 questions.md。
- **Checklist 可直接执行**：开发人员拿到就能按步骤干活。

### 职责边界

- **report.md 是决策文档，不是所有细节的全集**。
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责。
- 不要复制 PRD 原文，只引用 REQ-ID。
- 建议总长度控制在 200-400 行（Markdown 源码），超过时优先精简变更明细表和字段清单，不要精简摘要、影响范围和契约风险。

## plan.md

可执行的开发操作手册，精确到文件路径和行号。

### 结构模板

```markdown
# 开发计划：<需求名称>

## 范围和假设
- 本计划覆盖的 REQ 范围
- 前置假设和依赖

## 建议实现顺序
Phase 1 → Phase 2 → Phase 3，每阶段标注依赖和前置条件。

## 分层任务（只展示命中的层）

### 后端（示例）
#### Phase 1: 基础设施
- [ ] **1.1** 添加 CampaignType 常量
  - 文件：`common/consts/campaign.go:27`
  - 操作：在现有枚举末尾添加新常量
  - 关联：REQ-001, IMP-BE-001
  - 验证：`grep -n "TypeNewCampaign" common/consts/campaign.go`

- [ ] **1.2** 创建 Business 实现
  - 文件：`model/business_object/new_campaign/`（新建目录）
  - 操作：创建完整 Business 结构体，实现 ~31 个接口方法
  - 参考实现：`model/business_object/gas_coupon_campaign/`
  - 关联：REQ-001, IMP-BE-002

#### Phase 2: 注册与路由
...

### 前端 / BFF（如有命中）
...

## 契约对齐任务
| 契约 | 状态 | 需要确认方 | 确认内容 |
只列 needs_confirmation 和 blocked。

## QA 矩阵
| 场景 | 关键检查点 | 关联 REQ | 优先级 |
覆盖正常流 + 边界情况 + 异常流。

## 风险和回滚
- 回滚方案（如"关闭 Apollo 开关即可隐藏新类型"）
- 观测建议
- 已知坑点

## 回归重点
哪些已有功能可能受影响，需要回归验证。
```

### 写作规则

- **精确到文件和行号**：每个任务给出目标文件路径，尽量带行号。
- **给出验证命令**：每个关键步骤附带 grep/go test 等验证命令。
- **给出参考实现**：类似功能的已有代码路径，开发人员可以参照。
- **Checklist 格式**：用 `- [ ]` 格式，开发人员可以直接勾选。
- **按 Phase 分组**：体现依赖关系，Phase 间标注前置条件。
- **不编造行号或命令**：如果不确定行号，写"约在 XX 附近"或省略行号，不要编造。验证命令只给出已确认可用的。

### 职责边界

- **plan.md 是执行文档，不是二次报告**。
- 不要重复 report.md 的分析结论，只写"做什么、怎么做"。
- 不要复制 PRD 原文。
- 建议总长度控制在 150-350 行（Markdown 源码），超过时优先精简参考实现描述，不要精简任务清单和 QA 矩阵。

## questions.md

只放阻塞问题、需 owner 确认的问题和低置信度假设：

- 问题。
- 影响的输出或开发任务。
- 建议 owner。
- 需要的证据。
- 当前建议默认策略。

### 职责边界

- **questions.md 必须保持精简，不能变成垃圾桶**。
- 每个问题必须可操作：有明确 owner、影响范围、所需证据。
- 不放普通备注、已确认事实、或无行动价值的问题。
- 建议总长度控制在 30-80 行（Markdown 源码）。

## evidence.yaml

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

## requirement-ir.yaml

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

## layer-impact.yaml

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
        affected_symbols:                     # GitNexus impact（可选，图谱可用时填充）
          - symbol: ""
            blast_radius: []
            confidence: 0.0
            graph_provider: "gitnexus"
        business_constraints:                 # Graphify 业务关联（可选，图谱可用时填充）
          - concept: ""
            related_concepts: []
            design_rationale: ""
            risk_if_violated: ""
            graph_provider: "graphify"
        graph_evidence_refs: []               # GEV-xxx / GEV-Bxxx 溯源
  bff:
    impacts: []
  backend:
    impacts: []
quality_gates: []
```

`surface` 使用 `layer-adapters.md` 中定义的能力面名称。

## contract-delta.yaml

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
    graph_evidence_refs: []               # GEV-xxx 图谱溯源（可选）
alignment_summary:
  status: "aligned | needs_confirmation | blocked | not_applicable"
  blockers: []
  next_actions: []
```

以下场景必须生成 Contract Delta：多层协作、API/schema 变化、下游系统集成、权益/券/支付/奖励链路、审计 payload、异步事件。

## reference-update-suggestions.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_reference/04-routing-playbooks.yaml"
    summary: ""
    evidence: ["EV-001"]
    priority: "high | medium | low"
    proposed_patch: ""
```
