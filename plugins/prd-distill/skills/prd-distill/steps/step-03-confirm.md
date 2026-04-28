# 步骤 3：计划、报告与反馈

## 目标

生成：

- `_output/prd-distill/<slug>/report.md`
- `_output/prd-distill/<slug>/plan.md`
- `_output/prd-distill/<slug>/questions.md`
- `_output/prd-distill/<slug>/artifacts/reference-update-suggestions.yaml`

## 合并计划

`plan.md` 合并开发、QA 和契约对齐计划，按命中的层分组：

- 前端任务
- BFF 任务
- 后端任务
- 契约对齐任务
- 开放问题和风险
- 建议实现顺序
- QA 矩阵和回归重点

每个任务引用 `REQ-*`、`IMP-*` 或 `CONTRACT-*`。

QA 部分包含：

- Requirement 验收矩阵
- 分层单元/集成检查
- 契约测试
- 回归流程
- 边界和反向用例
- 人工验收清单

每个 QA 用例引用 `REQ-*` 或 `CONTRACT-*`。

## 确认

生成 `questions.md`：

- 展示所有 `medium` 和 `low` confidence 项。
- 展示 `needs_confirmation` 或 `blocked` 的 Contract Delta。
- 展示 reference 矛盾和迁移建议。
- 标注建议 owner、所需证据和当前默认策略。

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

`report.md` 汇总，优先一屏可读：

1. 需求摘要
2. 命中的层和能力面
3. 关键开发结论
4. 契约风险和阻塞项
5. Top open questions
6. `plan.md` 和 `artifacts/` 索引
