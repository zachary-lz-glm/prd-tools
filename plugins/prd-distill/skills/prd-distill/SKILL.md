---
name: prd-distill
description: 将 PRD、需求文本、技术方案或变更说明先做稳定读取与质量检查，再编译为 AI-friendly PRD（13-section 规范化中间层），最后蒸馏为有证据支撑的 report、plan、spec 和 context，包括 Requirement IR、Layer Impact、Contract Delta、技术方案、开发/测试/契约计划和 reference 回流建议。适用于用户调用 /prd-distill，要求分析 PRD、拆需求、评估影响范围、生成开发计划、识别接口契约风险或生成 QA 矩阵时。
---

# prd-distill

Claude Code 中通过以下命令触发：

```text
/prd-distill spec <prd-file-or-text>   → PRD 解析 + 结构化需求
/prd-distill report <slug>             → 影响分析报告（需用户确认）
/prd-distill plan <slug>               → 技术方案（需 approved report）
/prd-distill <PRD 文件或需求文本>       → 引导式入口（不自动生成 plan）
```

人类可读文档见插件根目录 `README.md`。

## 团队模式（v2.20）

**自动检测**：执行前读取 `_prd-tools/reference/project-profile.yaml`（或 `team/project-profile.yaml`），如果 `layer: "team-common"`，自动进入团队模式。

**团队模式 vs 单仓模式**：

| 方面 | 单仓模式 | 团队模式 |
|------|----------|----------|
| 源码扫描 | `rg`/`glob` 源码 + reference | 禁止；从 `team/01-codebase.yaml` + `snapshots/` 读取 |
| Step 2.5 / 3.5 | 如果 index 存在则执行 | 跳过（团队仓无 index） |
| Layer Impact | 主要分析 1 层 | 4 层全部从 snapshots 填充 |
| Contract Delta | 单仓视角 | 全栈：consumers[] 从 `team/03-contracts.yaml` |
| Plan | 1 份 `plan.md` | 1 份 `team-plan.md` + N 份 `plans/plan-{repo}.md` |
| Report §10 | 按层简述（至少 4 子节） | 强制 5 个子节：10.1 Frontend / 10.2 BFF / 10.3 Backend / 10.4 External / 10.5 跨层风险 |

成员仓列表来自 `team_reference.member_repos[]`，sub-plan 文件名动态生成（`member_repos[].repo` 小写 → `plans/plan-{repo}.md`）。

## 三段式工作流（硬约束）

`/prd-distill` 采用三段式工作流：**spec → report(confirm) → plan**

| 阶段 | 核心问题 | 是否读源码 | 是否需要用户确认 |
|------|----------|------------|------------------|
| spec | PRD 本身到底说了什么 | 默认不读源码 | 不强制，但输出 open questions |
| report | 这个 PRD 放到当前项目会影响什么 | 必须读 reference / index / 源码 | 必须确认 |
| plan | 在确认后的影响分析基础上怎么实施 | 只消费确认后的 report 和 context | 不再重新解释 PRD |

### Stage 1: spec

Steps: 0 → 1 → 1.5-afprd → 1.5-quality → 2

允许产物：
- `_ingest/*`
- `spec/ai-friendly-prd.md`
- `context/evidence.yaml`
- `context/prd-quality-report.yaml`
- `context/requirement-ir.yaml`

**禁止产物**：`report.md`、`plan.md`、`context/readiness-report.yaml`、`context/final-quality-gate.yaml`

### Stage 2: report

Steps: 2.5 → 3.1 → 3.2 → 3.5 → 3.6 → 4 → 8 → 8.1-confirm

允许产物：
- `context/query-plan.yaml`（如 index 存在）
- `context/context-pack.md`（如 index 存在）
- `context/graph-context.md`
- `context/layer-impact.yaml`
- `context/contract-delta.yaml`
- `context/critique/*.yaml`
- `report.md`
- `context/report-confirmation.yaml`

**禁止产物**：`plan.md`、`context/readiness-report.yaml`、`context/final-quality-gate.yaml`

**Step 8.1 后必须暂停**：向用户展示 report 摘要和确认选项，写入 `context/report-confirmation.yaml`。

### Stage 3: plan

Steps: 5 → 6 → 7 → 8.5 → 8.6

**前置条件**：`context/report-confirmation.yaml` 必须为 `status: approved`。

