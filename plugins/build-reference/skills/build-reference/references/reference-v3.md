# Reference v3.1

Reference v3 是 PRD-to-code 工作流的项目长期记忆。前端、BFF、后端共用同一套结构，内容由各层适配器决定。

## 默认视图

```text
_reference/
├── README.md 或 00-index.md       # 人类导航和版本信息
├── project-profile.yaml           # 项目画像：层级、技术栈、能力面、入口
├── contracts.yaml 或 08-contracts.yaml
├── playbooks.yaml 或 09-playbooks.yaml
└── artifacts/ 或 01~09            # 机器可读细节，可按需展开
```

首次构建可以继续产出 `00~09`，但最终给用户看的摘要必须优先指向默认视图。老项目已有 `00~09` 时兼容读取，不强制迁移。

## 文件职责和边界

| 文件 | 职责 |
|---|---|
| `00-index.md` | 导航、freshness、关键入口、场景到文件映射 |
| `01-entities.yaml` | 已存在的静态事实：枚举、字段、组件、领域对象、endpoint、结构体 |
| `02-architecture.yaml` | 结构和运行流：能力面、入口、数据流、注册点、依赖枢纽、高风险区域 |
| `03-conventions.yaml` | 代码写法约定：命名、注册模式、转换模式、反模式、风格。不要放跨层字段契约或需求 playbook |
| `04-constraints.yaml` | 硬规则：白名单、校验红线、生成边界、质量门控。不要放普通代码风格 |
| `05-routing.yaml` | PRD 信号如何路由到 Requirement IR、能力面和目标层。不要放完整实现步骤 |
| `06-glossary.yaml` | 业务术语、同义词、枚举 label、字段/组件映射 |
| `07-business-context.yaml` | 业务域背景、隐式规则、历史决策、已知歧义。不要放代码实现细节 |
| `08-contracts.yaml` | 跨层和外部契约：producer/consumer、字段、兼容性、owner、alignment_status。不要放开发步骤 |
| `09-playbooks.yaml` | 场景打法：触发信号、分层步骤、QA 矩阵、常见坑、golden sample。不要重复字段级契约 |

### 03 / 08 / 09 分界

- `03-conventions` 回答“代码在这个项目里通常怎么写”：命名、注册、转换、错误处理、反模式。
- `08-contracts` 回答“系统边界之间承诺了什么”：API/schema/event/payload 字段、required、类型、兼容性、owner。
- `09-playbooks` 回答“遇到某类 PRD 应该怎么推进”：先看哪里、改哪些能力面、测哪些场景、历史样例是什么。

如果一条知识同时像 03/08/09，按以下规则归档：

1. 字段、endpoint、schema、event、DB payload、producer/consumer -> `08-contracts`。
2. 开发顺序、测试矩阵、需求场景处理套路 -> `09-playbooks`。
3. 代码模式、命名、注册点、反模式 -> `03-conventions`。
4. 其他文件只引用 ID，不复制正文。

## 元信息

每个 YAML 文件以如下字段开头：

```yaml
schema_version: "3.1"
tool_version: "2.2.0"
layer: "frontend | bff | backend | multi-layer"
project: ""
last_verified: "YYYY-MM-DD"
verify_cadence: "14d"
owner: ""
```

老版本 `version: "3.0"` 可兼容读取；新建或大改时使用 `schema_version`。

## 证据要求

每个非显然事实都必须有证据：

```yaml
evidence:
  - id: "EV-001"
    kind: "code | prd | tech_doc | git_diff | negative_code_search | human | api_doc"
    source: ""
    locator: ""
    summary: ""
confidence: "high | medium | low"
```

`high` 表示直接来自源码、PRD、技术文档等权威来源。`medium` 表示证据部分完整。`low` 表示可作为线索，但不能自动执行。

## 从旧版 Reference 迁移

旧版可能存在 `05-mapping.yaml`，迁移关系如下：

- `capability_boundary`、`prd_routing`、`field_mappings`、`change_type_rules` -> `05-routing.yaml`
- `golden_samples`、`development_playbook`、`common_mistakes` -> `09-playbooks.yaml`
- API/schema/后端/前端契约面 -> `08-contracts.yaml`
- `inventory` 中已实现事实 -> `01-entities.yaml`
- 旧版 `war_stories`、`third_rails`、`change_heatmap` 保留到 `03-conventions` / `02-architecture`

迁移时不要自动删除旧文件。先创建 v3.1 默认视图，再生成 `reference-update-suggestions.yaml`。

## 质量门控

致命项：

- 默认视图缺失，且 `00~09` 也不完整。
- entity、route、contract、playbook 没有证据。
- enum 或 contract 字段与源码/技术文档冲突。
- 多层变化没有 contract delta。
- 业务关键校验只在前端，且没有明确授权。
- 03/08/09 边界混乱导致同一事实出现相互矛盾版本。

警告项：

- 文件超过 `verify_cadence` 未验证。
- glossary 缺少常见 PRD 同义词。
- playbook 缺少 QA matrix。
- golden sample 没覆盖高频变化模式。

没有致命项，且警告项有明确后续动作，才能认为 reference 可用。
