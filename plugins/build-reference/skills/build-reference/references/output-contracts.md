# 输出契约 v2.8

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
└── artifacts/
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

用户默认只需要读 `report.md`（决策+阻塞问题）和 `plan.md`（技术方案+开发计划）。`prd-ingest/` 是原始文档读取层，`artifacts/` 是给 AI、审计、回流和高级排查使用的证据链。

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
| `questions.md` | `report.md` §10 |

## prd-ingest/

`prd-ingest/` 解决"PRD 到底被 AI 读成了什么"的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。

| 文件 | 用途 | 边界 |
|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、大小、hash、生成时间、读取方式 | 不写需求摘要或实现判断 |
| `document.md` | 转换后的可读 markdown，作为 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `document-structure.json` | 段落、标题、表格、图片等结构块，含 block id 和 locator | 不写业务语义结论 |
| `evidence-map.yaml` | PRD 块级证据，供 `artifacts/evidence.yaml` 映射 | 不放源码、diff、reference 证据 |
| `media/` | 抽出的图片、截图、流程图原文件 | 不修改图片内容 |
| `media-analysis.yaml` | 图片分析状态；LLM Vision 分析过为 `llm_vision_analyzed`（medium），否则 `needs_vision_or_human_review`（low） | 没有 vision/OCR/人工确认时不推断图片含义 |
| `tables/` | 单独抽出的表格 markdown | 不修复原表格，只保留转换结果 |
| `extraction-quality.yaml` | 读取质量门禁：`pass | warn | block`、统计、风险 | 不写开发计划 |
| `conversion-warnings.md` | 给人看的转换风险 | 不替代 report.md §10 |

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
- `warn`：允许继续，但必须在 `report.md` §10 中暴露风险。
- 图片、截图、流程图里的信息，没有 vision/OCR/人工确认时，只能作为待确认问题，不能作为高置信度结论。

## report.md

渐进式披露（Progressive Disclosure）：同一文件内从结论到细节逐层展开，包含阻塞问题与待确认项，不需要跳到其他文件就能获取核心信息。

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

## 10. 阻塞问题与待确认项

### 10.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

### 10.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。

### 10.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。

如无阻塞问题，显式写"当前无阻塞问题"。

---
*详细证据链见 artifacts/*，按需展开*
```

### 写作规则

- **自然语言为主**，避免纯 YAML/JSON 格式；用 Markdown 表格提高可扫描性。
- **具体到文件路径**：每个变更项都带目标文件路径（如 `model/business_object/xxx/`）。
- **关联 ID**：每个条目引用 REQ-*/IMP-*/CONTRACT-*，方便跳到 artifacts 查证。
- **不隐藏低置信度**：低置信度项用 ⚠ 标注，进入 §10.2。
- **Checklist 可直接执行**：开发人员拿到就能按步骤干活。
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）。这些线索对开发定位问题有极高价值。

### 职责边界

- **report.md 是决策文档，不是所有细节的全集**。
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责。
- 不要复制 PRD 原文，只引用 REQ-ID。
- 建议总长度控制在 250-500 行（Markdown 源码）。超限时精简优先级：变更明细表 > 字段清单 > 校验规则（先精简）；阻塞问题与线索 > 契约风险 > 影响范围（不精简）。

## plan.md

可 review 的初步技术方案文档 + 可执行的开发计划。精确到文件路径和行号，包含架构决策和数据模型。

### 结构模板

```markdown
# 技术方案：<需求名称>

## 1. 范围与假设
### 目标
本方案覆盖的 REQ 范围和预期产出。

### 非目标
明确排除的范围，避免过度设计。

### 前置条件与依赖
需要先完成的基础设施、其他团队接口、外部系统准备。

## 2. 整体架构
### 方案概述
用文字描述+简单框图说明整体方案。

### 核心数据模型
关键结构体/Schema 用伪代码展示字段结构（从源码已有结构体推断）。

### 关键设计决策
列出主要 trade-off 和选择理由（如：为什么选方案 A 不选方案 B）。

### 与现有系统的交互
调用链、数据流、涉及的已有模块和接口。

## 3. 实现计划
### Phase 1: 基础设施
- [ ] **1.1** <任务描述>
  - 文件：`path/to/file.go:27`
  - 操作：具体操作描述
  - 关联：REQ-001, IMP-BE-001
  - 验证：`grep -n "XXX" path/to/file.go`

### Phase 2: 核心功能
...

### Phase 3: 联调与收尾
...

## 4. API 设计
### Schema 变更
新增或修改的请求/响应字段表格。

### 接口变更
| 接口 | 方法 | 变更类型 | 字段变更 |

### 外部服务调用
调用的外部接口、预期请求/响应、超时和降级策略。

## 5. 数据存储
### 表/索引变更
新增表、新增字段、索引变更。

### 缓存变更
缓存 Key 设计、过期策略、一致性保证。

### Migration 要点
数据库迁移注意事项。

## 6. 配置与开关
### Feature Flag
开关名称、作用、默认值。

### 灰度策略
灰度维度（用户/城市/百分比）、回滚条件。

## 7. 校验规则汇总
| 规则 | 层 | 目标文件 | 错误提示 |
前端/BFF/后端校验规则矩阵。

## 8. QA 矩阵
| 场景 | 关键检查点 | 关联 REQ | 优先级 |
覆盖正常流 + 边界情况 + 异常流，P0/P1/P2 分级。

## 9. 契约对齐
| 契约 | 状态 | Producer | Consumer | 需确认内容 |
只列 needs_confirmation 和 blocked。

## 10. 风险与回滚
### 回滚方案
具体回滚步骤（如"关闭 Apollo 开关即可隐藏新类型"）。

### 观测建议
需要关注的 metric、日志、报警。

### 已知坑点
源码线索暗示的潜在问题（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）。

### 回归范围
哪些已有功能可能受影响，需要回归验证。

## 11. 工作量估算
| 模块 | 估算 | 说明 |
按模块估算人天，标注关键路径。
```

### 写作规则

- **精确到文件和行号**：每个任务给出目标文件路径，尽量带行号。不确定行号时标注"约在 XX 附近"，不要编造。
- **给出验证命令**：每个关键步骤附带 grep/go test 等验证命令。
- **给出参考实现**：类似功能的已有代码路径，开发人员可以参照。
- **代码线索不可省略**：每个任务必须保留文件路径、行号、参考结构体名、proxy 路径等线索。
- **Checklist 格式**：用 `- [ ]` 格式，开发人员可以直接勾选。
- **按 Phase 分组**：体现依赖关系，Phase 间标注前置条件。

### 职责边界

- **plan.md 是可 review 的技术方案，不是二次报告**。
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"。
- 不要复制 PRD 原文。
- 建议总长度控制在 300-600 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）。

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
