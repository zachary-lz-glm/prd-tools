# 步骤 1：证据与 Requirement IR

## 目标

将 PRD 和可选技术文档解析为：

- `_output/prd-distill/<slug>/evidence.yaml`
- `_output/prd-distill/<slug>/requirement-ir.yaml`

## 输入

- 来自 docx/md/粘贴内容的 PRD 文本。
- 可选后端/API/技术方案文档。
- 如存在，读取 `_reference/05-routing.yaml`、`_reference/06-glossary.yaml`、`_reference/07-business-context.yaml`。
- 旧版兼容：`_reference/05-mapping.yaml`。

## 执行

1. 将 PRD 转成可读文本；docx 转换失败时，让用户提供 md/text。
2. 先建立 evidence 台账，再做结论。
3. 将 PRD 拆成独立业务 requirement。
4. 按以下信号匹配每个 requirement：
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
5. 产出 `requirement-ir.yaml`。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
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
