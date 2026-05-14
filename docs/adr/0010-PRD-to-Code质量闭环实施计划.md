# ADR-0010：PRD-to-Code 质量闭环实施计划

> **已废弃**：AI-friendly PRD 和 Critique Pass 已在 v2.20 瘦身重构中删除。本 ADR 记录的历史决策不再适用。

| 字段 | 值 |
|------|---|
| 状态 | 计划中 |
| 日期 | 2026-05-11 |
| 目标版本 | v2.16.x / v2.17.0 |
| 触发 | AI-friendly PRD、Requirement IR 对齐、REQ→Code Anchor 强绑定已完成 MVP，需要继续补齐 reference 质量修复、Agent Pack 和 benchmark 闭环 |

## Context

PRD Tools 当前主链路已经形成：

```text
/reference
  -> _prd-tools/reference/
  -> _prd-tools/reference/index/

/prd-distill
  -> _ingest/document.md
  -> spec/ai-friendly-prd.md
  -> context/prd-quality-report.yaml
  -> context/requirement-ir.yaml
  -> context/layer-impact.yaml
  -> context/contract-delta.yaml
  -> report.md / plan.md / portal.html
```

已经完成或基本完成的三个阶段：

1. **AI-friendly PRD Compiler**
   - 原始 PRD 先编译为 `spec/ai-friendly-prd.md`。
   - 产出 `context/prd-quality-report.yaml`。
   - 用 `explicit / inferred / missing_confirmation` 区分确定事实、推断和待确认项。

2. **Requirement IR 对齐**
   - `requirement-ir.yaml` 优先消费 `ai-friendly-prd.md`。
   - requirement 追溯到 `ai_prd_req_id`。
   - `planning.eligibility` 防止 `missing_confirmation` 进入确定开发任务。

3. **REQ → Code Anchor 强绑定**
   - 建立 `REQ-ID -> IMP-ID -> code_anchor -> layer` 的链路。
   - `layer-impact.yaml` 要么给出代码锚点，要么给出 fallback reason。
   - report/plan 不能绕过 requirement/layer-impact 直接编造目标文件。

这三步之后，PRD Tools 已经从“PRD 分析 prompt”演进为一个 PRD-to-code 上下文编译链路。但近期在真实仓库 `dive-bff` 的 `/reference` 测试中暴露了新的问题：

| 问题 | 表现 | 影响 |
|------|------|------|
| reference 被过度 prompt 影响 | 模型在枚举清单里生成了源码之外的内容 | 误导后续 PRD 路由、领域术语和代码锚点判断 |
| reference 产物不完整 | 曾出现只生成部分 YAML、index 为空、portal 缺失 | `/prd-distill` 消费到半成品上下文 |
| Agent Pack 尚未落地 | 目前 report/plan/context 已有，但没有单独面向 coding agent 的执行包 | Claude Code / GLM / Codex / Cursor 仍需自己拼上下文 |
| benchmark 未形成闭环 | 已有 oracle 评分，但还未覆盖 AI-friendly PRD trace、layer、Agent Pack 等新能力 | 无法量化本轮优化是否真的提升 PRD-to-code 质量 |

因此，接下来不应继续堆更多“约束句子”，而应按以下原则推进：

```text
修复 reference 产出诱导
  -> 生成 Agent Pack
  -> 用 benchmark 跑分
  -> 根据分数反推 Compiler / IR / Anchor / Agent Pack
```

## Decision

### 1. 产品定位

PRD Tools 不直接对标自动写完整代码的 coding agent。它应定位为：

> 面向存量业务工程的 PRD Context Compiler + Evidence Gate + Benchmark Harness。

它位于 PRD 和 coding agent 之间：

```text
PRD / 技术方案 / 历史需求 / 源码
        ↓
PRD Tools
        ↓
AI-friendly PRD / Requirement IR / Code Anchors / Contract Delta / Agent Pack
        ↓
Claude Code / Codex / GLM / Cursor / OpenHands
```

### 2. 外部生态坐标

| 方向 | 代表 | 强项 | PRD Tools 的位置 |
|------|------|------|------------------|
| Spec-driven development | GitHub Spec Kit | `spec -> plan -> tasks` 标准链路 | 从真实 PRD、存量代码和契约证据编译出可执行上下文 |
| Coding agent | Claude Code / Codex / Cursor | 读代码、改文件、跑命令 | 提供执行前上下文、风险边界和验收计划 |
| Autonomous engineer | Devin / OpenHands | 长任务执行、PR、环境管理 | 提供任务包和证据链，不替代执行环境 |
| PRD SaaS | ChatPRD 等 | 写 PRD、整理 PRD | 面向工程落地，不做泛文档美化 |

PRD Tools 的差异点不是“直接生成代码”，而是让 coding agent 在动代码前知道：

