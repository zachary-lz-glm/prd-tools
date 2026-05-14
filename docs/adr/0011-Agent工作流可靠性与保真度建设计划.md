# ADR-0011：Agent 工作流可靠性与保真度建设计划

> **已废弃**：三段式工作流、Completion Gate、Pre-flight Enforcement 已在 v2.20 瘦身重构中删除。本 ADR 记录的历史决策不再适用。

| 字段 | 值 |
|------|---|
| 状态 | 实施中 |
| 日期 | 2026-05-12 |
| 起始版本 | v2.16.1 |
| 目标版本 | v2.16.3 / v2.17.0 / v2.18.0 |
| 分支 | v2.0 |
| 范围 | 整合原 0011（防降智）+ 原 0012（三段式工作流）+ 原 0013（保真度优先）三份计划，形成一次完整迭代的统一蓝图 |
| 触发 | `/reference` 和 `/prd-distill` 在 v2.16.x 调试中暴露三类问题：多步 workflow 跳步、错误理解扩散、信息保真度下降。从 prompt 约束升级为可验证、可恢复、可度量的 agent 执行系统 |

## Context

### 这次迭代解决三个层次的问题

| 层次 | 问题 | 表象 |
|------|------|------|
| 顺序与执行 | 长流程跳步、中间产物半成品、上下文变长后注意力衰减 | step 输出不完整仍继续往后走、重新跑不知道跑到哪 |
| 信息扩散 | 错误理解从 report 传染到 plan、用户缺少明确确认点 | 一轮长上下文连续生成 report+plan，偏差被放大 |
| 信息保真 | AI-friendly PRD 被误用为压缩层，长尾业务规则蒸发 | 13 章节齐全、所有 gate 通过，但和原始 PRD 对比丢了关键细节 |

三者必须一起解决，否则单点修复会被另两类问题抵消。

### v2.16.1 → v2.16.2 已经发生的变更

| 提交 | 内容 | 性质 |
|------|------|------|
| `4bc89ff` | AI-friendly PRD compiler pipeline（13-section 规范化） | 引入了有损架构（见下） |
| `632e4e7` | Hard completion gates（reference/distill quality gate） | 方向对，但只检查存在性 |
| `6965cb0` | Portal 模板化渲染（脚本 + 固定模板） | 保留 |
| `7ac0248` | Portal 模板安装 | 保留 |

### v2.16.2 暴露的隐含假设漏洞

复盘发现 v2.16.2 引入的 AI-friendly PRD compiler 存在一个未被验证的设计前提：

> **假设：AI-friendly PRD 是可靠的下游主输入。**

这个假设通过三处规则被锁死：

1. SKILL.md：「requirement-ir.yaml 必须以 spec/ai-friendly-prd.md 为主输入，document.md 只作为证据回查」。
2. 下游 Step 2 输入清单不再包含 document.md。
3. quality gate 只检查「13 章节齐全 + ai_prd_req_id 存在」，不检查信息覆盖率。

结果是：原始 PRD → AI-friendly PRD（压缩）→ Requirement IR（再压缩）→ report/plan（消费压缩版），信息逐层蒸发。已生成的 `document-structure.json` 和 `evidence-map.yaml` 本可承担覆盖验证，但没有任何下游消费它们，变成孤儿数据。

### 行业信号收敛到同一方向

- Anthropic Building Effective Agents：简单、可组合 workflow pattern 优先于复杂 agent 框架。
- Anthropic Best practices for Claude Code：上下文窗口越满，模型越容易忘指令。
- LangGraph durable execution：checkpoint、resume、deterministic replay 是长流程关键能力。
- OpenAI Structured Outputs / Pydantic AI：结构化输出 + validation retry 是减少格式漂移的主流解法。
- AlphaCodium：代码任务先抽测试、边界和验收标准，再进入实现（flow engineering）。
- GitHub Spec Kit：`spec -> plan -> tasks` 多阶段流水线正在成为 agent 友好标准。

### Sonnet 4.6 研究结论的取舍

| 结论 | 判断 | 处理 |
|------|------|------|
| MetaGPT / AlphaCodium / LangGraph 方向 | 借鉴 | 学习「角色隔离、test-first、多阶段 flow、状态机持久化」，不照搬框架 |
| 三层防御（结构 / 语义 / schema） | 不够工程化 | 扩展为 7 层：保真度、状态机、契约、门禁、上下文预算、恢复、benchmark |
| Negative Space Prompting | 只能辅助 | 每步保留 `MUST NOT`，但不依赖它保证顺序 |
| Process Reward Models | 暂不落地 | 没有训练数据和 reward model |
| XML 状态锚点 | 低成本可用 | 用于 prompt header，权威状态来自 `workflow-state.yaml` |

