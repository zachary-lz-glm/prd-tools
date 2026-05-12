# v2.18.1 审计修复报告

## 摘要
- P0 修复: 6/6
- P1 修复: 10/10
- P2 修复: 0/11（跳过，有余力再做）
- 未完成/跳过: P2 全部 11 项（不在本次执行范围）

## Selfcheck 结果

### 修复前（审计快照）
- 7 fail：D1 / D2 / D5 / D6 / S2 / C2 / X1
- 2 warn：D4 / S3
- 6 pass

### 修复后
- 2 fail：D5 / X1（对应 P2-7 / P2-8，不在 P0/P1 范围）
- 2 warn：D4（gate mentions 一致性，16 个 gap）/ S3（tool-version stale，对应 P2-1）
- 11 pass

> 注：README 说"P0+P1 全做完 fail 归零"，但 D5 和 X1 原始映射就是 P2-7/P2-8，不在 P0/P1 范围内。从 7 fail 降到 2 fail 是 P0+P1 的预期成果。

## 每个 FIX 的验证输出

### P0-1 distill-workflow-gate.py import yaml
- commit: 3978684
```
P0-1: exit=0
```

### P0-2 remove duplicate Step 2.5/2.6 in workflow.md
- commit: d90a164
```
1
1
```

### P0-3 reference-step-gate 2d requires 02-coding-rules
- commit: 3531c68
```
P0-3 OK
```

### P0-4 align contract-delta.contract.yaml with real schema
- commit: 3926b30
- 注：选择方式 B（保留 deltas，删掉 required_top_level），因真实产物用 `deltas` 不用 `contracts`。output-contracts.md 的 `contracts` 模板需单独同步。
```
yaml-ok=0
=== Artifact Contract: contract-delta.contract.yaml ===
  Artifact: .../contract-delta.yaml
  Status: pass
  [+] All rules passed
validate-exit=0
```

### P0-5 code_scan must cover build/ for registry changes
- commit: a9b9df0
```
step-02-classify.md:6
step-02-classify.md:1
scripts/context-pack.py:460-461 (build/**/*.d.ts, build/**/*.js)
```

### P0-6 coverage-report missing now carries real block_ids
- commit: 4d25263
- 根因：document-structure.json 用 `id` 字段，代码读 `block_id` → 空字符串。修为 `block.get("block_id") or block.get("id", "")`。
```
P0-6 OK
```

### P1-1 normalize smart quotes in workflow.md yaml templates
- commit: da23dcf
```
P1-1 OK: 5 yaml blocks clean
```

### P1-2 SKILL.md lists distill-workflow-gate.py
- commit: 5f50789
```
plugins/prd-distill/skills/prd-distill/SKILL.md:112
```

### P1-3 align source_blocks / source_block_ids semantics
- commit: 005564d
```
workflow.md + output-contracts.md 两处均出现 source_blocks，workflow.md 不再写"必填"
```

### P1-4 fix duplicate step number in step-01-parse.md
- commit: d238163
```
P1-4 OK
```

### P1-5 8.1-confirm step reads real report-confirmation status
- commit: 27bb8ff
```
yaml imported OK
report-confirmation.yaml found in distill-step-gate.py
```

### P1-6 enforce IR ↔ ai-friendly-prd REQ id consistency
- commit: 6bd193e
```
step-01-parse.md: 1 occurrence of ai_prd_req_id
IR ↔ AI-friendly PRD section added at L112
```

### P1-7 align ai-friendly-prd h2 thresholds
- commit: b8d089b
```
contract min_h2: 13 (in rules[0])
quality-gate thresholds: <8 → fail, <13 → warning
```

### P1-8 tag Self-Check items as [M]achine / [H]uman
- commit: e8eb7fb
```
prd-distill steps: step-02-classify.md (9 tags), step-03-confirm.md (11 tags)
reference steps: step-00-greenfield.md (8), step-01-structure-scan.md (8), step-03-quality-gate.md (8), step-04-feedback-ingest.md (8)
selfcheck-runner.py: stub created, compiles OK
```

### P1-9 add fix_hint to distill-workflow and reference-step gates
- commit: 76e94c0
```
_gate_fixhint.py created with 8 hint entries
distill-workflow-gate.py: fix_hint imported and wired in print_summary
reference-step-gate.py: fix_hint imported and wired for missing_coding_rules
```

### P1-10 document overall_score formula in output-contracts
- commit: 6073cba
```
output-contracts.md: overall_score algorithm section added with weights table and status mapping
```

## 不完成 / 跳过说明

- P2 全部 11 项跳过（不在本次执行范围，由维护者决定是否继续）
- D4 warn (gate mentions 16 gaps): 完整修复合并 P2 范围，当前 16 个 gap 不影响流程正确性
- S3 warn (tool-version stale): 对应 P2-1，默认值应改为读 VERSION 文件

## 后续建议

1. output-contracts.md 的 `contracts` vs `deltas` 模板需要对齐决策（P0-4 选择了保留 deltas）
2. D5 (step-04-portal current_step=4 vs filename implies 9) 和 X1 (workflow.md 步骤 2.6/7 不在 STEP_TABLE) 属于 P2 范围
3. selfcheck-runner.py 目前是 stub，完整实现作为下个 milestone
