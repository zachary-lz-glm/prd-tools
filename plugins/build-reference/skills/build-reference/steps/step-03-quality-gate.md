# 步骤 3：质量门控

## 目标

验证 `_reference/` 对 `/prd-distill` 是否有用、够新、可安全使用。

## 检查项

致命项：

- v3 reference 文件缺失。
- entity、route、contract 或 playbook 没有 evidence。
- 引用的文件路径不存在。
- enum/field/contract 与源码或文档冲突。
- 多层契约面缺少 contract 条目。
- 影响业务结果的校验只在前端，且没有明确授权。

警告项：

- `last_verified + verify_cadence` 已过期。
- glossary 缺少常见 PRD 同义词。
- playbook 缺少 QA 矩阵。
- golden sample 缺少变更文件或 contract 引用。
- 存在旧版 `05-mapping.yaml`，但没有 v3 迁移建议。

## 输出

```yaml
status: "pass | warning | fail"
score: 0
fatal_findings: []
warnings: []
adapter_gate_results: []
sample_replay:
  sample_id: ""
  passed: false
  gaps: []
next_actions: []
```

存在致命发现时，不要宣称 reference 已可用于生产。