### PRD Tools 已有基础

| 已有能力 | 位置 | 价值 |
|----------|------|------|
| reference / distill 两阶段 | `plugins/*/workflow.md` | 长期知识与单次 PRD 分离 |
| step gate | `scripts/{reference,distill}-step-gate.py` | 前置文件检查 |
| workflow gate | `scripts/{reference,distill}-workflow-gate.py` | 完成顺序和主产物检查 |
| completion gate | `{reference,distill}-quality-gate.py`、`final-quality-gate.py` | 最小交付物检查 |
| AI-friendly PRD / Requirement IR | prd-distill workflow | 结构化中间层（需重新定位） |
| readiness-report | `context/readiness-report.yaml` | 能否开工的红绿灯雏形 |
| document-structure / evidence-map | `_ingest/` | 已生成但未被消费的保真度数据 |

当前缺口不是「再写更多强提示词」，而是把这些脚本升级为一个**保真、可恢复、可观察**的 workflow runtime。

## Decision

采用「Fidelity-First + Workflow Runtime + Contracted Artifacts + Context Budget + Benchmark Loop」整体路线。

### 0. 总原则

PRD Tools 多步 agent 可靠性不再依赖模型自觉，而依赖七层机制：

```text
0. Fidelity First       原始 PRD 始终是主输入，压缩层是索引不是替代
1. Workflow State       记录当前步骤、完成步骤、产物 hash、重入点
2. Artifact Contract    每步产物有 schema / 必填字段 / trace 规则
3. Step Gate            进入步骤前检查前置产物和状态
4. Quality Gate         步骤后检查产物完整性、语义红线、保真度
5. Context Budget       每步只读最小必要文件
6. Benchmark Loop       用真实 case 量化收益
```

核心判断：

> 原始 PRD 是事实，prompt 是说明书，gate 是刹车，workflow-state 是账本，benchmark 是收益证明。

### 0.1 Human Checkpoints

防跳步不等于全自动跑到底。必须保留两个关键人机交互点：

| Workflow | Checkpoint | 目的 | 通过后 |
|----------|------------|------|--------|
| `/reference` | Mode Selection Gate | 让用户选择 F→A、F only、A only、B/B2/C/E，避免误重建或误跳过上下文收集 | 才允许写 reference 产物 |
| `/prd-distill` | Report Review Gate | 让用户确认 AI 对 PRD、影响范围、契约风险和阻塞项的理解 | 才允许生成最终 `plan.md` |

这两个 checkpoint 是工作流的一部分，不是可选 UI。后续任何 completion gate 都必须检查对应确认状态。

### 1. Fidelity First：保真度优先

#### 1.1 AI-friendly PRD 重新定位

| 维度 | v2.16.2（有损） | v2.16.3 起（保真） |
|------|----------------|-------------------|
| 角色 | 下游主输入（替代 document.md） | 结构化导航 + REQ-ID 框架 |
| 是否压缩 | 是（13 章节压缩长尾） | 是（索引必然压缩） |
| 是否替代原始 PRD | 是 | 否 |
| 下游消费方式 | 直接读 ai-friendly-prd.md 提取需求 | 用 ai-friendly-prd.md 定位 REQ，再回查 document.md 获取完整细节 |

**AI-friendly PRD 是结构化索引层，不是摘要层。** 它帮助 AI 定位信息，不替代原始内容。

#### 1.2 主输入回到 `_ingest/document.md`

修正 SKILL.md / workflow.md 中的关键条款：

```diff
- requirement-ir.yaml 必须以 spec/ai-friendly-prd.md 为主输入，
- _ingest/document.md 只能作为证据回查。
+ requirement-ir.yaml 必须以 _ingest/document.md 为主输入，
+ spec/ai-friendly-prd.md 作为 REQ-ID 框架和章节索引，
+ _ingest/evidence-map.yaml 作为 block 级证据指针。
+ 不允许只读 ai-friendly-prd.md 就生成 requirement-ir。
```

requirement-ir 每条 requirement 的 trace 关系：

