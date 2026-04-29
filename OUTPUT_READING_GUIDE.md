# PRD Tools 产出阅读指南

这份文档面向第一次使用 PRD Tools 的同学，解释一次完整运行后会看到哪些目录和文件、每个文件解决什么问题、应该按什么顺序阅读，以及这些产物如何进入真实研发流程。

## 一句话理解

PRD Tools 的产出分三类：

| 类型 | 目录 | 作用 |
|---|---|---|
| 项目长期知识 | `_reference/` | 让 AI 了解当前项目：项目结构、业务术语、契约、开发套路 |
| 单次需求分析 | `_output/prd-distill/<slug>/` | 把一个 PRD 转成结论、计划、问题和证据链 |
| 构建和质量过程 | `_output/*.yaml` | 记录知识库构建、健康检查、质量门控和回流结果 |

可以把它理解为：

```text
_reference/ 负责长期记忆
_output/prd-distill/<slug>/ 负责本次需求
_output/*.yaml 负责过程审计
```

## 推荐阅读顺序

第一次看产物时，不要从 YAML 开始读。建议按下面顺序：

| 顺序 | 文件 | 你要看什么 |
|---|---|---|
| 1 | `_output/prd-distill/<slug>/report.md` | 先看这次需求是什么、影响哪些层、最大风险是什么 |
| 2 | `_output/prd-distill/<slug>/questions.md` | 看哪些问题必须找 owner 确认，哪些会阻塞开发 |
| 3 | `_output/prd-distill/<slug>/plan.md` | 看开发顺序、QA 矩阵、契约对齐任务 |
| 4 | `_output/prd-distill/<slug>/prd-ingest/extraction-quality.yaml` | 看 PRD 是否读取完整，有没有图片/表格/解析风险 |
| 5 | `_output/prd-distill/<slug>/artifacts/contract-delta.yaml` | 多团队协作时看接口、字段、枚举、外部系统是否对齐 |
| 6 | `_output/prd-distill/<slug>/artifacts/evidence.yaml` | 对结论有疑问时查证据来源 |
| 7 | `_output/prd-distill/<slug>/artifacts/reference-update-suggestions.yaml` | 需求结束后看哪些知识值得回流到 `_reference/` |

日常使用时，大多数人只需要先读前三个文件：`report.md`、`questions.md`、`plan.md`。

## 单次 PRD 产出目录

运行 `prd-distill` 后，会生成：

