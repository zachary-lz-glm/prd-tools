---
name: team-distill
description: 团队级 PRD 蒸馏 — 跨多个仓库（前端/BFF/后端）的 PRD 蒸馏，从团队 reference 原样副本生成 team-plan 和各仓库 sub-plan。适用于用户调用 /team-distill，且已有团队 knowledge base 时。
---

# team-distill

通过 `/team-distill <PRD 文件或需求文本>` 触发。

**前置条件**：`project-profile.yaml` 存在且 `layer: "team-common"`，或 `references/` 目录存在且有子目录。

## 与单仓模式的差异

| 方面 | 单仓 `/prd-distill` | 团队 `/team-distill` |
|------|---------------------|---------------------|
| 源码扫描 | rg/glob + reference | **禁止 rg/glob**，只读 `references/{repo}/` 下的 01-05 YAML |
| Step 2.5 Query Plan | index 存在则执行 | 从 `references/{repo}/index/` 加载多仓 index（`context-pack.py --team-references`） |
| Step 3.1 Graph Context | 3 阶段扫描 | **只读 reference**：从各仓 01-05 YAML 构建理解，禁止 rg/glob |
| 涉及仓库识别 | 不适用 | 自动匹配 PRD 需求 → 各仓 reference，识别涉及仓库及角色 |
| Contract Delta | 单仓视角 | 跨仓视角：从各仓 03-contracts.yaml 理解 producer/consumer 边界 |
| Plan | 1 份 plan.md | 1 份 team-plan.md + N 份 plans/plan-{repo}.md |
| Report | 1 份 report.md | 1 份 report.md（按仓库分组展示影响和任务） |

成员仓列表来自 `project-profile.yaml` 的 `team_repos[]`。涉及的仓库和角色从各仓 03-contracts.yaml 自动推断。

## 核心职责

与单仓模式相同（详见 `skills/prd-distill/SKILL.md`），但面向多仓库：
1. 从各仓库 reference 副本获取跨仓实体、契约、规则。
2. 自动识别 PRD 涉及哪些仓库及角色（producer/consumer/middleware）。
3. 生成团队级总计划 + 各仓库独立 sub-plan。

## 触发条件

- 用户调用 `/team-distill`。
- `project-profile.yaml` 含 `layer: "team-common"` 或 `references/` 目录存在。

不触发：无团队 knowledge base、单仓项目。

## 输入

同单仓模式，额外：
- `project-profile.yaml`：团队配置（`team_repos[]`）。
- `references/{repo}/`：各成员仓库的 reference 原样副本（01-05 YAML + index）。

## 输出结构

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # 同单仓
├── report.md                      # 团队级报告（§10 分 5 个子节）
├── team-plan.md                   # 团队级开发计划总览
├── plans/                         # Sub-Plans（动态命名）
│   ├── plan-{repo1}.md            # 成员仓 sub-plan
│   └── plan-{repo2}.md
└── context/
    ├── layer-impact.yaml          # 4 层完整填充
    ├── contract-delta.yaml        # 跨仓 consumers[]
    └── ...                        # 其余同单仓
```

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md`（本文件） | 执行团队蒸馏时 |
| `skills/prd-distill/workflow.md` | 通用步骤详情 |
| `skills/prd-distill/references/output-contracts.md` | 输出格式定义 |
| `skills/prd-distill/references/layer-adapters.md` | 能力面定义 |
