# 输出契约 v3.0

这些契约由 `/reference` 和 `/prd-distill` 共用。字段名保持英文，方便机器稳定解析；说明文字使用中文，方便团队阅读。

## 统一产出目录

两个插件共用 `_prd-tools/` 作为产出目录根：

```text
_prd-tools/
├── README.md                              # 产出索引
├── reference/                             # 知识库 SSOT（reference 产出）
│   ├── 00-portal.md
│   ├── 01-codebase.yaml
│   ├── 02-coding-rules.yaml
│   ├── 03-contracts.yaml
│   ├── 04-routing-playbooks.yaml
│   ├── 05-domain.yaml
│   └── project-profile.yaml
├── build/                                 # reference 运行报告
│   ├── modules-index.yaml
│   ├── context-enrichment.yaml
│   ├── quality-report.yaml
│   ├── health-check.yaml
│   ├── feedback-report.yaml
│   └── graph/
│       ├── STATUS.md
│       ├── sync-report.yaml
│       ├── code-evidence.yaml
│       └── business-evidence.yaml
└── distill/                               # prd-distill 蒸馏产出
    └── <slug>/
        ├── spec/
        │   ├── requirement-ir.yaml
        │   └── evidence.yaml
        ├── plan.md
        ├── report.md
        ├── readiness-report.yaml
        ├── tasks/
        │   └── T-NNN-*.md
        ├── context/
        │   ├── graph-context.md
        │   ├── layer-impact.yaml
        │   ├── contract-delta.yaml
        │   └── reference-update-suggestions.yaml
        └── _ingest/
            ├── source-manifest.yaml
            ├── document.md
            ├── document-structure.json
            ├── evidence-map.yaml
            ├── media/
            ├── tables/
            ├── extraction-quality.yaml
            └── conversion-warnings.md
```

用户默认只需要读：
- `_prd-tools/STATUS.md` 或 `_prd-tools/dashboard/index.html`（项目/最近一次 distill 状态入口）
- `_prd-tools/distill/<slug>/report.md`（决策+阻塞问题）
- `_prd-tools/distill/<slug>/plan.md`（技术方案+开发计划）
- `_prd-tools/distill/<slug>/readiness-report.yaml`（机器可读就绪度和 provider 增益）
- `_prd-tools/distill/<slug>/tasks/`（AI 可执行任务）

`spec/` 是结构化需求，`context/` 是契约分析上下文，`_ingest/` 是原始文档读取层。

## _ingest/

`_ingest/` 解决"PRD 到底被 AI 读成了什么"的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。

| 文件 | 用途 | 边界 |
|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、大小、hash、生成时间、读取方式 | 不写需求摘要或实现判断 |
| `document.md` | 转换后的可读 markdown，作为 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `document-structure.json` | 段落、标题、表格、图片等结构块，含 block id 和 locator | 不写业务语义结论 |
| `evidence-map.yaml` | PRD 块级证据，供 `spec/evidence.yaml` 映射 | 不放源码、diff、reference 证据 |
| `media/` | 抽出的图片、截图、流程图原文件 | 不修改图片内容 |
| `media-analysis.yaml` | 图片分析状态；LLM Vision 分析过为 `llm_vision_analyzed`（medium），否则 `needs_vision_or_human_review`（low） | 没有 vision/OCR/人工确认时不推断图片含义 |
| `tables/` | 单独抽出的表格 markdown | 不修复原表格，只保留转换结果 |
| `extraction-quality.yaml` | 读取质量门禁：`pass | warn | block`、统计、风险 | 不写开发计划 |
| `conversion-warnings.md` | 给人看的转换风险 | 不替代 report.md §11 |

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
- `warn`：允许继续，但必须在 `report.md` §11 中暴露风险。
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

## 3. 代码命中摘要
| 来源 | 命中内容 | 用于哪些结论 | 缺口 |
列出代码搜索命中的关键函数/调用链/API consumer。

## 4. 关键结论
新增/修改/不改什么，每个结论带 REQ-ID 和代码路径引用。

## 5. 变更明细表（核心可操作内容）
| ID | 变更描述 | 类型 | 目标文件 | 关键函数/符号 | 验证来源 |
列出所有 IMP-* 项，精确到文件路径和关键 symbol，标注 code_verified / graph_verified / reference_only。

## 6. 字段清单（按功能模块分组）
| 字段 | 类型 | 必填 | 来源 | 契约ID |
从 requirement-ir 和 contract-delta 中提取，按业务模块分组。

## 7. 校验规则
| ID | 规则描述 | 错误文案/提示 | 目标文件 |
从 requirement-ir.rules 中提取可验证的校验规则。

## 8. 开发 Checklist（可直接执行）
- [ ] 1. <具体操作>（<目标文件>）— REQ-001, IMP-001
- [ ] 2. <具体操作>（<目标文件>）— REQ-002, IMP-002
...
按建议实现顺序排列，每项标注关联的 REQ/IMP/CONTRACT。

