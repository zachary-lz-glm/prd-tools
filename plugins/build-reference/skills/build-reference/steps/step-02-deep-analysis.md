# 步骤 2：深度分析

## 目标

生成 reference v4.0：

```text
_reference/00-portal.md
_reference/project-profile.yaml
_reference/01-codebase.yaml
_reference/02-coding-rules.yaml
_reference/03-contracts.yaml
_reference/04-routing-playbooks.yaml
_reference/05-domain.yaml
```

## 输入

- `_output/modules-index.yaml`
- `_output/context-enrichment.yaml`，如存在
- `_output/graph/code-graph-evidence.yaml`，如存在（GitNexus 代码图谱证据）
- `_output/graph/business-graph-evidence.yaml`，如存在（Graphify 业务图谱证据）
- `references/reference-v4.md`
- `references/layer-adapters.md`
- `references/output-contracts.md`
- `templates/` 下的模板

## 执行

### 前置：图谱证据加载

1. 检查 `_output/graph/graph-sync-report.yaml` 是否存在。
2. 如存在且任一 provider 的 `available: true`：
   a. 读取 `_output/graph/code-graph-evidence.yaml`（如存在），建立 GEV ID 查找表。
   b. 读取 `_output/graph/business-graph-evidence.yaml`（如存在），建立 GEV-B ID 查找表。
3. 如不存在或全部 `available: false`：全部使用 rg/glob/Read 流程，不查询图谱。所有条目的 `graph_sources` 设为 `[]`。

按以下顺序生成文件，后生成的文件必须检查先生成的文件，避免内容重叠：

### 阶段 1：代码库静态清单（GitNexus 主导）

1. 为分析过程中发现的事实建立 evidence 台账。
2. 如果有 `_output/graph/code-graph-evidence.yaml`：
   a. 从图谱证据中提取模块、符号、入口、数据流作为初始数据。
   b. 用 `mcp__gitnexus__query` 补充调用链和依赖关系。
   c. 图谱结果标注 `evidence.kind: knowledge_graph`、`confidence: high`。
3. 如果没有代码图谱：按原有方式通过源码 Read 提取。
4. 生成 `01-codebase.yaml`：目录结构、枚举、模块（能力面+入口点）、注册点（只记录在哪里）、数据流（只记录通用结构流）、外部系统（只记录名称和文件位置）、核心结构体（只有字段名列表）。
   - 每个条目根据图谱贡献填写 `graph_sources` 和 `graph_evidence_refs`。
   - 图谱发现的模块/符号：`graph_sources: ["gitnexus"]`，GEV ID 填入 `graph_evidence_refs`。
   - 无图谱数据的条目：`graph_sources: []`，`graph_evidence_refs: []`。
   - 文件级 `graph_providers` 根据 graph-sync-report 的 available 状态填写。

### 阶段 2：编码规则（Graphify 主导）

5. 如果有 `_output/graph/business-graph-evidence.yaml`：
   a. 从 Graphify 的 `rationale_for` 节点提取设计原理。
   b. 从 God Nodes 和 Surprising Connections 提取危险区和反模式。
   c. Graphify `EXTRACTED` → `high`，`INFERRED` → `medium`/`low`（按 confidence 映射）。
6. 如果没有业务图谱：从源码注释（`# WHY:`、`# NOTE:`、`# HACK:`）和历史 diff 提取。
7. 生成 `02-coding-rules.yaml`：编码规范与约束（用 severity 区分软硬）、高风险区域（third_rails → danger_zones）、踩坑经验。
   - `rules` 的 `graph_sources` 按来源填写：结构性规则←`["gitnexus"]`，设计原理←`["graphify"]`，两者皆有←`["gitnexus", "graphify"]`。
   - `danger_zones` 的 `graph_sources`：blast radius←`["gitnexus"]`，God Nodes/Surprising Connections←`["graphify"]`，或两者。
   - `war_stories` 的 `graph_sources` 只设 `["graphify"]`（历史决策、踩坑叙事）。
   - 检查 01-codebase 中的 registries，如果 registries 中包含了"怎么注册"的规则描述，将规则部分移到 02 的 rules 中。

### 阶段 3：契约（GitNexus 主导，Graphify 辅助）

8. 如果有代码图谱：
   a. `mcp__gitnexus__context` 提供跨文件 import resolution 和类型推断。
   b. 精确填充 producer/consumer 关系。
9. 如果有业务图谱：
   a. Graphify 补充业务语义描述（契约背后的业务原因）。
10. 生成 `03-contracts.yaml`：跨层和外部契约、字段级定义（type/required/compatibility）。
    - 每个 contract 条目的 `graph_sources` 设为 `["gitnexus"]`，GEV ID 填入 `graph_evidence_refs`。
    - 检查 01-codebase 中的 structures.fields，如果包含 type/required 信息，删除并添加 `contract_ref` 指向 03 中的契约。
    - 检查 01-codebase 中的 external_systems，如果展开了 endpoint 列表，将 endpoint 详情移到 03，01 中只保留系统名和 contract_ref。

