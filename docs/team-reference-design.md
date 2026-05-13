# Team Common Reference 设计文档

> **状态**：v2.18.1 脚手架已落地（schema 字段 + 消费指令 + 本文档）；v2.19 实现聚合；v2.20 实现团队级 distill。
> **作用域**：PRD Tools 从单仓自治 → 全团队共享知识库的演进路线。

---

## 1. 目标与非目标

### 目标

- 各业务方（前端 genos、BFF dive-bff/dive-template-bff、后端 magellan）各自跑 `/reference` 产出本仓知识库 → 自动聚合到**团队公共知识库**
- 在团队仓直接跑 `/prd-distill`，产出**涉及前端+BFF+后端的跨仓技术方案**（含每个仓的 sub-plan）
- 保留单仓自治：团队仓只沉淀"多仓已 checked_by 的事实"，不覆盖本仓内部细节

### 非目标（本设计不解）

- 不做实时同步（pull-based，按需聚合）
- 不做代码级跨仓搜索（团队仓没有源码副本，只有 reference 知识）
- 不做自动冲突合并（冲突项留候选 + 人工仲裁）
- 不替代各仓的 `/prd-distill`（团队 distill 是**补充**，产出跨仓技术方案，单仓细节仍在各仓做）

---

## 2. 核心决策

### 决策 1：Pull-based 聚合，不是 Push-based

**选择**：团队仓有聚合脚本，按需 pull 各成员仓的 reference 来聚合。

**不选 push-based**（各仓跑完 reference 后 git hook 自动 push 到团队仓）的原因：

| 维度 | push-based | pull-based（选） |
|---|---|---|
| 实时性 | 高 | 低（按需） |
| 冲突处理 | 每次 push 都要处理 | 聚合时集中处理 |
| 认证复杂度 | 每个成员仓都要配 SSH key / token | 团队仓一处配 |
| 误操作风险 | 高（垃圾 reference 立即污染团队仓） | 低（聚合前可审） |
| CI 依赖 | 强 | 无 |

**权衡结论**：团队 reference 的更新需要审核（contract 冲突、术语歧义、playbook 覆盖），全自动 push 容易把未验证的内容推上去。pull-based 把聚合动作集中到团队仓，更可控。

### 决策 2：单业务一仓，按层组织

**选择**：每个业务域**一个独立的团队仓**（如 `dive-team-reference`），仓内按层组织（frontend/bff/backend/team），不再嵌套业务子目录。

```text
dive-team-reference/                   # 团队仓根（专属 dive 业务）
├── .prd-tools-team-version            # 团队仓版本（跟 prd-tools 插件版本一致）
├── README.md                          # 使用说明
├── team/                              # 跨层聚合产物（SSOT，跨仓 distill 读这里)
│   ├── 00-portal.md                   # 团队级导航
│   ├── project-profile.yaml           # layer: "team-common", business: "dive"
│   ├── 01-codebase.yaml               # 跨仓代码地图（cross_repo_entities 索引）
│   ├── 02-coding-rules.yaml           # 全团队共享的 fatal 规则（取并集）
│   ├── 03-contracts.yaml              # 跨仓契约 SSOT（含 checked_by 多仓）
│   ├── 04-routing-playbooks.yaml      # 跨仓 playbook（layer_steps 三层都填）
│   ├── 05-domain.yaml                 # 全团队术语、业务决策
│   └── portal.html
├── frontend/                          # 前端层
│   └── snapshots/
│       ├── genos/                     # 成员仓 reference 快照（只读镜像）
│       │   ├── _snapshot-meta.yaml    # {commit_sha, synced_at, source_repo}
│       │   └── *.yaml                 # 该仓的 5 文件全量镜像
│       └── dive-editor/
├── bff/
│   └── snapshots/
│       ├── dive-bff/
│       └── dive-template-bff/
├── backend/
│   └── snapshots/
│       └── magellan/
└── build/
    ├── aggregation-report.yaml        # 上次聚合的状态：各仓贡献了什么
    └── conflicts.yaml                 # 跨仓冲突清单（待人工仲裁）
```

**为什么不嵌业务域子目录（`dive/team/`、`dive/frontend/`）**：