## 9. 契约风险
只列 alignment_status 为 needs_confirmation 或 blocked 的契约。

## 10. Top Open Questions
最多5个最关键的阻塞问题，带 Q-ID。

## 11. 阻塞问题与待确认项

### 11.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

### 11.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。

### 11.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。

如无阻塞问题，显式写"当前无阻塞问题"。

---
*详细证据链见 spec/ 和 context/*
```

### 写作规则

- **自然语言为主**，避免纯 YAML/JSON 格式；用 Markdown 表格提高可扫描性。
- **具体到文件路径**：每个变更项都带目标文件路径（如 `model/business_object/xxx/`）。
- **关联 ID**：每个条目引用 REQ-*/IMP-*/CONTRACT-*，方便跳到 spec/ 或 context/ 查证。
- **不隐藏低置信度**：低置信度项用 ⚠ 标注，进入 §11.2。
- **Checklist 可直接执行**：开发人员拿到就能按步骤干活。
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）。这些线索对开发定位问题有极高价值。

### 职责边界

- **report.md 是决策文档，不是所有细节的全集**。
- 不要把完整 YAML 证据链展开到 report 里，那是 spec/ 和 context/ 的职责。
- 不要复制 PRD 原文，只引用 REQ-ID。
- 建议总长度控制在 300-650 行（Markdown 源码）。超限时精简优先级：字段清单 > 校验规则（先精简）；代码命中摘要 > 变更明细表 > 阻塞问题与线索 > 契约风险 > 影响范围（不精简）。

## plan.md

可 review 的函数级技术方案文档 + 可执行的开发计划。精确到文件路径、行号、关键函数/方法/结构体，包含架构决策、调用链、数据模型和回归范围。

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
### 代码坐标
| REQ | 入口/函数/结构体 | 文件:行号 | 调用链角色 | 来源 |
来自代码搜索。必须标注搜索来源（rg/Read 等）。

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
  - 关键函数/结构体：`SymbolName`
  - 操作：具体操作描述
  - 调用链影响：入口 -> 当前函数 -> 下游函数/consumer
  - 证据依据：`GCTX-001` / `EV-001`
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

## 12. AI 执行说明

### 目标
本次 AI 编码执行的具体目标（1-3 句话）。来自 `spec/requirement-ir.yaml` 的核心意图。

### 允许修改的文件
精确列出 AI 可以修改/创建的文件清单（来自 §3 实现计划 + `context/layer-impact.yaml` affected_files）。

### 禁止修改的文件
明确排除不在本次需求范围内的文件（共享配置、其他团队接口、已稳定的公共模块等）。

### 阻塞项（必须先确认）
从 `context/contract-delta.yaml` blocked 项和 report.md §11 提取。无阻塞项时写"无阻塞项，可直接执行"。

### 推荐执行顺序
按依赖拓扑排序的 task 序列：
- T-001 → T-002 → ...（标注依赖关系和对应 `tasks/` 文件名）

### 验证检查点
每个 Phase 完成后运行的验证命令（编译、测试、lint）。

### 失败排查优先级
1. 检查阻塞项是否已确认
2. 检查文件路径/行号是否匹配当前代码
3. 检查参考实现版本差异
4. 检查契约对齐状态
```

### 写作规则

- **精确到文件和行号**：每个任务给出目标文件路径，尽量带行号。不确定行号时标注"约在 XX 附近"，不要编造。
- **精确到函数级**：MODIFY/DELETE 任务必须给出入口函数、关键函数/方法/结构体、调用方/被调用方和回归影响；ADD 任务必须给出相邻参考实现或负向搜索证据。
- **Graph Context 优先**：先消费代码搜索结果，再写 plan。不能只根据 `_prd-tools/reference/` 写计划。
- **给出验证命令**：每个关键步骤附带 grep/go test 等验证命令。
- **给出参考实现**：类似功能的已有代码路径，开发人员可以参照。
- **代码线索不可省略**：每个任务必须保留文件路径、行号、参考结构体名、proxy 路径等线索。
- **Checklist 格式**：用 `- [ ]` 格式，开发人员可以直接勾选。
- **按 Phase 分组**：体现依赖关系，Phase 间标注前置条件。
- **§12 数据来自已有 artifacts**：不允许引入新的事实判断。允许/禁止文件清单必须和 `context/layer-impact.yaml` 的 affected_files 对齐。

### 职责边界

- **plan.md 是可 review 的技术方案，不是二次报告**。
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"。
- 不要复制 PRD 原文。
- 建议总长度控制在 300-700 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）。

## tasks/

`tasks/` 目录存放 AI 可直接消费的独立任务文件。每个文件是一个自包含的 vibe coding prompt。

### 文件命名

`T-{NNN}-{kebab-case-slug}.md`，例如 `T-001-add-campaign-type-enum.md`。

### 任务文件模板

```markdown
# T-{NNN}: {任务标题}

