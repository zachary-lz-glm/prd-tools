---
name: prd-distill
description: 将 PRD、需求文本、技术方案或变更说明先做稳定读取与质量检查，再蒸馏为有证据支撑的 report、plan 和 artifacts，包括 Requirement IR、Layer Impact、Contract Delta、技术方案、开发/测试/契约计划和 reference 回流建议。适用于用户调用 /prd-distill，要求分析 PRD、拆需求、评估影响范围、生成开发计划、识别接口契约风险或生成 QA 矩阵时。
---

# prd-distill

Claude Code 中通过 `/prd-distill <PRD 文件或需求文本>` 触发。

人类可读文档见插件根目录 `README.md`。

## 触发条件

- 用户提供 PRD 文件路径或需求文本，要求分析。
- `/prd-distill` 命令。
- 需要评估影响范围、拆任务、对齐接口、生成 QA 矩阵。

不触发：直接改代码、无可分析输入、用户明确不要分析。

## 核心职责

不是总结 PRD，而是回答五个问题：

1. PRD 到底新增、修改、删除或不改变哪些需求点。
2. 这些需求分别影响前端、BFF、后端的哪些能力面。
3. 哪些字段、枚举、schema、endpoint、event 需要跨团队对齐。
4. 开发顺序和 QA 覆盖场景。
5. 本次需求暴露了哪些新知识，需回流到 `_reference/`。

## 输入

- PRD：`.docx`/`.md`/`.txt`/`.pdf`/`.pptx`/`.xlsx`/`.html` 或粘贴文本。
- 可选技术方案、API 文档、接口定义。
- 当前项目源码路径。
- 当前项目 `_reference/`。
- 可选历史分支、diff、已有实现。

PRD 读取规则：
- 文件输入优先运行 `uv run <skill>/scripts/ingest_prd.py <prd> --out _output/prd-distill/<slug>/prd-ingest`。
- 粘贴文本 → 手工创建 ingestion 证据（来源、段落定位、质量说明）。
- 用 MarkItDown (microsoft/markitdown) 转换文件格式。
- 配置 `ANTHROPIC_AUTH_TOKEN` 或 `OPENAI_API_KEY` 后自动启用 LLM Vision 分析图片。
- `.md/.txt` 保留原文行号和 markdown 图片引用。
- 无 vision/人工确认的截图、流程图不能作为高置信度结论。

## 输出结构

```text
_output/prd-distill/<slug>/
├── prd-ingest/                    # PRD 原始读取
│   ├── source-manifest.yaml       #   文件路径、格式、hash、读取方式
│   ├── document.md                #   转换后可读 markdown
│   ├── document-structure.json    #   段落、表格、图片结构块
│   ├── evidence-map.yaml          #   PRD 块级证据 id
│   ├── media/                     #   抽出的图片
│   ├── media-analysis.yaml        #   图片语义分析状态
│   ├── tables/                    #   抽出的表格
│   ├── extraction-quality.yaml    #   pass/warn/block 质量门禁
│   └── conversion-warnings.md     #   转换风险
├── report.md                      # 渐进式披露报告
├── plan.md                        # 技术方案 + 开发/测试计划
└── artifacts/
    ├── evidence.yaml              # 证据台账
    ├── graph-context.md           # 图谱驱动的函数级上下文
    ├── requirement-ir.yaml        # 结构化需求
    ├── layer-impact.yaml          # 分层影响
    ├── contract-delta.yaml        # 契约差异
    └── reference-update-suggestions.yaml  # 回流建议
```

## 输出文件边界

| 文件 | 用途 | 不放 |
|---|---|---|
| `prd-ingest/*` | PRD 原始读取结果 | 不写业务结论 |
| `report.md` | 渐进式披露：摘要→变更→字段→规则→Checklist→契约风险→§11 阻塞项 | 不展开 YAML 证据链 |
| `plan.md` | 技术方案 + 实现计划 + QA 矩阵 + 回滚方案 | 不复制 PRD 原文 |
| `artifacts/evidence.yaml` | 证据台账：PRD、技术方案、源码、负向搜索、图谱查询 | 不下结论 |
| `artifacts/graph-context.md` | 函数级技术上下文：GitNexus 符号/调用链、Graphify 业务约束 | 不替代源码确认 |
| `artifacts/requirement-ir.yaml` | 结构化需求：业务意图、规则、验收条件、变更类型 | 不写实现细节 |
| `artifacts/layer-impact.yaml` | 分层影响：目标层、能力面、计划变化、风险 | 不写字段级契约详情 |
| `artifacts/contract-delta.yaml` | 契约差异：字段、producer、consumer、alignment_status | 不写开发顺序 |
| `artifacts/reference-update-suggestions.yaml` | 回流建议 | 不直接改 `_reference/` |