- 仓名 `dive-team-reference` 已表达业务归属，再嵌 `dive/` 是冗余
- YAGNI：当前只有 dive 一个业务，不为"未来可能有多业务"预留路径
- 业务边界天然就是治理边界：dive 的 owner 不会管其他业务的知识库
- 如果未来真有多业务（比如出现 `xxx` 业务），就**新建独立的 `xxx-team-reference` 仓**，保持每仓单业务的简洁性。多仓如何在更高层组织（git submodule / monorepo / 部门级 manifest）属于未来问题，本设计不涉及

**要点**：
- `team/` 是**聚合产物**（SSOT 层），所有跨仓 PRD 分析都读这里
- `snapshots/` 是**成员仓镜像**（备份层），用于追溯"team 里的 CONTRACT-001 来自哪个仓的哪个 commit"
- `team/project-profile.yaml` 仍保留 `business: "dive"` 字段，便于团队 distill 产物里标注业务上下文（不影响目录结构）

### 决策 3：不新建 skill，复用 `/reference` 的模式扩展

**选择**：在现有 `/reference` skill 增加 2 个新模式：

| 新模式 | 何时 | 输出 |
|---|---|---|
| `T 团队聚合` | 在团队仓执行 | 从 `team_reference:.member_repos[]` 配置的成员仓聚合事实 |
| `T2 团队继承` | 在成员仓执行 | 从团队仓继承公共事实到本仓 `_prd-tools/reference/` |

**不选**创建 `/team-reference` 新 skill 的原因：模式本质是 `/reference` 的扩展（同样的输入文件、同样的输出结构），单独 skill 是冗余抽象。

### 决策 4：团队 distill 复用 `/prd-distill`，加 `--mode team`

**选择**：`/prd-distill` 通过 `_prd-tools/reference/project-profile.yaml` 的 `layer: "team-common"` **自动识别**团队模式，或显式 `--mode team`。

**自动识别逻辑**：
- 在团队仓执行 `/prd-distill <prd.docx>` → 读 project-profile.yaml 发现 `layer: team-common` → 切换到 team 模式
- team 模式下跳过 `rg`/`glob` 源码扫描（团队仓没有源码），改为从 `team/01-codebase.yaml` 的跨仓代码地图查 code_anchors
- `layer-impact.yaml` 的 frontend/bff/backend 三层从对应 `snapshots/` 读信息填充

---

## 3. 聚合算法（v2.19 核心）

### 团队仓初始化（首次使用）

聚合前团队仓必须先初始化一次。约定 bootstrap 步骤，**无需新脚本**：

```bash
# 1. 创建空仓并初始化目录
mkdir -p dive-team-reference/{team,frontend/snapshots,bff/snapshots,backend/snapshots,build}
cd dive-team-reference/
echo "2.19.0" > .prd-tools-team-version

# 2. 手工创建 team/project-profile.yaml（模板见下文「配置文件」段）
#    必填：layer: team-common, business: dive, team_reference.member_repos[]

# 3. 首次运行聚合（会生成 team/*.yaml 的初版）
/reference
# 选择模式：T 团队聚合
```

`team/project-profile.yaml` 的模板通过扩展现有 `plugins/reference/skills/reference/templates/project-profile.yaml` 得到——在该模板加 `layer: team-common` 分支说明，无新文件。

### 入口

```bash
# 在团队仓执行
cd dive-team-reference/
/reference
# 选择模式：T 团队聚合
# 成员仓路径：从 team/project-profile.yaml 的 team_reference.member_repos 读取
```

底层调用 `scripts/team-reference-aggregate.py`（单脚本，v2.19 唯一新增）。

**聚合输出位置**：所有合并产物写入团队仓 `team/` 目录的对应 5 文件，覆盖上次聚合结果（增量 diff 留 git 看）。`snapshots/{layer}/{repo}/` 下写入成员仓 reference 的全量镜像 + `_snapshot-meta.yaml`。

### 配置文件

团队仓 `team/project-profile.yaml`：

