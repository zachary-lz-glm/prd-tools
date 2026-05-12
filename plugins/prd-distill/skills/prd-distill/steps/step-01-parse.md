<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>0, 1, 1.5-afprd, 1.5-quality, 2</current_step>
  <allowed_inputs>PRD file (.md/.txt/.docx), _prd-tools/reference/ (if exists), references/layer-adapters.md</allowed_inputs>
  <must_not_read_by_default>source code (beyond reference routing), report.md, plan.md</must_not_read_by_default>
  <must_not_produce>context/layer-impact.yaml</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

> **修复循环规避规则**：
> 如果 gate 连续 2 次报同一个 fail，**必须停下**检查：
> 1. workflow 模板教你写的字段名/格式 vs gate 检查的字段名/格式是否一致
> 2. 是 gate 错了还是产物错了？
> 3. 不要为了让 gate 过就编造/删除证据。

> **跨步骤交叉引用**：本文件声称覆盖 gate steps 0, 1, 1.5-afprd, 1.5-quality, 2，但正文仅详述 Step 0（PRD Ingestion）和 Step 2（Requirement IR）。Step 1（Evidence Ledger）和 Step 1.5（AI-friendly PRD）的完整指令见 workflow.md 对应步骤段落。
>
> 宁可让 gate 报 fail，也不要让产物偏离原文。

# 步骤 1：证据与 Requirement IR

## Pre-flight

支持 `.md`/`.txt`/`.docx` 文件或粘贴文本。

**docx 读取流程（零第三方依赖，Claude 原生多模态看图）：**

### docx 解压标准流程（硬约束）

优先使用 `ingest-docx.py` 脚本：

```bash
python3 .prd-tools/scripts/ingest-docx.py --input "<prd.docx>" --output _prd-tools/distill/<slug>
```

如果脚本不可用，fallback 到手动 Python zipfile：

```bash
python3 - <<'EOF'
import zipfile, re, shutil
from pathlib import Path

src = "<PRD_FILE>.docx"
dst = Path("_prd-tools/distill/<SLUG>/_ingest")
dst.mkdir(parents=True, exist_ok=True)
(dst / "media").mkdir(exist_ok=True)

with zipfile.ZipFile(src) as z:
    xml = z.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]*>", "", xml)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    (dst / "document.md").write_text(text, encoding="utf-8")
    for name in z.namelist():
        if name.startswith("word/media/"):
            with z.open(name) as f:
                (dst / "media" / Path(name).name).write_bytes(f.read())
EOF
```

**不要用 `unzip -d`**——macOS 下解压出来的文件默认 mode 是 700，需要额外 chmod，易踩 permission denied。

- docx 本质是 zip 包，`word/document.xml` 包含正文，`word/media/` 包含嵌入图片。
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

### 团队公共 reference 消费（可选）

如果当前仓 `_prd-tools/reference/project-profile.yaml` 的 `team_reference.upstream_local_path` 存在：

1. Read `<upstream_local_path>/reference/05-domain.yaml` 作为全团队业务术语
2. Read `<upstream_local_path>/reference/03-contracts.yaml` 获取跨仓契约基线
3. Read `<upstream_local_path>/reference/04-routing-playbooks.yaml` 的跨仓 playbook

这些信息在 report/plan 中允许高于本仓 reference 的权威性——它们是"全团队已 checked_by 的共识"。

## 执行

1. 读取文件或接受粘贴文本：
   - `.md`/`.txt`：直接读取，保留原文格式。
   - `.docx`：使用 Pre-flight 中的 Python zipfile 标准流程一次性提取文本和图片。
     a. 运行 Python zipfile 脚本提取 `document.md` + `media/*`。
     b. 解析 XML 中的 `<w:drawing>` / `<w:pict>` 标签定位图片插入位置，在文本中插入 `![image-N](media/imageN.png)` 占位标记。
     c. 用 Read 工具逐个查看 `_ingest/media/` 下的图片，理解内容（UI 截图、流程图、数据图表），将分析结果写入 `_ingest/media-analysis.yaml`。
   - 粘贴文本：直接作为 document 内容。
   创建 `_ingest/` 证据结构。
