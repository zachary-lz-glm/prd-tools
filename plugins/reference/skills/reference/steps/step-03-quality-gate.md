<workflow_state>
  <workflow>reference</workflow>
  <current_step>4</current_step>
  <allowed_inputs>_prd-tools/reference/ (all files), source code</allowed_inputs>
  <must_not_read_by_default>_prd-tools/distill/</must_not_read_by_default>
  <must_not_produce>_prd-tools/reference/01-codebase.yaml (modification)</must_not_produce>
</workflow_state>

## MUST NOT

- MUST verify ALL prerequisite files exist and are non-empty before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if any prerequisite file is missing

# 步骤 4：质量门控

## 目标

验证 `_prd-tools/reference/` 对 `/prd-distill` 是否有用、够新、可安全使用。

## 检查项

致命项：

- v4 reference 文件缺失（至少需要 01~05 中的 3 个）。
- entity、route、contract 或 playbook 没有 evidence。
- 引用的文件路径不存在。
- enum/field/contract 与源码或文档冲突。
- 多层契约面缺少 contract 条目。
- 影响业务结果的校验只在前端，且没有明确授权。
- 跨文件重复：同一事实（如字段定义、编码规则）出现在多个文件中且措辞矛盾。
- 所有 contracts[].producer 不是字符串单值 → fail
- 所有 contracts[].consumers 不是数组或长度 < 1 → fail
- 所有 contracts[].checked_by 不是数组 → fail

警告项：

- `last_verified + verify_cadence` 已过期。
- 05-domain 术语缺少常见 PRD 同义词。
- playbook 缺少 QA 矩阵。
- golden sample 缺少变更文件或 contract 引用。
- 路由条目缺少 playbook_ref。
- 存在旧版 v3.1 文件（00~09），但没有 v4 迁移建议。
- 使用了 `direction:` 字段的契约需重写为 producer/consumers[]
- 跨仓契约（consumers 含非当前仓角色）未填 consumer_repos
- 每个 prd_routing[] 条目缺少 handoff_surfaces 字段 → warn
- 跨层 PRD 但 handoff_surfaces 为空 → warn（必须填）
- 每个 playbook[].layer_steps 缺少 frontend/bff/backend 三个 key → fail

## 边界检查

验证以下跨文件边界：

1. 01-codebase 中不应出现字段级 type/required 信息（应引用 03-contracts）。
2. 02-coding-rules 中不应出现场景驱动的开发步骤（应在 04-routing-playbooks）。
3. 03-contracts 中不应出现编码规则（应在 02-coding-rules）。
4. 04-routing-playbooks 的路由条目不应包含实现步骤（步骤只在 playbook 中）。
5. 05-domain 的术语不应与 01-codebase 的枚举 label 重复。重复时应用 `see_enum:` 引用。

## 输出

```yaml
status: "pass | warning | fail"
score: 0
fatal_findings: []
warnings: []
boundary_violations: []
adapter_gate_results: []
sample_replay:
  sample_id: ""
  passed: false
  gaps: []
next_actions: []
```

存在致命发现时，不要宣称 reference 已可用于生产。

## Self-Check（质量检查后必须逐项验证）

> **Self-Check 的两种条目**：本清单同时包含 (a) **机器可验证断言**（标 `[M]`）和 (b) **人工判读提示**（标 `[H]`）。执行 Self-Check 时：
> - `[M]` 条目必须逐条列出 `verify: <命令>` 与 `expect: <结果>`，未通过不得进下一步。
> - `[H]` 条目作为判读提示，LLM 自检后必须写入 workflow-state.yaml 的 `self_check_notes[step_id]` 数组，内容为"我为什么认为这条满足"的简短解释。

- [ ] [H] quality-report.yaml 的 score 是根据实际检查结果计算，不是估算
- [ ] [M] 每个 fatal_finding 都有具体的 reference 文件和证据引用
- [ ] [M] boundary_violations 列出了具体的重叠内容和建议修复方式
- [ ] [M] sample_replay 已执行（如有 golden sample）
- [ ] [H] 幻觉检查覆盖了所有文件路径、函数名、变量名
