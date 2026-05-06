---
name: build-reference
description: 为前端、BFF、后端通用的 PRD-to-code 工作流构建、更新、健康检查或回流项目 reference 知识库。适用于用户调用 /build-reference，构建项目知识库、项目画像、能力面适配器、契约、打法、golden sample、反馈回流机制时。
---

# build-reference

Claude Code 中可通过 `/build-reference` 使用。

## 这个 skill 是做什么的

`build-reference` 负责把一个项目中会影响 PRD-to-code 的长期知识沉淀到 `_reference/`。

`_reference/` 默认是单仓权威知识库：它只对当前仓库中可验证的事实负责。跨仓契约、上下游 owner、其他仓实现细节可以作为线索记录，但在对应 owner 确认前必须标记为 `needs_confirmation`，不能写成确定事实。

它不是生成项目百科，也不是简单罗列目录；它只记录后续 PRD 蒸馏真正需要的事实：

- 项目画像：技术栈、入口、构建/测试命令、部署形态。
- 能力面：当前仓承担哪些能力，关键文件和入口在哪里。
- 业务实体：枚举、字段、组件、DTO、领域对象、endpoint、DB model。
- 跨层契约：producer、consumer、字段、required、type、owner、alignment_status、跨仓确认状态。
- 开发套路：高频需求如何改、先看哪里、要测什么、常见坑是什么。
- 历史样例：真实 PRD、技术方案、分支 diff、返工经验和 golden sample。

## 什么时候使用

使用场景：

- 团队第一次接入 PRD Tools，需要初始化 `_reference/`。
- 项目结构、活动类型、接口契约、schema 或业务规则发生较大变化。
- 完成一次真实 PRD 后，需要把新增术语、新契约、踩坑和经验回流。
- 怀疑已有 reference 过期、缺证据、和源码矛盾，或需要健康检查。

不要使用的场景：

- 用户只是想让你解释某段代码。
- 用户只是要求直接实现一个具体改动，且没有要求维护 reference。
- 当前没有项目源码，也没有任何可验证上下文。

## 输入

优先收集：

- 当前项目路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- 历史 PRD、技术方案、接口文档。
- 历史分支、commit、diff、返工记录。
- 当前已有 `_reference/` 和 `_output/`。

没有历史样例时也可以构建，但必须标注业务语义置信度较低。

## 输出

长期知识库输出到项目根目录：

```text
_reference/
├── 00-portal.md                # 人类导航 + 场景阅读指南
├── project-profile.yaml        # 项目画像
├── 01-codebase.yaml            # 代码库静态清单
├── 02-coding-rules.yaml        # 编码规则（规范+约束）
├── 03-contracts.yaml           # 跨层和外部契约
├── 04-routing-playbooks.yaml   # PRD 路由信号 + 场景打法
└── 05-domain.yaml              # 业务领域知识
```

兼容读取旧版 v3.1 文件（`01-entities.yaml` ~ `09-playbooks.yaml`），自动映射到 v4.0 结构。

过程和质量报告输出到：

```text
_output/
├── context-enrichment.yaml
├── modules-index.yaml
├── reference-health.yaml
├── reference-quality-report.yaml
├── feedback-ingest-report.yaml
└── graph/
    ├── graph-sync-report.yaml        # 始终生成，记录图谱可用状态
    ├── GRAPH_STATUS.md               # 给人看的图谱状态、可视化入口和下一步
    ├── code-graph-evidence.yaml      # GitNexus 证据（如可用）
    └── business-graph-evidence.yaml  # Graphify 证据（如可用）
```

## 工作模式

| 模式 | 何时使用 | 主要输出 |
|---|---|---|
| `F 上下文收集` | 首次建设前，收集历史 PRD、技术方案、分支 diff | `_output/context-enrichment.yaml` |
| `A 全量构建` | 首次构建或项目大改后重建 | `_reference/` |
| `B 增量更新` | 只更新受 git diff、文件变化或新证据影响的部分 | 更新后的 `_reference/` |
| `B2 健康检查` | 判断 reference 是否完整、过期、缺证据 | `_output/reference-health.yaml` |
| `C 质量门控` | 检查证据、契约闭环、源码一致性、幻觉风险 | `_output/reference-quality-report.yaml` |
| `E 反馈回流` | 从 prd-distill 输出中回收确认过的新知识 | `_output/feedback-ingest-report.yaml` |

如果用户没有指定模式，先检查 `_reference/` 是否存在：

- 不存在：建议 `F 上下文收集`，然后 `A 全量构建`。
- 已存在：建议 `B2 健康检查` 或按用户目标执行 `B/E/C`。

## 能力面适配器

前端、BFF、后端共用同一套流程，但不绑定固定目录结构。

先识别项目层级，再读取 `references/layer-adapters.md`。路径只作为候选，最终结论必须来自源码、配置、类型定义、注册点、调用链、测试或负向搜索。

典型能力面：

- 前端：`ui_route`、`view_component`、`form_or_schema`、`state_flow`、`client_contract`、`content_i18n`、`client_validation`。
- BFF：`edge_api`、`schema_or_template`、`orchestration`、`transform_mapping`、`frontend_contract`、`upstream_contract`。
- 后端：`api_surface`、`application_service`、`domain_model`、`validation_policy`、`persistence_model`、`async_event`、`external_integration`。

## 文件边界（v4.0）

构建 `_reference/` 时必须遵守：

