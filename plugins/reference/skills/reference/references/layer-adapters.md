# 能力面适配器 v2.1

主流程对前端、BFF、后端通用；适配器只规定“需要识别哪些能力面、收集哪些证据、如何做质量门控”。路径名只是初始搜索候选，不是事实来源。

## 通用方法

1. 先生成项目画像：语言、框架、入口、构建/测试命令、部署形态、已有约定文档。
2. 再识别能力面：用 `rg`、目录、注册表、路由、类型定义、调用链和测试文件共同定位。
3. 每个能力面记录 `surface`、`owner_layer`、`entrypoints`、`key_files`、`symbols`、`evidence`、`confidence`。
4. 若路径命中但未读源码，只能作为 `candidate`；只有读到实现、注册、类型或负向搜索，才能进入 reference。
5. 同一个需求可能命中多个能力面；多层或外部系统变化必须进入 contract delta。

能力面记录建议：

```yaml
surfaces:
  - id: "SURFACE-001"
    layer: "frontend | bff | backend"
    surface: ""
    responsibility: ""
    entrypoints: []
    key_files: []
    symbols: []
    contract_refs: []
    evidence: []
    confidence: "high | medium | low"
```

## 前端能力面

| surface | 关注内容 | 质量门控 |
|---|---|---|
| `ui_route` | 页面路由、菜单、权限入口、layout 容器 | 路由/权限必须有源码或配置证据 |
| `view_component` | 可见组件、弹窗、表格列、详情块 | 验证 props/state/渲染条件，不凭文件名推断 |
| `form_or_schema` | 表单字段、动态 schema、组件元数据 | 字段名、类型、默认值、提交 payload 与契约一致 |
| `state_flow` | store、hook、cache、派生状态、跨组件数据流 | 追踪“接口响应 -> 状态 -> UI -> 提交”的链路 |
| `client_contract` | 前端到 BFF/后端的 API client、request/response | 记录 endpoint/method/字段/错误处理 |
| `content_i18n` | 文案、枚举 label、locale key、占位符 | 新可见文案要有 i18n 或明确文案计划 |
| `client_validation` | disabled、互斥、上限、格式校验、guard | 奖励/金额/资格等关键规则不能只有前端 owner |
| `preview_readonly` | 预览、详情、编辑、复制、只读回显 | 新字段要覆盖读写两条链路 |
| `tracking_permission` | 埋点、权限、灰度、实验开关 | 涉及发布观测或权限时记录 owner 和验证方式 |

前端候选路径示例：`src/components/**`、`src/pages/**`、`src/routes/**`、`src/store/**`、`src/hooks/**`、`src/api/**`、`app/**/src/**`。这些路径只用于起搜，不能替代证据。

## BFF 能力面

| surface | 关注内容 | 质量门控 |
|---|---|---|
| `edge_api` | BFF endpoint、handler、serverless action、权限上下文 | 请求/响应和错误码有契约证据 |
| `schema_or_template` | 表单 schema、模板、组件配置、detail/rules schema | 字段名、组件、类型、options、validation 明确 |
| `orchestration` | 多接口聚合、流程编排、批量/编辑/复制语义 | 每个上游/下游责任边界清晰 |
| `transform_mapping` | 前端字段和后端字段转换、默认值、兼容处理 | 映射规则必须可追踪到源码或文档 |
| `linkage_options` | 动态 options、字段联动、clear-on-change | 记录依赖字段、触发时机和上游来源 |
| `upstream_contract` | BFF 调用后端/外部服务的 request/response | 不把后端 owned 字段默认为已支持 |
| `frontend_contract` | 前端消费的 schema/payload/展示值 | UI payload 契约和展示 owner 清晰 |
| `batch_import_export` | 批量导入、模板下载、导出、解析错误 | 单个、批量、错误提示都要检查 |
| `config_toggle` | 国家、城市、业务线、灰度、开关配置 | 记录配置来源、默认行为和发布风险 |
| `bff_observability` | 日志、告警、trace、降级 | 关键失败有可观测或人工排查入口 |

BFF 候选路径示例：`src/handler/**`、`src/service/**`、`src/config/**`、`config/template/**`、`serverless/**`、`api/**`。候选命中后仍需读实现。

## 后端能力面

| surface | 关注内容 | 质量门控 |
|---|---|---|
| `api_surface` | endpoint、RPC、DTO、枚举、错误码 | required/default/兼容性说清楚 |
| `application_service` | 用例服务、流程编排、事务边界、锁 | 关键状态流和失败模式有证据 |
| `domain_model` | 聚合、策略、factory、领域对象、状态机 | registry 和实现都验证 |
| `validation_policy` | 不变量、互斥、上限、阶段规则、权限 | 服务端承接业务关键规则 |
| `persistence_model` | DB/model/migration/缓存/存储格式 | 历史数据兼容性和迁移假设明确 |
| `async_event` | job、queue、event、retry、幂等 | producer/consumer/idempotency 记录 |
| `external_integration` | 权益、券、支付、风控、消息等外部 API | payload 映射、失败模式和 owner 明确 |
| `config_toggle` | 国家、产品线、Apollo/配置中心、灰度开关 | 默认值、发布顺序和回滚方式明确 |
| `audit_observability` | 审批、审计、导出、日志、metric、alarm | 新领域字段覆盖审核和排查链路 |
| `test_surface` | 单测、集成测试、fixture、回归入口 | 计划必须落到可执行测试或人工验收 |

后端候选路径示例：`controller/**`、`handler/**`、`service/**`、`model/**`、`domain/**`、`dao/**`、`repository/**`、`client/**`、`job/**`、`internal/**`、`common/**`。不同语言和框架可有完全不同目录名，以能力面证据为准。

## 跨层契约规则

以下情况必须生成或更新 contract delta：

- 新增/修改字段、枚举、schema、endpoint、event、外部 API、DB payload。
- PRD 涉及奖励、金额、权益、资格、互斥、上限、发放、审计、预算、告警。
- 前端/BFF/后端任一层只看到“展示或透传”，但 owner 未确认。
- 现有 reference 与源码、PRD、技术方案出现矛盾。

`alignment_status` 规则：

- `aligned`：producer 和 consumer 都有证据。
- `needs_confirmation`：PRD 有描述，但某层源码/文档/owner 未确认。
- `blocked`：字段、枚举、required、时序或责任归属冲突。
- `not_applicable`：确认是单层内部变化。

## 质量门控

- 不同项目结构不得套模板路径；先识别能力面，再定位文件。
- 输出中要区分 `candidate`、`verified`、`negative_search`。
- 单层项目也要标出外部契约面；没有上游/下游证据时写 `needs_confirmation`。
- 低置信度不是失败，但必须进入开放问题或人工确认项。
