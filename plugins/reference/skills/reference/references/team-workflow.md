# 团队知识库工作流（Mode T / T2 / T-init）

> **定位**：跨仓库 PRD 蒸馏的支撑基础设施。当需求涉及前端、BFF、后端多个仓库时，单仓 reference 无法看到全貌，团队模式把各成员仓的知识库聚合到团队仓。

## Mode → 阶段映射

| 模式 | 跑哪些阶段 | 关键产物 |
|------|-----------|---------|
| **T** 团队聚合 | 阶段 5（见下文） | `team/*.yaml` + `snapshots/` + `build/conflicts.yaml` |
| **T2** 团队继承 | 阶段 6（见下文） | 更新后的本仓 `reference/*.yaml` |
| **T-init** 团队初始化 | 阶段 T-init（见下文） | `team/project-profile.yaml` + 首次聚合产物 |

单仓模式（F/A/B/B2/C/E）的阶段定义在主 `workflow.md` 中，不在本文件。

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

就绪状态汇总表展示给用户。至少 1 个仓库就绪才能继续。未就绪的仓库告知用户需先在对应仓库运行 `/reference` Mode A。

### 步骤 3：创建团队仓库结构

生成以下文件：

**`team/project-profile.yaml`** — 基于成员仓库模板改编：
- `layer: "team-common"`
- `reference_scope.authority: "team_common"`
- 取消注释 `team_reference.member_repos[]` 和 `aggregation_policy`，填入收集的信息
- 使用默认聚合策略（`contracts: union_by_id`, `domain_terms: union_dedupe`, `coding_rules: fatal_cross_layer`, `playbooks: cross_layer_only`）

**`.prd-tools-team-version`** — 写入当前 prd-tools 版本号（读 `VERSION` 文件）

目录结构（用 `.gitkeep` 占位空目录）：

```text
team/
build/
{各层}/snapshots/{各仓}/.gitkeep
```

### 步骤 4：运行首次聚合

按阶段 5（Mode T）的聚合策略执行合并，写入 `team/01-codebase.yaml` ~ `team/05-domain.yaml` 和 `{各层}/snapshots/{仓}/` 全量镜像。

聚合完成后展示聚合摘要，如有冲突列出冲突项。

### 步骤 5：生成 README.md

在仓库根目录生成 `README.md`，包含业务域名、目录结构、成员仓库列表和更新聚合说明。

## 阶段 5：团队聚合（Mode T 详解）

> **定位**：在团队仓执行，从各成员仓的 `_prd-tools/reference/` 聚合事实到团队仓 `team/`。

**前置条件**：
- 当前工作目录是团队仓（含 `team/project-profile.yaml`，`layer: team-common`）
- `team_reference.member_repos[]` 已配置各成员仓路径
- 各成员仓已运行过 `/reference` Mode A/B，有完整的 01-05 YAML
- **各成员仓已将 `_prd-tools/reference/*.yaml` 提交到 git**

**数据源解析优先级**：
1. `local_path` 存在且有 `_prd-tools/reference/` → 直接读本地（最快）
2. `local_path` 不可用 → 跳过该成员仓并在报告中标记

**执行步骤**：

1. **读取配置**：`team/project-profile.yaml` 的 `team_reference.member_repos[]` 和 `aggregation_policy`
2. **解析成员仓**：按优先级找到每个成员仓的 `_prd-tools/reference/` 目录，跳过不可达的仓并报告
3. **读取 YAML**：从每个可达成员仓读取 01-05 五个 YAML 文件
4. **按策略聚合**（见下表 + 硬约束），同时收集冲突
5. **写入产物**：
   - `team/01-codebase.yaml` ~ `team/05-domain.yaml`（带 `repo_scope.authority: team_common` 和时间戳）
   - `{各层}/snapshots/{仓}/` — 成员仓全量镜像 + `_snapshot-meta.yaml`（含 `commit_sha`、`synced_at`）
   - `build/aggregation-report.yaml`（成员仓列表、各产物条目数、快照状态）
   - `build/conflicts.yaml`（如有冲突）
6. **同步 index**：对每个可达成员仓，如果 `_prd-tools/reference/index/` 存在，将其中的 `entities.json`、`edges.json`、`inverted-index.json`、`manifest.yaml` 复制到 `{layer}/snapshots/{repo}/index/`。无 index 的成员仓在 `aggregation-report.yaml` 中标记 `index: skipped`。

### 聚合策略

