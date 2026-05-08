# ADR-0009：PRD Tools 产品化 MVP 落地计划

| 字段 | 值 |
|------|---|
| 状态 | 已收敛到 v2.0 当前分支 |
| 版本 | v2.0 增量产品化 |
| 日期 | 2026-05-08 |
| 触发 | 近期 GitHub 热榜显示 Agent Skills、Spec-Driven Development、MCP、上下文工程和 AI 变更审查工具快速升温；PRD Tools 需要从内部工作流升级为可度量、可安装、可复用、可对外表达价值的产品 |

> 说明：本文最初按 3.0 major 计划撰写。后续决策是先把高收益、低平台化成本的能力落到当前 v2.0 分支：`readiness-report.yaml`、`.prd-tools/status.sh`、`_prd-tools/STATUS.md` 和静态 dashboard。Eval Harness、MCP / Agent API 继续作为后续路线，不作为当前版本门槛。

## Context（为什么做）

PRD Tools 当前已经具备两个关键能力：

1. `/reference`：把项目结构、业务术语、跨层契约、开发打法和历史经验沉淀到 `_prd-tools/reference/`。
2. `/prd-distill`：把单个 PRD 蒸馏为 `report.md`、`plan.md`、`spec/`、`context/`、`tasks/`，并通过 evidence 机制约束结论来源。

这套能力已经能解决真实业务项目中的 PRD-to-code 问题，但产品化程度不足：

| 问题 | 当前表现 | 对使用方的影响 |
|------|----------|----------------|
| 定位不够尖锐 | README 仍偏"工具集"描述 | 用户难以一句话理解 PRD Tools 相比普通 AI agent 的差异 |
| 收益不够量化 | GitNexus、Graphify、Reference 的贡献散落在输出里 | 用户只感知到"跑得慢/文件多"，不容易看到多发现了哪些风险 |
| 输出缺少状态入口 | 需要人工翻 `report.md`、`plan.md`、YAML | TL/PM/QA 无法 30 秒判断这次结果是否可用 |
| 评测体系缺失 | 没有 golden PRD 对比 | 无法回答"准确性提升多少、图谱值不值得跑" |
| 生态入口不足 | 主要依赖 Claude Code skill | 其他 agent、CI、Copilot/MCP 难以消费 `_prd-tools/` |
| 安装残留影响体验 | 旧 `/build-reference`、旧目录、全局 skill 缓存可能干扰 | 新用户或迁移用户容易跑到旧流程 |

近期 GitHub 热榜和生态信号说明，市场正在向以下方向收敛：

| 生态方向 | 代表项目/趋势 | 对 PRD Tools 的启发 |
|----------|---------------|----------------------|
| Agent Skills / slash workflow | `addyosmani/agent-skills` 等项目把工程流程拆为稳定命令 | PRD Tools 应把 `/reference`、`/prd-distill` 做成稳定、可解释、可组合的工作流入口 |
| Spec-Driven Development | GitHub Spec Kit、OpenSpec、Spec Kitty 等强调 `spec -> plan -> tasks` | PRD Tools 应兼容 SDD 输出形态，但保留 evidence、contract delta、reference 回流优势 |
| Context Engineering | `design.md` 等把 agent 上下文做成 repo-native、可 lint、可 diff 的文件 | `_prd-tools/reference/` 应被定位为 PRD-to-code 的上下文编译结果，而不是普通文档 |
| MCP 标准化 | MCP Registry 和 GitHub Copilot MCP 支持成为外部上下文入口 | PRD Tools 应规划 MCP Server，让 Reference、Distill、Metrics 可被多个 agent 消费 |
| AI 变更审查 | `hunk` 等项目关注 agent 变更可审查性 | PRD Tools 应输出 readiness、contract risk、blocking questions，成为 coding 前的审查门 |
| 结构化文档索引 | PageIndex 等强调长文档结构索引和导航 | 历史 PRD、技术方案和团队经验应从简单文件扫描升级为可度量的 reference/context 索引 |

因此，本轮产品化的核心不是"再加一个分析文件"，而是把 PRD Tools 从内部 workflow 升级成：

> 面向存量工程的 PRD Context Compiler：把 PRD、历史需求、源码、代码图谱、业务图谱、契约和交付经验，编译成可被人、AI agent、CI 和 MCP 消费的工程上下文与执行包。

