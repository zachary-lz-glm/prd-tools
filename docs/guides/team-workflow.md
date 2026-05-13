# 团队知识库工作流指南

> 适用版本：v2.19.2+ | 模式：Mode T（聚合）、Mode T2（继承）

## 概述

团队知识库解决的是**跨仓库 PRD 蒸馏**问题：当一个需求涉及前端、BFF、后端三个仓库时，单仓 reference 无法看到全貌。团队模式把各成员仓的知识库聚合到一个团队仓，然后在团队仓上执行 PRD 蒸馏，产出跨仓整体计划 + 每个成员仓的子计划。

## 前提条件

- 各成员仓已完成 prd-tools 安装（`bash install.sh`）
- 各成员仓已运行 `/reference`（Mode F → Mode A/B），生成了 01-05 YAML + index
- 各成员仓的 `_prd-tools/reference/` 已 commit 到 git

## 完整流程

### 第一步：成员仓准备

在每个成员仓（如 genos、dive-bff、dive-editor-g）分别执行：

```bash
# 1. 安装 prd-tools（如未安装）
bash <(curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/v2.0/install.sh)

# 2. 构建知识库
/reference
# 首次选 Mode F（从零开始），后续用 Mode A（增量更新）

# 3. 提交产物
git add _prd-tools/reference/
git commit -m "chore: update prd-tools reference"
```

产物结构：

```
_prd-tools/reference/
  project-profile.yaml
  01-codebase.yaml
  02-coding-rules.yaml
  03-contracts.yaml
  04-routing-playbooks.yaml
  05-domain.yaml
  index/                        # Evidence Index（代码符号索引）
    entities.json
    edges.json
    inverted-index.json
    manifest.yaml
```

### 第二步：初始化团队仓

```bash
# 创建或进入团队仓库
mkdir ~/work/dive-drv-reference && cd ~/work/dive-drv-reference
git init

# 初始化 prd-tools
bash <path-to-prd-tools>/install.sh

# 启动团队初始化
/reference Mode T-init
```

交互式收集信息后，生成 `team/project-profile.yaml`：

```yaml
layer: "team-common"
team_reference:
  member_repos:
    - repo: "genos"
      local_path: "/Users/didi/work/genos"
      layer: "frontend"
    - repo: "dive-bff"
      local_path: "/Users/didi/work/dive-bff"
      layer: "bff"
    - repo: "dive-editor-g"
      local_path: "/Users/didi/work/dive-editor-g"
      layer: "backend"
  aggregation_policy:
    contracts: "union_by_id"
    domain_terms: "union_dedupe"
    coding_rules: "fatal_cross_layer"
    playbooks: "cross_layer_only"
    codebase: "index_only"
```

### 第三步：执行聚合

```bash
/reference Mode T
```

聚合器执行 6 个步骤：

| # | 步骤 | 说明 |
|---|------|------|
| 1 | 读取配置 | `team/project-profile.yaml` 的成员仓列表和聚合策略 |
| 2 | 解析成员仓 | 按 `local_path` 找到各仓的 `_prd-tools/reference/` |
| 3 | 读取 YAML | 从各成员仓读 01-05 |
| 4 | 按策略聚合 | 按下表策略合并，收集冲突 |
| 5 | 写入产物 | `team/01-05.yaml` + `snapshots/` + `aggregation-report.yaml` |
| 6 | 同步 index | 复制各成员仓 `index/` 到 `{layer}/snapshots/{repo}/index/` |

**聚合策略**：

| 产物 | 策略 | 说明 |
|------|------|------|
| 01-codebase | `index_only` | 只提取跨仓枚举索引和跨仓实体索引，**禁止推断内容** |
| 02-coding-rules | `fatal_cross_layer` | 只聚合 fatal 级 + 影响跨层的规则 |
| 03-contracts | `union_by_id` | 合并契约，producer 不一致标冲突 |
| 04-routing-playbooks | `cross_layer_only` | 只聚合跨层 playbook |
| 05-domain | `union_dedupe` | 同名术语合并为单一 term 下挂 views[] |

**聚合硬约束**：

1. **01-codebase 禁止推断内容** — `cross_layer_data_flows`、`cross_repo_registration_points`、`shared_external_systems`、`known_gaps` 不写入
2. **02-coding-rules 跨层过滤** — 纯本仓内部规则不升级到团队仓
3. **03-contracts producer 验证** — 无成员仓声明产出的 endpoint 标记 `endpoint_producer_unverified`，不伪造 producer
4. **05-domain 同名术语合并** — 不同仓对同一术语有不同定义时，合并为单一 term + views[] 数组

### 第四步：处理冲突（如有）

查看 `build/conflicts.yaml`：

