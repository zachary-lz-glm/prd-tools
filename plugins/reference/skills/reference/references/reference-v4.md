# Reference v4.0

Reference v4 是 PRD-to-code 工作流的项目长期记忆。前端、BFF、后端共用同一套结构，内容由各层适配器决定。

`_prd-tools/reference/` 的默认治理范围是**单仓权威**：它对当前仓库中可验证的事实负责，不直接充当全平台团队 wiki。跨仓信息可以记录为协作线索，但在对应 owner 仓库或 owner 团队确认前，必须标记为 `needs_confirmation` 或 `unknown`。

v4 相比 v3 的核心变化：**从 10 文件精简到 6 文件**，统一分类维度为"知识在开发生命周期中的角色"，每个事实只存在于一个文件（SSOT），通过 ID 跨文件引用。

## 默认视图

```text
_prd-tools/reference/
├── 00-portal.md                # 人类导航和场景阅读指南
├── project-profile.yaml        # 项目画像：层级、技术栈、能力面、入口
├── 01-codebase.yaml            # 代码库静态清单
├── 02-coding-rules.yaml        # 编码规则（规范+约束）
├── 03-contracts.yaml           # 跨层和外部契约
├── 04-routing-playbooks.yaml   # PRD 路由信号 + 场景打法
└── 05-domain.yaml              # 业务领域知识
```

## 文件职责和边界

### 00-portal.md
导航、项目画像摘要、按场景阅读指南、健康状态。

### project-profile.yaml
**项目画像：当前仓库的身份、技术栈、入口、能力面和协作边界。**

包含：项目层级、技术栈、运行/测试命令、能力面、`reference_scope`、`related_repositories`。

`reference_scope.authority` 固定表达当前 `_prd-tools/reference/` 的权威范围，默认是 `single_repo`。`related_repositories` 只记录与当前仓库有关的上下游/消费者/生产者线索，不能替代对方仓库的 reference。

### 01-codebase.yaml
**静态清单：代码库中已存在的事实。**

包含：目录结构、枚举值、模块（能力面+入口点）、注册点（只记录在哪里）、数据流（只记录通用结构流）、外部系统（只记录名称和文件位置）、核心结构体（只有字段名列表）。

**不放**：字段级契约（见 03）、编码规则（见 02）、业务术语解释（见 05）、场景步骤（见 04）。

### 02-coding-rules.yaml
**编码规则：怎么写代码。**

包含：编码规范与约束（合并了旧版 conventions + constraints，用 severity 区分软硬）、高风险区域（third_rails）、踩坑经验。

**不放**：字段级契约（见 03）、场景打法步骤（见 04）。

### 03-contracts.yaml
**契约：系统边界之间的承诺。字段级信息的唯一权威来源。**

包含：endpoint、schema、event、payload 的字段级定义（request_fields / response_fields 含 type、required、compatibility）。

契约必须区分本仓已确认事实和跨仓待确认信号：

- 当前仓是 producer：可以记录 producer 侧字段定义，但 consumer 侧实际使用必须有 `consumer_repos[].verification`。
- 当前仓是 consumer：可以记录本仓消费方式，但 producer 的内部实现和最终 schema owner 必须由 producer 仓确认。
- 跨仓契约、字段 owner、上下游影响面如果只有 PRD 或推断证据，`alignment_status` 和对应 verification 必须是 `needs_confirmation`。

**不放**：编码规则（见 02）、开发步骤（见 04）、枚举值列表（见 01）。

### 04-routing-playbooks.yaml
**PRD 路由信号 + 场景打法。**

路由部分只记录信号到能力面的映射，不展开实现步骤。步骤只在 playbook 中。

包含：能力边界、PRD 路由（prd_keywords → target_surfaces → playbook_ref）、字段映射（prd_field → code_field → contract_ref）、场景打法（layer_steps、QA 矩阵、common_mistakes）、golden samples。

跨仓协作只记录 handoff：目标仓、层级、原因、期望 owner、确认状态。不要在本仓 playbook 中展开其他仓库的内部实现步骤。

**不放**：枚举值（见 01）、字段级契约（见 03）、编码规则（见 02）。

### 05-domain.yaml
**业务领域知识。**

包含：业务域概览、术语、隐式业务规则、历史决策。

**不放**：代码路径（见 01）、编码规则（见 02）、契约字段（见 03）。

## 跨文件引用规则

| 信息类型 | 权威文件 | 其他文件中的引用方式 |
|---------|---------|-------------------|
| 枚举值 | 01-codebase.enums | 其他文件用枚举名引用，不重复值 |
| 字段 type/required | 03-contracts.fields | 01 和 04 用 `contract_ref` 引用 |
| 编码规则 | 02-coding-rules.rules | 04 的 playbook 步骤用 `ref_rule` 引用 |
| 开发步骤 | 04-routing-playbooks.playbooks | 01 的模块不展开步骤，用 `playbook_ref` 引用 |
| 外部系统 endpoint | 03-contracts | 01 的 external_systems 用 `contract_ref` 引用 |
| 业务术语 | 05-domain.terms | 其他文件不重复术语解释 |