```yaml
- id: REQ-001
  ai_prd_req_id: REQ-1.2        # 索引锚点
  source_blocks:                 # 新增：原始 PRD block_id 列表
    - block_id: B-031
      type: text
    - block_id: B-035
      type: table
  evidence:
    - "_ingest/document.md:142-156"
  acceptance_criteria: [...]
```

#### 1.3 保真度门禁 `prd-coverage-gate.py`

消费已生成但孤立的 `document-structure.json` 和 `evidence-map.yaml`，输出 `context/coverage-report.yaml`。

最小检查集：

| 检查项 | 规则 | 等级 |
|-------|------|------|
| block_coverage | `document-structure.json` 中所有 P0/P1 block 必须出现在 `evidence-map.yaml` | fatal |
| media_coverage | 所有 `media/*.png` 必须在 `media-analysis.yaml` 有 analysis | fatal |
| requirement_trace | `requirement-ir.yaml` 每条 requirement 的 `source_blocks` 非空 | fatal |
| ai_prd_coverage | `ai-friendly-prd.md` 章节覆盖 `document-structure.json` 中所有 section | warning |
| detail_recall | 数值约束 / 枚举值 / 边界条件类 block 必须 100% 被 requirement-ir 覆盖 | warning（v2.17 升 fatal） |

`distill-quality-gate.py` 集成此 gate：fail 阻断，warning 进入 readiness risks。

<!-- APPEND_MARKER_1 -->

### 2. Workflow State v2

统一状态文件：

```text
_prd-tools/build/reference-workflow-state.yaml
_prd-tools/distill/<slug>/workflow-state.yaml
```

状态文件是 workflow 的权威账本：

```yaml
schema_version: "2.0"
workflow: "reference | prd-distill"
run_id: "2026-05-12T10-30-00Z"
tool_version: "2.17.0"
mode: "spec | report | plan"           # prd-distill 三段式专用
current_stage: "spec | awaiting_report_confirmation | plan | completed"
current_step: "3.2-layer-impact"
status: "running | blocked | failed | completed"
completed_steps:
  - id: "0-ingest"
    output:
      - "_ingest/document.md"
      - "_ingest/source-manifest.yaml"
    hash: "sha256:..."
    completed_at: ""
    gate:
      status: "pass"
      script: "distill-step-gate.py"
blocked_steps: []
artifacts:
  context/requirement-ir.yaml:
    producer_step: "2-requirement-ir"
    schema: "requirement_ir_v2"
    hash: "sha256:..."
    required_by:
      - "3.1-graph-context"
      - "3.2-layer-impact"
human_checkpoints:
  report_review:
    status: "pending | approved | needs_revision | blocked"
resume:
  next_step: "3.2-layer-impact"
  reason: "previous steps passed"
```

要求：

- 每步开始时写 `current_step`。
- 每步完成后登记 output、hash、gate status。
- gate fail 时状态变 `blocked`，写 `blocked_steps`。
- 重新运行时 agent 必须先读 state，不能凭对话记忆判断进度。

### 3. 三段式 `/prd-distill`

把 PRD-to-Code 拆成三个不同认知任务：

| 阶段 | 核心问题 | 是否读源码 | 是否需要用户确认 |
|------|----------|------------|------------------|
| spec | PRD 本身到底说了什么 | 否（只读原始 PRD） | 不强制，但输出 open questions |
| report | 这个 PRD 放到当前项目会影响什么 | 必须读 reference / index / 源码 | **必须确认** |
| plan | 在确认后的影响分析基础上怎么实施 | 只消费确认后的 report 和 context | 不再重新解释 PRD |

命令形态：

```bash
/prd-distill spec <prd-file-or-text>
/prd-distill report <slug>
/prd-distill plan <slug>

# 兼容入口：先跑 spec，提示用户继续
/prd-distill <prd-file-or-text>
```

<!-- APPEND_MARKER_2 -->

#### 3.1 spec 阶段

**职责**：读取 `.md / .txt / .docx / pasted text`，建立证据结构，生成 AI-friendly spec 和 Requirement IR。

**产物**：

```text
_prd-tools/distill/<slug>/
├── _ingest/
│   ├── document.md
│   ├── document-structure.json
│   ├── evidence-map.yaml
│   ├── media/
│   └── media-analysis.yaml
├── spec/ai-friendly-prd.md
└── context/
    ├── prd-quality-report.yaml
    ├── requirement-ir.yaml
    └── coverage-report.yaml
```

**完成 gate**：

- `spec/ai-friendly-prd.md` 至少 13 章节。
- `requirement-ir.yaml` 每条 requirement 能追溯到 ai-friendly-prd 的 REQ-ID **和** document.md 的 source_blocks。
- 每条 P0/P1 requirement 必须有 acceptance criteria 或 open question。
- `prd-coverage-gate.py status: pass`。

**默认不做**：不扫描源码、不生成 layer-impact、不生成 report / plan、不把 inferred 或 missing_confirmation 当成确定任务。

#### 3.2 report 阶段

**职责**：把 spec 放到当前项目语境中，生成影响分析报告，**暂停等待用户确认**。

**消费**：`spec/ai-friendly-prd.md` + `context/requirement-ir.yaml` + `_prd-tools/reference/` + （如有 index）`query-plan.yaml` + `context-pack.md`。

**产物**：

```text
_prd-tools/distill/<slug>/
├── report.md
└── context/
    ├── query-plan.yaml
    ├── context-pack.md
    ├── graph-context.md
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── report-confirmation.yaml  # 等待用户确认后写入
```

**Report Review Gate**：

```yaml
schema_version: "1.0"
status: "approved | needs_revision | blocked"
confirmed_by: "user"
confirmed_at: ""
approved_sections:
  - "requirements"
  - "layer_impact"
  - "contract_delta"
  - "open_questions"
revision_requests: []
blocked_reason: ""
```

规则：`approved` 才允许进入 plan；`needs_revision` 回到上游修正；`blocked` 停止。

**UX 要求**：report 结束时输出简短确认提示（需求摘要 + 影响范围 + 契约风险 + Top Open Questions + 未覆盖 block 清单）。

#### 3.3 plan 阶段

**职责**：在 report 已 approved 后，生成可执行技术方案和交付包。

**消费**：approved 的 `report.md` + `requirement-ir.yaml` + `layer-impact.yaml` + `contract-delta.yaml` + `context-pack.md`。

**产物**：

```text
_prd-tools/distill/<slug>/
├── plan.md
├── portal.html
└── context/
    ├── readiness-report.yaml
    ├── final-quality-gate.yaml
    └── reference-update-suggestions.yaml
```

**默认不做**：不重新解释原始 PRD、不绕过 report 重新扫源码、不把 blocked / missing_confirmation 写入确定 checklist、不直接改代码。

#### 3.4 Reference Workflow 边界

`/reference` **不采用三段式拆命令**。

```text
/reference
  -> Mode Selection Gate
  -> Mode F context enrichment（可选）
  -> Phase 1 structure scan
  -> Phase 2 deep analysis consolidated pass
  -> quality / index / portal
```

原因：reference 是长期知识库构建，需要整体建模；Phase 2 五个产物文件互相约束，拆成独立小任务会丢全局一致性。

<!-- APPEND_MARKER_3 -->

### 4. Step Gate 从「文件存在」升级为「状态 + 契约」

| 检查项 | 当前 | 升级后 |
|--------|------|--------|
| 前置文件 | 存在且非空 | 存在、非空、hash 登记在 state |
| 顺序 | 部分检查 | requested_step 必须等于 state.resume.next_step，除非 `--allow-rerun` |
| 产物版本 | 基本无 | schema_version / tool_version 必须存在 |
| trace | 少量文本检查 | REQ-ID / IMP-ID / ai_prd_req_id / source_blocks 必须跨文件可追溯 |
| 条件步骤 | index 存在时检查 query-plan | 写入 state 的 skipped reason |
| 三段式 stage | 无 | spec/report/plan stage；plan stage 必须检查 `report-confirmation.yaml status: approved` |

### 5. Artifact Contract Registry

新增产物契约目录：

```text
plugins/prd-distill/skills/prd-distill/references/contracts/
├── ai-friendly-prd.contract.yaml
├── requirement-ir.contract.yaml
├── layer-impact.contract.yaml
├── contract-delta.contract.yaml
├── readiness-report.contract.yaml
└── agent-pack.contract.yaml

plugins/reference/skills/reference/references/contracts/
├── reference-files.contract.yaml
├── project-profile.contract.yaml
└── quality-report.contract.yaml
```

contract 先用轻量 YAML 规则：

