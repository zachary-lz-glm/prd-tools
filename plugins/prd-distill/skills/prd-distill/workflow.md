# prd-distill 工作流

## 目标

把 PRD 蒸馏为工程可执行的结论、计划和证据链：

```text
PRD raw file/text
  -> _ingest/*
  -> tech docs + reference + code + graph-context
  -> report.md（精准影响报告 + 阻塞问题）
  -> plan.md（函数级技术方案）
  -> readiness-report.yaml（能不能开工的红绿灯）
  -> context/*
  -> [辅助层] query-plan.yaml + context-pack.md + final-quality-gate.yaml
```

主流程对前端、BFF、后端通用；层差异通过 `references/layer-adapters.md` 的能力面适配器生效。默认给人看轻量输出，机器可读细节放入 `context/`。

短入口：

- `/prd-distill`：日常使用入口，执行本 workflow 的完整流程。

## 步骤 0：PRD Ingestion

读取或收集：

- PRD：`.md | .txt | .docx | pasted text`。
  - `.md`/`.txt`：直接读取。
  - `.docx`：用 `unzip` 提取 `word/document.xml`（文本）和 `media/`（图片）。文本去 XML 标签后写入 `_ingest/document.md`，图片拷贝到 `_ingest/media/`。在文本中图片位置插入 `![image-N](media/imageN.png)` 占位。Claude 用 Read 工具逐个查看图片（原生多模态），理解 UI 截图、流程图、数据图表，结果写入 `_ingest/media-analysis.yaml`。复杂格式（嵌套表格）可能丢失，此时 `extraction-quality.yaml` 标记 `warn`。
  - 粘贴文本：手工建立来源和定位。
- 技术方案 / API 文档：可选，但多层或后端相关需求强烈建议读取。
- `_prd-tools/reference/`：优先 v4（6 文件结构）；若只有 v3.1（10 文件结构），兼容读取；若只有旧版 `05-mapping.yaml`，兼容读取并在回流建议里提示迁移。
- 目标代码库：用于代码锚定。

创建输出目录：

```text
_prd-tools/distill/<slug>/
├── _ingest/
├── report.md
├── plan.md
├── portal.html
└── context/
```

Claude 直接读取 `.md/.txt` 文件，用 `unzip` 提取 `.docx` 文件，或接受粘贴文本，手动创建 `_ingest/` 证据结构：

```text
_ingest/
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
- `block`：暂停，要求用户提供 markdown/text。

如果用户只粘贴文本，手工创建等价的 source、document、evidence-map 和 quality 记录，保证后续 evidence 仍可追溯。

## 步骤 1：证据台账

先建立 `context/evidence.yaml`，后续所有判断只引用 evidence id。

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

- PRD 原文证据优先从 `_ingest/evidence-map.yaml` 映射，定位到 block、line、table 或 image id。
- 源码证据要能定位文件和符号；尽量带行号。
- 搜不到也是证据，用 `negative_code_search`，记录 query 和搜索范围。
- 没有人工确认的图片不能生成高置信度需求。

## 步骤 2：Requirement IR

将 `_ingest/document.md` 转成 `context/requirement-ir.yaml`。

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

## 步骤 2.5：Query Plan（辅助层）

> **定位**：Query Plan 是辅助层，不替代 report.md 和 plan.md 作为主产物。

如果 `_prd-tools/reference/index/` 存在，运行 `scripts/context-pack.py` 生成 `context/query-plan.yaml`，为后续 Graph Context（步骤 3.1）提供代码锚点检索提示。

```bash
scripts/context-pack.py \
  --distill _prd-tools/distill/<slug> \
  --index _prd-tools/reference/index \
  --out _prd-tools/distill/<slug>/context/context-pack.md
```

产出 `context/query-plan.yaml`：

```yaml
schema_version: "1.0"
phases:
  seed_anchors: []        # 从 requirement-ir 提取的种子查询词
  impact_hints: []        # 从 layer-impact 提取的文件路径提示
  p0_requirements: []     # P0 需求的关键实体和术语