## Decision（做什么）

### 1. 产品定位

产品化对外定位统一为：

> PRD Tools 是面向存量业务工程的 PRD-to-code 上下文编译器和风险评估器。

它不直接承诺"自动写完代码"，而是承诺在写代码前给出：

1. PRD 被读成了什么。
2. 需求影响哪些层、哪些能力面、哪些关键文件/符号。
3. 哪些契约、字段、枚举、schema、event、外部接口需要 owner 确认。
4. 哪些结论有 PRD/源码/图谱/人工证据，哪些只是低置信度假设。
5. 开发、测试、联调和回滚应按什么顺序执行。
6. 哪些新知识值得回流到项目 reference。

3.0 的一句话价值表达：

> 让 AI 在动代码前先知道改哪、影响谁、风险在哪、证据是什么。

### 2. 产品能力版图

产品化路线分为 6 个能力面，其中前 4 个优先落在 v2.0 当前分支，后 2 个作为后续扩展：

| 能力面 | 用户感知入口 | 核心产物 | 价值 |
|--------|--------------|----------|------|
| Reference Compiler | `/reference` | `_prd-tools/reference/`、`_prd-tools/build/` | 把项目长期知识编译成可复用上下文 |
| PRD Distiller | `/prd-distill` | `_prd-tools/distill/<slug>/` | 把单个 PRD 编译成 report/plan/spec/context/tasks |
| Readiness Scoring | `readiness-report.yaml`、`metrics/latest.yaml` | 分数、风险、证据覆盖、图谱增益 | 量化本次输出是否可用于研发 |
| Status Dashboard | `.prd-tools/status.sh`、`_prd-tools/STATUS.md`、`_prd-tools/dashboard/index.html` | 项目状态、最近一次 distill、阻塞项 | 30 秒判断当前项目是否就绪 |
| Eval Harness | `eval/`、`prd-tools eval` | golden cases、对比报告 | 量化工具收益和准确性 |
| MCP / Agent API | `prd-tools mcp`（规划） | reference/search/distill/readiness tools | 让 Codex、Claude、Copilot、CI 消费 PRD Tools |

### 3. 统一输出目录

当前版本继续使用 `_prd-tools/` 作为唯一输出根目录，并新增 `dashboard/` 与 readiness 相关约定。`metrics/`、`eval/` 是后续评测路线的预留约定。

```text
_prd-tools/
├── STATUS.md                              # 人类可读项目状态面板
├── README.md                              # 产出索引
├── reference/                             # 长期知识库
├── build/                                 # reference 运行报告
│   └── graph/
├── distill/
│   └── <slug>/
│       ├── report.md
│       ├── plan.md
│       ├── readiness-report.yaml          # 本次 PRD 蒸馏可用性评分
│       ├── spec/
│       ├── context/
│       ├── tasks/
│       └── _ingest/
├── metrics/
│   ├── latest.yaml                        # 最近一次运行的指标快照
│   └── history.jsonl                      # 每次 reference/distill/eval 的指标流水
└── dashboard/
    └── index.html                         # 可选，本地静态 dashboard
```

输出职责：

| 文件 | 职责 | 生成方 |
|------|------|--------|
| `_prd-tools/STATUS.md` | 当前项目一屏状态：reference、graph provider、最近 distill、阻塞项、下一步；适合终端、PR 和留档 | `.prd-tools/status.sh` 或 skill 收尾 |
| `_prd-tools/metrics/latest.yaml` | 最近一次运行指标，供 CLI/CI/MCP 读取 | `/reference`、`/prd-distill`、`prd-tools status` |
| `_prd-tools/metrics/history.jsonl` | 指标历史流水，支持趋势分析 | 每次工具运行 append |
| `_prd-tools/distill/<slug>/readiness-report.yaml` | 单次 PRD 的可执行性评分和风险解释 | `/prd-distill` |
| `_prd-tools/dashboard/index.html` | 本地静态可视化页面；与 STATUS.md 同源，适合浏览器快速扫状态 | `.prd-tools/status.sh` |

### 4. Readiness Scoring

3.0 必须把"这次产出是否可用"变成显式评分，而不是只在报告里散落描述。

