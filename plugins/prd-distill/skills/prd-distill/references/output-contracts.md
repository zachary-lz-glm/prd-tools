# 输出契约 v3.0

这些契约由 `/reference` 和 `/prd-distill` 共用。字段名保持英文，方便机器稳定解析；说明文字使用中文，方便团队阅读。

**辅助层产出**：必须存在且通过 gate 校验，但不是用户的首要阅读目标（如 query-plan、context-pack、final-quality-gate、prd-quality-report）。

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
│   ├── project-profile.yaml
│   ├── portal.html                        # ⚠️ 脚本渲染（render-reference-portal.py），AI 不得手写
│   └── index/                     # Evidence Index（辅助层）
│       ├── entities.json          # 代码实体索引
│       ├── edges.json             # 实体关系索引
│       ├── inverted-index.json    # 倒排索引
│       └── manifest.yaml          # 索引元数据
├── build/                                 # reference 运行报告
│   ├── modules-index.yaml
│   ├── context-enrichment.yaml
│   ├── quality-report.yaml
│   ├── health-check.yaml
│   ├── feedback-report.yaml
└── distill/                               # prd-distill 蒸馏产出
    └── <slug>/
        ├── spec/                          # AI-friendly PRD（规范化中间层）
        │   └── ai-friendly-prd.md         #   13-section 对 AI agent 友好的 PRD
        ├── plan.md
        ├── report.md
        ├── portal.html                    # ⚠️ 脚本渲染（render-distill-portal.py），AI 不得手写
        ├── context/
        │   ├── prd-quality-report.yaml    #   AI-friendly PRD 质量评分
        │   ├── requirement-ir.yaml
        │   ├── evidence.yaml
        │   ├── readiness-report.yaml
        │   ├── graph-context.md
        │   ├── layer-impact.yaml
        │   ├── contract-delta.yaml
        │   ├── reference-update-suggestions.yaml
        │   ├── query-plan.yaml              # 查询计划（辅助层）
        │   ├── context-pack.md              # 上下文包（辅助层）
        │   └── final-quality-gate.yaml      # 最终质量门禁（辅助层）
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
- `_prd-tools/distill/<slug>/report.md`（决策+阻塞问题）
- `_prd-tools/distill/<slug>/plan.md`（技术方案+开发计划）
- `_prd-tools/distill/<slug>/portal.html`（可视化浏览器页面，双击即可打开）
- `_prd-tools/distill/<slug>/context/readiness-report.yaml`（就绪度评分、阻塞项）

`context/` 包含结构化需求、证据台账、契约分析上下文和就绪度评分，`_ingest/` 是原始文档读取层。

## _ingest/

`_ingest/` 解决"PRD 到底被 AI 读成了什么"的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。`.md`/`.txt` 直接读取，`.docx` 用 `unzip -p <file> word/document.xml | sed 's/<[^>]*>//g'` 提取纯文本后写入 `document.md`。

| 文件 | 用途 | 边界 |
|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、大小、hash、生成时间、读取方式 | 不写需求摘要或实现判断 |
| `document.md` | 转换后的可读 markdown，作为 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `document-structure.json` | 段落、标题、表格、图片等结构块，含 block id 和 locator。`exclusion_types` 字段列出不需要 evidence 覆盖的 block 类型（如 `revision_history`、`toc`、`decoration`） | 不写业务语义结论 |
| `evidence-map.yaml` | PRD 块级证据，供 `context/evidence.yaml` 映射。顶层字段：`meta`（元数据）、`blocks`（数组，每个元素含 `block_id / lines / content_summary / req_ids`） | 不放源码、diff、reference 证据 |
| `media/` | 抽出的图片、截图、流程图原文件（docx 提取时自动抽取） | 不修改图片内容 |
| `media-analysis.yaml` | 图片分析状态和摘要。顶层字段 `media`（权威）是数组，每条含 `file / type / summary / confidence`；`images`/`items` 仅为兼容旧产物。类型：`ui_screenshot | flowchart | data_chart | table_image | decoration` | 不确认的图片内容只能产生低置信度问题 |
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
  - "Images are analyzed by Claude Read (native multimodal). AI-interpreted content is medium confidence by default."
