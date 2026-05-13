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

## 阶段

| 阶段 | 名称 | 输入 | 输出 |
|---|---|---|---|
| 0 | 上下文收集 | 历史 PRD、技术方案、分支 diff、发布/返工记录 | `_prd-tools/build/context-enrichment.yaml` |
| 1 | 结构扫描 | 项目目录、核心源码、git 历史 | `_prd-tools/build/modules-index.yaml` |
| 2 | 深度分析 | modules-index、源码、能力面适配器 | `_prd-tools/reference/` v4.0 |
| 3 | 质量门控 | reference、源码、样例需求 | `_prd-tools/build/quality-report.yaml` |
| 3.5 | Evidence Index | reference、项目源码 | `_prd-tools/reference/index/`（辅助层） |
| 4 | 反馈回流 | `/prd-distill` 输出、源码、reference | `_prd-tools/build/feedback-report.yaml` |

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

## 阶段 2：深度分析

每个子步骤独立读取所需的参考文件：
- `steps/step-02-deep-analysis.md` 包含 5 个阶段的完整生成指令、边界规则、去重检查和输出质量标准
- 共享规则：`references/reference-v4.md` 的文件边界规则、`references/layer-adapters.md` 的能力面适配器
- 读取 `references/output-contracts.md` 索引，按需加载 `schemas/` 下的具体 schema

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

1. 阶段 1：`01-codebase.yaml`
2. 阶段 2：`02-coding-rules.yaml`（检查 01 去重）
3. 阶段 3：`03-contracts.yaml`（检查 01 去重，移入字段级信息）
4. 阶段 4：`04-routing-playbooks.yaml`（含 capability_inventory，检查 02 去重）
5. 阶段 5：`05-domain.yaml` + `00-portal.md`（检查术语与静态事实边界）

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

## 阶段 3：质量门控

必须检查：

- 文件完整性：`01~05` 中至少 3 个存在。
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

## 阶段 3.5：Evidence Index 构建

基于阶段 2 生成的 reference 和项目源码，构建 Evidence Index（辅助层），为下游 `/prd-distill` 提供确定性代码锚点检索。

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

## 阶段 3.6：Reference Completion Gate（硬约束）

> **定位**：Completion Gate 是 /reference 的硬完成门禁。不通过不得宣称 /reference 完成。

运行命令：

```bash
python3 .prd-tools/scripts/quality-gate.py reference --root .
```

检查内容：

1. required reference files 是否存在且非空
2. index 四个文件是否存在且非空
3. YAML 文件是否基本可读
4. 关键 reference 文件是否包含 schema_version
5. 是否存在模糊统计、未证据化 owner/contact、无证据 high confidence（warning）

门禁规则：

- exit code 2（fail）：必须补缺失文件，不得宣称 /reference 完成。
- exit code 0（pass 或 warning）：可以完成，但 warning 必须在最终回复中说明。
- index 缺失时，不得宣称 /reference 完成。
- 最终回复必须列出 index manifest 摘要（实体数、边数、term 数）。

## 阶段 4：反馈回流

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

## 阶段 T-init：团队仓库初始化

> **定位**：在空团队仓库中引导初始化，创建配置和目录结构，运行首次聚合。
> **触发条件**：用户确认这是团队知识库仓库，且 `team/project-profile.yaml` 不存在。

### 步骤 1：收集成员仓库信息

向用户交互式收集：

- **业务域名**（e.g. "marketing"）— 用于 project-profile.yaml 的 `business` 字段
- **成员仓库列表**，逐条收集：
  - 仓库名（e.g. "frontend-main"）
  - 本地路径（e.g. "/Users/example/work/frontend-main"）
  - 所属层：`frontend` | `bff` | `backend`
  - 角色：`producer` | `consumer` | `middleware` | `peer`

每条确认后继续下一条，用户说"完成"后进入步骤 2。

### 步骤 2：验证成员仓库就绪

对每个成员仓库逐个检查：

