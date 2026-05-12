# 验证清单（对账用）

> 这份清单把所有 FIX 的 verify 命令集中在一处，方便**维护者验收**和 **GLM 交付时自查**。
>
> 三类验证：
> - **minimal_verify**：单个 FIX 改完立即跑
> - **batch_verify**：一批（P0/P1/P2）全做完跑
> - **regression_verify**：全做完后跑一次完整自检（就是 selfcheck skill，见 `/Users/didi/.claude/plugins/prd-tools-selfcheck/` 或本仓库 `plugins/prd-tools-selfcheck/`）

---

## P0

### P0-1 `distill-workflow-gate.py` import yaml

```bash
cd /Users/didi/work/prd-tools
python3 -c "import ast, sys; tree = ast.parse(open('scripts/distill-workflow-gate.py').read()); names = {n.name for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}; sys.exit(0 if 'yaml' in names else 1)"
echo "P0-1: exit=$? (expect 0)"
```

### P0-2 workflow.md 无重复章节

```bash
rg -c "^## 步骤 2\.5：Query Plan" plugins/prd-distill/skills/prd-distill/workflow.md
rg -c "^## 步骤 2\.6：Context Pack" plugins/prd-distill/skills/prd-distill/workflow.md
# 期望：都输出 1
```

### P0-3 reference-step-gate 2d 需要 02-coding-rules

```bash
python3 - <<'EOF'
src = open('scripts/reference-step-gate.py').read()
start = src.find('"2d"')
end = src.find('}', start)
assert '02-coding-rules.yaml' in src[start:end], "Stage 2 prereq missing"
print("P0-3 OK")
EOF
```

### P0-4 contract-delta 字段对齐

```bash
python3 -c "import yaml; c=yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml')); assert 'contracts' in c.get('required_top_level', []) and 'deltas' not in c.get('required_top_level', []); print('P0-4 OK')"

# 如果 dive-bff 快照存在，再跑 validate-artifact
SAMPLE=/Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot/context/contract-delta.yaml
if [ -f "$SAMPLE" ]; then
  python3 scripts/validate-artifact.py \
    --contract plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml \
    --artifact "$SAMPLE"
fi
```

### P0-5 code_scan 覆盖 build/

```bash
# step 文件里有 build/ 兜底说明
rg -q "build/" plugins/prd-distill/skills/prd-distill/steps/ && echo "step has build/ reference"
# OQ-CODE-NAMING 约束在 step 中
rg -q "OQ-CODE-NAMING" plugins/prd-distill/skills/prd-distill/steps/ && echo "OQ-CODE-NAMING rule present"
# context-pack seed_queries 含 build pattern
rg -q "build/\*\*" scripts/context-pack.py && echo "P0-5 OK"
```

### P0-6 coverage-report missing 不再是空字符串

```bash
GEN=$(rg -l "coverage-report\.yaml" scripts/ plugins/ | head -1)
python3 - <<EOF
src = open('$GEN').read()
bad = ["missing.append('')", 'missing.append("")', "[''] *", '[""] *']
assert not any(p in src for p in bad), "empty-string bug remains"
print("P0-6 OK")
EOF
```

### P0 batch_verify

```bash
cd /Users/didi/work/prd-tools

for f in scripts/*.py; do python3 -m py_compile "$f" || exit 1; done
echo "all scripts compile"

for f in plugins/*/skills/*/references/contracts/*.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" || exit 1
done
echo "all contracts parse"

# 无重复章节（包含 2.5/2.6/8.6 等所有）
for skill in plugins/prd-distill/skills/prd-distill plugins/reference/skills/reference; do
  dup=$(rg "^## 步骤 " "$skill/workflow.md" | sort | uniq -d)
  if [ -n "$dup" ]; then echo "DUPLICATE in $skill:"; echo "$dup"; exit 1; fi
done
echo "no duplicate sections"

echo "=== P0 batch OK ==="
```

---

## P1

### P1-1 workflow.md yaml 块无智能引号

```bash
python3 - <<'EOF'
import re
s = open('plugins/prd-distill/skills/prd-distill/workflow.md').read()
for i, b in enumerate(re.findall(r'```ya?ml\n(.*?)\n```', s, re.DOTALL)):
    for c in '""''':
        assert c not in b, f"smart quote in yaml block {i}"
print("P1-1 OK")
EOF
```

### P1-2 SKILL.md 列出 distill-workflow-gate

```bash
rg -q "distill-workflow-gate" plugins/prd-distill/skills/prd-distill/SKILL.md && echo "P1-2 OK"
```

