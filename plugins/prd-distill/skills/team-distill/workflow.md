# team-distill 工作流

> Step 0-2（PRD Ingestion、Evidence、Requirement IR）与单仓模式相同，详见 `skills/prd-distill/workflow.md`。
> 本文件只描述团队模式与单仓的差异步骤。

## 目标

面向多仓库团队的 PRD 蒸馏：从各仓库 reference 原样副本生成跨仓影响分析和分仓库开发计划。

前置：`project-profile.yaml` 含 `layer: "team-common"` 或 `references/` 目录存在。

---

## Step 0-2：同单仓

PRD Ingestion → Evidence → Requirement IR，流程同 `skills/prd-distill/workflow.md`。

额外消费：
- 各仓 `references/{repo}/05-domain.yaml`：术语，用于 requirement-ir 术语对齐。
- 各仓 `references/{repo}/02-coding-rules.yaml`：fatal 规则，在 requirement-ir 中标记相关规则。

## Step 3：Layer Impact（团队模式）

### 3.1 Graph Context（从 Reference 读取）

**禁止执行 rg/glob 命令** — 团队仓没有源码。

对每个 REQ 的扫描流程：

1. 读取各仓 `references/{repo}/01-codebase.yaml` 的模块/枚举/实体，匹配 PRD 相关内容。
2. 对每个 REQ，匹配涉及的仓库和角色（从 03-contracts 的 producer/consumer 关系推断）。
3. 需要契约细节时，读 `references/{repo}/03-contracts.yaml`。
4. 需要路由信息时，读 `references/{repo}/04-routing-playbooks.yaml`。

自动识别涉及仓库：将 PRD requirement 的关键词与各仓的 04-routing-playbooks 和 01-codebase 模块名匹配，确定每个 REQ 涉及哪些仓库及角色（producer/consumer/middleware）。

GCTX entry 标记 `source: "team_reference"`，附带 `repo` 字段。

### 3.2 Layer Impact 生成

4 层 IMP 从各仓 reference 填充。每层的 `code_anchors` 指向对应仓库的 reference 文件路径。

confidence 规则：
- `medium`（默认，未直接验证源码）
- `high`（被多个仓库 reference 交叉验证时）

## Step 3.5：Context Pack

从 `references/{repo}/index/` 加载多仓 index：

```bash
python3 .prd-tools/scripts/context-pack.py \
  --distill _prd-tools/distill/<slug> \
  --team-references references \
  --out _prd-tools/distill/<slug>/context/context-pack.md
```

## Step 4：Contract Delta（团队模式）

跨仓视角：
- 从各仓 `references/{repo}/03-contracts.yaml` 读取 producer/consumer 信息，构建跨仓契约全景。
- consumer 调用的 endpoint 在其他仓声明为 producer → 标记 cross_repo 契约，`alignment_status: needs_confirmation`。
- 每条 delta 的 `consumers[]` 跨仓填充。

## Step 5：Plan（团队模式）

生成 `team-plan.md` + N 份 `plans/plan-{repo}.md`。

成员仓列表从 `project-profile.yaml` 的 `team_repos[]` 读取。涉及的仓库和角色从各仓 03-contracts.yaml 自动推断。

**team-plan.md 结构**：
1. **范围与假设**：目标、跨仓依赖、成员仓角色表
2. **涉及仓库总览**：按 repo 分组的代码坐标、跨仓调用链、关键设计决策
3. **跨仓时序**：Phase 1-N 跨仓依赖图、每个仓的交付里程碑
4. **Sub-Plan 索引表**：列出所有 sub-plan 文件名 + 对应仓 + IMP 数
5. **契约对齐（跨仓）**：从 contract-delta.yaml 提取跨仓契约摘要
6. **风险与回滚**：跨仓联调风险、回滚策略
7. **工作量总览**：按仓汇总

**plans/plan-{repo}.md**：复用标准 11-section plan 模板，scope 限定到单个成员仓。

文件名从 `team_repos[].repo` 动态生成，禁止硬编码。

## Step 8：Report（团队模式）

report.md §10 强制 5 个子节：
- §10.1 Frontend：前端层 IMP 和契约
- §10.2 BFF：BFF 层 IMP 和契约
- §10.3 Backend：后端层 IMP 和契约
- §10.4 External：外部系统影响
- §10.5 跨层对齐风险：`consumers - checked_by` 不为空 / `alignment_status: blocked` 等

## Step 8.1-8.5：同单仓

Report Review Gate、Final Quality Gate 流程同单仓模式。

Quality Gate 团队模式检查 `team-plan.md` + `plans/` 目录（而非 `plan.md`）。

## Step 7：Reference 回流（团队模式）

额外触发条件：
- 发现跨仓契约、owner、handoff 或团队级术语候选，但当前仓不能独立确认。
- `team_reference_candidate: true` 标记为团队知识库收集候选。