```yaml
layer: "team-common"
business: "dive"
team_reference:
  version: "2.19.0"
  member_repos:
    - repo: "genos"
      local_path: "/path/to/genos"
      layer: "frontend"
      role: "producer"                 # producer | consumer | peer
    - repo: "dive-bff"
      local_path: "/path/to/dive-bff"
      layer: "bff"
      role: "middleware"
    - repo: "magellan"
      local_path: "/path/to/magellan"
      layer: "backend"
      role: "producer"
  aggregation_policy:
    contracts: "union_by_id"           # 同 ID 合并 producer/consumers/checked_by
    domain_terms: "union_dedupe"       # 去重合并
    coding_rules: "fatal_only"         # 只聚合 severity=fatal 规则
    playbooks: "cross_layer_only"      # 只聚合 target_surfaces 含 2+ 层的 playbook
```

### 5 类产物的聚合策略

#### 3.1 `03-contracts.yaml` — 跨仓契约合并

**输入**：每个成员仓的 `03-contracts.yaml` 中 `team_reference_candidate: true` 的条目。

**合并规则**：

```
对同一 contract_id 在多仓出现：
  merged.producer = 所有仓声称 producer 的取值（应一致，冲突则标 conflict）
  merged.consumers = ∪ 各仓的 consumers  
  merged.checked_by = ∪ 各仓的 checked_by  
  merged.consumer_repos = ∪ 各仓的 consumer_repos（去重 by repo）
  merged.request_fields / response_fields = 以 producer 仓的定义为准，其他仓标 "echo"
  merged.aggregation_status = "confirmed" if consumers ⊆ checked_by else "candidate"
```

**冲突**：

- Producer 不一致 → `conflicts.yaml` 记录，聚合产物标 `aggregation_status: conflict`
- 字段定义不一致 → 以 producer 仓为准，其他仓的差异写入 `divergence_notes`

#### 3.2 `05-domain.yaml` — 术语合并

**合并规则**：

```
terms 按 term 名合并：
  definitions 相同 → 合并 synonyms 和 evidence
  definitions 不同 → 两个定义都保留，标 divergence
see_enum 指向本仓 01-codebase 的，聚合时重写为 "<repo>:01-codebase.<EnumName>"
implicit_rules 按 id 合并
decision_log 按 id 合并
```

#### 3.3 `02-coding-rules.yaml` — 只聚合 fatal

**合并规则**：

```
只取 severity=fatal 的规则，其他层级不进团队仓
按 rule_id 去重
冲突处理：rule_id 相同但描述不同 → conflict
danger_zones 按 file_path 聚合（跨仓同路径提示合并）
```

#### 3.4 `04-routing-playbooks.yaml` — 跨层 playbook

**合并规则**：

```
只聚合 target_surfaces 涉及 2+ 层的 playbook（单层 playbook 留本仓）
prd_routing 合并 handoff_surfaces（各仓对同一 ROUTE 的 handoff 建议取并集）

playbooks 合并 layer_steps：
  对同一 PLAYBOOK-id：
    team playbook.layer_steps.frontend = 选择 frontend 层成员仓里 playbook_owner=true 的 layer_steps（**不取并集**）
    若多仓都标 playbook_owner=true → 标 conflict
    若没仓标 owner → 取**有内容的那个**，多个则按 producer_repo 优先
  目的：避免简单 ∪ 产生混乱的 step 列表
cross_repo_handoffs 合并去重（按 repo+layer 二元组）
golden_samples 中 team_reference_candidate: true 的升级到团队仓
```

> **`playbook_owner` 字段**：复用现有 `04-routing-playbooks.yaml` 模板的 `owner: ""` 字段，约定值为 `repo:<repo-name>` 表示该 playbook 由哪个仓主导。无新字段。

#### 3.5 `01-codebase.yaml` — 不聚合，只建索引

**原因**：`01-codebase.yaml` 含本仓代码地图，聚合后会非常庞大且无价值（团队仓不需要读具体文件）。

**替代做法**：在团队仓 `01-codebase.yaml` 只存**跨仓代码坐标索引**：

