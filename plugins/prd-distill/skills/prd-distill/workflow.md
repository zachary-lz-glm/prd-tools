# prd-distill 工作流

## 目标

把 PRD 蒸馏为工程可执行的结论、计划和证据链：

```text
PRD raw file/text
  -> prd-ingest/*
  -> tech docs + reference + code + graph-context
  -> report.md（精准影响报告 + 阻塞问题）
  -> plan.md（函数级技术方案）
  -> artifacts/*
```

主流程对前端、BFF、后端通用；层差异通过 `references/layer-adapters.md` 的能力面适配器生效。默认给人看轻量输出，机器可读细节放入 `artifacts/`。

短入口：

- `/prd-distill`：日常使用入口，执行本 workflow 的完整流程。

## 步骤 0：PRD Ingestion

读取或收集：

- PRD：`.docx | .md | .txt | .pdf | .pptx | .xlsx | .html | pasted text`。
- 技术方案 / API 文档：可选，但多层或后端相关需求强烈建议读取。
- `_reference/`：优先 v4（6 文件结构）；若只有 v3.1（10 文件结构），兼容读取；若只有旧版 `05-mapping.yaml`，兼容读取并在回流建议里提示迁移。
- 目标代码库：用于代码锚定。

创建输出目录：

```text
_output/prd-distill/<slug>/
├── prd-ingest/
├── report.md
├── plan.md
└── artifacts/
```

文件型 PRD 必须优先执行：

```bash
uv run <skill-dir>/scripts/ingest_prd.py <prd-file> --out _output/prd-distill/<slug>/prd-ingest
```

`prd-ingest/` 产出：

```text
prd-ingest/
├── source-manifest.yaml
├── document.md
├── document-structure.json
├── evidence-map.yaml
├── media/
├── media-analysis.yaml
├── tables/
├── extraction-quality.yaml
└── conversion-warnings.md
```

读取 `extraction-quality.yaml`：

- `pass`：可进入后续蒸馏。
- `warn`：可继续，但必须把图片未分析、复杂表格风险写入 `report.md` §11。
- `block`：暂停，要求用户提供 markdown/text，或检查 MarkItDown 安装。

图片分析说明：

- `source-manifest.yaml` 中 `ingestion.ocr` 字段记录图片分析模式：`llm_vision`（已分析）或 `not_available`（未分析）。
- `media-analysis.yaml` 中每个图片的 `analysis_status` 为 `llm_vision_analyzed`（LLM 已分析）或 `needs_vision_or_human_review`（需人工确认）。
- 设置 `ANTHROPIC_AUTH_TOKEN` 或 `OPENAI_API_KEY` 环境变量后，ingestion 自动启用 LLM Vision 图片分析。

如果用户只粘贴文本，手工创建等价的 source、document、evidence-map 和 quality 记录，保证后续 evidence 仍可追溯。

## 步骤 1：证据台账

先建立 `artifacts/evidence.yaml`，后续所有判断只引用 evidence id。

证据类型：

- `prd`
- `tech_doc`
- `code`
- `git_diff`
- `negative_code_search`
- `human`
- `api_doc`
- `reference`

格式见 `references/output-contracts.md`。

规则：

- PRD 原文证据优先从 `prd-ingest/evidence-map.yaml` 映射，定位到 block、line、table 或 image id。
- 源码证据要能定位文件和符号；尽量带行号。
- 搜不到也是证据，用 `negative_code_search`，记录 query 和搜索范围。
- 没有 vision/OCR/人工确认的图片不能生成高置信度需求。

## 步骤 2：Requirement IR

将 `prd-ingest/document.md` 转成 `artifacts/requirement-ir.yaml`。

每个 requirement 必须包含：

- `id`
- `title`
- `intent`
- `change_type`
- `business_entities`
- `rules`
- `acceptance_criteria`
- `target_layers`
- `evidence`
- `confidence`

原则：

- 业务规则、字段、枚举、限制、互斥、数量上限、流程差异都要拆成可追踪 requirement。
- 不要把实现方案直接混进 IR；实现影响放到 layer impact。
- 不确定项进入 `open_questions`。

