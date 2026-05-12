<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>2</current_step>
  <allowed_inputs>context/evidence.yaml, context/requirement-ir.yaml, _prd-tools/reference/, context/query-plan.yaml</allowed_inputs>
  <must_not_read_by_default>report.md, plan.md, original long PRD</must_not_read_by_default>
  <must_not_produce>report.md, plan.md</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

# 步骤 2：Layer Impact 与 Contract Delta

## 目标

将 Requirement IR 转成：

- `_prd-tools/distill/<slug>/context/layer-impact.yaml`
- `_prd-tools/distill/<slug>/context/contract-delta.yaml`
- `_prd-tools/distill/<slug>/context/graph-context.md`

## 输入

- `context/evidence.yaml`
- `context/requirement-ir.yaml`
- `_prd-tools/reference/`（**必须消费**，如存在）：
  - `project-profile.yaml`：项目元数据。
  - `01-codebase.yaml`：模块、注册点、数据流——作为源码扫描的代码地图。
  - `02-coding-rules.yaml`：fatal 级规则——layer-impact 必须检查是否触及。
  - `03-contracts.yaml`：现有契约——作为 contract-delta 基线。
  - `04-routing-playbooks.yaml`：路由表——确定每个 REQ 的 target_surfaces。
  - v3.1 兼容：`01-entities.yaml`、`02-architecture.yaml`、`03-conventions.yaml`、`04-constraints.yaml`、`08-contracts.yaml`、`09-playbooks.yaml`
- `context/query-plan.yaml`（如步骤 2.5 已生成，**必须消费**）
- `references/layer-adapters.md`

## 执行

### 源码上下文构建（Reference-First，始终执行）

**⚠ 强制：必须先消费 reference 再扫描源码。禁止跳过 reference 直接 grep。**

1. 先生成 `context/graph-context.md`：
   a. **阶段 1 — Reference 路由**（必须先执行）：
      - 从 requirement-ir 提取业务实体、字段、枚举、接口、动作词和目标层。
      - 将关键词与 `04-routing-playbooks.yaml` 的 `prd_routing` 匹配，确定 target_surfaces。
      - 从 `01-codebase.yaml` 提取匹配的 modules、registries、data_flows，获得精确文件路径。
      - 检查 `02-coding-rules.yaml` 中是否有相关 fatal 规则，记录为必检项。
      - 如存在 `query-plan.yaml`，读取 `matched_entities` 获取预匹配代码锚点。
   b. **阶段 2 — Index 精确扫描**（index 存在时优先）：
      - 对 query-plan.yaml 中 confidence=high 的 matched_entities，直接 Read 源码确认。
      - 对 confidence=low 的实体用 `rg` 验证是否为噪音。
   c. **阶段 3 — 补充扫描**（仅覆盖阶段 1-2 未命中的部分）：
      - 使用 `rg`/`glob` 搜索源码中**未被 reference/index 覆盖**的符号、文件和 execution flows。
      - 使用 `Read` 读取命中文件，获取 callers/callees/processes/file path。
   d. 对 MODIFY/DELETE 或高风险改动用 `rg` 追踪引用链，评估 blast radius。
   e. 对 API/route/schema 改动用 `rg` 搜索 consumer 和字段访问模式。
   f. 记录实际执行的搜索查询、命中结果和 **reference 消费记录**（从哪些 reference 文件提取了哪些路由/规则/实体）。
   g. 每条线索标注来源：`reference_routing` | `index_query` | `code_scan`。

`graph-context.md` 必须给每条关键线索分配 GCTX ID，供 plan.md / report.md 引用。

### 基础分析（始终执行）

2. 为每个目标层选择能力面适配器。
3. 对每个 requirement 搜索并读取代码，确认当前状态。
4. 按适配器 surface 记录 Layer Impact。
5. 对每个跨层/API/schema/event/downstream 契约面创建 Contract Delta。
6. 从规范、约束、third rails、契约、playbook 和 `graph-context.md` 中补充风险。

### 代码影响分析

7. 对每个 requirement 涉及的代码符号：
   a. 用 `rg` 追踪引用链获取影响范围。
   b. 将影响的模块和调用链写入 layer-impact.yaml 的 `affected_symbols` 字段。
   c. 如果影响范围超过 5 个模块，提升 `risk_level`。
   d. 记录证据到 context/evidence.yaml。

### 业务影响分析

8. 对每个 requirement 的业务关键词：
   a. 用 `rg`/`glob` 搜索 reference 和代码中的业务关联。
   b. 确认变更不会违反 rationale_for 中的设计决策。
   c. 将业务影响和设计约束写入 layer-impact.yaml 的 `business_constraints` 字段。

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

## 输出

`graph-context.md` 输出格式见 `references/schemas/03-context.md`。plan.md 中每个 MODIFY/DELETE 任务必须引用至少一个 GCTX ID；无法引用时，必须在 graph-context 的 fallback/未命中表中说明。

## Self-Check（生成后必须逐项验证）
- [ ] 每个 IMP-* 项的 surface 使用 layer-adapters.md 中定义的能力面名称
- [ ] MODIFY/DELETE 类型的 IMP 有源码证据（不只是 reference 标记）
- [ ] ADD 类型有 negative_code_search 证据或参考实现路径
- [ ] graph-context.md 中每个 GCTX 条目都被 plan.md 或 report.md 引用
- [ ] Contract Delta 只在跨层/API/外部系统场景生成
- [ ] alignment_status 为 needs_confirmation 的契约列出了需要确认的内容
