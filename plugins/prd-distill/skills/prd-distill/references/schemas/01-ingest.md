# _ingest/

`_ingest/` 解决"PRD 到底被 AI 读成了什么"的问题。它不是需求结论层，只负责保真读取、定位、图片/表格风险暴露。`.md`/`.txt` 直接读取，`.docx` 用 `unzip -p <file> word/document.xml | sed 's/<[^>]*>//g'` 提取纯文本后写入 `document.md`。

| 文件 | 用途 | 边界 |
|---|---|---|
| `source-manifest.yaml` | 原始文件路径、格式、大小、hash、生成时间、读取方式 | 不写需求摘要或实现判断 |
| `document.md` | 转换后的可读 markdown，作为 Requirement IR 的主输入 | 不补充 PRD 没写的信息 |
| `document-structure.json` | PRD 结构块清单（段落、标题、表格、图片），含 block_id 和定位。用于后续覆盖验证，确保没有 block 被遗漏 | 不写业务语义结论 |
| `evidence-map.yaml` | PRD block → evidence_id 映射，记录每个 block 是否被需求提取覆盖 | 不放源码、diff、reference 证据 |
| `media/` | 抽出的图片、截图、流程图原文件（docx 提取时自动抽取） | 不修改图片内容 |
| `media-analysis.yaml` | 图片分析状态和摘要；Claude 用 Read 工具（原生多模态）直接查看图片后填写。类型：`ui_screenshot | flowchart | data_chart | table_image | decoration`。每条包含：文件名、类型、关键信息摘要、置信度 | 不确认的图片内容只能产生低置信度问题 |
| `tables/` | 单独抽出的表格 markdown | 不修复原表格，只保留转换结果 |
| `extraction-quality.yaml` | 读取质量门禁：`pass | warn | block`、统计、风险 | 不写开发计划 |
| `conversion-warnings.md` | 给人看的转换风险 | 不替代 report.md §12 |

`extraction-quality.yaml` 示例：

```yaml
schema_version: "1.0"
status: "pass | warn | block"
stats:
  paragraphs: 0
  tables: 0
  media: 0
coverage:
  total_blocks: 0
  mapped_blocks: 0
  excluded_blocks: 0
  unmapped_blocks: []
  coverage_ratio: 0.0
quality_gates: []
warnings: []
rules:
  - "Images are analyzed by Claude Read (native multimodal). AI-interpreted content is medium confidence by default."
```

`document-structure.json` schema：

```json
{
  "schema_version": "1.0",
  "blocks": [
    {
      "block_id": "",
      "block_type": "heading | paragraph | table | media | code_block | list",
      "level": 0,
      "text_excerpt": "",
      "heading": "",
      "row_count": 0,
      "columns": [],
      "media_ref": "",
      "context": "",
      "locator": { "line_start": 0, "line_end": 0 }
    }
  ],
  "exclusion_types": ["toc", "header_footer", "decoration", "revision_history"]
}
```

`evidence-map.yaml` schema：

```yaml
schema_version: "1.0"
blocks:
  - block_id: ""
    evidence_id: ""
    excluded: false
    exclude_reason: ""
    requirement_ids: []
    confidence: "high | medium | low"
```

覆盖验证规则：

- `document-structure.json` 的每个 `block` 必须在 `evidence-map.yaml` 中有对应条目（`evidence_id` 或 `excluded: true`）。
- `excluded: true` 的 block 必须填写 `exclude_reason`，有效值为 `exclusion_types` 中的类型或 `"merged_into"` + 被合并的 block_id。
- `unmapped_blocks` 列出所有没有 evidence 也没有 excluded 标记的 block_id。
- `coverage_ratio` = `mapped_blocks / total_blocks`。低于 0.8 时 `extraction-quality.yaml` 的 `status` 必须为 `warn` 或更低。

`media-analysis.yaml` schema：

```yaml
schema_version: "1.0"
media:
  - file: ""
    type: "ui_screenshot | flowchart | data_chart | table_image | decoration"
    summary: ""
    confidence: "medium"
```

质量规则：

- `block`：暂停蒸馏，要求用户提供 markdown/text。
- `warn`：允许继续，但必须在 `report.md` §12 中暴露风险。
- Claude 看图提取的信息置信度为 `medium`（AI 视觉理解），关键结论仍需文本证据或人工确认才能升为 `high`。