#### 4.1 单次 PRD readiness

`_prd-tools/distill/<slug>/readiness-report.yaml` 格式：

```yaml
schema_version: "2.0"
tool_version: "<current VERSION>"
generated_at: "2026-05-08T00:00:00Z"
distill_slug: "<slug>"
status: "pass | warning | fail"
score: 0
summary:
  decision: "ready_for_dev | needs_owner_confirmation | blocked"
  top_reason: ""
scores:
  prd_ingestion:
    score: 0
    status: "pass | warning | fail"
    factors:
      extraction_quality: "pass | warn | block"
      media_unreviewed_count: 0
      table_warning_count: 0
  evidence_coverage:
    score: 0
    requirement_count: 0
    requirements_with_prd_evidence: 0
    requirements_with_code_or_negative_search: 0
    low_confidence_requirement_count: 0
  graph_context:
    score: 0
    gitnexus_available: false
    graphify_available: false
    gctx_count: 0
    provider_added_findings:
      gitnexus: 0
      graphify: 0
  contract_alignment:
    score: 0
    aligned_count: 0
    needs_confirmation_count: 0
    blocked_count: 0
  task_executability:
    score: 0
    task_count: 0
    tasks_with_target_files: 0
    tasks_with_verification: 0
    tasks_with_graph_or_code_context: 0
risks:
  blockers: []
  needs_confirmation: []
  low_confidence_assumptions: []
next_actions:
  - ""
```

评分建议：

| 维度 | 权重 | 说明 |
|------|------|------|
| PRD 读取质量 | 20 | `_ingest/extraction-quality.yaml`、图片/表格风险 |
| 证据覆盖 | 25 | 每个 REQ 是否有 PRD 证据、源码或负向搜索 |
| 图谱上下文 | 15 | GitNexus/Graphify 是否提供可消费 GCTX |
| 契约对齐 | 25 | `blocked`、`needs_confirmation` 数量和严重度 |
| 任务可执行性 | 15 | tasks 是否有目标文件、上下文、验证命令 |

状态阈值：

| 分数 | 状态 | 含义 |
|------|------|------|
| 85-100 | `pass` | 可进入研发，仍需处理普通确认项 |
| 60-84 | `warning` | 可以评审，但必须先确认 top risks |
| 0-59 | `fail` | 不建议进入开发，需补 PRD、owner 或源码证据 |

硬性降级规则：

| 条件 | 强制状态 |
|------|----------|
| `extraction-quality.status = block` | `fail` |
| 任一 P0 contract 为 `blocked` | `fail` |
| 多层需求但没有 `contract-delta.yaml` | `fail` |
| `report.md` 缺少阻塞项章节 | `warning` |
| `tasks/` 缺少目标文件或验证命令 | `warning` |

#### 4.2 Graph Provider 增益量化

产品化输出需要显式回答"GitNexus / Graphify 值不值得跑"。

`readiness-report.yaml` 和 `metrics/latest.yaml` 中记录：

```yaml
provider_value:
  gitnexus:
    available: true
    evidence_count: 0
    affected_symbols_count: 0
    api_consumers_found: 0
    findings_used_by_plan: 0
    added_value:
      - "发现 /api/foo 的 3 个 consumer"
      - "定位 SymbolA -> SymbolB 调用链"
  graphify:
    available: true
    evidence_count: 0
    business_constraints_found: 0
    historical_patterns_found: 0
    findings_used_by_plan: 0
    added_value:
      - "发现该 PRD 与历史 CourierDxGy playbook 相似"
      - "发现业务术语 A 与外部系统 B 存在隐式关联"
```

产品口径：

| Provider | 产品定位 | 不负责 |
|----------|----------|--------|
| GitNexus | 代码结构图谱：符号、调用链、API consumer、影响半径 | 业务规则正确性 |
| Graphify | 业务语义图谱：概念、历史需求、隐式约束、设计原理 | 源码事实最终确认 |
| Reference | 精选治理层：确认后的长期知识和开发打法 | 原始全量图谱 |

### 5. Status Dashboard

当前版本新增 `.prd-tools/status.sh`，优先以 shell 脚本落地，后续可包装为 CLI。

#### 5.1 命令目标

在任意项目根目录执行：

```bash
bash .prd-tools/status.sh
```

