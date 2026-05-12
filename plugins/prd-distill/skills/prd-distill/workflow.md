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

## 步骤 1：证据台账 + 覆盖验证

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

格式见 `references/schemas/03-context.md`。

规则：

- PRD 原文证据优先从 `_ingest/evidence-map.yaml` 映射，定位到 block、line、table 或 image id。
- 源码证据要能定位文件和符号；尽量带行号。
- 搜不到也是证据，用 `negative_code_search`，记录 query 和搜索范围。
- 没有人工确认的图片不能生成高置信度需求。

**覆盖验证（Completeness Check）**：

在生成 requirement-ir 之前和之后各执行一次覆盖检查：

1. **前置检查**：确认 `_ingest/document-structure.json` 中每个 block 都已评估。每个 block 必须有 evidence_id 或被标记为 excluded（含 exclude_reason）。
2. **后置检查**：确认 `evidence-map.yaml` 的 coverage_ratio >= 0.8。低于 0.8 时 `extraction-quality.yaml` 必须标 `warn`，并在 `unmapped_blocks` 列出未覆盖 block。
3. `coverage_ratio` 写入 `_ingest/extraction-quality.yaml` 的 `coverage` 字段，并作为 `readiness-report.yaml` 的 `evidence_coverage` 评分输入。

## 步骤 1.5：AI-friendly PRD Compile

> **定位**：AI-friendly PRD 是规范化中间层，把现实中不够 AI-friendly 的 PRD 编译成对 AI agent 友好的统一结构。它不替代原始 PRD，也不替代 report.md / plan.md / requirement-ir.yaml，但后续步骤必须优先读取它。

**前置条件**：Step 0（PRD Ingestion）和 Step 1（Evidence Ledger）已完成。

**输入**：
- `_ingest/document.md`
- `_ingest/extraction-quality.yaml`
- `_ingest/media-analysis.yaml`（如存在）
- `_ingest/tables/`（如存在）

**输出**：
- `spec/ai-friendly-prd.md`
- `context/prd-quality-report.yaml`

### spec/ai-friendly-prd.md

AI-friendly PRD 必须使用 13 个固定章节：

```markdown
# AI-friendly PRD: <title>

## 1. Overview
说明需求背景、业务目标、产品范围。

## 2. Problem Statement
说明要解决的问题、当前痛点、为什么要做。

## 3. Target Users
列出角色、用户群、使用场景。

## 4. Goals & Success Metrics
列出目标和可衡量指标。
如果原 PRD 没有指标，必须标注：`Missing confirmation`。

## 5. User Stories
用统一格式：
- As a <role>, I want <capability>, so that <benefit>.
每条必须有 source 标记。

## 6. Functional Requirements
原子化需求列表。
格式：
- REQ-001
  - Priority: P0/P1/P2
  - Statement:
  - Source: explicit | inferred | missing_confirmation
  - Evidence: 原 PRD 摘要或位置描述
  - Acceptance Criteria:
    - AC-001:

## 7. Non-Functional Requirements
性能、权限、兼容性、稳定性、国际化、可观测性等。
没有则写 `No explicit NFR found`，不能编造。

## 8. Technical Considerations
接口、字段、枚举、状态、配置、数据流、前端/BFF/后端边界。
不确定的写 `Needs owner confirmation`。

## 9. UI/UX Requirements
页面、表单、组件、文案、错误提示、预览、交互。
没有明确 UI 描述则写缺失。

## 10. Out of Scope
明确不做什么。
如果原 PRD 没写，列出 inferred risks，不要当事实。

## 11. Timeline & Milestones
里程碑、灰度、上线、依赖。
原 PRD 没有则标 missing。

## 12. Risks & Mitigations
列出冲突、歧义、缺字段、跨团队依赖、实现风险。

## 13. Open Questions
必须列出所有需要 owner 确认的问题。
每条包含：
- Question
- Why it matters
- Blocking level: P0/P1/P2
- Suggested owner: PM/FE/BFF/BE/QA/Unknown
```

### Source 标记规则

所有关键条目必须标注：

- `source: explicit`：原 PRD 明确写了。
- `source: inferred`：从上下文合理推断，但原文没有直接写清楚。
- `source: missing_confirmation`：缺失或冲突，必须确认。