```yaml
cross_repo_entities:
  - term: "CampaignType"
    defined_in:
      repo: "dive-bff"
      file: "src/config/constant/campaignType.ts"
      enum_ref: "see_enum: CampaignType"   # 指向成员仓详细定义
    consumed_by:
      - repo: "genos"
        file: "src/views/CampaignForm.tsx"
      - repo: "magellan"
        file: "internal/campaign/type.go"
```

详细枚举值和 label 留在成员仓的 `01-codebase.yaml` 里，通过 snapshots/ 可查。

### 冲突处理

`build/conflicts.yaml`：

```yaml
conflicts:
  - type: "contract_producer_mismatch"
    contract_id: "CONTRACT-CAMPAIGN-001"
    divergent_claims:
      - repo: "dive-bff"
        claim: "producer=bff"
      - repo: "magellan"
        claim: "producer=backend"
    suggested_resolution: "ask owner"
    owner_candidates: ["@backend-lead", "@bff-lead"]
```

人工仲裁后，修复方提交 PR 到**对应成员仓**修正字段。下次成员仓跑 `/reference` 重新生成 reference 后，再次在团队仓跑聚合（手动触发），冲突自动消失。**团队仓的 conflicts.yaml 不手工编辑**——它是聚合产物，由源头修复决定。

---

## 4. 继承接口（成员仓视角）

### 入口

```bash
# 在成员仓执行
cd dive-bff/
/reference
# 选择模式：T2 团队继承
```

底层调用 `scripts/team-reference-inherit.py`（v2.19 第二个新增脚本，也是唯一另一个）。

### 继承规则

```
从 <team-repo>/team/ 读取 5 文件 → 镜像到本仓 _prd-tools/reference/
每条继承条目加 metadata：
  source: "team-common"
  read_only: true
  last_inherited: <ISO-8601>
```

**冲突策略**：

- 本仓已有同 ID 条目 → 保留本仓版本（不覆盖），在 conflict log 提示
- 本仓没有 → 新增条目，标 `source: team-common`
- `02-coding-rules.yaml` fatal 规则：**强制覆盖**（团队级 fatal 规则权威）

**inherit_scopes 过滤**（在 project-profile.yaml 配置）：

```yaml
team_reference:
  inherit_scopes:
    - domain_terms              # 继承 05-domain
    - contracts_cross_repo      # 继承 03-contracts
    - coding_rules_fatal        # 继承 02-coding-rules fatal 规则
    # - routing_playbooks       # 可选：默认不继承，playbook 通常本仓化
```

---

## 5. 团队级 distill（v2.20）

### 触发

```bash
# 在团队仓执行
cd dive-team-reference/team/
/prd-distill /path/to/cross-team-prd.docx
```

`/prd-distill` 读 `project-profile.yaml` 发现 `layer: team-common`，自动进入 team 模式。

### 与单仓 distill 的差异

| 步骤 | 单仓 distill | 团队 distill |
|---|---|---|
| Step 0 PRD Ingestion | 同 | 同 |
| Step 1 Evidence | 同 | 同 |
| Step 2 Requirement IR | 同 | 同 |
| Step 3.1 Graph Context | `rg`/`glob` 源码 + reference | **仅**从团队仓 `team/01-codebase.yaml` 的 cross_repo_entities 查；需要源码细节时下钻到对应 `snapshots/<repo>/` 读 |
| Step 3.2 Layer Impact | 按本仓层生成 IMP | **同时**生成 4 层 IMP（frontend / bff / backend / external），每层的 code_anchors 从对应 snapshots 查，找不到的写 `needs_confirmation` |
| Step 4 Contract Delta | 按本仓视角 | 全栈视角：每条 delta 含完整 producer/consumers[]/checked_by[] |
| Step 5 Plan | 1 份 plan.md | 1 份 team-plan.md（总览）+ N 份 sub-plan-{repo}.md（每个受影响仓一份） |
| Step 8 Report | 本仓 report.md | 团队 report.md：§10 分前端/BFF/后端/外部 4 小段 |

### 新增产物

团队 distill 产物目录：