- `needs_revision`：不得生成 plan，必须修正 report 或上游 context。
- `blocked`：停止蒸馏。

允许产物：
- `plan.md`（单仓）或 `team-plan.md` + `plans/plan-{repo}.md`（团队）
- `context/readiness-report.yaml`
- `context/final-quality-gate.yaml`
- `context/reference-update-suggestions.yaml`

**plan 阶段不得重新解释原始 PRD**，只消费 approved report 和 context。

## Pre-flight Enforcement（硬约束）

**每步执行前必须验证前置产物：**

Before each step, verify ALL prerequisite files from the previous step exist and are non-empty. If ANY is missing, STOP and complete that step first. Use `ls -la <path>` to verify.

**Hard Constraints Reference（关键禁止项，<10 条）：**

| # | 约束 | 原因 |
|---|------|------|
| 1 | 不得跳过前置产物验证直接执行步骤 | 步骤依赖链断裂 |
| 2 | report 未 approved 时不得生成 plan | 用户未确认影响分析 |
| 3 | spec 阶段不得产出 report/plan | 三段式工作流隔离 |
| 4 | plan 阶段不得重新解释原始 PRD | 只消费 approved report |
| 5 | 不得编造行号或 grep 命令结果 | 证据链真实性 |
| 6 | `inferred` 不得伪装为 `explicit` | 置信度诚实 |
| 7 | 每个 REQ-ID 必须在 ai-friendly-prd.md 有标题锚点 | 追溯链完整性 |

其余禁止项详见 workflow.md 对应步骤。

## Final Completion Gate（硬约束）

/prd-distill 完成必须满足以下条件，缺一不可：

1. `spec/ai-friendly-prd.md` 必须存在且包含 13 个章节。不生成不得进入 requirement-ir。
2. `context/requirement-ir.yaml` 必须包含 `ai_prd_req_id`。
3. `context/layer-impact.yaml` 必须包含 `code_anchors` 或 fallback reason。
4. 如果 `_prd-tools/reference/index` 存在，必须运行 `context-pack.py` 生成 `context/query-plan.yaml` 和 `context/context-pack.md`。**团队模式豁免**（无 index）。
5. `context/final-quality-gate.yaml` 必须生成。
6. 必须运行 `python3 .prd-tools/scripts/quality-gate.py distill --mode all --distill-dir _prd-tools/distill/<slug> --repo-root .`，且 exit code 不为 2。
7. completion gate 不通过，不得宣称 /prd-distill 完成。
8. `report.md` 必须包含 PRD 质量摘要。
9. 生成最终 plan 前，必须获得用户对 `report.md` 的确认，并写入 `context/report-confirmation.yaml`。
10. `context/report-confirmation.yaml` 的 `status` 必须为 `approved`，否则不得生成最终 plan。
11. plan 不得包含把 `missing_confirmation` 当确定任务的内容。团队模式：`team-plan.md` 和所有 `plans/plan-*.md` 均适用此规则。
12. **团队模式**：`team-plan.md` 必须存在且包含 Sub-Plan 索引表；`plans/` 目录必须存在，且每个有 IMP 的成员仓有对应的 `plans/plan-{repo}.md`。

## 触发条件

- 用户提供 PRD 文件路径或需求文本，要求分析。
- `/prd-distill` 命令。
- 需要评估影响范围、拆任务、对齐接口、生成 QA 矩阵。

不触发：直接改代码、无可分析输入、用户明确不要分析。

## 核心职责

不是总结 PRD，而是回答五个问题：

1. PRD 到底新增、修改、删除或不改变哪些需求点。
2. 这些需求分别影响前端、BFF、后端的哪些能力面。
3. 哪些字段、枚举、schema、endpoint、event 需要跨团队对齐。
4. 开发顺序和 QA 覆盖场景。
5. 本次需求暴露了哪些新知识，需回流到 `_prd-tools/reference/`。

## 输入

- PRD：`.md`/`.txt`/`.docx` 或粘贴文本。
- 可选技术方案、API 文档、接口定义。
- 当前项目源码路径。
- 当前项目 `_prd-tools/reference/`。
- 可选历史分支、diff、已有实现。

