# build-reference 工作流

## 目标

构建 reference v4.0，让后续 `/prd-distill` 能稳定产出：

`report -> plan -> questions -> artifacts -> Reference 回流`

reference 是"可验证指南针"，不是项目百科。6 个文件，每个事实只存在一处（SSOT），按场景阅读。

## 三层架构

```
Graphify (业务维度)          GitNexus (代码维度)          prd-tools (治理维度)
"为什么这样设计"              "代码怎么连接"               "怎么从 PRD 到代码"
PRD/技术方案/截图/历史文档     代码仓库                     编排 + 证据治理 + 质量门控
        │                          │                           │
        └──────────────────────────┼───────────────────────────┘
                                   ▼
                         _reference/ 企业级可治理知识库
```

关键原则：**图谱是原始发现层，reference 是精选后的企业知识库。**

## 阶段

| 阶段 | 名称 | 输入 | 输出 |
|---|---|---|---|
| 0 | 上下文收集 | 历史 PRD、技术方案、分支 diff、发布/返工记录 | `_output/context-enrichment.yaml` |
| 1 | 结构扫描 | 项目目录、核心源码、git 历史 + **双图谱查询** | `_output/modules-index.yaml` + `_output/graph/*.yaml` |
| 2 | 深度分析 | modules-index、图谱证据、源码、能力面适配器 | `_reference/` v4.0 |
| 3 | 质量门控 | reference、源码、样例需求 + **图谱证据校验** | `_output/reference-quality-report.yaml` |
| 4 | 反馈回流 | `/prd-distill` 输出、源码、reference + **图谱增量更新** | `_output/feedback-ingest-report.yaml` |

## 阶段 0：上下文收集

用于提升 reference 的业务价值，尤其适合团队首次建设。

收集 1~3 个历史需求，每个需求尽量包含：

- PRD / 技术方案 / 接口文档路径
- 前端、BFF、后端代码库路径和分支
- 已知返工、线上问题、CR 争议点

输出：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
samples:
  - id: "SAMPLE-001"
    title: ""
    docs: []
    repos:
      frontend: { path: "", branch: "" }
      bff: { path: "", branch: "" }
      backend: { path: "", branch: "" }
    requirement_signals: []
    files_changed: []
    contract_surfaces: []
    lessons:
      - type: "playbook | contract | validation | pitfall | terminology"
        detail: ""
        evidence: []
