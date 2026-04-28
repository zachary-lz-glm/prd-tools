# 步骤 2：Layer Impact 与 Contract Delta

## 目标

将 Requirement IR 转成：

- `_output/prd-distill/<slug>/layer-impact.yaml`
- `_output/prd-distill/<slug>/contract-delta.yaml`

## 输入

- `evidence.yaml`
- `requirement-ir.yaml`
- `_reference/01-entities.yaml`
- `_reference/02-architecture.yaml`
- `_reference/03-conventions.yaml`
- `_reference/04-constraints.yaml`
- `_reference/08-contracts.yaml`
- `_reference/09-playbooks.yaml`
- `references/layer-adapters.md`

## 执行

1. 为每个目标层选择适配器。
2. 对每个 requirement 搜索并读取代码，确认当前状态。
3. 按适配器 concern 记录 Layer Impact。
4. 对每个跨层/API/schema/event/downstream 契约面创建 Contract Delta。
5. 从规范、约束、third rails、契约、playbook 中补充风险。

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
