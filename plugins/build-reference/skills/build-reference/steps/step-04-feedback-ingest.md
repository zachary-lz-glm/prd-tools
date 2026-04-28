# 步骤 4：反馈回流

## 目标

在人工确认后，使用 `/prd-distill` 的输出改进 `_reference/`。

## 输入

- `_output/prd-distill/**/artifacts/reference-update-suggestions.yaml`
- `_output/prd-distill/**/report.md`
- 兼容旧版：`_output/prd-distill/**/reference-update-suggestions.yaml`、`_output/prd-distill/**/distilled-report.md`
- 当前 `_reference/`
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
2. 用当前源码或文档重新检查 evidence。
3. 对矛盾项，展示当前 reference 事实、新证据和修复建议。
4. 让用户逐条批准、编辑或跳过。
5. 只应用用户确认过的变更。
6. 更新 `last_verified`。
7. 写入 `_output/feedback-ingest-report.yaml`。

## 规则

- 不应用推测性更新。
- 不覆盖无关 reference 内容。
- 不自动删除旧版文件。
- 每个已应用更新都必须有 evidence。
