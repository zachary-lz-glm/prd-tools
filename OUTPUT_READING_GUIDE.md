# PRD Tools 产出阅读指南

这是一份给第一次使用 PRD Tools 的读者看的速查文档。目标很简单：看到 `_prd-tools/` 后，知道先读什么、每个文件有什么用、哪些风险必须处理。

## 先看这张图

```text
PRD 原文
  ↓
_ingest/               证明 AI 读到了什么
  ↓
spec/                  保存结构化证据和中间判断
  ↓
report.md              给人看的结论
plan.md                给研发/QA 的执行计划
  ↓
reference-update       把新知识回流到 _prd-tools/reference/
```

## 三分钟读法

如果你只是想快速判断这次产出有没有用，按这个顺序读：

| 顺序 | 文件 | 用 30 秒看什么 | 读完应该得到什么 |
|---:|---|---|---|
| 1 | `report.md` | 需求摘要、影响层、关键风险、§10 阻塞问题 | 这次需求大不大、影响哪里、哪些事要先确认 |
| 2 | `plan.md` | 实现顺序、QA 矩阵、契约任务 | 怎么拆开发和测试 |
| 3 | `spec/contract-delta.yaml` | `needs_confirmation/blocked` | 跨团队契约是否对齐 |
| 4 | `_ingest/extraction-quality.yaml` | `pass/warn/block` | PRD 是否读可靠 |
| 5 | `spec/evidence.yaml` | 关键结论证据来源 | 是否需要继续查证 |

大多数日常评审只需要前 3 个文件。出现争议时，再看 `spec/`。

## 产物总览

一次 `prd-distill` 的标准输出如下：

| 区域 | 文件/目录 | 给谁看 | 一句话作用 |
|---|---|---|---|
| 人读结论 | `report.md` | TL、研发、QA、PM | 一屏说明需求、影响、风险，并收口阻塞问题 |
| 执行计划 | `plan.md` | 研发、QA | 开发顺序、QA 矩阵、契约任务 |
| PRD 读取 | `_ingest/` | 工具维护者、审计者 | 证明 PRD 被读成了什么 |
| 证据链 | `spec/evidence.yaml` | 研发、审计者 | 每个结论的来源 |
| 需求 IR | `spec/requirement-ir.yaml` | 研发、QA、AI | PRD 拆出来的结构化需求 |
| 影响分析 | `spec/layer-impact.yaml` | 研发、TL | 前端/BFF/后端能力面影响 |
| 契约差异 | `spec/contract-delta.yaml` | 跨团队 owner | 字段、接口、事件、外部系统对齐 |
| 知识回流 | `spec/reference-update-suggestions.yaml` | TL、工具维护者 | 哪些新知识要沉淀到 `_prd-tools/reference/` |

## 按角色阅读

不同角色不用读同一堆文件：

| 角色 | 必读 | 需要时再读 | 重点问题 |
|---|---|---|---|
| 后端研发 | `report.md`、`plan.md` | `layer-impact.yaml`、`evidence.yaml` | 改哪些模块，证据是否来自源码 |
| 前端/BFF | `report.md`、`contract-delta.yaml` | `layer-impact.yaml` | 是否有枚举、schema、payload、接口变化 |
| QA | `plan.md`、`requirement-ir.yaml` | `report.md` §10 | 验收条件、边界值、回归范围是否完整 |
| TL | `report.md`、`contract-delta.yaml` | `reference-update-suggestions.yaml` | 有没有阻塞、漏层、外部依赖和沉淀价值 |
| PM/业务 owner | `report.md` | `plan.md` 的 QA 部分 | PRD 是否被理解正确，哪些规则要确认 |
| 工具维护者 | `_ingest/`、`evidence.yaml`、`reference-update-suggestions.yaml` | `_prd-tools/build/quality-report.yaml` | 读取质量、证据质量、知识库是否要更新 |

## 人读文件

### report.md

| 项 | 说明 |
|---|---|
| 它是什么 | 给人看的结论报告，也是阻塞问题和 owner 确认项的唯一人读入口 |
| 回答什么 | 需求是什么、影响哪些层、关键开发结论、最大风险、哪些问题需要谁确认 |
| 不放什么 | 不展开完整证据链，不写所有实现细节 |
| 怎么判断好坏 | 一屏内能说清需求范围、关键风险和下一步，§10 每个问题都有 owner、影响范围和需要证据 |
| 读完动作 | 如果看到阻塞或 `needs_confirmation`，拉 owner 确认，确认结果回写到计划或 reference |

### plan.md

