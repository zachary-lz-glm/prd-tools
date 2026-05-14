---
name: team-reference
description: 团队 reference 收集 — 将各成员仓库的 reference 原样收集到团队仓库，不做聚合/合并/冲突检测。适用于团队仓库调用 /team-reference。
---

# team-reference

团队 reference 收集，通过 `/team-reference` 触发。

不做聚合、不合并、不冲突检测。各成员仓的 reference 保持独立原样。

## 工作模式

| 模式 | 何时 | 输出 |
|---|---|---|
| T 收集 | 成员仓 reference 更新后 | `references/{repo}/` — 各成员仓 reference 原样副本 |

## 前置条件

- 当前工作目录是团队仓库（`project-profile.yaml` 含 `layer: team-common` 或存在 `references/` 目录）。
- `project-profile.yaml` 的 `team_repos[]` 已配置各成员仓路径。
- 各成员仓已运行过 `/reference` Mode A/B，有完整 01-05 YAML + index。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md`（本文件） | 执行团队收集时 |
| `skills/reference/workflow.md` | 单仓 reference 详情 |