```yaml
artifact: "context/requirement-ir.yaml"
schema_version: "2.0"
required_top_level:
  - meta
  - requirements
required_rules:
  - id: "primary_source_is_raw"
    path: "meta.primary_source"
    equals: "_ingest/document.md"
  - id: "req_has_full_trace"
    each: "requirements"
    required:
      - id
      - ai_prd_req_id
      - source_blocks
      - evidence
      - acceptance_criteria
  - id: "source_blocks_not_empty"
    each: "requirements"
    require:
      - "len(source_blocks) > 0"
  - id: "missing_confirmation_not_ready"
    each: "requirements"
    when: "source == missing_confirmation"
    forbid:
      - "planning.eligibility == ready"
```

通用 validator：`python3 scripts/validate-artifact.py --artifact <file> --contract <contract>`

### 6. Context Budget：防降智的真正抓手

每步 context budget 规则：

| 步骤 | 必读 | 禁止默认读取 | 输出 |
|------|------|--------------|------|
| reference step 01 | project tree、少量入口源码 | 全量 references | modules-index |
| reference step 02 | `reference-v4.md`、当前层 adapter、templates、modules-index | prd-distill schemas | reference 6 文件 |
| distill spec step 1.5 | `_ingest/document.md`、`evidence-map.yaml`、`document-structure.json` | 源码 | ai-friendly PRD |
| distill spec step 2 | `_ingest/document.md`（主）+ ai-friendly PRD（索引）+ evidence-map + prd-quality-report | 源码 | requirement-ir |
| distill report step 3.1 | requirement-ir、reference routing、index/query-plan | report/plan | graph-context |
| distill plan step 5 | approved report、requirement-ir、layer-impact、contract-delta、context-pack | 原始长 PRD | plan |

每个 step prompt 顶部增加固定 header：

```xml
<workflow_state>
  <workflow>prd-distill</workflow>
  <stage>spec</stage>
  <current_step>2-requirement-ir</current_step>
  <primary_input>_ingest/document.md</primary_input>
  <index_inputs>spec/ai-friendly-prd.md, _ingest/evidence-map.yaml</index_inputs>
  <must_not_read_by_default>report.md, plan.md, unrelated source files</must_not_read_by_default>
  <must_not_produce>report.md, plan.md</must_not_produce>
</workflow_state>
```

### 7. Acceptance Criteria 闭环

| 产物 | 要求 |
|------|------|
| `spec/ai-friendly-prd.md` | 每个 REQ 必须有 AC 或明确 `missing_confirmation` |
| `context/requirement-ir.yaml` | AC 必须结构化：`id / statement / source / testability` |
| `context/layer-impact.yaml` | 每个 impact 必须说明影响哪些 AC |
| `plan.md` | 每个实现任务必须引用 REQ-ID 和 AC-ID |
| `agent-pack/verification-plan.md` | 每个 AC 至少一种验证方式 |
| `readiness-report.yaml` | AC 不可测时降低 task_executability |

### 8. Two-Pass Critic（不做 PRM）

```text
Pass A: 生成步骤产物
Pass B: 只读本步骤产物 + contract + 上一步产物，输出 critique.yaml
Gate: critique.status != fail 才允许进入下一步
```

只在高风险步骤启用：AI-friendly PRD、Requirement IR、Layer Impact、Contract Delta、Agent Pack。

### 9. 跳步定义为可测试故障

| 类型 | 例子 | 检测方式 |
|------|------|----------|
| `missing_prerequisite` | 有 layer-impact 但无 requirement-ir | step gate |
| `stale_artifact` | plan 引用旧 requirement hash | workflow-state hash |
| `trace_break` | plan task 无 REQ-ID | artifact contract |
| `forbidden_output` | spec stage 生成 report.md | step sandbox |
| `underconsumed_reference` | reference 存在但 graph-context 没用 | quality gate |
| `assumption_promoted` | missing_confirmation 进入确定任务 | contract validator |
| `context_overread` | spec stage 读源码并直接写实现计划 | step-inputs.yaml |
| `fidelity_loss` | P0 block 未进入 requirement-ir | prd-coverage-gate |
| `index_treated_as_source` | Step 2 没读 document.md，只读了 ai-friendly-prd | step-inputs.yaml |

每次 gate fail 记录到 `_prd-tools/metrics/workflow-violations.jsonl`。

<!-- APPEND_MARKER_4 -->

## Implementation Plan

按版本分阶段。每个阶段独立验收、独立发版。