## 步骤 3：Layer Impact

在生成 Layer Impact 前，先构建需求级图谱上下文。

### 3.1 Graph Context（图谱驱动技术上下文）

生成 `artifacts/graph-context.md`。这个文件是 `plan.md` 和 `report.md` 的直接输入，目标是把 PRD 语言变成可执行的代码坐标。

当 GitNexus 可用时，对每个 REQ 执行：

1. 用 `mcp__gitnexus__query` 查询业务实体、字段名、接口名、动作词和 reference routing 关键词，找到相关 execution flows、函数、类、方法和文件。
2. 对 Top symbols 用 `mcp__gitnexus__context` 获取 callers、callees、imports、properties、参与流程和文件位置。
3. 对 MODIFY/DELETE/契约变化候选用 `mcp__gitnexus__impact` 获取 blast radius。
4. 对 API/route/schema 变化用 `mcp__gitnexus__api_impact`、`route_map` 或 `shape_check` 获取 consumers、字段访问和 shape mismatch。
5. 将命中的符号写成函数级技术线索：`symbol`、`kind`、`file:line`、`role_in_flow`、`callers`、`callees`、`risk`、`recommended_plan_usage`。

当 Graphify 可用时，对每个 REQ 执行：

1. 用 `/graphify query` 查询业务实体、隐式规则、历史术语。
2. 用 `/graphify path "<需求关键词>" "<目标模块/业务概念>"` 追踪业务关联路径。
3. 用 `/graphify explain "<变更概念>"` 获取设计原理、隐式约束和历史坑点。
4. 将结果写入 `business_constraints`，并标明 `confidence: high|medium|low`。Graphify `INFERRED` 默认不能写 high。

图谱不可用时也必须生成 `artifacts/graph-context.md`，写明 unavailable reason，并列出 fallback `rg`/Read 查询。

读取目标层适配器：

- frontend / BFF / backend 单层：生成对应 impacts。
- multi-layer：每层各生成 impacts，并合并进一个 `artifacts/layer-impact.yaml`。

每个 impact 必须说明：

- requirement_id
- layer
- surface
- target 文件/模块/接口/组件
- current_state
- planned_delta
- risks
- evidence
- confidence

ADD/MODIFY/DELETE/NO_CHANGE 必须由源码或负向搜索支撑。

图谱增强（可选，当图谱可用时）：

- 优先消费 `artifacts/graph-context.md`，不要在 plan/report 阶段重新凭空猜函数。
- 如 GitNexus available：将 `mcp__gitnexus__query/context/impact/api_impact` 结果写入 impact 条目的 `affected_symbols` 和 `graph_evidence_refs`。
- 如 Graphify available：将 `/graphify query/path/explain` 结果写入 impact 条目的 `business_constraints`。
- 图谱不可用时这些字段留空，不影响核心流程。

## 步骤 4：Contract Delta

多层、接口、schema、事件、外部权益/券/支付/审计等需求必须生成 `artifacts/contract-delta.yaml`。单层且无契约变化时也创建最小文件，写明 `alignment_summary.status: not_applicable`。

每个 contract 记录：

- producer
- consumers
- contract_surface
- request_fields
- response_fields
- alignment_status
- checked_by
- evidence
- graph_evidence_refs（可选，图谱可用时填充）

判断：

- `aligned`：生产者和消费者都有证据。
- `needs_confirmation`：PRD/技术方案有描述，但某层源码或文档未确认。
- `blocked`：字段、枚举、required、时序或责任归属冲突。
- `not_applicable`：确认为单层内部变化。

## 步骤 5：计划

生成 `plan.md`（函数级技术方案文档 + 开发计划）：