输出：

```text
PRD Tools Status

Install
  version: <current VERSION>
  command: /reference ok
  skills: reference / prd-distill ok

Reference
  status: exists | missing | stale
  health: pass | warning | fail | unknown
  last_quality_score: 86

Graph Providers
  gitnexus: available | missing | stale
  graphify: available | missing | stale

Latest Distill
  slug: station-new-driver-coupon
  readiness: warning (78)
  blockers: 0
  needs_confirmation: 3
  tasks: 8

Next Actions
  1. Confirm CTR-008 with backend owner
  2. Run /reference Mode E after delivery
```

同时生成 `_prd-tools/STATUS.md` 和 `_prd-tools/dashboard/index.html`。两者共用同一个脚本推导的数据：Markdown 是稳定文本入口，HTML 是可视化入口，不作为另一份事实来源。

`_prd-tools/STATUS.md` 示例：

```markdown
# PRD Tools Status

## 1. Project Readiness
...

## 2. Latest Distill
...

## 3. Provider Value
...

## 4. Next Actions
...
```

#### 5.2 状态来源

| 状态项 | 来源 |
|--------|------|
| 安装版本 | `.prd-tools-version` |
| skills | `.claude/skills/reference`、`.claude/skills/prd-distill`；`/reference` 由 skill name 提供 |
| reference 是否存在 | `_prd-tools/reference/` |
| reference 质量 | `_prd-tools/build/quality-report.yaml`、`health-check.yaml` |
| GitNexus | `.gitnexus/` |
| Graphify | `graphify-out/graph.json` |
| 最近 distill | `_prd-tools/distill/*/readiness-report.yaml` 或目录 mtime |
| 阻塞项 | `readiness-report.yaml`、`report.md`、`contract-delta.yaml` |
| metrics | `_prd-tools/metrics/latest.yaml` |

### 6. Eval Harness

3.0 要把"收益"从主观感受变成可复盘数据。

#### 6.1 目录结构

```text
eval/
├── README.md
├── cases/
│   └── <case-id>/
│       ├── input/
│       │   ├── prd.md
│       │   ├── tech-doc.md
│       │   └── repo-notes.md
│       ├── expected/
│       │   ├── requirements.yaml
│       │   ├── contract-delta.yaml
│       │   ├── affected-files.yaml
│       │   └── blocking-questions.yaml
│       └── config.yaml
├── runs/
└── run-eval.sh
```

#### 6.2 首批评测用例

| Case | 类型 | 目标 |
|------|------|------|
| `bff-new-campaign-type` | BFF 新活动类型 | 验证枚举、schema、上游契约、preview、batch import 是否被召回 |
| `frontend-form-field-change` | 前端表单字段 | 验证 UI/schema/client validation/QA matrix |
| `backend-contract-change` | 后端接口字段 | 验证 DTO、service、DB、event、consumer 对齐 |
| `multi-layer-coupon-reward` | 多层权益/券需求 | 验证 contract delta 和 owner confirmation |
| `image-heavy-prd` | 图片/表格重 PRD | 验证 ingestion warning 和 block 策略 |

#### 6.3 指标

| 指标 | 计算方式 | 目标 |
|------|----------|------|
| Requirement Recall | 命中的 expected requirements / expected total | >= 0.85 |
| Contract Delta Recall | 命中的 expected contracts / expected total | >= 0.85 |
| Affected File Recall | 命中的 expected files / expected total | >= 0.75 |
| False Assumption Count | 无证据高置信度结论数量 | <= 2 |
| Evidence Coverage | 有 PRD/源码/负向搜索证据的结论比例 | >= 0.9 |
| Task Executability | 有目标文件、上下文、验证命令的 task 比例 | >= 0.8 |
| Blocking Question Precision | blocking questions 中真实阻塞比例 | >= 0.75 |

#### 6.4 Provider 消融实验

每个 case 至少跑 4 组：

| 组别 | Reference | GitNexus | Graphify | 目的 |
|------|-----------|----------|----------|------|
| Baseline | off | off | off | 纯 PRD + rg/Read |
| Reference only | on | off | off | 验证长期知识库收益 |
| GitNexus | on | on | off | 验证代码图谱收益 |
| Full | on | on | on | 验证双图谱 + reference 总收益 |