### 阶段 4：路由与打法（Graphify 主导）

11. 如果有业务图谱：
    a. `/graphify path "PRD 关键词" "目标模块"` 追踪业务关联。
    b. 从 Graphify 的 Leiden 聚类结果提取场景模式。
    c. 图谱的 routing 候选标注 `graph_sources: ["graphify"]`。
12. 如果有代码图谱：
    a. GitNexus impact 补充 PRD 路由到代码模块的映射。
13. 生成 `04-routing-playbooks.yaml`：PRD 路由信号（只到能力面级别）、字段映射（prd_field → code_field → contract_ref）、场景打法（步骤只在这里）。
    - `prd_routing` 的 `graph_sources`：Graphify Leiden 聚类←`["graphify"]`，GitNexus 代码路径←`["gitnexus"]`，或两者。
    - `playbooks` 和 `golden_samples` 的 `graph_sources` 主要设为 `["graphify"]`。
    - 检查 02-coding-rules 中是否有场景驱动的开发步骤，如有，移到 04 的 playbook 中。
    - routing 条目必须有 `playbook_ref` 指向对应的 playbook。
    - field_mappings 中不放字段 type/required，只用 `contract_ref` 引用 03。

### 阶段 5：业务领域（Graphify 独占）

14. 如果有业务图谱：
    a. `/graphify query "业务术语和隐式规则"` 提取领域概念。
    b. Graphify 的多模态提取（PRD 截图、流程图）补充视觉证据。
    c. 历史决策从 `rationale_for` 节点提取。
15. 如果没有业务图谱：从 PRD、技术方案、QA 记录人工提取。
16. 生成 `05-domain.yaml`：业务域概览、术语（只收录非枚举概念）、隐式业务规则、历史决策。
    - 所有条目的 `graph_sources` 设为 `["graphify"]`，GEV-B ID 填入 `graph_evidence_refs`。
    - 无图谱数据时：`graph_sources: []`，`graph_evidence_refs: []`。
    - 检查 01-codebase 中的枚举 label，如果 05-domain 的术语与枚举 label 重复，删除 05 中的重复条目，改为 `see_enum: "<EnumName>"`。

### 阶段 6：导航

17. 生成 `00-portal.md`：项目画像摘要、按场景阅读指南、文件地图、健康状态。
    - 标注哪些 reference 文件有图谱数据源支撑。
18. 更新 `project-profile.yaml`（如需要）。
    - `graph_providers` 字段记录可用图谱，结构为 `[{provider, graph, available}]`。
    - 每个 `capability_surfaces` 条目根据图谱贡献填写 `graph_sources` 和 `graph_evidence_refs`。

## 去重检查（生成完成后必执行）

按以下规则检查所有已生成文件，发现重叠时合并到对应权威文件：

1. **字段级信息**：如果 01-codebase 或 04-routing-playbooks 中出现了字段 type/required 等契约信息，删除该内容并添加 `contract_ref: "CONTRACT-xxx"` 引用 03-contracts。
2. **编码规则**：如果 04-routing-playbooks 的步骤中包含了编码级规则（如"需要注册到 factory"），将规则移到 02-coding-rules，步骤中只写 `ref_rule: "RULE-xxx"`。
3. **实现步骤**：如果 01-codebase 的模块描述中包含了场景驱动的实现步骤，将步骤移到 04-routing-playbooks 的 playbook 中。
4. **术语解释**：如果 05-domain 的术语与 01-codebase 的枚举 label 完全重复，删除 05-domain 中的重复条目，改为 `see_enum: "<EnumName>"`。
5. **外部集成**：如果 01-codebase 的 external_systems 中展开了 endpoint 列表，将 endpoint 详情移到 03-contracts，01 中只保留系统名和 `contract_ref`。

## 确定性验证

记录以下事实前必须读取源码：

- enum 值
- switch/registry 分支
- 导出的类型/方法
- 字段名
- endpoint 路径
- request/response payload 字段
- 校验规则
- 下游集成 payload 映射

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

**图谱证据不需要额外源码确认的情况**：GitNexus AST 精确提取的模块结构、符号列表、调用链（confidence: high）。需要源码确认的情况：字段级契约、枚举值、业务规则。

## 输出质量

- 每个非显然条目都有 evidence。
- 跨层假设写入 `03-contracts.yaml`。
- 场景知识写入 `04-routing-playbooks.yaml`，不要散落在说明文字中。
- 代码写法写入 `02-coding-rules.yaml`，不要复制契约和 playbook。
- 层专属事实使用适配器中的 surface 名称。
- 每个文件都有 `boundary` 字段声明。
- 图谱来源的证据标注 `kind: knowledge_graph` 和 `source: gitnexus | graphify`。
