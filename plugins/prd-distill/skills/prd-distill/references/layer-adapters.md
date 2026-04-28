# 分层适配器

主流程保持通用。适配器只负责规定每一层应该优先收集什么证据、分析什么影响、检查哪些契约面和质量门控。

## 前端

优先扫描：

- `src/components/**`
- `src/pages/**`
- `src/store/**`
- `src/hooks/**`
- `app/**/src/**`

关注点：

| concern | 关注内容 | 质量门控 |
|---|---|---|
| `component` | 可见组件、表单字段、弹窗、表格列 | 从实现中验证 props/state |
| `form_schema` | 字段配置、校验 schema、生成式 UI 元数据 | 提交字段名必须和契约一致 |
| `state` | 本地状态、store、cache、派生状态 | 追踪 API 到提交 payload 的数据流 |
| `route` | 页面路由、菜单、权限 key | 路由和权限必须有证据 |
| `api_client` | 前端到 BFF 的请求/响应 | 记录 endpoint、method、request/response 字段 |
| `i18n` | 文案、枚举 label、locale key | 新可见文案要有 i18n 或文案计划 |
| `preview` | 详情、复制、编辑、只读预览 | 检查共享流程 |
| `validation` | disabled、互斥、客户端 guard | 影响业务结果的规则必须有 BFF/backend 证据 |

前端不能成为金额、奖励、权益、资格、互斥、上限等业务规则的唯一 owner。

## BFF

优先扫描：

- `src/config/template/**`
- `src/config/constant/**`
- `src/handler/**`
- `src/service/**`
- `config/template/**`
- `config/constant/**`

关注点：

| concern | 关注内容 | 质量门控 |
|---|---|---|
| `campaign_type` | 活动枚举、路由、模板选择 | 枚举端到端注册完整 |
| `schema_template` | 表单 schema、render 模板、detail/rules schema | 字段名、组件、类型、options、validation 明确 |
| `linkage` | 动态 options、字段依赖、clear-on-change | 记录依赖字段和上游 endpoint |
| `preview_options` | 预览、详情、options hydration | 展示值的 owner 清晰 |
| `batch` | 批量创建/编辑/复制语义 | 单个和批量场景都检查 |
| `i18n` | label 和可翻译 schema 字段 | 复用现有 key 规范 |
| `frontend_contract` | 前端消费的 schema | UI payload 契约明确 |
| `upstream_contract` | 后端 API request/response | 不推断后端 owned 字段 |

BFF 是中介层，必须同时暴露前端 schema 契约和后端假设。

## 后端

优先扫描：

- `src/modules/**`
- `src/controller/**`
- `src/service/**`
- `src/model/**`
- `controller/**`
- `service/**`
- `model/**`
- `common/**`
- `internal/**`

关注点：

| concern | 关注内容 | 质量门控 |
|---|---|---|
| `api_contract` | endpoint、DTO、枚举、错误码 | required/default/兼容性说清楚 |
| `domain_object` | 聚合、策略、factory 注册 | registry 和实现都验证 |
| `validation` | 不变量、互斥、上限、阶段规则 | 服务端要承接业务关键规则 |
| `persistence` | DB/model/migration/存储格式 | 历史数据兼容性检查 |
| `async_job` | job、queue、event、retry | producer/consumer/idempotency 记录 |
| `downstream_integration` | 权益/券/支付/风控等外部 API | payload 映射和失败模式记录 |
| `audit` | 审批、审计、导出、展示 payload | 新领域字段覆盖相关链路 |
| `observability` | metric、log、alarm、trace | 发布后如何发现失败 |

后端计划涉及存储或外部集成时，要写清发布和兼容性假设。

## 多层规则

只要一个 requirement 影响多层，就必须生成 `contract-delta.yaml`。如果 owner 不清楚，写 `alignment_status: needs_confirmation`，不要默默把责任归给当前正在看的层。
