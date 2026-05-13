# 团队知识库工作流指南

> 适用版本：v2.17+ | 模式：Mode T（聚合）、Mode T2（继承）

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
bash <(curl -fsSL <install-url>)

# 2. 构建知识库
/reference
# 首次选 Mode F（从零开始），后续用 Mode A（增量更新）

# 3. 提交产物
git add _prd-tools/reference/
git commit -m "chore: update prd-tools reference"
```

### 第二步：初始化团队仓

```bash
# 创建或进入团队仓库
mkdir ~/work/dive-drv-reference && cd ~/work/dive-drv-reference
git init

# 安装 prd-tools
bash <path-to-prd-tools>/install.sh

# 启动团队初始化
/reference
# 选择"团队知识库仓库" → 进入 Mode T-init 交互式初始化
```

### 第三步：执行聚合

```bash
/reference Mode T
```

聚合策略：

| 产物 | 策略 | 说明 |
|------|------|------|
| 01-codebase | `index_only` | 只提取跨仓枚举索引和跨仓实体索引 |
| 02-coding-rules | `fatal_cross_layer` | 只聚合 fatal 级 + 影响跨层的规则 |
| 03-contracts | `union_by_id` | 合并契约，producer 不一致标冲突 |
| 04-routing-playbooks | `cross_layer_only` | 只聚合跨层 playbook |
| 05-domain | `union_dedupe` | 同名术语合并为单一 term 下挂 views[] |

聚合硬约束：
1. 01-codebase 禁止推断内容（无数据流、注册点、外部系统）
2. 02-coding-rules 纯本仓规则不升级
3. 03-contracts 无成员仓声明的 endpoint 标 `endpoint_producer_unverified`，不伪造
4. 05-domain 同名术语合并为单一 term + views[]

### 第四步：处理冲突（如有）

查看 `build/conflicts.yaml`，回到对应成员仓修正字段 → 重新跑 `/reference` → 重新聚合。

### 第五步：团队级 PRD 蒸馏

```bash
/prd-distill <PRD文件路径>
```

系统自动检测 `layer: "team-common"` 进入团队模式。团队模式下：
- Step 2.5 Query Plan：从 `snapshots/{repo}/index/` 加载多仓 index
- Step 3.1 Graph Context：从 `team/01-codebase` + index + snapshots 读取，**禁止 rg/glob**
- Step 3.2 Layer Impact：4 层 IMP 全部从 snapshots 填充
- Step 4 Contract Delta：全栈 consumers[]
- Step 5 Plan：生成 `team-plan.md` + `plans/plan-{repo}.md`

### 第六步：继承回成员仓（Mode T2，可选）

```bash
cd ~/work/genos
/reference Mode T2
```

从团队仓继承跨仓 fatal 规则、领域术语等到本仓 `_prd-tools/reference/`。

## 增量更新

成员仓代码变更后：

```bash
# 1. 在变更的成员仓更新 reference
cd ~/work/dive-bff
/reference                    # Mode A 增量更新
git add _prd-tools/reference/ && git commit -m "chore: update reference"

# 2. 在团队仓重新聚合
cd ~/work/dive-drv-reference
/reference Mode T             # 重新聚合
```

## 常见问题

**Q：某个成员仓没有 index 怎么办？**
A：不影响聚合。该仓标记 `index: skipped`，蒸馏时只能用 YAML 快照做字面匹配。

**Q：团队仓蒸馏时还能用 rg/glob 扫源码吗？**
A：不能。团队仓没有源码，所有代码信息来自 snapshots 和 index。

**Q：聚合后的 01-codebase 为什么没有数据流和注册点？**
A：这些是推断产物，团队仓只保留可验证的事实。

**Q：context-pack.py 的 --team-snapshots 和 --index 有什么区别？**
A：`--index` 加载单仓 index，`--team-snapshots` 自动发现并合并多个成员仓的 index，每个 entity 带 `repo` 字段区分来源。