2. 读取 `_ingest/extraction-quality.yaml`；`status: block` 时暂停，`status: warn` 时继续但必须暴露风险。
3. 以 `_ingest/document.md` 为主输入，结合 `evidence-map.yaml` 建立 context/ evidence 台账。
4. 将 PRD 拆成独立业务 requirement。
5. 按以下信号匹配每个 requirement（**必须优先使用 reference 路由表**）：
   - **reference 路由匹配**（优先级最高）：将 PRD 关键词与 `04-routing-playbooks.yaml` 的 `prd_keywords` 匹配，确定 target_surfaces 和 playbook_ref。
   - **reference 术语匹配**：将 PRD 表述与 `05-domain.yaml` 的 terms/synonyms 对齐。
   - routing 关键词
   - glossary 同义词
   - 结构信号
   - playbook/golden sample 相似度
   - 低置信度兜底匹配
6. 产出 `context/requirement-ir.yaml`。

## 规则

- `context/evidence.yaml` 是**唯一权威 evidence 账本**。必须包含以下三类条目：
  1. 原始 PRD block（从 `_ingest/evidence-map.yaml` 全量复制 `EV-BG-*`, `EV-CFG-*`, `EV-VIS-*` 等）
  2. Ingestion 证据（`EV-INGEST-*`：文本提取、图片分析）
  3. Reference 消费证据（`EV-REF-*`：消费 `_prd-tools/reference/*.yaml` 的摘要）
- `_ingest/evidence-map.yaml` 是 ingestion 阶段的原始产物，仅用于 step-0 输出验证，**不得被 requirement-ir.yaml / layer-impact.yaml / contract-delta.yaml 引用**。
- evidence.yaml 字段名硬约束：顶层键用 `items:`（不是 `entries:`），每条用 `kind:`（不是 `type:`），定位用 `locator:`（不是 `section:`），摘要用 `summary:`（不是 `desc:`）。
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
    evidence:
      summary: ""
      source_blocks:
        - block_id: "document.md:L10-16"
          type: "text"
      source_block_ids: ["B-001"]
      evidence_ids: ["EV-001"]
    confidence: "medium"
open_questions: []
```

## ai-friendly-prd.md 生成硬规则

### 13 段必须用英文标准名

ai-friendly-prd.md 的 13 个 `##` 段必须使用以下英文标题，**顺序固定，不得翻译，不得合并**：

1. Overview
2. Problem Statement
3. Target Users
4. Goals & Success Metrics
5. User Stories
6. Functional Requirements
7. Non-Functional Requirements
8. Technical Considerations
9. UI/UX Requirements
10. Out of Scope
11. Timeline & Milestones
12. Risks & Mitigations
13. Open Questions

### 每个 REQ-XXX 必须是独立 `### REQ-XXX` 三级标题锚点

在 Functional / Non-Functional / Technical / UI/UX / Open Questions 这 5 段内，每条需求必须形如：

```markdown
### REQ-CFG-001

**Source**: explicit
**Priority**: P0
...
```

标题**只放** `### REQ-XXX`，描述性文字放正文。**不得**写成 `### FR-2: 配置页面基础信息（REQ-ID: CFG-001）` 这种复合标题。

## IR ↔ AI-friendly PRD 编号一致性（硬约束）

生成 IR 前后，必须跑以下两条自检：

1. **每条 IR 的 `ai_prd_req_id` 必须在 `spec/ai-friendly-prd.md` 里有独立 `### REQ-XXX` 三级标题能命中**。未命中 → 当前 IR 生成失败，不得提交。
   - verify: `grep -c "ai_prd_req_id" context/requirement-ir.yaml`
   - expect: 数量与 requirements 条目数一致
2. **ai-friendly-prd.md 里每个 `REQ-xxx` heading 必须在 IR 列表里至少出现一次**（哪怕 `type: NO_CHANGE`）。缺失 → 补一条 IR 占位，type=NO_CHANGE，summary 写 "no BFF-layer change, reviewed"。
   - verify: `grep -oE 'REQ-[0-9]+' spec/ai-friendly-prd.md | sort -u | while read rid; do grep -q "$rid" context/requirement-ir.yaml || echo "MISSING: $rid"; done`
   - expect: 无输出（所有 REQ-ID 均已覆盖）
