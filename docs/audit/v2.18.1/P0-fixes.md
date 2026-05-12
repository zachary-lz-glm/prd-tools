# P0 修复清单

> **执行原则**：按 P0-1 → P0-6 顺序做。每个 FIX 一个独立 commit。遇到现状与文档描述不一致先停下回报。

---

## P0-1 — `distill-workflow-gate.py` 缺 `import yaml`

### 问题
`scripts/distill-workflow-gate.py` 在 `_check_critique_status` 里调用 `yaml.safe_load(f)`，但文件头部没 `import yaml`。只要 `context/critique/*.yaml` 存在（Two-Pass Critic MVP 会生成这些文件），脚本就会抛 `NameError: name 'yaml' is not defined` 并 exit 1，导致 /prd-distill 永远无法通过 completion gate。

### 证据
- `scripts/distill-workflow-gate.py:20-25` 现有 import:
  ```python
  import argparse
  import os
  import re
  import sys
  from pathlib import Path
  ```
- `scripts/distill-workflow-gate.py:348-351`:
  ```python
  for cf in critique_files:
      try:
          with open(cf, 'r', encoding='utf-8') as f:
              data = yaml.safe_load(f) or {}
  ```

### 修复

在 `scripts/distill-workflow-gate.py` 的 import 区（约第 24-25 行之间）加一行：

```python
import yaml
```

**放在 `import sys` 之后、`from pathlib import Path` 之前**（按字母序）。

### verify
```bash
cd /Users/didi/work/prd-tools
python3 -c "import ast, sys; tree = ast.parse(open('scripts/distill-workflow-gate.py').read()); names = {n.name for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}; sys.exit(0 if 'yaml' in names else 1)"
echo "exit=$?"
```
**期望**：`exit=0`

### commit 信息
```
fix(audit-p0): [P0-1] distill-workflow-gate.py import yaml

_check_critique_status used yaml.safe_load without importing yaml.
NameError would fire whenever context/critique/*.yaml exists (Two-Pass
Critic MVP creates these), blocking /prd-distill completion gate.
```

---

## P0-2 — `workflow.md` 有整段重复的 Step 2.5/2.6

### 问题
`plugins/prd-distill/skills/prd-distill/workflow.md` 里 "## 步骤 2.5：Query Plan" 和 "## 步骤 2.6：Context Pack" 完全重复出现两次。LLM 读到会重复执行，或触发 gate 的 ordering 保护、被迫用 `--allow-rerun` 绕过。

### 证据
- 第一份：`workflow.md` L351（Step 2.5 开头）到 L382（Step 2.6 结尾）
- 重复份：L384（Step 2.5 再次开头）到 L415

审计时这两份内容一字不差。

### 修复

**先 grep 定位再删**，不要靠行号。

1. `rg -n "^## 步骤 2\.5：Query Plan" plugins/prd-distill/skills/prd-distill/workflow.md` → 应返回**两行**。
2. `rg -n "^## 步骤 2\.6：Context Pack" plugins/prd-distill/skills/prd-distill/workflow.md` → 应返回**两行**。
3. 如果不是恰好两行，停下回报。
4. 如果是恰好两行：
   - 确认两份 Step 2.5 的内容字符串相等（可以用 `sed` 或 `awk` 把两段提取出来 diff 一下）。如果不等，停下回报。
   - **删除第二份**（L384-L415 附近）。保留第一份。
   - 删除后相邻行如果有多余空行，保留最多一个空行。

### 另：检查 Step 8.6 是不是也重复

```bash
rg -n "^## 步骤 8\.6" plugins/prd-distill/skills/prd-distill/workflow.md
```

审计发现 "## 步骤 8.6：Distill Completion Gate" 也出现两次，标题相同但内容不同（一个是硬约束描述，一个是检查清单）。**这次 FIX 不处理 8.6**（那属于 P2-6，留到 P2 再做）。仅处理 2.5/2.6。

### verify
```bash
cd /Users/didi/work/prd-tools
rg -c "^## 步骤 2\.5：Query Plan" plugins/prd-distill/skills/prd-distill/workflow.md
rg -c "^## 步骤 2\.6：Context Pack" plugins/prd-distill/skills/prd-distill/workflow.md
```
**期望**：两行都输出 `1`。

### commit 信息
```
fix(audit-p0): [P0-2] remove duplicate Step 2.5/2.6 in workflow.md

workflow.md had Step 2.5 (Query Plan) and Step 2.6 (Context Pack) each
appearing twice with identical content. LLM would re-execute these
steps, overwriting query-plan.yaml and context-pack.md, or hit gate
ordering protection and be forced into --allow-rerun which bypasses
the ordering safeguard entirely.
```