## 能力面适配器

读取 `references/layer-adapters.md` 按目标层套用适配器。路径只是候选，最终以能力面证据为准。

## 契约规则

以下场景必须检查或生成 Contract Delta：
- 影响超过一层。
- 新增或修改 request/response/schema/event/payload/DB 字段。
- 涉及权益、券、奖励、支付、预算、审计、异步事件、外部系统。
- 任一层只是展示/透传但 owner 未确认。

`alignment_status` 规则：
- `aligned`：producer 和 consumer 都有证据。
- `needs_confirmation`：PRD 有描述但某层未确认。
- `blocked`：字段/枚举/required/时序冲突。
- `not_applicable`：单层内部变化。

## 质量规则

- 先证据，后结论。
- 每个 requirement 至少有 PRD 或技术文档证据（优先来自 `prd-ingest/evidence-map.yaml`）。
- 每个 layer impact 至少有源码或负向搜索证据。
- `extraction-quality.yaml` 为 `warn` 时必须在 `report.md` §11 暴露。
- 业务关键规则不能只靠前端守。
- 中低置信度项必须进入 `report.md` §11。
- 不确定标 `confidence: low`，不补脑。
- 不直接修改 `_reference/`，只生成回流建议。

## 图谱增强（可选）

当 GitNexus 或 Graphify 可用时，必须构建一次需求级图谱上下文 → `artifacts/graph-context.md`。

| 场景 | 工具 | 查询 |
|---|---|---|
| PRD 概念→代码路由 | GitNexus | `query` 按业务实体/字段/接口查 execution flows |
| 函数级上下文 | GitNexus | `context` 获取 callers/callees、文件位置 |
| 影响范围评估 | GitNexus | `impact` 获取爆炸半径 |
| 契约 consumer 发现 | GitNexus | `route_map`/`api_impact` 补充 consumer |
| 业务规则约束 | Graphify | `/graphify path`/`/graphify explain` |

图谱不可用时回退到 Read + rg/glob。

如果 `_output/graph/graph-sync-report.yaml` 存在且 provider available，优先读取图谱证据。GitNexus AST 提取可作 high-confidence 代码线索；Graphify INFERRED 只能作 medium/low 业务线索。

## 暂停条件

- PRD 无法读取且无文本输入。
- `extraction-quality.yaml` 为 `status: block`。
- 关键要求只存在于图片中，无 vision/人工确认。
- 目标仓库路径不存在。
- 多层契约冲突导致计划不可执行。
- 缺少关键证据且无法补齐。

## 执行步骤

1. 确认 PRD 来源和目标项目路径。
2. PRD ingestion：运行 `ingest_prd.py`，检查 `extraction-quality.yaml`。
3. 读取 `_reference/`（优先 v4，兼容 v3.1）。
4. 建立 `artifacts/evidence.yaml`，映射 ingestion 证据后补充源码/图谱证据。
5. 拆 `artifacts/requirement-ir.yaml`。
6. 构建 `artifacts/graph-context.md`。
7. 生成 `artifacts/layer-impact.yaml`。
8. 生成 `artifacts/contract-delta.yaml`。
9. 生成 `plan.md`（消费 `graph-context.md` 函数级上下文）。
10. 生成 `report.md`（渐进式披露 + 图谱命中摘要 + §11）。
11. 生成 `artifacts/reference-update-suggestions.yaml`。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整蒸馏时 |
| `references/output-contracts.md` | 确认输出格式和字段边界时 |
| `references/layer-adapters.md` | 判断能力面时 |
| `references/selectable-reward-golden-sample.md` | 复杂需求校准时 |
| `references/external-practices.md` | 解释设计依据时 |

## 完成标准

完成后必须说明：
- 输出目录路径。
- `report.md` 最重要结论。
- `report.md` §11 最重要阻塞项。
- 是否存在 `needs_confirmation` 或 `blocked` 契约。
- 是否生成 reference 回流建议。
