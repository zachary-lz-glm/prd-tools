# reference 工作流

## 目标

构建 reference v4.0，让后续 `/prd-distill` 能稳定产出：

`report -> plan -> questions -> artifacts -> Reference 回流`

reference 是"可验证指南针"，不是项目百科。6 个文件，每个事实只存在一处（SSOT），按场景阅读。

短入口：

- `/reference`：日常使用入口，执行本 workflow 的各个模式。

默认治理范围是单仓：当前仓 `_prd-tools/reference/` 只沉淀本仓确认事实。跨仓契约、上下游 owner、团队级 taxonomy 可以作为候选或 handoff 记录，但在 owner 确认前不能升级为确定事实。

## 定位

prd-tools 负责 PRD-to-code 全链路的发现、证据治理和质量门控，产出单仓可治理的 reference 知识库。

## Phase

| Phase | 名称 | 输入 | 输出 |
|---|---|---|---|
| 1 | 上下文收集 | 历史 PRD、技术方案、分支 diff、发布/返工记录 | `_prd-tools/build/context-enrichment.yaml` |
| 2 | 结构扫描 | 项目目录、核心源码、git 历史 | `_prd-tools/build/modules-index.yaml` |
| 3 | 深度分析 | modules-index、源码、能力面适配器 | `_prd-tools/reference/` v4.0 |
| 4 | 质量门控 | reference、源码、样例需求 | `_prd-tools/build/quality-report.yaml` |
| 5 | Evidence Index | reference、项目源码 | `_prd-tools/reference/index/`（辅助层） |
| 6 | 反馈回流 | `/prd-distill` 输出、源码、reference | `_prd-tools/build/feedback-report.yaml` |

## Phase 1: 上下文收集

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

## Phase 2: 结构扫描

判断项目层级并选择能力面适配器：

- `frontend`：ui_route、view_component、form_or_schema、state_flow、client_contract 等。
- `bff`：edge_api、schema_or_template、orchestration、transform_mapping、upstream/frontend_contract 等。
- `backend`：api_surface、application_service、domain_model、validation_policy、persistence_model、async_event 等。

扫描规则：

- 使用 `rg` / glob，范围限定在当前项目，不跨项目搜索。
- 排除 `node_modules`、`dist`、`build`、`coverage`、测试、mock、fixture、生成物。
- 读取文件前先确认路径存在。

输出 `_prd-tools/build/modules-index.yaml`，同时沉淀 `_prd-tools/reference/project-profile.yaml`：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
reference_scope:
  authority: "single_repo"
  repo_role: "frontend | bff | backend | multi-layer"
  team_reference_ready: false