---

## P0-3 — `reference-step-gate.py` Stage 4 前置漏 `02-coding-rules.yaml`

### 问题
`reference` workflow 的 Stage 4（`04-routing-playbooks.yaml`）要求"检查 02 去重"，意味着它依赖 `02-coding-rules.yaml` 已经存在。但 `reference-step-gate.py` 里 step "2d" 的 prerequisites 只列了 01 和 03，没列 02。用户 `--allow-rerun` 回到 2b 删掉 coding-rules 再跳 2d 会静默放行，产出质量下降。

### 证据
- `scripts/reference-step-gate.py:61-68`:
  ```python
  "2d": {
      "label": "Phase 2 Stage 4: routing",
      "prerequisites": [
          ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
          ("_prd-tools/reference/03-contracts.yaml", "Stage 3"),
      ],
  ```
- `plugins/reference/skills/reference/workflow.md:133`: "阶段 4：`04-routing-playbooks.yaml`（含 capability_inventory，**检查 02 去重**）"
- `plugins/reference/skills/reference/steps/step-02-deep-analysis.md:88`: "阶段 4 的去重依赖 02-coding-rules"

### 修复

在 `scripts/reference-step-gate.py` 的 "2d" prerequisites 里，**在 01 之后、03 之前**插入一行：

```python
("_prd-tools/reference/02-coding-rules.yaml", "Stage 2"),
```

修改后应该是：
```python
"2d": {
    "label": "Phase 2 Stage 4: routing",
    "prerequisites": [
        ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
        ("_prd-tools/reference/02-coding-rules.yaml", "Stage 2"),
        ("_prd-tools/reference/03-contracts.yaml", "Stage 3"),
    ],
},
```

### verify
```bash
cd /Users/didi/work/prd-tools
python3 - <<'EOF'
import ast
tree = ast.parse(open('scripts/reference-step-gate.py').read())
# Find STEP_TABLE / config dict and check "2d" prereqs include 02-coding-rules
src = open('scripts/reference-step-gate.py').read()
start = src.find('"2d"')
end = src.find('}', start)
assert '02-coding-rules.yaml' in src[start:end], "Stage 2 prereq missing"
print("OK: Stage 4 (2d) now requires 02-coding-rules.yaml")
EOF
```
**期望**：输出 `OK: Stage 4 (2d) now requires 02-coding-rules.yaml`，exit 0。

### commit 信息
```
fix(audit-p0): [P0-3] reference-step-gate 2d requires 02-coding-rules

workflow.md and step-02-deep-analysis.md both state that Stage 4
(routing-playbooks) performs dedup against 02-coding-rules, but the
step-gate only enforced 01 and 03 as prerequisites. A user running
--allow-rerun against 2b (dropping 02) and then jumping to 2d would
silently pass, producing a routing-playbooks with duplicate entries.
```

---

## P0-4 — `contract-delta.contract.yaml` 字段名与真实 schema 完全不匹配

### 问题
`plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml` 声明的 `required_top_level` 是 `meta` / `deltas`，但真实 schema（workflow.md §步骤 4 和 `output-contracts.md:770-794` 定义）用的顶层字段是 `schema_version` / `contracts`，数组叫 `contracts` 不叫 `deltas`，每条字段是 `producer / consumers / contract_surface / change_type / alignment_status`。一旦 `validate-artifact.py` 启用，这份 contract 会对**所有** distill 产物 fail。

### 证据
- contract 现状 `plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml:1-10`:
  ```yaml
  required_top_level:
    - meta
    - deltas
  rules:
    - id: "delta_has_trace"
      each: "deltas"
      required:
        - id
        - requirement_id
        - layer
  ```
- 真实 schema `plugins/prd-distill/skills/prd-distill/references/output-contracts.md:770-794` 字段清单见该文件。顶层是 `schema_version` / `tool_version` / `contracts` / `alignment_summary`，数组 `contracts` 每条含：`id / producer / consumers / contract_surface / change_type / alignment_status / fields? / notes?`。
- `scripts/distill-quality-gate.py:_check_artifact_contracts` 会调 `validate-artifact.py`，后者按 contract 检查字段。

### 修复

**先读两份文件确认现状**，再决定改动：
1. Read `plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml` 完整内容。
2. Read `plugins/prd-distill/skills/prd-distill/references/output-contracts.md` 的 `contract-delta.yaml` 一节（搜 "contract-delta" 定位）。
3. 以 `output-contracts.md` 为权威源，重写 contract 文件。

