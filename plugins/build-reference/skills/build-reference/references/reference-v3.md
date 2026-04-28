# Reference v3

Reference v3 是 PRD-to-code 工作流的项目长期记忆。前端、BFF、后端共用同一套结构，内容由各层适配器决定。

## 文件集合

```text
_reference/
├── 00-index.md
├── 01-entities.yaml
├── 02-architecture.yaml
├── 03-conventions.yaml
├── 04-constraints.yaml
├── 05-routing.yaml
├── 06-glossary.yaml
├── 07-business-context.yaml
├── 08-contracts.yaml
└── 09-playbooks.yaml
```

## 文件职责

| 文件 | 职责 |
|---|---|
| `00-index.md` | 导航、freshness、关键入口、场景到文件映射 |
| `01-entities.yaml` | 已有枚举、字段、组件、领域对象、endpoint、结构体 |
| `02-architecture.yaml` | 模块图、数据流、注册点、依赖枢纽、高风险区域 |
| `03-conventions.yaml` | 命名、代码模式、反模式、踩坑历史、风格 |
| `04-constraints.yaml` | 硬规则、白名单、校验规则、生成边界、质量门控 |
| `05-routing.yaml` | PRD 信号到 Requirement IR 和分层影响的映射 |
| `06-glossary.yaml` | 业务术语、同义词、枚举 label、字段/组件映射 |
| `07-business-context.yaml` | 业务域概览、隐式规则、决策记录、里程碑 |
| `08-contracts.yaml` | 跨层和外部契约 |
| `09-playbooks.yaml` | 场景 playbook、QA 矩阵、golden sample |

## 元信息

每个 YAML 文件以如下字段开头：

```yaml
version: "3.0"
layer: "frontend | bff | backend | multi-layer"
project: ""
last_verified: "YYYY-MM-DD"
verify_cadence: "14d"
owner: ""
```

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

迁移时不要自动删除旧文件。先创建 v3 文件，再生成 `reference-update-suggestions.yaml`。

## 质量门控

致命项：

- v3 必需文件缺失。
- entity、route、contract、playbook 没有证据。
- enum 或 contract 字段与源码/技术文档冲突。
- 多层变化没有 contract delta。
- 业务关键校验只在前端，且没有明确授权。

警告项：

- 文件超过 `verify_cadence` 未验证。
- glossary 缺少常见 PRD 同义词。
- playbook 缺少 QA matrix。
- golden sample 没覆盖高频变化模式。

没有致命项，且警告项有明确后续动作，才能认为 reference 可用。