```

`media-analysis.yaml` 示例：

```yaml
schema_version: "1.0"
media:
  - file: "media/image2.png"
    type: "ui_screenshot"
    summary: "DIVE 2.0 MIS 创建活动页面-目标人群步骤，包含是否限制司机、人群选择方式、CSV上传等表单"
    confidence: "medium"
  - file: "media/image5.png"
    type: "ui_screenshot"
    summary: "活动规则配置页面，包含完单数、奖励类型（折扣卡/优惠券）、优惠券配置模块"
    confidence: "medium"
  - file: "media/image1.png"
    type: "data_chart"
    summary: "司机早期加油次数与30日留存增长率关系图"
    confidence: "medium"
```

质量规则：

- `block`：暂停蒸馏，要求用户提供 markdown/text。
- `warn`：允许继续，但必须在 `report.md` §12 中暴露风险。
- Claude 看图提取的信息置信度为 `medium`（AI 视觉理解），关键结论仍需文本证据或人工确认才能升为 `high`。

## spec/ai-friendly-prd.md

AI-friendly PRD（规范化中间层）：把现实中不够 AI-friendly 的 PRD 编译成对 AI agent 友好的统一 13-section 结构。它不替代原始 PRD，也不替代 report.md / plan.md / requirement-ir.yaml，但后续步骤必须优先读取它。

| 用途 | 边界 |
|---|---|
| 给 AI agent 消费的规范化 PRD，13 个固定章节、原子化 REQ-ID、source 标记 | 不替代原始 PRD；不替代 report.md / plan.md / requirement-ir.yaml |

### 13-section 结构

```markdown
# AI-friendly PRD: <title>

## 1. Overview
说明需求背景、业务目标、产品范围。

## 2. Problem Statement
说明要解决的问题、当前痛点、为什么要做。

## 3. Target Users
列出角色、用户群、使用场景。

## 4. Goals & Success Metrics
列出目标和可衡量指标。
如果原 PRD 没有指标，必须标注：`Missing confirmation`。

## 5. User Stories
用统一格式：
- As a <role>, I want <capability>, so that <benefit>.
每条必须有 source 标记。

## 6. Functional Requirements
原子化需求列表。
格式：
- REQ-001
  - Priority: P0/P1/P2
  - Statement:
  - Source: explicit | inferred | missing_confirmation
  - Evidence: 原 PRD 摘要或位置描述
  - Acceptance Criteria:
    - AC-001:

## 7. Non-Functional Requirements
性能、权限、兼容性、稳定性、国际化、可观测性等。
没有则写 `No explicit NFR found`，不能编造。

## 8. Technical Considerations
接口、字段、枚举、状态、配置、数据流、前端/BFF/后端边界。
不确定的写 `Needs owner confirmation`。

## 9. UI/UX Requirements
页面、表单、组件、文案、错误提示、预览、交互。
没有明确 UI 描述则写缺失。

## 10. Out of Scope
明确不做什么。
如果原 PRD 没写，列出 inferred risks，不要当事实。

## 11. Timeline & Milestones
里程碑、灰度、上线、依赖。
原 PRD 没有则标 missing。

## 12. Risks & Mitigations
列出冲突、歧义、缺字段、跨团队依赖、实现风险。

