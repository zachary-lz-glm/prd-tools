# prd-distill Workflow

## 概述

3 步工作流，将原始 PRD 蒸馏为带变更分类（ADD/DELETE/MODIFY）的结构化开发文档。蒸馏结合领域知识（`_reference/05-mapping.yaml`）进行路由匹配、能力检查和变更分类。**参考是快速通道，源码是最终权威**。支持前端、BFF、后端三层通用。

```
PRD + reference/01 → step-01(解析+路由匹配+代码锚定) → step-02(分类+源码验证) → step-03(确认+输出) → 蒸馏报告
```

## 3 步定义

| 步骤 | 名称 | 输入 | 输出 | 人工确认 |
|------|------|------|------|---------|
| 1 | 解析 + 路由匹配 | PRD 文档 + `_reference/05-mapping.yaml` | 路由结果 + 原始提取 | 否 |
| 2 | 分类 + 结构化 | 路由结果 + inventory 检查 | 带 ADD/DELETE/MODIFY 的蒸馏草稿 | 否 |
| 3 | 确认 + 输出 | 蒸馏草稿 | 最终蒸馏报告 | **是** — 确认所有 low/medium 项 + 变更分类 |

## 进度追踪

进度存储在 `_output/distill-progress.yaml` 中。

```yaml
session_id: "distill-{timestamp}"
created_at: "2026-04-24T10:00:00Z"
current_step: 1
prd_source: "/path/to/prd.docx"
reference_used: "_reference/05-mapping.yaml"
layer: <frontend|bff|backend>  # 从 reference/01 的 layer 字段读取
steps:
  step_01:
    status: in_progress         # not_started | in_progress | completed | failed
    started_at: "2026-04-24T10:00:00Z"
    completed_at: null
  step_02:
    status: not_started
    started_at: null
    completed_at: null
    items_classified: 0
  step_03:
    status: not_started
    started_at: null
    completed_at: null
last_updated: "2026-04-24T10:00:00Z"
```

## 步骤间数据传递

| 步骤 | 写入文件 | 读取文件 |
|------|---------|---------|
| step-01 | `_output/distilled-<name>-routing.md` | PRD 原文 + `_reference/05-mapping.yaml` + **项目源码** |
| step-02 | `_output/distilled-<name>-draft.md` | routing + `_reference/05-mapping.yaml` inventory + **项目源码** |
| step-03 | `_output/distilled-<name>.md` | draft + 用户确认 |

## 确认流程

蒸馏完成后，根据置信度分布和变更分类决定确认方式（step-03 执行）：

1. **变更分类确认**（新增）：展示 ADD/DELETE/MODIFY 汇总表，用户确认分类是否准确
2. **置信度分级确认**（原有）：
   - **全部 high** → 简要确认 `[Y/n]`
   - **有 medium** → 列出逐个确认
   - **有 low** → **强制逐个确认** + 展示 PRD 原文引用

## 错误处理

- PRD 文件不存在 → 立即暂停 + 明确错误
- PRD 内容无法解析 → 提示检查文件格式
- reference/01 路由表无法匹配 → 标记 change_type: ADD，置信度 low
- Token 超限 → 分段蒸馏

## 执行准则

1. **reference 是快速通道，源码是最终权威** — reference 帮助 AI 快速理解项目结构，但不替代源码验证。涉及 ADD/MODIFY 判断时，必须用 Grep/Read 验证源码
2. **代码锚定（Code Grounding）** — 每个变更分类（ADD/MODIFY/DELETE/NO_CHANGE）必须有源码依据。reference 中的 `implemented` 标记仅作为初始假设，关键判断必须锚定到实际代码
3. **每个功能点必须标注变更类型** — ADD / MODIFY / DELETE / NO_CHANGE
4. **每个字段必须标注置信度** — high / medium / low
5. **每个字段必须标注来源引用** — PRD 原文段落或行号
6. **不确定的一律标 low** — 禁止猜测后标为 high
7. **蒸馏输出格式统一** — Markdown 表格（人可读）+ YAML 块（机器可读）
8. **通用层感知** — 自动从 `05-mapping.yaml` 的 `layer` 字段确定层，按层适配分类和目标格式
9. **验证来源透明** — 每个变更项标注 `verification_source`：`reference_only` / `code_verified` / `code_contradicts_reference`

## 步骤文件执行

- `steps/step-01-parse.md` → 步骤 1
- `steps/step-02-classify.md` → 步骤 2
- `steps/step-03-confirm.md` → 步骤 3
