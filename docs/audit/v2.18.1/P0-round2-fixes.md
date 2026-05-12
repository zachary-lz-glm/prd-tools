# P0-round2 修复清单（基于实际 /prd-distill 运行日志）

> **这批 FIX 来自 2026-05-12 用户手动跑 /prd-distill 暴露的问题**。与 P0-round1 合并后的 6 个 P0 不同，这批 FIX 反映的是**工作流契约与 gate 契约的断层**——AI 按 workflow.md 产出的产物被 gate 拒绝，AI 回去改证据对齐 gate，改到违反原文，陷入"修复循环"，最后被用户手动终止。
>
> **执行前必读**：
> 1. 部分问题可能 P0-round1/P1 已经修复，开工前先跑 `python3 tools/selfcheck/run.py --all` 看现状
> 2. 每个 FIX 标了 `relates_to`，指向 round1 的相关 FIX（如有）
> 3. 每个 FIX 带 `verify`，改完立即跑
> 4. commit prefix: `fix(audit-p0r2): [P0R2-x] ...`

## 症状与根因总览

| 症状（用户实跑日志看到的） | 真实根因 | 落点 FIX |
|---|---|---|
| AI 生成 13 章节用 `§1 Overview（需求概述）` 格式，gate 查 `Overview`，fail | workflow 模板和 gate 正则两份契约 | P0R2-1 |
| `prd-quality-report.yaml` 用 `overall_score:`，gate 查 `^score:`，fail | 同上；字段名两份 | P0R2-2 |
| `evidence-map.yaml` 用 `evidence_map:` 作顶层 key，gate 查 `blocks:`，ratio=0 | 同上；顶层 key 两份 | P0R2-3 |
| `media-analysis.yaml` 用 `images:`，gate 查 `media` 或 `items`，全 miss | 同上；顶层 key 两份 | P0R2-4 |
| `requirement-ir.yaml` 的 `evidence:` 写成字符串，contract 要 object with `source_blocks / source_block_ids` | contract 没告诉 AI 真实结构 | P0R2-5 |
| `contract-delta.yaml` 条目缺 `meta / requirement_id / layer`，artifact-contract fail | contract 要求 ≠ workflow 模板 | P0R2-6 |
| `docx` 解压后 `permission denied`，AI 绕了 4 次路才拿到文本 | workflow 没说 docx 的正确解压方式，AI 踩 unzip 系统路径/权限坑 | P0R2-7 |
| `context-pack.py` 参数是 `--distill/--index/--out`，workflow 用 `--distill-dir/--repo-root` | 脚本 CLI 与 workflow 文档不一致 | P0R2-8 |
| `final-quality-gate.py` 参数是 `--distill`，workflow 用 `--distill-dir` | 同上 | P0R2-9 |
| Step 0 workflow 说会自动生成 `document-structure.json / evidence-map.yaml`，实际 AI 忘记生成，直到 Step 2 gate 才报错 | Step 0 产出清单是"建议"不是"硬约束"，导致迟到失败 | P0R2-10 |
| AI 多次绕过失败跑 `--allow-rerun` 改证据对齐 gate；一改就违反原文 | 失败时没有"不要改证据，改 gate/contract/模板"的提示 | P0R2-11 |
| `coverage-gate` 把 `B-000`（修订历史表）也当成必须覆盖，fail 18 blocks | `exclusion_types` 机制存在但 workflow 没告诉 AI 填 | P0R2-12 |

## 系统性根因（写给 AI 读的总结）

**workflow 契约（给 AI 生成）和 gate 契约（给 AI 校验）是两套独立写出来的规范，没有单一权威源，所以字段名/正则/章节名/顶层 key 必然漂移。**

五个表现：
1. `spec/ai-friendly-prd.md` 的章节标题格式：workflow 模板用 `## §N Name（中文）`，gate 正则 `^##\s+(?:\d+\.?\s+)?{english_name}`，两份不交集
2. `prd-quality-report.yaml` 字段：workflow 用 `overall_score`，gate 查 `score`
3. `evidence-map.yaml` 顶层 key：workflow 示例用 `evidence_map:`，gate 读 `blocks:`
4. `media-analysis.yaml` 顶层 key：workflow 示例用 `images:`，gate 读 `media` 或 `items`
5. `requirement-ir.yaml` 的 `evidence:`：workflow 模板里是字符串，contract 要 object

