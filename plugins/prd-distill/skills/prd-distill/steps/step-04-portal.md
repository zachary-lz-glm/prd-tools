<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>9</current_step>
  <allowed_inputs>report.md, plan.md, spec/ai-friendly-prd.md, context/*</allowed_inputs>
  <must_not_read_by_default>source code (not needed for portal rendering)</must_not_read_by_default>
  <must_not_produce>any context/ YAML files</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

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

## Self-Check

- [ ] [M] `portal.html` 渲染完成后，如果 `context/evidence.yaml` 存在，其中所有 EV-PRD-* ID 必须出现在 portal 的 HTML 内容中（全集校验）。缺失 EV 必须在 portal 源码报告中标注为 "unrendered"。
  - verify: `grep -oE 'EV-PRD-[0-9]+' portal.html | sort -u > /tmp/portal_evs.txt && grep -oE 'EV-PRD-[0-9]+' context/evidence.yaml | sort -u | comm -23 - /tmp/portal_evs.txt`
  - expect: 无输出（所有 EV-PRD-* 均已渲染）
