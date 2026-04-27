# /prd-distill — PRD 蒸馏工具

## 入口行为

当用户输入 `/prd-distill` 时，按以下流程执行：

### 1. 检查前置条件

读取 `_reference/05-mapping.yaml`（PRD 路由表 + 能力清单）。

- 文件存在 → 继续，读取 `layer` 字段确定目标层（frontend / bff / backend）
- 文件不存在 → 提示用户先运行 `/build-reference` 构建领域知识，然后 HALT

同时验证以下文件是否齐全：
- `_reference/05-mapping.yaml` — 必须存在（路由表 + inventory + 能力边界 + golden_samples + structural_patterns）
- `_reference/01-entities.yaml` — 必须存在（枚举定义）
- `_reference/06-glossary.yaml` — 必须存在（术语表 + 同义词）
- `_reference/04-constraints.yaml` — 应存在（约束规则，缺失时跳过 fatal_errors 检查）

### 2. 收集 PRD 输入

使用 AskUserQuestion 引导用户提供 PRD：

> **请提供 PRD 来源：**
> - **文件路径**（.docx / .md）
> - **直接描述需求**（自然语言）
> - **其他**（粘贴内容等）

支持两种输入方式：
1. **文件路径**：读取 .docx（自动分级回退转换：pandoc → mammoth → textutil → 提示用户）或 .md 文件
2. **自然语言描述**：直接使用用户输入的文本

### 3. 可选：收集后端技术文档

使用 AskUserQuestion 询问：

> **是否有本次需求的后端技术文档？**（描述后端 API 变更）
> - **有** → 请提供文件路径
> - **没有** → 继续仅基于 PRD 蒸馏

### 4. 执行蒸馏

输入收集完成后：
- 读取 `_reference/05-mapping.yaml`（PRD 路由表 + 能力清单 + 能力边界 + golden_samples + structural_patterns）
- 读取 `_reference/01-entities.yaml`（枚举定义）
- 读取 `_reference/06-glossary.yaml`（术语表 + 同义词）
- 读取 `workflow.md` 并按 3 步流程执行

### 5. 输出

蒸馏完成后生成：
- `_output/distilled-<campaign-name>.md` — 蒸馏报告（含变更分类 ADD/DELETE/MODIFY + 字段清单 + YAML 块）
- `_output/distill-progress.yaml` — 蒸馏进度

## 快速体验

- 前端示例 PRD：`examples/dive-frontend/step1-prd-distill/`
- BFF 示例 PRD：`_bff-gen/examples/sample-prd-shift-checkin.md`

## 文件索引

| 文件 | 职责 |
|------|------|
| `workflow.md` | 3 步蒸馏流程编排（解析→分类→确认） |
| `steps/step-01-parse.md` | 步骤 1：解析 PRD + 路由匹配 |
| `steps/step-02-classify.md` | 步骤 2：变更分类（ADD/MODIFY/DELETE）+ 结构化 |
| `steps/step-03-confirm.md` | 步骤 3：变更分类确认 + 置信度检查 + 人工确认 |
