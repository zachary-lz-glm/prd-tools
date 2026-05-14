<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>6, 7, 8, 9, 10, 11</current_step>
  <allowed_inputs>context/evidence.yaml, context/requirement-ir.yaml, context/graph-context.md, context/layer-impact.yaml, context/contract-delta.yaml, references/output-contracts.md</allowed_inputs>
  <must_not_read_by_default>original long PRD (use requirement-ir instead)</must_not_read_by_default>
  <must_not_produce>context/requirement-ir.yaml (already produced)</must_not_produce>
</workflow_state>

## MUST NOT

- MUST verify ALL prerequisite files exist and are non-empty before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if any prerequisite file is missing

# Phase C — Output: Report, Plan, Quality Gate（Step 6-11）

## 目标

本步骤分为两个阶段，中间必须 HARD STOP。

### 阶段 A — 生成 report.md 后立即暂停

生成以下产物后 **HARD STOP**，写入 `context/report-confirmation.yaml`（status: pending），向用户展示 report 摘要并询问 approved / needs_revision / blocked。

- `_prd-tools/distill/<slug>/report.md`（决策报告 + 阻塞问题）
- `_prd-tools/distill/<slug>/context/report-confirmation.yaml`

**绝对不得在用户回复前生成 plan.md。**

### 阶段 B — 用户 approved 后才继续

仅当 `report-confirmation.yaml` 的 `status: approved` 时，生成：

- `_prd-tools/distill/<slug>/plan.md`（技术方案 + 开发计划）
- `_prd-tools/distill/<slug>/context/reference-update-suggestions.yaml`

## 输入

- `context/evidence.yaml`
- `context/requirement-ir.yaml`
- `context/graph-context.md`
- `context/layer-impact.yaml`
- `context/contract-delta.yaml`
- `references/output-contracts.md`（report.md、plan.md、reference-update-suggestions 格式定义）

**HARD GATE**：以上 5 个 context 文件必须全部存在且非空，才能开始写 report.md。不得用 Agent 异步生成 context 文件的同时写 report——report 必须消费已完成的 context 产物。如果任何前置文件缺失，必须先完成对应上游 Step，不能跳过。

## report.md（需求翻译 + 阻塞问题）

`report.md` 是**需求翻译文档**：回答"PM 到底要什么"。§1-§7 使用纯业务语言，§8 收纳技术细节作为附录。开发者先理解需求，再按需翻阅技术细节。

必须包含以下 9 个章节（不得增删、不得改名、不得加 §x 前缀）：

### 1. 需求摘要（30秒决策）
- 纯业务语言一句话总结：PM 要什么、影响范围多大
- 变更规模统计
- 不超过 5 行
- **不出现**文件路径、API 字段名、枚举值、YAML 代码块

### 2. PRD 内容过滤声明
- ✅ 纳入分析：与当前项目相关的需求范围
- ❌ 已排除：与当前项目无关的需求 + 排除原因
- ⚠️ 需关注但不涉及代码修改：如灰度开关、后端独立处理等

### 3. 需求拆解（核心章节，占 50%+ 篇幅）
- 三栏式表格：`| REQ-ID | PM 想要什么 | 现有系统怎么做 | 需要新增/改什么 | 优先级 | 待确认 |`
- **纯业务语言**：不出现文件路径、API 字段名、枚举值
- 每个 REQ 必须有一行，包括 NO_CHANGE 的
- 已有能力判定标注来源（code_scan / reference / negative_search / inferred / out_of_scope）
- out_of_scope 的 REQ 在"PM 想要什么"写"（本项目不涉及）"，"需要新增/改什么"写排除原因
- 低置信度匹配用 ⚠ 标注

### 4. 业务规则
- 纯业务逻辑表格：`| 规则 | 说明 | 歧义/待确认 | 重要性 |`
- **不出现"前端守/后端守"**——这是技术决策，放在 plan §7

### 5. 影响面概览（粗粒度）
- 模块级表格：`| 影响模块 | 改动类型 | 影响程度 |`
- 不展开具体文件和函数

### 6. 开发 Checklist
- 6.1 开发前必须完成
- 6.2 开发中必须注意
- 6.3 开发后必须验证

### 7. Open Questions & 阻塞问题
- 7.1 Top Open Questions（最多 5 个）
- 7.2 阻塞问题（6 要素）
- 7.3 低置信度假设
- 7.4 Owner 确认项

### 8. 技术附录
- 8.A 源码扫描命中摘要
- 8.B 变更明细表（IMP 清单）
- 8.C 字段清单（按模块分组）
- 8.D 校验规则明细
- 8.E 契约对齐与风险（8.E.1-8.E.5 按 5 层分组，每层至少 1 行或"无变更"）