1. `local_path` 目录是否存在
2. `_prd-tools/reference/project-profile.yaml` 是否存在
3. 5 个 YAML 文件（01-05）是否都存在

就绪状态汇总表展示给用户：

```text
| 仓库 | 路径存在 | reference 存在 | 5 文件齐全 | 状态 |
|------|---------|---------------|-----------|------|
| repo-a | ✓ | ✓ | ✓ | ✅ 就绪 |
| repo-b | ✓ | ✗ | — | ⚠️ 需先运行 /reference Mode A |
```

未就绪的仓库：
- 告知用户需先在对应仓库运行 `/reference` Mode A 生成完整 reference
- 用户可选择：跳过未就绪仓库继续、或中止等所有仓库就绪

至少 1 个仓库就绪才能继续。

### 步骤 3：创建团队仓库结构

生成以下文件：

**`team/project-profile.yaml`** — 基于成员仓库模板（`templates/project-profile.yaml`）改编：
- `layer: "team-common"`
- `business: "<用户填写的业务域名>"`
- `reference_scope.authority: "team_common"`
- 取消注释 `team_reference.member_repos[]` 和 `aggregation_policy`，填入收集的信息
- 使用默认聚合策略（`contracts: union_by_id`, `domain_terms: union_dedupe`, `coding_rules: fatal_only`, `playbooks: cross_layer_only`）
- 不需要 `tech_stack`、`entrypoints`、`capability_surfaces` 等成员仓库专属字段

**`.prd-tools-team-version`** — 写入当前 prd-tools 版本号（读 `VERSION` 文件）

**目录结构**（用 `.gitkeep` 占位空目录）：

```text
team/
build/
{各层}/snapshots/{各仓}/.gitkeep
```

### 步骤 4：运行首次聚合

```bash
python3 <prd-tools-path>/scripts/team-reference-aggregate.py --team-root .
```

`<prd-tools-path>` 解析方式：查找 `~/.claude/plugins/` 下已安装的 prd-tools 路径，或让用户指定。

聚合完成后展示：
- `build/aggregation-report.yaml` 摘要（成员仓数量、各产物条目数）
- 如有 `build/conflicts.yaml`，列出冲突项和处理建议

### 步骤 5：生成 README.md

在仓库根目录生成 `README.md`，包含：

```markdown
# {业务域名} 团队知识库

prd-tools 自动维护的团队级公共知识库。

## 目录结构

- `team/` — 团队级聚合数据（SSOT）
- `{各层}/snapshots/` — 成员仓库快照
- `build/` — 聚合报告和冲突记录

## 成员仓库

| 仓库 | 层 | 角色 |
|------|---|------|
| repo-a | frontend | producer |
| ... | ... | ... |

## 更新聚合

当成员仓库的 reference 更新后，在本仓库重新运行：

```bash
python3 ~/work/prd-tools/scripts/team-reference-aggregate.py --team-root .
```
```

## 阶段 5：团队聚合（Mode T）

> **定位**：在团队仓执行，从各成员仓的 `_prd-tools/reference/` 聚合事实到团队仓 `team/`。

**前置条件**：
- 当前工作目录是团队仓（含 `team/project-profile.yaml`，`layer: team-common`）
- `team_reference.member_repos[]` 已配置各成员仓路径
- 各成员仓已运行过 `/reference` Mode A/B，有完整的 01-05 YAML
- **各成员仓已将 `_prd-tools/reference/*.yaml` 提交到 git**（聚合脚本需从 git 读取）

**数据源解析优先级**：
1. `local_path` 存在且有 `_prd-tools/reference/` → 直接读本地（最快）
2. `remote_url` 提供且 local_path 不可用 → `git clone --depth 1` 到临时目录后读取

运行命令：

```bash
python3 scripts/team-reference-aggregate.py --team-root .
```

**成员仓前提**：各仓需将 `_prd-tools/reference/` 提交到 git（确保 `.gitignore` 没有忽略该目录）。YAML 文件是文本，体积小，适合版本控制。

