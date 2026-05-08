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

## 图谱证据检查

1. 如果 `_prd-tools/build/graph/sync-report.yaml` 存在且任一 provider `available: true`：
   a. 至少一个 reference 文件的条目有非空 `graph_sources` 和非空 `graph_evidence_refs`。
   b. 所有 `graph_evidence_refs` 中引用的 GEV / GEV-B ID 都能在 `_prd-tools/build/graph/` 对应文件中找到。
   c. `project-profile.yaml` 的 `graph_providers` 与 `graph-sync-report` 的 `available` 状态一致。
   d. 每个有图谱支撑的 reference 文件（01-05）的 `graph_providers` 字段已正确填写。
2. 如果 `_prd-tools/build/graph/sync-report.yaml` 不存在：
   a. 所有 reference 条目的 `graph_sources` 应为 `[]`。
   b. 不报为错误，但记为警告："图谱证据未生成，reference 完全基于源码扫描"。
3. 图谱置信度校验：
   a. GitNexus `confidence: high` 的结构发现（模块、符号、调用链）不需要额外源码确认。
   b. Graphify `EXTRACTED` 且有 source locator 的条目可标 `confidence: high`；无 locator 的 `EXTRACTED` 标 `medium`。
   c. Graphify `INFERRED` 的 medium/low 条目，其关联的 reference 条目应有对应的 EV-xxx 源码确认证据。
   d. Graphify `AMBIGUOUS` 条目不应直接进入 reference，需人工确认。

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
graph_evidence_check:
  providers_available: []
  reference_files_with_graph_data: []
  orphan_graph_refs: []
  unconfirmed_medium_low: []
  graph_sync_report_exists: true|false
adapter_gate_results: []
sample_replay:
  sample_id: ""
  passed: false
  gaps: []
next_actions: []
```

存在致命发现时，不要宣称 reference 已可用于生产。