```text
_output/prd-distill/<slug>/
├── report.md
├── plan.md
├── questions.md
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
└── artifacts/
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

### report.md

`report.md` 是给人看的结论报告，适合负责人、研发、QA、PM 快速阅读。

它回答：

- 这个 PRD 一句话是什么。
- 影响前端、BFF、后端还是外部系统。
- 最关键的开发结论是什么。
- 最大的风险和阻塞点是什么。
- 后续应该重点读哪些文件。

边界：

- 它不是完整开发方案。
- 它不展开所有证据。
- 它只保留足够做第一轮判断的信息。

怎么用：

- 评审前先看它，快速决定本次需求复杂度。
- 如果报告里出现 `needs_confirmation` 或 `blocked`，不要直接开工，先读 `questions.md`。

### questions.md

`questions.md` 是阻塞问题和 owner 确认清单。

它回答：

- 哪些信息 PRD 没说清楚。
- 哪些接口、字段、外部系统需要确认。
- 每个问题影响哪些需求、计划或契约。
- 建议找谁确认。
- 如果暂时确认不了，默认策略是什么。

边界：

- 普通备注不放这里。
- 已经确认的事实不放这里。
- 只有会影响开发、测试、契约对齐或上线风险的问题才放这里。

怎么用：

- TL 可以用它拉 PM、前端、BFF、后端、外部 owner 对齐。
- QA 可以用它识别哪些测试场景暂时不能定稿。
- 确认后，应该把结论补回开发计划或回流到 reference。

### plan.md

`plan.md` 是合并后的开发、测试、契约对齐计划。

它回答：

- 建议按什么顺序开发。
- 每个阶段改哪些能力面或文件。
- 哪些任务依赖 owner 确认。
- QA 应该测哪些场景。
- 哪些契约需要前端、BFF、后端或外部系统对齐。

边界：

- 它不直接改代码。
- 它不替代详细技术方案。
- 它是开发前的执行地图。

怎么用：

- 研发用它拆任务。
- QA 用它写测试用例。
- TL 用它检查是否遗漏批量、审核、回滚、外部接口、异步任务等高风险链路。

## PRD 读取产物：prd-ingest/

`prd-ingest/` 解决一个非常关键的问题：AI 到底把 PRD 读成了什么。

它不是需求分析结果，而是 PRD 原文读取和质量门禁层。

### source-manifest.yaml

记录原始 PRD 文件信息。

它回答：

- AI 读的是哪个文件。
- 文件格式是什么。
- 文件大小和 hash 是什么。
- 用什么方式读取。

为什么需要：

- 防止大家拿不同版本 PRD 讨论。
- 方便复盘时确认当时分析的输入。

### document.md

PRD 转换后的可读 Markdown。

它回答：

- docx、txt、md 或 pdf 最终被转换成了什么文本。
- 后续 Requirement IR 是基于哪些内容拆出来的。

为什么需要：

- 让人能快速检查 PRD 转换是否漏段落。
- 让 AI 后续分析有稳定输入，而不是直接猜 docx。

### document-structure.json

PRD 的结构化块信息。

它记录：

- 段落。
- 标题。
- 表格。
- 图片。
- block id。
- locator。

为什么需要：

- 后续 evidence 可以定位到具体 PRD block。
- 如果某个需求结论有争议，可以追溯到 PRD 的具体位置。

### evidence-map.yaml

PRD 块级证据地图。

它回答：

- 每个 PRD 段落、表格、图片对应哪个证据 id。
- 哪些内容置信度高，哪些内容需要人工确认。

边界：

- 它只记录 PRD 证据。
- 源码证据、reference 证据、负向搜索证据放在 `artifacts/evidence.yaml`。

### media/

从 PRD 中抽出的图片、截图、流程图原文件。

为什么需要：

- 很多 PRD 的关键信息藏在截图或流程图里。
- 工具必须把图片暴露出来，不能假装已经理解。

注意：

- 抽出图片不等于理解图片。
- 没有 vision/OCR/人工确认时，图片内容不能作为高置信度结论。

### media-analysis.yaml

图片语义分析状态。

默认情况下，它会标记为：

```yaml
analysis_status: "needs_vision_or_human_review"
confidence: "low"
```

为什么需要：

- 明确告诉用户：这里有图片，但当前没有确认图片语义。
- 如果图片里包含关键规则，应该进入 `questions.md`。

### tables/

从 PRD 中单独抽出的表格 Markdown。

为什么需要：

- PRD 表格通常包含字段、枚举、校验、批量规则。
- 单独抽出后，研发和 QA 可以更容易核对。

注意：

- 如果原表格有合并单元格，可能会出现读取风险。
- 风险会记录在 `extraction-quality.yaml` 和 `conversion-warnings.md`。

### extraction-quality.yaml

PRD 读取质量门禁。

核心字段：

| 字段 | 含义 |
|---|---|
| `status: pass` | PRD 读取质量正常，可以继续分析 |
| `status: warn` | 可以继续，但存在图片、复杂表格、PDF 顺序等风险 |
| `status: block` | 读取失败或缺少关键文本，应暂停并补充输入 |

常见 warning：

- 图片未做 vision/OCR。
- 表格存在合并单元格。
- PDF 阅读顺序可能不可靠。
- 文档中没有可读文本。

怎么用：

- `pass`：继续看 `report.md`。
- `warn`：继续看，但要确认 `report.md` 或 `questions.md` 是否暴露了这些风险。
- `block`：不要使用后续结论，先补 markdown/text 或人工确认。

### conversion-warnings.md

给人看的转换风险摘要。

它比 `extraction-quality.yaml` 更容易读，适合在评审时快速说明：

- 这次 PRD 哪些部分可能没读准。
- 哪些图片或表格需要人工复核。

## 机器和审计产物：artifacts/

`artifacts/` 是给 AI、审计、复盘和知识回流使用的结构化中间产物。

普通用户不需要每次都读，但当你要判断“AI 为什么这么说”时，就应该看这里。

### evidence.yaml

证据台账。

它回答：

- 每个结论来自 PRD、技术方案、源码、reference、git diff、负向搜索还是人工确认。
- 证据位置在哪里。
- 证据置信度如何。

证据类型：

| 类型 | 含义 |
|---|---|
| `prd` | 来自 PRD |
| `tech_doc` | 来自技术方案或接口文档 |
| `code` | 来自源码 |
| `reference` | 来自 `_reference/` |
| `negative_code_search` | 搜过但没找到，也是一种证据 |
| `human` | 用户或 owner 明确确认 |

怎么用：

- 对某个结论不信时，先查 evidence id。
- 发现 evidence 只有 reference、没有 code 时，要谨慎。
- 发现 evidence 是 negative search 时，说明工具确认过“当前代码没有”。

### requirement-ir.yaml

结构化需求 IR。

IR 是 Intermediate Representation，也就是把 PRD 从自然语言拆成稳定的需求单元。

它回答：

- 每个需求点是什么。
- 是新增、修改、删除还是不变。
- 业务实体是什么。
- 规则和验收条件是什么。
- 影响哪些层。
- 证据是什么。

边界：

- IR 描述业务意图和验收规则。
- 不写具体文件实现细节。
- 文件和模块影响放在 `layer-impact.yaml`。

怎么用：

- QA 可以按 REQ 写测试用例。
- 研发可以按 REQ 对照实现是否漏需求。
- PM 可以核对 PRD 是否被拆错。

### layer-impact.yaml

分层影响分析。

它回答：

- 每个 requirement 影响前端、BFF、后端还是外部系统。
- 命中哪个能力面。
- 当前代码状态是什么。
- 计划变化是什么。
- 风险和依赖是什么。

能力面示例：

| 层 | 能力面示例 |
|---|---|
| frontend | `ui_route`、`view_component`、`form_or_schema`、`client_contract` |
| bff | `edge_api`、`schema_or_template`、`transform_mapping`、`upstream_contract` |
| backend | `api_surface`、`domain_model`、`validation_policy`、`external_integration` |

为什么不用固定路径：

- 不同项目目录结构可能完全不同。
- 但能力面相对稳定。
- 工具先按能力面判断，再用源码证据落到具体文件。

怎么用：

- TL 用它检查是否漏层。
- 后端只看 backend impacts。
- 前端/BFF 可以快速判断是否真的需要自己改。

### contract-delta.yaml

契约差异。

它回答：

- 本次需求新增或修改了哪些跨层/外部契约。
- producer 是谁。
- consumer 是谁。
- request/response/event/payload 字段怎么变。
- 当前是否对齐。

核心状态：

| 状态 | 含义 |
|---|---|
| `aligned` | producer 和 consumer 都有证据，基本对齐 |
| `needs_confirmation` | PRD 有描述，但某层或 owner 未确认 |
| `blocked` | 字段、枚举、required、时序或责任归属冲突 |
| `not_applicable` | 单层内部变化，不涉及契约 |

怎么用：

- 跨前端/BFF/后端需求必须看这个文件。
- 涉及外部系统、券、权益、支付、预算、审计、异步事件时也必须看。
- `needs_confirmation` 和 `blocked` 应同步进入 `questions.md`。

### reference-update-suggestions.yaml

知识回流建议。

它回答：

- 本次需求发现了哪些 `_reference/` 没有的新知识。
- 哪些术语、契约、路由、playbook 应该补充。
- 哪些事实和现有 reference 矛盾。
- 本次需求是否适合作为 golden sample。

边界：

- 它只是建议。
- 不会自动修改 `_reference/`。
- 需要通过 `build-reference` 的 `E 反馈回流` 或人工确认后再写回。

怎么用：

- 需求结束后，TL 或工具维护者看这个文件。
- 确认过的新知识回流到 `_reference/`，下一次 PRD 分析会更准。

## 项目知识库：_reference/

`_reference/` 是项目长期知识库。它不是某次 PRD 的输出，而是后续每次 PRD 分析的上下文基础。

推荐结构：

```text
_reference/
├── 00-index.md
├── project-profile.yaml
├── 01-entities.yaml
├── 02-architecture.yaml
├── 03-conventions.yaml
├── 04-constraints.yaml
├── 05-routing.yaml
├── 06-glossary.yaml
├── 07-business-context.yaml
├── 08-contracts.yaml
└── 09-playbooks.yaml
```

### 00-index.md

导航入口。

它回答：

- 这个 reference 当前是什么版本。
- 哪些文件最重要。
- 当前健康状态如何。
- 新用户应该先看哪里。

### project-profile.yaml

项目画像。

记录：

- 技术栈。
- 项目类型。
- 构建/测试命令。
- 关键入口。
- 部署形态。
- 主要能力面。

它帮助 AI 快速知道“这是一个什么项目”。

### 01-entities.yaml

静态实体库。

记录：

- 枚举。
- 字段。
- DTO。
- endpoint。
- 组件。
- 领域对象。
- DB model。

边界：

- 只放已经存在的事实。
- 不写开发步骤。

### 02-architecture.yaml

架构和运行流。

记录：

- 模块职责。
- 数据流。
- 注册点。
- 调用链。
- 依赖枢纽。
- 高风险区域。

边界：

- 不写字段级契约详情。
- 字段契约放 `08-contracts.yaml`。

### 03-conventions.yaml

工程惯例库。

它回答：这个项目里代码通常怎么写。

适合放：

- 命名习惯。
- 注册模式。
- 转换模式。
- 错误处理习惯。
- 推荐写法。
- 代码层面的反模式。

不适合放：

- 跨层字段契约。
- 业务红线。
- 某类需求完整打法。

判断标准：

```text
如果它是在说“顺着项目习惯应该怎么写”，放 03。
```

### 04-constraints.yaml

约束与护栏库。

它回答：什么事情不能错、不能生成、必须拦截。

适合放：

- 枚举白名单。
- 字段必填规则。
- 金额范围。
- 业务校验红线。
- 生成边界。
- 必须执行的质量门禁规则。

不适合放：

- 普通代码风格。
- 推荐写法。
- 历史经验故事。

判断标准：

```text
如果它是在说“越过这条线就会出错或有线上风险”，放 04。
```

### 05-routing.yaml

PRD 信号路由。

它回答：

- PRD 里出现某些关键词或结构时，应该路由到哪些需求类型。
- 可能影响哪些层。
- 应该优先检查哪些能力面。

例如：

- “新增活动类型”可能路由到 CampaignType、factory、schema、business object。
- “批量配置”可能路由到 batch import/export。
- “券/权益/奖励”可能路由到外部系统契约。

### 06-glossary.yaml

业务术语表。

记录：

- 业务词。
- 同义词。
- 英文名。
- 代码字段名。
- 枚举 label。

它解决 PRD 语言和代码语言不一致的问题。

### 07-business-context.yaml

业务背景和隐式规则。

记录：

- 历史决策。
- 隐式业务规则。
- 已知歧义。
- owner 约定。
- 背景知识。

边界：

- 不写代码实现细节。
- 不写完整 playbook。

### 08-contracts.yaml

跨层和外部契约库。

记录：

- producer。
- consumer。
- 字段。
- required。
- 类型。
- 兼容性。
- owner。
- alignment_status。

它回答：

```text
系统边界承诺了什么。
```

### 09-playbooks.yaml

高频需求打法。

记录：

- 某类需求通常怎么推进。
- 先看哪些文件。
- 常见坑。
- QA 矩阵。
- golden sample。

它回答：

```text
遇到某类需求应该怎么推进。
```

## 构建过程产物

这些文件通常在 `_output/` 根目录。

### context-enrichment.yaml

上下文收集结果。

记录：

- 历史 PRD。
- 技术方案。
- 分支 diff。
- golden sample 候选。
- 历史返工经验。

它用于首次建设 `_reference/` 前，让工具先理解真实业务样例。

### modules-index.yaml

项目扫描快照。

记录：

- 模块。
- 能力面。
- 关键文件。
- 入口。
- 候选契约。

它是 build-reference 对项目结构的中间理解。

### reference-health.yaml

知识库健康检查。

回答：

- `_reference/` 是否完整。
- 是否过期。
- 是否缺证据。
- 文件边界是否混乱。
- 有没有 low confidence 项。

### reference-quality-report.yaml

质量门控结果。

检查：

- 证据是否充分。
- 契约是否闭环。
- 源码和 reference 是否一致。
- 是否存在幻觉风险。
- 是否有必须修复的问题。

### feedback-ingest-report.yaml

反馈回流审计。

记录：

- 哪些 `reference-update-suggestions` 被采纳。
- 哪些被跳过。
- 为什么跳过。
- 更新了哪些 reference 文件。

## 不同角色怎么读

### 研发

先读：

1. `report.md`
2. `plan.md`
3. `artifacts/layer-impact.yaml`
4. `artifacts/evidence.yaml`

重点关注：

- 建议实现顺序。
- 目标文件/模块。
- 当前代码状态。
- 哪些结论有源码证据。
- 哪些任务依赖 owner 确认。

### QA

先读：

1. `report.md`
2. `plan.md`
3. `artifacts/requirement-ir.yaml`
4. `questions.md`

重点关注：

- 每个 REQ 的验收条件。
- QA 矩阵。
- 边界值。
- 回归范围。
- 还没确认的测试前提。

### TL / 技术负责人

先读：

1. `report.md`
2. `questions.md`
3. `artifacts/contract-delta.yaml`
4. `plan.md`
5. `artifacts/reference-update-suggestions.yaml`

重点关注：

- 是否漏层。
- 是否漏外部系统。
- 是否有跨团队契约未对齐。
- 风险是否能接受。
- 哪些知识应该沉淀。

### PM / 业务 owner

先读：

1. `report.md`
2. `questions.md`
3. `plan.md` 中 QA 矩阵部分

重点关注：

- PRD 是否被理解正确。
- 哪些规则或默认策略需要确认。
- 验收标准是否覆盖业务目标。

### 工具维护者

先读：

1. `prd-ingest/extraction-quality.yaml`
2. `artifacts/evidence.yaml`
3. `artifacts/reference-update-suggestions.yaml`
4. `_output/reference-quality-report.yaml`

重点关注：

- 文档读取质量。
- 证据链是否足够。
- reference 是否需要更新。
- 工具版本是否产生稳定收益。

## 状态判断速查

### extraction-quality.status

| 状态 | 处理方式 |
|---|---|
| `pass` | 可以正常使用后续分析 |
| `warn` | 可以继续，但必须确认 warning 是否已进入报告或问题清单 |
| `block` | 暂停使用结论，先补充 PRD 文本、OCR 或人工确认 |

### confidence

| 值 | 含义 |
|---|---|
| `high` | 有较强证据，通常来自 PRD + 源码或明确文档 |
| `medium` | 有依据，但仍有部分实现、owner 或上下游未确认 |
| `low` | 只能作为假设或待确认问题，不应直接开发 |

### alignment_status

| 值 | 处理方式 |
|---|---|
| `aligned` | 可以按计划推进 |
| `needs_confirmation` | 先找 owner 确认，再进入开发或联调 |
| `blocked` | 不建议继续开发，必须解决冲突 |
| `not_applicable` | 单层内部变化，不涉及跨层契约 |

## 一次完整使用流程

### 首次接入项目

1. 安装 PRD Tools。
2. 收集 1-3 个历史 PRD、技术方案、分支 diff。
3. 运行 `build-reference` 的 `F 上下文收集`。
4. 运行 `A 全量构建` 生成 `_reference/`。
5. 运行 `B2 健康检查`。
6. 运行 `C 质量门控`。
7. 用一个真实新 PRD 运行 `prd-distill`。

### 日常新需求

1. 运行 `prd-distill`。
2. 先读 `report.md`。
3. 再读 `questions.md`，拉 owner 确认。
4. 读 `plan.md` 拆开发和 QA。
5. 多层需求检查 `contract-delta.yaml`。
6. 对结论有疑问时查 `evidence.yaml`。
7. 需求结束后看 `reference-update-suggestions.yaml`。
8. 通过 `build-reference` 的 `E 反馈回流` 更新 `_reference/`。

## 如何判断这次产出是否可靠

可以用下面清单快速判断：

| 检查项 | 可靠表现 | 风险表现 |
|---|---|---|
| PRD 读取 | `extraction-quality` 为 pass 或 warn 且 warning 已暴露 | block，或图片/表格风险未进入问题清单 |
| 需求拆解 | REQ 覆盖核心业务规则和验收条件 | 只总结背景，没有拆规则 |
| 代码证据 | 关键 impact 有 code evidence 或 negative search | 只引用 reference |
| 契约 | 多层/外部系统有 contract delta | 接口字段只在计划里口头提到 |
| 问题清单 | 阻塞项有 owner 和影响范围 | 问题泛泛而谈 |
| QA | 测试项能追到 REQ 或 contract | 只有笼统“回归测试” |
| 回流 | 有可采纳的 reference 更新建议 | 没有沉淀价值 |

## 常见误解

### 看到很多 YAML，是不是太复杂？

默认不需要每个人都读 YAML。YAML 是给 AI、审计、回流和高级排查用的。普通协作优先读 `report.md`、`questions.md`、`plan.md`。

### `warn` 是失败吗？

不是。`warn` 表示可以继续，但存在读取或证据风险。比如 PRD 有图片未做 OCR、表格有合并单元格。这些风险必须出现在 `report.md` 或 `questions.md` 中。

### `reference` 是最终事实吗？

不是。`_reference/` 是加速器，不是最终权威。最终权威优先级通常是：

```text
源码 / PRD / 技术方案 / 接口文档 / owner 确认 > reference
```

### 为什么有些前端/BFF/后端层是空的？

因为工具按能力面判断影响范围，不会为了凑格式硬写空任务。当前仓库如果只包含后端代码，前端/BFF 通常只会出现在契约确认里，而不是具体实现计划里。

### 什么时候必须看 artifacts？

以下情况必须看：

- 结论有争议。
- 需求影响多层。
- 涉及接口、schema、event、payload、DB 字段。
- 涉及权益、券、奖励、支付、预算、审计、异步任务、外部系统。
- 要把本次需求沉淀为 reference。

## 最小会议用法

如果只有 15 分钟评审，可以这样用：

1. 用 `report.md` 讲 3 分钟：需求、影响层、关键结论。
2. 用 `questions.md` 讲 5 分钟：阻塞问题和 owner。
3. 用 `contract-delta.yaml` 讲 4 分钟：跨层字段和外部系统。
4. 用 `plan.md` 讲 3 分钟：开发顺序和 QA 重点。

会议结束时应该得到：

- 哪些问题谁来确认。
- 哪些任务可以先开工。
- 哪些契约需要同步前端/BFF/后端/外部团队。
- 哪些测试场景必须覆盖。

## 产出质量的目标

PRD Tools 不是追求“AI 看完 PRD 后给一篇漂亮总结”，而是追求：

- 需求拆得清。
- 影响面找得准。
- 证据能追溯。
- 风险能提前暴露。
- 契约能对齐。
- 测试能落地。
- 知识能回流。

最终目标是降低返工、减少跨团队误解，让每次 PRD 分析都能沉淀成下一次更准确的项目知识。