聚合策略（由 `team_reference.aggregation_policy` 配置）：

| 产物 | 默认策略 | 说明 |
|------|---------|------|
| 03-contracts | union_by_id | 同 ID 合并 producer/consumers/checked_by，producer 不一致标 conflict |
| 05-domain | union_dedupe | 按 term 名去重，定义不同标 divergence |
| 02-coding-rules | fatal_only | 只聚合 severity=fatal 规则 |
| 04-routing-playbooks | cross_layer_only | 只聚合 target_surfaces 涉及 2+ 层的 playbook |
| 01-codebase | index_only | 不聚合代码地图，只从 contracts 提取 cross_repo_entities 索引 |

产出：

- `team/01-codebase.yaml` ~ `team/05-domain.yaml`：5 个聚合产物
- `{frontend,bff,backend}/snapshots/{repo}/`：成员仓全量镜像 + `_snapshot-meta.yaml`
- `build/aggregation-report.yaml`：聚合状态报告
- `build/conflicts.yaml`：跨仓冲突清单（待人工仲裁）

冲突处理：团队仓的 `conflicts.yaml` 不手工编辑。仲裁方式是回到对应成员仓修正字段，重新跑 `/reference`，再回到团队仓重新聚合。

`build/conflicts.yaml` 格式：

```yaml
generated_at: "<ISO-8601>"
total_conflicts: 0
conflicts:
  - type: "contract_producer_mismatch"     # 或 coding_rule_conflict / playbook_layer_steps_conflict
    contract_id: "CONTRACT-XXX"            # 或 rule_id / playbook_id
    divergent_claims:
      - repo: "repo-a"
        claim: "..."
      - repo: "repo-b"
        claim: "..."
    suggested_resolution: "ask owner"
```

冲突类型及处理方式：

| 冲突类型 | 原因 | 处理 |
|---------|------|------|
| `contract_producer_mismatch` | 多仓声称自己是同一契约的 producer | 回到冲突仓确认实际 owner，修正 `producer` 字段 |
| `coding_rule_conflict` | 同一 rule_id 在不同仓有不同描述 | 对齐规则描述后重新聚合 |
| `playbook_layer_steps_conflict` | 多仓为同一 playbook 的同一层写了 steps | 确定一个 `playbook_owner`，其他仓删除该层 steps |

## 阶段 6：团队继承（Mode T2）

> **定位**：在成员仓执行，从团队仓 `team/` 继承公共事实到本仓 `_prd-tools/reference/`。

**前置条件**：
- 当前工作目录是成员仓（含 `_prd-tools/reference/`）
- `project-profile.yaml` 的 `team_reference.upstream_local_path` 指向团队仓本地路径
- `team_reference.inherit_scopes` 已配置继承范围
- 团队仓已运行过 Mode T 聚合

运行命令：

```bash
python3 scripts/team-reference-inherit.py --repo-root .
```

继承规则：

| 场景 | 行为 |
|------|------|
| 本仓没有同 ID 条目 | 新增，标 `source: "team-common"`, `read_only: true` |
| 本仓已有同 ID（非 team-common） | 保留本仓版本，记 conflict |
| 本仓已有同 ID（team-common） | 更新为团队仓最新版 |
| coding_rules_fatal | **强制覆盖**（团队级 fatal 规则权威） |

`inherit_scopes` 可选值：`domain_terms`、`contracts_cross_repo`、`coding_rules_fatal`。

## 执行规则

1. 源码是最终权威；reference 是快速通道。
2. 不确定就写 low confidence，不要补脑。
3. 多层需求必须显式记录契约面。
4. 前端、BFF、后端保持同一 reference 结构，层差异用能力面适配器表达。
5. 跨仓事实默认是线索，不是结论；没有 owner 确认时写 `needs_confirmation`。
6. 每个 reference 文件尽量短；复杂样例放 `04-routing-playbooks.golden_samples`。
7. 完成后给用户一份摘要：新增/更新文件、质量门控结果、下一步建议。