输出对比：

```yaml
case_id: "bff-new-campaign-type"
baseline:
  readiness_score: 62
  contract_recall: 0.55
full:
  readiness_score: 87
  contract_recall: 0.9
delta:
  readiness_score: "+25"
  contract_recall: "+0.35"
  graph_added_findings: 8
```

### 7. MCP / Agent API 路线

3.0 不要求一次实现完整 MCP Server，但必须在契约层预留。

#### 7.1 Tool 规划

| MCP Tool | 输入 | 输出 | 用途 |
|----------|------|------|------|
| `get_reference` | section / query | reference 片段 | 让 coding agent 获取项目长期知识 |
| `search_reference` | query | matched facts + evidence | 语义检索 reference |
| `get_contracts` | route / keyword | contracts + status | 查字段/接口契约 |
| `get_latest_readiness` | slug optional | readiness report | 让 CI/agent 判断是否可开发 |
| `distill_prd` | PRD path/text | distill output path | 触发 PRD 蒸馏 |
| `get_graph_context` | requirement / slug | GCTX 条目 | 给 coding agent 精准代码坐标 |

#### 7.2 API 边界

MCP Tool 只读取 `_prd-tools/` 和项目源码，不默认写业务代码。

允许写入：

- `_prd-tools/distill/`
- `_prd-tools/build/`
- `_prd-tools/metrics/`
- `_prd-tools/STATUS.md`

禁止默认写入：

- 业务源码
- 其他仓库
- 全局配置

### 8. 版本与迁移策略

原计划采用一次 major bump；当前决策是先同步到 `v2.0` 分支，用增量方式落地已验证的产品化能力：

| 项 | 决策 |
|----|------|
| 版本号 | 沿用当前 `VERSION`，不单独开 3.0 |
| 分支 | `v2.0` |
| 旧入口 | `/build-reference` 不再作为正式入口，仅作为旧残留清理对象 |
| 旧目录 | `_reference/`、`_output/` 只兼容读取，不作为新输出 |
| 新目录 | `_prd-tools/` 是唯一正式输出根 |
| 安装 | `install.sh` 清理项目和全局旧 `build-reference` skill |
| doctor | 检查全局旧 skill、项目旧产物、新 reference 状态 |

迁移规则：

| 检测到 | 行为 |
|--------|------|
| `.claude/skills/build-reference` | doctor 报错，install 清理 |
| `~/.claude/skills/build-reference` | doctor 报错，install 清理 |
| `_reference/` | status 标记为 legacy output，提示重新跑 `/reference` |
| `_output/` | status 标记为 legacy output，提示迁移或删除 |
| `_prd-tools/reference/` 不存在 | status 下一步提示 `/reference` |

### 9. 分阶段落地计划

#### Phase 0：产品定义和契约锁定

目标：先把产品化 MVP 做什么写清楚，防止边做边漂。

| 任务 | 文件 | 验收 |
|------|------|------|
| 新增本 ADR | `docs/adr/0009-PRD-Tools-3.0产品化落地计划.md` | ADR 覆盖定位、输出、评分、status、eval、MCP、路线 |
| 更新 ADR 索引 | `docs/adr/README.md` | 0009 可点击 |
| 更新 CHANGELOG 草案 | `CHANGELOG.md` | 当前版本条目列出已落地能力 |

完成标准：

- ADR 被合并。
- 后续实施 PR 必须引用本 ADR。

#### Phase 1：输出契约和安装体验

目标：让用户重新安装后不会跑旧流程，并能看到 `_prd-tools/` 输出目录和评分契约。

| 任务 | 文件 | 验收 |
|------|------|------|
| 版本号保持一致 | `VERSION`、两个 plugin.json、marketplace | 版本一致性校验通过 |
| 清理旧入口残留 | `install.sh`、`doctor.sh` | 全局/项目 build-reference 都会被提示或清理 |
| 输出契约新增 readiness/metrics/status | 两份 `output-contracts.md` | `validate-contracts.sh` 通过 |
| SKILL 流程要求生成 readiness | `prd-distill/SKILL.md`、`workflow.md`、step 文件 | 完成标准包含 readiness |
| reference 收尾要求更新 STATUS | `reference/SKILL.md`、`workflow.md` | `/reference` 完成后说明 status |

