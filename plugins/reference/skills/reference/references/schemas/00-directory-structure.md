# 统一产出目录

两个插件共用 `_prd-tools/` 作为产出目录根：

```text
_prd-tools/
├── README.md                              # 产出索引
├── reference/                             # 知识库 SSOT（reference 产出）
│   ├── 01-codebase.yaml
│   ├── 02-coding-rules.yaml
│   ├── 03-contracts.yaml
│   ├── 04-routing-playbooks.yaml
│   ├── 05-domain.yaml
│   ├── project-profile.yaml
│   └── index/                             # Evidence Index（辅助层）
│       ├── entities.json                  # 代码实体索引
│       ├── edges.json                     # 实体关系索引
│       ├── inverted-index.json            # 倒排索引
│       └── manifest.yaml                  # 索引元数据
├── build/                                 # reference 运行报告
│   ├── modules-index.yaml
│   ├── context-enrichment.yaml
│   ├── quality-report.yaml
│   ├── health-check.yaml
│   ├── feedback-report.yaml
│   └── graph/
│       ├── sync-report.yaml
│       ├── code-evidence.yaml
│       └── business-evidence.yaml
└── distill/                               # prd-distill 蒸馏产出
    └── <slug>/
        ├── plan.md
        ├── report.md
        ├── context/
        │   ├── requirement-ir.yaml
        │   ├── evidence.yaml
        │   ├── readiness-report.yaml
        │   ├── graph-context.md
        │   ├── layer-impact.yaml
        │   ├── contract-delta.yaml
        │   └── reference-update-suggestions.yaml
        └── _ingest/
            ├── source-manifest.yaml
            ├── document.md
            ├── document-structure.json
            ├── evidence-map.yaml
            ├── media/
            ├── tables/
            ├── extraction-quality.yaml
            └── conversion-warnings.md
```

用户默认只需要读：
- `_prd-tools/distill/<slug>/report.md`（决策+阻塞问题）
- `_prd-tools/distill/<slug>/plan.md`（技术方案+开发计划）
- `_prd-tools/distill/<slug>/context/readiness-report.yaml`（就绪度评分、阻塞项）

`context/` 包含结构化需求、证据台账、契约分析上下文和就绪度评分，`_ingest/` 是原始文档读取层。

