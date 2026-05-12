# ADR-0011：Agent 工作流顺序与防降智实施计划

| 字段 | 值 |
|------|---|
| 状态 | 计划中 |
| 日期 | 2026-05-12 |
| 目标版本 | v2.17.0 / v2.18.0 |
| 分支 | v2.0 |
| 触发 | 最近 `/reference` 和 `/prd-distill` 调试暴露出多步 workflow 跳步、产物半成品、上下文变长后模型注意力衰减等问题；需要从 prompt 约束升级为可验证、可恢复、可度量的 agent 执行系统 |

## Context

Sonnet 4.6 给出的研究结论方向基本正确：PRD-to-Code 的关键瓶颈不是“模型不会写代码”，而是：

1. PRD、reference、代码锚点、契约和执行计划之间缺少强制顺序。
2. 中间产物不完整时，agent 仍会继续往后编。
3. 上下文变长后，模型会忘记早期约束，出现跳步、重复、越界、低质量总结。
4. 质量检查散落在 prompt 和最终报告里，缺少机器可验证的红绿灯。

但 Sonnet 报告中也有需要降噪的地方：

| 结论 | 判断 | 处理 |
|------|------|------|
| MetaGPT / AlphaCodium / LangGraph 方向值得借鉴 | 正确 | 借鉴“角色隔离、test-first、多阶段 flow、状态机持久化”，不照搬框架 |
| 三层防御：结构层 / 语义层 / schema 层 | 正确但不够工程化 | 扩展为 6 层：状态机、schema、质量门禁、上下文预算、恢复机制、benchmark |
| Negative Space Prompting | 有用但只能辅助 | 每步保留 `MUST NOT`，但不能依赖它保证顺序 |
| Process Reward Models | 当前不落地 | 没有训练数据和 reward model，不作为近期计划 |
| XML 状态锚点 | 低成本可用 | 可用于 prompt header，但权威状态必须来自 `workflow-state.yaml` |

行业信号也在收敛到同一方向：

- Anthropic 的 agent 实践强调简单、可组合的 workflow pattern，而不是一上来堆复杂 autonomous agent。
- LangGraph 的 durable execution 强调 checkpoint、resume、deterministic replay，正好对应长流程中断和重入问题。
- OpenAI Structured Outputs / Pydantic AI 都说明结构化输出和 validation retry 是减少格式漂移的主流工程解法。
- AlphaCodium 代表的 flow engineering 说明代码任务要先抽测试、边界和验收标准，再进入实现。
- GitHub Spec Kit 代表的 spec-driven development 正在把 `spec -> plan -> tasks` 变成 agent 友好的标准流水线。
- Claude Code 官方最佳实践明确指出上下文窗口越满，模型越容易忘指令、犯错；这正是 prd-tools 的“降智”根因之一。

PRD Tools 已经有基础：

| 已有能力 | 位置 | 价值 |
|----------|------|------|
| reference / distill 两阶段 | `plugins/*/workflow.md` | 已经把长期知识和单次 PRD 分离 |
| step gate | `scripts/reference-step-gate.py`、`scripts/distill-step-gate.py` | 已有前置文件检查 |
| workflow gate | `scripts/reference-workflow-gate.py`、`scripts/distill-workflow-gate.py` | 已有完成顺序和主产物检查 |
| completion gate | `reference-quality-gate.py`、`distill-quality-gate.py`、`final-quality-gate.py` | 已有最小交付物检查 |
| AI-friendly PRD / Requirement IR | `prd-distill` workflow | 已经把原始 PRD 编译成结构化中间层 |
| readiness-report | `context/readiness-report.yaml` | 已有“能不能开工”的红绿灯雏形 |

当前缺口不是“再写更多强提示词”，而是把这些脚本升级为一个可恢复的 workflow runtime。

## Decision

采用“Workflow Runtime + Contracted Artifacts + Context Budget + Benchmark Loop”的路线。

### 1. 总原则

PRD Tools 的多步 agent 可靠性不再依赖模型自觉，而依赖六层机制：

```text
1. Workflow State       记录当前步骤、完成步骤、产物 hash、重入点
2. Artifact Contract    每步产物有 schema / 必填字段 / trace 规则
3. Step Gate            进入步骤前检查前置产物和状态
4. Quality Gate         步骤后检查产物完整性和语义红线
5. Context Budget       每步只读最小必要文件，避免上下文过载
6. Benchmark Loop       用真实 case 量化有没有减少漏召回、跳步和假计划
```