## Objective
本次任务要完成什么（1-2 句话）。来自 plan.md §3 对应 Step。

## Target Files
- `path/to/file.ts:行号` — 改动类型（MODIFY/ADD/DELETE）
- ...

## Forbidden Files
不可修改的文件列表。来自 plan.md §12 禁止文件清单。

## Business Context
来自 `spec/requirement-ir.yaml` 对应 REQ 的 rules 和 acceptance_criteria。
以 bullet list 形式列出与本次任务直接相关的业务规则。

## Code Context
### 当前代码
本次任务涉及的已有代码片段（通过 Read 工具读取后内联）。
仅包含与改动直接相关的函数/结构体/接口，不内联整个文件。

### 参考实现
类似功能的已有代码路径 + 关键代码片段（来自 plan.md §3 的参考实现字段）。

### 调用链
入口 → 当前函数 → 下游函数/consumer（来自 `context/graph-context.md` GCTX 条目）。

## Field Mappings
来自 `context/layer-impact.yaml` 和 `context/contract-delta.yaml`，仅列出与本次任务相关的字段映射表：
| PRD 字段 | name | 组件类型 | 约束 | 来源 |

## Contract Constraints
来自 `context/contract-delta.yaml`，仅列出与本次任务相关的契约约束。

## Implementation Steps
编号的操作步骤，每步说明具体改什么、怎么改。

## Verification
- `{验证命令}` — 预期结果
- `{验证命令}` — 预期结果

## Dependencies
- 前置任务：T-{NNN}（如无写"无前置依赖"）
- 后续任务：T-{NNN}
```

### 生成规则

- 每个 task 文件对应 plan.md §3 中的一个 Step（Phase 1.1 → T-001, Phase 1.2 → T-002, ...）。
- **上下文内联**：每个 task 必须自包含，AI 不需要读其他文件就能执行。参照代码、字段映射、契约约束从 spec/ 和 context/ 内联。
- **Code Context 精确度**：内联的代码片段仅包含与改动直接相关的部分（函数签名、结构体定义、关键逻辑），不超过 80 行。超过时截取关键部分并标注"完整实现见 `path/to/file.ts:行号`"。
- **依赖声明**：每个 task 显式声明前置/后续 task，形成 DAG。
- **禁止文件**：每个 task 继承 plan.md §12 的禁止文件清单。
- **所有数据来自已有 artifacts**：spec/requirement-ir（业务上下文）、context/layer-impact（字段映射）、context/contract-delta（契约约束）、源码搜索（调用链、参考实现）、源码（当前代码片段）。不引入新的事实判断。

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

## spec/evidence.yaml

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

## spec/requirement-ir.yaml

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

## readiness-report.yaml

`readiness-report.yaml` 是单次 PRD 蒸馏的机器可读红绿灯。它回答"这次分析能不能进入开发/评审，为什么"，同时给 `_prd-tools/STATUS.md` 和 dashboard 提供数据。

```yaml
schema_version: "3.0"
tool_version: "<tool-version>"
generated_at: "2026-05-08T00:00:00Z"
distill_slug: "<slug>"
status: "pass | warning | fail"
score: 0
decision: "ready_for_dev | needs_owner_confirmation | blocked"
summary:
  title: ""
  top_reason: ""
scores:
  prd_ingestion: 0
  evidence_coverage: 0
  code_search: 0
  contract_alignment: 0
  task_executability: 0
risks:
  blocked:
    - id: ""
      title: ""
      owner: ""
      source: "contract | evidence | ingestion | task"
  needs_confirmation:
    - id: ""
      title: ""
      owner: ""
      source: "contract | evidence | ingestion | task"
  low_confidence_assumptions: []
provider_value:
  reference:
    reused_playbooks: 0
    reused_contracts: 0
    examples: []
next_actions: []
```

评分建议：

| 维度 | 权重 | 数据来源 |
|---|---:|---|
| `prd_ingestion` | 20 | `_ingest/extraction-quality.yaml`、media/table warnings |
| `evidence_coverage` | 25 | `spec/evidence.yaml`、`spec/requirement-ir.yaml` |
| `code_search` | 15 | 代码搜索覆盖率 |
| `contract_alignment` | 25 | `context/contract-delta.yaml` |
| `task_executability` | 15 | `plan.md`、`tasks/` |

状态阈值：

| 分数 | status | decision |
|---:|---|---|
| 85-100 | `pass` | `ready_for_dev`，除非有硬阻塞 |
| 60-84 | `warning` | `needs_owner_confirmation` |
| 0-59 | `fail` | `blocked` |

硬性降级：

- `_ingest/extraction-quality.yaml` 为 `block` → `fail`。
- 任一 P0 契约为 `blocked` → `fail`。
- 多层需求缺少 `context/contract-delta.yaml` → `fail`。
- `tasks/` 缺少目标文件或验证命令 → 至少 `warning`。