| 项 | 说明 |
|---|---|
| 它是什么 | 开发、QA、契约对齐的合并计划 |
| 回答什么 | 先做什么、后做什么、测什么、哪些任务依赖确认 |
| 不放什么 | PRD 原文复制、完整代码实现 |
| 怎么判断好坏 | 任务能追到 `REQ-*`、`IMP-*` 或 `CONTRACT-*` |
| 读完动作 | 拆任务、排期、补 QA case、确认跨团队契约 |

## PRD 读取区：_ingest/

`_ingest/` 的作用不是分析需求，而是回答：**AI 读到的 PRD 是否可靠？**

| 文件/目录 | 作用 | 什么时候看 | 风险信号 |
|---|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、hash、读取方式 | 复盘、确认 PRD 版本 | 文件不是预期版本 |
| `document.md` | 转换后的 PRD 正文 | 怀疑漏读、误读时 | 关键章节缺失 |
| `document-structure.json` | 段落、表格、图片结构块 | 需要精确定位证据时 | 结构块异常少 |
| `evidence-map.yaml` | PRD block 到证据 id 的映射 | 查 PRD 证据来源时 | 大量 low confidence |
| `media/` | 抽出的图片、截图、流程图 | PRD 有图时 | 图片里有关键规则 |
| `media-analysis.yaml` | 图片是否已被 vision/OCR/人工确认 | 有截图/流程图时 | `needs_vision_or_human_review` |
| `tables/` | 抽出的表格 markdown | PRD 表格很多时 | 合并单元格、字段丢失 |
| `extraction-quality.yaml` | PRD 读取质量门禁 | 每次都建议看 | `warn` 或 `block` |
| `conversion-warnings.md` | 给人看的转换风险 | 评审前快速扫 | 图片/表格风险未进入 `report.md` §10 |

### extraction-quality 怎么判断

| 状态 | 含义 | 你该怎么做 |
|---|---|---|
| `pass` | PRD 读取质量正常 | 可以正常使用后续分析 |
| `warn` | 可继续，但存在图片、复杂表格、PDF 顺序等风险 | 确认风险是否进入 `report.md` §10 |
| `block` | 读取失败或缺少关键文本 | 暂停使用结论，补 markdown/text/OCR/人工确认 |

常见 warning 的处理方式：

| Warning | 代表什么 | 正确处理 |
|---|---|---|
| 图片未 OCR/vision | 图片内容没被确认 | 图片里的规则不能作为高置信度结论 |
| 表格合并单元格 | 表格结构可能被读错 | 人工核对 `tables/` |
| PDF 阅读顺序风险 | 段落顺序可能错乱 | 核对 `document.md` |
| 没有可读文本 | 可能是扫描件 | 使用 OCR 或让用户提供文本版 |

## 机器和审计区：spec/

`spec/` 是给 AI、审计、复盘和知识回流用的。普通读者不用每次全读，但下面这些文件决定了产出的可信度。

| 文件 | 它回答的问题 | 好产出的特征 | 风险信号 |
|---|---|---|---|
| `evidence.yaml` | 结论证据来自哪里 | PRD、源码、reference、负向搜索分清楚 | 关键结论只有 reference，没有源码或 PRD |
| `requirement-ir.yaml` | PRD 被拆成哪些需求 | 每个 REQ 有规则、验收条件、证据 | 只写背景，没有可验收规则 |
| `layer-impact.yaml` | 影响哪些层和能力面 | 每个 IMP 有 current_state、planned_delta、evidence | 只写“需要修改后端”，没有能力面和证据 |
| `contract-delta.yaml` | 字段/接口/事件/外部系统怎么变 | producer、consumer、字段、状态清楚 | 多层需求没有 contract |
| `reference-update-suggestions.yaml` | 哪些知识要回流 | 建议能落到具体 `_prd-tools/reference/` 文件 | 只有泛泛总结，没有 target_file |

### evidence.yaml 速查

| evidence kind | 含义 | 可信度提示 |
|---|---|---|
| `prd` | 来自 PRD | 需求来源必备 |
| `tech_doc` | 来自技术方案/API 文档 | 对接口和实现判断很重要 |
| `code` | 来自源码 | 工程判断最关键 |
| `reference` | 来自 `_prd-tools/reference/` | 加速理解，但不是最终权威 |
| `negative_code_search` | 搜过没找到 | 证明当前代码没有该能力 |
| `human` | 人工确认 | 需要记录确认人或来源 |

### requirement-ir.yaml 速查

