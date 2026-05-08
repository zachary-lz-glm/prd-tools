# PRD Tools 产出阅读指南

这份文档只回答一个问题：看到 `_prd-tools/` 后，先读什么，怎么判断这次结果能不能用于评审或开发。

详细字段契约看两个插件里的 `references/output-contracts.md`；这里不重复展开 YAML 结构。

## 先看什么

| 顺序 | 文件 | 适合谁 | 30 秒内看什么 |
|---:|---|---|---|
| 1 | `_prd-tools/STATUS.md` 或 `_prd-tools/dashboard/index.html` | 所有人 | reference、图谱、最近一次 distill、下一步 |
| 2 | `_prd-tools/distill/<slug>/report.md` | PM、TL、研发、QA | 需求摘要、影响范围、契约风险、阻塞项 |
| 3 | `_prd-tools/distill/<slug>/plan.md` | 研发、QA | 实现顺序、文件坐标、QA 矩阵、回滚 |
| 4 | `_prd-tools/distill/<slug>/readiness-report.yaml` | TL、工具维护者、CI | status、score、decision、provider value |
| 5 | `_prd-tools/distill/<slug>/context/contract-delta.yaml` | 跨团队 owner | `blocked` / `needs_confirmation` |
| 6 | `_prd-tools/distill/<slug>/_ingest/extraction-quality.yaml` | 工具维护者、评审人 | PRD 读取是 pass、warn 还是 block |

日常评审通常读前 3 个就够；出现争议时再看 `spec/`、`context/` 和 `_ingest/`。

## 两个入口的分工

| 文件 | 作用 | 是否维护事实 |
|---|---|---|
| `_prd-tools/STATUS.md` | 纯文本状态入口，适合终端、PR、代码评审和留档 | 否，来自 `status.sh` 推导 |
| `_prd-tools/dashboard/index.html` | 本地可视化入口，适合浏览器扫状态 | 否，和 STATUS.md 同源 |

如果两者看起来重复，这是刻意设计：**同一份状态，一份给文本环境，一份给浏览器。**

## 单次 PRD 输出地图

```text
_prd-tools/distill/<slug>/
├── report.md
├── plan.md
├── readiness-report.yaml
├── tasks/
├── spec/
│   ├── evidence.yaml
│   └── requirement-ir.yaml
├── context/
│   ├── graph-context.md
│   ├── layer-impact.yaml
│   ├── contract-delta.yaml
│   └── reference-update-suggestions.yaml
└── _ingest/
    ├── document.md
    ├── evidence-map.yaml
    ├── extraction-quality.yaml
    ├── media-analysis.yaml
    └── tables/
```

| 区域 | 回答什么 | 什么时候看 |
|---|---|---|
| `report.md` | 这次需求是什么、影响哪里、风险是什么 | 每次都看 |
| `plan.md` | 怎么改、怎么测、按什么顺序执行 | 每次都看 |
| `readiness-report.yaml` | 能不能进入开发/评审，为什么 | 需要量化状态或接 CI 时 |
| `tasks/` | 给 AI 或研发的自包含任务 | 要进入实现时 |
| `spec/` | PRD 被拆成哪些需求，证据是什么 | 对结论有争议时 |
| `context/` | 图谱、分层影响、契约差异、回流建议 | 做技术评审和跨团队对齐时 |
| `_ingest/` | PRD 原文被读成了什么，读取是否可靠 | 怀疑漏读、误读、图片/表格风险时 |

## 按角色读

| 角色 | 必读 | 需要时再读 | 重点问题 |
|---|---|---|---|
| PM / 业务 owner | `STATUS.md`、`report.md` | `_ingest/document.md` | PRD 是否被理解正确，哪些规则要确认 |
| TL | `STATUS.md`、`readiness-report.yaml`、`report.md` | `context/contract-delta.yaml` | 能不能开工，阻塞项 owner 是谁 |
| 研发 | `plan.md`、`context/graph-context.md` | `tasks/`、`spec/evidence.yaml` | 改哪些文件，证据是否可靠 |
| QA | `plan.md`、`spec/requirement-ir.yaml` | `report.md` 阻塞项 | 验收条件、边界值、回归范围是否完整 |
| 工具维护者 | `readiness-report.yaml`、`_ingest/` | `spec/`、`context/` | 读取质量、证据覆盖、provider value |

## 风险状态怎么判断

| 信号 | 含义 | 动作 |
|---|---|---|
| `readiness.status: pass` | 可以进入开发或联调 | 按 `plan.md` 执行 |
| `readiness.status: warning` | 可以评审，但有确认项 | 先处理 `needs_confirmation` |
| `readiness.status: fail` | 不建议开工 | 补 PRD、owner 或源码证据 |
| `extraction-quality: block` | PRD 没读可靠 | 暂停，补 markdown/text/OCR/人工确认 |
| `contract-delta blocked` | 契约冲突 | 停止推进，先解决冲突 |
| `contract-delta needs_confirmation` | 某层或 owner 未确认 | 拉 owner 确认 |
| 只有 reference 证据 | 结论不够硬 | 补源码、技术文档或负向搜索证据 |

## Reference 怎么读

`_prd-tools/reference/` 是项目长期知识库，不是某次 PRD 的临时结论。

| 场景 | 先看 | 再看 |
|---|---|---|
| 了解项目整体 | `00-portal.md` | `project-profile.yaml` |
| 查模块、枚举、注册点 | `01-codebase.yaml` | `project-profile.yaml` |
| 查编码规则和红线 | `02-coding-rules.yaml` | `04-routing-playbooks.yaml` |
| 对齐接口和字段 | `03-contracts.yaml` | `context/contract-delta.yaml` |
| 接新需求找打法 | `04-routing-playbooks.yaml` | `05-domain.yaml` |
| 理解业务术语 | `05-domain.yaml` | `03-contracts.yaml` |

## 15 分钟评审模板

| 时间 | 看什么 | 产出什么 |
|---:|---|---|
| 2 分钟 | `STATUS.md` / dashboard | 确认 reference、图谱和 readiness 状态 |
| 4 分钟 | `report.md` | 对齐需求范围、影响层、关键风险 |
| 4 分钟 | `context/contract-delta.yaml` | 明确 blocked / needs_confirmation 的 owner |
| 3 分钟 | `plan.md` | 确认开发顺序和 QA 重点 |
| 2 分钟 | `context/reference-update-suggestions.yaml` | 判断哪些知识要回流 |

会议结束时至少明确：

- 哪些任务可以直接开工。
- 哪些问题需要谁确认，什么时候确认。
- 哪些字段、枚举、接口或外部系统要同步。
- 哪些测试必须覆盖。
- 哪些知识要在交付后回流到 reference。

## 常见误解

| 误解 | 正确认知 |
|---|---|
| dashboard 和 STATUS.md 重复 | 它们同源，一个给浏览器，一个给文本环境 |
| YAML 很多，所以所有人都要读 | 普通评审只读 STATUS、report、plan |
| `warning` 表示失败 | `warning` 表示能继续，但风险必须显式处理 |
| reference 是最终事实 | reference 是加速器，最终以源码、PRD、技术方案、owner 确认为准 |
| 图谱结论可以直接当事实 | GitNexus/Graphify 是发现层，关键结论仍要 evidence 支撑 |