- 精确到文件路径和行号。
- 包含 12 个章节：范围与假设、图谱命中与代码坐标、整体架构、实现计划、API 设计、数据存储、配置与开关、校验规则汇总、QA 矩阵、契约对齐、风险与回滚、工作量估算。
- 用 `- [ ]` checklist 格式，可直接勾选。
- 每个任务包含：目标文件、操作描述、参考实现、关联 REQ/IMP/CONTRACT、验证命令。
- 每个 MODIFY/DELETE 任务必须引用 `graph-context.md` 中的函数级线索；ADD 任务必须引用相邻参考实现或负向搜索证据。
- 技术方案必须说明关键调用链、入口函数、下游 consumer 和回归范围。
- **代码线索不可省略**：文件路径、行号、参考结构体名必须保留。
- 按 Phase 分组，Phase 间标注依赖。
- 不直接写代码，除非用户明确要求进入实现。
- 格式详见 `references/output-contracts.md` 中 plan.md 模板。

## 步骤 6：Reference 回流

生成 `artifacts/reference-update-suggestions.yaml`：

```yaml
schema_version: “4.0”
tool_version: “<tool-version>”
suggestions:
  - id: “REF-UPD-001”
    type: “new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate”
    target_file: “_reference/04-routing-playbooks.yaml”
    summary: “”
    current_repo_scope:
      authority: “single_repo”
      action: “apply_to_current_repo | record_as_signal | needs_owner_confirmation”
    owner_to_confirm: []
    team_reference_candidate: false
    team_scope:
      type: “contract | domain_term | playbook | decision | routing_signal | golden_sample”
      related_repos: []
      aggregation_status: “candidate | confirmed | rejected | not_applicable”
    evidence: [“EV-001”]
    graph_context_refs: []
    priority: “high | medium | low”
    confidence: “high | medium | low”
    proposed_patch: “”
```

触发条件：

- PRD 出现 reference 没有的术语、枚举、路由、契约或场景。
- reference 说已实现但源码不存在，或源码存在但 reference 缺失。
- 本次需求能作为高价值 golden sample。
- 发现跨仓契约、owner、handoff 或团队级术语候选，但当前仓不能独立确认。

边界规则：

- `/prd-distill` 只产出回流建议，不直接编辑 `_reference/`。
- 当前仓可验证的事实标记为 `apply_to_current_repo`。
- 其他仓实现细节、跨仓 owner、团队级 taxonomy 标记为 `needs_owner_confirmation` 或 `record_as_signal`。
- `team_reference_candidate: true` 是未来团队知识库聚合候选，不代表已确认。

## 步骤 7：人类报告

`report.md` 采用渐进式披露（Progressive Disclosure）结构，同一文件内从结论到细节逐层展开，最后以阻塞问题收尾：

1. **需求摘要**（30秒决策）：一句话 + 变更类型统计
2. **图谱命中摘要**：GitNexus/Graphify 可用状态、命中的关键函数/流程/业务约束、未命中原因
3. **影响范围**：命中的层、能力面、关键文件
4. **关键结论**：带 REQ-ID、代码路径和图谱证据
5. **变更明细表**：所有 IMP-* 项，精确到文件路径
6. **字段清单**：按功能模块分组，含类型/必填/契约ID
7. **校验规则**：规则描述 + 错误文案 + 目标文件
8. **开发 Checklist**：可直接执行的操作列表
9. **契约风险**：needs_confirmation / blocked 项
10. **Top Open Questions**：最多5个
11. **阻塞问题与待确认项**：阻塞问题（6 要素）+ 低置信度假设 + Owner 确认项

格式详见 `references/output-contracts.md` 中 report.md 模板。

报告里不要隐藏低置信度项；低置信度是价值，不是瑕疵。**线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留。

## 暂停条件

遇到以下情况暂停并说明：

- PRD 无法读取且用户没有提供文本。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据，且无法通过源码或负向搜索补齐。

## 执行规则

1. 先证据，后结论。
2. IR 描述业务意图，impact 描述代码影响，contract 描述跨层接口。
3. 业务规则不能只靠前端守。
4. 多层需求必须给契约计划。
5. 每个输出都要能回溯 evidence。
6. 完成后简要告知输出路径、最重要的阻塞/风险，并优先引导用户阅读 `report.md`。