## 13. Open Questions
必须列出所有需要 owner 确认的问题。
每条包含：
- Question
- Why it matters
- Blocking level: P0/P1/P2
- Suggested owner: PM/FE/BFF/BE/QA/Unknown
```

### Source 标记规则

所有关键条目必须标注：

- `source: explicit`：原 PRD 明确写了。
- `source: inferred`：从上下文合理推断，但原文没有直接写清楚。
- `source: missing_confirmation`：缺失或冲突，必须确认。

硬约束：

1. `inferred` 不能进入最终 plan 的必做项，除非 report/questions 明确提示需确认。
2. `missing_confirmation` 必须进入 Open Questions（§13）。
3. `requirement-ir.yaml` 中每条 requirement 应能追溯到 ai-friendly-prd.md 的 REQ-ID。
4. `report.md` 中必须说明 AI-friendly PRD 的质量状态。
5. `plan.md` 不得把 `missing_confirmation` 当确定实现任务。

## context/prd-quality-report.yaml

AI-friendly PRD 质量评分：评估原始 PRD 转换为 AI-friendly PRD 的质量、缺失项、推断项和风险项。

- `overall_score` (int, 0-100): 权威字段，按评分公式计算。
- `score` (int, 0-100, 已废弃): 旧字段名，新产物不要写，gate 仍接受但不推荐。

```yaml
schema_version: "1.0"
status: "pass | warning | fail"
overall_score: 0
summary:
  decision: "ready_for_distill | distill_with_warnings | needs_prd_clarification"
  top_reasons: []
scores:
  structure:
    score: 0
    max: 20
    findings: []
  atomicity:
    score: 0
    max: 15
    findings: []
  acceptance_criteria:
    score: 0
    max: 20
    findings: []
  constraints_and_scope:
    score: 0
    max: 15
    findings: []
  technical_specificity:
    score: 0
    max: 15
    findings: []
  ambiguity_risk:
    score: 0
    max: 15
    findings: []
counts:
  requirements_total: 0
  explicit_requirements: 0
  inferred_requirements: 0
  missing_confirmation_items: 0
  acceptance_criteria_total: 0
  open_questions: 0
risks:
  blockers: []
  warnings: []
  ambiguous_terms: []
  conflicting_values: []
  missing_sections: []
coverage:
  has_overview: true/false
  has_problem_statement: true/false
  has_target_users: true/false
  has_success_metrics: true/false
  has_user_stories: true/false
  has_functional_requirements: true/false
  has_nfr: true/false
  has_technical_considerations: true/false
  has_ui_ux: true/false
  has_out_of_scope: true/false
  has_timeline: true/false
  has_risks: true/false
  has_open_questions: true/false
```

评分规则（总分 100）：

| 维度 | 分值 | 说明 |
|---|---:|---|
| structure | 20 | 是否能映射到 13 个章节；是否有清晰标题/表格/列表；是否能区分背景、需求、规则、问题 |
| atomicity | 15 | 需求是否可拆成原子 REQ；是否混合多个动作；是否存在一条需求多个验收口径 |
| acceptance_criteria | 20 | 是否有可验证 AC；是否有数值范围、边界条件、错误提示；是否能转成测试条件 |
| constraints_and_scope | 15 | 是否有 out of scope；是否有权限、互斥、灰度、兼容、依赖边界 |
| technical_specificity | 15 | 是否有字段、枚举、状态、接口、配置、前端/BFF/后端边界 |
| ambiguity_risk | 15 | 模糊词越多扣分；冲突数字扣分；图片/表格无文字说明扣分；关键 owner 缺失扣分 |

状态阈值：

- 85-100：`pass`
- 60-84：`warning`
- 0-59：`fail`

硬降级：

- P0 需求超过 3 条 `missing_confirmation`：最多 `warning`
- 核心功能目标不明确：`fail`
- 无法提取 functional requirements：`fail`
- PRD 主要信息在图片/表格但未解析：`warning` 或 `fail`

| 用途 | 边界 |
|---|---|
| 评估 AI-friendly PRD 转换质量、source 分布、缺失项 | 不替代 readiness-report.yaml（就绪度评估）；不替代 report.md（人类决策文档） |

> **辅助层定位**：prd-quality-report 是 Step 1.5 的质量评估产出，为后续 Step 2 Requirement IR 和 Step 8 Report 提供输入，但不替代 readiness-report 的综合就绪度评估。

## portal.html ⚠️ 脚本渲染

> **由渲染脚本生成，AI 不得手写。**
> 修改此文件前，应编辑对应插件的 portal-template.html 并重新运行渲染脚本。

自包含 HTML 可视化页面，将 report.md、plan.md 和 context/* 的内容整合为一个浏览器可交互页面。零外部依赖，file:// 协议可用。

| 属性 | 值 |
|------|-----|
| generated_by | 渲染脚本（各插件独立） |
| template | 各插件的 `assets/portal-template.html` |
| 手写 | ❌ 禁止 |
| 渲染命令 | `python3 scripts/render-*-portal.py`（各插件独立） |

| 用途 | 边界 |
|---|---|
| 浏览器一站式浏览蒸馏产出的总览、源码命中、影响分析、契约差异、开发计划、QA 矩阵、阻塞问题和回流建议 | 不替代 report.md 和 plan.md 的人读文本；不包含原始 PRD 内容 |

## report.md

渐进式披露（Progressive Disclosure）：同一文件内从结论到细节逐层展开，包含阻塞问题与待确认项，不需要跳到其他文件就能获取核心信息。

### 结构模板

```markdown
# 需求分析报告：<需求名称>

