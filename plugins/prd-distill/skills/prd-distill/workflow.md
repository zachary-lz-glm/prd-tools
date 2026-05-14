# prd-distill 工作流

## 目标

把 PRD 蒸馏为工程可执行的结论、计划和证据链。主流程对前端、BFF、后端通用；层差异通过 `references/layer-adapters.md` 的能力面适配器生效。

入口：`/prd-distill <PRD 文件或需求文本>`

流程在生成 `report.md` 后暂停，等用户确认后再生成 `plan.md`。

---

## 步骤 0：PRD Ingestion

读取或收集：

- PRD：`.md | .txt | .docx | pasted text`。
  - `.md`/`.txt`：直接读取。
  - `.docx`：用 `unzip` 提取 `word/document.xml`（文本）和 `media/`（图片）。文本去 XML 标签后写入 `_ingest/document.md`，图片拷贝到 `_ingest/media/`。在文本中图片位置插入 `![image-N](media/imageN.png)` 占位。Claude 用 Read 工具逐个查看图片（原生多模态），理解 UI 截图、流程图、数据图表，结果写入 `_ingest/media-analysis.yaml`。
  - 粘贴文本：手工建立来源和定位。
- 技术方案 / API 文档：可选，但多层或后端相关需求强烈建议读取。
- `_prd-tools/reference/`：必须读取并消费。
- 目标代码库：用于代码锚定。

### Reference 消费（Step 0 之后必须完成）

如果 `_prd-tools/reference/` 存在，必须消费：

1. **路由映射**（`04-routing-playbooks.yaml`）：建立 PRD 关键词 → target_surfaces → playbook_ref 映射表。
2. **代码地图**（`01-codebase.yaml`）：提取 modules、registries、data_flows、enums、external_systems。
3. **编码规则**（`02-coding-rules.yaml`）：提取 fatal 级规则。
4. **契约**（`03-contracts.yaml`）：提取现有 API 契约作为基线。
5. **领域术语**（`05-domain.yaml`）：提取 terms 和 implicit_rules。

将消费状态写入 `context/evidence.yaml`（`EV-REF-CONSUMED`）。

如果 reference 不存在：layer-impact/contract-delta confidence 强制降为 `low`，report.md 暴露缺失。

创建输出目录：

```text
_prd-tools/distill/<slug>/
├── _ingest/
├── report.md
├── plan.md
└── context/
```

_ingest/ 结构：

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
- `warn`：可继续，但必须把风险写入 report.md。
- `block`：暂停，要求用户提供 markdown/text。

## 步骤 1：证据台账

建立 `context/evidence.yaml`，后续所有判断只引用 evidence id。

证据类型：`prd`、`tech_doc`、`code`、`git_diff`、`negative_code_search`、`human`、`api_doc`、`reference`。

规则：
- PRD 原文证据优先从 `_ingest/evidence-map.yaml` 映射。
- 源码证据要能定位文件和符号；尽量带行号。
- 搜不到也是证据，用 `negative_code_search`。
- 没有人工确认的图片不能生成高置信度需求。

## 步骤 2：Requirement IR

将原始 PRD 需求转成 `context/requirement-ir.yaml`。

主输入：`_ingest/document.md`（原始 PRD 全文）。

每个 requirement 必须包含：

- `id`：稳定 REQ-ID
- `title`、`statement`
- `priority`：P0 | P1 | P2
- `intent`
- `change_type`：ADD | MODIFY | DELETE | NO_CHANGE
- `business_entities`
- `rules`
- `acceptance_criteria`：每条 AC 包含 `id`、`statement`、`testability`
- `target_layers`
- `evidence`：`summary`、`location`、`source_blocks`、`evidence_ids`
- `open_question_refs`
- `confidence`
- `risk_flags`

原则：
- 业务规则、字段、枚举、限制、互斥、数量上限、流程差异都要拆成可追踪 requirement。
- 不把实现方案混进 IR。
- 不确定项进入 `open_questions`。
- 逐 block 提取：遍历 `document-structure.json` 的每个 block，确保无遗漏。

降级规则：
- acceptance_criteria 缺失或 `testability: not_testable` 时，`confidence` 不能为 `high`。
- P0 requirement 如果信息严重不足，必须进入 `open_questions`。

## 步骤 2.5：Query Plan（Reference Index 桥接层）

如果 `_prd-tools/reference/index/` 存在，运行 `context-pack.py` 生成 `context/query-plan.yaml`：

```bash
python3 .prd-tools/scripts/context-pack.py \
  --distill _prd-tools/distill/<slug> \
  --index _prd-tools/reference/index \
  --out _prd-tools/distill/<slug>/context/context-pack.md
```

产出 `context/query-plan.yaml`，为后续源码扫描提供预匹配的代码锚点。

## 步骤 3：Layer Impact

### 3.1 Graph Context（Reference-First 源码扫描）

生成 `context/graph-context.md`。

对每个 REQ 按以下优先级执行扫描：

**阶段 1：Reference 路由**
1. 从 requirement-ir 提取业务实体、字段名、接口名、动作词。
2. 将关键词与 `04-routing-playbooks.yaml` 匹配，确定 target_surfaces。
3. 从 `01-codebase.yaml` 提取精确文件路径和符号列表。
4. 如存在 `query-plan.yaml`，读取 `matched_entities` 获取预匹配锚点。

**阶段 2：补充扫描**
5. 用 `rg`/`glob` 搜索阶段 1 未覆盖的业务实体和动作词。
6. 用 `Read` 读取命中文件，获取 callers、callees、imports。
7. 对 MODIFY/DELETE 候选用 `rg` 追踪引用链，评估 blast radius。