---

## P0R2-1 — AI-friendly PRD 章节标题格式与 gate 正则统一

### 问题

Workflow 模板（`steps/step-01-parse.md` 或对应 step）教 AI 写：
```markdown
## §1 Overview（需求概述）
```

但 `scripts/distill-quality-gate.py:51-127` 的 `AFPRD_SECTIONS` 列的是纯英文（`Overview`, `Problem Statement`, ...），正则 `^##\s+(?:\d+\.?\s+)?{english_name}` 匹配 `## 1. Overview` 或 `## Overview`，**完全不匹配 `§1 Overview`**。

实际运行日志里，AI 先按 workflow 写出 13 个 `§N ...` 标题，gate 说"missing all 13 sections"，AI 再手工改成 `N. Name（中文副标题）` 才过。

### 修复

**以 gate 的英文 SECTION 列表为准**（它是机器校验方）。把 workflow 模板改成产出 `## N. EnglishName（中文副标题）` 格式。

1. 读 `scripts/distill-quality-gate.py:51-69` 拿到完整 `AFPRD_SECTIONS` 列表（13 个英文名，顺序敏感）。
2. 找 AI-friendly PRD 生成 step（`grep -rl "ai-friendly-prd\|AI-friendly PRD" plugins/prd-distill/skills/prd-distill/steps/`），在模板章节把 `## §1 Overview（xxx）` 改为 `## 1. Overview（xxx）`，13 个都改。
3. 同步更新 `plugins/prd-distill/skills/prd-distill/references/output-contracts.md` 里 `spec/ai-friendly-prd.md` 相关示例（如果有）。
4. 在生成 step 的 Self-Check 加一条 `[M]` 断言：
   ```
   - [M] spec/ai-friendly-prd.md 每个章节标题格式为 `## N. EnglishName` 或 `## N. EnglishName（中文）`，N 从 1 到 13
     verify: `python3 -c "import re; m={'Overview','Problem Statement','Target Users','Goals & Success Metrics','User Stories','Functional Requirements','Non-Functional Requirements','Technical Considerations','UI/UX Requirements','Out of Scope','Timeline & Milestones','Risks & Mitigations','Open Questions'}; t=open('spec/ai-friendly-prd.md').read(); found={x for x in m if re.search(rf'^##\s+(?:\d+\.?\s+)?{re.escape(x)}', t, re.M)}; assert found==m, sorted(m-found)"`
     expect: exit 0
   ```

### relates_to
P1-1（智能引号）修过 workflow.md yaml 块，本 FIX 是独立的章节标题问题。

### verify
```bash
cd /Users/didi/work/prd-tools
rg -n "## §" plugins/prd-distill/skills/prd-distill/steps/ plugins/prd-distill/skills/prd-distill/workflow.md | grep -iE "overview|requirements" && echo "STILL HAS §" && exit 1 || echo "OK: no § prefix in afprd templates"
```

### commit
```
fix(audit-p0r2): [P0R2-1] ai-friendly-prd section format matches gate regex

Workflow template taught AI to use `## §1 Overview（需求概述）` headings,
but distill-quality-gate AFPRD_SECTIONS regex only matches
`## Overview` / `## 1. Overview`. Real runs missed all 13 sections,
forcing manual retrofit. Changed templates to `## N. EnglishName（中文）`
and added a machine-verifiable self-check.
```

---

## P0R2-2 — `prd-quality-report.yaml` 字段名 `overall_score` vs `score`

### 问题

`scripts/distill-quality-gate.py:156`：
```python
has_score = bool(re.search(r'^score:\s*\d+', text, re.M))
```

但 workflow 教 AI 写 `overall_score: 72`（见 P1-10 刚引入的评分公式也是这么写的）。gate 只认 `score:` 开头的行 → 永远 fail，AI 手工加一行 `score: 72` 兜底。

### 修复

**两侧同改**，以 workflow/P1-10 的 `overall_score` 为准（更语义清晰）：

1. 改 gate 正则让它接受两种：
   ```python
   # scripts/distill-quality-gate.py:156
   has_score = bool(re.search(r'^(overall_score|score):\s*\d+', text, re.M))
   ```
2. 在 `output-contracts.md` 的 `prd-quality-report.yaml` schema 段落加明确字段：
   ```
   - `overall_score` (int, 0-100): 权威字段，按 P1-10 公式计算。
   - `score` (int, 0-100, 已废弃): 旧字段名，新产物不要写，gate 仍接受但不推荐。
   ```
3. 同步 `references/contracts/prd-quality-report.contract.yaml`（如存在）把 required 字段定为 `overall_score`，`score` 不要求。

### relates_to
P1-10（引入 overall_score 公式）

### verify
```bash
rg -n "r'\^score:|has_score" scripts/distill-quality-gate.py
# 期望：正则含 overall_score
python3 -c "import re; assert re.search(r'\(overall_score\|score\)', open('scripts/distill-quality-gate.py').read())" && echo "P0R2-2 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-2] gate accepts overall_score as score alias