硬约束：
1. `inferred` 不能进入最终 plan 的必做项，除非 report/questions 明确提示需确认。
2. `missing_confirmation` 必须进入 Open Questions（§13）。
3. `requirement-ir.yaml` 中每条 requirement 应能追溯到 ai-friendly-prd.md 的 REQ-ID。
4. `report.md` 中必须说明 AI-friendly PRD 的质量状态。
5. `plan.md` 不得把 `missing_confirmation` 当确定实现任务。

### context/prd-quality-report.yaml

格式见 `references/output-contracts.md` 中 `context/prd-quality-report.yaml` 章节。

评分规则（总分 100）：

| 维度 | 分值 | 说明 |
|---|---:|---|
| structure | 20 | 是否能映射到 13 个章节；是否有清晰标题/表格/列表；是否能区分背景、需求、规则、问题 |
| atomicity | 15 | 需求是否可拆成原子 REQ；是否混合多个动作；是否存在一条需求多个验收口径 |
| acceptance_criteria | 20 | 是否有可验证 AC；是否有数值范围、边界条件、错误提示；是否能转成测试条件 |
| constraints_and_scope | 15 | 是否有 out of scope；是否有权限、互斥、灰度、兼容、依赖边界 |
| technical_specificity | 15 | 是否有字段、枚举、状态、接口、配置、前端/BFF/后端边界 |
| ambiguity_risk | 15 | 模糊词越多扣分；冲突数字扣分；图片/表格无文字说明扣分；关键 owner 缺失扣分 |

状态阈值：
- 85-100：`pass`
- 60-84：`warning`
- 0-59：`fail`

硬降级：
- P0 需求超过 3 条 `missing_confirmation`：最多 `warning`
- 核心功能目标不明确：`fail`
- 无法提取 functional requirements：`fail`
- PRD 主要信息在图片/表格但未解析：`warning` 或 `fail`

### 后续步骤约束

- **Step 2 Requirement IR** 必须读取 `spec/ai-friendly-prd.md` 作为主输入，替代直接读取 `_ingest/document.md`。
- requirement-ir 中每条 requirement 应尽量引用 ai-friendly-prd 的 REQ-ID。
- **Step 8 Report** 必须包含 PRD quality 摘要（从 prd-quality-report.yaml 提取）。
- **Questions** 必须吸收 ai-friendly-prd §13 的 Open Questions。
- **Final Quality Gate** 可以读取 prd-quality-report.yaml 作为辅助信息。

## 步骤 2：Requirement IR

将 `spec/ai-friendly-prd.md` 转成 `context/requirement-ir.yaml`。

### 主输入

- **主输入**：`spec/ai-friendly-prd.md` + `context/prd-quality-report.yaml`。
- **证据回查**：`_ingest/document.md` 只用于证据回查和 block 定位，不是主输入。不允许直接从原始 PRD 推导 requirement，必须经过 AI-friendly PRD 的 REQ-ID 和 source 标记。

### Source 继承规则

requirement-ir 中每条 requirement 的 `source` 和 `planning.eligibility` 必须继承 AI-friendly PRD 的 source 状态：

| AI-friendly PRD source | requirement-ir `source` | `planning.eligibility` | `confirmation.status` |
|---|---|---|---|
| `explicit` | `explicit` | `ready`（如无其他阻塞） | `confirmed` |
| `inferred` | `inferred` | `assumption_only`（除非 report/questions 明确标注确认路径） | `needs_confirmation` |
| `missing_confirmation` | `missing_confirmation` | `blocked` | `blocked` |

硬约束：
1. `missing_confirmation` 必须进入 `open_question_refs`，且 `planning.eligibility=blocked`。
2. `inferred` 默认 `planning.eligibility=assumption_only`，不得直接进入确定开发 checklist。
3. report.md 和 plan.md 不得绕过 requirement-ir 直接从原始 PRD 推导确定任务。

### 降级规则

- 如果 acceptance_criteria 缺失或 `testability: not_testable`，`planning.eligibility` 不能为 `ready`。
- 如果 P0 requirement 是 `missing_confirmation`，`confirmation.status` 必须为 `blocked`。
- `assumption_only` / `blocked` 的 requirement 必须进入 report.md §11 或 §12。

### 消费 capability_inventory

读取 `_prd-tools/reference/04-routing-playbooks.yaml` 的 `capability_inventory`（如存在），用于区分已有能力与需新增能力：

- `generic_capabilities` 中 `status: verified` 的功能 → 不新增 REQ，但在相关 REQ 的 rules 中注明"复用已有 XXX 能力"。
- `dimensioned_capabilities` 中 `existing_entries` 不包含目标维度值 → 需要 ADD 类型 REQ。
- `missing_capabilities` 中的功能 → 标记 `confidence: low`，加入 `open_questions`。

