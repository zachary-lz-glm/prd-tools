# 步骤 1：证据与 Requirement IR

## Pre-flight

支持 `.md/.txt` 文件或粘贴文本。其他格式请先转为 markdown。

## 目标

将 PRD 和可选技术文档解析为：

- `_prd-tools/distill/<slug>/_ingest/*`
- `_prd-tools/distill/<slug>/context/evidence.yaml`
- `_prd-tools/distill/<slug>/context/requirement-ir.yaml`

## 输入

- 来自 `.md/.txt` 或粘贴内容的 PRD。
- 可选后端/API/技术方案文档。
- 如存在，读取 `_prd-tools/reference/04-routing-playbooks.yaml`、`_prd-tools/reference/05-domain.yaml`。
- v3.1 兼容：`_prd-tools/reference/05-routing.yaml`、`_prd-tools/reference/06-glossary.yaml`、`_prd-tools/reference/07-business-context.yaml`。
- 旧版兼容：`_prd-tools/reference/05-mapping.yaml`。

## 执行

1. 读取 `.md/.txt` 文件或接受粘贴文本，Claude 直接解析为 `_ingest/` 证据结构。
2. 读取 `_ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
3. 以 `_ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 context/ evidence 台账。
4. 将 PRD 拆成独立业务 requirement。
4. 按以下信号匹配每个 requirement：
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
5. 产出 `context/requirement-ir.yaml`。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
- PRD evidence 优先映射 `_ingest/evidence-map.yaml` 的 block/table/image 定位。
- 图片、截图、流程图没有人工确认时，只能产生低置信度问题，不能当成已确认需求。
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