如果一条知识同时像多个文件，按以下规则归档：

1. 字段、endpoint、schema、event、DB payload、producer/consumer → **03-contracts**
2. 开发顺序、测试矩阵、需求场景处理套路 → **04-routing-playbooks**
3. 代码模式、命名、注册规则、红线、反模式 → **02-coding-rules**
4. 业务概念、隐式规则、历史决策 → **05-domain**
5. 已存在的静态事实（枚举、模块、入口） → **01-codebase**
6. 其他文件只引用 ID，**绝不复制正文**

## 单仓与团队知识库边界

当前 prd-tools 面向单仓使用：后端仓、前端仓、BFF 仓都可以各自拥有一份 `_prd-tools/reference/`。每份 reference 只对本仓事实提供权威结论。

跨仓协作按三种状态维护：

| 状态 | 含义 | 允许用途 |
|------|------|---------|
| `confirmed` | 已由当前仓证据或对应 owner 确认 | 可进入 plan/report 的确定性结论 |
| `needs_confirmation` | 有 PRD、调用线索或历史样例，但缺 owner 确认 | 可作为阻塞问题、handoff、回流候选 |
| `unknown` | 仅知道可能相关，缺少足够证据 | 只能作为开放问题 |

未来如果建设 B 端团队级知识库，应从各仓 `_prd-tools/reference/` 和 `reference-update-suggestions.yaml` 聚合：

1. 只自动聚合 `confirmed` 且证据可追溯的事实。
2. `team_reference_candidate: true` 只是候选标记，不代表已经同步到团队知识库。
3. 团队级知识库负责跨仓 taxonomy、公共契约目录、领域术语和 owner 索引；单仓 `_prd-tools/reference/` 仍保留本仓事实权威。
4. 跨仓冲突以 producer owner 或平台治理确认结果为准，并回写到相关仓的 reference。

## 元信息

每个 YAML 文件以如下字段开头：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
layer: "frontend | bff | backend | multi-layer"
project: ""
last_verified: "YYYY-MM-DD"
verify_cadence: "14d"
owner: ""
boundary: "<本文件只放什么、不放什么>"
```

`project-profile.yaml` 额外维护治理字段：

```yaml
reference_scope:
  authority: "single_repo"
  repo_role: "frontend | bff | backend | multi-layer"
  team_reference_ready: false
related_repositories:
  - repo: ""
    role: "frontend | bff | backend | external"
    relationship: "upstream | downstream | consumer | producer | peer"
    verification: "confirmed | needs_confirmation | unknown"
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

旧版 v3.1 存在 00~09 共 10 个文件，迁移关系：

| v3.1 旧文件 | v4.0 新归属 |
|------------|-----------|
| `00-index.md` | `00-portal.md`（增加场景阅读指南） |
| `01-entities.yaml` 枚举、结构体 | `01-codebase.yaml` enums, structures |
| `01-entities.yaml` entities (API/field级) | `03-contracts.yaml` contracts |
| `02-architecture.yaml` modules, registries, data_flows | `01-codebase.yaml` |
| `02-architecture.yaml` third_rails | `02-coding-rules.yaml` danger_zones |
| `02-architecture.yaml` external_integration | `01-codebase.yaml` external_systems（名称） + `03-contracts.yaml`（endpoint 详情） |
| `03-conventions.yaml` | `02-coding-rules.yaml` rules (severity: warning/info) |
| `04-constraints.yaml` | `02-coding-rules.yaml` rules (severity: fatal) |
| `05-routing.yaml` routing, field_mappings | `04-routing-playbooks.yaml` prd_routing, field_mappings |
| `06-glossary.yaml` 术语 | `05-domain.yaml` terms（去掉 enum_value/field_id） |
| `07-business-context.yaml` | `05-domain.yaml` implicit_rules, decision_log |
| `08-contracts.yaml` | `03-contracts.yaml` |
| `09-playbooks.yaml` | `04-routing-playbooks.yaml` playbooks, golden_samples |

迁移时不要自动删除旧文件。先创建 v4 默认视图，再生成 `reference-update-suggestions.yaml`。

读取旧版 reference（v3.1）时自动兼容：`01-entities.yaml` + `02-architecture.yaml` 映射为 `01-codebase`，`03-conventions.yaml` + `04-constraints.yaml` 映射为 `02-coding-rules`，以此类推。

## 质量门控

致命项：

- 默认视图缺失（00-portal.md 和至少 01~05 中的 3 个文件不存在）。
- entity、route、contract 或 playbook 没有 evidence。
- enum 或 contract 字段与源码/技术文档冲突。
- 多层契约面缺少 contract 条目。
- 影响业务结果的校验只在前端，且没有明确授权。
- 跨文件重复：同一事实（如字段定义、编码规则）出现在多个文件中且措辞矛盾。

警告项：

- `last_verified + verify_cadence` 已过期。
- 05-domain 术语缺少常见 PRD 同义词。
- playbook 缺少 QA 矩阵。
- golden sample 没覆盖高频变化模式。
- 路由条目缺少 playbook_ref。

没有致命项，且警告项有明确后续动作，才能认为 reference 可用。