```yaml
conflicts:
  - type: "contract_producer_mismatch"
    contract_id: "CONTRACT-XXX"
    divergent_claims: [...]
  - type: "endpoint_producer_unverified"
    contract_id: "CONTRACT-YYY"
    ...
  - type: "coding_rule_conflict"
    rule_id: "RULE-XXX"
    ...
```

**处理方式**：回到对应成员仓修正字段 → 重新跑 `/reference` → 回到团队仓重新聚合。

### 第五步：团队级 PRD 蒸馏

```bash
/prd-distill spec <PRD文件路径>
```

系统自动检测 `layer: "team-common"` 进入团队模式。三段式流程：

#### spec 阶段

解析 PRD → `spec/ai-friendly-prd.md` + `context/requirement-ir.yaml`

#### report 阶段

| 步骤 | 做什么 | 团队模式数据源 |
|------|--------|---------------|
| Step 2 | 解析 requirement-ir | PRD 文件 |
| Step 2.5 | Query Plan | 从 `snapshots/{repo}/index/` 加载多仓 index（`context-pack.py --team-snapshots`） |
| Step 3.1 | Graph Context | `team/01-codebase` + index 精准匹配 + snapshots 下钻，**禁止 rg/glob** |
| Step 3.2 | Layer Impact | 4 层 IMP 全部从 snapshots 填充 |
| Step 3.5 | Context Pack | 多仓 index 融合，锚点带 repo 前缀（如 `dive-bff:src/config/constant/campaignType.ts:3`） |
| Step 4 | Contract Delta | `team/03-contracts.yaml` 全栈 consumers[] |
| Step 5 | Plan | 生成 `team-plan.md` + `plans/plan-{repo}.md` |

#### plan 阶段

产出：

```
_prd-tools/distill/<slug>/
  report.md                    # 跨仓需求评审报告
  team-plan.md                 # 跨仓整体计划
  plans/
    plan-genos.md              # 前端子计划
    plan-dive-bff.md           # BFF 子计划
    plan-dive-editor-g.md      # 后端子计划
```

### 第六步：继承回成员仓（Mode T2，可选）

让成员仓的单仓蒸馏也能感知跨层约束：

```bash
cd ~/work/genos

/reference Mode T2
```

从团队仓 `team/` 继承跨仓 fatal 规则、领域术语等公共事实到本仓 `_prd-tools/reference/`。

## 增量更新

成员仓代码变更后，重新执行：

```bash
# 1. 在变更的成员仓更新 reference
cd ~/work/dive-bff
/reference                    # Mode A 增量更新
git add _prd-tools/reference/ && git commit -m "chore: update reference"

# 2. 在团队仓重新聚合
cd ~/work/dive-drv-reference
/reference Mode T             # 重新聚合（增量，只同步变更的仓）

# 3. 如需重新蒸馏
/prd-distill spec <PRD>
```

## 数据流

```
成员仓 A ──/reference──→ 01-05 YAML + index
成员仓 B ──/reference──→ 01-05 YAML + index
成员仓 C ──/reference──→ 01-05 YAML
                              │
              /reference Mode T（聚合 + index 同步）
                              │
                              ▼
        team/ (聚合产物)
        {layer}/snapshots/{repo}/ (全量镜像 + index)
                              │
              /prd-distill spec <PRD>
                              │
                              ▼
        query-plan.yaml  ← context-pack.py --team-snapshots
        graph-context.md (index_query + team_snapshot)
        context-pack.md  (多仓锚点，repo 前缀)
        team-plan.md + plans/plan-{repo}.md
```

## 常见问题

**Q：某个成员仓没有 index 怎么办？**
A：不影响聚合。该仓在 `aggregation-report.yaml` 中标记 `index: skipped`，蒸馏时该仓只能用 YAML 快照做字面匹配，无法精准检索代码符号。建议对该仓运行 `/reference` 补建 index。

**Q：团队仓蒸馏时还能用 rg/glob 扫源码吗？**
A：不能。团队仓没有源码，所有代码信息来自 snapshots 和 index。GCTX entry 只允许 `source: "team_snapshot"` 或 `source: "index_query"`。

**Q：聚合后的 01-codebase 为什么没有数据流和注册点？**
A：这些是推断产物（无源码锚点），团队仓只保留可验证的事实。注册点归入 `04-routing-playbooks`，数据流保留在各成员仓各自的 01-codebase 中。

**Q：context-pack.py 的 --team-snapshots 和 --index 有什么区别？**
A：`--index` 加载单仓 index（正常模式），`--team-snapshots` 自动发现并合并多个成员仓的 index（团队模式），合并后每个 entity 带有 `repo` 字段用于区分来源。
