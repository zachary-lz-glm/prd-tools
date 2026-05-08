# PRD Tools

PRD Tools 是一套面向业务研发团队的 AI 工程工作流，把 PRD 从“自然语言需求”转成“有证据、可执行、可测试、可回流”的开发计划。

使用方只需要记住两个入口：

| 步骤 | 入口 | 结果 |
|---|---|---|
| 1 | `/reference` | 建好项目上下文 `_prd-tools/reference/` |
| 2 | `/prd-distill` | 把 PRD 变成技术文档 `report.md` + `plan.md` |

它不是单纯让 AI 帮忙“理解一下 PRD”，而是让 AI 在真实代码库里完成四件事：

1. 建立项目知识库，沉淀项目结构、业务术语、跨层契约和高频开发套路。
2. 将新 PRD 拆成结构化需求、分层影响、契约差异、开发计划和测试计划。
3. 用源码、PRD、技术方案、git diff 和负向搜索为每个结论提供证据。
4. 将每次真实需求中发现的新知识、踩坑和契约变化回流到项目知识库。

适用对象：

- 前端、BFF、后端业务团队。
- 需要频繁根据 PRD 改代码的业务项目。
- 跨团队字段、接口、活动类型、权益、奖励、券、预算、审核、异步任务等协作较多的项目。
- 希望让 AI 输出不只停留在“泛泛分析”，而是能产出可执行工程计划的团队。

不适用场景：

- 一次性 demo、无长期维护价值的小项目。
- 没有源码、没有 PRD、也没有任何可验证上下文的纯脑暴场景。
- 希望 AI 直接跳过分析、直接大范围改代码的场景。

## 核心理念

```text
PRD / 技术方案 / 源码 / 历史 diff
        ↓
/reference
        ↓
项目知识库 _prd-tools/reference/
        ↓
/prd-distill
        ↓
report / plan / spec
        ↓
反馈回流到 _prd-tools/reference/
```

这套工作流的核心判断是：PRD-to-code 的难点通常不在“写几行代码”，而在以下问题：

- PRD 里的业务词和代码里的字段、枚举、模块名称不一致。
- 前端、BFF、后端对同一个字段的 owner 和 required 认知不一致。
- AI 容易只看当前仓库，忽略上下游契约和外部系统。
- 同类需求反复返工，但历史经验没有被沉淀。
- 测试计划和开发计划脱节，导致提测后才发现规则缺口。

PRD Tools 用 `_prd-tools/reference/` 做长期记忆，用 `_prd-tools/` 做单次需求分析，用 evidence 机制保证结论可追溯。

当前 `_prd-tools/reference/` 是单仓知识库：后端仓、前端仓、BFF 仓各自维护自己的事实。跨仓契约和团队级知识可以先作为候选信号沉淀，后续再由团队知识库聚合 confirmed 事实。

## PRD 读取链路

PRD Tools 不把 `.docx` 或 PDF 直接交给 LLM 猜。`prd-distill` 会先做一层 PRD Ingestion，把原始文档转成可审计的中间产物，再进入 Requirement IR 和分层影响分析。

```text
原始 PRD 文件
        ↓
prd-ingest：文本 / 表格 / 图片 / 结构 / 质量门禁
        ↓
Requirement IR：业务规则、验收条件、变更类型
        ↓
Layer Impact / Contract Delta / Plan
```

当前内置能力：

| 输入 | 处理方式 | 风险处理 |
|---|---|---|
| `.docx` | MarkItDown 抽取正文、表格、图片 | 图片语义、复杂合并表格默认进入质量警告 |
| `.pdf` | MarkItDown 内置 PDF 解析 | 表格、图片、阅读顺序默认进入质量警告 |
| `.pptx` / `.xlsx` | MarkItDown 转换 | 复杂动画/公式可能丢失细节 |
| `.html` / `.epub` | MarkItDown 转换 | 样式依赖的内容可能丢失 |
| `.md` / `.txt` | 保留原文和行号，识别 markdown 图片引用 | 图片引用需要 vision 或人工确认 |
| 粘贴文本 | 手工建立来源、段落定位和质量说明 | 缺少原文件 hash，置信度按输入质量标注 |
| PRD 中的图片/流程图 | LLM Vision（markitdown-ocr）自动分析 | 未配置 API Key 时标记为待确认 |