### Requirement 字段（v5.0）

每个 requirement 必须包含：

- `id`：requirement-ir 自己的稳定 REQ-ID
- `ai_prd_req_id`：必须引用 `spec/ai-friendly-prd.md` 中的 REQ-ID
- `title`
- `statement`
- `priority`：P0 | P1 | P2
- `source`：继承 AI-friendly PRD 的 source（explicit / inferred / missing_confirmation）
- `intent`
- `change_type`
- `business_entities`
- `rules`
- `acceptance_criteria`：每条 AC 包含 `id`、`statement`、`source`、`testability`
- `target_layers`
- `evidence`：包含 `summary`、`location`、`source_block_ids`、`evidence_ids`
- `open_question_refs`：关联 ai-friendly-prd §13 的问题 ID
- `confirmation`：包含 `status`、`reason`、`suggested_owner`
- `planning`：包含 `eligibility`、`rule`
- `confidence`
- `risk_flags`

### 输出要求

- `meta.ai_prd_source` 必须设为 `"spec/ai-friendly-prd.md"`。
- `schema_version` 必须为 `"5.0"`。
- 所有 `missing_confirmation` requirement 必须同时出现在 `open_questions` 中。

原则：

- 业务规则、字段、枚举、限制、互斥、数量上限、流程差异都要拆成可追踪 requirement。
- 不要把实现方案直接混进 IR；实现影响放到 layer impact。
- 不确定项进入 `open_questions`。
- **逐 block 提取**：遍历 `document-structure.json` 的每个 block，确保没有段落/表格/图片被跳过。
- **AI-friendly PRD REQ-ID 对齐**：每条 requirement 应引用 `spec/ai-friendly-prd.md` 中的 REQ-ID（如 `AFPRD-REQ-001`），并在 `evidence` 中注明 source 标记（explicit / inferred / missing_confirmation）。

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

### 3.0 Requirement 消费

先从 `context/requirement-ir.yaml` 读取所有 requirements：

- **只允许 `planning.eligibility=ready` 的 requirement 进入确定性实现影响**。
- `planning.eligibility=assumption_only` 的 requirement 只能生成：risks、open questions、needs_confirmation、假设性影响。
- `planning.eligibility=blocked` 的 requirement 只能生成：risks、open questions、blocked 影响标注。
- 每个 IMP 必须继承 requirement 的 `ai_prd_req_id`、`requirement_source`、`planning_eligibility`。

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
13. 每条 GCTX entry 必须引用 `requirement_id`、`impact_id`（如已确定）、`ai_prd_req_id`、`layer`、`code_anchor id/file/symbol/line`、`confidence`、`evidence source`。
14. 生成 §3 Code Anchor 汇总表，为 report/plan 提供可直接引用的锚点清单。

始终生成 `context/graph-context.md`，记录实际执行的搜索查询、命中结果和**reference 消费记录**（从哪些 reference 文件提取了哪些路由/规则/实体）。

**门禁检查**：graph-context.md 中至少 30% 的线索应来自阶段 1-2（reference/index），否则在 readiness-report 中标记 `reference_underconsumed`。

### 3.2 Layer Impact 生成

读取目标层适配器：

- frontend / BFF / backend 单层：生成对应 impacts。
- multi-layer：每层各生成 impacts，并合并进一个 `context/layer-impact.yaml`。

每个 impact 必须说明：

- `id`：IMP 稳定 ID
- `requirement_id`：引用 requirement-ir 的 REQ-ID
- `ai_prd_req_id`：引用 AI-friendly PRD 的 REQ-ID
- `requirement_source`：继承 requirement 的 source
- `planning_eligibility`：继承 requirement 的 planning.eligibility
- `layer`
- `surface`
- `target` 文件/模块/接口/组件
- `current_state`
- `planned_delta`
- `code_anchors`：代码锚点列表（见下方规则）
- `dependencies`
- `risks`
- `evidence`
- `confidence`

### 3.3 Code Anchor 规则

为每个 `ready` requirement 建立：requirement_id → IMP-ID → code_anchors

**MODIFY / DELETE IMP**：
- 必须做负向搜索或源码确认。
- 必须至少有一个 `code_anchor`，除非明确写入 fallback reason。
- `code_anchor` 必须标注 `layer`、`file`、`symbol`、`line`（尽量精确）、`anchor_type`、`confidence`、`source`。

