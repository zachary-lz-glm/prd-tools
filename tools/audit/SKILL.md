---
name: self-audit
description: prd-tools 迭代后自审计工具。三 Agent 并行审计（静态演练 + 跨文件一致性 + 产物验证），与 selfcheck 基线对比，输出按优先级分类的 FIX 文档。适用于用户调用 /self-audit，要求检查 prd-tools 自身的一致性、找出工作流/脚本/文档/契约漂移、验证历史产物质量时。
---

# self-audit

Claude Code 中通过 `/self-audit` 触发。

> **内部工具**：本 skill 位于仓库根目录 `tools/audit/` 和 `.claude/commands/self-audit.md`，不在 `plugins/` 下，**不随 marketplace 插件分发**。只有 clone 了 prd-tools 仓库的开发者可用。

## 触发条件

- `/self-audit` 命令。
- prd-tools 完成一次迭代（版本变更、gate/workflow/command 改动、脚本重构、新增 contract/schema）后。
- 用户想验证 prd-tools 自身文档/脚本/契约的一致性。
- 用户想验证 /prd-distill 或 /reference 实际产物的质量。

不触发：直接改代码、无 prd-tools 仓库上下文。

## 核心职责

不是跑 /prd-distill 或 /reference 的完整流程，而是回答四个问题：

1. prd-tools 的 SKILL.md / workflow.md / steps / commands 构成的指令链，对 LLM 来说是否可无歧义执行。
2. workflow 模板（教 AI 生成什么）和 gate 脚本（检查 AI 生成了什么）之间是否存在字段名/格式/结构漂移。
3. 如果有历史产物，产物是否符合当前契约且质量达标。
4. selfcheck 的自动化检查是否覆盖了审计发现的问题；未覆盖的应推荐新增检查。

## 参数

| 参数 | 格式 | 默认值 | 说明 |
|------|------|--------|------|
| `--plugin` | `prd-distill` / `reference` / `all` | `all` | 审计目标插件 |
| `--version` | `<semver>` | 读取 `VERSION` 文件 | 审计版本号（影响输出目录和版本快照） |
| `--artifact-path` | `<dir-path>` | 自动探测 `_prd-tools/` | 产物验证的目标目录 |
| `--skip-selfcheck` | flag | false | 跳过 selfcheck 基线 |

## 执行步骤

### Phase 0: 基线建立

1. 运行 `python3 tools/selfcheck/run.py --all --format json` 获取基线（`--format json` 必须，默认是 text 格式，合并阶段要解析 JSON）。
2. 读取 `VERSION` 文件确定审计版本。
3. 创建输出目录 `docs/audit/<version>/`。
4. 确定审计范围和产物路径。

### Phase 1: 三 Agent 并行

三个 Agent 各自独立运行，产出各自的 findings 列表。详见 `agents/` 目录下的模板。

#### Agent A: 静态演练
读取 `agents/agent-A-static-walkthrough.md` 执行。

#### Agent B: 跨文件一致性
读取 `agents/agent-B-cross-file-consistency.md` 执行。

#### Agent C: 产物验证（条件执行）
读取 `agents/agent-C-artifact-validation.md` 执行。
- 如果有产物目录，则执行。
- 如果无产物，跳过并提示用户先运行 `/prd-distill` 或 `/reference`。

### Phase 2: 合并与去重

读取 `merge-prompt.md` 执行合并逻辑。

### Phase 3: 输出

按 `output-schema.md` 格式写入 `docs/audit/<version>/`。

## 输出结构

```text
docs/audit/<version>/
├── README.md               # 审计报告总览（优先级摘要 + FIX 清单表）
├── context-for-ai.md       # 审计背景（版本快照、审计方法、系统性根因）
├── P0-fixes.md             # P0 FIX 清单（流程阻断/上线风险）
├── P1-fixes.md             # P1 FIX 清单（质量退化）
├── P2-fixes.md             # P2 FIX 清单（可维护性）
├── verify-checklist.md     # 每个 FIX 的独立验证命令
└── selfcheck-delta.md      # selfcheck 覆盖缺口 + 新增 check 建议
```

## 完成标准

完成后必须说明：
- 审计版本和范围（哪个/哪些插件）。
- selfcheck 基线结果（pass/warn/fail 数）。
- Agent A/B/C 各自发现的问题数量。
- 合并去重后按 P0/P1/P2 分类的数量。
- selfcheck 覆盖缺口数量。
- 输出目录路径。
