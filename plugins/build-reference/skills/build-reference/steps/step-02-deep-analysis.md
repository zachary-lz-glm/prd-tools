# 步骤 2：深度分析

## 目标

生成 reference v3.1：

```text
_reference/00-index.md
_reference/project-profile.yaml
_reference/01-entities.yaml
_reference/02-architecture.yaml
_reference/03-conventions.yaml
_reference/04-constraints.yaml
_reference/05-routing.yaml
_reference/06-glossary.yaml
_reference/07-business-context.yaml
_reference/08-contracts.yaml
_reference/09-playbooks.yaml
```

## 输入

- `_output/modules-index.yaml`
- `_output/context-enrichment.yaml`，如存在
- `references/reference-v3.md`
- `references/layer-adapters.md`
- `references/output-contracts.md`
- `templates/` 下的模板

## 执行

1. 为分析过程中发现的事实建立 evidence 台账。
2. 提取实体：枚举、字段、组件、API、领域对象、validator、integration。
3. 提取项目画像和架构：能力面、入口、数据流、注册点、依赖枢纽、third rails、heatmap。
4. 提取契约：producer、consumers、契约面、字段、兼容性、对齐状态。
5. 提取路由：PRD 信号如何映射到 Requirement IR 和 Layer Impact。
6. 提取 playbook：高频需求场景、分层步骤、契约检查、QA 矩阵、常见错误。
7. 提取规范、约束、术语和业务背景。

## 确定性验证

记录以下事实前必须读取源码：

- enum 值
- switch/registry 分支
- 导出的类型/方法
- 字段名
- endpoint 路径
- request/response payload 字段
- 校验规则
- 下游集成 payload 映射

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## 输出质量

- 每个非显然条目都有 evidence。
- 跨层假设写入 `08-contracts.yaml`。
- 场景知识写入 `09-playbooks.yaml`，不要散落在说明文字中。
- 代码写法写入 `03-conventions.yaml`，不要复制契约和 playbook。
- 层专属事实使用适配器中的 surface 名称。
