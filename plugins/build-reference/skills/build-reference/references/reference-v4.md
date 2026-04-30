# Reference v4.0

Reference v4 是 PRD-to-code 工作流的项目长期记忆。前端、BFF、后端共用同一套结构，内容由各层适配器决定。

v4 相比 v3 的核心变化：**从 10 文件精简到 6 文件**，统一分类维度为"知识在开发生命周期中的角色"，每个事实只存在于一个文件（SSOT），通过 ID 跨文件引用。

## 默认视图

```text
_reference/
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

**不放**：编码规则（见 02）、开发步骤（见 04）、枚举值列表（见 01）。

### 04-routing-playbooks.yaml
**PRD 路由信号 + 场景打法。**

路由部分只记录信号到能力面的映射，不展开实现步骤。步骤只在 playbook 中。

包含：能力边界、PRD 路由（prd_keywords → target_surfaces → playbook_ref）、字段映射（prd_field → code_field → contract_ref）、场景打法（layer_steps、QA 矩阵、common_mistakes）、golden samples。

**不放**：枚举值（见 01）、字段级契约（见 03）、编码规则（见 02）。

### 05-domain.yaml
**业务领域知识。**

包含：业务域概览、术语（只收录无法归入 01 枚举 label 的概念）、隐式业务规则、历史决策。

**不放**：代码路径（见 01）、编码规则（见 02）、契约字段（见 03）。

## 跨文件引用规则

| 信息类型 | 权威文件 | 其他文件中的引用方式 |
|---------|---------|-------------------|
| 枚举值和 label | 01-codebase.enums | 其他文件用枚举名引用，不重复值 |
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

## 证据要求

每个非显然事实都必须有证据：

```yaml
evidence:
  - id: "EV-001"
    kind: "code | prd | tech_doc | git_diff | negative_code_search | human | api_doc | knowledge_graph"
    source: ""
    locator: ""
    summary: ""
confidence: "high | medium | low"
```

`high` 表示直接来自源码、PRD、技术文档等权威来源。`medium` 表示证据部分完整。`low` 表示可作为线索，但不能自动执行。

## 图谱证据层（Graph Evidence）

当 GitNexus 或 Graphify 图谱可用时，reference 可以从图谱获取结构化证据。图谱是原始发现层，reference 是精选后的企业知识库。

### 原则

| 原则 | 说明 |
|------|------|
| Raw Graph ≠ Reference | 图谱是原始知识发现层，reference 是精选后的企业知识库 |
| 图谱结论仍需确认 | 关键契约、字段、枚举必须回到源码或接口定义确认 |
| INFERRED 默认非高置信度 | Graphify 的 INFERRED 关系必须降级为 medium/low，除非能追到原文 |
| 不把完整 graph 塞进 prompt | 只用 query 拉小子图，避免 context 爆炸 |
| Provider 可替换 | 不绑定具体工具，未来可替换为内部 MCP、Neo4j、Sourcegraph、CodeQL |

### 统一图谱证据格式

不绑定具体图谱工具，用 `graph_evidence` 统一记录：

```yaml
_output/graph/
├── business-graph-evidence.yaml    # Graphify 业务图谱证据
├── code-graph-evidence.yaml        # GitNexus 代码图谱证据
└── graph-sync-report.yaml          # 图谱同步状态报告
```

每条图谱证据：

```yaml
graph_evidence:
  - id: "GEV-001"
    provider: "graphify | gitnexus | <custom>"
    graph: "business | code"
    query: ""
    result_summary: ""
    source: "graphify-out/graph.json | .gitnexus/ | <custom>"
    source_files: []
    used_for: []                     # 哪些 reference 文件会引用
    confidence: "high | medium | low"
```

### 图谱 Provider 对应关系

| Provider | Graph 类型 | 适用的 reference 文件 | 核心能力 |
|----------|-----------|---------------------|---------|
| `gitnexus` | `code` | 01-codebase、03-contracts | 模块、调用链、字段、契约、影响面 |
| `graphify` | `business` | 02-coding-rules、04-routing-playbooks、05-domain | 业务概念、规则、因果、历史决策、设计原理 |
| `<custom>` | 自定义 | 按需 | 内部 MCP、Neo4j、Sourcegraph、CodeQL 等 |

### reference 文件与图谱数据源

| reference 文件 | 主要图谱来源 | 辅助来源 | 说明 |
|---------------|------------|---------|------|
| `01-codebase.yaml` | GitNexus (code) | — | 目录、模块、符号、入口、数据流从代码图谱辅助发现 |
| `02-coding-rules.yaml` | Graphify (business) | GitNexus | 设计原理、常见模式、危险区从 rationale_for 节点和调用链提炼 |
| `03-contracts.yaml` | GitNexus (code) | Graphify | FE/BFF/BE 字段、producer/consumer 从跨文件解析对齐 |
| `04-routing-playbooks.yaml` | Graphify (business) | GitNexus | PRD 关键词到能力面映射从业务图谱提取 |
| `05-domain.yaml` | Graphify (business) | — | 活动类型、权益、隐式规则从 PRD/技术方案多模态提取 |

### 图谱置信度映射

| 图谱 Provider 置信度 | evidence.confidence | 说明 |
|---------------------|--------------------|----|
| GitNexus (AST 精确提取) | `high` | 机器精度，无需降级 |
| Graphify `EXTRACTED` | `high` | 直接提取，等同于源码证据 |
| Graphify `INFERRED` confidence ≥ 0.8 | `medium` | 需要源码或文档确认 |
| Graphify `INFERRED` confidence < 0.8 | `low` | 只能作为线索，不直接进入 reference |
| Graphify `AMBIGUOUS` | `low` | 需人工确认后才能进入 reference |

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
