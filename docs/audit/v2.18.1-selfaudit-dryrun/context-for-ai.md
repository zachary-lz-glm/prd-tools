# 审计背景（开始修复前必读）

## 为什么要做这次审计

v2.18.1 完成了 39 个 FIX（6 P0 + 10 P1 + 11 P2 + 12 P0R2），selfcheck 从 7 fail 降到 0 fail。本次是 `/self-audit` skill 的**干跑验证**，目的是：

1. 验证 self-audit skill 本身能否正确执行（三 Agent 并行 + merge + 输出）
2. 检查 v2.18.1 修复后是否还有残留问题
3. 发现 selfcheck 未能覆盖的系统性问题

## 审计是怎么做的

三 Agent 并行审计方法论：

| Agent | 职责 | 文件范围 |
|---|---|---|
| Agent A | 静态演练：模拟 LLM 按指令链顺序读取，发现歧义、矛盾、衰减点 | command.md → SKILL.md → workflow.md → steps → contracts → schemas |
| Agent B | 跨文件一致性：机械性字段名/正则/step ID 交叉比对 | 所有文件 vs gate 脚本 |
| Agent C | 产物验证：对照契约/schema 检查实际产物 | `_prd-tools/distill/` 下的所有产出 |

Agent C 激活条件：`--artifact-path` 指向 `/Users/didi/work/dive-bff/_prd-tools`（存在）。

## 系统性根因

| 根因类型 | 描述 | 影响的 FIX |
|---|---|---|
| `copy_drift` | 同一事实在多个文件中描述，迭代时部分文件未同步 | P0-1, P0-2, P1-3, P1-9, P2-2, P2-10 |
| `gate_template_mismatch` | Workflow 模板教 AI 生成一种格式，gate 脚本检查另一种 | P1-2, P1-11, P2-7 |
| `structural_gap` | 缺失映射表、step 文件、或 gate 注册 | P0-3, P0-4, P0-5, P1-4, P1-5, P1-7 |
| `hardcoded_values` | Schema 描述 v5.0 结构但 LLM 实际产出 v1.0 | P1-1, P2-6 |
| `missing_fix_hint` | P0R2-11 修了 gate fix hint 表但未覆盖所有 gate | P0-3 |
| `artifact_quality` | 产物中存在追溯链断裂 | P0-6, P2-8, P2-9 |

## 对执行修复的影响

- **不要动产物**：Agent C 发现的问题存在于 dive-bff 的产物中，那些产物不可修改。应修复 prd-tools 的模板/schema/contract 来防止未来产出同样问题。
- **03-context.md 是重灾区**：Agent A 和 B 都指向 03-context.md 与 output-contracts.md 之间的漂移。03-context.md 应以 output-contracts.md 为 SSOT。
- **step 文件是架构债务**：step-01~04 的编号与 gate step IDs 不对应，是历史遗留。不要求重命名文件，但至少需要映射表。

## 版本范围

| 审计时快照 | 值 |
|---|---|
| VERSION | 2.18.1 |
| 分支 | v2.0 |
| selfcheck | 14 pass · 1 warn · 0 fail |
| PLUGIN_SCOPE | prd-distill |
| ARTIFACT_PATH | /Users/didi/work/dive-bff/_prd-tools |
| Agent A findings | 26 |
| Agent B findings | 12 |
| Agent C findings | 8 |
| 合并去重后 | 29 (6 P0 + 13 P1 + 10 P2) |
