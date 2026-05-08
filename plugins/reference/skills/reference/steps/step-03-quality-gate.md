# 步骤 3：质量门控

## 目标

验证 `_prd-tools/reference/` 对 `/prd-distill` 是否有用、够新、可安全使用。

## 检查项

致命项：

- v4 reference 文件缺失（至少需要 00-portal.md 和 01~05 中的 3 个）。
- entity、route、contract 或 playbook 没有 evidence。
- 引用的文件路径不存在。
- enum/field/contract 与源码或文档冲突。
- 多层契约面缺少 contract 条目。
- 影响业务结果的校验只在前端，且没有明确授权。
- 跨文件重复：同一事实（如字段定义、编码规则）出现在多个文件中且措辞矛盾。

警告项：

- `last_verified + verify_cadence` 已过期。
- 05-domain 术语缺少常见 PRD 同义词。
- playbook 缺少 QA 矩阵。
- golden sample 缺少变更文件或 contract 引用。
- 路由条目缺少 playbook_ref。
- 存在旧版 v3.1 文件（00~09），但没有 v4 迁移建议。

## 边界检查

验证以下跨文件边界：

1. 01-codebase 中不应出现字段级 type/required 信息（应引用 03-contracts）。
2. 02-coding-rules 中不应出现场景驱动的开发步骤（应在 04-routing-playbooks）。
3. 03-contracts 中不应出现编码规则（应在 02-coding-rules）。
4. 04-routing-playbooks 的路由条目不应包含实现步骤（步骤只在 playbook 中）。
5. 05-domain 的术语不应与 01-codebase 的枚举 label 重复。

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
- [ ] quality-report.yaml 的 score 是根据实际检查结果计算，不是估算
- [ ] 每个 fatal_finding 都有具体的 reference 文件和证据引用
- [ ] boundary_violations 列出了具体的重叠内容和建议修复方式
- [ ] sample_replay 已执行（如有 golden sample）
- [ ] 幻觉检查覆盖了所有文件路径、函数名、变量名