完成标准：

- `bash -n install.sh scripts/doctor.sh` 通过。
- `scripts/validate-contracts.sh` 通过。
- 本地安装到测试项目后 doctor 显示无 legacy skill。

#### Phase 2：status/dashboard 最小可用版

目标：用户不用翻 YAML，也能知道项目是否 ready。

| 任务 | 文件 | 验收 |
|------|------|------|
| 新增 status 脚本 | `scripts/status.sh` | 可在项目根目录运行 |
| install 复制 status | `install.sh` | 安装后 `.prd-tools/status.sh` 存在 |
| 生成 STATUS.md | `scripts/status.sh` | `_prd-tools/STATUS.md` 生成 |
| README 增加三分钟检查 | `README.md` | 新用户知道先跑 doctor/status |

完成标准：

- `bash .prd-tools/status.sh` 输出安装、reference、graph、latest distill、next actions。
- 没有 `_prd-tools/` 时不失败，只给 next actions。
- 有旧 `_reference/` / `_output/` 时明确提示 legacy。

#### Phase 3：readiness 评分落地

目标：每次 `/prd-distill` 都能量化可用性和风险。

| 任务 | 文件 | 验收 |
|------|------|------|
| 定义 readiness 模板 | `output-contracts.md` | schema 完整 |
| step 要求生成 readiness | `step-03-confirm.md` 或 workflow | report/plan 后必须生成 |
| metrics latest/history | workflow + status | 最近一次 distill 会写 metrics |
| provider value 摘要 | `graph-context.md` + readiness | GitNexus/Graphify 贡献可见 |

完成标准：

- 真实 PRD distill 输出 `readiness-report.yaml`。
- report.md 中有 "Readiness / Provider Value" 摘要。
- status 能读取最近 readiness。

#### Phase 4：Eval Harness（后续）

目标：回答"工具到底提升多少准确性和收益"。

| 任务 | 文件 | 验收 |
|------|------|------|
| 新增 eval 目录 | `eval/` | README + cases 结构存在 |
| 首批 golden case | `eval/cases/*` | 至少 3 个 case |
| eval runner | `eval/run-eval.sh` | 能生成对比报告 |
| 消融实验文档 | `eval/README.md` | baseline/reference/gitnexus/full 说明清楚 |

完成标准：

- 至少一个真实项目 case 能跑出 baseline vs full 对比。
- 输出指标覆盖 requirement recall、contract recall、evidence coverage、false assumptions。

#### Phase 5：MCP 和 CI 集成（后续）

目标：让 PRD Tools 从 Claude Code skill 升级为 agent/CI 可消费的上下文服务。

| 任务 | 文件 | 验收 |
|------|------|------|
| MCP server 设计 | `docs/adr/0010-*.md` 或 `docs/mcp.md` | tool schema 明确 |
| 最小 MCP 实现 | `mcp/` 或 `scripts/mcp-*` | 能读取 reference/readiness |
| GitHub Action 设计 | `.github/workflows/` 文档或模板 | PR 可评论 readiness |
| CI strict 模式 | `doctor.sh --strict`、`status.sh --strict` | 自动化可判定失败 |

完成标准：

- 外部 agent 能通过 MCP 读取 reference 和 readiness。
- CI 能在 PR 里报告 PRD readiness 和 contract risk。

### 10. 验收指标

产品化 MVP 必须满足：

| 指标 | 目标 |
|------|------|
| 安装成功后旧 `/build-reference` 文件层残留 | 0 |
| 新输出目录 | 100% 使用 `_prd-tools/` |
| doctor 必需项误报 | 0 个已知场景 |
| status 无产物项目运行 | 不报错，给 next actions |
| readiness schema | 每次 `/prd-distill` 必须生成 |
| provider value | GitNexus/Graphify 可用时必须列出贡献 |
| contract validation | `scripts/validate-contracts.sh` 通过 |
| shell syntax | `bash -n install.sh scripts/doctor.sh scripts/status.sh` 通过 |

后续完整产品化目标：