## 1. 需求摘要（30秒决策）
一句话摘要 + 变更类型统计（ADD/MODIFY/DELETE/NO_CHANGE 各几项）。

## 2. PRD 质量摘要
来自 `context/prd-quality-report.yaml`：
- AI-friendly PRD 总分和状态（pass / warning / fail）
- source 分布：explicit / inferred / missing_confirmation 各多少条
- 关键缺失项、硬降级原因、风险摘要
- 如果 `prd-quality-report.yaml` 状态为 fail 或 warning，必须在此说明对后续蒸馏的影响

## 3. 源码扫描命中摘要
| 来源 | 命中内容 | 用于哪些结论 | 缺口 |
列出代码搜索命中的关键函数/调用链/API consumer。

## 4. 影响范围
命中的层、能力面、关键文件/模块（表格形式）。

## 5. 关键结论
新增/修改/不改什么，每个结论带 REQ-ID 和代码路径引用。

## 6. 变更明细表（核心可操作内容）
| ID | 变更描述 | 类型 | 目标文件 | 关键函数/符号 | 验证来源 |
列出所有 IMP-* 项，精确到文件路径和关键 symbol，标注 code_verified / graph_verified / reference_only。

## 7. 字段清单（按功能模块分组）
| 字段 | 类型 | 必填 | 来源 | 契约ID |
从 requirement-ir 和 contract-delta 中提取，按业务模块分组。

## 8. 校验规则
| ID | 规则描述 | 错误文案/提示 | 目标文件 |
从 requirement-ir.rules 中提取可验证的校验规则。

## 9. 开发 Checklist（可直接执行）
- [ ] 1. <具体操作>（<目标文件>）— REQ-001, IMP-001
- [ ] 2. <具体操作>（<目标文件>）— REQ-002, IMP-002
...
按建议实现顺序排列，每项标注关联的 REQ/IMP/CONTRACT。

## 10. 契约风险
只列 alignment_status 为 needs_confirmation 或 blocked 的契约。

## 11. Top Open Questions
最多5个最关键的阻塞问题，带 Q-ID。

## 12. 阻塞问题与待确认项

### 12.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

### 12.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。

### 12.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。

如无阻塞问题，显式写"当前无阻塞问题"。

---
*详细证据链见 context/*
```

### 写作规则

- **自然语言为主**，避免纯 YAML/JSON 格式；用 Markdown 表格提高可扫描性。
- **具体到文件路径**：每个变更项都带目标文件路径（如 `model/business_object/xxx/`）。
- **关联 ID**：每个条目引用 REQ-*/IMP-*/CONTRACT-*，方便跳到 context/ 查证。
- **不隐藏低置信度**：低置信度项用 ⚠ 标注，进入 §11.2。
- **Checklist 可直接执行**：开发人员拿到就能按步骤干活。
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）。这些线索对开发定位问题有极高价值。
- **P0/P1 需求细节必须显性披露**：券批次/券张数/互斥、折扣卡 Card ID/数量/有效期/城市校验、EventRule、Budget/GMV、Push 占位符不能只存在于 `context/`，必须在 report 的字段、校验、阻塞或 open question 中出现。
- **冲突比结论更重要**：PRD 内部范围矛盾、报错文案 typo、owner 职责不清必须进入 §12；不要被 reference 的既有打法掩盖。
- **OQ 质量约束**：Open Questions 必须是真正的未解决问题。如果 report 正文已给出推断结论（如 typo 已识别为 "应为 X"），应列为 Assumption 而非 OQ。
- **Reference 不可盲信**：reference/index 命中的事实必须被 PRD、源码、技术文档、接口文档或负向搜索确认。无法确认时写成低/中置信度假设。