related_repositories:
  - repo: ""
    role: "frontend | bff | backend | external"
    relationship: "upstream | downstream | consumer | producer | peer"
    verification: "confirmed | needs_confirmation | unknown"
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
```

## Phase 3: 深度分析

每个子步骤独立读取所需的参考文件：
- `steps/step-02-deep-analysis.md` 包含 5 个子阶段的完整生成指令、边界规则、去重检查和输出质量标准
- 共享规则：`references/reference-v4.md` 的文件边界规则、`references/layer-adapters.md` 的能力面适配器
- 读取 `references/output-contracts.md` 获取各文件的格式定义

生成 `_prd-tools/reference/` v4.0：

```text
project-profile.yaml        # 项目画像
01-codebase.yaml            # 静态清单
02-coding-rules.yaml        # 编码规则
03-contracts.yaml           # 契约
04-routing-playbooks.yaml   # 路由 + 打法
05-domain.yaml              # 业务领域
```

按以下顺序逐步执行子步骤（每步只读当前子步骤文件 + 上一步输出），后生成的文件必须检查先生成的文件，避免内容重叠：

1. 子阶段 1：`01-codebase.yaml`
2. 子阶段 2：`02-coding-rules.yaml`（检查 01 去重）
3. 子阶段 3：`03-contracts.yaml`（检查 01 去重，移入字段级信息）
4. 子阶段 4：`04-routing-playbooks.yaml`（含 capability_inventory，检查 02 去重）
5. 子阶段 5：`05-domain.yaml` + `00-portal.md`（检查术语与静态事实边界）

每个子步骤文件末尾有 Self-Check 清单，生成后必须逐项验证通过再进入下一步。

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

事实生成硬约束：

- 禁止使用 `120+`、`几十个`、`大量` 这类模糊统计；没有确定计数来源时写 `unknown`，并把补计数放入 `open_questions` 或 `next_actions`。
- 禁止臆造 owner、IM 群、频道、上下游系统职责、部署平台细节。当前仓无法证明的内容写成候选线索，并标记 `verification: needs_confirmation`。
- `confidence: high` 必须在同一条目或相邻上下文中出现 `evidence`、`verified_by`、`source` 或 `locator`。
- 对跨仓 API、前端消费方、后端 producer 的描述必须区分 `confirmed` / `inferred` / `needs_confirmation`。

跨文件引用规则（详见 `references/reference-v4.md`）：

- 字段 type/required 只在 `03-contracts`，其他文件用 `contract_ref` 引用。
- 编码规则只在 `02-coding-rules`，playbook 步骤用 `ref_rule` 引用。
- 开发步骤只在 `04-routing-playbooks` 的 playbook 中。
- 术语只在 `05-domain`。
- 外部系统 endpoint 详情只在 `03-contracts`，`01-codebase` 用 `contract_ref` 引用。

## Phase 4: 质量门控

必须检查：

- 文件完整性：`00-portal.md` 存在，`01~05` 中至少 3 个存在。
- 证据完整性：实体、路由、契约、playbook 关键项都有 evidence。
- 源码一致性：路径、枚举值、注册点、模板函数、契约字段仍存在。
- 契约闭环：跨层字段有 producer / consumer / checked_by / alignment_status。
- 能力面适配器门控：按 `references/layer-adapters.md` 检查当前层必需 surface。
- 边界门控：5 条跨文件边界规则（见 step-03-quality-gate.md）。
- 幻觉检查：文件、函数、变量、机制不能没有证据。
- 样例回归：至少用一个 golden sample 反推 PRD -> IR -> Layer Impact -> Contract Delta 是否走通。

输出 `_prd-tools/build/quality-report.yaml`：

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

## Phase 5: Evidence Index 构建

基于 Phase 3 生成的 reference 和项目源码，构建 Evidence Index（辅助层），为下游 `/prd-distill` 提供确定性代码锚点检索。

> **定位**：Evidence Index 是辅助层，不替代 reference 作为 SSOT。reference 的 6 个文件仍是主产物。

运行命令：

```bash
python3 .prd-tools/scripts/build-index.py --repo <项目路径> --out _prd-tools/reference/index
```

产出：

```text
_prd-tools/reference/index/
├── entities.json          # 代码实体（函数、类、枚举、接口等）
├── edges.json             # 实体关系（DEFINES、IMPORTS、RESOLVED_IMPORT、REFERENCES 等）
├── inverted-index.json    # term→entity 倒排索引
└── manifest.yaml          # 索引元数据（实体数、边数、term 数、构建时间）
```

索引能力：

- 实体类型：file、function、class、interface、enum、const、import、switch_case、template、registry
- 关系类型：DEFINES、IMPORTS、RESOLVED_IMPORT、REGISTERS、REFERENCES
- 构建模式：增量（默认，基于文件 hash 差异）或全量（`--full`）
- 查询模式：`--query <关键词> --index _prd-tools/reference/index` 确定性评分检索
- 支持语言：TypeScript/JavaScript、Go

触发时机：

- 全量构建（Mode A）后自动执行
- 增量更新（Mode B）后可选执行
- 健康检查（Mode B2）时检查索引与源码一致性

## Phase 6: 反馈回流

读取 `_prd-tools/distill/**/context/reference-update-suggestions.yaml` 和 `report.md`。兼容读取旧版 `spec/reference-update-suggestions.yaml` 等文件名。

回流仍以单仓为边界：只自动处理当前仓可验证事实。跨仓建议必须保留 `team_reference_candidate`、`team_scope` 和 `owner_to_confirm`，除非用户或 owner 明确确认，否则不要把其他仓事实写成本仓确定结论。

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
- 是否是未来团队知识库候选，以及需要哪个 owner 确认

用户确认后再修改 reference，并更新 `last_verified`。

## Mode → Phase 映射（B / B2 / C / E 可执行清单）

`F` 和 `A` 走完整 Phase 1-5。其他模式按下表只跑必要 Phase，避免重复全量构建：

| 模式 | 跑哪些 Phase | 跳过 | 关键产物 | 完成判定 |
|------|-----------|------|---------|---------|
| **F** 上下文收集 | Phase 1 | 2/3/4/5 | `build/context-enrichment.yaml` | 至少 1 个 sample 含 lessons[] |
| **A** 全量构建 | Phase 2 → 3 → 4 → 5 | — | `reference/01-05.yaml` + `project-profile.yaml` + `index/` | 所有 required 文件存在且非空 |
| **B** 增量更新 | Phase 2（增量扫 git diff 影响的模块）→ Phase 3 的相关子阶段（只重写涉及的 yaml）→ Phase 5（增量 build-index，默认无 `--full`） | Phase 1；Phase 3 中未受影响的子阶段 | 受影响的 yaml 文件 + 更新后的 `index/manifest.yaml` | 只动了"应该动"的文件 |
| **B2** 健康检查 | Phase 4 + last_verified 检查 + index 与源码一致性 | Phase 1/2/3/5（不重建） | `build/health-check.yaml`（含 stale_entries / missing_evidence / index_drift） | 报告 status: pass/warning/fail |
| **C** 质量门控 | Phase 4 only | Phase 1/2/3/5（信任已有产物） | `build/quality-report.yaml` | fatal_findings 为空 |
| **E** 反馈回流 | Phase 6 | 其他全部 | `build/feedback-report.yaml` + 受影响的 `reference/*.yaml`（仅有证据的建议被应用） | 所有 suggestion 已 dispositioned (apply / reject / defer) |

团队模式（Mode T 收集）详见 `/team-reference`。

**Mode B/B2/C/E 共同规则**：

- 执行前必须读 `_prd-tools/build/reference-workflow-state.yaml`，确认上次完成态。
- 不允许"顺手补全"非本模式应该动的文件（典型陷阱：Mode B2 只是检查健康，不能直接改 yaml；发现问题写到 health-check.yaml 让用户决定走 B 还是 A）。
- 结束时更新 `reference-workflow-state.yaml` 的 `mode` / `completed_at` / `last_verified`。

## 执行规则

1. 源码是最终权威；reference 是快速通道。
2. 不确定就写 low confidence，不要补脑。
3. 多层需求必须显式记录契约面。
4. 前端、BFF、后端保持同一 reference 结构，层差异用能力面适配器表达。
5. 跨仓事实默认是线索，不是结论；没有 owner 确认时写 `needs_confirmation`。
6. 每个 reference 文件尽量短；复杂样例放 `04-routing-playbooks.golden_samples`。
7. 完成后给用户一份摘要：新增/更新文件、质量门控结果、下一步建议。