PRD 读取规则：
- 文件输入支持 `.md/.txt`（直接读取）和 `.docx`（用 unzip 提取文本+图片，零第三方依赖）。
- `.docx` 读取：解压提取 `word/document.xml`，去除 XML 标签得到纯文本；同时提取 `media/` 下的所有图片到 `_ingest/media/`。在文本中图片位置插入 `![image-N](media/imageN.png)` 占位。Claude 用 Read 工具直接查看图片（原生多模态），理解 UI 截图、流程图、数据图表。
- 用户也可以直接粘贴 PRD 文本。
- 粘贴文本 → 手工创建 ingestion 证据（来源、段落定位、质量说明）。
- 无人工确认的截图、流程图不能作为高置信度结论。

## 输出结构

### 单仓模式

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # PRD 原始读取
│   ├── source-manifest.yaml       #   文件路径、格式、hash、读取方式
│   ├── document.md                #   转换后可读 markdown
│   ├── document-structure.json    #   段落、表格、图片结构块
│   ├── evidence-map.yaml          #   PRD 块级证据 id
│   ├── media/                     #   抽出的图片
│   ├── media-analysis.yaml        #   图片语义分析状态
│   ├── tables/                    #   抽出的表格
│   ├── extraction-quality.yaml    #   pass/warn/block 质量门禁
│   └── conversion-warnings.md     #   转换风险
├── spec/                          # AI-friendly PRD（规范化中间层）
│   └── ai-friendly-prd.md         #   13-section 对 AI agent 友好的 PRD
├── report.md                      # 渐进式披露报告
├── plan.md                        # 函数级技术方案 + 开发/测试计划 + QA 矩阵
└── context/
    ├── prd-quality-report.yaml    #   AI-friendly PRD 质量评分
    ├── requirement-ir.yaml        # 结构化需求：业务意图、规则、验收条件
    ├── evidence.yaml              # 证据台账：PRD、技术方案、源码、负向搜索
    ├── readiness-report.yaml      # 就绪度评分 + 风险 + provider 增益
    ├── graph-context.md           # 源码扫描的函数级上下文
    ├── layer-impact.yaml          # 分层影响
    ├── contract-delta.yaml        # 契约差异
    ├── report-confirmation.yaml   # 用户确认 report 后才允许生成最终 plan
    ├── reference-update-suggestions.yaml  # 回流建议
    ├── query-plan.yaml              # 查询计划（辅助层）
    ├── context-pack.md              # 上下文包（辅助层）
    └── final-quality-gate.yaml      # 最终质量门禁（辅助层）
```

### 团队模式

如果 `project-profile.yaml` 的 `layer: team-common`：

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # 同单仓
├── spec/                          # 同单仓
├── report.md                      # 团队级报告（§10 分 frontend/BFF/backend/external 4 个子节）
├── team-plan.md                   # 团队级开发计划（总览 + 跨仓时序 + Sub-Plan 索引）
├── plans/                         # Sub-Plans 目录（动态命名）
│   ├── plan-genos.md              # 前端仓 sub-plan（文件名来自 member_repos[].repo）
│   ├── plan-dive-bff.md           # BFF sub-plan
│   └── plan-magellan.md           # 后端 sub-plan
└── context/
    ├── layer-impact.yaml          # 4 层完整填充（anchors 来自 snapshots）
    ├── contract-delta.yaml        # 全栈 consumers[]
    └── ...                        # 其余同单仓
```

## 输出文件边界

