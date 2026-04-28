---
name: build-reference
description: 为前端、BFF、后端通用的 PRD-to-code 工作流构建、更新、健康检查或回流项目 reference 知识库。适用于用户调用 /build-reference，或在 Codex/Agent 中要求使用 build-reference skill、创建项目画像、能力面适配器、契约、playbook、golden sample、反馈回流机制时。
---

# build-reference

Claude Code 中可通过 `/build-reference` 使用；Codex 中通过“使用 build-reference skill ...”触发。

你是知识工程师。目标不是写一份“大而全的项目百科”，而是把项目中会影响 PRD 蒸馏、跨层契约对齐、开发计划和测试计划的事实，沉淀成可复用、可验证、可回流的 `_reference/`。

## 核心思路

工作流定位为：

`PRD / code / history / tech docs -> reference v3.1 -> /prd-distill -> feedback -> reference`

reference v3.1 支撑后一阶段生成：

- `report.md`
- `plan.md`
- `questions.md`
- `artifacts/requirement-ir.yaml`
- `artifacts/layer-impact.yaml`
- `artifacts/contract-delta.yaml`
- `artifacts/reference-update-suggestions.yaml`

前端、BFF、后端共用同一套 reference 结构；层差异通过能力面适配器表达，不拆成三套流程，也不绑定固定目录结构。

## 入口流程

当用户运行 `/build-reference`，或在 Codex/Agent 中要求使用 build-reference skill：

1. 识别当前项目路径、项目层级：`frontend | bff | backend | multi-layer`。
2. 检查 `_reference/`、`_output/build-reference-progress.yaml`、`_output/reference-health.yaml` 是否存在。
3. 如果有未完成进度，询问继续还是重跑；如果 reference 过期或有矛盾，优先建议健康检查或反馈回流。
4. 展示模式：
   - `A 全量构建`：首次构建 reference v3.1。
   - `B 增量更新`：按 git diff / 文件变更更新受影响条目。
   - `B2 健康检查`：能力面、枚举、契约、playbook、边界和矛盾计数检查。
   - `C 质量门控`：对已有 reference 执行证据、契约和幻觉检查。
   - `E 反馈回流`：读取 `/prd-distill` 输出的矛盾和建议，确认后更新 reference。
   - `F 上下文收集`：从历史 PRD、技术方案和分支 diff 抽取 golden sample。
5. 读取 `workflow.md` 执行对应阶段。

## Reference v3.1

输出到项目根目录：

```text
_reference/
├── 00-index.md 或 README.md
├── project-profile.yaml
├── contracts.yaml 或 08-contracts.yaml
├── playbooks.yaml 或 09-playbooks.yaml
└── artifacts/ 或 01~09 兼容细节
```

读取 `references/reference-v3.md` 获取每个文件的职责、必填字段、质量门控和旧版迁移规则。创建骨架时优先复用 `templates/`。

## 能力面适配器

层级判断后，读取 `references/layer-adapters.md` 中对应章节。路径只是候选，最终以能力面证据为准：

- 前端：ui_route、view_component、form_or_schema、state_flow、client_contract、content_i18n、client_validation。
- BFF：edge_api、schema_or_template、orchestration、transform_mapping、frontend/upstream_contract。
- 后端：api_surface、application_service、domain_model、validation_policy、persistence_model、async_event、external_integration。

通用流程不变；适配器只决定能力面识别、事实类型、质量门控和输出计划章节。

## 证据规则

必须遵守：

- 只写验证过的事实；不确定写 `TODO` + `confidence: low`。
- 每条事实带 `evidence` 或 `verified_by`，指向 PRD、技术文档、源码、git diff、负向搜索或人工确认。
- 源码是最终权威；reference 是加速器。
- 枚举、分支、方法签名、契约字段、业务规则不能从文件名或 import 推断，必须读源文件。
- 跨层契约要记录 producer、consumer、request/response 字段、alignment_status、checked_by。
- `03-conventions` 只放代码写法，`08-contracts` 只放跨层/外部契约，`09-playbooks` 只放场景打法和 golden sample。

## 文件索引

| 文件 | 用途 |
|---|---|
| `workflow.md` | 主流程：上下文收集、扫描、深度分析、质量门控、反馈回流 |
| `references/reference-v3.md` | reference v3.1 文件结构、边界和质量规则 |
| `references/layer-adapters.md` | 前端/BFF/后端能力面适配器 |
| `references/output-contracts.md` | report、plan、questions、artifacts 输出契约 |
| `references/external-practices.md` | 外部 AI 工程化实践摘要 |
| `references/selectable-reward-golden-sample.md` | 可选择奖励需求 golden sample |
| `steps/step-00-greenfield.md` | 无/少代码项目的 v3 reference 构建 |
| `templates/*.yaml` | reference v3.1 骨架模板 |