内置 ingestion 会生成：

```text
_prd-tools/distill/<slug>/_ingest/
├── source-manifest.yaml        # 原始文件路径、格式、大小、hash、读取方式
├── document.md                 # 转换后的可读 markdown，后续 IR 的主输入
├── document-structure.json     # 段落、表格、图片等结构块和定位
├── evidence-map.yaml           # PRD 块级证据 id
├── media/                      # 从 PRD 抽出的图片原文件
├── media-analysis.yaml         # 图片语义分析状态，默认需要 vision/人工确认
├── tables/                     # 单独抽出的表格 markdown
├── extraction-quality.yaml     # pass / warn / block 质量门禁
└── conversion-warnings.md      # 给人看的转换风险
```

准确性原则：

- 不承诺”100% 自动正确”，承诺”不静默丢信息”：图片、复杂表格、读取失败会变成显式 warning、question 或 block。
- 每个 requirement 必须能追到 PRD block/table/image、技术方案、源码或人工确认。
- 没有 OCR/vision/人工确认的截图、流程图、图片文字，只能作为待确认问题，不能作为高置信度结论。

LLM Vision 图片分析（可选增强）：

- 检测到 `ANTHROPIC_AUTH_TOKEN` 或 `OPENAI_API_KEY` 时自动启用。
- 一键安装脚本第 7 步会提示输入 `ANTHROPIC_AUTH_TOKEN`；也可以安装前或运行前手动设置：`export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx`。
- 支持 OpenAI 兼容端点（含智谱 bigmodel.cn 自动适配）。
- 对 PRD 中的流程图、设计稿、截图进行语义分析，产出结构化描述。

## 外部工具

PRD Tools 的部分能力依赖外部工具。安装脚本自动处理安装和配置，**所有工具都是可选的**——缺失时核心功能仍可用，只是降级到源码扫描。

