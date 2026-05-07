# 步骤 1：证据与 Requirement IR

## Pre-flight 依赖检查

进入本步骤前，按 PRD 输入类型自检：

| 输入类型 | 必需工具 | 检查方式 | 缺失时的行为 |
|---------|---------|---------|-------------|
| `.docx` / `.pdf` / `.pptx` / `.xlsx` / `.html` / `.epub` | `markitdown` 在 PATH | `command -v markitdown` | **停止本步骤**，提示运行 `bash .prd-tools/doctor.sh --fix` |
| PRD 含图片/流程图/截图 | Vision API key | `$ANTHROPIC_AUTH_TOKEN` 或 `$OPENAI_API_KEY` | 继续，但所有图片在 `media-analysis.yaml` 标 `status: pending_human_review` |
| `.md` / `.txt` / 粘贴文本 | 无 | — | 直接进入 ingest |

依赖缺失时不要伪造证据。`extraction-quality.yaml` 必须如实记录跳过的图片/表格，evidence 链路只能引用真实读到的内容。

## 目标

将 PRD 和可选技术文档解析为：

- `_prd-tools/distill/<slug>/_ingest/*`
- `_prd-tools/distill/<slug>/spec/evidence.yaml`
- `_prd-tools/distill/<slug>/spec/requirement-ir.yaml`

## 输入

- 来自 `.docx/.md/.txt/.pdf` 或粘贴内容的 PRD。
- 可选后端/API/技术方案文档。
- 如存在，读取 `_prd-tools/reference/04-routing-playbooks.yaml`、`_prd-tools/reference/05-domain.yaml`。
- v3.1 兼容：`_prd-tools/reference/05-routing.yaml`、`_prd-tools/reference/06-glossary.yaml`、`_prd-tools/reference/07-business-context.yaml`。
- 旧版兼容：`_prd-tools/reference/05-mapping.yaml`。

## 执行

1. 文件型 PRD 优先运行 `scripts/ingest_prd.py`，生成 `_ingest/`。
2. 读取 `_ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
3. 以 `_ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 spec/ evidence 台账。
4. 将 PRD 拆成独立业务 requirement。
4. 按以下信号匹配每个 requirement：
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
5. 产出 `spec/requirement-ir.yaml`。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
- PRD evidence 优先映射 `_ingest/evidence-map.yaml` 的 block/table/image 定位。
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
