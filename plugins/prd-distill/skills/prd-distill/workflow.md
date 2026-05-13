# prd-distill 工作流

> **加载指引**：每个 step 只需加载 workflow.md 对应段落 + step 文件 + output-contracts.md 对应 schema 段，不需要全文加载。按需读取可显著降低 attention decay。

## 目标

把 PRD 蒸馏为工程可执行的结论、计划和证据链。采用**三段式工作流**：

```text
PRD raw file/text
  → /prd-distill spec      (Steps 0→1→1.5→2)
  → /prd-distill report    (Steps 2.5→3.1→3.2→4→8→8.1)
  → user confirmation      (report-confirmation.yaml)
  → /prd-distill plan      (Steps 5→6→8.5→8.6→9)
```

## Step 文件 ↔ Gate Step ID 映射

> Step numbers are logical IDs, NOT execution order. Follow the three-stage execution sequence from command.md.

| Step 文件 | 覆盖的 Gate Step IDs | 所属 Stage |
|---|---|---|
| step-01-parse.md | 0, 1, 1.5-afprd, 1.5-quality, 2 | spec |
| step-02-classify.md | 2.5, 3.1, 3.2, 3.5, 3.6, 4 | report |
| step-03-confirm.md | 8, 8.1-confirm, 5, 6, 7, 8.5, 8.6 | report + plan |

每个阶段的核心问题：

| 阶段 | 核心问题 | 是否读源码 | 是否需要用户确认 |
|------|----------|------------|------------------|
| spec | PRD 本身到底说了什么 | 默认不读源码 | 不强制，但输出 open questions |
| report | 这个 PRD 放到当前项目会影响什么 | 必须读 reference / index / 源码 | 必须确认 |
| plan | 在确认后的影响分析基础上怎么实施 | 只消费确认后的 report 和 context | 不再重新解释 PRD |

主流程对前端、BFF、后端通用；层差异通过 `references/layer-adapters.md` 的能力面适配器生效。默认给人看轻量输出，机器可读细节放入 `context/`。

短入口：

- `/prd-distill spec <PRD>`：只运行 spec 阶段，不生成 report.md 和 plan.md。
- `/prd-distill report <slug>`：运行 report 阶段，生成 report.md 后暂停等待用户确认。
- `/prd-distill plan <slug>`：运行 plan 阶段，需 report-confirmation.yaml status: approved。
- `/prd-distill <PRD>`：引导式入口，不自动生成 plan。

## 团队模式自动检测（v2.20）

执行前，读取 `_prd-tools/reference/project-profile.yaml`（或 `team/project-profile.yaml`）。如果 `layer: "team-common"`，进入团队模式：

- 从 `team_reference.member_repos[]` 获取成员仓列表（`repo`、`layer`、`local_path`/`remote_url`）
- Step 2.5 / 3.5：**跳过**（团队仓无 `_prd-tools/reference/index/`）
- Step 3.1：数据源改为 `team/01-codebase.yaml` cross_repo_entities + `snapshots/{layer}/{repo}/` 下钻，**禁止 rg/glob**
- Step 3.2：4 层 IMP 全部从 snapshots 填充
- Step 4：contract delta 消费 `team/03-contracts.yaml` 全栈 consumers[]
- Step 5：生成 `team-plan.md` + `plans/plan-{repo}.md`（文件名从 `member_repos[].repo` 动态生成）
- Step 8：report.md §10 强制 4 个子节（10.1–10.4）

---

# ── spec 阶段 ──

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
- report.md §12 必须暴露："本次蒸馏未消费 reference，影响分析和契约检查可能不完整"。

创建输出目录：

```text
_prd-tools/distill/<slug>/
├── _ingest/
├── report.md
├── plan.md
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
- `warn`：可继续，但必须把图片未分析、复杂表格风险写入 `report.md` §12。
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
6. 每个 REQ-ID 必须在 ai-friendly-prd.md §6 中有对应的 `### REQ-XXX` 标题锚点，确保 requirement-ir.yaml 到 ai-friendly-prd.md 的追溯链完整。缺失的 REQ-ID 标题必须在 prd-quality-report.yaml 中标记为 warning。

### Self-Check（afprd 生成后）