核心判断：

> prompt 是说明书，gate 是刹车，workflow-state 是事实来源，benchmark 是收益证明。

### 1.1 Human Checkpoints

防跳步不等于全自动跑到底。PRD Tools 必须保留关键人机交互点：

| Workflow | Checkpoint | 目的 | 通过后 |
|----------|------------|------|--------|
| `/reference` | Mode Selection Gate | 让用户选择 F→A、F only、A only、B/B2/C/E，避免误重建或误跳过上下文收集 | 才允许写 reference 产物 |
| `/prd-distill` | Report Review Gate | 让用户确认 AI 对 PRD、影响范围、契约风险和阻塞项的理解 | 才允许生成最终 `plan.md` |

这两个 checkpoint 是工作流的一部分，不是可选 UI。后续任何 completion gate 都必须检查对应确认状态。

### 2. Workflow State v2

新增统一状态文件：

```text
_prd-tools/build/reference-workflow-state.yaml
_prd-tools/distill/<slug>/workflow-state.yaml
```

状态文件不再只是 `completed_steps`，而要成为 workflow 的权威账本。

```yaml
schema_version: "2.0"
workflow: "reference | prd-distill"
run_id: "2026-05-12T10-30-00Z"
tool_version: "2.17.0"
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
resume:
  next_step: "3.2-layer-impact"
  reason: "previous steps passed"
```

要求：

- 每个步骤开始时写 `current_step`。
- 每个步骤完成后登记 output、hash、gate status。
- 如果 gate fail，状态变成 `blocked`，并写 `blocked_steps`。
- 重新运行时，agent 必须先读取 state，不能凭对话记忆判断进度。

### 3. Step Gate 从“文件存在”升级为“状态 + 契约”

现有 step gate 只看文件是否存在，容易被空文件、错版文件、旧文件骗过。升级方向：

| 检查项 | 当前 | 升级后 |
|--------|------|--------|
| 前置文件 | 存在且非空 | 存在、非空、hash 登记在 state |
| 顺序 | 部分检查 | requested_step 必须等于 state.resume.next_step，除非 `--allow-rerun` |
| 产物版本 | 基本无 | schema_version / tool_version 必须存在 |
| trace | 少量文本检查 | REQ-ID / IMP-ID / ai_prd_req_id 必须跨文件可追溯 |
| 条件步骤 | index 存在时检查 query-plan | 写入 state 的 skipped reason，避免后续误判 |

近期不必引入 LangGraph。用现有 Python 脚本即可落地 80% 的 durable execution 思想。

### 4. Artifact Contract Registry

新增产物契约目录：

```text
plugins/prd-distill/skills/prd-distill/references/contracts/
├── ai-friendly-prd.contract.yaml
├── requirement-ir.contract.yaml
├── graph-context.contract.yaml
├── layer-impact.contract.yaml
├── contract-delta.contract.yaml
├── readiness-report.contract.yaml
└── agent-pack.contract.yaml

plugins/reference/skills/reference/references/contracts/
├── reference-files.contract.yaml
├── project-profile.contract.yaml
└── quality-report.contract.yaml
```

contract 先不追求完整 JSON Schema，采用轻量 YAML 规则，方便 shell/Python 校验。

```yaml
artifact: "context/requirement-ir.yaml"
schema_version: "2.0"
required_top_level:
  - meta
  - requirements
required_rules:
  - id: "ai_prd_source"
    path: "meta.ai_prd_source"
    equals: "spec/ai-friendly-prd.md"
  - id: "req_has_trace"
    each: "requirements"
    required:
      - id
      - ai_prd_req_id
      - evidence
      - acceptance_criteria
  - id: "missing_confirmation_not_ready"
    each: "requirements"
    when: "source == missing_confirmation"
    forbid:
      - "planning.eligibility == ready"
```

先实现一个通用 validator：

```bash
python3 .prd-tools/scripts/validate-artifact.py \
  --artifact _prd-tools/distill/<slug>/context/requirement-ir.yaml \
  --contract .prd-tools/contracts/requirement-ir.contract.yaml
```

收益：