**阶段 3：汇总**
8. 将命中的符号写成函数级技术线索：`symbol`、`kind`、`file:line`、`role_in_flow`、`callers`、`callees`、`risk`。
9. 每条线索标注来源：`reference_routing` | `code_scan`。

始终生成 `context/graph-context.md`，记录实际执行的搜索查询和命中结果。

### 3.2 Layer Impact 生成

读取目标层适配器，生成 `context/layer-impact.yaml`。

每个 impact 必须说明：

- `id`：IMP 稳定 ID
- `requirement_id`：引用 REQ-ID
- `layer`、`surface`
- `target`：文件/模块/接口/组件
- `current_state`、`planned_delta`
- `code_anchors`：代码锚点列表
- `dependencies`、`risks`、`evidence`、`confidence`

### 3.3 Code Anchor 规则

**MODIFY / DELETE IMP**：
- 必须至少有一个 `code_anchor`（`layer`、`file`、`symbol`、`line`、`confidence`、`source`），除非明确写入 fallback reason。

**ADD IMP**：
- 可以没有现有锚点，但必须给 proposed target。

锚点来源：`graph`（源码确认）| `rg`（搜索命中）| `reference`（知识库路由）| `inferred`（推断）

低置信度 anchor 必须进入 report 风险或 plan 假设。

### 3.5 Context Pack（Index 融合层）

在步骤 3.2 完成后，如果索引存在，运行：

```bash
python3 .prd-tools/scripts/context-pack.py \
  --distill _prd-tools/distill/<slug> \
  --index _prd-tools/reference/index \
  --out _prd-tools/distill/<slug>/context/context-pack.md
```

## 步骤 4：Contract Delta

多层、接口、schema、事件等需求必须生成 `context/contract-delta.yaml`。单层无契约变化时也创建最小文件。

每个 contract 记录：

- producer、consumers
- contract_surface
- request_fields、response_fields
- alignment_status：`aligned` | `needs_confirmation` | `blocked` | `not_applicable`
- checked_by、evidence

## 步骤 5：计划

前置：`context/report-confirmation.yaml` 存在且 `status: approved`。

生成 `plan.md`（函数级技术方案 + 开发计划）：

- 精确到文件路径和行号。
- 11 个章节：范围与假设、整体架构、实现计划、API 设计、数据存储、配置与开关、校验规则汇总、QA 矩阵、契约对齐、风险与回滚、工作量估算。
- 用 `- [ ]` checklist 格式。
- 每个任务包含：目标文件、操作描述、参考实现、关联 REQ/IMP/CONTRACT、验证命令。
- 按 Phase 分组，Phase 间标注依赖。
- 格式详见 `references/schemas/04-report-plan.md`。

## 步骤 6：Readiness 评分

生成 `context/readiness-report.yaml`。

数据来源：`_ingest/extraction-quality.yaml`、`context/evidence.yaml`、`context/requirement-ir.yaml`、`context/graph-context.md`、`context/contract-delta.yaml`、`plan.md`。

输出：
- `status`: `pass | warning | fail`
- `score`: 0-100
- `decision`: `ready_for_dev | needs_owner_confirmation | blocked`
- `scores`: prd_ingestion / evidence_coverage / code_search / contract_alignment / task_executability
- `next_actions`: 最多 5 条

## 步骤 7：Reference 回流

生成 `context/reference-update-suggestions.yaml`。

触发条件：
- PRD 出现 reference 没有的术语、枚举、路由、契约或场景。
- reference 说已实现但源码不存在，或源码存在但 reference 缺失。
- 本次需求能作为高价值 golden sample。

边界：`/prd-distill` 只产出回流建议，不直接编辑 `_prd-tools/reference/`。

## 步骤 8：人类报告

`report.md` 渐进式披露结构：

1. **需求摘要**（30秒决策）
2. **源码扫描命中摘要**
3. **影响范围**
4. **关键结论**：带 REQ-ID 和代码路径
5. **变更明细表**：所有 IMP-* 项
6. **字段清单**：按功能模块分组
7. **校验规则**
8. **开发 Checklist**
9. **契约风险**
10. **Top Open Questions**：最多 5 个
11. **阻塞问题与待确认项**：阻塞问题（6 要素）+ 低置信度假设 + Owner 确认项

格式详见 `references/schemas/04-report-plan.md`。

## 步骤 8.1：Report Review Gate

生成 report.md 后必须暂停，让用户确认：

1. 向用户展示 report 摘要。
2. 询问：`approved` | `needs_revision` | `blocked`。
3. 写入 `context/report-confirmation.yaml`。
4. 只有 `approved` 时才允许进入步骤 5 生成 plan。

```yaml
schema_version: "1.0"
status: "approved | needs_revision | blocked"
confirmed_by: "user"
confirmed_at: ""
revision_requests: []
blocked_reason: ""
```

修正规则：
- `needs_revision`：回到对应上游产物修正，不在 plan 里打补丁。
- `blocked`：停止蒸馏。

## 步骤 8.5：Final Quality Gate

```bash
python3 .prd-tools/scripts/quality-gate.py final \
  --distill _prd-tools/distill/<slug>
```

5 项检查：required_files / context_pack_consumed / code_anchor_coverage / plan_actionability / blocker_quality。

## 暂停条件

- PRD 无法读取且无文本输入。
- `extraction-quality.yaml` 为 `block`。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据且无法补齐。

## 执行规则

1. 先证据，后结论。
2. IR 描述业务意图，impact 描述代码影响，contract 描述跨层接口。
3. 业务规则不能只靠前端守。
4. 多层需求必须给契约计划。
5. 每个输出都要能回溯 evidence。
6. 完成后告知输出路径和最重要的阻塞/风险。
7. report.md 和 plan.md 是主产物；query-plan、context-pack、final-quality-gate 是辅助层。
8. reference 存在时必须消费。不存在时标记缺失并降低置信度。
