# 输出契约 v3.0 — 索引

这些契约由 `/reference` 和 `/prd-distill` 共用。字段名保持英文，方便机器稳定解析；说明文字使用中文，方便团队阅读。

原文拆分为 6 个按需加载的 schema 文件，避免一次加载全部内容。按需读取对应的 schema 文件，不要一次全部加载。

## Schema 文件索引

| # | 文件 | 内容 | 消费步骤 |
|---|------|------|----------|
| 1 | `schemas/00-directory-structure.md` | 统一产出目录树 + portal.html 边界 | 任何需要了解输出文件布局的步骤 |
| 2 | `schemas/01-ingest.md` | `_ingest/` 全部 schema（source-manifest、document、document-structure.json、evidence-map、media-analysis、extraction-quality、conversion-warnings） | prd-distill step-01 |
| 3 | `schemas/02-capability-inventory.md` | `capability_inventory` schema + 生成规则 + 消费规则 | reference step-02d、prd-distill step-01 |
| 4 | `schemas/03-context.md` | `context/` 全部 YAML schema（graph-context.md、evidence.yaml、requirement-ir.yaml、layer-impact.yaml、contract-delta.yaml、reference-update-suggestions.yaml） | prd-distill step-01 ~ step-03 |
| 5 | `schemas/04-report-plan.md` | `report.md` 模板 + 写作规则 + `plan.md` 模板 + 写作规则 | prd-distill step-03 |
| 6 | `schemas/05-readiness.md` | `readiness-report.yaml` schema + 评分表 + 阈值 + 硬性降级 | prd-distill step-06 |
