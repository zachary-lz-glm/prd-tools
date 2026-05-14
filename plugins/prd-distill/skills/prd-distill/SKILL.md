---
name: prd-distill
description: 将 PRD、需求文本或技术方案蒸馏为有证据支撑的 report、plan 和 context，包括 Requirement IR、Layer Impact、Contract Delta、技术方案、开发/测试/契约计划和 reference 回流建议。适用于用户调用 /prd-distill，要求分析 PRD、拆需求、评估影响范围、生成开发计划、识别接口契约风险或生成 QA 矩阵时。
---

# prd-distill

通过 `/prd-distill <PRD 文件或需求文本>` 触发。

人类可读文档见插件根目录 `README.md`。

## 核心职责

不是总结 PRD，而是回答五个问题：

1. PRD 到底新增、修改、删除或不改变哪些需求点。
2. 这些需求分别影响前端、BFF、后端的哪些能力面。
3. 哪些字段、枚举、schema、endpoint、event 需要跨团队对齐。
4. 开发顺序和 QA 覆盖场景。
5. 本次需求暴露了哪些新知识，需回流到 `_prd-tools/reference/`。

## 触发条件

- 用户提供 PRD 文件路径或需求文本，要求分析。
- `/prd-distill` 命令。
- 需要评估影响范围、拆任务、对齐接口、生成 QA 矩阵。

不触发：直接改代码、无可分析输入、用户明确不要分析。

## 输入

- PRD：`.md`/`.txt`/`.docx` 或粘贴文本。
- 可选上下游接口文档（强烈建议传入）：后端 API 文档、BFF Schema 文档、上游服务接口定义等。传入后作为 Contract Delta 的直接证据源。
- 当前项目源码路径。
- 当前项目 `_prd-tools/reference/`（必须存在，否则置信度强制降为 `low`）。
- 可选历史分支、diff、已有实现。

## 输出结构

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # PRD 原始读取
│   ├── source-manifest.yaml
│   ├── document.md
│   ├── document-structure.json
│   ├── evidence-map.yaml
│   ├── media/
│   ├── media-analysis.yaml
│   ├── tables/
│   ├── extraction-quality.yaml
│   └── conversion-warnings.md
├── report.md                      # 渐进式披露报告
├── plan.md                        # 函数级技术方案 + 开发计划
└── context/
    ├── requirement-ir.yaml        # 结构化需求
    ├── evidence.yaml              # 证据台账
    ├── readiness-report.yaml      # 就绪度评分
    ├── graph-context.md           # 源码扫描上下文
    ├── layer-impact.yaml          # 分层影响
    ├── contract-delta.yaml        # 契约差异
    ├── report-confirmation.yaml   # 用户确认
    ├── reference-update-suggestions.yaml  # 回流建议
    ├── query-plan.yaml            # 查询计划（辅助层）
    ├── context-pack.md            # 上下文包（辅助层）
    └── final-quality-gate.yaml    # 最终质量门禁（辅助层）
```

## 输出文件边界

| 文件 | 用途 | 不放 |
|---|---|---|
| `report.md` | 渐进式披露：摘要→变更→字段→规则→Checklist→契约风险→阻塞项 | 不展开 YAML 证据链 |
| `plan.md` | 技术方案 + 实现计划 + QA 矩阵 + 回滚方案 | 不复制 PRD 原文 |
| `context/requirement-ir.yaml` | 结构化需求：业务意图、规则、验收条件 | 不写实现细节 |
| `context/evidence.yaml` | 证据台账 | 不下结论 |
| `context/graph-context.md` | 函数级技术上下文 | 不替代源码确认 |
| `context/layer-impact.yaml` | 分层影响 | 不写字段级契约详情 |
| `context/contract-delta.yaml` | 契约差异 | 不写开发顺序 |
| `context/readiness-report.yaml` | 机器可读就绪度评分 | 不替代 report.md |
| `context/reference-update-suggestions.yaml` | 回流建议 | 不直接改 reference |

## 质量规则

- 先证据，后结论。
- 每个 requirement 至少有 PRD 或技术文档证据。
- 每个 layer impact 至少有源码或负向搜索证据。
- `extraction-quality.yaml` 为 `warn` 时必须在 report.md 暴露。
- 业务关键规则不能只靠前端守。
- 中低置信度项必须进入 report.md 阻塞问题章节。
- 不确定标 `confidence: low`，不补脑。
- 不直接修改 `_prd-tools/reference/`，只生成回流建议。
- reference 存在时必须消费；不存在时标记缺失并降低置信度。
- reference 不可盲信：凡是进入 report/plan 的结论，必须被源码、PRD 或负向搜索二次确认。

## Report Review Gate

`report.md` 生成后暂停，要求用户确认 AI 是否读懂 PRD。只有 `approved` 后才生成 plan。

## 暂停条件

- PRD 无法读取且无文本输入。
- `extraction-quality.yaml` 为 `block`。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据且无法补齐。

## 降级条件

- reference 不存在：confidence 强制降为 `low`，report.md 暴露缺失。

## 能力面适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。

## 契约规则

以下场景必须检查或生成 Contract Delta：
- 影响超过一层。
- 新增或修改 request/response/schema/event/payload/DB 字段。
- 涉及权益、券、奖励、支付、预算、审计、异步事件、外部系统。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整蒸馏时 |
| `references/output-contracts.md` | 确认输出格式和字段边界时 |
| `references/layer-adapters.md` | 判断能力面时 |

## 完成标准

完成后必须说明：
- 输出目录路径。
- report.md 最重要结论。
- report.md 阻塞项。
- 是否存在 `needs_confirmation` 或 `blocked` 契约。
- readiness-report.yaml 的 status、score、decision。
