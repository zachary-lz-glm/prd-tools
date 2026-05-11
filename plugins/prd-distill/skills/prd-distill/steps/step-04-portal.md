# 步骤 4：Portal HTML 生成

> **硬约束**：AI 不得手写 portal.html。portal.html 必须由 `render-distill-portal.py` 使用固定模板生成。

## 命令

```bash
python3 .prd-tools/scripts/render-distill-portal.py \
  --distill-dir _prd-tools/distill/<slug> \
  --template .prd-tools/assets/distill-portal-template.html \
  --out _prd-tools/distill/<slug>/portal.html
```

## 前置条件

- 步骤 8（report.md）已完成
- 步骤 8.5（final-quality-gate）已完成
- 步骤 8.6（distill completion gate）已通过
- `render-distill-portal.py` 和模板已安装（由 install.sh 安装）

## 输入

- `_prd-tools/distill/<slug>/report.md`
- `_prd-tools/distill/<slug>/plan.md`
- `_prd-tools/distill/<slug>/spec/ai-friendly-prd.md`
- `_prd-tools/distill/<slug>/context/` 下所有文件

## 输出

- `_prd-tools/distill/<slug>/portal.html`（自包含，零外部依赖，file:// 可打开）

## 页面结构

- 顶部 summary cards：PRD 质量、需求数、Ready/Assumption/Blocked、代码锚点、Final Gate
- 导航 tabs：概览、AI-friendly PRD、需求、代码锚点、风险与问题、报告、方案、原始上下文
- 突出展示：prd-quality-report status/score、ai_prd_req_id 计数、planning eligibility 分布、code_anchors/fallback、final-quality-gate 状态
- 原始上下文：可搜索的 raw viewer

## 约束

- AI 不得手写或修改 portal.html 内容。
- portal.html 是脚本渲染产物，风格由模板固定。
- portal.html 缺失或为空时，distill-quality-gate 必须 fail。
- 最终回复必须说明 portal 是脚本生成。