### 9. Readiness Score
- 评分表 + Decision

### Context Pack 必引用规则

`context/context-pack.md` 中 **🔴 Must-Reference Anchors** 段的每个锚点，必须在以下位置之一出现：

- report.md §8.B（变更明细表）
- plan.md §3（实现计划 / Implementation Checklist）

如果某个 🔴 Must-Reference 锚点无法关联到任何变更，必须在 report.md §7 显式说明原因（如："该锚点已确认不受本 PRD 影响"）。

写作规则：
- §1-§5 使用纯业务语言，不出现文件路径、API 字段名、枚举值、YAML
- §1 不超过 5 行
- §3 占 report 50%+ 篇幅
- §8 技术附录用 `详见 plan Phase X.X` 引用已展开内容，不重复
- 低置信度项用 ⚠ 标注，进入 §7
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索在 §7 和 §8 中保留
- §8.E 每层都要有自己的小段，即使为空也要显式写"无变更"
- 单仓和团队模式一致；团队模式下各子节 IMP 来自对应 `references/{repo}` 的 layer

职责边界：
- **report.md 是需求翻译文档**：回答"PM 到底要什么"
- §1-§7 是业务层，§8 是技术附录层
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责
- 不要复制 PRD 原文，只引用 REQ-ID
- "前端守/后端守"等实现分工不在 report 中出现——那是 plan §7 的职责
- 建议总长度控制在 300-650 行（Markdown 源码）。超限时精简优先级：§8 技术附录 > §5 影响面概览（先精简）；§3 需求拆解 > §7 阻塞问题与线索 > §4 业务规则（不精简）

---

## ⏸ Report Review Gate（HARD STOP）

report.md 生成后、plan.md 生成前，必须暂停：

1. 生成 `context/report-confirmation.yaml`（按 workflow.md Step 7 的格式）
2. 向用户展示 report.md 摘要，等待确认
3. 仅当用户确认 `status: approved` 时继续 Phase 2
4. 如果 `status: needs_revision`：回到上游修复对应 artifacts，重新生成 report.md
5. 如果 `status: blocked`：终止工作流

**不得在 report 未获批准时生成 plan.md。**

---

## plan.md（技术方案 + 开发计划）

`plan.md` 是**可 review 的函数级技术方案文档**，也是**拿去就能干活的操作手册**。必须优先消费代码搜索结果。

必须包含以下 12 个章节（不得增删、不得改名、不得加 §x 前缀）：

### 1. 范围与假设
- **目标**：本方案覆盖的 REQ 范围和预期产出
- **非目标**：明确排除的范围，避免过度设计
- **前置条件与依赖**：需要先完成的基础设施、其他团队接口、外部系统准备

### 2. 整体架构
- **代码坐标**：REQ 到关键函数/结构体/API consumer 的映射表
- **方案概述**：文字描述 + 简单框图
- **核心数据模型**：关键结构体/Schema 用伪代码展示字段结构
- **关键设计决策**：主要 trade-off 和选择理由
- **与现有系统的交互**：调用链、数据流、涉及的已有模块和接口
- **新增文件结构**：如果方案包含新建文件，用树形结构列出新增的目录和文件（如 `src/components/NewCmp/index.tsx`）。只列 ADD 文件，复用 §2.5 映射表中改动类型为 ADD 的行。无新增文件时写"无新增文件"

### 2.5 需求→文件映射（全景图）
- 表格：`| # | 需求点 | 影响文件 | 改动类型 | 优先级 | Plan 章节 |`
- 与 report §3 需求拆解形成闭环：每个需求点都有对应的代码落点
- 开发者一眼看到全貌
- "需求点"使用业务语言（与 report §3 一致）
- 新建文件标注 **(新建)**

### 3. 实现计划
每个任务必须包含：
- **文件路径:行号**（尽量带行号，不确定时标注"约在 XX 附近"）
- **改动类型**: MODIFY | ADD | DELETE
- **当前代码**: 从源码提取的关键片段（ADD 任务写"—"）
- **目标代码**: 修改后的代码（DELETE 任务写"—"）
- **受影响调用方**: 列出所有调用点，标注需改/不需改
- **关键函数/结构体**（入口函数、validator、service 等）
- **代码依据**（GCTX/EV ID）
- **关联** REQ/IMP/CONTRACT
- **验证命令**（grep/go test 等）

`当前代码`和`目标代码`从源码提取，不是凭空写的。新建文件无法给当前代码时，给出参考的同类文件路径。
用 `- [ ]` checklist 格式，按 Phase 分组，Phase 间标注前置条件。

### 4. API 设计
- Schema 变更
- 接口变更：`| 接口 | 方法 | 变更类型 | 字段变更 |`
- 外部服务调用

