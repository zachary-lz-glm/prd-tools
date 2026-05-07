# 步骤 2：Layer Impact 与 Contract Delta

## 目标

将 Requirement IR 转成：

- `_prd-tools/distill/<slug>/context/layer-impact.yaml`
- `_prd-tools/distill/<slug>/context/contract-delta.yaml`
- `_prd-tools/distill/<slug>/context/graph-context.md`

## 输入

- `spec/evidence.yaml`
- `spec/requirement-ir.yaml`
- `_prd-tools/reference/project-profile.yaml`，如存在
- `_prd-tools/reference/01-codebase.yaml`
- `_prd-tools/reference/02-coding-rules.yaml`
- `_prd-tools/reference/03-contracts.yaml`
- `_prd-tools/reference/04-routing-playbooks.yaml`
- `_prd-tools/graph/code-graph-evidence.yaml`，如存在（GitNexus）
- `_prd-tools/graph/business-graph-evidence.yaml`，如存在（Graphify）
- v3.1 兼容：`_prd-tools/reference/01-entities.yaml`、`_prd-tools/reference/02-architecture.yaml`、`_prd-tools/reference/03-conventions.yaml`、`_prd-tools/reference/04-constraints.yaml`、`_prd-tools/reference/08-contracts.yaml`、`_prd-tools/reference/09-playbooks.yaml`
- `references/layer-adapters.md`

## 执行

### 图谱上下文构建（始终执行，工具不可用时写 fallback）

1. 先生成 `context/graph-context.md`：
   a. 从 requirement-ir 提取业务实体、字段、枚举、接口、动作词和目标层。
   b. 如 GitNexus 可用，使用 `mcp__gitnexus__query` 找 execution flows 和候选符号。
   c. 对候选符号使用 `mcp__gitnexus__context` 获取 callers/callees/processes/file path。
   d. 对 MODIFY/DELETE 或高风险改动使用 `mcp__gitnexus__impact` 获取 blast radius。
   e. 对 API/route/schema 改动使用 `mcp__gitnexus__api_impact` / `route_map` / `shape_check` 找 consumer 和字段访问。
   f. 如 Graphify 可用，使用 `/graphify query/path/explain` 获取业务关联、设计原理和隐式约束。
   g. 如工具不可用，记录 unavailable reason，并列出实际执行的 `rg`/Read fallback 查询。

`graph-context.md` 必须给每条关键线索分配 GCTX ID，供 plan.md / report.md 引用。

### 基础分析（始终执行）

2. 为每个目标层选择能力面适配器。
3. 对每个 requirement 搜索并读取代码，确认当前状态。
4. 按适配器 surface 记录 Layer Impact。
5. 对每个跨层/API/schema/event/downstream 契约面创建 Contract Delta。
6. 从规范、约束、third rails、契约、playbook 和 `graph-context.md` 中补充风险。

### 代码影响分析（GitNexus 可用时增强）

7. 对每个 requirement 涉及的代码符号：
   a. `mcp__gitnexus__impact <symbol>` 获取爆炸半径。
   b. 将影响的模块和调用链写入 layer-impact.yaml 的 `affected_symbols` 字段。
   c. 如果影响范围超过 5 个模块，提升 `risk_level`。
   d. 记录图谱证据到 spec/evidence.yaml。

### 业务影响分析（Graphify 可用时增强）

8. 对每个 requirement 的业务关键词：
   a. `/graphify path "需求关键词" "受影响模块"` 追踪业务关联路径。
   b. `/graphify explain "变更概念"` 获取设计原理和隐式规则。
   c. 确认变更不会违反 rationale_for 中的设计决策。
   d. 将业务影响和设计约束写入 layer-impact.yaml 的 `business_constraints` 字段。

## 代码锚定规则

- `ADD`：目标行为/符号不存在，有代码搜索支撑。
- `MODIFY`：目标存在，但 requirement 改变行为。
- `DELETE`：PRD 明确移除或废弃行为/契约。
- `NO_CHANGE`：源码证据证明现有行为已满足 requirement。

不要只依赖 reference 的 `implemented` 标记，必须使用代码证据或负向搜索证据。

## 契约规则

以下场景生成 Contract Delta：

- 影响超过一层。
- request/response/schema/event payload 变化。
- 触达外部权益、券、支付、奖励、风控、审计系统。
- producer/consumer 归属不清。

任一侧未验证时，使用 `alignment_status: needs_confirmation`。

## 图谱增强输出

当图谱工具可用时，layer-impact.yaml 增加以下字段：

```yaml
affected_symbols:                     # GitNexus impact 结果
  - symbol: ""
    blast_radius: []
    confidence: 0.0
    graph_provider: "gitnexus"

business_constraints:                 # Graphify 业务关联结果
  - concept: ""
    related_concepts: []
    design_rationale: ""
    risk_if_violated: ""
    graph_provider: "graphify"
```

`graph-context.md` 输出格式见 `references/output-contracts.md`。plan.md 中每个 MODIFY/DELETE 任务必须引用至少一个 GCTX ID；无法引用时，必须在 graph-context 的 fallback/未命中表中说明。