- [M] `spec/ai-friendly-prd.md` 每个章节标题格式为 `## N. EnglishName` 或 `## N. EnglishName（中文）`，N 从 1 到 13
  verify: `python3 -c "import re; m={'Overview','Problem Statement','Target Users','Goals & Success Metrics','User Stories','Functional Requirements','Non-Functional Requirements','Technical Considerations','UI/UX Requirements','Out of Scope','Timeline & Milestones','Risks & Mitigations','Open Questions'}; t=open('spec/ai-friendly-prd.md').read(); found={x for x in m if re.search(rf'^##\s+(?:\d+\.?\s+)?{re.escape(x)}', t, re.M)}; assert found==m, sorted(m-found)"`
  expect: exit 0

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

- **Step 2 Requirement IR** 以 `_ingest/document.md` 为主输入，`spec/ai-friendly-prd.md` 为 REQ-ID 索引辅助（不替代原始内容）。
- requirement-ir 中每条 requirement 应尽量引用 ai-friendly-prd 的 REQ-ID。
- **Step 8 Report** 必须包含 PRD quality 摘要（从 prd-quality-report.yaml 提取）。
- **Questions** 必须吸收 ai-friendly-prd §13 的 Open Questions。
- **Final Quality Gate** 可以读取 prd-quality-report.yaml 作为辅助信息。

## 步骤 2：Requirement IR

将原始 PRD 需求转成 `context/requirement-ir.yaml`。

### 主输入

- **主输入**：`_ingest/document.md`（原始 PRD 全文）。
- **索引辅助**：`spec/ai-friendly-prd.md`（REQ-ID 框架 + 章节索引，用于定位和结构化，不替代原始内容）。
- **证据指针**：`_ingest/evidence-map.yaml` + `_ingest/document-structure.json`（block 级切片和覆盖追踪）。
- **质量参考**：`context/prd-quality-report.yaml`。
- 不允许只读 ai-friendly-prd.md 就生成 requirement-ir，必须回查 document.md 获取完整细节。

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
- `evidence`：包含 `summary`、`location`、`source_blocks` 或 `source_block_ids`（原始 PRD block_id 列表，至少一个非空；新产物用 source_blocks，旧产物保留 source_block_ids 兼容）、`evidence_ids`
- `open_question_refs`：关联 ai-friendly-prd §13 的问题 ID
- `confirmation`：包含 `status`、`reason`、`suggested_owner`
- `planning`：包含 `eligibility`、`rule`
- `confidence`
- `risk_flags`

### 输出要求

- `meta.primary_source` 必须设为 `"_ingest/document.md"`。
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

> query-plan.yaml 由 `context-pack.py` 脚本自动生成，LLM 不需要手写。每个 phase 条目为 string 类型。

```yaml
schema_version: "1.0"
phases:
  seed_anchors: []        # 从 requirement-ir 提取的种子查询词
  impact_hints: []        # 从 layer-impact 提取的文件路径提示
  p0_requirements: []     # P0 需求的关键实体和术语
```

**团队模式**：跳过此步骤。团队仓无 `_prd-tools/reference/index/`，不生成 query-plan.yaml。Step gate 会自动通过。

## 步骤 3.5：Context Pack（Reference Index 融合层）

> **定位**：Context Pack 融合 Evidence Index 与 distill 上下文，为 report/plan 提供精简代码坐标。当 index 存在时**必须运行**。

在步骤 3.2（Layer Impact）完成后、步骤 4（Contract Delta）之前，**必须**运行 `python3 .prd-tools/scripts/context-pack.py`（此时 layer-impact.yaml 已存在），生成 `context/context-pack.md`，将 Evidence Index 中的代码实体与 distill 上下文融合，形成模型可直接消费的精简上下文（建议 ≤800 行）。

触发时机：步骤 3.2 完成后、步骤 4 之前。如果索引不存在则跳过，但必须在 readiness-report 中记录缺失。

**团队模式**：跳过此步骤。团队仓无 index，不生成 context-pack.md。Step gate 会自动通过。

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

**推测信息约束**：所有"推测"/"speculative"信息（如未确认的接口路径、未验证的调用关系）必须加 `⚠ speculative, confidence=<low|medium>, verify before use` 前缀，否则不得出现在 `graph-context.md` 中。