quality-gate only matched ^score:\s*\d+ but workflow/P1-10 use
overall_score:. Every fresh run failed has_score check until AI
manually added a duplicate `score:` line. Gate now accepts both,
overall_score is the canonical name going forward.
```

---

## P0R2-3 — `evidence-map.yaml` 顶层 key：`evidence_map` vs `blocks`

### 问题

`scripts/prd-coverage-gate.py:50`：
```python
em_blocks = em.get("blocks", [])
```

但 workflow 示例让 AI 写：
```yaml
evidence_map:
  - block_id: "B-001"
    ...
```

顶层 key 对不上，`em_blocks = []`，**所有 block 都 missing**，ratio=0.0。

用户实际跑时 AI 最后把顶层 key 从 `evidence_map:` 改成 `blocks:` 才过 gate——但改完 workflow 模板依然教下一个 AI 写 `evidence_map:`。

### 修复

**统一顶层 key 为 `blocks`**（短、语义清）：

1. `scripts/prd-coverage-gate.py:50` 不改。
2. 改 workflow 模板 + output-contracts：
   - `grep -rn "evidence_map:" plugins/prd-distill/skills/prd-distill/ | grep -v "evidence-map.yaml\|evidence_map_ref"` 找所有写成顶层 `evidence_map:` 的示例（注意排除路径引用）
   - 把示例改为顶层 `blocks:`：
     ```yaml
     meta:
       generated_at: ...
       source: "_ingest/document.md"
     blocks:
       - block_id: "B-001"
         lines: "10-16"
         ...
     ```
3. 在 `output-contracts.md` 的 `_ingest/evidence-map.yaml` 段落明确：
   ```
   顶层字段：
   - `meta`: 元数据
   - `blocks`: 数组，每个元素含 `block_id / lines / content_summary / req_ids`
   ```

### verify
```bash
cd /Users/didi/work/prd-tools
# workflow/template 里不应再有顶层 evidence_map:
rg -n "^evidence_map:" plugins/prd-distill/skills/prd-distill/ | grep -v "\.py:" && echo "STILL HAS" && exit 1 || echo "P0R2-3 OK"
# output-contracts 明确了 blocks 作为顶层
rg -n "^\s*blocks:" plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```

### commit
```
fix(audit-p0r2): [P0R2-3] evidence-map.yaml top-level key unified as `blocks`

workflow templates used `evidence_map:` as top-level key, but
prd-coverage-gate reads `em.get("blocks", [])`. Every run produced
coverage_ratio=0.0 until AI manually renamed the key. Unified around
`blocks:` and updated all templates/examples.
```

---

## P0R2-4 — `media-analysis.yaml` 顶层 key：`images` vs `media`

### 问题

`scripts/prd-coverage-gate.py:122`：
```python
for item in analysis.get("media", analysis.get("items", [])):
```

接受 `media` 或 `items`。但 workflow 模板示例让 AI 写：
```yaml
images:
  - id: "IMG-001"
    file: "media/image1.png"