| 文件 | 用途 | 不放 |
|---|---|---|
| `_ingest/*` | PRD 原始读取结果 | 不写业务结论 |
| `report.md` | 渐进式披露：摘要→变更→字段→规则→Checklist→契约风险→§12 阻塞项 | 不展开 YAML 证据链 |
| `plan.md` | 技术方案 + 实现计划 + QA 矩阵 + 回滚方案 | 不复制 PRD 原文 |
| `context/evidence.yaml` | 证据台账：PRD、技术方案、源码、负向搜索 | 不下结论 |
| `context/requirement-ir.yaml` | 结构化需求：业务意图、规则、验收条件、变更类型 | 不写实现细节 |
| `context/readiness-report.yaml` | 机器可读就绪度评分、风险、provider 增益 | 不替代 report.md 的人读解释 |
| `context/graph-context.md` | 函数级技术上下文：源码扫描发现的符号、调用链和业务约束 | 不替代源码确认 |
| `context/layer-impact.yaml` | 分层影响：目标层、能力面、计划变化、风险 | 不写字段级契约详情 |
| `context/contract-delta.yaml` | 契约差异：字段、producer、consumer、alignment_status | 不写开发顺序 |
| `context/report-confirmation.yaml` | 用户对 report 理解的确认状态，决定是否允许生成最终 plan | 不存放新的需求分析结论 |
| `context/reference-update-suggestions.yaml` | 回流建议 | 不直接改 `_prd-tools/reference/` |
| `context/query-plan.yaml` | 查询计划：种子锚点、影响提示、P0 术语（辅助层） | 不替代 graph-context.md |
| `context/context-pack.md` | 上下文包：模型可消费的精简代码上下文（辅助层） | 不替代 graph-context.md |
| `context/final-quality-gate.yaml` | 最终质量门禁：5 项确定性检查评分（辅助层） | 不替代 readiness-report.yaml |
| `spec/ai-friendly-prd.md` | AI-friendly PRD：13-section 规范化中间层，给 AI agent 消费 | 不替代原始 PRD；不替代 report.md / plan.md / requirement-ir.yaml |
| `context/prd-quality-report.yaml` | AI-friendly PRD 质量评分：source 分布、缺失项、推断项、风险项 | 不替代 readiness-report.yaml |

## 能力面适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。路径只是候选，最终以能力面证据为准。

## 契约规则

以下场景必须检查或生成 Contract Delta：
- 影响超过一层。
- 新增或修改 request/response/schema/event/payload/DB 字段。
- 涉及权益、券、奖励、支付、预算、审计、异步事件、外部系统。
- 任一层只是展示/透传但 owner 未确认。

`alignment_status` 规则：
- `aligned`：producer 和 consumer 都有证据。
- `needs_confirmation`：PRD 有描述但某层未确认。
- `blocked`：字段/枚举/required/时序冲突。
- `not_applicable`：单层内部变化。

## 质量规则

- 先证据，后结论。
- 每个 requirement 至少有 PRD 或技术文档证据（优先来自 `_ingest/evidence-map.yaml`）。
- 每个 layer impact 至少有源码或负向搜索证据。
- `extraction-quality.yaml` 为 `warn` 时必须在 `report.md` §12 暴露。
- 业务关键规则不能只靠前端守。
- 中低置信度项必须进入 `report.md` §12。
- 不确定标 `confidence: low`，不补脑。
- 不直接修改 `_prd-tools/reference/`，只生成回流建议。
- **⚠ Reference 强制消费**：reference 存在时，步骤 3 门禁→步骤 6 桥接→步骤 7 reference-first 扫描，缺一不可。reference 不存在时，必须显式标记缺失并降低置信度。
- **⚠ Reference 不可盲信**：reference/index 只提供候选事实、路由和代码锚点。凡是会进入 report/plan 的结论，必须由 PRD、源码、技术文档、接口文档或负向搜索二次确认；无法确认时降置信度并写入 §12。
- `report.md` 生成前必须核对 P0/P1 细节：券批次/券张数/互斥、折扣卡 Card ID/数量/有效期/城市校验、EventRule、Budget/GMV、Push 占位符、PRD 内部冲突或 typo。不能只在 context YAML 中出现。

### AI-friendly PRD 规则

1. 输入 PRD 后，**必须先生成 AI-friendly PRD**（`spec/ai-friendly-prd.md`），不允许直接从原始 PRD 跳到 report/plan。
2. AI-friendly PRD 是结构化索引层（帮助 AI 定位信息），不替代原始 PRD。
3. 所有 `inferred` / `missing_confirmation` 必须显式标注 source。
4. `missing_confirmation` 不得进入确定性开发任务（plan.md 的 checklist）。
5. `requirement-ir.yaml` 中每条 requirement 应能追溯到 ai-friendly-prd.md 的 REQ-ID。

### Requirement-IR 对齐规则

1. `requirement-ir.yaml` 必须以 `_ingest/document.md` 为主输入，`spec/ai-friendly-prd.md` 作为 REQ-ID 框架和章节索引，`_ingest/evidence-map.yaml` 作为 block 级证据指针。不允许只读 ai-friendly-prd.md 就生成 requirement-ir。
2. 每条 requirement 必须包含 `ai_prd_req_id` 和 `source`，`source` 必须继承 AI-friendly PRD 的 source 标记（explicit / inferred / missing_confirmation）。
3. `missing_confirmation` 必须进入 `open_question_refs`，且 `planning.eligibility=blocked`。
4. `inferred` 默认 `planning.eligibility=assumption_only`，不得直接进入确定开发 checklist。
5. report.md 和 plan.md 不得绕过 requirement-ir 直接从原始 PRD 推导确定任务。