- 把“模型应该记住的格式”变成脚本能检查的规则。
- 后续可逐步迁移到 JSON Schema / Pydantic，不影响当前 shell-first 架构。

### 5. Context Budget：防降智的真正抓手

“AI 降智”在 prd-tools 里主要不是模型突然变笨，而是上下文变得又长又混：

- workflow.md + SKILL.md + 多个 references + 源码 + PRD + 历史对话一起进上下文。
- 早期硬约束被后续材料冲淡。
- 同一事实在多个文件重复出现，模型不知道哪个权威。
- 长步骤一次性做太多任务，模型在后半段开始偷懒。

新增每步 context budget 规则：

| 步骤 | 必读 | 禁止默认读取 | 输出 |
|------|------|--------------|------|
| reference step 01 | project tree、少量入口源码 | 全量 references | modules-index |
| reference step 02 | `reference-v4.md`、当前层 adapter、templates、modules-index | prd-distill schemas | reference 6 文件 |
| distill step 1.5 | `_ingest/document.md`、evidence-map | 源码 | ai-friendly PRD |
| distill step 2 | ai-friendly PRD、prd-quality-report | 源码 | requirement-ir |
| distill step 3.1 | requirement-ir、reference routing、index/query-plan | report/plan | graph-context |
| distill step 5 | requirement-ir、layer-impact、contract-delta、context-pack | 原始长 PRD | plan |

每个 step prompt 顶部增加固定 header：

```xml
<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>3.2-layer-impact</current_step>
  <allowed_inputs>context/requirement-ir.yaml, context/graph-context.md</allowed_inputs>
  <must_not_read_by_default>report.md, plan.md, unrelated source files</must_not_read_by_default>
  <must_not_produce>report.md, plan.md</must_not_produce>
</workflow_state>
```

注意：XML header 只是模型可读提示，不能替代 step gate。

### 6. Acceptance Criteria First

AlphaCodium 的核心启发不是“让 AI 自测一下”，而是把验收条件前置为所有后续步骤的约束。

prd-tools 已经在 AI-friendly PRD 和 requirement-ir 中引入 `acceptance_criteria`，但还需要补闭环：

| 产物 | 要求 |
|------|------|
| `spec/ai-friendly-prd.md` | 每个 REQ 必须有 AC 或明确 `missing_confirmation` |
| `context/requirement-ir.yaml` | AC 必须结构化：`id / statement / source / testability` |
| `context/layer-impact.yaml` | 每个 impact 必须说明影响哪些 AC |
| `plan.md` | 每个实现任务必须引用 REQ-ID 和 AC-ID |
| `agent-pack/verification-plan.md` | 每个 AC 至少有一种验证方式：unit / integration / manual / owner_confirmation |
| `readiness-report.yaml` | AC 不可测时降低 task_executability |

这比单纯“让模型保证质量”更有效，因为它把质量锚点从最终报告前移到 PRD 编译阶段。

### 7. Two-Pass Critic，而不是 PRM

近期不做 Process Reward Model。改成低成本 Two-Pass Critic：

```text
Pass A: 生成步骤产物
Pass B: 只读本步骤产物 + contract + 上一步产物，输出 critique.yaml
Gate: critique.status != fail 才允许进入下一步
```

critique 输出：

```yaml
schema_version: "1.0"
step: "3.2-layer-impact"
status: "pass | warning | fail"
findings:
  - id: "F-001"
    severity: "fatal | warning"
    artifact: "context/layer-impact.yaml"
    issue: "IMP-003 has no requirement_id"
    fix: "Add requirement_id or move item to open questions"
```

只在高风险步骤启用：

- AI-friendly PRD
- Requirement IR
- Layer Impact
- Contract Delta
- Agent Pack

### 8. “跳步”定义为可测试故障

新增 workflow violation taxonomy：

| 类型 | 例子 | 检测方式 |
|------|------|----------|
| `missing_prerequisite` | 有 layer-impact 但无 requirement-ir | step gate |
| `stale_artifact` | plan 引用旧 requirement hash | workflow-state hash |
| `trace_break` | plan task 无 REQ-ID | artifact contract |
| `forbidden_output` | step 2 生成 report.md | step sandbox / diff check |
| `underconsumed_reference` | reference 存在但 graph-context 没用 | quality gate |
| `assumption_promoted` | missing_confirmation 进入确定任务 | contract validator |
| `context_overread` | step 2 读取源码并直接写实现计划 | execution log / state inputs |