### 5. 数据存储
- 表/索引变更
- 缓存变更
- Migration 要点

### 6. 配置与开关
- Feature Flag
- 灰度策略

### 7. 校验规则汇总（分层矩阵）
- 必须分 7.1 前端 / 7.2 BFF / 7.3 后端 三个小节，每节至少 1 行或显式"无"
- `| 规则 ID | 规则描述 | 目标文件 | 错误文案 | 前端守 | 后端守 |`
- "前端守/后端守"在此处体现，不在 report 中出现

### 8. QA 矩阵
- `| # | 场景 | 测试路由 | 操作步骤 | 预期结果 | 关联 REQ | 优先级 |`
- **测试路由**：具体的 URL path 或页面路径（如 `/create?source_entry=lucky_wheel`）
- **操作步骤**：1. xxx 2. xxx 3. xxx 的步骤序列，可复制的测试路径
- P0/P1/P2 分级

### 9. 契约对齐（全栈视图）
- `| 契约ID | Producer | Consumers | Checked By | 状态 | 需确认内容 |`

### 10. 风险与回滚
- **10.1 风险登记表**：`| # | 风险 | 影响范围 | 缓解措施 | 监控信号 |`
  - 每个风险必须有"缓解措施"——可执行的具体动作，不是"需确认"
  - 缓解措施示例："前端先用 mock 开发"、"优先出 schema 设计再编码"、"回归测试覆盖 type=12 现有功能"
- **10.2 回滚方案**：逐 Phase 回滚步骤，标注最大风险点的回滚策略
- **10.3 观测建议**：需关注的 metric、日志、报警
- **10.4 已知坑点**：源码线索暗示的潜在问题
- **10.5 回归范围**：哪些已有功能可能受影响

### 11. 工作量估算

必须包含 11.1 模块估算表 + 11.2 排期建议。

**11.1 模块估算表**：按 §3 每个 Phase 一行
- `| Phase | 任务数 | 复杂度 | 估算 | 依赖 | 可并行 |`
- "任务数" = 该 Phase 的 `- [ ]` checklist 项数
- "复杂度" = S(仅改配置/枚举) / M(改逻辑+测试) / L(新组件+新接口) / XL(多模块联动)
- "估算" = 基于复杂度的天级范围：S=0.5天, M=1-2天, L=2-4天, XL=3-5天
- "依赖" = 前置 Phase 编号
- "可并行" = 标注无依赖可同时进行的 Phase 编号

**11.2 排期建议**（一段文字）：
- 关键路径：串行依赖链中最长的路径
- 并行切割点：依据 Phase 依赖关系标注可并行的阶段
- 总估算：`单人 X-Y 天 / N人并行 X'-Y' 天`
- 外部阻塞点：后端接口、设计稿等非团队可控依赖

写作规则：
- **§2.5 映射表必须完整**：每个 REQ 都有对应行
- **§3 任务必须包含当前/目标代码**：从源码提取，不是凭空写的
- **§3 受影响调用方必须列出所有调用点**：标注需改/不需改
- **§8 QA 矩阵必须包含测试路由和操作步骤**
- **代码线索不可省略**：每个任务必须保留文件路径、行号、参考结构体名等线索
- 不编造行号或命令：不确定时写"约在 XX 附近"
- 验证命令只给出已确认可用的

职责边界：
- **plan.md 是可 review 的技术方案，不是二次报告**
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"
- 不要重复 report §8 技术附录的细节——report 已展开的用 `详见 report §8.X` 引用
- 不要复制 PRD 原文
- 技术细节的 SSOT：plan §3-§4 为实现细节权威源；report §8 为概览级
- 建议总长度控制在 300-700 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > §2.5 映射表 > QA 矩阵 > 风险与回滚（不精简）

**团队模式 plan 生成**：

`team-plan.md`（团队级总览，7-section）：
1. 范围与假设（目标、跨仓依赖、成员仓角色表）
2. 跨仓架构（代码坐标按 repo 分组、跨仓调用链）
3. 跨仓时序（Phase 依赖图、每仓里程碑）
4. Sub-Plan 索引表（| 仓 | Sub-Plan 文件 | IMP 数 |）
5. 契约对齐全栈视图
6. 风险与回滚
7. 工作量总览

`plans/plan-{repo}.md`（成员仓 sub-plan）：
- 复用标准 12-section plan 模板（含 §2.5 映射表）
- Scope 限定到单个成员仓
- IMP 从 `layer-impact.yaml` 该仓对应层提取
- 文件名动态生成：`team_repos[].repo` → `plan-{repo}.md`

**禁止硬编码**：sub-plan 文件名必须从 `team_repos[].repo` 动态生成。

## Reference 回流

生成 `context/reference-update-suggestions.yaml`：

