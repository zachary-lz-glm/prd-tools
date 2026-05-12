# 审计背景与方法论

## 为什么做这次审计

在 dryrun 29 findings 修复后（commit 480f1d0），需要验证修复是否引入了新问题、是否完全消除了原始 P0、以及前次审计未覆盖的 reference 插件是否存在系统性问题。

## 方法论

- **Agent A**（静态演练）：按 spec→report→plan→reference 顺序模拟完整执行链，检查矛盾、缺失过渡、未定义输入输出、gate enforcement 覆盖。
- **Agent B**（跨文件一致性）：交叉比对 schema 字段名、step ID 映射、模板结构、跨引用有效性。
- **Agent C**（产物验证）：SKIPPED — 无可用产物。

## 系统性根因

| 根因类型 | 数量 | 说明 |
|---------|------|------|
| copy_drift | 8 | 同一事实在多文件中不一致（前次修复引入 + 残留） |
| step_id_mismatch | 4 | step 序列在不同文件中不一致 |
| ambiguous_transition | 3 | 步骤间过渡指令缺失或不明确 |
| attention_decay | 2 | 文件过长导致指令稀释 |
| normativeness | 3 | 指令措辞不准确或误导 |
| unclear_instruction | 2 | 缺少必要上下文 |

## 关键发现：前次修复引入的不一致

前次 dryrun 修复中有 3 个 P1 级新问题是由修复本身引入的：

1. **P1-2**（layer-impact）：P1-2 修复将 contract 从 `impacts` 改为 `capability_areas`，但未同步更新 output-contracts.md 的 layer-impact schema（仍用 `impacts`）
2. **P1-8**（evidence fields）：P2-10 修复将 03-context.md evidence schema 从 `kind/summary` 改为 `type/desc`，但未同步 output-contracts.md（仍用 `kind/locator/summary`）
3. **P1-5**（SKILL.md 缺 3.5）：P0-5 将 step 2.6 改为 3.5 并更新了 command.md，但未同步 SKILL.md 的 report stage 序列

**教训**：跨文件修复时必须追踪所有引用位置，特别是 output-contracts.md（双插件共享）和 SKILL.md。

## 版本快照

| 组件 | 版本/行数 |
|------|----------|
| prd-tools | v2.18.1 |
| workflow.md | 869 行 |
| output-contracts.md | ~1020 行 |
| SKILL.md | ~406 行 |
| command.md | ~181 行 |
| selfcheck | 15 checks (C1-C3, D1-D6, S1-S4, X1, X4) |