```

## 步骤 2.6：Context Pack（辅助层）

> **定位**：Context Pack 是辅助层，不替代 graph-context.md。graph-context.md 仍是源码扫描的主产出。

在步骤 3（Layer Impact）完成后，再次运行 `scripts/context-pack.py`（此时 layer-impact.yaml 已存在），生成 `context/context-pack.md`，将 Evidence Index 中的代码实体与 distill 上下文融合，形成模型可直接消费的精简上下文（建议 ≤800 行）。

触发时机：步骤 3 完成后、步骤 4（Contract Delta）之前。如果索引不存在则跳过。

## 步骤 3：Layer Impact

在生成 Layer Impact 前，先构建需求级代码上下文。

### 3.1 Graph Context（源码驱动技术上下文）

生成 `context/graph-context.md`。这个文件是 `plan.md` 和 `report.md` 的直接输入，目标是把 PRD 语言变成可执行的代码坐标。

对每个 REQ 执行源码扫描：

1. 从 requirement-ir 提取业务实体、字段名、接口名、动作词和 reference routing 关键词。
2. 用 `rg`/`glob` 搜索源码中匹配的函数、类、方法、文件和符号。
3. 用 `Read` 读取命中文件，获取 callers、callees、imports、properties 和参与流程。
4. 对 MODIFY/DELETE/契约变化候选用 `rg` 追踪引用链，评估 blast radius。
5. 将命中的符号写成函数级技术线索：`symbol`、`kind`、`file:line`、`role_in_flow`、`callers`、`callees`、`risk`、`recommended_plan_usage`。

始终生成 `context/graph-context.md`，记录实际执行的搜索查询和命中结果。

读取目标层适配器：

- frontend / BFF / backend 单层：生成对应 impacts。
- multi-layer：每层各生成 impacts，并合并进一个 `context/layer-impact.yaml`。

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

源码扫描增强：

- 优先消费 `context/graph-context.md`，不要在 plan/report 阶段重新凭空猜函数。
- 将源码扫描命中的符号写入 impact 条目的 `affected_symbols` 和 `graph_evidence_refs`。
- 将业务约束写入 impact 条目的 `business_constraints`。

## 步骤 4：Contract Delta

多层、接口、schema、事件、外部权益/券/支付/审计等需求必须生成 `context/contract-delta.yaml`。单层且无契约变化时也创建最小文件，写明 `alignment_summary.status: not_applicable`。

每个 contract 记录：

- producer
- consumers
- contract_surface
- request_fields
- response_fields
- alignment_status
- checked_by
- evidence
- graph_evidence_refs（可选，源码扫描命中时填充）

判断：

- `aligned`：生产者和消费者都有证据。
- `needs_confirmation`：PRD/技术方案有描述，但某层源码或文档未确认。
- `blocked`：字段、枚举、required、时序或责任归属冲突。
- `not_applicable`：确认为单层内部变化。

## 步骤 5：计划

生成 `plan.md`（函数级技术方案文档 + 开发计划）：

- 精确到文件路径和行号。
- 包含 10 个章节：范围与假设、源码扫描命中与代码坐标、整体架构、实现计划、API 设计、数据存储、校验规则汇总、QA 矩阵、契约对齐、风险与回滚。
- 用 `- [ ]` checklist 格式，可直接勾选。
- 每个任务包含：目标文件、操作描述、参考实现、关联 REQ/IMP/CONTRACT、验证命令。
- 每个 MODIFY/DELETE 任务必须引用 `graph-context.md` 中的函数级线索；ADD 任务必须引用相邻参考实现或负向搜索证据。
- 技术方案必须说明关键调用链、入口函数、下游 consumer 和回归范围。
- **代码线索不可省略**：文件路径、行号、参考结构体名必须保留。
- 按 Phase 分组，Phase 间标注依赖。
- 不直接写代码，除非用户明确要求进入实现。
- 格式详见 `references/output-contracts.md` 中 plan.md 模板。

## 步骤 6：Readiness 评分

生成 `readiness-report.yaml`，用于回答"这次 PRD 蒸馏能不能进入开发/评审"。

数据来源：
- `_ingest/extraction-quality.yaml` → PRD 读取质量。
- `context/evidence.yaml` + `context/requirement-ir.yaml` → 证据覆盖。
- `context/graph-context.md` → source code scanning coverage。
- `context/contract-delta.yaml` → 契约对齐和 owner 确认。
- `plan.md` → 计划是否可执行。

输出要求：
- `status`: `pass | warning | fail`。
- `score`: 0-100。
- `decision`: `ready_for_dev | needs_owner_confirmation | blocked`。
- `provider_value`: 列出 source code scanning 和 reference 对 plan/report 实际贡献了什么。
- `next_actions`: 最多 5 条，优先处理 blocked 和 needs_confirmation。

## 步骤 7：Reference 回流

生成 `context/reference-update-suggestions.yaml`：

```yaml
schema_version: “4.0”
tool_version: “<tool-version>”
suggestions:
  - id: “REF-UPD-001”
    type: “new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate”
    target_file: “_prd-tools/reference/04-routing-playbooks.yaml”
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

