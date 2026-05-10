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
- `_prd-tools/reference/`：**必须读取并消费**。优先 v4（6 文件结构）；若只有 v3.1（10 文件结构），兼容读取；若只有旧版 `05-mapping.yaml`，兼容读取并在回流建议里提示迁移。reference 消费是后续所有步骤的前置知识，不是可选建议。
- 目标代码库：用于代码锚定。

### Reference 消费门禁（Step 0 之后必须完成）

如果 `_prd-tools/reference/` 存在，**必须**完成以下消费，缺一不可：

1. **路由映射**（`04-routing-playbooks.yaml`）：提取所有 `prd_routing` 条目，建立 PRD 关键词 → target_surfaces → playbook_ref 映射表。后续 Step 3.1 源码扫描**必须先查此表**确定扫描范围，不能盲目 grep。
2. **代码地图**（`01-codebase.yaml`）：提取 modules、registries、data_flows、enums、external_systems。后续源码扫描命中时，**必须与代码地图交叉验证**，确认命中的模块和注册点与 reference 一致。
3. **编码规则**（`02-coding-rules.yaml`）：提取所有 fatal 级规则。影响分析时**必须检查是否触及这些规则**，在 layer-impact 中引用规则 ID。
4. **契约**（`03-contracts.yaml`）：提取现有 API 契约。contract-delta 生成时**必须以此为基线**，逐条对比变更。
5. **领域术语**（`05-domain.yaml`）：提取 terms 和 implicit_rules。requirement-ir 拆解时**必须用领域术语对齐** PRD 表述。

将 reference 消费状态写入 `context/evidence.yaml`：

```yaml
- id: "EV-REF-CONSUMED"
  kind: "reference"
  source: "_prd-tools/reference/"
  summary: "reference 消费完成：routing=N, rules=N, contracts=N, terms=N"
  locator: "步骤 0 消费门禁"
```

如果 `_prd-tools/reference/` **不存在**：
- 所有 layer-impact、contract-delta 的 confidence 强制降为 `low`。
- readiness-report.yaml 必须在 `next_actions` 首位写入："建议运行 `/reference` 生成项目知识库后再蒸馏"。
- report.md §11 必须暴露："本次蒸馏未消费 reference，影响分析和契约检查可能不完整"。

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

## 步骤 2.5：Query Plan（Reference Index 桥接层）

> **定位**：Query Plan 是 reference index 到源码扫描的**强制桥接层**。当 index 存在时，步骤 3.1 **必须消费** query-plan.yaml，不能跳过直接 grep。

**前置条件**：`context/requirement-ir.yaml` 已生成（步骤 2 完成）。

如果 `_prd-tools/reference/index/` 存在，**必须**运行 `python3 .prd-tools/scripts/context-pack.py` 生成 `context/query-plan.yaml`，为后续 Graph Context（步骤 3.1）提供预匹配的代码锚点。

```bash
python3 .prd-tools/scripts/context-pack.py \
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

## 步骤 2.6：Context Pack（Reference Index 融合层）

> **定位**：Context Pack 融合 Evidence Index 与 distill 上下文，为 report/plan 提供精简代码坐标。当 index 存在时**必须运行**。

在步骤 3（Layer Impact）完成后，**必须**运行 `python3 .prd-tools/scripts/context-pack.py`（此时 layer-impact.yaml 已存在），生成 `context/context-pack.md`，将 Evidence Index 中的代码实体与 distill 上下文融合，形成模型可直接消费的精简上下文（建议 ≤800 行）。

触发时机：步骤 3 完成后、步骤 4（Contract Delta）之前。如果索引不存在则跳过，但必须在 readiness-report 中记录缺失。

## 步骤 3：Layer Impact

在生成 Layer Impact 前，先构建需求级代码上下文。

### 3.1 Graph Context（Reference-First 源码扫描）

生成 `context/graph-context.md`。这个文件是 `plan.md` 和 `report.md` 的直接输入，目标是把 PRD 语言变成可执行的代码坐标。

**⚠ 强制：必须先消费 reference 再扫描源码。禁止跳过 reference 直接 grep。**

对每个 REQ 按以下优先级执行扫描：

**阶段 1：Reference 路由（必须先执行）**

1. 从 requirement-ir 提取业务实体、字段名、接口名、动作词。
2. 将提取的关键词与 `04-routing-playbooks.yaml` 的 `prd_routing` 匹配，确定 target_surfaces 和 playbook_ref。
3. 从 `01-codebase.yaml` 提取匹配到的 modules、registries、data_flows，获得精确的文件路径和符号列表。
4. 检查 `02-coding-rules.yaml` 中是否有相关 fatal 规则（如"新增 CampaignType 必须在 3 处注册"），记录为必检项。
5. 如存在 `query-plan.yaml`（步骤 2.5 产出），读取 `matched_entities` 获取预匹配的代码锚点。

**阶段 2：Index 驱动精确扫描（index 存在时优先）**

6. 对 query-plan.yaml 中 confidence=high 的 matched_entities，直接 Read 对应源码文件，确认符号和上下文。这比 grep 更精确，因为 index 已预计算了实体位置。
7. 对 confidence=low 的实体，用 `rg` 验证是否为噪音。

**阶段 3：补充扫描（仅覆盖阶段 1-2 未命中的部分）**

8. 用 `rg`/`glob` 搜索阶段 1-2 **未覆盖**的业务实体和动作词。
9. 用 `Read` 读取命中文件，获取 callers、callees、imports、properties 和参与流程。
10. 对 MODIFY/DELETE/契约变化候选用 `rg` 追踪引用链，评估 blast radius。

**阶段 4：汇总**

11. 将命中的符号写成函数级技术线索：`symbol`、`kind`、`file:line`、`role_in_flow`、`callers`、`callees`、`risk`、`recommended_plan_usage`。
12. 每条线索必须标注来源：`source: "reference_routing"` | `"index_query"` | `"code_scan"`。

始终生成 `context/graph-context.md`，记录实际执行的搜索查询、命中结果和**reference 消费记录**（从哪些 reference 文件提取了哪些路由/规则/实体）。

**门禁检查**：graph-context.md 中至少 30% 的线索应来自阶段 1-2（reference/index），否则在 readiness-report 中标记 `reference_underconsumed`。

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

### Report 质量门禁

生成 `report.md` 前必须重新读取 `context/requirement-ir.yaml`、`context/graph-context.md`、`context/contract-delta.yaml` 和 `context/context-pack.md`，核对报告已覆盖下列高收益信息。缺任一项时，不要用泛化总结替代，必须补进对应章节或 §11：

- P0/P1 需求中的配置细节：券批次/券张数/互斥、折扣卡 Card ID/数量/有效期/城市校验、EventRule 格式、Budget/GMV 范围、Push 占位符。
- PRD 内部矛盾或疑似 typo：例如同一字段同时出现 `1-10` 与 `1-99`、报错文案 `1-0` 与规则 `1-9` 不一致。此类内容必须进入 §11 阻塞问题或低置信度假设。
- 关键代码锚点：`rewardCondition.ts`、`basic.ts`、`message.ts` 等如果已在 graph-context 中出现，report/plan 不得遗漏其风险说明。
- reference 只作为候选事实和路由依据；任何 reference 结论必须被源码、PRD、技术文档或负向搜索二次确认。未确认时降为 `confidence: low|medium` 并进入 §11。

## 步骤 8.5：Final Quality Gate（辅助层）

> **定位**：Final Quality Gate 是辅助层，不替代 readiness-report.yaml。readiness-report.yaml 仍是就绪度评估的主产出。

运行 `python3 .prd-tools/scripts/final-quality-gate.py` 对所有交付物执行 5 项确定性检查，生成 `context/final-quality-gate.yaml`。

```bash
python3 .prd-tools/scripts/final-quality-gate.py \
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
8. **⚠ Reference 强制消费**：`_prd-tools/reference/` 存在时，必须消费。Step 0 消费门禁（路由/规则/契约/术语）→ Step 2.5 桥接 index → Step 3.1 reference-first 扫描。禁止跳过 reference 直接 grep 源码。reference 不存在时，所有涉及 reference 的步骤必须标记缺失并降低置信度。