每次 gate fail 都按 taxonomy 记录到：

```text
_prd-tools/metrics/workflow-violations.jsonl
```

这能把“模型又乱来了”变成可统计的工程问题。

## Implementation Plan

### Phase 0：先止血

目标：不大改架构，先降低继续调试时的跳步概率。

任务：

1. 恢复 `/reference` Mode Selection Gate，首次构建默认推荐 F→A，但必须等用户确认。
2. 增加 `/prd-distill` Report Review Gate，`report.md` 未确认时不得生成最终 `plan.md`。
3. 在 `reference-step-gate.py` 和 `distill-step-gate.py` 增加 `--write-state`。
4. step gate 通过时写入 `workflow-state.yaml` 的 `current_step` 和 `resume.next_step`。
5. step gate 失败时写入 `status: blocked` 和缺失文件。
6. 在 SKILL.md 中强制每步开始前运行 step gate。
7. 在每个 step 文件顶部增加短 `workflow_state` header 和 `MUST NOT`。

验收：

- 手动删除前置产物时，下一步必须 fail。
- 重跑已完成步骤时，必须提示 unusual rerun。
- `workflow-state.yaml` 能看出当前跑到哪一步。
- `/reference` 在没有用户确认模式前不得开始构建 reference。
- `/prd-distill` 在 `context/report-confirmation.yaml` 未 `approved` 前不得生成最终 `plan.md`。

### Phase 1：Artifact Contract MVP

目标：把核心中间产物从“看起来像”变成“机器可检查”。

任务：

1. 新增 `scripts/validate-artifact.py`。
2. 新增 4 个最关键 contract：
   - `ai-friendly-prd.contract.yaml`
   - `requirement-ir.contract.yaml`
   - `layer-impact.contract.yaml`
   - `contract-delta.contract.yaml`
3. `distill-quality-gate.py` 调用 validator。
4. contract validator 输出 `context/artifact-validation.yaml`。
5. `readiness-report.yaml` 消费 validation 结果。

验收：

- 缺 `ai_prd_req_id` 时 fail。
- `missing_confirmation` 进入 `planning.eligibility: ready` 时 fail。
- `layer-impact` 中 IMP 没有 REQ-ID 时 fail。
- `contract-delta` 多层需求缺 producer/consumer 时 warning 或 fail。

### Phase 2：Context Budget 与步骤拆分

目标：减少上下文过载造成的注意力衰减。

任务：

1. 给每个 distill/reference step 增加 `allowed_inputs` 和 `forbidden_outputs`。
2. 把特别长的步骤拆成“生成”和“核验”两段。
3. 输出 `context/step-inputs.yaml`，记录每步实际消费了哪些文件。
4. quality gate 检查高风险步骤是否过度读取无关文件。

验收：

- Requirement IR 步骤不能依赖源码直接生成实现计划。
- Plan 步骤必须消费 layer-impact 和 contract-delta。
- Report/Plan 不再重复长篇原始 PRD，只引用 REQ-ID 和 evidence。

### Phase 3：Two-Pass Critic

目标：在最容易出错的中间层加入轻量自检。

任务：

1. 新增 `steps/critique-template.md`。
2. 为 5 个高风险产物生成 `context/critique/<step>.yaml`。
3. `distill-workflow-gate.py` 检查 critique fail 时阻断下一步。
4. 将 critique findings 汇总到 readiness-report。

验收：

- 人工制造一个 trace break，critic 能发现。
- critic 只读本步骤相关产物，不扩大上下文。
- warning 不阻断，但必须进入 readiness risks。

### Phase 4：Agent Pack 与验收闭环

目标：把“PRD-to-Code 计划”变成 coding agent 可安全消费的执行包。

对齐 ADR-0010 的 Agent Pack：

```text
agent-pack/
├── implementation-prompt.md
├── task-graph.yaml
├── code-anchor-map.yaml
├── verification-plan.md
├── risk-guardrails.md
└── review-checklist.md
```

新增强约束：

- `task-graph.yaml` 必须是 DAG，不能有循环。
- 每个 task 必须引用 REQ-ID、IMP-ID、AC-ID。
- 每个 task 必须有 `allowed_files` 或 `fallback_reason`。
- 每个 task 必须有 verification。
- blocked / missing_confirmation 只能进入 `risk-guardrails.md` 和 handoff task。

