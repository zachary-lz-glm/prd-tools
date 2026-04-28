# Golden Sample：可选择奖励增加 XTR 和油站权益

这个样例来自 DIVE 巴西“可选择奖励”需求，用作 PRD -> IR -> Layer Impact -> Contract Delta 的回归样例。

## 素材来源

- PRD：`/Users/didi/work/DIVE2.0-巴西-可选择奖增加奖励类型XTR和油站相关权益-L1.docx`
- 后端技术方案：`/Users/didi/work/可选择奖增加奖励类型XTR和油站相关权益-B端技术方案.docx`
- 前端代码：`/Users/didi/work/genos`，分支 `feature_oe_dive_customization`
- BFF 代码：`/Users/didi/work/dive-bff`，分支 `feature_oe_dive_customization`
- 后端代码：`/Users/didi/work/dive-editor-g`；用户给出的目标分支本地和远端都未找到，相关实现从 selectable reward 历史分支和 master 中定位。

## Requirement IR 草图

```yaml
requirements:
  - id: "REQ-001"
    title: "新增可选择 DxGy Custom Reward 活动类型"
    change_type: "ADD"
    business_entities: ["CampaignType", "SelectableDxGyCustom"]
    target_layers: ["frontend", "bff", "backend"]
    rules:
      - "新活动类型值为 41。"
    acceptance_criteria:
      - "前端、BFF、后端对 campaign type 41 识别一致。"
  - id: "REQ-002"
    title: "可选择奖励支持 cash、XTR、coupon、油站 discount card"
    change_type: "MODIFY"
    business_entities: ["RewardMethodType"]
    target_layers: ["frontend", "bff", "backend"]
    rules:
      - "奖励方式值包含 cash、xtr、coupon、discount_card。"
  - id: "REQ-003"
    title: "XTR 单阶段且互斥"
    change_type: "MODIFY"
    business_entities: ["XTR", "stage", "reward option"]
    target_layers: ["frontend", "bff", "backend"]
    rules:
      - "XTR 强制 stage=1。"
      - "XTR 不能和其他奖励方式出现在同一个 option。"
  - id: "REQ-004"
    title: "coupon 和油站 discount card 在同一 option 内互斥"
    change_type: "MODIFY"
    business_entities: ["coupon", "discount_card"]
    target_layers: ["frontend", "backend"]
  - id: "REQ-005"
    title: "支持 OS2 optional_reward 和 XTR right 映射"
    change_type: "ADD"
    business_entities: ["optional_reward", "right", "SPU", "SKU"]
    target_layers: ["backend", "bff"]
```

## Layer Impact 草图

前端：

- `RewardMethodType` 包含 `xtr`、`cash`、`coupon`、`discount_card`。
- Custom reward rule UI 限制最多 2 种奖励类型。
- UI 上体现 XTR 互斥，以及 coupon / discount_card 互斥。
- 关键文件包括 `app/dive/src/components/FormField/CustomRewardRule/...`、`RewardMethod.tsx`、`RewardColumn.tsx`。

BFF：

- campaign type 常量中存在 `CustomSelectableReward = 41`。
- schema render 包含 `reward_method_type` 和 `stage`。
- XTR 强制 `stage=1`。
- rules schema action 请求 schema rules endpoint 时携带 `campaign_type`、`reward_method_type`、`stage`、`city`、`product_id`。
- 关键文件包括 `src/config/constant/campaignType.ts`、`src/config/template/render/basic.ts`、`src/config/template/render/rules/details/customSelectable.ts`、`schemaRulesAction.ts`。

后端：

- 存在 `TypeDxGyCustomSelect CampaignType = 41`。
- Business object factory 注册 selectable custom campaign。
- 服务端校验互斥规则和 XTR 单阶段规则。
- 存在 OS2 optional reward 创建逻辑，以及 audit/right/SPU/SKU 处理。
- 关键文件包括 `common/consts/campaign.go`、`model/business_object/factory.go`、`model/business_object/selectable_dxgy_custom_campaign/*`。

## Contract Delta 草图

```yaml
contracts:
  - id: "CONTRACT-SCHEMA-RULES"
    producer: "bff"
    consumers: ["frontend"]
    contract_surface: "schema rules request"
    request_fields:
      - { name: "campaign_type", change_type: "ADD", required: true, type: "number" }
      - { name: "reward_method_type", change_type: "ADD", required: true, type: "string" }
      - { name: "stage", change_type: "ADD", required: true, type: "number" }
    alignment_status: "aligned"
  - id: "CONTRACT-OS2-OPTIONAL-REWARD"
    producer: "backend"
    consumers: ["external"]
    contract_surface: "OS2 optional_reward payload"
    alignment_status: "needs_confirmation"
  - id: "CONTRACT-XTR-RIGHT"
    producer: "backend"
    consumers: ["bff", "external"]
    contract_surface: "XTR right/SPU/SKU mapping"
    alignment_status: "needs_confirmation"
```

## QA 矩阵

- campaign type 41 可以创建、编辑、复制、预览、审计。
- 奖励方式可以正确展示 cash/XTR/coupon/discount card。
- 只选择 XTR：通过，stage 强制为 1。
- XTR 和其他奖励方式组合：UI 阻止，后端拒绝。
- coupon 和 discount card 出现在同一 option：阻止/拒绝。
- 超过 2 种奖励类型：阻止/拒绝。
- 有效期超过 10 段：阻止/拒绝。
- 批量创建保持相同约束。
- OS2 optional reward payload 包含预期 right/SPU/SKU 字段。

## 预期 Reference 回流

- 增加术语：`可选择奖`、`XTR`、`油站权益`、`discount_card`、`optional_reward`。
- 增加 routing pattern：`新增奖励类型 / 新增权益类型 / 新 campaign type`。
- 增加契约面：schema rules、custom reward rule payload、OS2 optional reward、XTR right mapping。
- 增加 playbook：`新增可选奖励类型`。
