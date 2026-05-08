# prd-distill

> 把 PRD 蒸馏成有证据支撑的技术报告和开发计划：影响分析、契约差异、QA 矩阵、待确认问题，全部可追溯到源码和 PRD 原文。

## 快速使用

在 Claude Code 中进入目标项目，运行：

```
/prd-distill <PRD 文件路径或需求文本>
```

示例：

```
/prd-distill docs/新司机完单奖励PRD.docx
/prd-distill 需要在活动页面新增一种优惠券类型，type_id=45
```

## 流程总览

### 主流程

```mermaid
flowchart TD
  A["/prd-distill <PRD 文件或需求文本>"] --> B{"输入类型"}
  B -- "docx/pdf/pptx/xlsx/html/md/txt" --> C["PRD Ingestion\n读取文件"]
  B -- "粘贴文本" --> D["手工建立来源和定位"]
  C --> E["_ingest/\nsource-manifest / document / tables / media / quality"]
  D --> E
  E --> F{"extraction-quality"}
  F -- "block" --> G["暂停：要求补充可读 PRD"]
  F -- "pass/warn" --> H["Step 2：拆 Requirement IR\n业务意图 + 规则 + 验收条件"]
  H --> I["Step 3.1：源码上下文构建\n（扫描代码定位函数坐标）"]
  I --> J["context/graph-context.md\n函数级技术线索 + 业务约束"]
  J --> K["Step 3：Layer Impact\n按能力面分层"]
  J --> L["Step 4：Contract Delta\n字段级契约差异"]
  K --> M["Step 5：plan.md\n函数级技术方案 + QA 矩阵"]
  L --> M
  K --> N["Step 7：report.md\n渐进式披露 + §11 阻塞项"]
  L --> N
  K --> O["Step 6：reference-update-suggestions\n知识回流建议"]
  L --> O
```

### 代码搜索如何参与蒸馏（Step 3.1 详解）

这是 prd-distill 中代码搜索的核心环节。对每个需求点（REQ），通过源码搜索定位代码坐标：

```mermaid
flowchart LR
  subgraph Input["需求点 REQ"]
    REQ["业务实体 + 字段名 + 接口名 + 动作词"]
  end

  subgraph Search["代码搜索"]
    direction TB
    S1["rg/grep(REQ 关键词)\n→ 匹配的文件、函数、类"]
    S2["Read(命中的文件)\n→ 调用链、结构体、接口"]
    S3["import 分析\n→ 依赖关系、受影响模块"]
    S1 --> S2 --> S3
  end

  REQ --> Search

  Search --> GC["context/graph-context.md\n├ 代码线索：symbol, file:line,\n│  callers, callees, risk\n└ recommended_plan_usage"]

  GC --> LI["Layer Impact"]
  GC --> CD["Contract Delta"]
  GC --> PL["plan.md\n函数级技术方案\n精确到 file:line + 参考实现"]
  GC --> RP["report.md §2\n代码命中摘要"]
```

### 代码搜索在各步骤的具体作用

| 步骤 | 代码搜索做什么 |
|------|---------------|
| **Step 3.1 代码搜索上下文** | rg/grep + Read → 函数坐标、调用链 |
| **Step 3 Layer Impact** | 受影响符号写入 impact |
| **Step 4 Contract Delta** | 搜索 consumer 字段访问 |
| **Step 5 plan.md** | 引用代码搜索的 file:line 线索 |
| **Step 7 report.md** | §2 代码命中摘要 |
| **Step 6 回流建议** | 发现 reference 缺失的符号/调用链 |

## 什么时候用

| 场景 | 用它 |
|------|------|
| 拿到新 PRD，需要评估影响范围 | 是 |
| 需要给前端/BFF/后端拆任务、对齐接口 | 是 |
| 需要识别字段、枚举、schema 的契约风险 | 是 |
| 需要生成 QA 测试矩阵 | 是 |
| 直接改代码，不需要分析 | 否 |
| 没有任何可分析的输入 | 否 |

## 支持的输入格式

| 格式 | 处理方式 | 注意事项 |
|------|---------|---------|
| `.md` / `.txt` | 保留原文和行号 | 图片引用需要人工确认 |
| 粘贴文本 | 手工建立来源和质量说明 | 缺少原文件 hash |

## 产出文件

```
_prd-tools/distill/<slug>/
├── _ingest/                       # PRD 原始读取结果
│   ├── source-manifest.yaml       #   原始文件信息
│   ├── document.md                #   转换后的可读 markdown
│   ├── evidence-map.yaml          #   PRD 块级证据映射
│   ├── media/                     #   抽出的图片
│   ├── tables/                    #   抽出的表格
│   └── extraction-quality.yaml    #   读取质量门禁
├── report.md                      # 影响报告 + 风险 + 待确认项
├── plan.md                        # 函数级技术方案 + 开发计划 + QA 矩阵
└── context/
    ├── requirement-ir.yaml        # 结构化需求
    ├── evidence.yaml              # 证据台账
    ├── readiness-report.yaml      # 就绪度评分 + 风险 + provider 增益
    ├── graph-context.md           # 源码扫描的函数级上下文
    ├── layer-impact.yaml          # 分层影响
    ├── contract-delta.yaml        # 契约差异
    └── reference-update-suggestions.yaml  # 知识回流建议
```

**人类阅读：** `report.md`（决策报告）+ `plan.md`（开发计划）

**机器/审计：** `context/` 和 `_ingest/` 用于审计复盘和知识回流

## 典型使用流程

**首次蒸馏：**
1. 确保项目已运行过 `/reference`（有 `_prd-tools/reference/`）
2. 运行 `/prd-distill <PRD 文件>`
3. 先看 `report.md` 的结论和阻塞项
4. 再看 `plan.md` 的开发计划

**日常循环：**
1. `/prd-distill` 分析 PRD → 产出 report + plan
2. 按 plan 开发
3. 交付后运行 `/reference` 的 Mode E 回流经验

## 常见问题

**Q: PRD 是飞书/钉钉链接怎么办？**
A: 目前不支持直接读取在线文档。请导出为 docx/pdf 或复制粘贴文本。

**Q: 报告质量不好怎么办？**
A: 优先确保 `_prd-tools/reference/` 质量过关（先跑 `/reference` 的 B2 健康检查）。reference 越准确，蒸馏质量越高。

**Q: 需要哪些环境变量？**
A: 不需要。PRD Tools 只依赖 Claude Code 和原生 shell 工具。

**Q: `_prd-tools/reference/` 不存在能跑吗？**
A: 能跑，但会缺少项目上下文，影响分析深度。建议先跑 `/reference`。