| 字段 | 你要看什么 |
|---|---|
| `change_type` | 是 `ADD`、`MODIFY`、`DELETE` 还是 `NO_CHANGE` |
| `rules` | 业务规则是否拆完整 |
| `acceptance_criteria` | QA 能不能据此验收 |
| `target_layers` | 是否命中了正确层 |
| `evidence` | 是否能追溯到 PRD/技术方案 |
| `confidence` | 低置信度是否进入 `report.md` §10 |

### layer-impact.yaml 速查

| 字段 | 你要看什么 |
|---|---|
| `layer` | 前端、BFF、后端、外部系统影响是否准确 |
| `surface` | 命中的是 UI、schema、API、领域模型、校验、外部集成等哪个能力面 |
| `current_state` | 当前代码是否已支持 |
| `planned_delta` | 计划新增/修改什么 |
| `risks` | 哪些实现风险要提前处理 |
| `evidence` | 是否有源码或负向搜索支撑 |

### contract-delta.yaml 速查

| 状态 | 含义 | 动作 |
|---|---|---|
| `aligned` | producer 和 consumer 都有证据 | 可以进入开发/联调 |
| `needs_confirmation` | PRD 有描述，但某层或 owner 未确认 | 拉 owner 确认 |
| `blocked` | 字段、枚举、required、时序或责任冲突 | 停止推进，先解决冲突 |
| `not_applicable` | 单层内部变化 | 不需要跨层契约对齐 |

必须看 contract 的场景：

| 场景 | 为什么 |
|---|---|
| 前端/BFF/后端都受影响 | 字段和 required 容易不一致 |
| 新增枚举或活动类型 | 多端必须同步 |
| 涉及券、权益、支付、预算 | 外部系统契约风险高 |
| 涉及 MQ/event/payload | 时序和幂等风险高 |
| 涉及 DB 字段或存储格式 | 兼容和迁移风险高 |

## 项目知识库：_prd-tools/reference/

`_prd-tools/reference/` 是项目长期记忆，不是某一次 PRD 的临时输出。v4.0 采用 6 文件结构，每个事实只存在于一个文件（SSOT），其他文件通过 ID 引用。

| 文件 | 一句话作用 | 不应该放什么 |
|---|---|---|
| `00-portal.md` | 人类导航、项目画像摘要、按场景阅读指南 | 大量事实细节 |
| `project-profile.yaml` | 项目画像、技术栈、入口、能力面、测试命令 | 单次 PRD 计划 |
| `01-codebase.yaml` | 静态清单：目录、枚举、模块、注册点、数据流 | 字段级契约、编码规则、实现步骤 |
| `02-coding-rules.yaml` | 编码规则：规范、约束、红线、反模式、踩坑经验 | 契约字段、打法步骤 |
| `03-contracts.yaml` | 跨层和外部契约：字段级信息的唯一权威来源 | 编码规则、开发步骤、枚举值列表 |
| `04-routing-playbooks.yaml` | PRD 路由信号 + 场景打法 + QA 矩阵 + golden samples | 枚举值、字段级契约、编码规则 |
| `05-domain.yaml` | 业务领域：术语、背景、隐式规则、历史决策 | 代码路径、编码规则、契约字段 |

### 按场景阅读

| 我想... | 先看 | 再看 |
|---|---|---|
| 了解项目整体结构 | `01-codebase.yaml` | `project-profile.yaml` |
| 新增一个活动类型 | `04-routing-playbooks.yaml` | `02-coding-rules.yaml`, `03-contracts.yaml` |
| 对齐跨层接口 | `03-contracts.yaml` | `01-codebase.yaml` |
| 理解业务术语 | `05-domain.yaml` | - |
| 查编码规范和红线 | `02-coding-rules.yaml` | - |
| 查高频需求怎么改 | `04-routing-playbooks.yaml` | `02-coding-rules.yaml` |

## 构建过程文件

这些通常在 `_prd-tools/build/` 目录，用来审计知识库构建过程。

| 文件 | 什么时候看 | 作用 |
|---|---|---|
| `context-enrichment.yaml` | 首次接入或补历史样例时 | 记录历史 PRD、技术方案、分支 diff、golden sample |
| `modules-index.yaml` | 检查项目扫描结果时 | 记录模块、能力面、关键文件、候选契约 |
| `health-check.yaml` | 怀疑知识库过期时 | 检查完整性、过期、缺证据、边界混乱 |
| `quality-report.yaml` | 上线或推广前 | 检查证据、契约闭环、源码一致性、幻觉风险 |
| `feedback-report.yaml` | 执行回流后 | 记录哪些建议被采纳或跳过 |