- 新术语、新路由、新契约、新 playbook
- golden sample 候选
- reference 与代码的矛盾
- 跨仓契约、owner、handoff 或团队级知识库候选

每条 suggestion **必须填满以下字段**（按 schema v2.0）：

```yaml
- id: REF-UPD-XXX
  type: "<枚举>"                      # 6 选 1: new_term/new_route/new_contract/new_playbook/contradiction/golden_sample_candidate
  target_file: "_prd-tools/reference/<xxx>.yaml"
  summary: "一句话说明这条建议做什么"
  current_repo_scope:
    authority: "single_repo"
    action: "<枚举>"                   # 3 选 1: apply_to_current_repo/record_as_signal/needs_owner_confirmation
  owner_to_confirm: ["<owner>"]
  team_reference_candidate: true|false
  team_scope:                         # 当 team_reference_candidate=true 时必填
    type: "<枚举>"
    related_repos: []
    aggregation_status: "candidate"
  priority: "high|medium|low"
  confidence: "high|medium|low"
  evidence: ["EV-001"]
  proposed_patch: ""
```

**禁止简化为 `{id, target_file, section, action, description, reason}` 6 字段**。

**团队公共库候选判定**：
- 契约影响 2+ 个仓 → `type=contract, team_reference_candidate=true`
- 术语首次出现且为全团队业务概念 → `type=domain_term, team_reference_candidate=true`
- 否则 → `team_reference_candidate=false`

`/prd-distill` 不直接编辑 `_prd-tools/reference/`；实际修改交给 `/reference` 的反馈回流。

## Self-Check（生成后必须逐项验证）

> **Self-Check 的两种条目**：本清单同时包含 (a) **机器可验证断言**（标 `[M]`）和 (b) **人工判读提示**（标 `[H]`）。执行 Self-Check 时：
> - `[M]` 条目必须逐条列出 `verify: <命令>` 与 `expect: <结果>`，未通过不得进下一步。
> - `[H]` 条目作为判读提示，LLM 自检后必须写入 workflow-state.yaml 的 `self_check_notes[step_id]` 数组，内容为"我为什么认为这条满足"的简短解释。

- [ ] [M] report.md 包含全部 9 个章节（§1-§9，注意 §8 含 5 个附录子节）
- [ ] [M] plan.md 包含全部 12 个章节（§1-§11 + §2.5，§11 工作量估算可选）
- [ ] [M] report.md §8.E 含 5 个子节（8.E.1 前端 / 8.E.2 BFF / 8.E.3 后端 / 8.E.4 外部 / 8.E.5 跨层风险），即使某层无变更也要显式写"无变更"
- [ ] [M] plan.md §9 全栈表包含 Producer/Consumers/Checked By 三列
- [ ] [M] plan.md §7 含 7.1/7.2/7.3 三个小节，每节至少 1 行或显式"无"
- [ ] [M] plan.md §3 含 Implementation Checklist 段（至少 5 个 `- [ ]` 任务）
- [ ] [M] plan.md §3 含 Verification Commands 段（至少 3 条命令）
- [ ] [M] report.md §7 每个 blocker 含 owner + suggestion + risk + mitigation 中至少 3 项
- [ ] [M] 每个 IMP 在 report.md §8.B 变更明细表中有对应行
- [ ] [M] report.md §3 覆盖所有 REQ（requirement-ir 中的每条 REQ 都有对应行）
- [ ] [M] plan.md §2.5 需求→文件映射表覆盖所有 REQ（每个 REQ 有对应行）
- [ ] [M] 每个 Phase 在 plan.md §3 中有 checklist 格式的任务
- [ ] [M] 每个 MODIFY/DELETE 任务引用了至少一个 GCTX ID
- [ ] [H] report.md §1-§5 不含文件路径、API 字段名、枚举值、YAML 代码块
- [ ] [H] report.md §4 业务规则不含"前端守/后端守"列
- [ ] [H] plan.md §3 每个任务包含当前代码/目标代码/受影响调用方
- [ ] [H] plan.md §8 QA 矩阵包含测试路由和操作步骤列
- [ ] [H] reference-update-suggestions.yaml 的 current_repo_scope.action 与证据来源匹配
- [ ] [M] report.md 长度在 300-650 行范围内（超出时按优先级精简）
- [ ] [M] plan.md 长度在 300-700 行范围内（超出时按优先级精简）

**团队模式 Self-Check**：
- `[M]` `team-plan.md` 存在且包含 Sub-Plan 索引表
- `[M]` `plans/` 目录存在
- `[M]` 每个 `layer-impact.yaml` 中有 IMP 的成员仓，`plans/plan-{repo}.md` 存在
- `[M]` sub-plan 文件名与 `team_repos[].repo` 一致
