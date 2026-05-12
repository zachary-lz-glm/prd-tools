<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>3</current_step>
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

生成：

- `_prd-tools/distill/<slug>/report.md`（决策报告 + 阻塞问题）
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

必须包含以下章节：

### 1. 需求摘要（30秒决策）
- 一句话摘要
- 变更类型统计：ADD/MODIFY/DELETE/NO_CHANGE 各几项

### 2. 影响范围
- 命中的层、能力面、关键文件/模块（表格形式）

### 3. 代码命中摘要
- 列出代码搜索命中的关键函数/调用链/API consumer
- 每条命中引用 GCTX/EV ID，并说明用于哪些 REQ/IMP/CONTRACT

### 4. 关键结论
- 新增/修改/不改什么，每个结论带 REQ-ID、代码路径和证据引用

### 5. 变更明细表（核心可操作内容）
- 列出所有 IMP-* 项
- 格式：`| ID | 变更描述 | 类型 | 目标文件 | 关键函数/符号 | 验证来源 |`
- 精确到文件路径和关键 symbol，标注 code_verified / graph_verified / reference_only

### 6. 字段清单（按功能模块分组）
- 从 requirement-ir 和 contract-delta 中提取
- 格式：`| 字段 | 类型 | 必填 | 来源 | 契约ID |`
- 按业务模块分组

### 7. 校验规则
- 从 requirement-ir.rules 中提取可验证的校验规则
- 格式：`| ID | 规则描述 | 错误文案/提示 | 目标文件 |`

### 8. 开发 Checklist（可直接执行）
- 用 `- [ ]` 格式
- 按建议实现顺序排列
- 每项标注具体操作 + 目标文件 + 关联 REQ/IMP/CONTRACT

### 9. 契约风险
- 只列 alignment_status 为 needs_confirmation 或 blocked 的契约

### 10. Top Open Questions
- 最多5个最关键的阻塞问题，带 Q-ID

### 11. 阻塞问题与待确认项

#### 11.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（如 `proxy/bpm.go:311 注释暗示冲单挑战系统已存在`）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

#### 11.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。

#### 11.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。

如无阻塞问题，显式写"当前无阻塞问题"。

写作规则：
- 自然语言为主，用 Markdown 表格提高可扫描性
- 每个变更项都带目标文件路径
- 关联 ID（REQ-*/IMP-*/CONTRACT-*）方便跳到 context/ 查证
- 低置信度项用 ⚠ 标注，进入 §11.2
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留，这些对开发定位问题有极高价值

职责边界：
- **report.md 是决策文档，不是所有细节的全集**
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责
- 不要复制 PRD 原文，只引用 REQ-ID
- 建议总长度控制在 300-650 行（Markdown 源码）。超限时精简优先级：字段清单 > 校验规则（先精简）；代码命中摘要 > 变更明细表 > 阻塞问题与线索 > 契约风险 > 影响范围（不精简）

## plan.md（技术方案 + 开发计划）

`plan.md` 是**可 review 的函数级技术方案文档**，也是**拿去就能干活的操作手册**。必须优先消费代码搜索结果。

必须包含以下 12 个章节：

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

### 7. 校验规则汇总
- `| 规则 | 层 | 目标文件 | 错误提示 |`

### 8. QA 矩阵
- `| 场景 | 关键检查点 | 关联 REQ | 优先级 |`
- P0/P1/P2 分级

### 9. 契约对齐
- `| 契约 | 状态 | Producer | Consumer | 需确认内容 |`

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
- 建议总长度控制在 300-600 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）

## Reference 回流

生成 `context/reference-update-suggestions.yaml`：

- 新术语、新路由、新契约、新 playbook
- golden sample 候选
- reference 与代码的矛盾
- 跨仓契约、owner、handoff 或团队级知识库候选

每条建议必须按 `references/schemas/03-context.md` 中 reference-update-suggestions schema 标注 `current_repo_scope`。当前仓可验证的事实才能标记为 `apply_to_current_repo`；其他仓实现细节、跨仓 owner、团队级 taxonomy 必须标记为 `record_as_signal` 或 `needs_owner_confirmation`，并填写 `owner_to_confirm`。`team_reference_candidate: true` 只表示未来团队知识库候选。

`/prd-distill` 不直接编辑 `_prd-tools/reference/`；实际修改交给 `/reference` 的反馈回流。

## Self-Check（生成后必须逐项验证）
- [ ] report.md 包含全部 11 个章节（§1-§11）
- [ ] plan.md 包含全部 11 个章节（§1-§11，§11 工作量估算可选）
- [ ] 每个 IMP 在 report.md §5 变更明细表中有对应行
- [ ] 每个 Phase 在 plan.md §3 中有 checklist 格式的任务
- [ ] 每个 MODIFY/DELETE 任务引用了至少一个 GCTX ID
- [ ] reference-update-suggestions.yaml 的 current_repo_scope.action 与证据来源匹配
- [ ] report.md 长度在 300-650 行范围内（超出时按优先级精简）
- [ ] plan.md 长度在 300-700 行范围内（超出时按优先级精简）
