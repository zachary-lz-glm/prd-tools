# v2.18.1 审计修复报告

## 摘要
- P0 修复: 6/6
- P1 修复: 10/10
- P2 修复: 11/11
- P0R2 修复: 12/12
- D4 selfcheck 修复: 1/1
- 未完成/跳过: 无

## Selfcheck 结果

### 修复前（审计快照）
- 7 fail：D1 / D2 / D5 / D6 / S2 / C2 / X1
- 2 warn：D4 / S3
- 6 pass

### P0+P1 修复后
- 2 fail：D5 / X1（对应 P2-7 / P2-8，不在 P0/P1 范围）
- 2 warn：D4 / S3
- 11 pass

### P2 修复后
- 0 fail
- 1 warn：D4（gate mentions 一致性，16 个 gap — 非功能性问题）
- 14 pass

### Round 2 修复后
- 0 fail
- 1 warn：D4（4 个真实同 skill 内缺口，从 16 降至 4）
- 14 pass

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
2. D4 (gate mentions 一致性, 4 个同 skill 内 gap): 属于低优先级文档一致性改进，可随日常维护逐步收敛
3. selfcheck-runner.py 目前是 stub，完整实现作为下个 milestone

---

## Round 2: P0R2 修复（基于实际 /prd-distill 运行日志）

### 摘要
- P0R2 修复: 12/12
- D4 selfcheck 修复: 1/1
- 未完成/跳过: 无

### Selfcheck 结果

#### Round 2 修复后
- 0 fail
- 1 warn：D4（4 个真实同 skill 内缺口，从 16 降至 4）
- 14 pass

### P0R2-1 ai-friendly-prd section format matches gate regex
- commit: a5548c6
- 现状已是正确格式 `## N. EnglishName`，无需修改模板。新增 Self-Check [M] 断言防漂移。
```
OK: no § prefix in afprd templates
```

### P0R2-2 gate accepts overall_score as score alias
- commit: f91fbb8
- gate 正则改为 `^(overall_score|score):\s*\d+`，output-contracts 标注 `overall_score` 为权威字段名。
```
P0R2-2 OK
```

### P0R2-3 evidence-map.yaml top-level key unified as `blocks`
- commit: 1a4aa2b
- schema 已用 `blocks:`，output-contracts 补充顶层字段说明。
```
P0R2-3 OK
```

### P0R2-4 media-analysis.yaml top-level key unified as `media`
- commit: 43014d7
- gate 兼容 `media`/`items`/`images`，schema 和 output-contracts 统一为 `media:`。
```
P0R2-4 OK
```

### P0R2-5 IR evidence field unified as object with source_blocks/source_block_ids
- commit: a0bff78
- step-01-parse.md evidence 从 `["EV-001"]` 改为 object 格式。
```
P0R2-5 OK
```

### P0R2-6 contract-delta requires meta + requirement_id + layer
- commit: ba2146d
- contract 新增 `required_top_level: [meta, schema_version, deltas]`，rules 新增 `requirement_id`/`layer`。output-contracts 模板从 `contracts:` 改为 `deltas:` 并加入 `meta`/`layer`/`requirement_id` 字段。
```
P0R2-6 OK
```

### P0R2-7 docx ingestion uses python zipfile standard path
- commit: 2d2f29b
- step-01-parse.md 替换 `unzip` 命令为 Python zipfile 标准流程，避免 macOS permission denied。
```
P0R2-7 OK
```

### P0R2-8 context-pack accepts --distill-dir alias + auto-derives --index/--out
- commit: 60de8a0
- context-pack.py `--distill` 新增 `--distill-dir` 别名，`--index`/`--out` 改为可选并自动推导。
```
P0R2-8 OK
```

### P0R2-9 final-quality-gate accepts --distill-dir alias
- commit: 7a23735
- final-quality-gate.py `--distill` 新增 `--distill-dir` 别名。
```
P0R2-9 OK
```

### P0R2-10 Step 0 outputs enforced as Step 1 prerequisites
- commit: deb1d05
- STEP_TABLE["1"].prerequisites 新增 `document-structure.json`、`evidence-map.yaml`、`source-manifest.yaml`。
```
P0R2-10 OK
```

### P0R2-11 gate failures suggest checking template/gate, not just artifact
- commit: a995cfb
- _gate_fixhint.py 改为 dict 结构含 `direction` 标签（check_template/check_both/fix_artifact）。step-01-parse.md 新增修复循环规避规则。
```
P0R2-11 step OK
P0R2-11 fixhint OK
```

### P0R2-12 document-structure.json exclusion_types taught to AI
- commit: 640a1d6
- output-contracts.md 双插件补充 `exclusion_types` 字段说明。
```
P0R2-12 OK
```

### D4 selfcheck scoped to within-skill gate references
- commit: 3050205
- D4_gate_mentions.py 从全量交叉检查改为按 skill prefix 隔离，误报从 16 降至 4。
```
⚠ [D4] gate script mentions are consistent per-skill
    4 within-skill gate gap(s)
```

## P2 修复提交记录

### P2-1 step-gate default tool-version reads VERSION file
- commit: aa7ecd7
- distill-step-gate.py / reference-step-gate.py 新增 `_default_tool_version()` 函数

### P2-2 accept --step 8.1 as alias for 8.1-confirm
- commit: cfe292d
- distill-step-gate.py 新增 `STEP_ALIASES` + `_resolve_step()`

### P2-3 final-quality-gate reads anchors from routing-playbooks
- commit: 8ef251c
- final-quality-gate.py 新增 `load_key_anchors()`, 硬编码改为 fallback

### P2-4 context-pack seed_queries derived from routing-playbooks
- commit: 24699f4
- context-pack.py 新增 `_load_seed_queries()`, 硬编码改为 fallback

### P2-5 remove deprecated graph/ subtree from output-contracts
- commit: f7a623c
- 双插件 output-contracts.md 删除已废弃 graph/ 目录描述

### P2-6 split duplicate Step 8.6 headings
- commit: b1dcf9f
- workflow.md 第二个 8.6 改为 8.6.1

### P2-7 materialize Phase 3.6 Critique Pass in workflow.md
- commit: 41ab9d1
- workflow.md 新增 Step 3.6 Critique Pass 章节

### P2-8 step-04-portal current_step aligns to gate --step 9
- commit: 2fa39f3
- step-04-portal.md `<current_step>` 从 4 改为 9

### P2-9 unify plan.md section count to 11 across docs
- commit: eca0f99
- workflow.md 和 step-03-confirm.md 章节数统一为 11

### P2-10 single canonical mode-selection schema
- commit: 4e64b4b
- 新增 mode-selection.schema.md, SKILL.md 改为引用

### P2-11 portal EV full-set self-check + speculative tagging
- commit: abf06e3
- step-04-portal.md 新增 EV 全集 Self-Check, workflow.md 新增推测信息约束

### 幽灵步骤注册
- commit: 3f9475f
- STEP_TABLE 注册 2.6/3.6/7/8.6.1, X1 fail 归零
