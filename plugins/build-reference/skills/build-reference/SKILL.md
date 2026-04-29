---
name: build-reference
description: 为前端、BFF、后端通用的 PRD-to-code 工作流构建、更新、健康检查或回流项目 reference 知识库。适用于用户调用 /build-reference，或在 Codex/Agent 中要求使用 build-reference skill、构建项目知识库、项目画像、能力面适配器、契约、playbook、golden sample、反馈回流机制时。
---

# build-reference

Claude Code 中可通过 `/build-reference` 使用；Codex 中通过“使用 build-reference skill ...”触发。

## 这个 skill 是做什么的

`build-reference` 负责把一个项目中会影响 PRD-to-code 的长期知识沉淀到 `_reference/`。

它不是生成项目百科，也不是简单罗列目录；它只记录后续 PRD 蒸馏真正需要的事实：

- 项目画像：技术栈、入口、构建/测试命令、部署形态。
- 能力面：前端/BFF/后端各自承担哪些能力，关键文件和入口在哪里。
- 业务实体：枚举、字段、组件、DTO、领域对象、endpoint、DB model。
- 跨层契约：producer、consumer、字段、required、type、owner、alignment_status。
- 开发套路：高频需求如何改、先看哪里、要测什么、常见坑是什么。
- 历史样例：真实 PRD、技术方案、分支 diff、返工经验和 golden sample。

## 什么时候使用

使用场景：

- 团队第一次接入 PRD Tools，需要初始化 `_reference/`。
- 项目结构、活动类型、接口契约、schema 或业务规则发生较大变化。
- 完成一次真实 PRD 后，需要把新增术语、新契约、踩坑和经验回流。
- 怀疑已有 reference 过期、缺证据、和源码矛盾，或需要健康检查。

不要使用的场景：

- 用户只是想让你解释某段代码。
- 用户只是要求直接实现一个具体改动，且没有要求维护 reference。
- 当前没有项目源码，也没有任何可验证上下文。

## 输入

优先收集：

- 当前项目路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- 历史 PRD、技术方案、接口文档。
- 历史分支、commit、diff、返工记录。
- 当前已有 `_reference/` 和 `_output/`。

没有历史样例时也可以构建，但必须标注业务语义置信度较低。

## 输出

长期知识库输出到项目根目录：

```text
_reference/
├── 00-index.md 或 README.md
├── project-profile.yaml
├── contracts.yaml 或 08-contracts.yaml
├── playbooks.yaml 或 09-playbooks.yaml
└── 01~09 兼容细节文件
```

过程和质量报告输出到：

```text
_output/
├── context-enrichment.yaml
├── modules-index.yaml
├── reference-health.yaml
├── reference-quality-report.yaml
└── feedback-ingest-report.yaml
```

## 工作模式

| 模式 | 何时使用 | 主要输出 |
|---|---|---|
| `F 上下文收集` | 首次建设前，收集历史 PRD、技术方案、分支 diff | `_output/context-enrichment.yaml` |
| `A 全量构建` | 首次构建或项目大改后重建 | `_reference/` |
| `B 增量更新` | 只更新受 git diff、文件变化或新证据影响的部分 | 更新后的 `_reference/` |
| `B2 健康检查` | 判断 reference 是否完整、过期、缺证据 | `_output/reference-health.yaml` |
| `C 质量门控` | 检查证据、契约闭环、源码一致性、幻觉风险 | `_output/reference-quality-report.yaml` |
| `E 反馈回流` | 从 prd-distill 输出中回收确认过的新知识 | `_output/feedback-ingest-report.yaml` |

如果用户没有指定模式，先检查 `_reference/` 是否存在：

- 不存在：建议 `F 上下文收集`，然后 `A 全量构建`。
- 已存在：建议 `B2 健康检查` 或按用户目标执行 `B/E/C`。

## 能力面适配器

前端、BFF、后端共用同一套流程，但不绑定固定目录结构。

先识别项目层级，再读取 `references/layer-adapters.md`。路径只作为候选，最终结论必须来自源码、配置、类型定义、注册点、调用链、测试或负向搜索。

典型能力面：

- 前端：`ui_route`、`view_component`、`form_or_schema`、`state_flow`、`client_contract`、`content_i18n`、`client_validation`。
- BFF：`edge_api`、`schema_or_template`、`orchestration`、`transform_mapping`、`frontend_contract`、`upstream_contract`。
- 后端：`api_surface`、`application_service`、`domain_model`、`validation_policy`、`persistence_model`、`async_event`、`external_integration`。

## 文件边界

构建 `_reference/` 时必须遵守：

- `01-entities`：只放已存在的静态事实，不写流程。
- `02-architecture`：只放结构、入口、运行流和高风险区域，不写字段契约详情。
- `03-conventions`：只放代码写法、命名、注册模式、反模式。
- `04-constraints`：只放硬规则、校验红线和生成边界。
- `05-routing`：只放 PRD 信号到需求、目标层、能力面的路由规则。
- `06-glossary`：只放业务术语、同义词和字段/组件映射。
- `07-business-context`：只放业务背景、隐式规则、历史决策和歧义。
- `08-contracts`：只放跨层和外部契约，不写开发步骤。
- `09-playbooks`：只放场景打法、QA 矩阵、常见坑和 golden sample，不复制字段级契约。

尤其注意：

```text
03-conventions：代码通常怎么写
08-contracts：系统边界承诺了什么
09-playbooks：遇到某类需求怎么推进
```

## 证据规则

必须遵守：

- 源码、PRD、技术文档、API 文档、git diff 是权威证据。
- reference 是加速器，不是最终权威。
- 枚举、字段、方法签名、契约字段、业务规则不能从文件名或 import 推断，必须读源文件。
- 搜不到也是证据，使用 `negative_code_search` 记录 query 和范围。
- 不确定就写 `confidence: low`，并进入开放问题或后续动作。
- 每条关键事实都要有 `evidence`、`verified_by` 或明确的负向搜索。

## 执行步骤

1. 识别项目路径、层级、已有 `_reference/` 和 `_output/`。
2. 根据用户目标选择模式。
3. 限定在当前项目内搜索，不跨兄弟项目。
4. 使用 `rg` / glob 找候选，再读取源码确认事实。
5. 生成或更新 `_reference/`。
6. 执行健康检查或质量门控。
7. 给用户摘要：新增/更新文件、质量状态、风险、下一步建议。

## 需要读取的参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 执行完整构建、健康检查、质量门控或反馈回流时 |
| `references/reference-v3.md` | 需要确认 reference 文件职责、边界、质量规则时 |
| `references/layer-adapters.md` | 判断前端/BFF/后端能力面时 |
| `references/output-contracts.md` | 需要和 prd-distill 输出契约对齐时 |
| `templates/*.yaml` | 创建 reference 骨架时 |
| `references/selectable-reward-golden-sample.md` | 需要示例或校准复杂需求时 |

## 完成标准

完成后不要只说“已构建”。必须说明：

- `_reference/` 新增或更新了哪些文件。
- reference 当前健康状态：pass / warning / fail。
- 哪些关键事实证据充分，哪些是 low confidence。
- 是否存在跨层契约 owner 未确认。
- 下一步应该运行 `prd-distill`，还是继续补历史样例或修复 reference。