1. PRD 被读成了什么。
2. 哪些 requirement 是确定的，哪些是推断或待确认。
3. 每条 requirement 影响哪些能力面和代码锚点。
4. 哪些契约、字段、枚举、schema、event 需要 owner 确认。
5. 哪些任务可以执行，哪些只能进入风险/开放问题。
6. 最后输出是否经 benchmark 验证。

### 3. Reference 原则修正

`/reference` 的模板和步骤文档应只要求记录可从源码读取的枚举事实。

#### 3.1 01-codebase.enums

`01-codebase.enums` 只记录源码中能读到的枚举事实。

模板中不再提供额外枚举说明字段。

```yaml
enums:
  CampaignType:
    definition_file: "src/config/constant/campaignType.ts"
    values:
      - name: "GasStation"
        value: 44
```

不在 reference prompt 中反复强调某个禁止项，因为这种反向提示也会把模型注意力拉到错误方向上。正确做法是：模板没有这个字段，步骤文档只说“枚举值从源码读取”。

#### 3.2 Reference 质量优化不是堆 gate

短期不继续往 `reference-quality-gate.py` 增加大量语义 smell check。

原因：

- 质量问题根源在 prompt/模板诱导，不是 gate 不够多。
- gate 过多会让模型产出围着检查项转，进一步降低自然分析质量。
- 当前更需要恢复 `v2.16.1` 那种按源码自然沉淀 reference 的风格。

当前只保留必要门禁：

- 主文件是否存在。
- index 是否生成。
- portal 是否脚本渲染。
- YAML 是否可读。
- schema_version 是否存在。

### 4. Agent Pack

在 reference 恢复稳定后，新增给 coding agent 的执行包。

输出目录：

```text
_prd-tools/distill/<slug>/agent-pack/
├── README.md
├── implementation-prompt.md
├── task-graph.yaml
├── code-anchor-map.yaml
├── verification-plan.md
├── risk-guardrails.md
└── review-checklist.md
```

文件职责：

| 文件 | 职责 |
|------|------|
| `README.md` | Agent Pack 入口说明和阅读顺序 |
| `implementation-prompt.md` | 给 Claude Code / GLM / Codex / Cursor 的执行提示词 |
| `task-graph.yaml` | 从 requirement/layer-impact 生成任务 DAG |
| `code-anchor-map.yaml` | `REQ-ID -> IMP-ID -> code_anchor -> file/symbol/layer/confidence` |
| `verification-plan.md` | 验证命令、手工 QA、契约检查、回滚验证 |
| `risk-guardrails.md` | 不得越界的范围、待确认项、跨层风险 |
| `review-checklist.md` | PR review checklist |

Agent Pack 输入来源：

| 输入 | 用途 |
|------|------|
| `spec/ai-friendly-prd.md` | 标准化需求 |
| `context/prd-quality-report.yaml` | PRD 质量与待确认项 |
| `context/requirement-ir.yaml` | REQ-ID、验收条件、planning eligibility |
| `context/layer-impact.yaml` | IMP-ID、layer、code anchors |
| `context/contract-delta.yaml` | 契约变化和 owner 确认 |
| `context/context-pack.md` | 精简代码上下文 |
| `report.md` | 决策摘要和阻塞项 |
| `plan.md` | 实现计划和 QA 矩阵 |

硬规则：

- `missing_confirmation` 不进入确定实现任务。
- 每个 implementation task 必须引用至少一个 `REQ-ID`。
- 每个 implementation task 必须引用 `IMP-ID` 和 code anchor，或写 fallback reason。
- 跨层契约未确认时，只能生成 handoff/check task。
- `implementation-prompt.md` 必须限制无关重构和无证据实现。

### 5. Benchmark 跑分与反推优化

Benchmark 是本轮闭环的核心。

现有 oracle 评分维度：

- requirement_recall
- code_anchor_accuracy
- blocker_quality
- plan_actionability
- false_positive_penalty

下一步扩展维度：

| 维度 | 说明 |
|------|------|
| ai_prd_traceability | requirement 是否能追溯到 AI-friendly PRD 的 REQ-ID |
| layer_accuracy | BFF/frontend/backend layer 判断是否正确 |
| missing_confirmation_guard | 待确认项是否被挡在确定任务外 |
| agent_pack_actionability | Agent Pack 是否可直接交给 coding agent 执行 |
| anchor_fallback_quality | 找不到代码锚点时 fallback reason 是否合理 |

优先跑现有真实 case：

```text
benchmarks/cases/gasstation-dxgy
benchmarks/cases/simba-shift-signin-award
benchmarks/cases/simba-shift-rider-type
benchmarks/cases/simba-shift-order-scope
benchmarks/cases/dive-rtc-trip-challenge
benchmarks/cases/dive-customization-xtr-gas-benefits
```

反推规则：

| 发现 | 反推优化位置 |
|------|--------------|
| REQ 漏召回 | AI-friendly PRD Compiler / requirement-ir |
| code anchor 漏命中 | context-pack / layer-impact / reference index |
| layer 判错 | reference layer adapters / routing playbooks |
| 假设进入计划 | requirement-ir planning eligibility / Agent Pack gate |
| plan 不可执行 | task-graph / verification-plan |
| blocker 漏报 | report generation / readiness gate |

