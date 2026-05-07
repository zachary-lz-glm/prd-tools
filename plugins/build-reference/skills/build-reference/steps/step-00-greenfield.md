# 步骤 0G：绿地 Reference

仅在目标项目没有代码或代码很少时使用。

## 目标

基于 PRD、兄弟项目模式和上游 API 文档创建 reference v3。

## 输入

- PRD 路径或粘贴文本。
- 可选兄弟项目路径。
- 可选上游 API/技术方案路径。

## 输出

使用 v3 templates 生成 `_prd-tools/reference/00~09`：

- 来自 PRD 的事实：`kind: prd`，`confidence: medium | low`
- 来自兄弟项目的模式：`kind: reference`，`confidence: medium`
- 未验证实现事实：`implemented: false`
- 未知项：`TODO`，`confidence: low`，`needs_domain_expert: true`

## 规则

- 没有代码时，不要声称有代码证据。
- 预期 API/schema 契约面写入 `08-contracts.yaml`。
- 开发假设和 QA 矩阵写入 `09-playbooks.yaml`。
- 每个生成的假设都必须成为开放问题或低置信度条目。
