# Audit Output Format Specification

All output lives in `docs/audit/<version>/` where `<version>` matches the `VERSION` file content.

## Required Files

### README.md

```markdown
# v<version> 审计修复实施文档

> 审计日期、方法、读者说明。
> 执行原则（严格按文档、一次一个 FIX、不要顺手改）。

## 文档拆分
| 文件 | 内容 | 执行顺序 |
|---|---|---|

## 修复总览
### P0（N 个，必须做完）
| ID | 一句话 | 预估改动 |
|---|---|---|

### P1（N 个）
### P2（N 个）

## 约定
### commit 规范
### 发版规则
### 不要动的东西
### 验收标准
### 工作分支

## 问题排查
```

### context-for-ai.md

```markdown
# 审计背景（开始修复前必读）

## 为什么要做这次修复
<迭代历史，为什么"全盘修复"后仍有残留>

## 审计是怎么做的
<三 Agent 方法论说明>

## 系统性根因
<按类型列出发现的根因>

## 对执行修复的影响
<不要做的事、要做的事>

## 关于产物证据
<产物不可动>

## 版本范围
| 审计时快照 | 值 |
|---|---|
```

### P0-fixes.md / P1-fixes.md / P2-fixes.md

每个 FIX 条目遵循此结构：

```markdown
## <FIX-ID> — <one-line description>

### 问题
<叙事性描述问题>

### 证据
- `<file>:<line>` — <这个位置说了什么/做了什么>
  ```
  <相关代码/文本片段>
  ```
- `<file>:<line>` — <矛盾位置>
  ```
  <相关代码/文本片段>
  ```

### 修复
<步骤化修复指令：先 grep 定位，再改什么>

### relates_to (optional)
<关联的其他 FIX>

### verify
​```bash
<验证命令，必须 exit 0>
​```

### commit
​```
fix(audit-p0): [P0-x] one-line description
​```
```

P0 文件开头：
```markdown
# P0 修复清单

> **执行原则**：按 P0-1 → P0-N 顺序做。每个 FIX 一个独立 commit。遇到现状与文档描述不一致先停下回报。
```

P1 文件开头：
```markdown
# P1 修复清单

> **前置**：P0 全部做完并通过验证。每个 FIX 独立 commit。commit prefix: `fix(audit-p1): [P1-x] ...`
```

P2 文件开头：
```markdown
# P2 修复清单

> **前置**：P0、P1 全部做完。P2 属于可读性/可维护性改进，可选做。每个 FIX 独立 commit，prefix `refactor(audit-p2): [P2-x] ...`。
```

### verify-checklist.md

```markdown
# 验证清单

> 三类验证：
> - **minimal_verify**：单个 FIX 改完立即跑
> - **batch_verify**：一批全做完跑
> - **regression_verify**：全做完后跑完整自检

## P0
### <FIX-ID> <description>
​```bash
<verify command>
​```

## P1
...

## P2
...

## Regression
​```bash
python3 tools/selfcheck/run.py --all
​```
```

### selfcheck-delta.md

```markdown
# Selfcheck 覆盖缺口分析

## 基线结果
| Check | Status | Message |
|---|---|---|

## 覆盖分析
| Finding | Covered by | or NOT COVERED |
|---|---|---|

## 新增 Check 建议
### NEW-CHECK-<N>
- **category**: <docs|scripts|contracts|cross>
- **description**: <one-line>
- **rationale**: <which finding(s) this catches>
- **pseudo_code**: <brief description>
```

### report.md

此文件在审计阶段不生成。仅在 FIX 全部执行完成后生成，用于验收。格式参考 `docs/audit/v2.18.1/report.md`。

## FIX ID Convention

- P0: `P0-<N>` (e.g., P0-1, P0-2)
- P1: `P1-<N>`
- P2: `P2-<N>`
- Round 2: `P0R2-<N>`

## Commit Convention

```
fix(audit-p0): [P0-x] one-line description
fix(audit-p1): [P1-x] one-line description
refactor(audit-p2): [P2-x] one-line description
fix(audit-p0r2): [P0R2-x] one-line description
```