| 指标 | 目标 |
|------|------|
| Golden case 数量 | >= 5 |
| Requirement Recall | >= 0.85 |
| Contract Delta Recall | >= 0.85 |
| Evidence Coverage | >= 0.9 |
| False Assumption Count | <= 2 / case |
| Task Executability | >= 0.8 |
| Full vs Baseline readiness 提升 | >= +15 分（目标，不作为硬门禁） |

### 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| readiness 评分被误解为绝对正确率 | 用户把分数当成质量保证 | 文档明确：score 是工程就绪度，不是 PRD 正确率 |
| Graphify 慢导致用户不用 | 业务图谱价值无法体现 | provider_value 明确列出 Graphify 多发现的历史模式/隐式规则 |
| 输出文件继续膨胀 | 用户阅读负担加重 | `STATUS.md` 和 `readiness-report.yaml` 做入口，report/plan 保持渐进式披露 |
| MCP 过早实现导致维护成本上升 | 分散 MVP 重点 | 当前版本先锁 schema 和 status，MCP 放 Phase 5 |
| eval case 难维护 | 指标失真 | 只维护少量高价值 golden case，优先真实历史 PRD |
| 旧目录兼容导致新旧混淆 | 用户继续读 `_reference/` | status/doctor 明确标 legacy，新输出只写 `_prd-tools/` |

### 12. 不在当前 MVP 范围

| 不做 | 原因 |
|------|------|
| 自动修改业务代码 | PRD Tools 定位是 context compiler + readiness gate |
| 团队级中央知识库 | 先把单仓 reference 和指标稳定 |
| 完整 Web App | 先用 `STATUS.md` 和静态 dashboard |
| 强依赖 Graphify/GitNexus | 它们是增强 provider，核心流程必须能降级 |
| 云端服务 | 当前优先本地 repo-native，保护业务代码和 PRD 数据 |

## Consequences（影响）

### 正向影响

| 维度 | 收益 |
|------|------|
| 产品表达 | 从"两个 skill"升级为"PRD Context Compiler" |
| 用户体验 | 用户能通过 status/readiness 直接判断能不能进入开发 |
| 可量化收益 | 能比较 baseline/reference/gitnexus/full 的准确性和召回 |
| 生态扩展 | 为 MCP、CI、GitHub Action、其他 agent 消费打基础 |
| 内部治理 | 输出契约、版本、旧入口迁移更可控 |

### 成本

| 成本 | 说明 |
|------|------|
| 契约复杂度上升 | 新增 readiness、metrics、status，需要校验防漂移 |
| 维护脚本增加 | `status.sh`、eval runner、未来 MCP server 都需要测试 |
| 文档更长 | 需要通过 README 的速读区和产出目录做渐进式阅读 |
| 评分口径需要迭代 | 第一版 readiness 可能需要根据真实项目校准 |

### 决策边界

产品化路线的核心交付顺序必须是：

1. 先锁产品定位和输出契约。
2. 再做 status/readiness 这类用户可感知能力。
3. 再做 eval 证明收益。
4. 最后做 MCP/CI 扩展。

不得一开始就投入大而全的平台化实现。

## References

- [GitHub Spec Kit](https://github.github.com/spec-kit/index.html) — Spec-Driven Development 的 `spec -> plan -> tasks` 参考。
- [OpenSpec](https://github.com/ZeeBJ/OpenSpec-7D) — repo-native spec/change folder 思路。
- [Spec Kitty](https://github.com/Priivacy-ai/spec-kitty) — kanban/worktree/review 式 spec 工作流。
- [agent-skills](https://github.com/addyosmani/agent-skills) — Agent Skills 和 slash workflow 产品化参考。
- [design.md](https://github.com/google-labs-code/design.md) — repo-native agent context、YAML tokens + Markdown rationale 参考。
- [MCP Registry](https://modelcontextprotocol.io/registry/about) — MCP 元数据与工具生态参考。
- [GitHub MCP 文档](https://docs.github.com/en/copilot/concepts/context/mcp) — Copilot 扩展外部上下文的 MCP 使用方式。
- [PageIndex](https://github.com/VectifyAI/PageIndex) — 长文档结构索引和导航思路。
- [hunk](https://github.com/modem-dev/hunk) — agent-authored changesets 审查体验参考。
- ADR-0005 Agent-Skills 融合落地方案。
- ADR-0006 图谱融合与知识库架构。
- ADR-0008 install.sh 职责拆分。