### v2.16.3（patch，本周）：保真度优先

目标：止血，把 v2.16.2 引入的有损架构改回索引架构，建立保真度 gate。

任务：

1. 修改 SKILL.md：把「requirement-ir 必须以 ai-friendly-prd 为主输入」改为「以 document.md 为主输入，ai-friendly-prd 是索引」。
2. 修改 workflow.md：Step 2 输入清单加 `document.md`、`evidence-map.yaml`、`document-structure.json`。
3. 修改 `distill-step-gate.py`：Step 2 prerequisites 补充 `document-structure.json` 和 `evidence-map.yaml`。
4. requirement-ir schema 新增 `source_blocks` 字段。
5. 新增 `scripts/prd-coverage-gate.py`：5 项最小检查。
6. `distill-quality-gate.py` 集成 `prd_coverage` 检查。
7. 输出 `context/coverage-report.yaml`。
8. CHANGELOG + release patch。

验收：

- 手动删除某 P0 block 的 evidence 后，coverage gate fail。
- 缺 media-analysis 条目时 fail。
- requirement-ir 中某条 requirement 缺 source_blocks 时 fail。
- 已有 distill 目录跑 quality gate 不报新增 false positive。
- 跑现有 benchmark case，coverage_ratio >= 0.9。

### v2.17.0（minor，2-3 周）：Workflow State + 三段式骨架

#### Phase A：Workflow State v2 + Step Gate 升级

1. 设计 `workflow-state.yaml` schema v2.0。
2. step gate 增加 `--write-state`。
3. step gate 通过时写 `current_step` 和 `resume.next_step`；fail 时写 `status: blocked`。
4. step gate 检查 hash 一致性。
5. SKILL.md 强制每步开始前运行 step gate。
6. 每个 step 文件顶部加 `workflow_state` header。
7. 支持 `--allow-rerun` 和 `--repair-state` 逃生口。

验收：删除前置产物后下一步 fail；重跑提示 unusual rerun；中断后能从 state 恢复。

#### Phase B：`/prd-distill` 三段式骨架

1. 更新 command 文件识别 `spec | report | plan` 子命令。
2. 更新 SKILL.md 三段式入口。
3. 保留 `/prd-distill <PRD>` 兼容入口。
4. `distill-step-gate.py` 增加 stage 概念。
5. `plan` gate 检查 `report-confirmation.yaml status: approved`。
6. `distill-workflow-gate.py` 顺序对齐三段式。
7. report 结束输出确认提示。
8. 用户回复写入 `report-confirmation.yaml`。

验收：spec 不生成 report/plan；report 不生成 plan；plan 在 report 未 approved 时 fail。

#### Phase C：`/reference` Mode Selection Gate

1. 恢复 Mode Selection Gate，首次构建默认推荐 F→A，必须等用户确认。
2. 写入 `reference-workflow-state.yaml` 的 `human_checkpoints.mode_selection`。

验收：`/reference` 在没有用户确认模式前不得开始构建。

### v2.18.0（minor，3-4 周）：Contract + Budget + Critic

#### Phase D：Artifact Contract MVP

1. 新增 `scripts/validate-artifact.py`。
2. 新增 4 个最关键 contract。
3. `distill-quality-gate.py` 调用 validator。
4. validator 输出 `context/artifact-validation.yaml`。
5. `readiness-report.yaml` 消费 validation 结果。

验收：缺 trace 时 fail；missing_confirmation 进入 ready 时 fail。

#### Phase E：Context Budget 落地

1. 每个 step 加 `allowed_inputs` 和 `forbidden_outputs`。
2. 长步骤拆成「生成」和「核验」两段。
3. 输出 `context/step-inputs.yaml`。
4. quality gate 检查过度读取。
5. 检查 Step 2 必须读 document.md。

验收：Requirement IR 步骤不能依赖源码直接生成实现计划；Plan 必须消费 layer-impact 和 contract-delta。

#### Phase F：Two-Pass Critic

1. 新增 `steps/critique-template.md`。
2. 为 5 个高风险产物生成 `context/critique/<step>.yaml`。
3. critique fail 时阻断下一步。
4. findings 汇总到 readiness-report。

验收：人工制造 trace break，critic 能发现；warning 不阻断但进入 readiness risks。

### v2.19.0（minor，待定）：Agent Pack + Benchmark

#### Phase G：Agent Pack