```

gate miss 全部媒体，"14 files without analysis"。

### 修复

**统一顶层 key 为 `media`**（与 `_ingest/media/` 目录名对应）：

1. `scripts/prd-coverage-gate.py:122` 可以保留对 `items` 的兼容（历史产物），但 **首选读 `media`**：
   ```python
   for item in analysis.get("media") or analysis.get("items") or analysis.get("images") or []:
   ```
2. 改 workflow 模板里 `media-analysis.yaml` 示例顶层 key 从 `images:` 改为 `media:`。
3. `output-contracts.md` 的对应段落明确 `media:` 是权威字段名，`images` / `items` 仅为兼容。

### verify
```bash
rg -n "^images:" plugins/prd-distill/skills/prd-distill/ | grep -v "\.py:" && echo "STILL HAS images: top-level" && exit 1 || echo "P0R2-4 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-4] media-analysis.yaml top-level key unified as `media`

workflow templates used `images:`, gate read `media`/`items`. All media
coverage checks failed until AI renamed. Standardized on `media:`,
kept images/items as legacy compat.
```

---

## P0R2-5 — `requirement-ir.yaml` 的 `evidence:` 字段结构

### 问题

Workflow 模板早期版本教 AI 写：
```yaml
- id: IR-001
  evidence: "document.md:L40-42"
```

但 `references/contracts/requirement-ir.contract.yaml` 要求：
```yaml
required:
  - evidence.source_blocks 或 evidence.source_block_ids (任一非空)
```

AI 第一次产出按字符串写，contract fail，被迫回去改成：
```yaml
- id: IR-001
  evidence:
    source_blocks: ["document.md:L40-42"]
    source_block_ids: ["B-005"]
```

### 修复

1. 所有 step 模板、workflow 示例里的 `evidence:` 示例统一为 object 结构。
2. `output-contracts.md` 的 `requirement-ir.yaml` 段落明确 evidence 必须是 object：
   ```yaml
   evidence:
     source_blocks: ["<file>:Lx-y", ...]  # 原文定位
     source_block_ids: ["B-xxx", ...]     # document-structure.json 的 block_id
   ```
3. 在 IR 生成 step 的 Self-Check 加 `[M]`：
   ```
   - [M] 每条 IR 的 evidence 字段必须是 mapping，且 source_blocks 或 source_block_ids 至少一个非空
     verify: python3 -c "import yaml; ir=yaml.safe_load(open('context/requirement-ir.yaml')); [assert isinstance(r.get('evidence'), dict) and (r['evidence'].get('source_blocks') or r['evidence'].get('source_block_ids')) for r in ir.get('requirements', [])]"
   ```

### relates_to
P1-3（source_blocks / source_block_ids 语义对齐），本 FIX 是它的模板落地。

### verify
```bash
cd /Users/didi/work/prd-tools
# workflow/step 示例里 evidence 不应再是纯字符串
rg -n "^\s+evidence:\s+\"" plugins/prd-distill/skills/prd-distill/steps/ plugins/prd-distill/skills/prd-distill/workflow.md && echo "STILL HAS scalar evidence" && exit 1 || echo "P0R2-5 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-5] IR evidence field unified as object with source_blocks/source_block_ids