```

把高价值样例沉淀到 `04-routing-playbooks.yaml` 的 `golden_samples`。

## 阶段 1：结构扫描

判断项目层级并选择能力面适配器：

- `frontend`：ui_route、view_component、form_or_schema、state_flow、client_contract 等。
- `bff`：edge_api、schema_or_template、orchestration、transform_mapping、upstream/frontend_contract 等。
- `backend`：api_surface、application_service、domain_model、validation_policy、persistence_model、async_event 等。

扫描规则：

- 使用 `rg` / glob，范围限定在当前项目，不跨项目搜索。
- 排除 `node_modules`、`dist`、`build`、`coverage`、测试、mock、fixture、生成物。
- 读取文件前先确认路径存在。

### 图谱增强（如可用）

**代码结构层（GitNexus）**：`mcp__gitnexus__query` 获取模块和符号，`mcp__gitnexus__context` 获取调用关系。AST 精度替代 regex 扫描。

**业务语义层（Graphify）**：`/graphify query` 提取业务概念，God Nodes 映射为核心模块，Surprising Connections 映射为跨域依赖。

图谱不可用时自动回退到原有 rg/glob 流程。

输出 `_output/modules-index.yaml` + `_output/graph/*.yaml`，同时沉淀 `_reference/project-profile.yaml`：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
graph_providers: []
capability_surfaces:
  - id: ""
    layer: ""
    surface: ""
    responsibility: ""
    key_files: []
    entrypoints: []
    symbols: []
    status: "candidate | verified | negative_search"
    evidence: []
    graph_source: "gitnexus | graphify | none"
```

## 阶段 2：深度分析

先读取：

- `references/reference-v4.md`
- `references/layer-adapters.md` 中当前层章节
- `references/output-contracts.md` 中 evidence 和 contract 部分

生成 `_reference/` v4.0：

```text
00-portal.md                # 人类导航 + 场景阅读指南
project-profile.yaml        # 项目画像
01-codebase.yaml            # 静态清单
02-coding-rules.yaml        # 编码规则
03-contracts.yaml           # 契约
04-routing-playbooks.yaml   # 路由 + 打法
05-domain.yaml              # 业务领域
```

提取顺序（后生成的文件必须检查先生成的文件，避免重叠）：

1. `01-codebase`：目录、枚举、模块、注册点、数据流、外部系统、结构体。
2. `02-coding-rules`：编码规范与约束、高风险区域、踩坑经验。
3. `03-contracts`：producer/consumer、endpoint/schema/event、字段级定义。
4. `04-routing-playbooks`：PRD 路由信号、字段映射、场景打法、golden samples。
5. `05-domain`：业务域概览、术语、隐式规则、历史决策。
6. `00-portal` + `project-profile`：导航和画像汇总。

每条事实必须具备：

```yaml
evidence:
  - id: "EV-001"
    kind: "code | prd | tech_doc | git_diff | negative_code_search | human | api_doc"
    source: ""
    locator: ""
    summary: ""
confidence: "high | medium | low"
```

跨文件引用规则（详见 `references/reference-v4.md`）：

- 字段 type/required 只在 `03-contracts`，其他文件用 `contract_ref` 引用。
- 编码规则只在 `02-coding-rules`，playbook 步骤用 `ref_rule` 引用。
- 开发步骤只在 `04-routing-playbooks` 的 playbook 中。
- 术语只在 `05-domain`（枚举 label 在 `01-codebase` 的 enums 中）。
- 外部系统 endpoint 详情只在 `03-contracts`，`01-codebase` 用 `contract_ref` 引用。

## 阶段 3：质量门控

必须检查：

- 文件完整性：`00-portal.md` 存在，`01~05` 中至少 3 个存在。
- 证据完整性：实体、路由、契约、playbook 关键项都有 evidence。
- 源码一致性：路径、枚举值、注册点、模板函数、契约字段仍存在。
- 契约闭环：跨层字段有 producer / consumer / checked_by / alignment_status。
- 能力面适配器门控：按 `references/layer-adapters.md` 检查当前层必需 surface。
- 边界门控：5 条跨文件边界规则（见 step-03-quality-gate.md）。
- 幻觉检查：文件、函数、变量、机制不能没有证据。
- 样例回归：至少用一个 golden sample 反推 PRD -> IR -> Layer Impact -> Contract Delta 是否走通。

输出 `_output/reference-quality-report.yaml`：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
status: "pass | warning | fail"
score: 0
fatal_findings: []
warnings: []
boundary_violations: []
sample_replay:
  sample_id: ""
  passed: false
  gaps: []
next_actions: []
```

致命项不通过时，不要宣称 reference 可用于生产；列出最小修复项。

## 阶段 4：反馈回流

读取 `_output/prd-distill/**/artifacts/reference-update-suggestions.yaml` 和 `report.md`。兼容读取旧版文件名。

只处理有证据的建议：

- `new_term`
- `new_route`
- `new_contract`
- `new_playbook`
- `contradiction`
- `golden_sample_candidate`

每条建议展示：

- 受影响 reference 文件
- 当前事实与新证据的差异
- 建议变更
- 证据来源
- 风险和置信度

用户确认后再修改 reference，并更新 `last_verified`。

## 执行规则

1. 源码是最终权威；reference 是快速通道。
2. 不确定就写 low confidence，不要补脑。
3. 多层需求必须显式记录契约面。
4. 前端、BFF、后端保持同一 reference 结构，层差异用能力面适配器表达。
5. 每个 reference 文件尽量短；复杂样例放 `04-routing-playbooks.golden_samples`。
6. 完成后给用户一份摘要：新增/更新文件、质量门控结果、下一步建议。