重写后 `contract-delta.contract.yaml` 应为：

```yaml
# Contract for context/contract-delta.yaml
# Source of truth: references/output-contracts.md §contract-delta
schema_version: "1.0"
required_top_level:
  - schema_version
  - contracts
rules:
  - id: "contract_has_identity"
    each: "contracts"
    required:
      - id
      - producer
      - consumers
      - contract_surface
      - change_type
      - alignment_status
  - id: "change_type_enum"
    each: "contracts"
    field: "change_type"
    enum:
      - ADD
      - MODIFY
      - REMOVE
      - NO_CHANGE
  - id: "alignment_status_enum"
    each: "contracts"
    field: "alignment_status"
    enum:
      - aligned
      - pending
      - blocked
      - not_applicable
```

**如果 `validate-artifact.py` 的 rule 语法不支持 `enum`** 这种形式（审计时未展开确认），只保留前一个 rule `contract_has_identity`，删除后两个 enum rule。**判定方法**：读 `scripts/validate-artifact.py`，搜 `rule.get('enum')` 或 `enum` 关键字。有就保留，没有就删。

### 关于 `requirement_id / layer` 两个字段

原 contract 要求的 `requirement_id` / `layer` 在真实 schema 里**没有**。按"以实际 schema 为准"的原则，本次 FIX 从 contract 里删掉它们。**不要反向去给 schema 加字段**——那属于功能扩展，不在本次审计修复范围。

### verify
```bash
cd /Users/didi/work/prd-tools

# 1. YAML 语法正确
python3 -c "import yaml; yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml'))"
echo "yaml-ok=$?"

# 2. 真实产物能过 contract（用 v2.18.0 的 dive-bff 快照做样本）
SAMPLE=/Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot/context/contract-delta.yaml
if [ -f "$SAMPLE" ]; then
  python3 scripts/validate-artifact.py \
    --contract plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml \
    --artifact "$SAMPLE" 2>&1 | tee /tmp/p0-4-verify.log
  echo "validate-exit=$?"
else
  echo "SAMPLE not found, skip live check"
fi
```
**期望**：`yaml-ok=0`。如果 sample 存在，`validate-exit=0` 且无 `Missing top-level key` 之类报错。

### commit 信息
```
fix(audit-p0): [P0-4] align contract-delta.contract.yaml with real schema

The contract declared required_top_level as [meta, deltas] and required
each deltas entry to have [id, requirement_id, layer]. None of these
fields exist in the real schema (output-contracts.md §contract-delta),
which uses [schema_version, contracts] and per-contract fields
[id, producer, consumers, contract_surface, change_type, alignment_status].
Once validate-artifact.py runs as part of distill-quality-gate, every
contract-delta.yaml fails with "Missing top-level key: meta", blocking
/prd-distill completion forever.
```

---

## P0-5 — code_scan 必须兜底扫 `build/` 避免漏发现已编译的历史实现

### 问题
v2.18.0 在 dive-bff 跑的产物里，LLM 生成了一个新 CampaignType 枚举名 `GasStationDxGy`，并标 `type_id=44 待确认`。但 dive-bff 的 `build/` 目录里早已有一份编译产物定义了 `CompleteOrderGas = 44`（同样的 type_id，不同的名字）——这是之前做过一版但回滚了 src 没回滚 build 的残留。LLM 没扫 build，完全不知道。

如果开发按 plan 执行，会新建 `CampaignType.GasStationDxGy = 44` 的枚举 + 对应 `gasStationDxGy.ts` 模板。但后端 / 已编译产物用的是 `CompleteOrderGas`——**编译过**，但运行时后端返回 type_id=44 时，BFF 的 switch 走 `GasStationDxGy` 分支、后端约定 `CompleteOrderGas`，表现为所有预览/查询/批量模板 fallback，**上线直接炸**。

### 证据
- 产物 `spec/ai-friendly-prd.md:18`、`context/requirement-ir.yaml`、`plan.md TASK-001` 统一用 `GasStationDxGy`。
- dive-bff 残留：
  ```
  build/config/constant/campaignType.d.ts:59         CompleteOrderGas = 44
  build/config/constant/campaignType.js:63           CampaignType[CampaignType["CompleteOrderGas"] = 44] = "CompleteOrderGas";
  build/config/template/preview/options/audienceSegmentation/completeOrderGas.js:3
                                                     exports.getCompleteOrderGasAudienceSegmentationTemplate = void 0;
  build/config/template/render/message.js:663        case campaignType_1.CampaignType.CompleteOrderGas:
  ```