Templates showed `evidence: "document.md:L40-42"` scalar; contract
required `evidence.source_blocks` or `evidence.source_block_ids`
mapping. Real runs produced scalar, failed contract, had to be
manually refactored. Templates now consistently show the mapping form.
```

---

## P0R2-6 — `contract-delta.yaml` 条目缺 `meta / requirement_id / layer`

### 问题

P0-4 已经把 contract 的 `required` 字段改对齐真实产物（`id / producer / change_type / alignment_status`）。**但用户这次实际跑时，`distill-quality-gate.py` 的 artifact-contract 检查仍然报 contract-delta 缺字段**，因为：

- P0-4 改的是 `required_top_level` 一层，但 `distill-quality-gate.py` 另有一条 `_check_artifact_contracts` 调用 `validate-artifact.py`，实际验收时**产物缺 `meta` / 条目缺 `requirement_id / layer`** 依然被报错。
- 用户为此手动给每个 delta 加了 `layer: bff` + `requirement_id: IR-xxx`，以及顶层 `meta: {primary_source, ai_prd_source, ...}`。

### 修复

**两选一，推荐 B**：

**方案 A**：让 contract 宽松一点，接受不含 `meta` 和条目不含 `requirement_id/layer` 的产物。

**方案 B（推荐）**：让 workflow 模板教 AI **一次性写全**：
1. 改 `references/contracts/contract-delta.contract.yaml`，在 `rules` 里增加：
   ```yaml
   rules:
     - id: "contract_has_identity"
       each: "deltas"
       required:
         - id
         - producer
         - change_type
         - alignment_status
         - requirement_id   # 新增
         - layer            # 新增
   required_top_level:
     - meta               # 新增
     - schema_version
     - deltas
   ```
2. 改 workflow.md Step 4（contract-delta 生成）模板：
   ```yaml
   schema_version: "1.0"
   meta:
     primary_source: "_ingest/document.md"
     ai_prd_source: "spec/ai-friendly-prd.md"
     requirement_ir_ref: "context/requirement-ir.yaml"
   deltas:
     - id: CD-001
       name: "..."
       change_type: NEW
       layer: bff          # 必填
       requirement_id: IR-001  # 必填，关联 requirement-ir.yaml
       producer: bff
       ...
   ```
3. 对应 output-contracts.md 同步字段。

### relates_to
P0-4（contract-delta schema 对齐）。本 FIX 是它的第二层补齐。

### verify
```bash
python3 -c "import yaml; c=yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml')); r=c['rules'][0]['required']; assert 'requirement_id' in r and 'layer' in r, r; assert 'meta' in c.get('required_top_level', []), c"
echo "P0R2-6 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-6] contract-delta requires meta + requirement_id + layer

