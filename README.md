# PRD Tools

PRD Tools 是一套面向业务研发团队的 AI 工程工作流，把 PRD 从“自然语言需求”转成“有证据、可执行、可测试、可回流”的开发计划。

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
build-reference
        ↓
项目知识库 _reference/
        ↓
prd-distill
        ↓
report / plan / questions / artifacts
        ↓
反馈回流到 _reference/
```

这套工作流的核心判断是：PRD-to-code 的难点通常不在“写几行代码”，而在以下问题：

- PRD 里的业务词和代码里的字段、枚举、模块名称不一致。
- 前端、BFF、后端对同一个字段的 owner 和 required 认知不一致。
- AI 容易只看当前仓库，忽略上下游契约和外部系统。
- 同类需求反复返工，但历史经验没有被沉淀。
- 测试计划和开发计划脱节，导致提测后才发现规则缺口。

PRD Tools 用 `_reference/` 做长期记忆，用 `_output/` 做单次需求分析，用 evidence 机制保证结论可追溯。

## 两个技能

### build-reference

`build-reference` 用于构建或更新项目知识库。

它会读取当前项目源码、历史 PRD、技术方案、分支 diff 和已有输出，沉淀出 `_reference/`。这个目录是后续所有 PRD 蒸馏的上下文基础。

典型使用时机：

- 团队第一次接入 PRD Tools。
- 项目结构、活动类型、接口契约或开发模式发生较大变化。
- 完成一次真实 PRD 后，需要把新术语、新契约、踩坑经验回流到知识库。
- 需要检查 `_reference/` 是否过期、是否有幻觉、是否与源码矛盾。

支持模式：

| 模式 | 用途 |
|---|---|
| `F 上下文收集` | 收集历史 PRD、技术方案、分支 diff，形成 golden sample 候选 |
| `A 全量构建` | 首次构建项目知识库 |
| `B 增量更新` | 根据代码变化或新证据更新部分 reference |
| `B2 健康检查` | 检查 reference 是否完整、过期、缺证据或边界混乱 |
| `C 质量门控` | 检查 evidence、契约闭环、源码一致性和幻觉风险 |
| `E 反馈回流` | 读取 prd-distill 输出，把确认过的新知识回流到 `_reference/` |

### prd-distill

`prd-distill` 用于处理单个新 PRD。

它会读取 PRD、可选技术方案、当前源码和 `_reference/`，输出一组面向研发执行的文件：结论报告、开发/测试计划、待确认问题、以及机器可读证据链。

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

### 项目知识库：`_reference/`

`_reference/` 是项目长期知识，不是某次 PRD 的临时结论。

推荐结构：

```text
_reference/
├── 00-index.md 或 README.md
├── project-profile.yaml
├── contracts.yaml 或 08-contracts.yaml
├── playbooks.yaml 或 09-playbooks.yaml
└── 01~09 兼容细节文件
```

核心文件说明：

| 文件 | 用途 | 边界 |
|---|---|---|
| `00-index.md` / `README.md` | 人类导航、版本信息、关键入口、健康状态 | 只做导航，不维护大量事实 |
| `project-profile.yaml` | 项目画像：技术栈、入口、能力面、关键文件、测试命令 | 不写某个 PRD 的具体计划 |
| `01-entities.yaml` | 已存在的静态事实：枚举、字段、组件、DTO、领域对象、endpoint | 不写流程和开发步骤 |
| `02-architecture.yaml` | 结构和运行流：模块职责、数据流、注册点、依赖枢纽、高风险区域 | 不写字段契约详情 |
| `03-conventions.yaml` | 代码写法：命名、注册模式、转换模式、反模式 | 不放跨层字段契约或需求 playbook |
| `04-constraints.yaml` | 硬约束：白名单、校验红线、生成边界、质量门控 | 不放普通代码风格 |
| `05-routing.yaml` | PRD 信号如何路由到需求 IR、目标层和能力面 | 不写完整实现方案 |
| `06-glossary.yaml` | 业务术语、同义词、枚举 label、字段/组件映射 | 不写完整业务规则 |
| `07-business-context.yaml` | 业务背景、隐式规则、历史决策、已知歧义 | 不写代码实现细节 |
| `08-contracts.yaml` / `contracts.yaml` | 跨层和外部契约：producer、consumer、字段、兼容性、owner、alignment_status | 不写开发步骤 |
| `09-playbooks.yaml` / `playbooks.yaml` | 高频需求打法、QA 矩阵、常见坑、golden sample | 不重复字段级契约 |

重点边界：

```text
03-conventions：代码通常怎么写
08-contracts：系统边界承诺了什么
09-playbooks：遇到某类需求怎么推进
```

### 构建过程产物：`_output/`

这些文件记录 build-reference 的运行过程和质量状态。

| 文件 | 用途 |
|---|---|
| `_output/context-enrichment.yaml` | 历史 PRD、技术方案、分支 diff、返工经验和 golden sample 候选 |
| `_output/modules-index.yaml` | 项目扫描快照，记录能力面、关键文件、入口和候选契约 |
| `_output/reference-health.yaml` | 健康检查结果，说明 reference 是否完整、过期、缺证据 |
| `_output/reference-quality-report.yaml` | 质量门控结果，检查证据、契约闭环、源码一致性和幻觉风险 |
| `_output/feedback-ingest-report.yaml` | 反馈回流审计记录，说明哪些建议被采纳或跳过 |

### PRD 蒸馏产物

单个 PRD 的输出目录：

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

人类默认阅读：

| 文件 | 用途 | 读者 |
|---|---|---|
| `report.md` | 一屏可读的结论报告：需求摘要、影响范围、关键风险、阻塞问题 | 负责人、PM、研发、QA |
| `plan.md` | 合并后的开发、测试、契约对齐计划 | 研发、QA、技术负责人 |
| `questions.md` | 阻塞问题、owner 确认项、低置信度假设 | PM、前端、BFF、后端、QA、外部 owner |

机器和审计阅读：

| 文件 | 用途 | 边界 |
|---|---|---|
| `artifacts/evidence.yaml` | 证据台账，记录 PRD、技术方案、源码、负向搜索、人工确认 | 只放证据，不下结论 |
| `artifacts/requirement-ir.yaml` | 结构化需求 IR，记录业务意图、规则、验收条件、变更类型 | 不写文件级实现 |
| `artifacts/layer-impact.yaml` | 分层影响分析，按能力面记录当前状态、计划变化、风险和证据 | 不写字段级契约详情 |
| `artifacts/contract-delta.yaml` | 契约差异，记录字段、producer、consumer、required、type、alignment_status | 不写开发顺序和 QA case |
| `artifacts/reference-update-suggestions.yaml` | 知识回流建议，新术语、新契约、新 playbook、矛盾、golden sample 候选 | 只是建议，不自动改 reference |

## 使用方式

### 安装

默认同时安装 Claude Code 和 Codex 所需的 skill：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash
```