**团队模式数据源**（`layer: team-common` 时）：
1. 读取 `team/01-codebase.yaml` 的 `cross_repo_entities`，获取 PRD 相关的跨仓实体映射
2. 对每个 REQ，从 cross_repo_entities 匹配实体，获取 `defined_in.repo`/`defined_in.file` 和 `consumed_by[]`
3. 需要代码细节时，下钻到 `snapshots/{layer}/{repo}/01-codebase.yaml` 获取 modules、registries、data_flows
4. 需要契约细节时，读 `snapshots/{layer}/{repo}/03-contracts.yaml`
5. 团队 fatal 规则从 `team/02-coding-rules.yaml` 读取
6. 团队术语从 `team/05-domain.yaml` 读取
7. **禁止执行 rg/glob 命令**——团队仓没有源码，所有 GCTX entry 标记 `source: "team_snapshot"`

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

**团队模式**：4 层 IMP 全部从 `snapshots/` 填充。每层的 `code_anchors` 指向 snapshots 文件路径（如 `snapshots/frontend/genos/01-codebase.yaml` 中的模块）。confidence 为 `medium`（未直接验证源码），除非被多个 snapshot 交叉验证（此时可为 `high`）。

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
- 将源码扫描命中的符号写入 impact 条目的 `code_anchors` 和 `graph_evidence_refs`（aspirational，尚未在 schema 中定义）。
- 将业务约束写入 impact 条目的 `business_constraints`。

### 3.4 Report / Plan 消费约束

- `report.md` 和 `plan.md` 中的每个 checklist 项必须引用：REQ-ID、IMP-ID、至少一个 code_anchor 或 fallback reason。
- `planning.eligibility != ready` 的 requirement 不得生成确定性实现任务。
- report/plan 不得绕过 layer-impact 直接编造目标文件。

## 步骤 3.6：Critique Pass（Two-Pass Critic）

> 在高风险步骤完成后立即执行，对产物做二次审查。详细模板见 `steps/critique-template.md`。

### 何时触发

以下步骤完成后，**必须**执行 critique pass：

- Step 1.5: AI-friendly PRD 生成后
- Step 2: Requirement IR 生成后
- Step 3.2: Layer Impact 生成后
- Step 4: Contract Delta 生成后

### 执行方式

1. **只读本步骤产物 + 上一步产物 + 对应 contract**。不扩大上下文。
2. 按 `steps/critique-template.md` 的检查维度逐项审查。
3. **输出 `context/critique/<step_id>.yaml`**，格式如下：

```yaml
schema_version: "1.0"
step: "<step_id>"
artifact: "<被检查的产物路径>"
status: "pass | warning | fail"
findings:
  - id: "F-001"
    severity: "fatal | warning"
    rule: "<对应 contract rule_id 或自由描述>"
    issue: "<具体问题>"
    fix: "<建议修正方式>"
```

### 结果处理

- **`status: fail`**：退回上一步修正产物，`distill-workflow-gate.py` 会阻断后续步骤。
- **`status: warning`**：不阻断流程，但必须进入 `readiness-report.yaml` 的 risks 部分。
- **`status: pass`**：继续下一步。

**输入**：当前步骤产物、上一步产物、对应 contract 文件
**输出**：`context/critique/<step_id>.yaml`

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

**团队模式**：全栈视角。每条 delta 的 `consumers[]` 从 `team/03-contracts.yaml` 的 `consumer_repos` 填充，`checked_by[]` 从聚合状态获取。每层契约基线从对应 `snapshots/{repo}/03-contracts.yaml` 读取。

# ── plan 阶段 ──

> **前置条件**：`context/report-confirmation.yaml` 必须为 `status: approved`。
> 未 approved 时不得生成 plan.md。
> plan 阶段不重新解释原始 PRD，只消费 approved report 和 context。

## 步骤 5：计划

生成 `plan.md`（函数级技术方案文档 + 开发计划）：

