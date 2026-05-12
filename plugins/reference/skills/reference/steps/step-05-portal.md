<workflow_state>
  <workflow>reference</workflow>
  <current_step>5</current_step>
  <allowed_inputs>_prd-tools/reference/00-portal.md, _prd-tools/reference/project-profile.yaml, _prd-tools/reference/01-05, _prd-tools/reference/index/</allowed_inputs>
  <must_not_read_by_default>source code (not needed for portal rendering)</must_not_read_by_default>
  <must_not_produce>any reference YAML files</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

# 步骤 5：Portal HTML 生成

> **硬约束**：AI 不得手写 portal.html。portal.html 必须由 `render-reference-portal.py` 使用固定模板生成。

## 命令

```bash
python3 .prd-tools/scripts/render-reference-portal.py \
  --root . \
  --template .prd-tools/assets/reference-portal-template.html \
  --out _prd-tools/reference/portal.html
```

## 前置条件

- 步骤 2（reference 主文件）已完成
- 步骤 3.5（Evidence Index）已完成
- `render-reference-portal.py` 和模板已安装（由 install.sh 安装）

## 输入

- `_prd-tools/reference/00-portal.md`
- `_prd-tools/reference/project-profile.yaml`
- `_prd-tools/reference/01-codebase.yaml`
- `_prd-tools/reference/02-coding-rules.yaml`
- `_prd-tools/reference/03-contracts.yaml`
- `_prd-tools/reference/04-routing-playbooks.yaml`
- `_prd-tools/reference/05-domain.yaml`
- `_prd-tools/reference/index/manifest.yaml`

## 输出

- `_prd-tools/reference/portal.html`（自包含，零外部依赖，file:// 可打开）

## 页面结构

- 顶部 summary cards：项目、层级、Reference 文件数、Evidence Index 实体数、生成时间
- 导航 tabs：概览、代码库、接口契约、路由手册、领域模型、Evidence Index、原始文件
- 每个 YAML 文件：字段摘要表 + raw viewer
- Evidence Index：manifest 统计 + raw viewer
- 原始文件：可搜索的 raw viewer

## 约束

- AI 不得手写或修改 portal.html 内容。
- portal.html 是脚本渲染产物，风格由模板固定。
- portal.html 缺失或为空时，reference-quality-gate 必须 fail。
- 最终回复必须说明 portal 是脚本生成。