| 产物 | 默认策略 | 说明 |
|------|---------|------|
| 03-contracts | union_by_id | 同 ID 合并 producer/consumers/checked_by，producer 不一致标 conflict；consumer 调用了但无成员仓声明产出的 endpoint，标记 `endpoint_producer_unverified` |
| 05-domain | union_dedupe | 按 term 名去重，同名不同定义时合并为单一 term 下挂 `views[]` |
| 02-coding-rules | fatal_cross_layer | 只聚合 severity=fatal **且影响 2+ 层或有 cross_layer_impact** 的规则 |
| 04-routing-playbooks | cross_layer_only | 只聚合 target_surfaces 涉及 2+ 层的 playbook |
| 01-codebase | index_only | 只从 contracts 提取 cross_repo_enums 和 cross_repo_entities 索引 |

### 聚合硬约束（Mode T 必须遵守）

1. **01-codebase 禁止推断内容**：`index_only` 策略只允许 `cross_repo_enums` 和 `cross_repo_entities`。以下内容**禁止写入**团队仓 01-codebase：
   - `cross_layer_data_flows`：推断产物，各仓各自的 `data_flows` 保留在成员仓
   - `cross_repo_registration_points`：归入 `04-routing-playbooks`
   - `shared_external_systems`：各成员仓各自的依赖，不聚合
   - `known_gaps`：归入 `build/conflicts.yaml`

2. **02-coding-rules 跨层过滤**：`fatal_cross_layer` 只有满足以下条件之一的 fatal 规则才升级：
   - 规则有 `cross_layer_impact` 字段且非空
   - 规则影响 2+ 层（如"新增 CampaignType 必须三仓同步"）

3. **03-contracts producer 验证**：consumer 调用某 endpoint 但所有成员仓都未声明产出，**不伪造 producer**。正确做法：`producer.repo` 写 `"unconfirmed"`，`producer.verification` 写 `"consumer_orphan"`，写入 `build/conflicts.yaml`。

4. **05-domain 同名术语合并**：同一术语在不同仓有不同定义时，合并为单一 term ID，下挂 `views[]` 数组区分各仓视角。

### 冲突处理

`build/conflicts.yaml` 格式：

```yaml
generated_at: "<ISO-8601>"
total_conflicts: 0
conflicts:
  - type: "contract_producer_mismatch"
    contract_id: "CONTRACT-XXX"
    divergent_claims:
      - repo: "repo-a"
        claim: "..."
      - repo: "repo-b"
        claim: "..."
    suggested_resolution: "ask owner"
```

团队仓的 `conflicts.yaml` 不手工编辑。仲裁方式是回到对应成员仓修正字段 → 重新跑 `/reference` → 回到团队仓重新聚合。

## 阶段 6：团队继承（Mode T2 详解）

> **定位**：在成员仓执行，从团队仓 `team/` 继承公共事实到本仓 `_prd-tools/reference/`。

**前置条件**：
- 当前工作目录是成员仓（含 `_prd-tools/reference/`）
- `project-profile.yaml` 的 `team_reference.upstream_local_path` 指向团队仓本地路径
- `team_reference.inherit_scopes` 已配置继承范围
- 团队仓已运行过 Mode T 聚合

**前置失败处理**：

| 检测项 | 失败时行为 |
|-------|-----------|
| `upstream_local_path` 字段未配置 | 停止，提示用户在 `project-profile.yaml` 配置后重试 |
| `upstream_local_path` 指向的目录不存在 | 停止，提示用户 `git clone` 或 `git pull` 团队仓到该路径 |
| 团队仓存在但 `team/` 目录缺失 | 停止，提示先在团队仓运行 `/reference` Mode T |
| 团队仓 `team/01-05.yaml` 部分缺失 | 部分继承：只继承存在且非空的 scope；缺失的写入 `build/inherit-skipped.yaml` |
| 团队仓某条目 `source: team-common` 但无 `evidence` | 跳过该条目，记入 `inherit-skipped.yaml` |

**执行步骤**：

1. 读取本仓 `_prd-tools/reference/project-profile.yaml`，获取 `team_reference.upstream_local_path` 和 `inherit_scopes`
2. 从团队仓 `team/` 目录读取对应 scope 的聚合 YAML
3. 对每个 scope，按继承规则合并到本仓的对应 YAML 文件
4. 更新 `project-profile.yaml` 的 `team_reference.last_synced`

### 继承规则

| 场景 | 行为 |
|------|------|
| 本仓没有同 ID 条目 | 新增，标 `source: "team-common"`, `read_only: true` |
| 本仓已有同 ID（非 team-common） | 保留本仓版本，记 conflict |
| 本仓已有同 ID（team-common） | 更新为团队仓最新版 |
| coding_rules_fatal | **强制覆盖**（团队级 fatal 规则权威） |

`inherit_scopes` 可选值：`domain_terms`、`contracts_cross_repo`、`coding_rules_fatal`。
