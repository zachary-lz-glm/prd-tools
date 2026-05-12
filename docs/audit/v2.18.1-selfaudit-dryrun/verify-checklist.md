# 验证清单

> 三类验证：
> - **minimal_verify**：单个 FIX 改完立即跑
> - **batch_verify**：一批全做完跑
> - **regression_verify**：全做完后跑完整自检

## P0

### P0-1 contract-delta 03-context.md sync
```bash
grep -n "contracts:" plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md && echo "FAIL" || echo "OK"
```

### P0-2 report.md section count unified
```bash
grep -c "PRD 质量摘要" plugins/prd-distill/skills/prd-distill/references/output-contracts.md plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
```

### P0-3 step-03 report-confirmation hard stop
```bash
grep -c "HARD STOP\|report-confirmation" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
```

### P0-4 step file mapping table
```bash
grep -A6 "Step 文件.*Gate Step ID" plugins/prd-distill/skills/prd-distill/workflow.md | head -8
```

### P0-5 step 2.6 renamed to 3.5
```bash
grep "3.5" .claude/commands/prd-distill.md scripts/distill-step-gate.py plugins/prd-distill/skills/prd-distill/workflow.md
```

### P0-6 REQ-ID anchor enforcement
```bash
grep "REQ-ID.*标题\|标题.*REQ-XXX\|heading.*anchor" plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md plugins/prd-distill/skills/prd-distill/workflow.md
```

## P1

### P1-1 requirement-ir input alignment
```bash
grep -n "主输入" plugins/prd-distill/skills/prd-distill/workflow.md | head -5
```

### P1-2 layer-impact contract capability_areas
```bash
grep "capability_areas\|impacts" plugins/prd-distill/skills/prd-distill/references/contracts/layer-impact.contract.yaml
```

### P1-3 plan.md length unified
```bash
grep "300-600" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md && echo "FAIL" || echo "OK"
```

### P1-4 step 3.6 critique in command
```bash
grep "3.6" .claude/commands/prd-distill.md
```

### P1-5 step 7 in plan stage
```bash
grep -A2 "plan:" .claude/commands/prd-distill.md
```

### P1-6 step numbering caveat
```bash
grep "logical IDs\|NOT execution order" plugins/prd-distill/skills/prd-distill/workflow.md
```

### P1-7 step-01 must_not_produce fix
```bash
grep "must_not_produce" plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md | grep "requirement-ir" && echo "FAIL" || echo "OK"
```

### P1-8 query-plan script-generated note
```bash
grep "script-generated\|脚本生成" plugins/prd-distill/skills/prd-distill/workflow.md
```

### P1-9 revision_requests structure
```bash
grep -A3 "revision_requests" plugins/prd-distill/skills/prd-distill/SKILL.md
```

### P1-10 readiness field unified
```bash
grep "plan_quality" plugins/prd-distill/skills/prd-distill/references/schemas/05-readiness.md plugins/prd-distill/skills/prd-distill/references/output-contracts.md && echo "FAIL" || echo "OK"
```

### P1-11 gate severity unified
```bash
grep -n "has_code_anchors\|has_fallback" scripts/distill-quality-gate.py scripts/distill-workflow-gate.py
```

### P1-12 project-profile fallback
```bash
grep "fallback\|不存在" plugins/prd-distill/skills/prd-distill/steps/step-02-classify.md
```

### P1-13 per-step loading guidance
```bash
grep "per-step\|不需要全文\|段落加载" plugins/prd-distill/skills/prd-distill/workflow.md
```

## P2

(verify commands in P2-fixes.md — lower priority, run individually)

## Regression
```bash
python3 tools/selfcheck/run.py --all
```
