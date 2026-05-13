<workflow_state>
  <workflow>reference</workflow>
  <current_step>0</current_step>
  <allowed_inputs>project directory, user requirements, sibling project patterns</allowed_inputs>
  <must_not_read_by_default>_prd-tools/reference/ (does not exist yet)</must_not_read_by_default>
  <must_not_produce>_prd-tools/distill/ outputs</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

# 步骤 0G：绿地 Reference

仅在目标项目没有代码或代码很少时使用。

## 目标

基于 PRD、兄弟项目模式和上游 API 文档创建 reference v4.0。

## 输入

- PRD 路径或粘贴文本。
- 可选兄弟项目路径。
- 可选上游 API/技术方案路径。
- `references/layer-adapters.md` 中当前层章节。
- `templates/` 下的 v4 模板。

## 输出

使用 v4 模板生成 `_prd-tools/reference/`：

```text
project-profile.yaml        # 项目画像（layer 标注 greenfield）
01-codebase.yaml            # 预期目录结构、枚举、模块
02-coding-rules.yaml        # 来自兄弟项目的编码规则
03-contracts.yaml           # 预期 API/schema 契约面
04-routing-playbooks.yaml   # PRD 路由信号 + 开发假设 + QA 矩阵
05-domain.yaml              # PRD 领域概念和术语
```

证据规则：

- 来自 PRD 的事实：`kind: prd`，`confidence: medium | low`
- 来自兄弟项目的模式：`kind: reference`，`confidence: medium`
- 未验证实现事实：`implemented: false`
- 未知项：`TODO`，`confidence: low`，`needs_domain_expert: true`

## 规则

- 没有代码时，不要声称有代码证据。
- 预期 API/schema 契约面写入 `03-contracts.yaml`。
- 开发假设和 QA 矩阵写入 `04-routing-playbooks.yaml`。
- 术语和领域概念写入 `05-domain.yaml`。
- 每个生成的假设都必须成为开放问题或低置信度条目。
- `project-profile.yaml` 的 `reference_scope` 标注 `greenfield: true`。

## Self-Check（生成后必须逐项验证）

> **Self-Check 的两种条目**：本清单同时包含 (a) **机器可验证断言**（标 `[M]`）和 (b) **人工判读提示**（标 `[H]`）。执行 Self-Check 时：
> - `[M]` 条目必须逐条列出 `verify: <命令>` 与 `expect: <结果>`，未通过不得进下一步。
> - `[H]` 条目作为判读提示，LLM 自检后必须写入 workflow-state.yaml 的 `self_check_notes[step_id]` 数组，内容为"我为什么认为这条满足"的简短解释。

- [ ] [H] project-profile.yaml 的 layer 字段与项目预期架构一致
- [ ] [M] 01-codebase.yaml 标注了 `implemented: false`（因为没有源码）
- [ ] [H] 03-contracts.yaml 的预期契约面有 PRD 或上游 API 文档证据
- [ ] [M] 04-routing-playbooks.yaml 的 playbook 步骤标注了 `confidence: low`
- [ ] [M] 每个 confidence: low 的条目在 open_questions 中有对应问题