验收：

- Agent Pack 可以直接交给 Claude Code / Codex / Copilot coding agent。
- coding agent 不需要重新阅读全量 PRD 就能执行第一批任务。
- review checklist 能反查每个 AC 是否被验证。

### Phase 5：Benchmark 验证收益

目标：证明这套机制真的减少跳步和低质量输出。

新增指标：

| 指标 | 定义 |
|------|------|
| workflow_order_pass_rate | 所有步骤按顺序完成比例 |
| artifact_contract_pass_rate | 核心产物 contract 通过率 |
| trace_completeness | REQ -> IMP -> task -> AC 链路完整率 |
| assumption_leak_count | missing_confirmation 进入确定任务次数 |
| context_overread_count | 步骤读取超出 allowed_inputs 的次数 |
| rerun_recovery_success | 中断后从 state 恢复成功率 |

至少跑：

```text
benchmarks/cases/gasstation-dxgy
benchmarks/cases/simba-shift-signin-award
benchmarks/cases/dive-customization-xtr-gas-benefits
```

目标阈值：

| 指标 | v2.17 目标 |
|------|------------|
| workflow_order_pass_rate | >= 95% |
| trace_completeness | >= 90% |
| assumption_leak_count | 0 |
| P0 requirement missed | 0 |
| rerun_recovery_success | >= 90% |

## Priority

最有收益的执行顺序：

1. **Workflow State v2**：先让流程可恢复、可观察。
2. **Artifact Contract MVP**：再让中间产物可检查。
3. **Context Budget**：控制降智的主要来源。
4. **Acceptance Criteria 闭环**：把质量锚点前移。
5. **Two-Pass Critic**：只在高风险步骤加，不全流程滥用。
6. **Agent Pack**：最后给 coding agent 稳定消费。
7. **Benchmark**：贯穿每个阶段，作为是否继续加复杂度的依据。

不要优先做：

- 训练 PRM。
- 引入完整 LangGraph runtime。
- 为每个小字段写复杂语义 smell check。
- 在 prompt 里堆越来越多“千万不要”。

## Consequences

收益：

- 跳步从“主观感觉”变成 gate 可捕获的错误。
- 中断恢复有 state，不再靠对话记忆。
- 产物质量从最终人工看报告，前移到每个中间层。
- 上下文预算能直接缓解长流程降智。
- Agent Pack 会更适合交给 Claude Code、Codex、Copilot coding agent 这类执行层。

代价：

- 会新增若干 contract 和 validator，维护成本上升。
- workflow-state hash 会让重跑和手工修改更严格，需要 `--allow-rerun`、`--repair-state` 等逃生口。
- Two-Pass Critic 会增加运行时间，只应放在高风险步骤。

风险与缓解：

| 风险 | 缓解 |
|------|------|
| gate 过严导致调试效率低 | 支持 `--warning-only` 和 `--repair-state`，但默认严格 |
| contract 维护滞后 | contract 和 output-contracts 同步纳入 `validate-contracts.sh` |
| 模型为了过 gate 写形式主义内容 | benchmark 加 false positive penalty，人工审查 golden cases |
| 状态文件与真实文件漂移 | 用 artifact hash 和 `validate-artifact.py --refresh` 修复 |

## References

- [Anthropic, “Building effective agents”](https://www.anthropic.com/research/building-effective-agents)：简单、可组合 workflow pattern 优先于复杂 agent 框架。
- [Anthropic, “Best practices for Claude Code”](https://code.claude.com/docs/en/best-practices)：上下文窗口填满后性能下降，需主动管理上下文。
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)：checkpoint、resume、deterministic replay 是长流程 agent 的关键能力。
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)：使用 JSON Schema / strict structured outputs 提升格式可靠性。
- [Pydantic AI output validation](https://pydantic.dev/docs/ai/core-concepts/output/)：结构化输出可结合 validation 和 retry。
- [AlphaCodium](https://huggingface.co/papers/2401.08500)：代码生成从 prompt engineering 转向 test-based flow engineering。
- [GitHub Spec Kit](https://github.com/github/spec-kit)：spec-driven development 的 `spec -> plan -> tasks` 多阶段流程。