### 职责边界

- **report.md 是决策文档，不是所有细节的全集**。
- 不要把完整 YAML 证据链展开到 report 里，那是 context/ 的职责。
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

### 职责边界

- **plan.md 是可 review 的技术方案，不是二次报告**。
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"。
- 不要复制 PRD 原文。
- 建议总长度控制在 300-700 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）。

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
每个 GCTX 条目中定位到的代码锚点汇总表，方便 report/plan 直接引用。

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
- graph-context 不只是代码扫描摘要，要成为 REQ→代码证据链的一部分。
- 每个 code anchor 必须说明是由 rg、GitNexus/reference、源码阅读还是推断得到。
- 低置信度 anchor 必须进入 report 风险或 plan 假设。
- 新增 §3 Code Anchor 汇总表，为 report/plan 提供可直接引用的锚点清单。

## context/evidence.yaml

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
  primary_source: "_ingest/document.md"
  source_docs: []
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
      source_block_ids: []
      source_blocks: []
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

### 字段说明

| 字段 | 含义 |
|---|---|
| `id` | requirement-ir 自己的稳定 REQ-ID |
| `ai_prd_req_id` | 必须引用 `spec/ai-friendly-prd.md` 中的 REQ-ID |
| `source` | 继承 AI-friendly PRD 的 source 状态：explicit / inferred / missing_confirmation |
| `evidence.summary` | 该需求来自 AI-friendly PRD 哪段、原始 PRD 哪段 |
| `evidence.source_block_ids` | AI-friendly PRD 或原始 PRD 的 block ID（旧格式兼容） |
| `evidence.source_blocks` | AI-friendly PRD 或原始 PRD 的 block ID（新格式，与 source_block_ids 任一非空即可） |
| `acceptance_criteria.source` | AC 的 source 状态 |
| `acceptance_criteria.testability` | AC 是否可转成测试条件 |
| `open_question_refs` | 关联 ai-friendly-prd §13 或 questions.md 的问题 ID |
| `confirmation.status` | 是否已确认：confirmed / needs_confirmation / blocked |
| `planning.eligibility` | explicit 且无阻塞 → ready；inferred → assumption_only；missing_confirmation → blocked |

### Source 继承规则

- AI-friendly PRD 中 `explicit` 的 REQ → requirement-ir `source` 必须为 `explicit`，`planning.eligibility` 可为 `ready`。
- AI-friendly PRD 中 `inferred` 的 REQ → requirement-ir `source` 必须为 `inferred`，`planning.eligibility` 默认为 `assumption_only`（除非 report/questions 明确标注确认路径）。
- AI-friendly PRD 中 `missing_confirmation` 的 REQ → requirement-ir `source` 必须为 `missing_confirmation`，`planning.eligibility` 必须为 `blocked`，`confirmation.status` 必须为 `blocked`。

### 降级规则

- 如果 acceptance_criteria 缺失或 `testability: not_testable`，`planning.eligibility` 不能为 `ready`。
- 如果 P0 requirement 是 `missing_confirmation`，`confirmation.status` 必须为 `blocked`。
- `missing_confirmation` 必须进入 `open_question_refs`。
- `inferred` 不能直接进入确定开发 checklist，只能作为 `assumption_only`。
- report.md 和 plan.md 只能消费 `planning.eligibility` 为 `ready` 的确定实现项。`assumption_only` / `blocked` 必须进入问题、风险或前置确认。

