<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>1</current_step>
  <allowed_inputs>PRD file (.md/.txt/.docx), _prd-tools/reference/ (if exists), references/layer-adapters.md</allowed_inputs>
  <must_not_read_by_default>source code (beyond reference routing), report.md, plan.md</must_not_read_by_default>
  <must_not_produce>context/requirement-ir.yaml, context/layer-impact.yaml</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

# 步骤 1：证据与 Requirement IR

## Pre-flight

支持 `.md`/`.txt`/`.docx` 文件或粘贴文本。

**docx 读取流程（零第三方依赖，Claude 原生多模态看图）：**

```bash
# 1. 提取 docx 中的文本内容
unzip -p <file>.docx word/document.xml | sed 's/<[^>]*>//g' | sed '/^$/d'

# 2. 提取 docx 中的图片
mkdir -p _ingest/media
unzip -o <file>.docx "media/*" -d _ingest/
```

- docx 本质是 zip 包，`word/document.xml` 包含正文，`media/` 包含嵌入图片。
- 文本提取：`sed` 去标签得到纯文本，写入 `_ingest/document.md`。
- 图片提取：`unzip` 将 `media/*.png|jpg|jpeg|gif` 抽出到 `_ingest/media/`。
- 图片定位：解析 `word/document.xml` 中的 `<w:drawing>` 或 `<w:pict>` 标签，在纯文本对应位置插入 `![image-N](media/imageN.png)` 占位标记，Claude 后续可用 Read 工具直接查看图片内容。
- Claude 原生支持图片理解（多模态），提取后直接用 Read 工具读取 `_ingest/media/imageN.png`，无需第三方 Vision API。
- 表格基本结构会保留（行会用换行分隔），但复杂格式可能丢失。
- 格式丢失时 `extraction-quality.yaml` 标记 `warn`，在 `report.md` §11 暴露。
- 图片分析结果写入 `_ingest/media-analysis.yaml`：每张图片的文件名、类型（UI截图/流程图/数据图表/装饰图）、关键信息摘要、置信度。

## 目标

将 PRD 和可选技术文档解析为：

- `_prd-tools/distill/<slug>/_ingest/*`
- `_prd-tools/distill/<slug>/context/evidence.yaml`
- `_prd-tools/distill/<slug>/context/requirement-ir.yaml`

## 输入

- 来自 `.md/.txt` 或粘贴内容的 PRD。
- 可选后端/API/技术方案文档。
- `_prd-tools/reference/`（**必须消费**，如存在）：
  - `04-routing-playbooks.yaml`：提取路由表，用于步骤 4 的 PRD 关键词匹配。
  - `05-domain.yaml`：提取领域术语，用于步骤 4 的 glossary 同义词匹配。
  - v3.1 兼容：`05-routing.yaml`、`06-glossary.yaml`、`07-business-context.yaml`。
  - 旧版兼容：`05-mapping.yaml`。

## 执行

1. 读取文件或接受粘贴文本：
   - `.md`/`.txt`：直接读取，保留原文格式。
   - `.docx`：
     a. `unzip -p <file> word/document.xml | sed 's/<[^>]*>//g' | sed '/^$/d'` 提取纯文本。
     b. `mkdir -p _ingest/media && unzip -o <file> "media/*" -d _ingest/` 提取所有图片。
     c. 解析 XML 中的 `<w:drawing>` / `<w:pict>` 标签定位图片插入位置，在文本中插入 `![image-N](media/imageN.png)` 占位标记。
     d. 写入 `_ingest/document.md`。
     e. 用 Read 工具逐个查看 `_ingest/media/` 下的图片，理解内容（UI 截图、流程图、数据图表），将分析结果写入 `_ingest/media-analysis.yaml`。
   - 粘贴文本：直接作为 document 内容。
   创建 `_ingest/` 证据结构。
2. 读取 `_ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
3. 以 `_ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 context/ evidence 台账。
4. 将 PRD 拆成独立业务 requirement。
4. 按以下信号匹配每个 requirement（**必须优先使用 reference 路由表**）：
   - **reference 路由匹配**（优先级最高）：将 PRD 关键词与 `04-routing-playbooks.yaml` 的 `prd_keywords` 匹配，确定 target_surfaces 和 playbook_ref。
   - **reference 术语匹配**：将 PRD 表述与 `05-domain.yaml` 的 terms/synonyms 对齐。
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
5. 产出 `context/requirement-ir.yaml`。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
- PRD evidence 优先映射 `_ingest/evidence-map.yaml` 的 block/table/image 定位。
- 图片、截图、流程图通过 Claude Read 工具（原生多模态）直接查看分析。分析结果写入 `media-analysis.yaml`。
- 图片中提取的信息置信度为 `medium`（AI 视觉理解），关键结论仍需文本证据或人工确认才能升为 `high`。
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