P0-4 aligned required_top_level, but validate-artifact still failed
on deltas missing requirement_id/layer and top-level missing meta.
AI manually backfilled 11 deltas + meta block. Templates now teach
these fields upfront and contract rules enforce them.
```

---

## P0R2-7 — docx 解压 permission denied 的标准路径

### 问题

实际跑时 AI 做了 4 次尝试：
1. `unzip -o ... -d docx-extracted/` → 解压成功但 `cp` 源目录权限问题
2. 改 `unzip ... -d docx2/word/...` → `media/*` 路径不匹配
3. 直接 `unzip ... "media/*"` → 失败
4. 最后用 `python3 zipfile + xml strip` 才搞定

**根因**：workflow.md 里写 docx 用 `unzip -p <file> word/document.xml | sed 's/<[^>]*>//g'`，这个命令只提文本不提 media，AI 为了提 media 瞎试 `unzip -d`，踩权限 + 路径坑。

### 修复

在 `plugins/prd-distill/skills/prd-distill/steps/step-00-*.md` 或 workflow.md Step 0 的 "docx ingestion" 段落，给出**完整单步命令**：

```markdown
### docx 解压标准流程（硬约束）

使用 Python zipfile 一次性提文本 + 图片，避免 unzip 的权限/glob 坑：

\`\`\`bash
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
\`\`\`

**不要用 `unzip -d`**——macOS 下解压出来的文件默认 mode 是 700，需要额外 chmod，易踩 permission denied。
```

### verify
```bash
rg -n "python3.*zipfile|docx.*zipfile" plugins/prd-distill/skills/prd-distill/steps/ plugins/prd-distill/skills/prd-distill/workflow.md && echo "P0R2-7 OK" || { echo "Standard docx ingestion not present"; exit 1; }
```

### commit
```
fix(audit-p0r2): [P0R2-7] docx ingestion uses python zipfile standard path

workflow said `unzip -p ... word/document.xml`, which only extracts
text. To also extract media, AI tried 4 different unzip invocations,
all hit permission or glob errors on macOS. Standardized on a single
python3 zipfile block that extracts both text and media in one shot.
```

---

## P0R2-8 — `context-pack.py` CLI：workflow 用 `--distill-dir`，脚本是 `--distill`

### 问题

`scripts/context-pack.py:815-819`：
```python
ap.add_argument('--distill', required=True, ...)
ap.add_argument('--index', required=True, ...)
ap.add_argument('--out', required=True, ...)
```

但 workflow.md 示例：
```bash
python3 scripts/context-pack.py --distill-dir _prd-tools/distill/... --repo-root .
```

AI 照抄失败，尝试 3 次后读 --help 才发现真实参数是 `--distill / --index / --out`。

### 修复

**两侧都改，首选让脚本接受两种**（更兼容）：

1. `scripts/context-pack.py` 让 `--distill` 同时接受 `--distill-dir`：
   ```python
   ap.add_argument('--distill', '--distill-dir', dest='distill', required=True, ...)
   ```
2. 同时加 `--index` 的 default（从 `--distill` 自动推导 `<repo>/_prd-tools/reference/index`）和 `--out` 的 default（`<distill>/context/context-pack.md`），这样 workflow 可以只传 `--distill-dir` + `--repo-root`。
3. 改 workflow.md 的示例命令，与脚本真实 CLI 对齐（用 `--distill` 或 `--distill-dir` 都行）。

### verify
```bash
python3 scripts/context-pack.py --distill-dir /tmp/nonexistent 2>&1 | grep -q "unrecognized" && echo "FAIL: --distill-dir not accepted" && exit 1 || echo "P0R2-8 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-8] context-pack accepts --distill-dir alias + auto-derives --index/--out

workflow documented `--distill-dir --repo-root`, script only accepted
`--distill --index --out`. AI wasted 3 retries. Added alias and
sensible defaults so workflow's shorter invocation works.
```

---

## P0R2-9 — `final-quality-gate.py` CLI：`--distill` vs `--distill-dir`

### 问题
同 P0R2-8，`scripts/final-quality-gate.py:601` 要求 `--distill`，workflow 示例用 `--distill-dir`。

### 修复
同 P0R2-8 的方式：给 `--distill` 加 `--distill-dir` alias。

### verify
```bash
python3 scripts/final-quality-gate.py --distill-dir /tmp/nonexistent 2>&1 | grep -q "unrecognized" && exit 1 || echo "P0R2-9 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-9] final-quality-gate accepts --distill-dir alias
```

---

## P0R2-10 — Step 0 产出清单改成"硬约束"，防止迟到失败

### 问题

用户实跑日志里 Step 0 gate PASS 了，但实际 AI **只写了 `source-manifest.yaml` / `extraction-quality.yaml` / `document.md`**，漏掉 `document-structure.json` 和 `evidence-map.yaml`。直到 Step 2 gate 才报 missing，AI 回头补写，补的字段顶层 key 又错（详见 P0R2-3）。

**根因**：Step 0 的 prerequisites 只检查"前置步骤"，不检查 Step 0 自己该产出的文件。Step 0 结束时没有任何 gate 强制校验产出完整性。

### 修复

在 `scripts/distill-step-gate.py` 的 `STEP_TABLE["1"]` 里把 `document-structure.json` 和 `evidence-map.yaml` 从"Step 1 期望"前移到"Step 0 产出 = Step 1 的 prerequisites"：

```python
"1": {
    "label": "Step 1: Evidence Ledger",
    "prerequisites": [
        ("_ingest/document.md", "Step 0"),
        ("_ingest/document-structure.json", "Step 0"),   # 新增
        ("_ingest/evidence-map.yaml", "Step 0"),         # 新增
        ("_ingest/source-manifest.yaml", "Step 0"),      # 新增
    ],
    ...
}
```

**验证**：审计时已经在 `scripts/distill-step-gate.py:93-94` 看到这两条 prereq 似乎已存在（commit 834ceb5 "全盘修复一致性" 里做过），**GLM 做本 FIX 前先 grep 确认现状**，如果已在则只改 step-00 文件补一段"必须在 Step 0 结束前产出以下文件"的硬约束文字 + Self-Check `[M]` 断言。

### verify
```bash
python3 -c "src=open('scripts/distill-step-gate.py').read(); start=src.find('\"1\":'); end=src.find('}', start); s=src[start:end]; assert 'document-structure.json' in s and 'evidence-map.yaml' in s, s"
echo "P0R2-10 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-10] Step 0 outputs enforced as Step 1 prerequisites

Real run: AI skipped document-structure.json + evidence-map.yaml in
Step 0 (workflow mentioned them as "outputs" but gate didn't enforce).
Failure surfaced only at Step 2, forcing AI to backfill and mismatch
key names. Now Step 1 gate fails fast if Step 0 outputs are missing.
```

---

## P0R2-11 — Gate 失败消息必须说"不要改证据，改 gate/contract/模板"

### 问题

用户观察到 AI 陷入的**修复循环**：
> gate 说 "blocks not covered" → AI 回去给 evidence-map 加本不存在的 block → 违反原文 → gate 过 → 但产出内容错了 → 下一轮用户发现不对，手动终止

**根因**：gate 失败消息只说 "block X not covered in evidence-map"，没说这可能是 **gate 字段名错** / **workflow 模板错**，暗示 AI "去改 evidence-map"，引导方向错误。

### 修复

扩展 P1-9 引入的 `scripts/_gate_fixhint.py`：

1. 给每个失败原因加 **方向标签**：
   ```python
   FIX_HINTS = {
       "block_not_covered": {
           "hint": "Add real evidence for uncovered block to evidence-map.yaml. DO NOT invent blocks — if the count is suspicious (e.g. all blocks missing), likely cause is top-level key mismatch (evidence_map vs blocks), check scripts/prd-coverage-gate.py and workflow template.",
           "direction": "check_both",  # don't blindly edit artifact
       },
       "afprd_missing_all_13_sections": {
           "hint": "Section format mismatch. workflow template may use `## §N Name` but gate expects `## N. Name`. DO NOT rewrite the 13 sections — check template vs gate regex first.",
           "direction": "check_template",
       },
       ...
   }
   ```
2. 在 gate 失败输出里强制打印 `direction` 和完整 hint。
3. 在所有 step 文件的 Self-Check 顶部加一段**硬约束**：
   ```
   > **修复循环规避规则**：
   > 如果 gate 连续 2 次报同一个 fail，**必须停下**检查：
   > 1. workflow 模板教你写的字段名/格式 vs gate 检查的字段名/格式是否一致
   > 2. 是 gate 错了还是产物错了？
   > 3. 不要为了让 gate 过就编造/删除证据。
   >
   > 宁可让 gate 报 fail，也不要让产物偏离原文。
   ```

### verify
```bash
rg -q "修复循环规避" plugins/prd-distill/skills/prd-distill/steps/ && echo "P0R2-11 OK"
grep -q "direction" scripts/_gate_fixhint.py && echo "fixhint table updated"
```

### commit
```
fix(audit-p0r2): [P0R2-11] gate failures suggest checking template/gate, not just artifact

Real run showed AI entering a "fix loop": gate fails, AI edits
artifact to match gate, artifact now deviates from source. Now every
gate failure emits a `direction: check_template | check_gate |
check_both` hint and step files carry a hard rule: if the same gate
fails twice, stop and investigate template/gate mismatch — don't
fabricate evidence to satisfy gate.
```

---

## P0R2-12 — `coverage-gate` 让 AI 知道 `exclusion_types` 的存在

### 问题

`scripts/prd-coverage-gate.py:47-48` 支持 `exclusion_types`：
```python
ds_blocks = ds.get("blocks", [])
exclusion_types = set(ds.get("exclusion_types", []))
```

像 `修订历史表`（B-000）、目录、纯样式段落等，按理应该列进 `exclusion_types: [revision_history, toc]` 然后 gate 就会跳过。

**但 workflow 完全没告诉 AI 这个字段存在**。AI 产出的 `document-structure.json` 从不写 `exclusion_types`，导致 B-000 被要求覆盖，AI 只能硬给它编一条 evidence。

### 修复

1. 在 `output-contracts.md` 的 `_ingest/document-structure.json` 段落补上 `exclusion_types` 字段定义：
   ```
   {
     "meta": {...},
     "blocks": [...],
     "exclusion_types": ["revision_history", "toc", "page_break", "decoration"]
   }
   ```
2. 在 Step 0 生成 `document-structure.json` 的 step 文件加 Self-Check `[M]`：
   ```
   - [M] document-structure.json 含 exclusion_types 字段，默认至少包含 ['revision_history', 'toc'] 若原文存在这些 block 类型
   ```
3. 并提示 AI：`block_type` 只要出现在 `exclusion_types`，evidence-map 就不需要覆盖它。

### verify
```bash
rg -q "exclusion_types" plugins/prd-distill/skills/prd-distill/steps/ plugins/prd-distill/skills/prd-distill/references/output-contracts.md && echo "P0R2-12 OK"
```

### commit
```
fix(audit-p0r2): [P0R2-12] document-structure.json exclusion_types taught to AI

prd-coverage-gate supports `exclusion_types` to skip irrelevant blocks
(revision history, TOC, etc.), but no workflow doc mentioned this
field. AI always produced coverage-required blocks for revision
history table and had to fabricate evidence. Now step-00 templates
teach exclusion_types and coverage skips them naturally.
```

---

## 另外：selfcheck D4 check 脚本自身修复

### 问题
`tools/selfcheck/checks/D4_gate_mentions.py` 在当前仓库输出 16 个 "gate reference gap"，实际是**误报**：
- `plugins/prd-distill/SKILL.md` 期望提及 `reference-*-gate.py`（反之亦然）
- 两个 skill 本应只提自己的 gate

### 修复

改 `tools/selfcheck/checks/D4_gate_mentions.py`：**同 skill 内自闭合**——命令里提到的 gate 只要求该 skill 的 SKILL.md / workflow.md 提到"同前缀"的 gate。

```python
# tools/selfcheck/checks/D4_gate_mentions.py

SKILL_GATE_PREFIX = {
    "prd-distill": ("distill-",),
    "reference": ("reference-",),
}

def check(repo_root):
    issues = []
    for skill in sorted(repo_root.glob("plugins/*/skills/*/SKILL.md")):
        skill_name = skill.parent.name  # e.g. "prd-distill"
        allowed_prefixes = SKILL_GATE_PREFIX.get(skill_name, ())
        skill_dir = skill.parent
        plugin_dir = skill_dir.parent.parent
        workflow = skill_dir / "workflow.md"

        cmd_candidates = list(plugin_dir.glob("commands/*.md")) + \
                         list((plugin_dir / ".claude" / "commands").glob("*.md") if (plugin_dir / ".claude" / "commands").exists() else []) + \
                         list((repo_root / ".claude" / "commands").glob("*.md") if (repo_root / ".claude" / "commands").exists() else [])

        skill_set = _collect(skill)
        workflow_set = _collect(workflow)
        cmd_set = set()
        for c in cmd_candidates:
            cmd_set |= _collect(c)

        # Only consider gates whose prefix matches this skill
        cmd_set_filtered = {g for g in cmd_set if any(g.startswith(p) for p in allowed_prefixes)}

        for g in cmd_set_filtered - skill_set:
            issues.append(f"{skill.relative_to(repo_root)} missing mention of {g}")
        for g in cmd_set_filtered - workflow_set:
            issues.append(f"{workflow.relative_to(repo_root)} missing mention of {g}")

    if issues:
        return {
            "status": "warn",
            "message": f"{len(issues)} within-skill gate gap(s)",
            "details": issues,
            "fix_hint": "add the missing gate script mention to the SAME skill's SKILL.md / workflow.md",
        }
    return {"status": "pass", "message": "gate references consistent per-skill"}
```

### verify
```bash
cd /Users/didi/work/prd-tools
python3 tools/selfcheck/run.py --category docs 2>&1 | grep "D4"
# 期望：✓ [D4] ... 或者 ⚠ 但数量 ≤ 3（真实同 skill 内缺失）
```

### commit
```
refactor(audit-p0r2): D4 selfcheck scoped to within-skill gate references

Previously D4 expected prd-distill SKILL.md to mention reference-*-gate.py
(and vice versa), flagging 16 cross-skill false positives. Restricted
the check to within-skill gate prefixes so D4 only flags real gaps
within the same skill.
```

---

## 执行顺序建议

1. **先** P0R2-1/2/3/4/5/6 —— 这 6 个是**字段/格式对齐**，修完下一次 /prd-distill 就不再有修复循环
2. **再** P0R2-7/8/9 —— 工具链平滑（docx / CLI 兼容）
3. **最后** P0R2-10/11/12 + D4 check 修复 —— 流程硬约束 + 错误引导 + selfcheck 归零

## 验收

做完后跑：
```bash
cd /Users/didi/work/prd-tools
python3 tools/selfcheck/run.py --all  # 目标：0 fail, 0 warn（或 ≤ 1 warn 且说明原因）
```

然后在 dive-bff 再跑一次 `/prd-distill` 实测（用 v2.18.0 一样的 PRD，对比修复前后的修复循环次数、人工干预次数、最终产物质量）。