### Report Review Gate 规则

`report.md` 是用户确认 AI 是否读懂 PRD、reference、源码影响和契约风险的 checkpoint。最终 `plan.md` 必须在 report 被确认后生成。

流程：

1. 先生成 `report.md`，覆盖需求理解、影响范围、关键代码锚点、契约风险和 Top Open Questions。
2. 停止继续生成 `plan.md`，向用户展示 report 摘要和确认选项。
3. 用户确认后写入 `context/report-confirmation.yaml`。
4. 只有 `status: approved` 时，才允许生成最终 `plan.md`。
5. 如果用户指出 report 不符合预期，必须回到对应上游产物修正：AI-friendly PRD、Requirement IR、Layer Impact 或 Contract Delta，而不是直接在 plan 里补丁式修正。

确认文件格式：见 `workflow.md`（SSOT）。

状态含义：

- `approved`：可以进入最终 `plan.md`。
- `needs_revision`：不得生成最终 plan，必须修正 report 或上游 context。
- `blocked`：停止蒸馏，等待用户补充 PRD、owner 确认或技术方案。

### REQ → Code Anchor 强绑定规则

1. 每个确定性实现任务必须能回溯到 requirement-ir 的 REQ-ID，并经由 IMP-ID 关联到代码锚点。
2. 每个 MODIFY/DELETE 任务必须有 `code_anchor`（layer、file、symbol/line、confidence、source）或 fallback reason。
3. 每个 `code_anchor` 必须标注 `layer`、`file`、`symbol`、`line`（尽量精确）、`anchor_type`、`confidence`、`source`（graph / rg / reference / inferred）。
4. `planning.eligibility != ready` 的 requirement 不得生成确定性实现任务，只能生成 risks / open questions / needs_confirmation / fallback notes。
5. report/plan 不得绕过 layer-impact 直接编造目标文件。
6. 没有 `code_anchor` 的 ready MODIFY/DELETE 项必须在 report 中标红为风险。
7. `code_anchor.source=inferred` 时，不得作为唯一 high confidence 证据。

## 暂停条件

- PRD 无法读取且无文本输入。
- `extraction-quality.yaml` 为 `status: block`。
- 关键要求只存在于图片中，无人工确认。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据且无法补齐。

## 降级条件（不暂停但必须标记）

- `_prd-tools/reference/` 不存在：layer-impact/contract-delta confidence 强制降为 `low`，report.md §12 暴露缺失，readiness-report next_actions 首位建议运行 `/reference`。

## 执行步骤

> 以下编号为逻辑描述顺序，对应 gate step IDs 见 command.md。

1. 确认 PRD 来源和目标项目路径。
2. PRD ingestion：
   - `.md`/`.txt`：直接读取。
   - `.docx`：用 `unzip` 提取 `word/document.xml`（文本）和 `media/`（图片）。文本去 XML 标签后写入 `_ingest/document.md`，图片拷贝到 `_ingest/media/`。在文本中图片位置插入 `![image-N](media/imageN.png)` 占位。用 Read 工具逐个查看图片，理解内容后写入 `_ingest/media-analysis.yaml`。
   - 粘贴文本：手工建立来源和定位。
   创建 `_ingest/` 证据结构。
3. **Reference 消费门禁**：读取 `_prd-tools/reference/`（优先 v4，兼容 v3.1），**必须消费**以下内容：
   - `04-routing-playbooks.yaml`：提取 PRD 关键词→target_surfaces 路由表，供步骤 7 源码扫描优先使用。
   - `01-codebase.yaml`：提取 modules、registries、data_flows，作为源码扫描的代码地图。
   - `02-coding-rules.yaml`：提取 fatal 级规则，在 layer-impact 中必须检查是否触及。
   - `03-contracts.yaml`：提取现有契约，作为 contract-delta 基线。
   - `05-domain.yaml`：提取领域术语，用于 requirement-ir 拆解时的术语对齐。
   - 将消费状态写入 evidence.yaml（`EV-REF-CONSUMED`）。
   - **⚠ reference 不存在时**：所有涉及 reference 的步骤标记缺失，layer-impact/contract-delta confidence 强制降为 `low`，report.md §12 必须暴露。