```
dive-team-reference/_prd-tools/distill/<slug>/
├── report.md                    # 团队级报告（§4 影响范围分 4 层）
├── team-plan.md                 # 团队级开发计划（总览 + 跨仓时序）
├── plans/
│   ├── plan-genos.md            # 前端仓的 sub-plan（提供给前端 owner）
│   ├── plan-dive-bff.md         # BFF 的 sub-plan
│   └── plan-magellan.md         # 后端的 sub-plan
├── context/
│   ├── layer-impact.yaml        # 4 层完整填充
│   ├── contract-delta.yaml      # 全栈 consumers[]
│   └── ...                      # 其余 context 文件同单仓 distill
└── portal.html                  # 可视化入口
```

### 产物消费路径

```
PM/TL 看 report.md + team-plan.md → 跨仓协调
前端 owner 看 plans/plan-genos.md → 前端执行
BFF owner 看 plans/plan-dive-bff.md → BFF 执行
后端 owner 看 plans/plan-magellan.md → 后端执行
```

---

## 6. 数据流全景

```
成员仓（dive-bff）                     团队仓（dive-team-reference）
────────────────                       ─────────────────────────────
/reference A 全量构建
  ↓
_prd-tools/reference/*.yaml
  标记 team_reference_candidate: true
  ↓
                                       /reference T 团队聚合
                                         ↓ 读成员仓
                                       聚合 → team/*.yaml
                                              {frontend,bff,backend}/snapshots/
                                              build/aggregation-report.yaml
                                              build/conflicts.yaml
                                       ↑
/reference T2 团队继承
  ↑ 读团队仓
_prd-tools/reference/ 新增 source=team-common 条目

                                       /prd-distill <cross-team-prd>
                                         ↓ 自动识别 layer=team-common
                                       team 模式执行
                                         ↓
                                       report.md + team-plan.md + plans/{repo}.md
                                         ↓
                                       各 owner 拉 sub-plan 回本仓
                                       各仓开发完后 → /reference B 增量更新 →
                                       下一次聚合获得最新状态
```

---

## 7. 版本演进

| 版本 | 交付 | 风险/已知限制 |
|---|---|---|
| v2.18.1 | Schema 字段 + 消费指令 + 本设计文档（脚手架） | 无聚合能力，仅为下轮铺路 |
| **v2.19** | `team-reference-aggregate.py` + `team-reference-inherit.py`；`/reference` T / T2 模式 | 团队 distill 尚未支持，只能聚合和消费公共术语 |
| **v2.20** | `/prd-distill` team 模式 + team-plan.md + sub-plans | 依赖 v2.19 团队仓有足够数据；首轮跑会暴露"reference 不够厚"的问题 |
| v2.21 | CI 自动聚合（定期触发）、portal 跨仓可视化 | 需要业务方认同并配合 |

### v2.19 交付边界

- ✅ 2 个新脚本：`team-reference-aggregate.py`、`team-reference-inherit.py`
- ✅ `/reference` workflow.md 新增 T / T2 模式描述
- ✅ 冲突文件格式
- ❌ **不做** `/team-reference` 新 skill（反膨胀原则）
- ❌ **不做** CI 自动化
- ❌ **不做** 跨业务域支持（只 dive 一个业务域）

### v2.20 交付边界

- ✅ `/prd-distill` 识别 `layer: team-common` 切换 team 模式
- ✅ `plugins/prd-distill/skills/prd-distill/steps/step-02-classify.md` 加 team 模式分支
- ✅ `render-distill-portal.py` 支持 sub-plan 渲染
- ❌ **不做** 新 skill
- ❌ **不做** 新 contract 文件（复用现有 contract schema）

---

## 8. 反膨胀自检（本设计已通过）

对照 CLAUDE.md 的反膨胀规则自查：

| 检查 | 结果 |
|---|---|
| 新增 skill 数量 | **0**（复用 `/reference` 模式 + `/prd-distill --mode team`） |
| 新增 slash command | **0** |
| v2.19 新增 scripts | **2**（aggregate + inherit，都有明确 caller） |
| v2.20 新增 scripts | **0**（改 step 文件 + 复用 render-distill-portal.py） |
| 新增 contract 文件 | **0**（复用 existing contracts） |
| 新增 schema 字段 | 最少化：`business`, `member_repos[]`, `aggregation_policy`, `role`（都在现有 project-profile.yaml 内扩展，无新文件） |
| 新增 YAML 顶层键 | `cross_repo_entities`（在 01-codebase.yaml 内），`conflicts`（单独文件，聚合副产物） |

