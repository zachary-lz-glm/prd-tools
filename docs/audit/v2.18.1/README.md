# v2.18.1 审计修复实施文档（GLM 专用）

> 这份文档是 2026-05-12 对 prd-tools v2.18.1 进行的一次多 Agent 审计报告的**可执行版本**。
> 读者：负责执行修复的 AI（GLM 或其它）。验收方：本仓库维护者。
>
> **执行原则**：
> 1. **严格按本文档指令**。不要自己发挥加额外改动。
> 2. **一次只做一个 FIX**，做完立即走自检（文档底部每个 FIX 都带 `verify:` 命令），通过后再做下一个。
> 3. **不要跨 FIX 合并改动**。每个 FIX 产生一个独立 commit，commit 信息用本文档给出的模板。
> 4. **遇到任何与本文档不一致的现状**（比如行号已经漂移、字段名已经改了）先**停下来回报**，不要自行决定。

## 文档拆分

| 文件 | 内容 | 执行顺序 |
|---|---|---|
| [P0-fixes.md](./P0-fixes.md) | 6 个 P0 修复（会让流程直接失败/上线炸） | **先做这个，全部通过再进 P1** |
| [P1-fixes.md](./P1-fixes.md) | 10 个 P1 修复（质量下降不炸） | P0 全绿再做 |
| [P2-fixes.md](./P2-fixes.md) | 11 个 P2 修复（可读性/可维护性） | 有余力再做，可选 |
| [P0-round2-fixes.md](./P0-round2-fixes.md) | **12 个来自实际 /prd-distill 运行日志的 P0R2**（工作流契约 vs gate 契约断层）+ D4 selfcheck 自修 | **round1 修完再做，必须做** |
| [verify-checklist.md](./verify-checklist.md) | 每个 FIX 的独立验证命令清单 | 做完每个 FIX 后对照这个跑 |
| [context-for-ai.md](./context-for-ai.md) | 背景：v2.16.1 → v2.18.0 做了什么迭代、审计怎么做的、哪些是系统性根因 | 开始前读一遍 |

## 修复总览

### P0（6 个，必须做完）

| ID | 一句话 | 预估改动 |
|---|---|---|
| P0-1 | `distill-workflow-gate.py` 加 `import yaml` | 1 行 |
| P0-2 | 删 `workflow.md` 重复的 Step 2.5/2.6 段 | 删 32 行 |
| P0-3 | `reference-step-gate.py` Stage 4 加 `02-coding-rules.yaml` 前置 | 1 行 |
| P0-4 | 重写 `contract-delta.contract.yaml`（字段名与真实 schema 对齐） | 重写 ~25 行 |
| P0-5 | **code_scan 增加 `build/` 目录兜底**（改 step 模板 + query-plan 策略） | 修改 3 个 step 文件 |
| P0-6 | `coverage-report.yaml` 生成器 bug：`missing: ['', '', ...]` 空字符串 | 修 1 个 Python 生成脚本 |

### P1（10 个）

见 `P1-fixes.md`。

### P2（11 个）

见 `P2-fixes.md`。

## 约定

### commit 规范

本仓库用 conventional commit。本次修复统一用如下前缀：

- P0 修复 → `fix(audit-p0): [P0-x] 一句话`
- P1 修复 → `fix(audit-p1): [P1-x] 一句话`
- P2 修复 → `refactor(audit-p2): [P2-x] 一句话`

示例：`fix(audit-p0): [P0-1] distill-workflow-gate.py import yaml`

### 发版规则

**不要**在修复过程中跑 `scripts/release.sh`。所有 FIX 完成后由维护者统一发 v2.18.2。

### 版本号/CHANGELOG

本次修复**不要手动改** `VERSION` / 各 `plugin.json` / `marketplace.json` / `CHANGELOG.md`。发版脚本会自动处理。

### 不要动的东西

- 不要改 `plugins/*/CHANGELOG.md`
- 不要改 `VERSION` 文件
- 不要改 `.claude-plugin/marketplace.json`
- 不要跑 `scripts/release.sh`
- 不要跑 `git push`（维护者自己 push）
- 不要改 dive-bff 仓库的任何东西（审计报告里提到 dive-bff 只是作为证据引用，不要动）
- 不要重构、不要拆文件、不要"顺手清理"

### 验收标准

每个 FIX 都会在 `verify-checklist.md` 里给出 3 类验证：
- **minimal_verify**：改完立即跑，必须过
- **full_verify**：P0/P1 全做完一起跑，必须过
- **evidence**：把 verify 命令的输出贴到 commit message 或 PR 描述里

**最终一把尺**：改完后跑 `python3 tools/selfcheck/run.py --all`，目标是 `0 fail`（`warn` 允许保留，但 commit message 里要说明原因）。

当前（审计快照时）selfcheck 输出：
- 7 fail：D1 / D2 / D5 / D6 / S2 / C2 / X1（对应 P0-1/P0-2/P0-4/P1-1/P1-4/P2-7/P2-8）
- 2 warn：D4 / S3（对应 P1-2 的扩大版、P2-1）
- 6 pass

按 P0+P1 全部修完后，fail 应归零；warn 应仅保留故意不修的。

### 工作分支

基于 `main` 分支新建 `fix/v2.18.1-audit`，所有修复提交到这个分支。做完后发 PR 到 main。

## 问题排查

- 本文档引用的行号是 2026-05-12 审计时的快照。如果你发现行号漂移，用 `grep -n` 或 `rg -n` 的方式按**字符串模式**而不是按行号定位。
- 如果找不到文档描述的代码/字符串，先 `git log -p` 看有没有被改过，不要自己猜。
- 如果某个 FIX 的 `verify` 过不了，不要自己改 verify 命令。停下来回报。

## 报告产出

所有 FIX 做完后，产出 `docs/audit/v2.18.1/report.md`，格式：

```markdown
# v2.18.1 审计修复报告

## 摘要
- P0 修复: x/6
- P1 修复: y/10
- P2 修复: z/11
- 未完成/跳过: 列表 + 原因

## 每个 FIX 的验证输出
### P0-1
[verify 命令输出]

### P0-2
...
```

这份报告会被维护者用作验收依据。
