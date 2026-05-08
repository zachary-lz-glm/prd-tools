# 步骤 0：上下文收集

## 目标

在构建 reference v4.0 之前，从历史 PRD、技术方案、分支和 diff 中提取可复用项目知识。

本步骤只收集事实，不修改 `_prd-tools/reference/`。

## 输入

一次性向用户收集 1-3 组历史样例：

- PRD 路径
- 可选技术方案/API 文档路径
- 前端代码库路径和分支/commit
- BFF 代码库路径和分支/commit
- 后端代码库路径和分支/commit
- 如有，补充已知事故、回滚、返工说明

## 执行

对每个样例：

1. 读取 PRD 和技术文档。
2. 在用户提供的 repo 范围内检查 git branch/diff。
3. 将 PRD 描述映射到实际变更文件和契约面。
4. 提取术语、路由信号、契约面、playbook 步骤、QA 用例、坑点和高风险文件。
5. 不确定就记录不确定，不猜测。

## 输出

写入 `_prd-tools/build/context-enrichment.yaml`：

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
collected_at: ""
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
    playbook_candidates: []
    glossary_candidates: []
    pitfalls: []
    qa_cases: []
    evidence: []
cross_sample_patterns:
  routing: []
  contracts: []
  playbooks: []
  risks: []
```

## 映射到 Reference v4.0

- 术语候选 -> `05-domain.yaml`
- 路由信号 -> `04-routing-playbooks.yaml`
- 契约面 -> `03-contracts.yaml`
- playbook、坑点、QA 用例、golden sample -> `04-routing-playbooks.yaml`
- 高风险文件 -> `02-coding-rules.yaml`（danger_zones）
- 业务决策 -> `05-domain.yaml`（decision_log）
- 枚举、结构体、模块 -> `01-codebase.yaml`
- 编码规范和约束 -> `02-coding-rules.yaml`
