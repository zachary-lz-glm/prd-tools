<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>8, 8.1-confirm, 5, 6, 7, 8.5, 8.6</current_step>
  <allowed_inputs>context/evidence.yaml, context/requirement-ir.yaml, context/graph-context.md, context/layer-impact.yaml, context/contract-delta.yaml, references/schemas/</allowed_inputs>
  <must_not_read_by_default>original long PRD (use requirement-ir instead)</must_not_read_by_default>
  <must_not_produce>context/requirement-ir.yaml (already produced)</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

# 步骤 3：计划、报告与反馈

## 目标

**Phase 1 — Report 生成：**

- `_prd-tools/distill/<slug>/report.md`（决策报告 + 阻塞问题）

**⏸ HARD STOP：生成 `context/report-confirmation.yaml`，暂停等用户确认。仅当 `status: approved` 时才继续 Phase 2。**

**Phase 2 — Plan 生成（仅当 report approved）：**

- `_prd-tools/distill/<slug>/plan.md`（技术方案 + 开发计划）
- `_prd-tools/distill/<slug>/context/reference-update-suggestions.yaml`

## 输入

- `context/evidence.yaml`
- `context/requirement-ir.yaml`
- `context/graph-context.md`
- `context/layer-impact.yaml`
- `context/contract-delta.yaml`
- `references/schemas/04-report-plan.md`（report.md + plan.md 格式定义）
- `references/schemas/03-context.md`（reference-update-suggestions schema）

## report.md（渐进式披露 + 阻塞问题）

`report.md` 是**给人看的完整分析文档**，采用渐进式披露结构，从结论到细节逐层展开，最后以阻塞问题收尾。不需要跳到其他文件就能获取核心信息。

必须包含以下 12 个章节（不得增删、不得改名、不得加 §x 前缀）：

### 1. 需求摘要（30秒决策）
- 一句话摘要
- 变更类型统计：ADD/MODIFY/DELETE/NO_CHANGE 各几项

### 2. PRD 质量摘要
来自 `context/prd-quality-report.yaml`：
- AI-friendly PRD 总分和状态（pass / warning / fail）
- source 分布：explicit / inferred / missing_confirmation 各多少条
- 关键缺失项和风险摘要

### 3. 源码扫描命中摘要
- 列出代码搜索命中的关键函数/调用链/API consumer
- 每条命中引用 GCTX/EV ID，并说明用于哪些 REQ/IMP/CONTRACT

### 4. 影响范围
- 命中的层、能力面、关键文件/模块（表格形式）

### 5. 关键结论
- 新增/修改/不改什么，每个结论带 REQ-ID、代码路径和证据引用

### 6. 变更明细表（核心可操作内容）
- 列出所有 IMP-* 项
- 格式：`| ID | 变更描述 | 类型 | 目标文件 | 关键函数/符号 | 验证来源 |`
- 精确到文件路径和关键 symbol，标注 code_verified / graph_verified / reference_only

### 7. 字段清单（按功能模块分组）
- 从 requirement-ir 和 contract-delta 中提取
- 格式：`| 字段 | 类型 | 必填 | 来源 | 契约ID |`
- 按业务模块分组

### 8. 校验规则
- 从 requirement-ir.rules 中提取可验证的校验规则
- 格式：`| ID | 规则描述 | 错误文案/提示 | 目标文件 |`

### 9. 开发 Checklist（可直接执行）
- 用 `- [ ]` 格式
- 按建议实现顺序排列
- 每项标注具体操作 + 目标文件 + 关联 REQ/IMP/CONTRACT

### 10. 契约对齐与建议
- 按受影响层分组列出（10.1 前端 / 10.2 BFF / 10.3 后端 / 10.4 外部 / 10.5 跨层风险）
- 每层都要有自己的小段，即使为空也要显式写"无变更"

### 11. Top Open Questions
- 最多5个最关键的阻塞问题，带 Q-ID

### 12. 阻塞问题与待确认项

#### 12.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

#### 12.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。

#### 12.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。

如无阻塞问题，显式写"当前无阻塞问题"。

写作规则：
- 自然语言为主，用 Markdown 表格提高可扫描性
- 每个变更项都带目标文件路径
- 关联 ID（REQ-*/IMP-*/CONTRACT-*）方便跳到 context/ 查证
- 低置信度项用 ⚠ 标注，进入 §12.2
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留，这些对开发定位问题有极高价值