## 如何判断一次产出是否可靠

用这张表快速打分：

| 检查项 | 可靠表现 | 风险表现 |
|---|---|---|
| PRD 读取 | `extraction-quality` 是 pass，或 warn 已明确暴露 | block，或图片/表格风险没进入报告 |
| 需求拆解 | REQ 覆盖规则、限制、验收条件 | 只总结背景 |
| 代码证据 | 关键 impact 有 code evidence 或 negative search | 只引用 reference |
| 契约 | 多层/外部系统有 contract delta | 接口字段只在 plan 里口头出现 |
| 阻塞问题 | `report.md` §10 每个问题有 owner、影响、所需证据 | 问题泛泛而谈 |
| QA | 测试项能追到 REQ 或 CONTRACT | 只有“回归测试” |
| 回流 | 有具体 target_file 和建议 | 没有沉淀价值 |

## 常见误解

| 误解 | 正确认知 |
|---|---|
| YAML 很多，所以很复杂 | 普通用户只读 `report.md` 和 `plan.md`；YAML 给审计和回流用 |
| `warn` 表示失败 | `warn` 表示可以继续，但风险必须显式处理 |
| `_prd-tools/reference/` 是最终事实 | `_prd-tools/reference/` 是加速器，最终仍要以源码、PRD、技术方案、owner 确认为准 |
| 前端/BFF 为空就是漏了 | 当前仓库没有对应实现时，工具会把它放到契约确认，而不是硬写任务 |
| evidence 只要有就够 | 关键结论最好同时有 PRD 证据和源码/技术方案证据 |

## 15 分钟评审模板

| 时间 | 看什么 | 产出什么 |
|---:|---|---|
| 5 分钟 | `report.md` | 对齐需求范围、影响层、阻塞问题、owner、截止时间 |
| 4 分钟 | `contract-delta.yaml` | 确认跨层字段、枚举、外部系统 |
| 3 分钟 | `plan.md` | 确认开发顺序和 QA 重点 |
| 3 分钟 | `reference-update-suggestions.yaml` | 判断是否值得回流知识库 |

会议结束时，至少要明确：

| 问题 | 结果 |
|---|---|
| 哪些任务可以直接开工 | 开发 owner 明确 |
| 哪些问题要确认 | owner 和时间明确 |
| 哪些契约要同步 | 前端/BFF/后端/外部团队明确 |
| 哪些测试必须覆盖 | QA 重点明确 |
| 哪些知识要沉淀 | reference 回流明确 |

## 完整流程速查

### 首次接入项目

| 步骤 | 动作 | 产出 |
|---:|---|---|
| 1 | 安装 PRD Tools | `.claude/skills` |
| 2 | 收集历史 PRD、技术方案、分支 diff | golden sample 候选 |
| 3 | 运行 `reference` 的 `F 上下文收集` | `context-enrichment.yaml` |
| 4 | 运行 `A 全量构建` | `_prd-tools/reference/` |
| 5 | 运行 `B2 健康检查` | `reference-health.yaml` |
| 6 | 运行 `C 质量门控` | `reference-quality-report.yaml` |
| 7 | 用真实 PRD 跑 `prd-distill` | 单次需求产物 |

### 日常新需求

| 步骤 | 动作 | 重点 |
|---:|---|---|
| 1 | 运行 `prd-distill` | 生成本次需求分析 |
| 2 | 读 `report.md` | 快速理解范围 |
| 3 | 读 `report.md` §10 | 拉 owner 确认 |
| 4 | 读 `plan.md` | 拆开发和 QA |
| 5 | 多层需求读 `contract-delta.yaml` | 对齐字段和接口 |
| 6 | 有争议读 `evidence.yaml` | 查证据 |
| 7 | 需求结束读 `reference-update-suggestions.yaml` | 准备知识回流 |
| 8 | 运行 `reference` 的 `E 反馈回流` | 更新 `_prd-tools/reference/` |

## 这份文档的阅读原则

这份指南按三个原则组织：

| 原则 | 落地方式 |
|---|---|
| 任务优先 | 先告诉你该读哪个文件，而不是先解释所有概念 |
| 表格优先 | 文件职责、状态判断、角色路径都用表格呈现 |
| 渐进展开 | 先看人读文件，再看 PRD 读取，再看 artifacts 和 reference |

最终目标不是让每个人理解所有 YAML，而是让每个角色都能快速找到自己要看的东西，并把 PRD 分析结果推进到开发、测试、契约对齐和知识回流。
