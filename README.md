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

`prd-distill` 支持 `.md/.txt` 文件和粘贴文本。Claude 直接读取文件内容，创建可审计的 `_ingest/` 证据结构，再进入 Requirement IR 和分层影响分析。

```text
PRD 文件(.md/.txt) 或粘贴文本
        ↓
Claude 读取 → _ingest/ 证据结构
        ↓
Requirement IR：业务规则、验收条件、变更类型
        ↓
Layer Impact / Contract Delta / Plan
```

其他格式请先转为 markdown。

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
└── context/
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── readiness-report.yaml
    ├── graph-context.md
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

快速阅读顺序：

| 顺序 | 文件 | 30 秒看什么 |
|---:|---|---|
| 1 | `report.md` | 需求摘要、影响范围、契约风险、阻塞项 |
| 2 | `plan.md` | 实现顺序、文件坐标、QA 矩阵、回滚 |
| 3 | `context/readiness-report.yaml` | status、score、decision、provider value |
| 4 | `context/contract-delta.yaml` | `blocked` / `needs_confirmation` |
| 5 | `_ingest/extraction-quality.yaml` | PRD 读取是 pass、warn 还是 block |

人类默认阅读：

| 文件 | 用途 | 读者 |
|---|---|---|
| `report.md` | 渐进式披露报告：需求摘要→变更明细表→字段清单→校验规则→开发Checklist→契约风险→阻塞问题与待确认项 | 负责人、PM、研发、QA |
| `plan.md` | 可执行的开发操作手册：精确到文件路径+行号，checklist格式，QA矩阵，回滚方案 | 研发、QA、技术负责人 |
| `context/readiness-report.yaml` | 本次 PRD 蒸馏的可用性评分、阻塞项、证据覆盖和 provider value | TL、工具维护者、CI |

PRD 读取和质量门禁：

| 文件 | 用途 | 边界 |
|---|---|---|
| `_ingest/source-manifest.yaml` | 记录原始文件、hash、格式和读取方式，回答”AI 读的是哪份 PRD” | 不写需求结论 |
| `_ingest/document.md` | 转换后的可读正文，作为拆 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `_ingest/document-structure.json` | 记录段落、表格、图片结构块和 locator，方便审计定位 | 不做业务判断 |
| `_ingest/evidence-map.yaml` | 给 PRD block/table/image 建证据 id，供 downstream evidence 引用 | 不放源码证据 |
| `_ingest/media/` | 保存从 PRD 抽出的图片、截图、流程图原文件 | 不改图、不推断图片含义 |
| `_ingest/media-analysis.yaml` | 记录图片是否已被人工确认 | 默认不产生高置信度结论 |
| `_ingest/tables/` | 保存抽出的表格 markdown，便于单独核验 | 不修复原表格 |
| `_ingest/extraction-quality.yaml` | 读取质量门禁，决定 pass、warn 或 block | 不写开发计划 |
| `_ingest/conversion-warnings.md` | 给人看的转换风险清单 | 不替代 `report.md` §11 |

机器和审计阅读：

| 文件 | 用途 | 边界 |
|---|---|---|
| `context/evidence.yaml` | 证据台账，记录 PRD、技术方案、源码、负向搜索、人工确认 | 只放证据，不下结论 |
| `context/requirement-ir.yaml` | 结构化需求 IR，记录业务意图、规则、验收条件、变更类型 | 不写文件级实现 |

上下文和评审阅读：

| 文件 | 用途 | 边界 |
|---|---|---|
| `context/graph-context.md` | 源码扫描发现摘要和证据入口 | 不替代源码或 owner 确认 |
| `context/layer-impact.yaml` | 分层影响分析，按能力面记录当前状态、计划变化、风险和证据 | 不写字段级契约详情 |
| `context/contract-delta.yaml` | 契约差异，记录字段、producer、consumer、required、type、alignment_status | 不写开发顺序和 QA case |
| `context/reference-update-suggestions.yaml` | 知识回流建议，新术语、新契约、新 playbook、矛盾、golden sample 候选 | 只是建议，不自动改 reference |

常见误解：

| 误解 | 正确认知 |
|---|---|
| YAML 很多，所以所有人都要读 | 普通评审只读 report、plan |
| `warning` 表示失败 | `warning` 表示能继续，但风险必须显式处理 |
| reference 是最终事实 | reference 是加速器，最终以源码、PRD、技术方案、owner 确认为准 |

## 使用方式

### 安装

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
```

安装完成后重启 Claude Code，新 skills 才会加载。

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