- 产物 `context/evidence.yaml` 只有占位 `EV-CODE-PENDING: source: pending`，没扫 build。

### 修复

这个 FIX 分三处改动，都在 `plugins/prd-distill/skills/prd-distill/` 下：

#### 5-A：`steps/step-02-classify.md`（或 query-plan 对应 step，需确认文件名）

**定位文件**：
```bash
rg -l "query.plan|query_plan|seed_queries|code_scan" plugins/prd-distill/skills/prd-distill/steps/
```

找 code_scan 或 query-plan 生成相关的 step。在 "扫描范围" 或类似章节里，**加一段**：

```markdown
### 扫描范围兜底：build/ 和 dist/

除 `src/` 外，必须额外扫描仓库的已编译产物目录（`build/`、`dist/`、`lib/` — 按项目实际 `project-profile.yaml` 的 build_output_dirs 决定）。目的：发现历史上实现过但已从 `src/` 移除的 registry 型改动（CampaignType 枚举、switch case、previewRewardType 映射等）。

**强制规则**：
- 对 registry 型改动（枚举、switch 新增 case、映射表新增 key），`code_scan` 必须在 `build/` 和 `src/` 各跑一遍。
- 若在 `build/` 发现**同 type_id / 同 key 但不同 name** 的既有实现，必须在 OQ 顶置一条：
  `OQ-CODE-NAMING: "历史实现 name={build_name}（见 build/path:L），PRD 提议 name={prd_name}。是否复用历史 name？"`
- 若 `build/` 和 `src/` 存在内容不一致（例如 `build/` 有但 `src/` 无），evidence.yaml 必须增加一条 `EV-CODE-BUILD-*` 记录此事实，并在 `graph-context.md` 的 §"历史残留" 段落说明。
```

#### 5-B：`steps/step-03-query-plan.md`（或对应文件）

在 seed_queries 构造规则里，加一条：

```markdown
- 对 registry 型改动，seed_queries 必须包含对应 build 目录的 pattern，例如 `build/**/campaignType.*`、`build/**/*.d.ts`。
```

#### 5-C：`assets/scripts/context-pack.py` 的 seed_queries 硬编码部分（L452-460 附近）

这里原本硬编码了 dive-bff 的业务词，本次 FIX **只加一条通用的 build 目录 pattern**（不动原有硬编码，那些属于 P2-4 的范围）：

```python
# 在现有 seed_queries 列表末尾追加
'build/**/*.d.ts',
'build/**/*.js',
```

**只加这两行**。不要整理、不要重构 seed_queries。

### verify

```bash
cd /Users/didi/work/prd-tools

# 5-A/5-B：step 文件里必须出现 build/ 兜底关键字
rg -c "build/" plugins/prd-distill/skills/prd-distill/steps/*.md
rg -c "OQ-CODE-NAMING" plugins/prd-distill/skills/prd-distill/steps/*.md

# 5-C：context-pack.py seed_queries 含 build
rg -n "build/\*\*/\*\.(d\.ts|js)" plugins/prd-distill/skills/prd-distill/assets/scripts/context-pack.py || \
rg -n "build/\*\*/\*\.(d\.ts|js)" scripts/context-pack.py
```
**期望**：至少有一个 step 文件包含 `build/`；`OQ-CODE-NAMING` 在至少一个 step 里出现；context-pack 里能 grep 到 build pattern。

### commit 信息
```
fix(audit-p0): [P0-5] code_scan must cover build/ for registry changes

LLM running /prd-distill on dive-bff invented CampaignType
GasStationDxGy=44, unaware that build/ already had CompleteOrderGas=44
compiled from a prior iteration. Following the generated plan would
ship a BFF that speaks GasStationDxGy while backend+compiled templates
speak CompleteOrderGas — runtime switches fall through, all preview /
query / batch templates break.

Add build/ to code_scan scope for registry-type changes (enums, switch
cases, mapping tables). When same id with different name is found in
build/, require a top-priority OQ-CODE-NAMING entry asking whether to
reuse the historical name.
```

---

## P0-6 — `coverage-report.yaml` 生成器 bug：missing 数组全是空字符串

### 问题
`context/coverage-report.yaml` 报 `status: fail / coverage_ratio: 0.0 / 18 blocks not covered`，但 `missing:` 数组里是 18 个空字符串 `['', '', '', ...]`，不是真正缺失的 block_id。这是生成脚本的 bug——它正确发现了"有 block 没被 evidence-map 引用"但没把 block_id 填进 missing 列表。