| 工具 | 在 PRD Tools 中做什么 | 缺失影响 | 安装方式 |
|---|---|---|---|
| **[MarkItDown](https://github.com/microsoft/markitdown)** | PRD 文档转换：把 docx/pdf/pptx/xlsx/html/epub 转成可分析 markdown | 只能处理 `.md`/`.txt` 和粘贴文本 | `uv tool install "markitdown[all]"` |
| **[markitdown-ocr](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-ocr)** | PRD 图片 OCR：提取 PDF/DOCX 中嵌入图片的文字，扫描件全文 OCR | PRD 中图片文字无法提取 | `uv tool install markitdown-ocr` |
| **[GitNexus](https://github.com/abhigyanpatwari/GitNexus)** | 代码知识图谱：AST 解析代码结构，提取模块、符号、调用链、API consumer、执行流；支持语义搜索（需 `--embeddings`） | 回退到 `rg`/glob + Read 手动扫描 | npx/bunx，自动配置为 MCP Server |
| **[Graphify](https://github.com/safishamsi/graphify)** | 业务语义图谱：从代码和文档中提取业务概念聚类、设计原理、隐式关联和约束 | 手工阅读推断业务语义 | `uv tool install graphifyy`，自动注册为 Claude Code Skill |

### GitNexus

GitNexus 把代码仓库索引为知识图谱，通过 MCP Server 为 Claude Code 提供多个工具（query、context、impact、cypher 等）。安装脚本会：

1. 自动检测 npx 或 bunx 运行时
2. 注册 MCP Server 到 `~/.claude/.mcp.json`（Claude Code 重启后加载）
3. 对目标项目执行 `gitnexus analyze --embeddings`（优先启用语义搜索；HuggingFace 不可达时自动回退到 AST-only 模式）

日常更新索引：
```bash
# 完整更新（含语义搜索，需要下载 HuggingFace 模型）
gitnexus analyze . --embeddings

# 快速更新（仅 AST 结构，不需要网络）
gitnexus analyze .
```

### Graphify

Graphify 是 Claude Code Skill，提供 `/graphify` 命令。安装脚本会执行 `graphify update .` 提取代码结构（快速，无 LLM）。深度业务语义分析需要在 Claude Code 中运行：

```
/graphify . --mode deep
```

这会使用 LLM Vision 分析代码和文档中的业务概念、设计原理和隐式关联，生成 `graphify-out/` 目录下的图谱文件。

### MarkItDown

Microsoft 的文档转换工具，支持 50+ 格式。`prd-distill` 的 PRD Ingestion 阶段使用它把原始文档转成可审计的 markdown。支持：

- **正文提取**：docx/pdf/pptx/xlsx/html/epub → markdown
- **表格提取**：单独抽出表格，便于核验
- **图片提取**：保存原文件，配合 LLM Vision 分析语义
- **OCR 扩展**（`markitdown-ocr`）：PDF/DOCX 中嵌入图片的文字提取、扫描件全文 OCR

## 两个技能

> 各技能的详细使用说明见插件目录下的 README：[`plugins/reference/README.md`](plugins/reference/README.md) 和 [`plugins/prd-distill/README.md`](plugins/prd-distill/README.md)。

### reference

`reference` 用于构建或更新项目知识库。

它会读取当前项目源码、历史 PRD、技术方案、分支 diff 和已有输出，沉淀出 `_prd-tools/reference/`。这个目录是后续所有 PRD 蒸馏的上下文基础。

典型使用时机：

- 团队第一次接入 PRD Tools。
- 项目结构、活动类型、接口契约或开发模式发生较大变化。
- 完成一次真实 PRD 后，需要把新术语、新契约、踩坑经验回流到知识库。
- 需要检查 `_prd-tools/reference/` 是否过期、是否有幻觉、是否与源码矛盾。

支持模式：

| 模式 | 用途 |
|---|---|
| `F 上下文收集` | 收集历史 PRD、技术方案、分支 diff，形成 golden sample 候选 |
| `A 全量构建` | 首次构建项目知识库 |
| `B 增量更新` | 根据代码变化或新证据更新部分 reference |
| `B2 健康检查` | 检查 reference 是否完整、过期、缺证据或边界混乱 |
| `C 质量门控` | 检查 evidence、契约闭环、源码一致性和幻觉风险 |
| `E 反馈回流` | 读取 prd-distill 输出，把确认过的新知识回流到 `_prd-tools/reference/` |

### prd-distill

`prd-distill` 用于处理单个新 PRD。

它会读取 PRD、可选技术方案、当前源码和 `_prd-tools/reference/`，输出一组面向研发执行的文件：结论报告、开发/测试计划、待确认问题、以及机器可读证据链。

典型使用时机：

- 拿到一个新 PRD，需要评估影响范围。
- 需要给前端、BFF、后端拆任务和对齐接口。
- 需要在开发前明确哪些字段、枚举、schema、event、外部接口要确认。
- 需要生成 QA 测试矩阵和回归重点。

## 能力面适配器

PRD Tools 不把“前端/BFF/后端”写死成固定目录结构，而是通过能力面适配不同项目。

路径只是搜索候选，最终结论必须来自源码、配置、类型定义、注册表、调用链、测试或负向搜索证据。

前端常见能力面：

| 能力面 | 关注内容 |
|---|---|
| `ui_route` | 页面路由、菜单、权限入口 |
| `view_component` | 可见组件、弹窗、表格、详情块 |
| `form_or_schema` | 表单字段、动态 schema、组件元数据 |
| `state_flow` | store、hook、cache、跨组件数据流 |
| `client_contract` | 前端请求、响应、错误处理 |
| `content_i18n` | 文案、枚举 label、locale key |
| `client_validation` | disabled、互斥、上限、格式校验 |
| `preview_readonly` | 预览、详情、编辑、复制、只读回显 |

BFF 常见能力面：

| 能力面 | 关注内容 |
|---|---|
| `edge_api` | BFF endpoint、handler、serverless action |
| `schema_or_template` | 表单 schema、模板、组件配置 |
| `orchestration` | 多接口聚合、流程编排 |
| `transform_mapping` | 前端字段和后端字段转换 |
| `linkage_options` | 动态 options、字段联动 |
| `frontend_contract` | 前端消费的 schema/payload |
| `upstream_contract` | BFF 调用后端或外部服务的契约 |
| `batch_import_export` | 批量导入、模板下载、导出、解析错误 |

后端常见能力面：

| 能力面 | 关注内容 |
|---|---|
| `api_surface` | endpoint、RPC、DTO、枚举、错误码 |
| `application_service` | 用例服务、流程编排、事务边界 |
| `domain_model` | 聚合、策略、factory、领域对象、状态机 |
| `validation_policy` | 不变量、互斥、上限、阶段规则、权限 |
| `persistence_model` | DB、model、migration、缓存、存储格式 |
| `async_event` | job、queue、event、retry、幂等 |
| `external_integration` | 权益、券、支付、风控、消息等外部 API |
| `audit_observability` | 审批、审计、导出、日志、metric、alarm |
| `test_surface` | 单测、集成测试、fixture、回归入口 |

这样设计的原因是：不同项目目录结构可能完全不同，但研发协作中的能力面相对稳定。

## 产出文件

### 项目知识库：`_prd-tools/reference/`

`_prd-tools/reference/` 是项目长期知识，不是某次 PRD 的临时结论。它默认对当前仓库负责，不替代其他仓库的 reference，也不直接充当全平台 wiki。

推荐结构（v4.0，6 文件）：

```text
_prd-tools/reference/
├── 00-portal.md                # 人类导航 + 按场景阅读指南
├── project-profile.yaml        # 项目画像
├── 01-codebase.yaml            # 代码库静态清单（目录、枚举、模块、注册点）
├── 02-coding-rules.yaml        # 编码规则（规范+约束合并，severity 区分软硬）
├── 03-contracts.yaml           # 跨层和外部契约（字段级信息的唯一权威来源）
├── 04-routing-playbooks.yaml   # PRD 路由信号 + 场景打法 + QA 矩阵
└── 05-domain.yaml              # 业务领域知识（术语+背景+隐式规则+决策日志）
```

兼容读取旧版 v3.1（10 文件结构：`01-entities.yaml` ~ `09-playbooks.yaml`），自动映射到 v4.0。

核心文件说明：

| 文件 | 用途 | 不放什么 |
|---|---|---|
| `00-portal.md` | 人类导航、项目画像摘要、按场景阅读指南、健康状态 | 不维护大量事实 |
| `project-profile.yaml` | 项目画像：技术栈、入口、能力面、关键文件、测试命令 | 不写某个 PRD 的具体计划 |
| `01-codebase.yaml` | 静态清单：目录、枚举、模块、注册点、数据流、外部系统 | 不放字段级契约、不放编码规则、不放实现步骤 |
| `02-coding-rules.yaml` | 编码规则：规范、约束、红线、反模式、踩坑经验 | 不放契约字段、不放打法步骤 |
| `03-contracts.yaml` | 契约：endpoint、schema、event、字段级定义 | 不放编码规则、不放开发步骤、不放枚举值列表 |
| `04-routing-playbooks.yaml` | PRD 路由信号 + 场景打法 + QA 矩阵 + golden samples | 不放枚举值、不放字段级契约、不放编码规则 |
| `05-domain.yaml` | 业务领域：术语、背景、隐式规则、历史决策 | 不放代码路径、不放编码规则、不放契约字段 |

v4.0 核心原则：**每个事实只存在于一个文件（SSOT）**，其他文件通过 ID 引用。

单仓与跨仓边界：

- 当前仓源码、技术文档和 owner 确认过的内容，可以作为本仓 confirmed 事实。
- 其他仓的实现细节、字段 owner、上下游契约，如果没有对应 owner 确认，只能标记为 `needs_confirmation`。
- `project-profile.yaml` 记录当前仓的 `reference_scope` 和 `related_repositories`，用于说明本仓角色和协作边界。
- `03-contracts.yaml` 记录 producer/consumer、字段定义和跨仓确认状态，是字段级契约的唯一权威来源。
- `04-routing-playbooks.yaml` 记录 PRD 路由、场景打法和跨仓 handoff，不展开其他仓的内部实现步骤。
- 未来团队级知识库应聚合各仓 `_prd-tools/reference/` 和 `reference-update-suggestions.yaml` 中 confirmed 或 candidate 事实，而不是让单个仓库维护全平台知识。

### 构建过程产物：`_prd-tools/build/`

这些文件记录 reference 的运行过程和质量状态。

| 文件 | 用途 |
|---|---|
| `_prd-tools/build/context-enrichment.yaml` | 历史 PRD、技术方案、分支 diff、返工经验和 golden sample 候选 |
| `_prd-tools/build/modules-index.yaml` | 项目扫描快照，记录能力面、关键文件、入口和候选契约 |
| `_prd-tools/build/health-check.yaml` | 健康检查结果，说明 reference 是否完整、过期、缺证据 |
| `_prd-tools/build/quality-report.yaml` | 质量门控结果，检查证据、契约闭环、源码一致性和幻觉风险 |
| `_prd-tools/build/feedback-report.yaml` | 反馈回流审计记录，说明哪些建议被采纳或跳过 |

### PRD 蒸馏产物

单个 PRD 的输出目录：

```text
_prd-tools/distill/<slug>/
├── _ingest/
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
├── readiness-report.yaml
├── tasks/
├── spec/
│   ├── evidence.yaml
│   └── requirement-ir.yaml
└── context/
    ├── graph-context.md
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

快速阅读顺序：

| 顺序 | 文件 | 30 秒看什么 |
|---:|---|---|
| 1 | `_prd-tools/STATUS.md` 或 `_prd-tools/dashboard/index.html` | reference、图谱、最近一次 distill、下一步 |
| 2 | `report.md` | 需求摘要、影响范围、契约风险、阻塞项 |
| 3 | `plan.md` | 实现顺序、文件坐标、QA 矩阵、回滚 |
| 4 | `readiness-report.yaml` | status、score、decision、provider value |
| 5 | `context/contract-delta.yaml` | `blocked` / `needs_confirmation` |
| 6 | `_ingest/extraction-quality.yaml` | PRD 读取是 pass、warn 还是 block |

人类默认阅读：

| 文件 | 用途 | 读者 |
|---|---|---|
| `report.md` | 渐进式披露报告：需求摘要→变更明细表→字段清单→校验规则→开发Checklist→契约风险→阻塞问题与待确认项 | 负责人、PM、研发、QA |
| `plan.md` | 可执行的开发操作手册：精确到文件路径+行号，checklist格式，QA矩阵，回滚方案 | 研发、QA、技术负责人 |
| `readiness-report.yaml` | 本次 PRD 蒸馏的可用性评分、阻塞项、证据覆盖和 provider value | TL、工具维护者、CI |

PRD 读取和质量门禁：

| 文件 | 用途 | 边界 |
|---|---|---|
| `_ingest/source-manifest.yaml` | 记录原始文件、hash、格式和读取方式，回答”AI 读的是哪份 PRD” | 不写需求结论 |
| `_ingest/document.md` | 转换后的可读正文，作为拆 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `_ingest/document-structure.json` | 记录段落、表格、图片结构块和 locator，方便审计定位 | 不做业务判断 |
| `_ingest/evidence-map.yaml` | 给 PRD block/table/image 建证据 id，供 downstream evidence 引用 | 不放源码证据 |
| `_ingest/media/` | 保存从 PRD 抽出的图片、截图、流程图原文件 | 不改图、不推断图片含义 |
| `_ingest/media-analysis.yaml` | 记录图片是否已被 vision/OCR/人工确认 | 默认不产生高置信度结论 |
| `_ingest/tables/` | 保存抽出的表格 markdown，便于单独核验 | 不修复原表格 |
| `_ingest/extraction-quality.yaml` | 读取质量门禁，决定 pass、warn 或 block | 不写开发计划 |
| `_ingest/conversion-warnings.md` | 给人看的转换风险清单 | 不替代 `report.md` §11 |

机器和审计阅读：

| 文件 | 用途 | 边界 |
|---|---|---|
| `spec/evidence.yaml` | 证据台账，记录 PRD、技术方案、源码、负向搜索、人工确认 | 只放证据，不下结论 |
| `spec/requirement-ir.yaml` | 结构化需求 IR，记录业务意图、规则、验收条件、变更类型 | 不写文件级实现 |

上下文和评审阅读：

| 文件 | 用途 | 边界 |
|---|---|---|
| `context/graph-context.md` | GitNexus / Graphify / reference 的发现摘要和证据入口 | 不替代源码或 owner 确认 |
| `context/layer-impact.yaml` | 分层影响分析，按能力面记录当前状态、计划变化、风险和证据 | 不写字段级契约详情 |
| `context/contract-delta.yaml` | 契约差异，记录字段、producer、consumer、required、type、alignment_status | 不写开发顺序和 QA case |
| `context/reference-update-suggestions.yaml` | 知识回流建议，新术语、新契约、新 playbook、矛盾、golden sample 候选 | 只是建议，不自动改 reference |

常见误解：

| 误解 | 正确认知 |
|---|---|
| dashboard 和 STATUS.md 重复 | 它们同源，一个给浏览器，一个给文本环境 |
| YAML 很多，所以所有人都要读 | 普通评审只读 STATUS、report、plan |
| `warning` 表示失败 | `warning` 表示能继续，但风险必须显式处理 |
| reference 是最终事实 | reference 是加速器，最终以源码、PRD、技术方案、owner 确认为准 |
| 图谱结论可以直接当事实 | GitNexus / Graphify 是发现层，关键结论仍要 evidence 支撑 |

## 使用方式

### 安装

安装分三层，每层职责单一（详见 [ADR-0008](docs/adr/0008-安装脚本职责拆分.md)）：

| 层 | 谁负责 | 装什么 | 失败行为 |
|---|---|---|---|
| 1. `install.sh` | prd-tools 仓库 | reference / prd-distill skills、本地 `doctor.sh` / `status.sh` | 网络挂直接 exit 1，前面没装的东西不会被污染 |
| 2. `doctor.sh` | 用户按需运行 | 诊断 uv / MarkItDown / Graphify / GitNexus / API key，给可复制的 fix 命令 | 默认只报告；`--strict` 出错即退；`--fix` 交互式逐条修 |
| 3. skill 运行时自检 | `/reference` `/prd-distill` 自身 | 在使用某个工具的步骤前就近检查 | 缺什么就降级什么，并在 portal/report 里标明 |

#### 第一步：安装 skills

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/v2.0/install.sh | bash
```

指定目标项目：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/v2.0/install.sh | bash -s /path/to/project
```

完成后目标项目下生成：

```text
.claude/skills/          # reference / prd-distill skills
.prd-tools-version       # 版本标记
.prd-tools/doctor.sh     # 本地副本，可随时跑
.prd-tools/status.sh     # 生成 _prd-tools/STATUS.md 和 dashboard
```

`/reference` 由 `.claude/skills/reference/SKILL.md` 的 skill name 提供，不再额外安装 `.claude/commands/reference.md` alias，避免同一入口出现两套定义。

`install.sh` 不再修改 `~/.claude/.mcp.json`、不装 PyPI/npm 包、不写 shell profile。

#### 第二步：诊断外部依赖

```bash
bash .prd-tools/doctor.sh           # 仅报告
bash .prd-tools/doctor.sh --fix     # 交互式逐条修复
bash .prd-tools/doctor.sh --strict  # 任一项缺失即退出 1（CI 用）
```

doctor 会逐项检查：

| 项 | 用途 | 缺失影响 |
|---|---|---|
| uv | Python 工具运行时 | MarkItDown / Graphify 装不上 |
| markitdown | PRD 文档转换 | 无法读 .docx/.pdf/.pptx |
| graphify (`graphifyy`) | 业务语义图谱 | `/graphify . --mode deep` 不可用 |
| gitnexus runtime (npx/bunx) | 代码图谱 | reference 退化为 grep/glob 扫描 |
| `~/.claude/.mcp.json` 中的 gitnexus 声明 | MCP 接入 | Claude Code 启动时无 gitnexus 工具 |
| ANTHROPIC_AUTH_TOKEN / OPENAI_API_KEY | Vision OCR + Graphify deep | PRD 图片标 pending、deep 模式禁用 |

每一项都附带可复制的 fix 命令；`.mcp.json` 缺失时会打出可粘贴的 JSON 片段。

#### 第三步：查看项目状态

```bash
bash .prd-tools/status.sh
```

它会同时生成：

| 文件 | 用途 |
|---|---|
| `_prd-tools/STATUS.md` | 纯文本状态页，适合终端、PR、代码评审和长期留档 |
| `_prd-tools/dashboard/index.html` | 本地可视化页面，适合浏览器里快速扫 reference、图谱 provider 和最近一次 distill 状态 |

两者来自同一个脚本推导的数据：Markdown 是稳定文本入口，HTML 是可视化入口，不作为另一份事实来源。

#### 第四步：配置 Vision API key（可选但推荐）

```bash
export ANTHROPIC_AUTH_TOKEN=sk-ant-xxx
# OpenAI-compatible provider 可额外设置：
export ANTHROPIC_BASE_URL=https://your-provider.example/v1
# 也兼容 OPENAI_API_KEY / OPENAI_BASE_URL
```

#### 第五步：重启 Claude Code

新增或更新的 skills 需要重启 Claude Code 才会加载。

#### 三种典型路径

| 场景 | 推荐 |
|---|---|
| 标准网络 + 本机已装 Node + macOS | install.sh → `bash .prd-tools/doctor.sh --fix` 一遍过 |
| 内网/SOCKS 代理 | install.sh 走 curl 拉 tarball；外部依赖手动按 doctor 输出装（npm/uv 不走 SOCKS） |
| CI / 自动化 | install.sh + `bash .prd-tools/doctor.sh --strict`，缺啥就在 CI 里加哪一行 |

### Claude Code

构建项目知识库：

```text
/reference
```

蒸馏新 PRD：

```text
/prd-distill <PRD 文件路径或需求文本>
```

日常工作流就是：

```text
/reference
/prd-distill <PRD 文件路径或需求文本>
```

## 推荐落地路径

首次接入：

1. 在目标项目安装 PRD Tools。
2. 准备 1-3 个历史 PRD、技术方案和对应分支 diff。
3. 运行 `/reference` Mode F（上下文收集），然后 Mode A（全量构建），生成 `_prd-tools/reference/`。
4. 运行 Mode B2（健康检查）和 Mode C（质量门控）。
5. 用一个新 PRD 运行 `/prd-distill`，检查输出质量。

日常使用：

1. 新需求进来后运行 `prd-distill`。
2. 研发和 QA 先看 `report.md` 和 `plan.md`。
3. 对需要对齐的字段和 owner 查看 `context/contract-delta.yaml`。
4. 需求完成后，将有效知识通过 `/reference` Mode E（反馈回流）写回 `_prd-tools/reference/`。

## 质量原则

- 源码和技术文档是最终证据，reference 是加速器。
- 不确定就标低置信度，不让 AI 补脑。
- 多层需求必须显式处理契约。
- 业务关键规则不能只靠前端守。
- 每个输出都要能回溯 evidence。
- 每次真实需求结束后，把新增知识和踩坑回流到 reference。

## 版本机制

- 仓库根目录 `VERSION` 是工具版本，5 处版本号保持一致（lockstep versioning）。
- Claude 插件元数据里的 `version` 与 `VERSION` 保持一致。
- 安装脚本会在目标项目写 `.prd-tools-version`。
- schema 使用 `schema_version`，工具使用 `tool_version`；老版本输出可兼容读取。

### 自动发版

使用 Conventional Commits 规范提交后，post-commit hook 会自动触发发版：

| 提交前缀 | 版本变更 | 自动触发 |
|---|---|---|
| `feat:` | minor（如 2.10.3 → 2.11.0） | 是 |
| `fix:` | patch（如 2.10.3 → 2.10.4） | 是 |
| `feat!:` 或 footer `BREAKING CHANGE:` | major（如 2.10.3 → 3.0.0） | 是 |
| `docs:` / `chore:` / `refactor:` | 不触发 | 否 |

自动发版流程：更新 5 处版本号 → 生成 CHANGELOG → 提交 → 创建 tag。

临时禁用：`PRD_TOOLS_NO_AUTO_RELEASE=1 git commit -m "feat: ..."`
