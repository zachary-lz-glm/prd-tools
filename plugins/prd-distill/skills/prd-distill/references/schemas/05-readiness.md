# readiness-report.yaml

`readiness-report.yaml` 是单次 PRD 蒸馏的机器可读红绿灯。它回答"这次分析能不能进入开发/评审，为什么"。

```yaml
schema_version: "3.0"
tool_version: "<tool-version>"
generated_at: "<ISO-8601>"
distill_slug: "<slug>"
status: "pass | warning | fail"
score: 0
decision: "ready_for_dev | needs_owner_confirmation | blocked"
summary:
  title: ""
  top_reason: ""
scores:
  prd_ingestion: 0
  evidence_coverage: 0
  code_search: 0
  contract_alignment: 0
  task_executability: 0
risks:
  blocked:
    - id: ""
      title: ""
      owner: ""
      source: "contract | evidence | ingestion | task"
  needs_confirmation:
    - id: ""
      title: ""
      owner: ""
      source: "contract | evidence | ingestion | task"
  low_confidence_assumptions: []
provider_value:
  reference:
    reused_playbooks: 0
    reused_contracts: 0
    examples: []
next_actions: []
```

评分建议：

| 维度 | 权重 | 数据来源 | 计算方式 |
|---|---:|---|---|
| `prd_ingestion` | 20 | `_ingest/extraction-quality.yaml`、media/table warnings | extraction-quality.status: pass=100, warn=70, block=0 |
| `evidence_coverage` | 25 | `_ingest/extraction-quality.yaml` coverage + `context/evidence.yaml` | `coverage_ratio * 100`（来自 extraction-quality.yaml 的 coverage.coverage_ratio） |
| `code_search` | 15 | `context/graph-context.md` | 命中符号数 / REQ 需要搜索的符号数 |
| `contract_alignment` | 25 | `context/contract-delta.yaml` | aligned 契约数 / 总契约数 |
| `plan_quality` | 15 | `plan.md`（文件路径精确度、验证命令覆盖） | 有 file:line 的任务数 / 总任务数 |

状态阈值：

| 分数 | status | decision |
|---:|---|---|
| 85-100 | `pass` | `ready_for_dev`，除非有硬阻塞 |
| 60-84 | `warning` | `needs_owner_confirmation` |
| 0-59 | `fail` | `blocked` |

硬性降级：

- `_ingest/extraction-quality.yaml` 为 `block` → `fail`。
- 任一 P0 契约为 `blocked` → `fail`。
- 多层需求缺少 `context/contract-delta.yaml` → `fail`。