### 已复用的现有基建

- `team_reference_candidate: true` 字段（v2.18.1 已定义）
- `consumer_repos`, `producer_repo`, `team_scope.related_repos` 字段（v2.18.1 已定义）
- `checked_by[]` 数组（v2.18.1 已定义）
- `handoff_surfaces`, `cross_repo_handoffs` 字段（v2.18.1 已定义）
- `/reference` 工作模式选择框架（现有 A/B/B2/C/E/F）
- `/prd-distill` 的 step gate 系统（现有）
- `render-distill-portal.py`（现有，需扩展支持 sub-plan）

---

## 9. 开放问题（等 v2.19 实施时确认）

1. **团队仓的 git 权限**：聚合脚本需要读成员仓 `_prd-tools/reference/`，是否要求成员仓 clone 到团队仓配置的 `local_path`？还是允许远程 fetch？
2. **snapshots 的刷新频率**：每次聚合都全量刷？还是基于 commit_sha diff 增量刷？
3. **多业务扩容时机**：当出现第二个业务（如 `xxx`）时，新建独立的 `xxx-team-reference` 仓即可——不在本设计内解决"如何在更高层组织多个业务团队仓"（git submodule / monorepo / 部门级 manifest）。等真有第二个业务时再讨论。
4. **v2.20 team distill 的 image/video 证据**：跨仓 PRD 的原型图/流程图放哪？（建议：就在团队仓 distill 目录下，不下沉到成员仓）

这些问题不阻塞 v2.19 实施，但 v2.19 工程开工前应在团队内对齐。

---

## 10. 给 v2.19 实施者的交付清单

### 必做（最小可运行聚合）

- [x] `scripts/team-reference-aggregate.py`（~500 行估算）
- [x] `scripts/team-reference-inherit.py`（~300 行估算）
- [x] `plugins/reference/skills/reference/workflow.md` 新增 T/T2 模式描述（~30 行）
- [x] `plugins/reference/skills/reference/SKILL.md` 模式选择表加 T/T2 两行
- [x] `plugins/reference/skills/reference/templates/project-profile.yaml` 扩展 `team_reference:` 块（member_repos + aggregation_policy 字段）
- [ ] 在 `dive-team-reference` 仓初始化一个 fixture（可用 dive-bff + mock genos + mock magellan 跑通聚合）
- [x] 写 `build/conflicts.yaml` 样板 + 冲突处理说明（写入 workflow.md Phase 5）

### 不做（留给 v2.20+）

- ❌ 任何 team distill 逻辑
- ❌ CI 自动化
- ❌ 跨业务域
- ❌ 新 skill
- ❌ 新 contract 文件

---

## 附录 A：与业界前沿的对比与借鉴

2025 年跨仓 AI 知识库是热点方向。本设计在确认方向时参考了以下方案：

### 高度相关方案

