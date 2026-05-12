# 验证命令清单

## minimal_verify（每个 FIX 完成后运行）

### P0
```bash
# P0-1: 无重复 blocked_reason
grep -c "blocked_reason" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### P1
```bash
# P1-1: primary_source 在 schema 中
grep "primary_source" plugins/prd-distill/skills/prd-distill/references/output-contracts.md

# P1-2: output-contracts layer-impact 无旧 impacts
grep "impacts" plugins/prd-distill/skills/prd-distill/references/output-contracts.md | grep -i layer

# P1-3: reference mode descriptions aligned
grep "health check\|quality gate" plugins/reference/skills/reference/SKILL.md

# P1-4: 3.6 in execution order
grep "3.6" .claude/commands/prd-distill.md | grep -v "Step IDs"

# P1-5: SKILL.md report stage has 3.5
grep "2.5.*3.1.*3.2.*3.5" plugins/prd-distill/skills/prd-distill/SKILL.md

# P1-6: SKILL.md plan stage has 7
grep "5.*6.*7.*8.5.*8.6.*9" plugins/prd-distill/skills/prd-distill/SKILL.md

# P1-7: SKILL.md blocker references use §12
grep -n "§11" plugins/prd-distill/skills/prd-distill/SKILL.md

# P1-8: output-contracts evidence uses type/desc
grep "kind:" plugins/prd-distill/skills/prd-distill/references/output-contracts.md | grep -i "prd\|tech_doc\|code"
```

## batch_verify（每个优先级批次完成后运行）

```bash
# 双插件 output-contracts 同步
diff plugins/prd-distill/skills/prd-distill/references/output-contracts.md plugins/reference/skills/reference/references/output-contracts.md

# gate 脚本编译
python3 -c "import py_compile; py_compile.compile('scripts/distill-step-gate.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('scripts/distill-quality-gate.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('scripts/distill-workflow-gate.py', doraise=True)"
```

## regression_verify（全部完成后运行）

```bash
python3 tools/selfcheck/run.py --all --format json
```