```text
agent-pack/
├── implementation-prompt.md
├── task-graph.yaml（DAG，每 task 引用 REQ-ID + AC-ID）
├── code-anchor-map.yaml
├── verification-plan.md
├── risk-guardrails.md
└── review-checklist.md
```

验收：Agent Pack 可直接交给 coding agent；不需要重新阅读全量 PRD。

#### Phase H：Benchmark

| 指标 | v2.17 目标 | v2.18 目标 |
|------|------------|------------|
| workflow_order_pass_rate | >= 95% | >= 98% |
| trace_completeness | >= 90% | >= 95% |
| coverage_ratio | >= 90% | >= 95% |
| assumption_leak_count | 0 | 0 |
| P0 requirement missed | 0 | 0 |
| rerun_recovery_success | >= 90% | >= 95% |

<!-- APPEND_MARKER_5 -->

## Priority

最有收益的执行顺序：

1. **保真度优先**（v2.16.3）——止血，纠正最严重的架构偏差。
2. **Workflow State v2**（v2.17.0 Phase A）——让流程可恢复、可观察。
3. **三段式骨架**（v2.17.0 Phase B）——防错误扩散。
4. **Mode Selection Gate**（v2.17.0 Phase C）——reference 入口对齐。
5. **Artifact Contract MVP**（v2.18.0 Phase D）——中间产物可检查。
6. **Context Budget**（v2.18.0 Phase E）——控制降智主因。
7. **Two-Pass Critic**（v2.18.0 Phase F）——高风险步骤自检。
8. **Agent Pack**（v2.19.0 Phase G）——稳定消费层。
9. **Benchmark**（v2.19.0 Phase H）——量化收益。

不要优先做：训练 PRM、引入完整 LangGraph runtime、为每个小字段写复杂语义 smell check、在 prompt 里堆越来越多「千万不要」。

## Consequences

### 收益

- 信息保真度从「人工对比」变成机器可验证。
- 跳步从「主观感觉」变成 gate 可捕获的错误。
- 中断恢复有 state，不再靠对话记忆。
- 错误理解扩散在 report review gate 被拦截。
- 上下文预算直接缓解长流程降智。
- Agent Pack 更适合交给 Claude Code、Codex、Copilot coding agent。

### 代价

- 新增若干 contract 和 validator，维护成本上升。
- workflow-state hash 让重跑更严格，需要逃生口。
- Two-Pass Critic 增加运行时间，只放高风险步骤。
- 三段式流程多一次用户确认。
- Step 2 输入变长（多读 document.md）。
- requirement-ir schema 增加 `source_blocks`，旧产物不向前兼容。

### 风险与缓解

| 风险 | 缓解 |
|------|------|
| gate 过严导致调试效率低 | `--warning-only` 和 `--repair-state`，默认严格 |
| contract 维护滞后 | 同步纳入 `validate-contracts.sh` |
| 模型为过 gate 写形式主义内容 | benchmark 加 false positive penalty |
| 状态文件与真实文件漂移 | artifact hash + `--refresh` 修复 |
| document.md 太长 Step 2 context 爆炸 | evidence-map 提供 block 切片，按 REQ 选择性读 |
| 旧 distill 目录跑新 gate 全部 fail | `--legacy-skip-coverage` 逃生口 |
| ai-friendly-prd 索引角色不清晰 | SKILL.md 显式禁止 + step-inputs.yaml 检查 |
| coverage_ratio 阈值定不准 | v2.16.3 先 warning，跑 benchmark 校准后升 fatal |
| 用户嫌确认麻烦 | 允许显式 approved，但必须写 confirmation |
| reference 被误拆碎 | 只做 Mode Selection Gate + 大阶段 gate |

## References

- `docs/adr/0012-retrospective.md`：v2.16.1 → v2.16.2 升级复盘，本 ADR 的直接触发源。
- ADR-0010：PRD-to-Code 质量闭环；本 ADR 是其工作流可靠性 + 保真度补丁。
- [Anthropic, "Building effective agents"](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic, "Best practices for Claude Code"](https://code.claude.com/docs/en/best-practices)
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [AlphaCodium](https://huggingface.co/papers/2401.08500)
- [GitHub Spec Kit](https://github.com/github/spec-kit)

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-12 | v1.0 | 整合原 ADR-0011（防降智）+ ADR-0012（三段式工作流）+ ADR-0013（保真度优先）为统一迭代计划 |