职责边界：
- **report.md 是决策文档，不是所有细节的全集**
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责
- 不要复制 PRD 原文，只引用 REQ-ID
- 建议总长度控制在 300-650 行（Markdown 源码）。超限时精简优先级：字段清单 > 校验规则（先精简）；代码命中摘要 > 变更明细表 > 阻塞问题与线索 > 契约风险 > 影响范围（不精简）

---

## ⏸ Report Review Gate（HARD STOP）

report.md 生成后、plan.md 生成前，必须暂停：

1. 生成 `context/report-confirmation.yaml`（按 workflow.md 步骤 8.1 的格式）
2. 向用户展示 report.md 摘要，等待确认
3. 仅当用户确认 `status: approved` 时继续 Phase 2
4. 如果 `status: needs_revision`：回到上游修复对应 artifacts，重新生成 report.md
5. 如果 `status: blocked`：终止工作流

**不得在 report 未获批准时生成 plan.md。**

---

## plan.md（技术方案 + 开发计划）

`plan.md` 是**可 review 的函数级技术方案文档**，也是**拿去就能干活的操作手册**。必须优先消费代码搜索结果。

必须包含以下 11 个章节（不得增删、不得改名、不得加 §x 前缀）：

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

### 3. 实现计划
每个任务必须包含：
- **具体文件路径**（尽量带行号，不确定时标注"约在 XX 附近"）
- **关键函数/结构体**（入口函数、validator、service、repository、consumer 等）
- **操作描述**（做什么）
- **调用链影响**（入口 -> 当前函数 -> 下游函数/consumer）
- **代码依据**（GCTX/EV ID；引用代码搜索证据）
- **参考实现**（类似功能的已有代码路径）
- **关联** REQ/IMP/CONTRACT
- **验证命令**（grep/go test 等）

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
- `| 规则 ID | 规则描述 | 目标文件 | 错误文案 | 来源 |`

### 8. QA 矩阵
- `| 场景 | 关键检查点 | 关联 REQ | 优先级 |`
- P0/P1/P2 分级

### 9. 契约对齐（全栈视图）
- `| 契约ID | Producer | Consumers | Checked By | 状态 | 需确认内容 |`

### 10. 风险与回滚
- 回滚方案
- 观测建议
- 已知坑点：源码线索暗示的潜在问题
- 回归范围

### 11. 工作量估算
- `| 模块 | 估算 | 说明 |`

写作规则：
- **代码线索不可省略**：每个任务必须保留文件路径、行号、参考结构体名等线索
- 不编造行号或命令：不确定时写"约在 XX 附近"
- 验证命令只给出已确认可用的

职责边界：
- **plan.md 是可 review 的技术方案，不是二次报告**
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"
- 不要复制 PRD 原文
- 建议总长度控制在 300-700 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）

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

- [ ] [M] report.md 包含全部 12 个章节（§1-§12）
- [ ] [M] plan.md 包含全部 11 个章节（§1-§11，§11 工作量估算可选）
- [ ] [M] report.md §10 含至少 4 个小段（前端/BFF/后端/外部），即使某层无变更也要显式写"无"
- [ ] [M] plan.md §9 全栈表包含 Producer/Consumers/Checked By 三列
- [ ] [M] plan.md §7 含 7.1/7.2/7.3 三个小节，每节至少 1 行或显式"无"
- [ ] [M] plan.md 含 Implementation Checklist 段（至少 5 个 `- [ ]` 任务）
- [ ] [M] plan.md 含 Verification Commands 段（至少 3 条命令）
- [ ] [M] report.md §12 每个 blocker 含 owner + suggestion + risk + mitigation 中至少 3 项
- [ ] [M] 每个 IMP 在 report.md §5 变更明细表中有对应行
- [ ] [M] 每个 Phase 在 plan.md §3 中有 checklist 格式的任务
- [ ] [M] 每个 MODIFY/DELETE 任务引用了至少一个 GCTX ID
- [ ] [H] reference-update-suggestions.yaml 的 current_repo_scope.action 与证据来源匹配
- [ ] [M] report.md 长度在 300-650 行范围内（超出时按优先级精简）
- [ ] [M] plan.md 长度在 300-700 行范围内（超出时按优先级精简）
