# 步骤 4：反馈回流

## 目标

在人工确认后，使用 `/prd-distill` 的输出改进 `_prd-tools/reference/`。

## 输入

- `_prd-tools/distill/**/context/reference-update-suggestions.yaml`
- `_prd-tools/distill/**/report.md`
- 兼容旧版：`_prd-tools/distill/**/spec/reference-update-suggestions.yaml`、`_prd-tools/distill/**/reference-update-suggestions.yaml`、`_prd-tools/distill/**/distilled-report.md`
- 当前 `_prd-tools/reference/`
- 当前源码

## 建议类型

- `new_term`
- `new_route`
- `new_contract`
- `new_playbook`
- `golden_sample_candidate`
- `contradiction`

## 执行

1. 收集建议，并按目标 reference 文件分组。
2. 读取 `current_repo_scope`、`owner_to_confirm`、`team_reference_candidate` 和 `team_scope`。
3. 用当前源码或文档重新检查 evidence。
4. 对矛盾项，展示当前 reference 事实、新证据和修复建议。
5. 让用户逐条批准、编辑或跳过。
6. 只应用用户确认过的变更。
7. 更新 `last_verified`。
8. 写入 `_prd-tools/build/feedback-report.yaml`。

## 规则

- 不应用推测性更新。
- 不覆盖无关 reference 内容。
- 不自动删除旧版文件。
- 每个已应用更新都必须有 evidence。
- `current_repo_scope.action: apply_to_current_repo` 且 evidence 可验证时，才允许写入当前仓 confirmed 事实。
- `record_as_signal` 或 `needs_owner_confirmation` 只能写入 handoff、unknowns、owner_to_confirm 或候选字段，不能升级为确定契约。
- `team_reference_candidate: true` 必须保留为候选标记；除非用户明确确认团队治理结果，否则不代表已经同步到团队知识库。

## Self-Check（回流后必须逐项验证）
- [ ] 每条 suggestion 的 target_file 是存在的 reference 文件
- [ ] apply_to_current_repo 的建议有当前仓源码证据支撑
- [ ] needs_owner_confirmation 的建议填写了 owner_to_confirm
- [ ] golden_sample_candidate 的建议有完整的 lessons 和 evidence
- [ ] 用户确认后才修改 reference，未自动修改