- 前置条件：`context/report-confirmation.yaml` 存在且 `status: approved`。
- 如果 report 尚未确认，只能停止并请求用户确认，不得生成最终 `plan.md`。
- 精确到文件路径和行号。
- 包含 11 个章节：范围与假设、整体架构、实现计划、API 设计、数据存储、配置与开关、校验规则汇总、QA 矩阵、契约对齐、风险与回滚、工作量估算。
- 用 `- [ ]` checklist 格式，可直接勾选。
- 每个任务包含：目标文件、操作描述、参考实现、关联 REQ/IMP/CONTRACT、验证命令。
- 每个 MODIFY/DELETE 任务必须引用 `graph-context.md` 中的函数级线索；ADD 任务必须引用相邻参考实现或负向搜索证据。
- 技术方案必须说明关键调用链、入口函数、下游 consumer 和回归范围。
- **代码线索不可省略**：文件路径、行号、参考结构体名必须保留。
- 按 Phase 分组，Phase 间标注依赖。
- 不直接写代码，除非用户明确要求进入实现。
- **`missing_confirmation` 不得作为确定实现任务**：ai-friendly-prd 中标注为 `missing_confirmation` 的需求不得写入 plan 的确定实现 checklist，只能写入"待确认"或"假设前提"章节。
- 格式详见 `references/schemas/04-report-plan.md` 中 plan.md 模板。

**团队模式 plan 生成**：

生成 `team-plan.md`（团队级总览）+ N 份 `plans/plan-{repo}.md`（成员仓 sub-plan）。

`team-plan.md` 结构：
1. **范围与假设**：目标、跨仓依赖、成员仓角色表（来自 member_repos）
2. **跨仓架构**：代码坐标总览（按 repo 分组，来自 cross_repo_entities）、跨仓调用链、关键设计决策
3. **跨仓时序**：Phase 1-N 跨仓依赖图、每个仓的交付里程碑
4. **Sub-Plan 索引表**：动态列出所有 sub-plan 文件名 + 对应仓 + IMP 数
5. **契约对齐（全栈）**：从 contract-delta.yaml 提取跨仓契约摘要
6. **风险与回滚**：跨仓联调风险、回滚策略
7. **工作量总览**：按仓汇总

`plans/plan-{repo}.md`：复用标准 11-section plan 模板，但 scope 限定到单个成员仓。每份 sub-plan 的 IMP 从 `layer-impact.yaml` 中该仓对应层的 entries 提取。

文件名生成规则：`member_repos[].repo` 值直接用作 `plan-{repo}.md`（如 `repo: "dive-bff"` → `plans/plan-dive-bff.md`）。

**禁止硬编码**：sub-plan 文件名必须从 `member_repos[].repo` 动态生成，不得硬编码特定仓库名。

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
- `provider_value.reference`: 必须包含 `reused_playbooks`, `reused_contracts`, `examples` 三个字段，统计 reference 被复用的数量（团队公共库 ROI 指标）。
- `scores`: 必须包含 `prd_ingestion`, `evidence_coverage`, `code_search`, `contract_alignment`, `task_executability` 5 个维度。
- `next_actions`: 最多 5 条，优先处理 blocked 和 needs_confirmation。

## 步骤 7：Reference 回流

生成 `context/reference-update-suggestions.yaml`：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "_prd-tools/reference/04-routing-playbooks.yaml"
    summary: ""
    current_repo_scope:
      authority: "single_repo"
      action: "apply_to_current_repo | record_as_signal | needs_owner_confirmation"
    owner_to_confirm: []
    team_reference_candidate: false
    team_scope:
      type: "contract | domain_term | playbook | decision | routing_signal | golden_sample"
      related_repos: []
      aggregation_status: "candidate | confirmed | rejected | not_applicable"
    evidence: ["EV-001"]
    graph_context_refs: []  # aspirational：尚未在 schema 中定义
    priority: "high | medium | low"
    confidence: "high | medium | low"
    proposed_patch: ""
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

**团队模式 report §10**：必须包含 4 个显式子节：
- §10.1 Frontend：前端层 IMP 和契约
- §10.2 BFF：BFF 层 IMP 和契约
- §10.3 Backend：后端层 IMP 和契约
- §10.4 External：外部系统影响（如有）

## 步骤 8.1：Report Review Gate（人类确认）

`report.md` 是最终 `plan.md` 的理解基础。生成 report 后必须暂停，让用户确认 AI 对 PRD、影响范围、契约风险和阻塞项的理解是否符合预期。