- `/prd-distill` 只产出回流建议，不直接编辑 `_prd-tools/reference/`。
- 当前仓可验证的事实标记为 `apply_to_current_repo`。
- 其他仓实现细节、跨仓 owner、团队级 taxonomy 标记为 `needs_owner_confirmation` 或 `record_as_signal`。
- `team_reference_candidate: true` 是未来团队知识库聚合候选，不代表已确认。

## 步骤 8：人类报告

`report.md` 采用渐进式披露（Progressive Disclosure）结构，同一文件内从结论到细节逐层展开，最后以阻塞问题收尾：

1. **需求摘要**（30秒决策）：一句话 + 变更类型统计
2. **源码扫描命中摘要**：命中的关键函数/流程/业务约束、未命中原因
3. **影响范围**：命中的层、能力面、关键文件
4. **关键结论**：带 REQ-ID、代码路径和源码扫描证据
5. **变更明细表**：所有 IMP-* 项，精确到文件路径
6. **字段清单**：按功能模块分组，含类型/必填/契约ID
7. **校验规则**：规则描述 + 错误文案 + 目标文件
8. **开发 Checklist**：可直接执行的操作列表
9. **契约风险**：needs_confirmation / blocked 项
10. **Top Open Questions**：最多5个
11. **阻塞问题与待确认项**：阻塞问题（6 要素）+ 低置信度假设 + Owner 确认项

格式详见 `references/output-contracts.md` 中 report.md 模板。

报告里不要隐藏低置信度项；低置信度是价值，不是瑕疵。**线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留。

## 步骤 8.5：Final Quality Gate（辅助层）

> **定位**：Final Quality Gate 是辅助层，不替代 readiness-report.yaml。readiness-report.yaml 仍是就绪度评估的主产出。

运行 `scripts/final-quality-gate.py` 对所有交付物执行 5 项确定性检查，生成 `context/final-quality-gate.yaml`。

```bash
scripts/final-quality-gate.py \
  --distill _prd-tools/distill/<slug>
```

5 项检查：

| 检查项 | 权重 | 说明 |
|--------|------|------|
| required_files | 20% | 必需文件和报告章节是否完整 |
| context_pack_consumed | 15% | context-pack 中代码实体被 report/plan 消费的比例 |
| code_anchor_coverage | 25% | 关键代码锚点在 graph-context/plan 中的覆盖率 |
| plan_actionability | 25% | plan 是否包含 checklist、文件路径、验证命令 |
| blocker_quality | 15% | 阻塞项是否有上下文和证据支撑 |

产出 `context/final-quality-gate.yaml`：

```yaml
schema_version: "1.0"
status: "pass | warning | fail"
score: 0
checks: { ... }
summary:
  top_gaps: []
```

触发时机：步骤 8（report.md）完成后、步骤 9（portal.html）之前。

## 步骤 9：Portal HTML 生成

生成 `_prd-tools/distill/<slug>/portal.html`，将所有蒸馏产物内联为一个自包含的可视化页面。

详细生成规则见 `steps/step-04-portal.md`。

核心要求：

- 读取全部产出文件（report.md、plan.md、context/*），解析为结构化数据后内联到 HTML。
- 页面包含 9 个可视化 Section：总览、源码命中、影响分析、契约差异、开发计划、QA 矩阵、阻塞问题、回流建议。
- 开发计划的 checklist 支持交互式勾选，状态持久化到 localStorage。
- 零外部依赖，file:// 协议可用，双击即可在浏览器中打开。
- 生成后告知用户文件路径。

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
6. 完成后简要告知输出路径、最重要的阻塞/风险，并优先引导用户阅读 `report.md`。同时告知 `portal.html` 可在浏览器中打开查看完整可视化报告。
7. **report.md 和 plan.md 是主产物**；query-plan、context-pack、final-quality-gate 是辅助层，不替代主产物的阅读优先级。