指定目标项目：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash -s /path/to/project
```

默认安装位置：

```text
.claude/skills/   # Claude Code
.agents/skills/   # Codex
```

安装后目标项目会生成：

```text
.prd-tools-version
```

用于确认当前安装版本和来源。

### Claude Code

构建项目知识库：

```text
/build-reference
```

蒸馏新 PRD：

```text
/prd-distill
```

### Codex

Codex 不使用 `/prd-distill` 这类 slash command，推荐用自然语言显式触发 skill。

构建项目知识库：

```text
使用 build-reference skill，为当前项目执行上下文收集、全量构建、健康检查和质量门控。
```

蒸馏新 PRD：

```text
使用 prd-distill skill，基于当前项目 _reference/ 和 PRD /path/to/prd.docx 生成 report.md、plan.md、questions.md 和 artifacts 证据链。
```

## 推荐落地路径

首次接入：

1. 在目标项目安装 PRD Tools。
2. 准备 1-3 个历史 PRD、技术方案和对应分支 diff。
3. 运行 `build-reference` 的 `F 上下文收集`。
4. 运行 `A 全量构建`，生成 `_reference/`。
5. 运行 `B2 健康检查` 和 `C 质量门控`。
6. 用一个新 PRD 运行 `prd-distill`，检查输出质量。

日常使用：

1. 新需求进来后运行 `prd-distill`。
2. 研发和 QA 先看 `report.md`、`plan.md`、`questions.md`。
3. 对需要对齐的字段和 owner 查看 `artifacts/contract-delta.yaml`。
4. 需求完成后，将有效知识通过 `build-reference` 的 `E 反馈回流` 写回 `_reference/`。

## 质量原则

- 源码和技术文档是最终证据，reference 是加速器。
- 不确定就标低置信度，不让 AI 补脑。
- 多层需求必须显式处理契约。
- 业务关键规则不能只靠前端守。
- 每个输出都要能回溯 evidence。
- 每次真实需求结束后，把新增知识和踩坑回流到 reference。

## 版本机制

- 仓库根目录 `VERSION` 是工具版本。
- Claude 插件元数据里的 `version` 与 `VERSION` 保持一致。
- 安装脚本会在目标项目写 `.prd-tools-version`。
- schema 使用 `schema_version`，工具使用 `tool_version`；老版本输出可兼容读取。
