# P0 修复清单

> **执行原则**：按 P0-1 → 顺序做。每个 FIX 一个独立 commit。

## P0-1 — SKILL.md report-confirmation.yaml 模板有重复 blocked_reason key

### 问题
`SKILL.md:301-302` 的 report-confirmation.yaml 模板中 `blocked_reason: ""` 出现两次。LLM 按此模板生成 YAML 会导致 duplicate key，YAML parser 取最后一个值，可能丢失数据。

### 证据
- `plugins/prd-distill/skills/prd-distill/SKILL.md:301-302` — 两行都是 `blocked_reason: ""`
- `workflow.md:722` — 只有单个 `blocked_reason`

### 修复
1. 删除 `SKILL.md:302` 的重复 `blocked_reason: ""` 行

### verify
```bash
grep -c "blocked_reason" plugins/prd-distill/skills/prd-distill/SKILL.md | grep -q "^1$\|^2$" && echo "Check blocked_reason count in SKILL.md" || echo "OK"
# 预期：SKILL.md 中 blocked_reason 出现恰好 2 次（模板中 1 个 + 正文描述中 1 个）
```

### commit
```
fix(audit-p0): [P0-1] remove duplicate blocked_reason in SKILL.md report-confirmation template
```
