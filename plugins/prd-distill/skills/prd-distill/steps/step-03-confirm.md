# 步骤 3：计划、报告与反馈

## 目标

生成：

- `_output/prd-distill/<slug>/report.md`
- `_output/prd-distill/<slug>/plan.md`
- `_output/prd-distill/<slug>/questions.md`
- `_output/prd-distill/<slug>/artifacts/reference-update-suggestions.yaml`

## 输入

- `artifacts/evidence.yaml`
- `artifacts/requirement-ir.yaml`
- `artifacts/layer-impact.yaml`
- `artifacts/contract-delta.yaml`
- `references/output-contracts.md` 中 report.md 和 plan.md 的格式定义

## report.md（渐进式披露）

`report.md` 是**给人看的完整分析文档**，采用渐进式披露结构，从结论到细节逐层展开，不需要跳到其他文件就能获取核心信息。

必须包含以下章节：

### 1. 需求摘要（30秒决策）
- 一句话摘要
- 变更类型统计：ADD/MODIFY/DELETE/NO_CHANGE 各几项

### 2. 影响范围
- 命中的层、能力面、关键文件/模块（表格形式）

### 3. 关键结论
- 新增/修改/不改什么，每个结论带 REQ-ID 和代码路径引用

### 4. 变更明细表（核心可操作内容）
- 列出所有 IMP-* 项
- 格式：`| ID | 变更描述 | 类型 | 目标文件 | 验证来源 |`
- 精确到文件路径，标注 code_verified / reference_only

### 5. 字段清单（按功能模块分组）
- 从 requirement-ir 和 contract-delta 中提取
- 格式：`| 字段 | 类型 | 必填 | 来源 | 契约ID |`
- 按业务模块分组（基础信息/活动规则/审核后权益赋值/批量Excel/User Query 等）

### 6. 校验规则
- 从 requirement-ir.rules 中提取可验证的校验规则
- 格式：`| ID | 规则描述 | 错误文案/提示 | 目标文件 |`

### 7. 开发 Checklist（可直接执行）
- 用 `- [ ]` 格式
- 按建议实现顺序排列
- 每项标注具体操作 + 目标文件 + 关联 REQ/IMP/CONTRACT

### 8. 契约风险
- 只列 alignment_status 为 needs_confirmation 或 blocked 的契约

### 9. Top Open Questions
- 最多5个最关键的阻塞问题，带 Q-ID

写作规则：
- 自然语言为主，用 Markdown 表格提高可扫描性
- 每个变更项都带目标文件路径
- 关联 ID（REQ-*/IMP-*/CONTRACT-*）方便跳到 artifacts 查证
- 低置信度项用 ⚠ 标注

职责边界：
- **report.md 是决策文档，不是所有细节的全集**
- 不要把完整 YAML 证据链展开到 report 里，那是 artifacts 的职责
- 不要复制 PRD 原文，只引用 REQ-ID
- 建议总长度控制在 200-400 行（Markdown 源码），超过时优先精简变更明细表和字段清单，不要精简摘要、影响范围和契约风险

## plan.md（可执行的开发操作手册）

`plan.md` 是**拿去就能干活的操作手册**，精确到文件路径和行号。

必须包含以下章节：

### 范围和假设
- 覆盖的 REQ 范围、前置假设和依赖

### 建议实现顺序
- Phase 1 → Phase 2 → Phase 3
- Phase 间标注依赖和前置条件

### 分层任务（只展示命中的层）
每个任务必须包含：
- **具体文件路径**（尽量带行号）
- **操作描述**（做什么）
- **参考实现**（类似功能的已有代码路径）
- **关联** REQ/IMP/CONTRACT
- **验证命令**（grep/go test 等）

用 `- [ ]` checklist 格式，开发人员可以直接勾选。

职责边界：
- **plan.md 是执行文档，不是二次报告**
- 不要重复 report.md 的分析结论，只写"做什么、怎么做"
- 不要复制 PRD 原文
- 不编造行号或命令：不确定时写"约在 XX 附近"或省略行号，不要编造
- 验证命令只给出已确认可用的
- 建议总长度控制在 150-350 行（Markdown 源码），超过时优先精简参考实现描述，不要精简任务清单和 QA 矩阵

### 契约对齐任务
- 格式：`| 契约 | 状态 | 需要确认方 | 确认内容 |`
- 只列 needs_confirmation 和 blocked

### QA 矩阵
- 格式：`| 场景 | 关键检查点 | 关联 REQ | 优先级 |`
- 覆盖正常流 + 边界情况 + 异常流

### 风险和回滚
- 回滚方案
- 观测建议
- 已知坑点

### 回归重点
- 哪些已有功能可能受影响，需要回归验证

## questions.md

只放阻塞问题、需 owner 确认的问题和低置信度假设：

- 问题
- 影响的输出或开发任务
- 建议 owner
- 需要的证据
- 当前建议默认策略

若没有阻塞问题，明确写"暂无阻塞问题"。

职责边界：
- **questions.md 必须保持精简，不能变成垃圾桶**
- 每个问题必须可操作：有明确 owner、影响范围、所需证据
- 不放普通备注、已确认事实、或无行动价值的问题
- 建议总长度控制在 30-80 行（Markdown 源码）

## Reference 回流

生成 `artifacts/reference-update-suggestions.yaml`：

- 新术语、新路由、新契约、新 playbook
- golden sample 候选
- reference 与代码的矛盾

`/prd-distill` 不直接编辑 `_reference/`；实际修改交给 `/build-reference` 的反馈回流。