## Implementation Plan

### Phase 1：Reference 产出质量修复

目标：修复 reference 模板和步骤文档中的产出诱导。

任务：

1. 删除 `01-codebase.yaml` 模板中的额外枚举说明字段。
2. 删除 reference 文档中围绕枚举说明做去重或归类的诱导表达。
3. 保持必要的 completion gate，不新增复杂语义 smell check。
4. 在 `dive-bff` 上重新安装并重跑 `/reference`。

验收：

- 新生成的 `01-codebase.enums.values` 不再出现源码之外的枚举说明字段。
- 不再生成源码之外的枚举项。
- index 和 portal 仍按 v2.16.2 流程生成。
- `reference-quality-gate.py --root .` 不 fail。

### Phase 2：Agent Pack MVP

目标：让 `/prd-distill` 输出可直接交给 coding agent 的执行包。

任务：

1. 更新 prd-distill SKILL/workflow/output-contracts。
2. 新增 agent-pack 输出目录和文件说明。
3. 从 requirement-ir/layer-impact/contract-delta 生成 task-graph 和 code-anchor-map。
4. 生成 implementation-prompt、verification-plan、risk-guardrails、review-checklist。
5. distill-quality-gate 增加最小 Agent Pack 检查。

验收：

- `/prd-distill` 产出 `agent-pack/`。
- implementation task 可追溯到 REQ-ID。
- missing_confirmation 不进入确定实现任务。
- Agent Pack 能直接作为 Claude Code / GLM / Codex 的执行上下文。

### Phase 3：Benchmark 扩展

目标：量化本轮优化收益。

任务：

1. 扩展 oracle score，增加 traceability/layer/agent-pack/missing_confirmation 相关维度。
2. 保持旧 oracle.yaml 兼容。
3. 至少用 1 个 BFF-heavy case 和 1 个 multi-layer case 跑分。
4. 输出回归分析和反推优化建议。

验收：

- `scripts/benchmark.sh lint` 通过。
- 新评分维度不破坏旧 case。
- 至少能定位 3 类优化建议。
- 不出现 P0 requirement missed。

### Phase 4：真实项目回归

目标：在 `dive-bff` 上验证完整链路。

步骤：

```bash
cd /Users/didi/work/prd-tools
bash install.sh /Users/didi/work/dive-bff

cd /Users/didi/work/dive-bff
rm -rf _prd-tools/reference _prd-tools/build
# 重启 Claude/GLM
# 运行 /reference
python3 .prd-tools/scripts/reference-quality-gate.py --root .

# 运行 /prd-distill <真实 PRD>
python3 .prd-tools/scripts/distill-quality-gate.py \
  --distill-dir _prd-tools/distill/<slug> \
  --repo-root .
```

验收：

- reference 产物完整。
- enum 只记录源码中的枚举事实。
- distill 产物完整。
- Agent Pack 可用。
- portal 可打开。

### Phase 5：发版

版本策略：

| 情况 | 版本 |
|------|------|
| 只修 reference 产出诱导 | v2.16.x patch |
| 加入 Agent Pack | v2.17.0 minor |
| benchmark 维度大改且破坏兼容 | v3.0.0 major |

发版前检查：

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache-prd-tools python3 -m py_compile scripts/*.py
bash scripts/validate-contracts.sh
scripts/benchmark.sh lint
git diff --check
```

## Consequences

收益：

- reference 去掉额外枚举说明等产出诱导，减少 AI 补脑。
- Agent Pack 让 prd-distill 输出更容易被 coding agent 直接消费。
- Benchmark 从“看起来不错”转向“真实命中率可度量”。
- PRD Tools 的定位更清晰：不是替代 coding agent，而是给 coding agent 编译上下文和验收边界。

代价：

- Agent Pack 会增加 distill 输出文件数量，需要 portal 和 README 做入口收敛。
- Benchmark 需要持续维护 oracle，否则分数会失真。

风险：

| 风险 | 缓解 |
|------|------|
| reference 仍然编造事实 | 优先修模板和 prompt，必要时再考虑 deterministic skeleton |
| Agent Pack 放大错误上下文 | Agent Pack 必须依赖 requirement/layer-impact/contract-delta，不直接从 PRD 自由生成 |
| benchmark 过拟合 | 使用 branch-backed cases 和真实 PRD 持续扩充 |
| 用户误以为工具会自动写代码 | README 和 Agent Pack 明确：PRD Tools 产出执行上下文，不替代 coding agent |

## References

- GitHub Spec Kit：spec-driven development 的 `spec -> plan -> tasks` 工作流。
- Claude Code / Codex / Cursor：coding agent 执行层。
- OpenHands / Devin：autonomous software engineering 方向。
- PRD Tools `benchmarks/`：当前 oracle benchmark 和 branch-backed cases。
