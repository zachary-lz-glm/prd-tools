<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>2.5, 3.1, 3.2, 3.5, 3.6, 4</current_step>
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

#### 扫描范围兜底：build/ 和 dist/

除 `src/` 外，必须额外扫描仓库的已编译产物目录（`build/`、`dist/`、`lib/` — 按项目实际 `project-profile.yaml` 的 build_output_dirs 决定；如果 `project-profile.yaml` 不存在或缺少 `build_output_dirs`，默认扫描 `build/` 和 `dist/`（如存在））。目的：发现历史上实现过但已从 `src/` 移除的 registry 型改动（CampaignType 枚举、switch case、previewRewardType 映射等）。

**强制规则**：
- 对 registry 型改动（枚举、switch 新增 case、映射表新增 key），`code_scan` 必须在 `build/` 和 `src/` 各跑一遍。
- 若在 `build/` 发现**同 type_id / 同 key 但不同 name** 的既有实现，必须在 OQ 顶置一条：
  `OQ-CODE-NAMING: "历史实现 name={build_name}（见 build/path:L），PRD 提议 name={prd_name}。是否复用历史 name？"`
- 若 `build/` 和 `src/` 存在内容不一致（例如 `build/` 有但 `src/` 无），evidence.yaml 必须增加一条 `EV-CODE-BUILD-*` 记录此事实，并在 `graph-context.md` 的 §"历史残留" 段落说明。

`graph-context.md` 必须给每条关键线索分配 GCTX ID，供 plan.md / report.md 引用。

### 基础分析（始终执行）

2. 为每个目标层选择能力面适配器。
3. 对每个 requirement 搜索并读取代码，确认当前状态。
4. 按适配器 surface 记录 Layer Impact。

### 四层影响强制分析

对每个 requirement，**必须按下列顺序分别判断 4 层**：

1. **frontend 影响**：这个需求会让前端 UI / 组件 / 表单 / 路由 / 客户端契约产生什么变化？
2. **bff 影响**：同上
3. **backend 影响**：即使本地没有后端仓，只要 PRD 提到数据/接口/枚举/校验/预算等后端职责，就必须生成 `IMP-BE-*` 条目
4. **external 影响**：涉及第三方系统（券、折扣卡、Push、DMS、权益、风控等）必须生成 `IMP-EXT-*`

**硬规则**：
- 4 个 layer key 必须同时存在于 layer-impact.yaml
- 空数组要显式写 `capability_areas: []` 并加 comment 说明理由
- 非当前仓层的 IMP confidence 不得 high，必须 needs_confirmation
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

- 每条 delta 的 `consumers` 必须是数组，至少包含 1 个除 producer 之外的层
- 同一契约影响多端时（如新增 endpoint 同时改前端调用 + 后端实现），**必须生成一条 delta 含 `consumers: [frontend, backend]`**，禁止拆成两条单边 delta
- 已对齐的层放入 `checked_by`，未对齐的层差集进入 report.md §10 对应小段
- **禁止**用 `direction: "bff -> frontend"` 单字符串替代 producer/consumers 结构

以下场景生成 Contract Delta：

- 影响超过一层。
- request/response/schema/event payload 变化。
- 触达外部权益、券、支付、奖励、风控、审计系统。
- producer/consumer 归属不清。

任一侧未验证时，使用 `alignment_status: needs_confirmation`。

## 输出

`graph-context.md` 输出格式见 `references/schemas/03-context.md`。plan.md 中每个 MODIFY/DELETE 任务必须引用至少一个 GCTX ID；无法引用时，必须在 graph-context 的 fallback/未命中表中说明。

## Self-Check（生成后必须逐项验证）

> **Self-Check 的两种条目**：本清单同时包含 (a) **机器可验证断言**（标 `[M]`）和 (b) **人工判读提示**（标 `[H]`）。执行 Self-Check 时：
> - `[M]` 条目必须逐条列出 `verify: <命令>` 与 `expect: <结果>`，未通过不得进下一步。
> - `[H]` 条目作为判读提示，LLM 自检后必须写入 workflow-state.yaml 的 `self_check_notes[step_id]` 数组，内容为"我为什么认为这条满足"的简短解释。

- [ ] [M] 每个 IMP-* 项的 surface 使用 layer-adapters.md 中定义的能力面名称
- [ ] [M] MODIFY/DELETE 类型的 IMP 有源码证据（不只是 reference 标记）
- [ ] [M] ADD 类型有 negative_code_search 证据或参考实现路径
- [ ] [M] graph-context.md 中每个 GCTX 条目都被 plan.md 或 report.md 引用
- [ ] [H] Contract Delta 只在跨层/API/外部系统场景生成
- [ ] [H] alignment_status 为 needs_confirmation 的契约列出了需要确认的内容
