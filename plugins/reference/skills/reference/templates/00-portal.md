# <project> Reference

`schema_version`: 4.0
`tool_version`: <tool-version>
`last_verified`: <YYYY-MM-DD>
`layer`: <frontend|bff|backend|multi-layer>
`owner`: <team>

## 项目画像

- 技术栈：
- 主要入口：
- 能力面：
- 测试入口：
- 构建/运行入口：

## 按场景阅读（人类入口）

| 我想... | 先看 | 再看 |
|---------|------|------|
| 了解项目整体结构 | `01-codebase.yaml` | `project-profile.yaml` |
| 新增一个活动类型 | `04-routing-playbooks.yaml` | `02-coding-rules.yaml`, `03-contracts.yaml` |
| 对齐跨层接口 | `03-contracts.yaml` | `01-codebase.yaml` |
| 理解业务术语 | `05-domain.yaml` | - |
| 查编码规范和红线 | `02-coding-rules.yaml` | - |
| 排查已知坑点 | `02-coding-rules.yaml` (danger_zones + war_stories) | `04-routing-playbooks.yaml` (common_mistakes) |

## 文件地图

| 文件 | 职责 | 不放什么 |
|------|------|---------|
| `project-profile.yaml` | 项目画像：技术栈、入口、能力面、候选路径 | 不放具体枚举值、不放契约字段 |
| `01-codebase.yaml` | 静态清单：目录、枚举、模块、入口点、注册点 | 不放字段级契约、不放实现步骤 |
| `02-coding-rules.yaml` | 编码规则：规范、约束、红线、反模式、踩坑经验 | 不放契约字段、不放打法步骤 |
| `03-contracts.yaml` | 契约：endpoint、schema、event、字段级定义 | 不放编码规则、不放路由信号 |
| `04-routing-playbooks.yaml` | 路由信号 + 场景打法 + QA 矩阵 + golden samples | 不放枚举值、不放契约字段 |
| `05-domain.yaml` | 业务领域：术语、背景、隐式规则、决策日志 | 不放代码路径、不放实现细节 |

## 健康状态

- status:
- score:
- warnings:
- next_actions:
