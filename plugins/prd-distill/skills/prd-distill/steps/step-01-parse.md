# 步骤 1：证据与 Requirement IR

## 目标

将 PRD 和可选技术文档解析为：

- `_output/prd-distill/<slug>/prd-ingest/*`
- `_output/prd-distill/<slug>/artifacts/evidence.yaml`
- `_output/prd-distill/<slug>/artifacts/requirement-ir.yaml`

## 输入

- 来自 `.docx/.md/.txt/.pdf` 或粘贴内容的 PRD。
- 可选后端/API/技术方案文档。
- 如存在，读取 `_reference/05-routing.yaml`、`_reference/06-glossary.yaml`、`_reference/07-business-context.yaml`。
- 旧版兼容：`_reference/05-mapping.yaml`。

## 执行

1. 文件型 PRD 优先运行 `scripts/ingest_prd.py`，生成 `prd-ingest/`。
2. 读取 `prd-ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
3. 以 `prd-ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 artifacts evidence 台账。
4. 将 PRD 拆成独立业务 requirement。
4. 按以下信号匹配每个 requirement：
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
5. 产出 `artifacts/requirement-ir.yaml`。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
- PRD evidence 优先映射 `prd-ingest/evidence-map.yaml` 的 block/table/image 定位。
- 图片、截图、流程图没有 vision/OCR 或人工确认时，只能产生低置信度问题，不能当成已确认需求。
- IR 不写文件级实现细节。
- 使用 `ADD | MODIFY | DELETE | NO_CHANGE`。
- 业务规则、限制、互斥、权益、奖励发放、审计、rollout 假设都必须显式写出。
- 未知项进入 `open_questions`，不要隐藏不确定性。

## 最小输出

```yaml
requirements:
  - id: "REQ-001"
    title: ""
    intent: ""
    change_type: "ADD"
    target_layers: ["frontend", "bff", "backend"]
    rules: []
    acceptance_criteria: []
    evidence: ["EV-001"]
    confidence: "medium"
open_questions: []
```
