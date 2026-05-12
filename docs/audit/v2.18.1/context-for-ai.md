# 审计背景（开始修复前必读）

## 为什么要做这次修复

prd-tools 从 v2.16.1 → v2.18.1 经历了一次大迭代（约 30 个 commit），包括：

- 三段式工作流骨架 + Workflow State v2
- 保真度优先架构修正（主输入回退 + prd-coverage-gate）
- Artifact Contract MVP（通用 validator + 4 个核心 contract）
- Context Budget + Two-Pass Critic gate
- Evidence Index 准确性提升（多行签名、跨文件边、增量更新、领域术语桥接）
- 删除 agent
- AI-friendly PRD Compiler MVP（13-section 规范化 PRD）
- Portal 模板 + 渲染脚本
- human_checkpoint 单复数兼容
- context-pack.py 兼容 IR-xxx
- "全盘修复 gate/workflow/command 一致性问题"（v2.18.1 最后这一个 commit）

即便最后一个 commit 名字叫"全盘修复一致性"，**仍然残留了结构性问题**。本次审计用三个并行 Agent 把这些残留问题挖出来。

## 审计是怎么做的

1. **Agent A'（静态演练）**：假装自己是运行 /prd-distill 和 /reference 的 LLM，从头到尾读 SKILL.md / workflow.md / steps/ / commands，找"读到这里下一步该干啥不清楚"/"指令自相矛盾"/"注意力衰减"的位置。
2. **Agent B（一致性扫描）**：grep + diff 方式横向扫 workflow / step / command / gate 脚本 / contracts / schemas，找字段名漂移、step-id 错配、单复数不一致、引用已删除文件等。
3. **Agent C（产物审计）**：针对 v2.18.0 在 dive-bff 实跑的产物（油站新司机完单领券这个真实需求），对照源码验证 plan.md 里的文件路径/行号是否真实、OQ 是否伪命题、IR 追溯链是否断、字段名是否编造。

## 五类系统性根因

本次发现的所有问题基本都能归到这五类。修 FIX 时心里记着根因，能帮你判断"要不要顺手改一个旁边看起来像但没在 FIX 里的东西"——**不要顺手改**，但要理解它们为什么存在：

1. **副本漂移（copy drift）**
   同一事实在 SKILL.md / workflow.md / command.md / step-*.md / references/ 各写一份副本，迭代时没同步更新。典型：Mode Selection YAML 3 份；Step 2.5/2.6/8.6 在 workflow.md 里整段重复；plan.md 章节数三处说法不一（10/11/12）。

2. **脚本即 schema**
   document-structure.json、evidence index manifest、coverage-report.yaml 的字段由 Python 脚本生成决定，文档里无定义。下游消费者不知道该期望什么字段 → 字段发散。

3. **code_scan 范围不足**
   只扫 `src/`，不扫 `build/` 等已编译产物。在 dive-bff 场景下，`build/` 里有一份早期实现过的 `CompleteOrderGas=44`，LLM 完全没看见，自创了个 `GasStationDxGy` → **上线直接炸**。

4. **Gate 无 fix_hint**
   所有 gate 脚本只说"错了什么"，不说"怎么修"。LLM 读到 fail 只能二次猜，进入"修 → 再失败 → 再修"循环，通常 3-5 次才修对。

5. **硬编码业务词**
   `final-quality-gate.py` 的 KEY_ANCHOR_FILES、`context-pack.py` 的 seed_queries 硬编码了 dive-bff 的文件名（campaignType.ts / previewRewardType.ts 等）。工具一旦复用到别的项目，永远 score cap 40、seed 全 miss，看起来一切正常实则失效。

## 对执行修复的影响

本文档把 27 个问题拆成 27 个 FIX，每个都精确到文件 + 行号 + 修改规则。执行时请**严格按 FIX 逐个来**，不要自己扩大范围。

**不要做的事**：
- 不要"顺手"重构。如果你看到一段代码不符合审计建议但不在 FIX 列表里，不要改。
- 不要"顺手"统一风格。如果 workflow.md 和 SKILL.md 两处写法不一致但不在 FIX 列表里，不要改。
- 不要"顺手"加测试。现有的 gate 脚本已经是部分测试，FIX 完后它们会验证。
- 不要改 CHANGELOG、VERSION、plugin.json、marketplace.json。
- 不要自己决定"这个 FIX 可以跳过"，遇到不理解的先停下回报。

**要做的事**：
- 每个 FIX 改完立即跑 `verify-checklist.md` 里对应的 minimal_verify。
- 每个 FIX 单独 commit，commit 信息按 README 里规定的格式。
- 做完所有 FIX 写 `docs/audit/v2.18.1/report.md` 汇总验证证据。

## 关于产物证据

审计报告里引用了 dive-bff 仓库里 `AI_test_prd_tools_v2.18.0` 分支的 artifact 作为"LLM 实际跑出来的产物"。这些产物**不能动**（它们是证据）。本次修复全部发生在 prd-tools 仓库内。

## 关于 memory

审计里提到"memory 里旧 session 记过 CompleteOrderGas=44 已经存在于 build/"——这是审计发现 P0-5 的线索之一，但 **memory 的修复不在本文档范围内**（memory 是用户侧的，不在 prd-tools 仓库）。

## 版本范围

| 审计时快照 | 值 |
|---|---|
| prd-tools VERSION | 2.18.1 |
| 最近 commit | 834ceb5 fix: 全盘修复 gate/workflow/command 一致性问题 |
| 审计日期 | 2026-05-12 |
| 审计分支 | dive-bff `AI_test_prd_tools_v2.18.1_audit`（基于 `AI_test_prd_tools_v2.18.0`，已把既有产物移到 `.v2.18.0_snapshot/` 保留） |

下一个预期版本：**v2.18.2**（由维护者手动发布，你不要发）。