**ADD IMP**：
- 可以没有现有代码锚点。
- 但必须给 proposed target layer / module / surface。
- 如有相邻参考实现，应作为 `code_anchor` 引用。

**锚点来源**：
- `graph`：源码 Read 确认，最高置信度。
- `rg`：搜索命中但未 Read 确认，中等置信度。
- `reference`：知识库路由命中，需源码二次确认。
- `inferred`：推断，不得作为唯一 high confidence 证据。

**低置信度 anchor**：必须进入 report 风险或 plan 假设。

ADD/MODIFY/DELETE/NO_CHANGE 必须由源码或负向搜索支撑。

源码扫描增强：

- 优先消费 `context/graph-context.md`，不要在 plan/report 阶段重新凭空猜函数。
- 将源码扫描命中的符号写入 impact 条目的 `code_anchors` 和 `graph_evidence_refs`。
- 将业务约束写入 impact 条目的 `business_constraints`。

### 3.4 Report / Plan 消费约束

- `report.md` 和 `plan.md` 中的每个 checklist 项必须引用：REQ-ID、IMP-ID、至少一个 code_anchor 或 fallback reason。
- `planning.eligibility != ready` 的 requirement 不得生成确定性实现任务。
- report/plan 不得绕过 layer-impact 直接编造目标文件。

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
- **`missing_confirmation` 不得作为确定实现任务**：ai-friendly-prd 中标注为 `missing_confirmation` 的需求不得写入 plan 的确定实现 checklist，只能写入"待确认"或"假设前提"章节。
- 格式详见 `references/schemas/04-report-plan.md` 中 plan.md 模板。

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
2. **PRD 质量摘要**（来自 prd-quality-report.yaml）：AI-friendly PRD 评分、source 分布（explicit/inferred/missing）、关键缺失项
3. **源码扫描命中摘要**：命中的关键函数/流程/业务约束、未命中原因
4. **影响范围**：命中的层、能力面、关键文件
5. **关键结论**：带 REQ-ID、代码路径和源码扫描证据
6. **变更明细表**：所有 IMP-* 项，精确到文件路径
7. **字段清单**：按功能模块分组，含类型/必填/契约ID
8. **校验规则**：规则描述 + 错误文案 + 目标文件
9. **开发 Checklist**：可直接执行的操作列表
10. **契约风险**：needs_confirmation / blocked 项
11. **Top Open Questions**：最多5个（必须吸收 `spec/ai-friendly-prd.md` §13 的 Open Questions）
12. **阻塞问题与待确认项**：阻塞问题（6 要素）+ 低置信度假设 + Owner 确认项

格式详见 `references/schemas/04-report-plan.md` 中 report.md 模板。

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

## 步骤 8.6：Distill Completion Gate（硬约束）

> **定位**：Distill Completion Gate 是 /prd-distill 的硬完成门禁。不通过不得宣称 /prd-distill 完成。

运行命令：

```bash
python3 .prd-tools/scripts/distill-quality-gate.py \
  --distill-dir _prd-tools/distill/<slug> \
  --repo-root .
```

检查内容：

1. required distill files 是否存在且非空
2. spec/ai-friendly-prd.md 是否包含 13 个章节
3. context/prd-quality-report.yaml 是否存在 status/score
4. requirement-ir.yaml 是否包含 ai_prd_req_id
5. requirement-ir.yaml 是否包含 planning eligibility 相关字段
6. layer-impact.yaml 是否包含 code_anchors 或 fallback/fallback_reason
7. 若 _prd-tools/reference/index 存在：query-plan.yaml 和 context-pack.md 必须存在
8. final-quality-gate.yaml 必须存在
9. report.md 必须包含 PRD 质量摘要
10. plan.md 不应包含把 missing_confirmation 当确定任务的内容

门禁规则：

- exit code 2（fail）：必须补缺失文件，不得宣称 /prd-distill 完成。
- exit code 0（pass 或 warning）：可以完成，但 warning 必须写入 report 或最终回复。

## 步骤 9：Portal HTML 生成

运行脚本生成 `_prd-tools/distill/<slug>/portal.html`，将所有蒸馏产物内联为一个自包含的可视化页面：

```bash
python3 .prd-tools/scripts/render-distill-portal.py \
  --distill-dir _prd-tools/distill/<slug> \
  --template .prd-tools/assets/distill-portal-template.html \
  --out _prd-tools/distill/<slug>/portal.html
```

**AI 不得手写 portal.html**，必须通过脚本渲染生成。

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