4. 建立 `context/evidence.yaml`，映射 ingestion 证据后补充源码证据和 reference 消费证据。
5. 拆 `context/requirement-ir.yaml`。

### report 阶段

6. **Index 桥接**：如果 `_prd-tools/reference/index/` 存在，**必须**运行 `python3 .prd-tools/scripts/context-pack.py` 生成 `context/query-plan.yaml`（查询计划）。步骤 7 源码扫描**必须消费** query-plan.yaml 的 matched_entities，不能跳过。
7. **Reference-First 源码扫描**：构建 `context/graph-context.md`。
   - **阶段 1（Reference 路由）**：先查 `04-routing-playbooks.yaml` 路由表确定 target_surfaces，再查 `01-codebase.yaml` 获得精确文件路径和符号。禁止跳过直接 grep。
   - **阶段 2（Index 精确扫描）**：消费 query-plan.yaml 中 confidence=high 的 matched_entities，直接 Read 源码确认。
   - **阶段 3（补充扫描）**：仅对阶段 1-2 未覆盖的部分用 rg/glob 补充扫描。
   - 每条线索标注来源：`reference_routing` | `index_query` | `code_scan`。
- [ ] ⚠ graph-context.md 存在性检查：`context/graph-context.md` 必须存在。如不存在，必须先生成再继续 plan.md。
- [ ] ⚠ reference 消费检查：如果 reference 存在，graph-context.md 中**每个关键 IMP 至少 1 条线索来自 reference/index**（阶段 1-2）。全部线索都来自 grep 时在 readiness-report 标记 `reference_underconsumed` 并在 §12 暴露原因。
8. **Index 融合**：如果索引存在，**必须**运行 `python3 .prd-tools/scripts/context-pack.py` 生成 `context/context-pack.md`（上下文包）。index 不存在则跳过，但必须在 readiness-report 记录缺失。
9. **Step 3.5 Context Pack**：layer-impact 完成后运行 `context-pack.py`，将 Evidence Index 代码实体与 distill 上下文融合为精简的 `context/context-pack.md`（≤800 行）。index 不存在则跳过。
10. **Step 3.6 Critique Pass**：高风险步骤（1.5/2/3.2/4）完成后对产物做二次审查，输出 `context/critique/<step_id>.yaml`。fail 阻断后续步骤，warning 记入 readiness-report。详见 `workflow.md` 步骤 3.6。
11. 生成 `context/layer-impact.yaml`。
12. 生成 `context/contract-delta.yaml`。
13. 生成 `report.md`（渐进式披露 + 源码扫描命中摘要 + §12）。
14. **Report Review Gate**：暂停，要求用户确认 report 是否符合预期，写入 `context/report-confirmation.yaml`。

### plan 阶段（requires approved report）

15. 用户确认 `approved` 后，生成 `plan.md`（消费 `graph-context.md` 函数级上下文）。
16. 生成 `context/readiness-report.yaml`。
17. （辅助层）运行 `python3 .prd-tools/scripts/quality-gate.py final` 生成 `context/final-quality-gate.yaml`（5 项确定性检查评分）。
18. 生成 `context/reference-update-suggestions.yaml`。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整蒸馏时 |
| `references/output-contracts.md` | 确认输出格式和字段边界时 |
| `references/layer-adapters.md` | 判断能力面时 |
| `references/selectable-reward-golden-sample.md` | 复杂需求校准时 |
| `references/external-practices.md` | 解释设计依据时 |

## 完成标准

完成后必须说明：
- 当前完成的阶段（spec / report / plan）。
- 输出目录路径。
- `report.md` 最重要结论。
- `report.md` §12 最重要阻塞项。
- 是否存在 `needs_confirmation` 或 `blocked` 契约。
- 是否生成 reference 回流建议。
- `readiness-report.yaml` 的 status、score、decision。

**三段式完成标准**：
- spec 阶段完成：`spec/ai-friendly-prd.md` + `context/requirement-ir.yaml` 存在，提示用户继续 `/prd-distill report <slug>`。
- report 阶段完成：`report.md` 存在，已写入 `context/report-confirmation.yaml`，等待用户确认。
- plan 阶段完成：`plan.md`（单仓）或 `team-plan.md` + `plans/`（团队）存在，所有 gate 通过。