### P1-3 source_blocks 在 output-contracts

```bash
rg -q "source_blocks" plugins/prd-distill/skills/prd-distill/references/output-contracts.md && \
  ! rg -q "source_blocks.*必填" plugins/prd-distill/skills/prd-distill/workflow.md && echo "P1-3 OK"
```

### P1-4 step-01-parse 编号无重复

```bash
python3 - <<'EOF'
import re
lines = open('plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md').readlines()
seen = {}
for i, l in enumerate(lines, 1):
    m = re.match(r'^(\d+)\. ', l)
    if m:
        n = m.group(1)
        if n in seen: 
            raise AssertionError(f"duplicate step {n} at L{i}, first at L{seen[n]}")
        seen[n] = i
print("P1-4 OK")
EOF
```

### P1-5 step-gate 读 report-confirmation

```bash
rg -q "report-confirmation.yaml" scripts/distill-step-gate.py && echo "P1-5 OK"
```

### P1-6 IR ↔ AI-PRD 编号约束

```bash
rg -q "ai_prd_req_id" plugins/prd-distill/skills/prd-distill/steps/ && \
  rg -q "IR.*AI-friendly PRD|ai-friendly-prd.*REQ" plugins/prd-distill/skills/prd-distill/steps/ && echo "P1-6 OK"
```

### P1-7 h2 阈值对齐

```bash
python3 -c "import yaml; c=yaml.safe_load(open('plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml')); assert c.get('min_h2')==13; print('P1-7 contract OK')"
rg -n "h2" scripts/distill-quality-gate.py | head
# 目视确认 quality-gate 阈值对齐 (13 warn, <8 fail)
```

### P1-8 Self-Check 标记

```bash
rg -c "\[M\]|\[H\]" plugins/prd-distill/skills/prd-distill/steps/ plugins/reference/skills/reference/steps/
test -f scripts/selfcheck-runner.py && python3 -m py_compile scripts/selfcheck-runner.py && echo "P1-8 OK"
```

### P1-9 fix_hint

```bash
test -f scripts/_gate_fixhint.py && \
  rg -q "fix_hint" scripts/distill-workflow-gate.py && \
  rg -q "fix_hint" scripts/reference-step-gate.py && echo "P1-9 OK"
```

### P1-10 overall_score 公式

```bash
rg -q "overall_score" plugins/prd-distill/skills/prd-distill/references/output-contracts.md && \
  rg -q "weighted_section_avg|penalty" plugins/prd-distill/skills/prd-distill/references/output-contracts.md && echo "P1-10 OK"
```

### P1 batch_verify

```bash
cd /Users/didi/work/prd-tools
bash -c '
for check in P1-1 P1-2 P1-3 P1-4 P1-5 P1-6 P1-7 P1-8 P1-9 P1-10; do
  echo "--- $check ---"
done
' # 跑上面每个 minimal_verify
```

---

## P2

（P2 是可选，每个 FIX 的 verify 在 `P2-fixes.md` 各自章节里。）

---

## regression_verify（全部做完后）

```bash
cd /Users/didi/work/prd-tools

# 1. 跑 selfcheck 工具（一次性做完所有上面的检查 + 额外的交叉检查）
python3 tools/selfcheck/run.py --all

# 2. 跑一次 hypothetical /prd-distill 的 dry-run（如果 selfcheck 支持 gate 离线验证）
python3 scripts/distill-workflow-gate.py \
  --distill-dir /Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot \
  --repo-root /Users/didi/work/dive-bff

# 3. 统计改动量
git diff --stat main..HEAD
```

---

## 验收报告模板

做完后产出 `docs/audit/v2.18.1/report.md`，格式：

```markdown
# v2.18.1 审计修复报告

## 摘要
- P0: 6/6 通过
- P1: X/10 通过（跳过: P1-Y 原因）
- P2: X/11 通过（跳过: P2-Y 原因）

## 证据

### P0-1 `distill-workflow-gate.py` import yaml
- commit: <sha>
- verify 输出:
  ```
  exit=0
  ```

### P0-2 ...

[每个 FIX 一段，贴 verify 命令输出]

## 不完成 / 跳过说明

- P1-8 只完成了 tagging，selfcheck-runner.py 是 stub — 完整实现留到下个 milestone
- P2-7 选方式 A 补 Phase 3.6 — 内容参考 references/critique-template.md
- ...

## 后续建议
（可选：执行过程中发现的新问题）
```
