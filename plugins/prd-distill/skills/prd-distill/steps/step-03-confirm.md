# 步骤 3：计划、报告与反馈

## 目标

生成：

- `_output/prd-distill/<slug>/dev-plan.md`
- `_output/prd-distill/<slug>/qa-plan.md`
- `_output/prd-distill/<slug>/reference-update-suggestions.yaml`
- `_output/prd-distill/<slug>/distilled-report.md`

## 开发计划

按层分组：

- 前端任务
- BFF 任务
- 后端任务
- 契约对齐任务
- 开放问题和风险
- 建议实现顺序

每个任务引用 `REQ-*`、`IMP-*` 或 `CONTRACT-*`。

## QA 计划

包含：

- Requirement 验收矩阵
- 分层单元/集成检查
- 契约测试
- 回归流程
- 边界和反向用例
- 人工验收清单

每个 QA 用例引用 `REQ-*` 或 `CONTRACT-*`。

## 确认

最终报告前：

- 展示所有 `medium` 和 `low` confidence 项。
- 展示 `needs_confirmation` 或 `blocked` 的 Contract Delta。
- 展示 reference 矛盾和迁移建议。
- 让用户确认或修正阻塞项。

## Reference 回流

生成以下建议：

- 新术语
- 新路由
- 新契约
- 新 playbook
- golden sample 候选
- reference 与代码的矛盾

`/prd-distill` 不直接编辑 `_reference/`；实际修改交给 `/build-reference` 的反馈回流。

## 最终报告

`distilled-report.md` 汇总：

1. Requirement IR
2. Layer Impact
3. Contract Delta
4. 开发计划
5. QA 计划
6. 阻塞问题
7. Reference 回流建议
