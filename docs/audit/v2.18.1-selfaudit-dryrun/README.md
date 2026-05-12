# v2.18.1-selfaudit-dryrun 审计报告

> **dryrun 验证**：2026-05-12 对 prd-tools v2.18.1 执行 `/self-audit --plugin prd-distill` 技能的干跑验证。
> 目的：验证 self-audit skill 本身能否跑通，以及 v2.18.1 修复后残留问题。
> 读者：prd-tools 维护者。

## 文档拆分

| 文件 | 内容 | 执行顺序 |
|---|---|---|
| [P0-fixes.md](./P0-fixes.md) | 6 个 P0 修复（流程阻断/产物不可用） | 先做 |
| [P1-fixes.md](./P1-fixes.md) | 13 个 P1 修复（质量退化） | P0 完成后 |
| [P2-fixes.md](./P2-fixes.md) | 10 个 P2 修复（可维护性） | 有余力可选 |
| [verify-checklist.md](./verify-checklist.md) | 每个 FIX 的独立验证命令 | 每个 FIX 后对照 |
| [selfcheck-delta.md](./selfcheck-delta.md) | selfcheck 覆盖缺口 + 新增 check 建议 | 参考 |
| [context-for-ai.md](./context-for-ai.md) | 审计背景 + 方法论 + 根因 | 开始前读 |
| [dryrun-report.md](./dryrun-report.md) | dryrun 验证指标汇总 | 本报告总览 |

## 修复总览

### P0（6 个）

| ID | 一句话 | 来源 Agent |
|---|---|---|
| P0-1 | contract-delta 03-context.md 残留 "contracts" 顶层键 + 缺 meta/requirement_id/layer | A+B+C |
| P0-2 | report.md 章节数 11 vs 12 漂移（4 处定义不一致） | A+B |
| P0-3 | step-03-confirm.md 绕过 report-confirmation gate（一次性生成 report+plan） | A |
| P0-4 | step 文件编号 01-04 与 gate step IDs 0-9.x 无映射 | A+B |
| P0-5 | step 2.6 Context Pack 编号暗示在 3 之前但实际在 3 之后执行 | A |
| P0-6 | IR 追溯链断裂（4 个 REQ-ID 在 ai-friendly-prd.md 中无标题锚点） | C |

### P1（13 个）

| ID | 一句话 | 来源 |
|---|---|---|
| P1-1 | requirement-ir 输入源矛盾（document.md vs ai-friendly-prd.md）+ schema-artifact 漂移 | A+C |
| P1-2 | layer-impact contract 假阳性（检查 impacts 但产物用 capability_areas） | C |
| P1-3 | plan.md 长度指引冲突（300-600 vs 300-700） | A |
| P1-4 | step 3.6 Critique Pass 无 gate enforcement | A |
| P1-5 | step 7 Reference Update 无执行位置（不在任何 stage） | A+B |
| P1-6 | step 编号 vs 执行顺序不一致（8 在 5 之前） | A |
| P1-7 | step-01-parse must_not_produce 与 Goal/Execution 矛盾 | A |
| P1-8 | query-plan.yaml phases 未充分说明 | A |
| P1-9 | report-confirmation revision_requests 格式漂移 | A |
| P1-10 | readiness 字段名 task_executability vs plan_quality | B |
| P1-11 | gate severity 不一致（quality=warning vs workflow=fail） | B |
| P1-12 | project-profile.yaml 无 fallback 规则 | A |
| P1-13 | workflow.md 853 行过长（attention decay） | A |

### P2（10 个）

| ID | 一句话 | 来源 |
|---|---|---|
| P2-1 | SKILL.md 执行步骤编号 1-17 与 gate ID 0-9 不对应 | A |
| P2-2 | 00-directory-structure.md 文件列表不完整 | A |
| P2-3 | "辅助层"概念未正式定义 | A |
| P2-4 | step 文件 self-check 格式不一致 | A |
| P2-5 | 禁止行为列表 50+ 过长（attention dilution） | A |
| P2-6 | source_blocks 字段类型不一致（string[] vs object[]） | B |
| P2-7 | deprecated score 字段永久双轨 | B |
| P2-8 | 产物缺可选文件 (tables/, conversion-warnings.md) | C |
| P2-9 | OQ 伪问题 (OQ-PRD-003) | C |
| P2-10 | evidence.yaml 字段名漂移（kind→type, summary→desc） | C |

## 与 v2.18.1 审计重叠

| 本次 ID | v2.18.1 对应 | 状态 |
|---|---|---|
| P0-1 | P0R2-6 | **残留**：P0R2-6 修了 contract.yaml + output-contracts.md 但未修 03-context.md |
| P0-2 | — | **新发现** |
| P0-3 | — | **新发现** |
| P0-4 | — | **新发现** |
| P0-5 | P0-2 (部分) | **残留**：P0-2 删了重复段落但 gate enforcement 问题仍在 |
| P0-6 | — | **新发现**（artifact 质量问题） |

## 约定

### 不要动的东西
- 不要改 dive-bff 仓库的任何东西
- 不要跑 release.sh / 改 VERSION
- 不要执行 /prd-distill 或 /reference

### 验收标准
最终 selfcheck 目标：`python3 tools/selfcheck/run.py --all` 保持 14 pass · 1 warn · 0 fail。