这个 bug 让 coverage-report 既喊 fail 又说不出哪里 fail，与 `final-quality-gate.yaml` (pass/88) 形成打架，人类看到两份打架的 gate 就失去判断力。

### 证据
- 产物：`/Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot/context/coverage-report.yaml`，里面 `missing` 数组全空字符串。
- 生成脚本：`scripts/prd-coverage-gate.py`（路径待确认，执行时 `rg -l "coverage-report.yaml" scripts/` 找）。

### 修复

#### 6-A：定位生成脚本
```bash
rg -l "coverage-report\.yaml|coverage_report" scripts/ plugins/
```
确定写 `coverage-report.yaml` 的脚本。**不要凭记忆，先 grep**。

#### 6-B：找 bug
在生成脚本里搜：
```bash
rg -n "missing|block_coverage" <那个脚本>
```
审计推测的 bug 点：计算 missing blocks 时，迭代器返回的是空对象（比如 `block.get('id', '')`），而不是 block_id。具体位置**必须读脚本确认**。

#### 6-C：修复规则

- 如果发现循环里把空字符串 push 到 missing，改为 push `block['id']`（或对应字段名）。
- 如果发现某个字段不存在导致 fallback 到 `''`，先检查 block_id 在 evidence-map 里的真实字段名（`block_id` vs `id` vs `source_block_id`）。真实字段名以 `document-structure.json` 的生成逻辑为准（读 ingest 脚本）。

#### 6-D：如果字段名调研下来是历史遗留的多种名字

不要强行统一。本 FIX 只修生成器让 missing 数组填进真实值。**跨产物字段统一属于 P1 范围**（见 P1-3 `source_blocks` vs `source_block_ids`），这次不做。

### verify

```bash
cd /Users/didi/work/prd-tools

# 找到生成脚本
GEN=$(rg -l "coverage-report\.yaml" scripts/ plugins/ | head -1)
echo "generator: $GEN"

# 跑一次，用快照产物的上游数据做输入（如果脚本支持）
# 否则用单元测试式的小输入
# 具体 verify 命令必须在读脚本后给出；如果脚本是 lib 型不能直接跑，写一个最小 Python 片段复现

# 最低限度验证：脚本里不再有 missing 写入空字符串的路径
python3 - <<EOF
import ast, sys
src = open('$GEN').read()
# 简单启发式：搜寻 missing.append('') 或 missing = [''] * N 这种明显 bug
bad_patterns = ["missing.append('')", 'missing.append("")', "[''] *", '[""] *']
found = [p for p in bad_patterns if p in src]
if found:
    print("BUG still present:", found)
    sys.exit(1)
print("no obvious empty-string bug remains")
EOF
```

**期望**：输出 `no obvious empty-string bug remains`，exit 0。

### commit 信息
```
fix(audit-p0): [P0-6] coverage-report missing now carries real block_ids

coverage-report.yaml was reporting fail with missing: ['','','',...]
18 empty strings. Generator correctly detected uncovered blocks but
pushed empty strings into the missing array instead of block_ids.
Result: final-quality-gate said pass/88 while coverage-report said
fail/0.0 with no diagnostic info, destroying human trust in both.
```

---

## 汇总验证（P0 全做完后跑）

```bash
cd /Users/didi/work/prd-tools

# 1. 所有 Python 脚本语法 OK
for f in scripts/*.py; do
  python3 -m py_compile "$f" || { echo "SYNTAX FAIL: $f"; exit 1; }
done
echo "all python scripts compile"

# 2. 所有 contract YAML 语法 OK
for f in plugins/*/skills/*/references/contracts/*.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" || { echo "YAML FAIL: $f"; exit 1; }
done
echo "all contracts parse"

# 3. workflow.md 没有重复章节
for skill in plugins/prd-distill/skills/prd-distill plugins/reference/skills/reference; do
  rg "^## 步骤 " "$skill/workflow.md" | sort | uniq -d | tee /tmp/dup.txt
done
test ! -s /tmp/dup.txt && echo "no duplicate sections" || { echo "DUPLICATE STILL PRESENT"; exit 1; }

# 4. contract-delta 产物过 validate-artifact
SAMPLE=/Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot/context/contract-delta.yaml
if [ -f "$SAMPLE" ]; then
  python3 scripts/validate-artifact.py \
    --contract plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml \
    --artifact "$SAMPLE"
fi
```

全通过后再进 P1。
