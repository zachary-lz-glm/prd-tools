# build-reference 工作流

## 目标

构建 reference v3，让后续 `/prd-distill` 能稳定产出：

`Requirement IR -> Layer Impact -> Contract Delta -> 开发计划 -> QA 计划 -> Reference 回流`

reference 是“可验证指南针”，不是项目百科。只记录会影响需求理解、分层影响、契约对齐、开发和测试计划的事实。

## 阶段

| 阶段 | 名称 | 输入 | 输出 |
|---|---|---|---|
| 0 | 上下文收集 | 历史 PRD、技术方案、分支 diff、发布/返工记录 | `_output/context-enrichment.yaml` |
| 1 | 结构扫描 | 项目目录、核心源码、git 历史 | `_output/modules-index.yaml` |
| 2 | 深度分析 | modules-index、源码、context-enrichment、分层适配器 | `_reference/00~09` |
| 3 | 质量门控 | reference、源码、样例需求 | `_output/reference-quality-report.yaml` |
| 4 | 反馈回流 | `/prd-distill` 输出、源码、reference | `_output/feedback-ingest-report.yaml` |

## 阶段 0：上下文收集

用于提升 reference 的业务价值，尤其适合团队首次建设。

收集 1~3 个历史需求，每个需求尽量包含：

- PRD / 技术方案 / 接口文档路径
- 前端、BFF、后端代码库路径和分支
- 已知返工、线上问题、CR 争议点

输出：

```yaml
version: "3.0"
samples:
  - id: "SAMPLE-001"
    title: ""
    docs: []
    repos:
      frontend: { path: "", branch: "" }
      bff: { path: "", branch: "" }
      backend: { path: "", branch: "" }
    requirement_signals: []
    files_changed: []
    contract_surfaces: []
    lessons:
      - type: "playbook | contract | validation | pitfall | terminology"
        detail: ""
        evidence: []
```

把高价值样例沉淀到 `09-playbooks.yaml` 的 `golden_samples`。

## 阶段 1：结构扫描

判断项目层级并选择适配器：

- `frontend`：组件、页面、store/hook、API client、i18n、表单/校验目录。
- `bff`：template/render、constant、handler/service、schema/action/linkage。
- `backend`：controller/handler、service、model/domain、validator、client、job、audit。

扫描规则：

- 使用 `rg` / glob，范围限定在当前项目，不跨项目搜索。
- 排除 `node_modules`、`dist`、`build`、`coverage`、测试、mock、fixture、生成物。
- 读取文件前先确认路径存在。

输出 `_output/modules-index.yaml`：

```yaml
version: "3.0"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
modules:
  - id: ""
    path: ""
    responsibilities: []
    key_files: []
    entrypoints: []
    likely_contracts: []
    evidence: []
```

## 阶段 2：深度分析

先读取：

- `references/reference-v3.md`
- `references/layer-adapters.md` 中当前层章节
- `references/output-contracts.md` 中 evidence 和 contract 部分

生成 `_reference/` 十个文件：

```text
00-index.md
01-entities.yaml
02-architecture.yaml
03-conventions.yaml
04-constraints.yaml
05-routing.yaml
06-glossary.yaml
07-business-context.yaml
08-contracts.yaml
09-playbooks.yaml
```

提取顺序：

1. `01-entities`：枚举、核心类型、组件/接口/领域对象、注册点。
2. `02-architecture`：模块职责、数据流、注册机制、热点文件、危险区域。
3. `08-contracts`：producer/consumer、endpoint/schema/event、字段、required、type、兼容性。
4. `05-routing`：PRD 关键词和结构信号如何映射到 Requirement IR 与目标层。
5. `09-playbooks`：高频场景的开发/契约/QA 清单和 golden sample。
6. `03/04/06/07`：命名、约束、术语、业务背景和历史决策。

每条事实必须具备：

```yaml
evidence:
  - id: "EV-001"
    kind: "code | prd | tech_doc | git_diff | negative_code_search | human | api_doc"
    source: ""
    locator: ""
    summary: ""
confidence: "high | medium | low"
```

## 阶段 3：质量门控

必须检查：

- 文件完整性：`00~09` 全部存在。
- 证据完整性：实体、路由、契约、playbook 关键项都有 evidence。
- 源码一致性：路径、枚举值、注册点、模板函数、契约字段仍存在。
- 契约闭环：跨层字段有 producer / consumer / checked_by / alignment_status。
- 分层适配器门控：按 `references/layer-adapters.md` 检查当前层必需门控。
- 幻觉检查：文件、函数、变量、机制不能没有证据。
- 样例回归：至少用一个 golden sample 反推 PRD -> IR -> Layer Impact -> Contract Delta 是否走通。

输出 `_output/reference-quality-report.yaml`：

```yaml
status: "pass | warning | fail"
score: 0
fatal_findings: []
warnings: []
sample_replay:
  sample_id: ""
  passed: false
  gaps: []
next_actions: []
```

致命项不通过时，不要宣称 reference 可用于生产；列出最小修复项。

## 阶段 4：反馈回流

读取 `_output/prd-distill/**/reference-update-suggestions.yaml` 和 `distilled-report.md`。

只处理有证据的建议：

- `new_term`
- `new_route`
- `new_contract`
- `new_playbook`
- `contradiction`
- `golden_sample_candidate`

每条建议展示：

- 受影响 reference 文件
- 当前事实与新证据的差异
- 建议变更
- 证据来源
- 风险和置信度

用户确认后再修改 reference，并更新 `last_verified`。

## 执行规则

1. 源码是最终权威；reference 是快速通道。
2. 不确定就写 low confidence，不要补脑。
3. 多层需求必须显式记录契约面。
4. 前端、BFF、后端保持同一 reference 结构，层差异用适配器表达。
5. 每个 reference 文件尽量短；复杂样例放 `09-playbooks.golden_samples`，不要塞进每个章节。
6. 完成后给用户一份摘要：新增/更新文件、质量门控结果、下一步建议。