- `01-codebase`：只放已存在的静态事实（目录、枚举、模块、注册点、数据流、外部系统、结构体）。不放字段级契约、不放编码规则、不放实现步骤。
- `02-coding-rules`：只放编码规则（规范+约束合并，severity 区分软硬）、高风险区域、踩坑经验。不放契约字段、不放打法步骤。
- `03-contracts`：只放跨层和外部契约的字段级定义。这是字段级信息的唯一权威来源。不放编码规则、不放开发步骤、不放枚举值列表。
- `04-routing-playbooks`：路由只放信号到能力面的映射（不含实现步骤）。打法只放在 playbook 中。不放枚举值、不放字段级契约、不放编码规则。
- `05-domain`：只放业务领域知识（术语、背景、隐式规则、决策日志）。不放代码路径、不放编码规则、不放契约字段。

跨文件引用规则：

- 字段 type/required 只在 `03-contracts`，其他文件用 `contract_ref` 引用。
- 编码规则只在 `02-coding-rules`，playbook 步骤用 `ref_rule` 引用。
- 开发步骤只在 `04-routing-playbooks` 的 playbook 中。
- 术语只在 `05-domain`（枚举 label 在 `01-codebase` 的 enums 中）。
- 外部系统 endpoint 详情只在 `03-contracts`，`01-codebase` 用 `contract_ref` 引用。

## 证据规则

必须遵守：

- 源码、PRD、技术文档、API 文档、git diff 是权威证据。
- reference 是加速器，不是最终权威。
- 当前仓源码只能证明当前仓事实；其他仓的契约 owner、字段语义和实现细节必须由对方 reference、接口文档或 owner 确认。
- 枚举、字段、方法签名、契约字段、业务规则不能从文件名或 import 推断，必须读源文件。
- 搜不到也是证据，使用 `negative_code_search` 记录 query 和范围。
- 不确定就写 `confidence: low`，并进入开放问题或后续动作。
- 每条关键事实都要有 `evidence`、`verified_by` 或明确的负向搜索。

## 图谱增强（可选）

当 GitNexus 或 Graphify 图谱可用时，build-reference 可以从图谱获取结构化证据，加速构建过程。

详细规则见 `references/reference-v4.md` 的「图谱证据层」章节。

| 图谱工具 | 维度 | 适用 reference 文件 |
|---------|------|-------------------|
| GitNexus | 代码结构 | 01-codebase、03-contracts |
| Graphify | 业务语义 | 02-coding-rules、04-routing-playbooks、05-domain |

核心原则：**图谱是原始发现层，reference 是精选后的企业知识库。Raw Graph 不等于 Reference。** 图谱结论仍需源码确认（GitNexus AST high 精度的结构发现除外）。

### 图谱证据桥接

每个 reference 条目使用两套独立的证据追踪，**不能互相替代**：

- `evidence: ["EV-xxx"]` — 可审计证据（源码、文档、人工确认）。关键 reference 条目必须至少有 EV 或明确豁免原因。
- `graph_evidence_refs: ["GEV-xxx"]` — 图谱溯源（GitNexus/Graphify 的结构化发现）。

图谱状态始终记录在 `_output/graph/graph-sync-report.yaml`（即使图谱不可用也会生成，记录 unavailable 原因）。质量门控会校验图谱证据与 reference 的一致性。

同时生成 `_output/graph/GRAPH_STATUS.md`，面向用户展示：

- GitNexus 是否可用、索引是否新鲜、对应 `.gitnexus/` 路径。
- Graphify 是否可用、是否已生成 `graphify-out/graph.json`、可视化页面 `graphify-out/graph.html` 和 `GRAPH_REPORT.md`。
- 本次 reference 哪些文件消费了图谱证据，哪些退回到源码扫描。
- 如果图谱缺失或过期，给出下一步命令，如 `npx -y gitnexus@latest analyze --incremental`（无 Node 时用 `bunx --bun gitnexus@latest analyze --incremental`）或 `/graphify . --mode deep`。

### 置信度映射

| 图谱来源 | confidence | 是否需要源码确认 |
|---------|-----------|--------------|
| GitNexus AST 提取 | high | 不需要 |
| Graphify EXTRACTED + source locator | high | 不需要 |
| Graphify EXTRACTED 无 locator | medium | 需要 |
| Graphify INFERRED ≥ 0.8 | medium | 需要 |
| Graphify INFERRED < 0.8 | low | 必须确认 |
| Graphify AMBIGUOUS | low | 必须人工确认 |

## 执行步骤

1. 识别项目路径、层级、已有 `_reference/` 和 `_output/`。
2. 根据用户目标选择模式。
3. 限定在当前项目内搜索，不跨兄弟项目。
4. 标注 `reference_scope.authority: single_repo`，并把跨仓线索写入确认状态字段。
5. 使用 `rg` / glob 找候选，再读取源码确认事实。
6. 生成或更新 `_reference/`。
7. 执行健康检查或质量门控。
8. 给用户摘要：新增/更新文件、质量状态、风险、下一步建议。

## 需要读取的参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整构建、健康检查、质量门控或反馈回流时 |
| `references/reference-v4.md` | 需要确认 reference 文件职责、边界、质量规则时 |
| `references/layer-adapters.md` | 判断前端/BFF/后端能力面时 |
| `references/output-contracts.md` | 需要和 prd-distill 输出契约对齐时 |
| `templates/*.yaml` | 创建 reference 骨架时 |
| `references/selectable-reward-golden-sample.md` | 需要示例或校准复杂需求时 |

## 完成标准

完成后不要只说"已构建"。必须说明：

- `_reference/` 新增或更新了哪些文件。
- reference 当前健康状态：pass / warning / fail。
- 哪些关键事实证据充分，哪些是 low confidence。
- 是否存在跨层契约 owner 未确认。
- 下一步应该运行 `prd-distill`，还是继续补历史样例或修复 reference。
