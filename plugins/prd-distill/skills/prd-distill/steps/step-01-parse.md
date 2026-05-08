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
- 如存在，读取 `_prd-tools/reference/04-routing-playbooks.yaml`、`_prd-tools/reference/05-domain.yaml`。
- v3.1 兼容：`_prd-tools/reference/05-routing.yaml`、`_prd-tools/reference/06-glossary.yaml`、`_prd-tools/reference/07-business-context.yaml`。
- 旧版兼容：`_prd-tools/reference/05-mapping.yaml`。

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
2. **生成 `_ingest/document-structure.json`**：逐段扫描 `document.md`，为每个段落、标题、表格、图片生成 block 条目（含 block_id、block_type、text_excerpt、locator）。
3. 读取 `_ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
4. 读取 `_prd-tools/reference/04-routing-playbooks.yaml` 的 `capability_inventory`（如存在），用于后续区分已有能力与需新增能力。
5. 以 `_ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 context/ evidence 台账。
6. **逐 block 提取需求**：遍历 `document-structure.json` 的每个 block，对每个内容块执行需求拆解。确保每个 block 都有 evidence_id 或被标记为 excluded。
7. 按以下信号匹配每个 requirement：
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
8. **消费 capability_inventory**：
   - PRD 提到的功能在 `generic_capabilities` 中 `status: verified` → 不需要新增 REQ，但在相关 REQ 的 `rules` 中注明"复用已有 XXX 能力"。
   - PRD 提到的功能在 `dimensioned_capabilities` 中但 `existing_entries` 不包含目标维度值 → 需要 ADD 类型的 REQ。
   - PRD 提到的功能在 `missing_capabilities` 中 → 标记 `confidence: low` 并加入 `open_questions`。
9. 产出 `context/requirement-ir.yaml`。
10. **覆盖验证**：
    a. 生成 `_ingest/evidence-map.yaml`，记录每个 block_id → evidence_id → requirement_ids 的映射。
    b. 计算 `coverage_ratio = mapped_blocks / total_blocks`。
    c. 更新 `_ingest/extraction-quality.yaml` 的 `coverage` 字段（total_blocks、mapped_blocks、excluded_blocks、unmapped_blocks、coverage_ratio）。
    d. `coverage_ratio < 0.8` 时 `extraction-quality.yaml` 的 `status` 必须为 `warn`，并在 `unmapped_blocks` 中列出未覆盖的 block_id。
    e. 未覆盖的 block 必须人工确认是遗漏还是可排除。

## 规则

- 每个 requirement 至少需要一个 PRD 或技术文档 evidence id。
- PRD evidence 优先映射 `_ingest/evidence-map.yaml` 的 block/table/image 定位。
- 图片、截图、流程图通过 Claude Read 工具（原生多模态）直接查看分析。分析结果写入 `media-analysis.yaml`。
- 图片中提取的信息置信度为 `medium`（AI 视觉理解），关键结论仍需文本证据或人工确认才能升为 `high`。
- IR 不写文件级实现细节。
- 使用 `ADD | MODIFY | DELETE | NO_CHANGE`。
- 业务规则、限制、互斥、权益、奖励发放、审计、rollout 假设都必须显式写出。
- 未知项进入 `open_questions`，不要隐藏不确定性。

## Self-Check（生成后必须逐项验证）
- [ ] document-structure.json 的每个 block 都有 block_id 和 block_type
- [ ] evidence-map.yaml 覆盖了 document-structure.json 中的所有 block_id
- [ ] coverage_ratio = mapped_blocks / total_blocks，计算正确
- [ ] coverage_ratio < 0.8 时 extraction-quality.yaml 的 status 为 warn
- [ ] 每个 REQ 至少有一个 PRD evidence（EV-ID）
- [ ] capability_inventory 中的已有能力在 REQ 的 rules 中标注了"复用已有"
- [ ] open_questions 中没有隐藏的不确定性

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
