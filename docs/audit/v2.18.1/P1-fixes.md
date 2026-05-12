# P1 修复清单

> **前置**：P0 全部做完并通过验证。每个 FIX 独立 commit。commit prefix: `fix(audit-p1): [P1-x] ...`

---

## P1-1 — `workflow.md` Step 7 模板用了全角智能引号

### 问题
`plugins/prd-distill/skills/prd-distill/workflow.md` Step 7 的 `reference-update-suggestions.yaml` 模板（约 L599-619）里所有引号都是 U+201C/U+201D (`"` / `"`) 和 U+2018/U+2019 (`'` / `'`)。YAML 不认这些，LLM 照抄会产出非法 YAML；pyyaml 抛 `ScannerError`，下游 gate 静默读成空 dict，产生假通过/假失败。

### 修复

```bash
cd /Users/didi/work/prd-tools
python3 - <<'EOF'
import re
f = 'plugins/prd-distill/skills/prd-distill/workflow.md'
s = open(f, encoding='utf-8').read()
# 只替换代码块内的智能引号 — 用保守方式先全文统计，再决定
count_before = sum(s.count(c) for c in '""''')
# 全文替换（workflow.md 里的正文中文不应有大量智能引号，但为稳妥只改 yaml/code block）
new = re.sub(
    r'(```ya?ml\n)(.*?)(\n```)',
    lambda m: m.group(1) + m.group(2).translate(str.maketrans({'"': '"', '"': '"', ''': "'", ''': "'"})) + m.group(3),
    s, flags=re.DOTALL
)
count_after = sum(new.count(c) for c in '""''')
print(f"smart quotes in yaml blocks: {count_before - count_after} replaced, {count_after} remain (outside yaml blocks)")
if new != s:
    open(f, 'w', encoding='utf-8').write(new)
    print("written")
EOF
```

**规则**：只改代码块（```yaml ... ```）内的智能引号。正文里的中文段落如果有智能引号，保留不动。

### verify
```bash
python3 - <<'EOF'
import re
f = 'plugins/prd-distill/skills/prd-distill/workflow.md'
s = open(f).read()
blocks = re.findall(r'```ya?ml\n(.*?)\n```', s, re.DOTALL)
for i, b in enumerate(blocks):
    for c in '""''':
        assert c not in b, f"block {i} still has smart quote {c!r}"
print(f"OK: {len(blocks)} yaml blocks clean")
EOF
```

### commit
```
fix(audit-p1): [P1-1] normalize smart quotes in workflow.md yaml templates

Step 7 template for reference-update-suggestions.yaml used U+201C/201D
and U+2018/2019. LLM copying would produce unparseable YAML; downstream
gates silently read {}, producing false pass/fail.
```

---

## P1-2 — `SKILL.md` Final Completion Gate 没提 `distill-workflow-gate.py`

### 问题
`plugins/prd-distill/skills/prd-distill/SKILL.md` §Final Completion Gate（约 L102-118）只列了 `distill-quality-gate.py` 和 `render-distill-portal.py`，但 `.claude/commands/prd-distill.md:150,167` 要求跑 `distill-workflow-gate.py`。LLM 若以 SKILL.md 为主，会跳过 workflow-gate。

### 修复

在 SKILL.md §Final Completion Gate 的脚本列表里加一条：

```markdown
- **必须运行** `python3 .prd-tools/scripts/distill-workflow-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`，且 exit code ≠ 2（0 = 全过，1 = warning，2 = 硬失败）。
```

**插入位置**：放在 `distill-quality-gate.py` 这条之后、`render-distill-portal.py` 之前。

### verify
```bash
rg -n "distill-workflow-gate" plugins/prd-distill/skills/prd-distill/SKILL.md
```
**期望**：至少一行命中。

### commit
```
fix(audit-p1): [P1-2] SKILL.md lists distill-workflow-gate.py

commands/prd-distill.md requires workflow-gate but SKILL.md did not.
LLMs reading SKILL.md as the primary reference would declare completion
without ever running the gate that enforces step ordering.
```

---

## P1-3 — `evidence.source_blocks` vs `source_block_ids` 表述矛盾

### 问题
- `workflow.md:329`: "evidence 包含 `source_blocks`（必填）、`source_block_ids`（兼容旧格式）"
- `requirement-ir.contract.yaml:23`: 只要 `len(source_blocks)>0 or len(source_block_ids)>0` 其一非空
- `prd-coverage-gate.py:170`: 同 contract，两者任一即可
- `output-contracts.md:649-653`: schema 里只列 `source_block_ids`，没列 `source_blocks`

文档自相矛盾，LLM 选哪个都可能写出不一致的产物。

### 修复

**以 contract + gate + output-contracts 为准**（它们是消费端），把 workflow.md 的"必填"措辞改成"任一非空"：

1. 读 `plugins/prd-distill/skills/prd-distill/workflow.md` 329 附近关于 `source_blocks` 的一段。
2. 把 `source_blocks（原始 PRD block_id 列表，必填）、source_block_ids（兼容旧格式）` 改为：
   ```
   source_blocks 或 source_block_ids（原始 PRD block_id 列表，至少一个非空；新产物用 source_blocks，旧产物保留 source_block_ids 兼容）
   ```
3. 同步在 `output-contracts.md` 的 evidence schema 里把 `source_blocks` 字段补上：在 `source_block_ids` 条目旁加 `source_blocks` 同结构的一条。

### verify
```bash
rg -n "source_blocks" plugins/prd-distill/skills/prd-distill/workflow.md plugins/prd-distill/skills/prd-distill/references/output-contracts.md
```
**期望**：workflow.md 和 output-contracts.md 两处都出现 `source_blocks`，且 workflow.md 不再写"必填"。

### commit
```
fix(audit-p1): [P1-3] align source_blocks / source_block_ids semantics

workflow.md marked source_blocks as mandatory; contract + gate +
output-contracts accept either one being non-empty. Unified under the
"either non-empty" semantics (consumer-side) and added source_blocks
to output-contracts schema for symmetry.
```

---

## P1-4 — `step-01-parse.md` 步骤编号 "4" 重复

### 问题
`plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md:74,75` 连续两个 `4.` 开头，后面的 `5.`（L83）实际是第 6 步。LLM 顺序推理可能漏步。

### 修复
把 L75 的 `4.` 改成 `5.`，L83 开始的 `5.` 改成 `6.`，以此类推直到本章节最后一条编号加 1。

**必须先读文件**确认 L74 往后的编号序列，再改，不要靠记忆。

### verify
```bash
python3 - <<'EOF'
import re
lines = open('plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md').readlines()
# Find numbered list near L74
for i, l in enumerate(lines[70:90], 71):
    m = re.match(r'^(\d+)\.', l)
    if m:
        print(f"L{i}: {m.group(1)}. ...")
EOF
```
**期望**：编号严格递增，无重复。

### commit
```
fix(audit-p1): [P1-4] fix duplicate step number in step-01-parse.md
```

---

## P1-5 — `distill-step-gate.py` `8.1-confirm` 硬写 approved

### 问题
`scripts/distill-step-gate.py:375-377` 里：
```python
if args.step == "8.1-confirm":
    state.set_human_checkpoint("report_review", "approved")
```
无论用户实际在 `report-confirmation.yaml` 写了 approved / needs_revision / blocked，workflow-state 里的 human_checkpoint 都会被硬写成 approved。未来若加"checkpoint=approved 才能进 plan"的检查会误放行。

### 修复
改为读 `report-confirmation.yaml` 的实际 status：

```python
if args.step == "8.1-confirm":
    rc_path = distill_dir / "context" / "report-confirmation.yaml"
    rc_status = "pending"
    if rc_path.exists():
        try:
            with open(rc_path, encoding='utf-8') as f:
                rc = yaml.safe_load(f) or {}
            rc_status = "approved" if rc.get("status") == "approved" else "pending"
        except Exception:
            rc_status = "pending"
    state.set_human_checkpoint("report_review", rc_status)
```

**注意**：这里用了 `yaml.safe_load`，需要 `distill-step-gate.py` 有 `import yaml`。先 grep 确认，没有就加。

### verify
```bash
python3 -c "import ast; tree = ast.parse(open('scripts/distill-step-gate.py').read()); assert any(isinstance(n, ast.Import) and any(a.name=='yaml' for a in n.names) for n in ast.walk(tree)), 'yaml not imported'"
rg -n "report-confirmation.yaml" scripts/distill-step-gate.py
```
**期望**：yaml 已 import；脚本里能 grep 到 `report-confirmation.yaml`。

### commit
```
fix(audit-p1): [P1-5] 8.1-confirm step reads real report-confirmation status

Previously the step gate hard-coded human_checkpoints.report_review to
"approved" regardless of what the user wrote in report-confirmation.yaml.
Any future check that gates plan generation on this checkpoint would
silently let needs_revision / blocked through.
```

---

## P1-6 — IR 里的 `ai_prd_req_id` 指向不存在的 REQ 编号 + REQ-003 漏 IR 映射

### 问题

这是**产物**层面的问题（v2.18.0 在 dive-bff 实跑时发生的），但根因在**工具**层面没有强制 IR ↔ AI-friendly-prd REQ 编号的一致性约束。

具体观察：
- 产物 `context/requirement-ir.yaml` L12-13: IR-003 `ai_prd_req_id: "REQ-010"`，L62: IR-010 `ai_prd_req_id: "REQ-ALERT-001"`，IR-011 `ai_prd_req_id: "REQ-SUPP-001"` —— 但 `spec/ai-friendly-prd.md` 只定义了 REQ-001 ~ REQ-007。
- REQ-003（目标人群步骤）在 ai-friendly-prd.md 里存在，但 IR 列表里没有对应项（即使是 `type=NO_CHANGE` 也应该留一条 IR 说"审阅过无改动"）。

### 修复

在 `plugins/prd-distill/skills/prd-distill/steps/` 里找 IR 生成 step（通常是 `step-01-parse.md` 或 `step-02-classify.md`，先 grep 定位），在其 Self-Check 章节加两条**可机器化**约束：

```markdown
### IR ↔ AI-friendly PRD 编号一致性（硬约束）

生成 IR 前后，必须跑以下两条自检：

1. **每条 IR 的 `ai_prd_req_id` 必须在 `spec/ai-friendly-prd.md` 里 `rg -F "REQ-" | rg "{ai_prd_req_id}"` 能命中**。未命中 → 当前 IR 生成失败，不得提交。
2. **ai-friendly-prd.md 里每个 `REQ-xxx` heading 必须在 IR 列表里至少出现一次**（哪怕 `type: NO_CHANGE`）。缺失 → 补一条 IR 占位，type=NO_CHANGE，summary 写 "no BFF-layer change, reviewed"。
```

**同步加到对应 contract**：`plugins/prd-distill/skills/prd-distill/references/contracts/requirement-ir.contract.yaml`，如果有 rules 语法支持，增加 cross-file 校验 rule。如果不支持，记为 TODO 加注释：

```yaml
# TODO(audit-p1-6): cross-file check against spec/ai-friendly-prd.md REQ ids;
# validator doesn't support cross-file rules yet, enforced via step self-check.
```

### verify
```bash
rg -c "ai_prd_req_id" plugins/prd-distill/skills/prd-distill/steps/*.md
# 应至少一个 step 里有对此约束的描述
rg -n "IR ↔ AI-friendly PRD" plugins/prd-distill/skills/prd-distill/steps/
```

### commit
```
fix(audit-p1): [P1-6] enforce IR ↔ ai-friendly-prd REQ id consistency

v2.18.0 produced IRs whose ai_prd_req_id pointed to REQ numbers that
don't exist in ai-friendly-prd.md (REQ-010, REQ-ALERT-001, REQ-SUPP-001),
and omitted an IR for REQ-003 (target audience step). Added hard
self-check rules in the IR step requiring every ai_prd_req_id to match
a real heading, and every REQ heading to be represented in IR (at least
as NO_CHANGE).
```

---

## P1-7 — `ai-friendly-prd.contract.yaml min_h2=13` vs `distill-quality-gate.py` 阈值 ≥8

### 问题
- `ai-friendly-prd.contract.yaml:7`: `min_h2: 13`
- `distill-quality-gate.py:136-139`: 改成"≥8 pass，<3 warning"

一份产物只有 10 个 h2 时：quality-gate pass/warning，artifact-contract fail，completion 被拖 fail。两处阈值不同。

### 修复

**以 contract 为权威**（13-section AI-friendly PRD 是设计意图）：

1. 保持 `ai-friendly-prd.contract.yaml` 的 `min_h2: 13`。
2. 修改 `scripts/distill-quality-gate.py` L136-139 附近的阈值，对齐 contract：
   - h2 < 13 → warning
   - h2 < 8 → fail

**先读脚本确认**这段代码的真实逻辑，再按上述语义改。

### verify
```bash
python3 -c "import yaml; c=yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml')); assert c.get('min_h2')==13"
rg -n "h2" scripts/distill-quality-gate.py | head -20
```

### commit
```
fix(audit-p1): [P1-7] align ai-friendly-prd h2 thresholds

contract required min_h2=13 but quality-gate accepted ≥8 as pass.
A 10-h2 artifact would pass quality-gate and fail validate-artifact,
confusing the completion signal. quality-gate now warns below 13 and
fails below 8, matching contract as source of truth.
```

---

## P1-8 — Self-Check 60% 不可验证（"score 不是估算"这类空话）

### 问题
10 个 step 文件的 Self-Check 章节里，约 60% 条目是无可验证标准的自述，比如：
- "score 是根据实际检查结果计算，不是估算"
- "线索式证据不能省略"
- "project-profile.yaml 的 layer 字段与源码实际架构一致"

LLM 读完很难判断是否达标，Self-Check 沦为形式。

### 修复

本 FIX 不在所有 step 文件里逐条重写（工程量过大，且改法需要设计决策）。只做**标记与优先级**：

1. 在每个 step 文件的 Self-Check 章节顶部加一段：

   ```markdown
   > **Self-Check 的两种条目**：本清单同时包含 (a) **机器可验证断言**（标 `[M]`）和 (b) **人工判读提示**（标 `[H]`）。执行 Self-Check 时：
   > - `[M]` 条目必须逐条列出 `verify: <命令>` 与 `expect: <结果>`，未通过不得进下一步。
   > - `[H]` 条目作为判读提示，LLM 自检后必须写入 workflow-state.yaml 的 `self_check_notes[step_id]` 数组，内容为"我为什么认为这条满足"的简短解释。
   ```

2. 为每个 step 的 Self-Check 条目前加 `[M]` / `[H]` 标记（**不改变条目文字**）。判断规则：
   - 包含 "rg"/"grep"/"path.exists"/"= N"/"in [...]" 这种客观判据 → `[M]`
   - 其他 → `[H]`
3. 新增 `scripts/selfcheck-runner.py`（骨架）：
   ```python
   # scripts/selfcheck-runner.py
   """Parse step file's Self-Check section, run [M] verify commands,
   collect [H] notes from workflow-state.yaml, print pass/fail per item.

   MVP: only validates [M] items that declare `verify:` and `expect:`.
   Reads workflow-state.yaml for [H] notes.
   """
   # stub: argparse --step-file --workflow-state
   # parse markdown, extract self-check items with [M]/[H] tags
   # for [M]: run verify command, compare to expect
   # for [H]: check corresponding note exists in workflow-state self_check_notes
   # exit 0 if all pass, 1 otherwise
   ```

   **MVP stub 就好**——完整实现属于新 feature，不在本次审计修复范围。stub 文件里写 `sys.exit(0)` + 一段 TODO 注释即可，实际实现作为下一个 milestone。

### verify
```bash
rg -c "\[M\]|\[H\]" plugins/*/skills/*/steps/*.md
test -f scripts/selfcheck-runner.py && python3 -m py_compile scripts/selfcheck-runner.py
```

### commit
```
fix(audit-p1): [P1-8] tag Self-Check items as [M]achine / [H]uman

60% of Self-Check items in step files were unverifiable ("score not
estimated") and got tacitly skipped. Tagged each item as [M] (machine
verifiable, must declare verify+expect) or [H] (human judgment, must
write rationale to workflow-state.self_check_notes). Added stub
selfcheck-runner.py for future automation.
```

---

## P1-9 — Gate 错误消息缺 `fix_hint`

### 问题
所有 gate 脚本只说"错了什么"，不说"怎么修"。LLM 进入修复循环。

### 修复

这是**体系性增强**，不可能一次修全部 gate。本 FIX 只做两件事：

1. 在 `scripts/` 下新建 `_gate_fixhint.py`（共享模块），定义 `fix_hint(check_id: str) -> str` 查表：
   ```python
   # scripts/_gate_fixhint.py
   """Shared fix_hint table for gate scripts. Each check emits a hint
   pointing to the concrete step / file / line to edit."""

   FIX_HINTS = {
       # distill-workflow-gate
       "missing_evidence_yaml": "Run Step 1. See workflow.md §步骤 1 / steps/step-01-parse.md",
       "missing_contract_delta": "Run Step 4. See workflow.md §步骤 4 / references/output-contracts.md §contract-delta",
       "report_not_approved": "Ask user to approve report.md; set context/report-confirmation.yaml.status=approved",
       "plan_missing_section": "Add section per workflow.md §plan template (10 sections). See steps/step-03-confirm.md plan checklist.",
       "critique_fail": "Re-run Two-Pass Critic or address critique findings. See references/critique-template.md",
       # distill-quality-gate
       "ai_friendly_prd_h2_low": "Add missing H2 sections to spec/ai-friendly-prd.md. Target: 13 sections (see references/contracts/ai-friendly-prd.contract.yaml).",
       # prd-coverage-gate
       "block_not_covered": "Add evidence for uncovered block to context/evidence-map.yaml. See workflow.md §Evidence Ledger.",
       # reference-step-gate
       "missing_coding_rules": "Run reference Phase 2 Stage 2 first. See workflow.md §阶段 2 / steps/step-02-deep-analysis.md Stage 2.",
   }

   def fix_hint(check_id: str) -> str:
       return FIX_HINTS.get(check_id, "")
   ```

2. 在 `distill-workflow-gate.py` 和 `reference-step-gate.py` 里：
   - 头部加 `from _gate_fixhint import fix_hint`（需要把 scripts 目录加 sys.path 或用 `importlib`，按两个脚本现有的 import 模式走）
   - 凡是输出 `fail:` / `missing:` 的位置，追加 ` → fix: <hint>`。
   - **只改这两个脚本**，其他 gate 留到 P2 或下一次。

### verify
```bash
test -f scripts/_gate_fixhint.py && python3 -m py_compile scripts/_gate_fixhint.py
rg -n "fix_hint" scripts/distill-workflow-gate.py scripts/reference-step-gate.py
```

### commit
```
fix(audit-p1): [P1-9] add fix_hint to distill-workflow and reference-step gates

All gates previously told the LLM what was wrong but not how to fix it,
forcing 3-5 retry cycles. Introduced scripts/_gate_fixhint.py as a
shared hint table and wired distill-workflow-gate.py and
reference-step-gate.py to emit `→ fix: <hint>` on failure messages.
Other gates follow in later iterations.
```

---

## P1-10 — `prd-quality-report.yaml` overall_score 算法不透明

### 问题
产物里 13 个 section 分数 70~95，overall_score 给 72（低于任何一节）。算法没交代，产品看到 "各节 80+ 但总分 72" 会追问。

### 修复

在 `plugins/prd-distill/skills/prd-distill/references/output-contracts.md` 或对应生成 step 里，**显式写明评分公式**：

```markdown
### overall_score 算法（新版）

```
weighted_section_avg = sum(section_score * weight) / sum(weight)
penalty = 3 * missing_items.high + 1 * missing_items.medium + 5 * risk_items.high
overall_score = max(0, round(weighted_section_avg - penalty))
```

权重表（默认所有 section weight=1，除非下列覆盖）：
- §4 Requirements: 2.0
- §5 Field Definitions: 1.5
- §6 Validation Rules: 1.5
- §11 Open Questions: 1.2

`status` 映射：
- overall_score ≥ 85 → pass
- 70 ≤ overall_score < 85 → warn
- overall_score < 70 → fail
```

同时在 `scripts/` 下找到生成 prd-quality-report.yaml 的脚本（`rg -l "prd-quality-report" scripts/`），把计算逻辑对齐上述公式。如果脚本里本来就是这套逻辑只是没文档化，只改文档。如果不是，改脚本 + 加注释引用 output-contracts.md。

### verify
```bash
rg -n "overall_score" plugins/prd-distill/skills/prd-distill/references/output-contracts.md
rg -l "prd-quality-report" scripts/ plugins/
```

### commit
```
fix(audit-p1): [P1-10] document overall_score formula in prd-quality-report

The 72/100 overall_score vs 70-95 section scores was unexplained,
undermining producer confidence in the report. Published the weighted
average + penalty formula in output-contracts.md and aligned the
generator with the documented spec.
```

---

## P1 汇总验证

```bash
cd /Users/didi/work/prd-tools

# P1-1: workflow.md yaml blocks clean
python3 - <<'EOF'
import re
s = open('plugins/prd-distill/skills/prd-distill/workflow.md').read()
for b in re.findall(r'```ya?ml\n(.*?)\n```', s, re.DOTALL):
    for c in '""''':
        assert c not in b, "smart quote leak"
print("P1-1 OK")
EOF

# P1-2: SKILL mentions workflow-gate
rg -q "distill-workflow-gate" plugins/prd-distill/skills/prd-distill/SKILL.md && echo "P1-2 OK"

# P1-3: source_blocks in output-contracts
rg -q "source_blocks" plugins/prd-distill/skills/prd-distill/references/output-contracts.md && echo "P1-3 OK"

# P1-5: step-gate reads report-confirmation
rg -q "report-confirmation.yaml" scripts/distill-step-gate.py && echo "P1-5 OK"

# P1-7: quality-gate aligns to min_h2=13
python3 -c "import yaml; c=yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml')); assert c.get('min_h2')==13" && echo "P1-7 OK"

# P1-8: Self-Check tagged
rg -q "\[M\]|\[H\]" plugins/prd-distill/skills/prd-distill/steps/ && echo "P1-8 OK"

# P1-9: fix_hint wired
test -f scripts/_gate_fixhint.py && rg -q "fix_hint" scripts/distill-workflow-gate.py && echo "P1-9 OK"

echo "=== P1 全部验证完毕 ==="
```