### 确认流程

1. 生成 `report.md`。
2. 向用户展示 report 摘要：
   - 需求摘要
   - 影响层和关键文件
   - 契约风险
   - Top Open Questions / 阻塞项
3. 询问用户：
   - `approved`：report 符合预期，可以生成最终 plan。
   - `needs_revision`：report 有偏差，需要说明要改哪里。
   - `blocked`：信息不足，暂停。
4. 将确认结果写入 `context/report-confirmation.yaml`。
5. 只有 `status: approved` 时，才允许进入步骤 5 生成最终 `plan.md`。

```yaml
schema_version: "1.0"
status: "approved | needs_revision | blocked"
confirmed_by: "user"
confirmed_at: ""
approved_sections:
  - "requirements"
  - "layer_impact"
  - "contract_delta"
  - "open_questions"
revision_requests:
  - section: ""
    issue: ""
    expected_change: ""
blocked_reason: ""
```

### 修正规则

- `needs_revision` 时，不要直接改 plan。必须回到对应上游产物修正：
  - 需求理解错 → 修 `spec/ai-friendly-prd.md` 和 `context/requirement-ir.yaml`
  - 影响范围错 → 修 `context/graph-context.md` 和 `context/layer-impact.yaml`
  - 契约判断错 → 修 `context/contract-delta.yaml`
  - 阻塞项错 → 修 `report.md` §12 和 readiness 输入
- `blocked` 时，不生成 plan、readiness 或 final-quality-gate。
- 如果用户明确说“跳过确认，直接生成 plan”，也必须写入 `report-confirmation.yaml`，`status: approved`，并在 `approved_sections` 中记录 `user_explicit_skip_review`。

### Report 质量门禁

生成 `report.md` 前必须重新读取 `context/requirement-ir.yaml`、`context/graph-context.md`、`context/contract-delta.yaml` 和 `context/context-pack.md`，核对报告已覆盖下列高收益信息。缺任一项时，不要用泛化总结替代，必须补进对应章节或 §12：

- P0/P1 需求中从 requirement-ir 提取的配置细节、业务约束和数值范围。
- PRD 内部矛盾或疑似 typo：同一字段出现不一致的数值范围或互斥描述。此类内容必须进入 §12 阻塞问题或低置信度假设。
- 关键代码锚点：graph-context.md 中标记为 `must` 的 code anchors，report/plan 不得遗漏其风险说明。
- reference 只作为候选事实和路由依据；任何 reference 结论必须被源码、PRD、技术文档或负向搜索二次确认。未确认时降为 `confidence: low|medium` 并进入 §12。

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

触发时机：步骤 8（report.md）完成后。

**团队模式**：检查 `team-plan.md` + `plans/` 目录（而非 `plan.md`）。

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

## 步骤 8.6.1：Gate 检查清单

> 条件步骤：运行 `distill-quality-gate.py` 和 `distill-workflow-gate.py`，确认所有 gate 通过。

**输入**：所有 context 文件、report.md、plan.md

**输出**：无文件产出（gate 检查结果）

**检查项**：

1. 运行 `python3 .prd-tools/scripts/distill-quality-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`，exit code 不为 2。
2. 运行 `python3 .prd-tools/scripts/distill-workflow-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`，exit code 不为 2。
3. 两个 gate 都通过即可完成。

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
7. **report.md 和 plan.md 是主产物**；query-plan、context-pack、final-quality-gate 是辅助层，不替代主产物的阅读优先级。
8. **⚠ Reference 强制消费**：`_prd-tools/reference/` 存在时，必须消费。Step 0 消费门禁（路由/规则/契约/术语）→ Step 2.5 桥接 index → Step 3.1 reference-first 扫描。禁止跳过 reference 直接 grep 源码。reference 不存在时，所有涉及 reference 的步骤必须标记缺失并降低置信度。
9. **三段式硬约束**：
   - spec 阶段不得生成 `report.md` 或 `plan.md`。
   - report 阶段不得生成 `plan.md`。
   - plan 阶段必须检查 `context/report-confirmation.yaml` 为 `status: approved`。
   - plan 阶段不得重新解释原始 PRD，只消费 approved report 和 context。