| 方案 | 核心思路 | 与本设计关系 |
|---|---|---|
| **[Modulus](https://news.ycombinator.com/item?id=47327351)** (2025 Show HN) | 跨仓知识编排给 AI agent，明确解决"agents don't understand dependencies between repos" | 最相似。`team_reference_candidate` + `consumer_repos` 是同构思路 |
| **[Backstage](https://roadie.io/backstage-spotify/)** / **[Cortex](https://www.cortex.io/)** | Internal Developer Portal — entity catalog + ownership + AI 推断 | 我们 contracts 的 `producer/consumers/checked_by` 三元组与 Backstage entity-relation model 同构 |
| **[Sourcegraph SCIP](https://sourcegraph.com/resources/context-compare)** | 跨仓代码符号索引（SCIP/LSIF 标准） | 我们 `_prd-tools/reference/index/entities.json` 是简化版同思路；长期可输出 SCIP 兼容格式 |
| **[CodeIndex MCP](https://www.cidx.dev/)** | manifest folder scope agents to relevant repos + 协调层 | `member_repos[]` 配置就是 manifest 模式 |
| **[Multi-Repo Workspace for Claude Code](https://www.iamraghuveer.com/posts/multi-repo-workspace-claude-code/)** | 跨仓任务在 Claude Code 中的工程实践 | 实操级别的对照案例 |
| **[Augment MCP Integration](https://www.augmentcode.com/guides/mcp-integration-streamlining-multi-repo-development)** | "60% of engineering time lost to context-switching" → MCP 解 | 印证我们解决问题的方向 |

### 已对齐的设计模式

1. **Manifest-based scoping**（CodeIndex / Augment / 本设计）：用配置文件枚举参与仓，agent 按需加载。本设计的 `team_reference.member_repos[]` 是这个模式。
2. **Entity-relation 三元组**（Backstage / 本设计）：`Producer → Contract → Consumers` + ownership 关系。本设计的契约 schema 与 Backstage `Component → API → Resource + ownedBy/dependsOn` 同构。
3. **Aggregator + snapshot 分层**（Sourcegraph 索引模型 / 本设计）：聚合产物（SSOT）与原始快照（追溯）分开。本设计的 `team/` vs `snapshots/` 是同思路。
4. **Manager-Worker plan 拆分**（[Codex subagents](https://www.digitalapplied.com/blog/codex-subagents-ga-multi-agent-autonomous-coding-guide) / 本设计）：总 plan 拆 sub-plan 给各仓 owner。本设计的 `team-plan.md` + `plans/plan-{repo}.md` 对应这个模式。

### 未来可吸收点（不在 v2.19/v2.20 scope）

1. **MCP Server 化**（v2.21+ 候选方向）：把团队仓 reference 暴露为 [MCP](https://modelcontextprotocol.io) Server，让 Claude Code、Cursor、其他 agent 通过标准协议查询，不限于 `/prd-distill` 自家消费。这是 2025 业界共识方向。
2. **SCIP 兼容索引**（v2.22+ 候选）：让 `build-index.py` 输出 [SCIP](https://about.sourcegraph.com/blog/announcing-scip) 格式，可直接被 Sourcegraph、Cody 等工具消费。
3. **Owner 自动推断**（参考 Cortex AI Ownership）：聚合冲突时给出 owner 候选建议，目前我们已有 `owner_candidates`，可在 v2.21+ 用 git blame / commit history 自动填充。

### 不吸收的部分（明确边界）

- ❌ **不做完整 IDP**（Backstage/Cortex 那套）：目标是 PRD-to-Code 流程，不是组织级运维门户。Backstage 解 "谁拥有这个 service"，我们解 "这个 PRD 怎么落到 3 个 repo"。混进去会失焦。
- ❌ **不做实时多 agent 编排**（Repowire/Moddy mesh）：需要分布式 agent 基础设施，pull-based 静态聚合够用。
- ❌ **不做 GraphQL 查询层**（Backstage 有）：YAML 文件 + 文件读取已够，加 GraphQL 是膨胀。

### 差异化定位

与上述方案相比，本设计的独特之处：

1. **PRD-flow native**：不是通用代码搜索 / 服务目录，而是为 "PRD → 跨仓技术方案" 单一流程优化。
2. **零基础设施依赖**：不需要部署服务、不需要 SaaS、不需要 GraphQL endpoint。一个 git 仓 + 几个 Python 脚本搞定。
3. **生成产物即文档**：team-plan.md / sub-plan-{repo}.md 是直接可读、可 review、可 commit 的 markdown，不是查询接口背后的数据。

---

## 附录 B：与 v2.18.1 FIXES.md 的关系

- 本设计**依赖** v2.18.1 FIXES.md 的 P0-6（contracts producer/consumers[]）、P0-7（layer-impact 四层）、P0-8（03-contracts team 字段）、P0-10（routing-playbooks cross_repo_handoffs）、P0-12（reference-update-suggestions team_reference_candidate）、P1-4（团队 reference 脚手架）
- 这些 P0/P1 修完后，各仓产出的 reference 才有足够字段支持 v2.19 聚合
- **本设计不引入新的 P0/P1 修复项**