Requirement IR 只描述业务意图和可验收规则，不写文件级实现细节。

## context/layer-impact.yaml

Layer Impact 是 REQ→代码影响的结构化映射。每个 IMP 必须能追溯到 requirement-ir 的 REQ-ID 和 AI-friendly PRD 的 source 状态。

```yaml
schema_version: "5.0"
tool_version: "<tool-version>"
layers:
  - layer: "frontend"
    capability_areas:
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
  - layer: "bff"
    capability_areas: []
  - layer: "backend"
    capability_areas: []
quality_gates: []
```

### 字段说明

| 字段 | 含义 |
|---|---|
| `id` | IMP 稳定 ID，格式 IMP-{层缩写}-{序号} |
| `requirement_id` | 必须引用 requirement-ir 的 REQ-ID |
| `ai_prd_req_id` | 必须引用 `spec/ai-friendly-prd.md` 的 REQ-ID |
| `requirement_source` | 继承 requirement 的 source 状态 |
| `planning_eligibility` | 继承 requirement 的 planning.eligibility |
| `code_anchors` | 代码锚点列表：精确定位到文件/符号/行号 |
| `code_anchors[].source` | 锚点来源：graph（源码确认）/ rg（搜索命中）/ reference（知识库路由）/ inferred（推断） |

### 强绑定规则

- 每个 IMP 必须引用 `requirement_id`，并继承 `ai_prd_req_id`、`requirement_source`、`planning_eligibility`。
- `planning_eligibility=blocked` 的 requirement 不得生成确定性实现 IMP，只能生成风险/待确认影响。
- `planning_eligibility=assumption_only` 的 requirement 只能生成假设性影响，标注需确认。
- `ready` 的 MODIFY/DELETE IMP 必须至少有一个 `code_anchor`，除非明确写入 fallback reason。
- ADD IMP 可以没有已有 `code_anchor`，但必须写 `target` surface 和 proposed location / owner layer。
- `code_anchor.source=inferred` 时，不得作为唯一 high confidence 证据。

`surface` 使用 `layer-adapters.md` 中定义的能力面名称。

## context/contract-delta.yaml

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
meta:
  primary_source: "_ingest/document.md"
  ai_prd_source: "spec/ai-friendly-prd.md"
  requirement_ir_ref: "context/requirement-ir.yaml"
deltas:
  - id: "CD-001"
    name: ""
    producer: "frontend | bff | backend | external"
    consumers: ["frontend", "bff", "backend", "external"]
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    layer: "bff"
    requirement_id: "REQ-001"
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

`readiness-report.yaml` 是单次 PRD 蒸馏的机器可读红绿灯。它回答"这次分析能不能进入开发/评审，为什么"。

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
| `evidence_coverage` | 25 | `context/evidence.yaml`、`context/requirement-ir.yaml` |
| `code_search` | 15 | 代码搜索覆盖率 |
| `contract_alignment` | 25 | `context/contract-delta.yaml` |
| `task_executability` | 15 | `plan.md`（文件路径精确度、验证命令覆盖） |

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

## _prd-tools/reference/index/

Evidence Index（辅助层）：基于正则扫描的代码实体索引，为下游 `/prd-distill` 提供确定性代码锚点检索。

| 文件 | 用途 | 边界 |
|---|---|---|
| `entities.json` | 代码实体：函数、类、枚举、接口、常量等 | 不替代 reference 的业务语义 |
| `edges.json` | 实体关系：DEFINES、IMPORTS、RESOLVED_IMPORT、REGISTERS、REFERENCES | 不记录跨仓关系 |
| `inverted-index.json` | term→entity 倒排索引 | 不含业务术语（仅代码符号） |
| `manifest.yaml` | 索引元数据：实体数、边数、term 数、构建时间 | 不含质量评分 |

> **辅助层定位**：index/ 不替代 reference 的 6 个文件作为 SSOT。reference 是业务知识的权威来源，index 是代码结构的检索加速器。

## context/query-plan.yaml

