<workflow_state>
  <workflow>prd-distill</workflow>
  <current_step>1, 2, 3</current_step>
  <allowed_inputs>PRD file (.md/.txt/.docx), _prd-tools/reference/ (if exists), references/layer-adapters.md</allowed_inputs>
  <must_not_read_by_default>source code (beyond reference routing), report.md, plan.md</must_not_read_by_default>
  <must_not_produce>context/layer-impact.yaml</must_not_produce>
</workflow_state>

## MUST NOT

- MUST verify ALL prerequisite files exist and are non-empty before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if any prerequisite file is missing

> **一致性检查规则**：
> 如果连续 2 次产出相同错误，**必须停下**检查：
> 1. workflow 模板要求的字段名/格式 vs 实际产出的字段名/格式是否一致
> 2. 是模板错了还是产物错了？
> 3. 不要为了通过检查就编造/删除证据。

> **范围声明**：本文件覆盖 spec 阶段 3 个 step（1 / 2 / 3）的共享约束和入口指引。每个 step 的完整指令以 workflow.md 对应段落为 SSOT，本文件只给跨步骤的入口规则和检查。
>
> 宁可让 gate 报 fail，也不要让产物偏离原文。

# spec 阶段入口（Step 1 → 2 → 3）

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

### md/txt 图片扫描流程（远程 URL 图片）

`.md`/`.txt` 文件中的远程图片 URL（如 S3 签名链接）包含关键 UI 需求，必须走以下子流程：

**触发条件**：`document.md` 中包含 `![...](https?://...)` 模式。

**子步骤**：

a. **扫描**：用 `grep -n '!\[.*\](https\?://)' _ingest/document.md` 扫描所有远程图片 URL。跳过已指向本地 `media/` 的占位符。

b. **下载**：对每个远程 URL，用 `curl -sL --max-time 30 -o "_ingest/media/image-N.ext" "<url>"` 下载到 `_ingest/media/`。文件编号从 1 开始连续递增，扩展名从 URL 或 Content-Type 推断（默认 `.png`）。如果下载失败（超时、403、404），记录到 `conversion-warnings.md`，不阻塞流程。

c. **重写引用**：将 `_ingest/document.md` 中对应的 `![alt](http...)` 替换为 `![image-N](media/image-N.ext)`，与 docx 管线输出格式一致。

d. **分析**：用 Read 工具逐个查看 `_ingest/media/` 下的图片，理解内容（UI 截图、流程图、数据图表），将分析结果写入 `_ingest/media-analysis.yaml`。与 docx 管线使用相同 schema。

e. **质量记录**：更新 `extraction-quality.yaml` 的 `stats.media` 计数。如有下载失败，标记 `status: warn`。

**规则**：
- 下载超时设为 30 秒（`curl --max-time 30`）。S3 签名 URL 有时效性，首次处理时必须下载。
- 如果所有图片均下载失败，`extraction-quality.yaml` 标记 `image_extraction_status: download_failed`，`status: warn`。
- 图片中提取的信息置信度为 `medium`（与 docx 管线一致），关键结论仍需文本证据或人工确认才能升为 `high`。

## 目标

将 PRD 和可选技术文档解析为：

- `_prd-tools/distill/<slug>/_ingest/*`
- `_prd-tools/distill/<slug>/context/evidence.yaml`
- `_prd-tools/distill/<slug>/context/requirement-ir.yaml`

## 输入

- 来自 `.md/.txt` 或粘贴内容的 PRD。
- 可选上下游接口文档（强烈建议传入）。传入后写入 `_ingest/` 并在 evidence-map.yaml 中注册。作为 Contract Delta 的直接证据源，证据优先级高于 PRD 推断。
- `_prd-tools/reference/`（**必须消费**，如存在）：
  - `04-routing-playbooks.yaml`：提取路由表，用于 Requirement IR 的 PRD 关键词匹配。
  - `05-domain.yaml`：提取领域术语，用于 Requirement IR 的 glossary 同义词匹配。
  - v3.1 兼容：`05-routing.yaml`、`06-glossary.yaml`、`07-business-context.yaml`。
  - 旧版兼容：`05-mapping.yaml`。

### 团队公共 reference 消费（可选）

如果当前仓 `_prd-tools/reference/project-profile.yaml` 的 `team_reference.upstream_local_path` 存在：

1. Read `<upstream_local_path>/reference/05-domain.yaml` 作为全团队业务术语
2. Read `<upstream_local_path>/reference/03-contracts.yaml` 获取跨仓契约基线
3. Read `<upstream_local_path>/reference/04-routing-playbooks.yaml` 的跨仓 playbook

这些信息在 report/plan 中允许高于本仓 reference 的权威性——它们是"全团队已 checked_by 的共识"。

**团队模式**（`layer: team-common`）：额外读取各仓 reference 副本作为需求匹配输入：
- 各仓 `references/{repo}/01-codebase.yaml`（模块、枚举、实体）
- 各仓 `references/{repo}/03-contracts.yaml`（producer/consumer 契约）
- 各仓 `references/{repo}/05-domain.yaml`（术语和决策）

## 执行

1. 读取文件或接受粘贴文本：
   - `.md`/`.txt`：读取文件内容写入 `_ingest/document.md`。然后执行「md/txt 图片扫描流程」（见下方）：扫描远程图片 URL → 下载到 `_ingest/media/` → 重写本地引用 → 分析图片 → 写入 `media-analysis.yaml`。无远程图片时跳过图片流程。
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

## IR 编号一致性

生成 IR 前后，必须跑自检：

1. **每条 IR 必须有唯一的 `id`**（REQ-XXX 格式），且 `evidence.source_blocks` 非空。
2. **PRD 中提到的每个需求都应在 IR 中有对应条目**（哪怕 `type: NO_CHANGE`）。
