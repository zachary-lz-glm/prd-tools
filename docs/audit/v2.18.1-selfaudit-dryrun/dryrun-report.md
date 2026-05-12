# Dryrun 验证报告

> `/self-audit --plugin prd-distill --artifact-path /Users/didi/work/dive-bff/_prd-tools` 干跑结果汇总

## 执行概要

| 指标 | 值 |
|---|---|
| 审计版本 | v2.18.1 |
| 插件范围 | prd-distill |
| 产物路径 | /Users/didi/work/dive-bff/_prd-tools |
| selfcheck 基线 | 14 pass · 1 warn · 0 fail |
| 输出目录 | docs/audit/v2.18.1-selfaudit-dryrun/ |

## Agent 发现统计

| Agent | 职责 | 原始 findings |
|---|---|---|
| Agent A | 静态演练 | 26 (4 P0, 16 P1, 6 P2) |
| Agent B | 跨文件一致性 | 12 (2 P0, 5 P1, 5 P2) |
| Agent C | 产物验证 | 8 (1 P0, 4 P1, 3 P2) |
| **合计** | | **46 raw findings** |

## Merge 去重

| 阶段 | 数量 |
|---|---|
| 去重前（raw total） | 46 |
| 去重后（merged by root cause） | 29 |
| 去重率 | 37% |

去重合并详情：

| 合并组 | 来源 findings | 合并后 ID |
|---|---|---|
| contract-delta schema 漂移 | A-3, A-14, B-01, B-02, B-09, C-6-3 (6→1) | P0-1 |
| report.md 章节数漂移 | A-4, A-17, B-03 (3→1) | P0-2 |
| step 文件/ID 映射 | A-1, A-18, B-04, B-05, B-10 (5→1) | P0-4 |
| step 2.6 context pack | A-8 (1→1) | P0-5 |
| requirement-ir 输入+schema | A-2, A-24, C-6-1 (3→1) | P1-1 |
| layer-impact contract 假阳性 | C-2, C-6-2 (2→1) | P1-2 |
| step 3.6 critique | A-7, A-22 (2→1) | P1-4 |
| step 7 reference update | A-19, B-11 (2→1) | P1-5 |

## P0/P1/P2 分类

| 优先级 | 数量 | 占比 |
|---|---|---|
| P0 | 6 | 21% |
| P1 | 13 | 45% |
| P2 | 10 | 34% |
| **合计** | **29** | 100% |

## Selfcheck 覆盖缺口

| 指标 | 值 |
|---|---|
| 总 merged findings | 29 |
| 被 existing selfcheck 覆盖 | 4 (部分覆盖) |
| **NOT COVERED** | **25** |
| 新增 check 建议 | 7 |

### 覆盖率：14% (4/29)

仅 X1 (workflow step IDs)、C2 (contract top-level)、C3 (artifact validation)、D4 (gate mentions) 部分覆盖了少数 findings。大多数 drift、schema-artifact mismatch、execution flow 问题是现有 selfcheck 无法捕获的。

## 与 v2.18.1 审计重叠分析

| 本次 ID | v2.18.1 对应 | 关系 | 说明 |
|---|---|---|---|
| P0-1 | P0R2-6 | **残留** | P0R2-6 修了 contract.yaml + output-contracts.md，但 03-context.md 未同步 |
| P0-5 | P0-2 | **残留** | P0-2 删了重复段落，但 step 2.6 的 gate enforcement 和编号问题仍在 |
| P1-1 | P0R2-5 | **延伸** | P0R2-5 修了 evidence 结构，但输入源矛盾未解 |
| P1-2 | — | **新发现** | layer-impact contract path 不匹配 |
| P0-2 | — | **新发现** | report.md 章节数漂移 |
| P0-3 | — | **新发现** | step-03 绕过 report gate |
| P0-4 | — | **新发现** | step 文件无映射 |
| P0-6 | — | **新发现** | IR 追溯链断裂 |

**重叠率**：2/6 P0 是 v2.18.1 的残留（P0-1 ≈ P0R2-6, P0-5 ≈ P0-2），4/6 P0 是新发现。
**P0 新发现率**：67% — 说明 self-audit skill 找到了 v2.18.1 审计未覆盖的盲区。

## Skill 质量评估

### 符合预期的方面
- **Agent A 和 B 有重叠**：contract-delta drift（A-3 + B-01）、report sections（A-4 + B-03）、step IDs（A-1 + B-04）都从不同角度发现了同一问题
- **Merge 去重有效**：46 raw → 29 merged，37% 去重率合理
- **selfcheck-delta 不是"全部 covered"**：25/29 findings 未被 selfcheck 覆盖，说明 Agent 挖到了 selfcheck 覆盖不到的层

### 需要关注的方面
- **P0=6 不接近 0**：理论上 v2.18.1 的 P0 都修完了，但仍有 6 个 P0。其中 2 个是残留（修了 contract/output 但漏了 schema），4 个是新发现的架构级问题
- **Agent C 的 IR 追溯链断裂 (P0-6)** 是产物质量问题，不是 prd-tools 源文件问题。标注为"新发现"，但应归因为 LLM 执行偏差而非模板错误
- **03-context.md 是系统性弱点**：被 Agent A、B、C 多次指向，是 schema-artifact drift 的主要来源

### 结论
`/self-audit` skill **可以跑通**。三 Agent 并行 + merge + 输出的完整流程正确执行。发现的问题质量较高（67% P0 为新发现），且 selfcheck-delta 分析揭示了 25 个覆盖缺口。建议在下次迭代修复后再次运行以验证修复效果。