查询计划（辅助层）：从 requirement-ir 和 layer-impact 提取的代码锚点检索提示。

```yaml
schema_version: "1.0"
phases:
  seed_anchors: []
  impact_hints: []
  p0_requirements: []
```

> **辅助层定位**：query-plan 是 context-pack.py 的中间产物，为 Graph Context 步骤提供搜索提示，不替代 graph-context.md。

## context/context-pack.md

上下文包（辅助层）：融合 Evidence Index 代码实体与 distill 上下文的精简文档（≤800 行），供模型直接消费。

包含 6 个 Section：
1. Requirement Seed Terms
2. Key Code Entities（按 requirement 分组）
3. Impact-Related Entities
4. Similar Registry/Template
5. High-Confidence Code Clues
6. Query Plan Summary

> **辅助层定位**：context-pack 不替代 graph-context.md。graph-context.md 是源码扫描的主产出，context-pack 是索引增强的辅助摘要。

## context/final-quality-gate.yaml

最终质量门禁（辅助层）：对所有交付物执行 5 项确定性检查的评分报告。

```yaml
schema_version: "1.0"
status: "pass | warning | fail"
score: 0
checks:
  required_files: { status: "", score: 0 }
  context_pack_consumed: { status: "", score: 0 }
  code_anchor_coverage: { status: "", score: 0 }
  plan_actionability: { status: "", score: 0 }
  blocker_quality: { status: "", score: 0 }
summary:
  top_gaps: []
```

> **辅助层定位**：final-quality-gate 不替代 readiness-report.yaml。readiness-report 是就绪度评估的主产出，final-quality-gate 是对交付物完整性的确定性检查补充。

## Portal 模板与渲染脚本

Portal 页面采用模板+脚本渲染机制，AI 不得直接手写 `portal.html`，必须通过修改模板并运行渲染脚本生成。

### reference portal

| 文件 | 路径 | 用途 |
|------|------|------|
| 模板 | `plugins/reference/skills/reference/assets/portal-template.html` | HTML 骨架 + CSS + 占位符，AI 可编辑 |
| 渲染脚本 | `scripts/render-reference-portal.py` | 读取模板 + reference 数据，输出 `portal.html` |
| 产出 | `_prd-tools/reference/portal.html` | 脚本渲染生成，AI 禁止手写 |

### distill portal

| 文件 | 路径 | 用途 |
|------|------|------|
| 模板 | `plugins/prd-distill/skills/prd-distill/assets/portal-template.html` | HTML 骨架 + CSS + 占位符，AI 可编辑 |
| 渲染脚本 | `scripts/render-distill-portal.py` | 读取模板 + distill 数据，输出 `portal.html` |
| 产出 | `_prd-tools/distill/<slug>/portal.html` | 脚本渲染生成，AI 禁止手写 |

### 渲染流程

1. 编辑对应插件的 `portal-template.html`（修改布局、样式、占位符）
2. 运行渲染脚本：`python3 scripts/render-reference-portal.py` 或 `python3 scripts/render-distill-portal.py`
3. 脚本读取模板，注入数据，输出 `portal.html`
4. 任何对 `portal.html` 的直接手写修改都会在下次渲染时被覆盖

## `context/final-quality-gate.yaml` overall_score 算法

```
weighted_avg = sum(check_weight * check_score for each check) / sum(check_weights)
overall_score = round(weighted_avg)
```

权重表（`scripts/final-quality-gate.py` CHECK_WEIGHTS）：

| 检查项 | 权重 |
|--------|------|
| required_files | 0.20 |
| context_pack_consumed | 0.15 |
| code_anchor_coverage | 0.25 |
| plan_actionability | 0.25 |
| blocker_quality | 0.15 |

`status` 映射：
- overall_score >= 85 → pass
- 60 <= overall_score < 85 → warning
- overall_score < 60 → fail

额外硬失败规则（无论 score 多少）：
- required_files 有 missing_critical → fail
- plan_actionability 有 missing_file_paths → fail
- plan_actionability 有 missing_checklists → warning (cap 84)
