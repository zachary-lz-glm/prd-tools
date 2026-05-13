# 04-routing-playbooks.yaml 的 capability_inventory

`04-routing-playbooks.yaml` 中新增 `capability_inventory` 部分，记录项目已有能力。prd-distill 在提取需求时消费此清单，区分"PRD 要求的是已有能力"还是"需要新增"。

适用于前端、BFF、后端所有层。维度名称（type/route/component/service）根据项目实际架构选择。

```yaml
capability_inventory:
  description: "项目已有能力清单，帮助 prd-distill 区分已有能力与需要新增的能力"

  generic_capabilities:
    - id: "CAP-001"
      name: ""
      description: ""
      scope: "generic"
      surfaces: []
      evidence: []
      status: "verified | partial | needs_verification"

  dimensioned_capabilities:
    - id: "CAP-DIM-001"
      name: ""
      dimension: ""             # 区分维度名称，根据项目架构命名
      dimension_source: ""      # 维度枚举/定义的源码位置
      pattern: "per_dimension"  # per_dimension | shared
      description: ""
      registration_point: ""
      existing_entries:
        - dimension_value: ""
          implementation: ""
          variant: ""
      evidence: []
      status: "verified | partial | needs_verification"

  coverage_matrix:
    description: "接口/字段/配置的覆盖方式矩阵"
    entries:
      - item: ""
        scope: "generic | per_dimension | hybrid"
        note: ""

  missing_capabilities:
    description: "已知缺失或未完整实现的能力"
    items:
      - name: ""
        status: "unknown | partial"
        note: ""
```

生成规则：

- `generic_capabilities`：从 `01-codebase.yaml` 的 `data_flow`、`03-contracts.yaml` 的通用接口推断。如果源码确认某个能力不按维度区分，标记 `scope: generic`。
- `dimensioned_capabilities`：从 `01-codebase.yaml` 的 `registration_points`、`enums`、switch/registry 分支推断。`dimension` 字段根据项目实际架构填写（BFF 通常用 type，前端用 route/component，后端用 service/model）。必须列出所有 `existing_entries`。
- `coverage_matrix`：从 `03-contracts.yaml` 的接口 + 源码中的 if/switch 分支推断每个功能是 generic 还是 per-dimension。
- `missing_capabilities`：从源码中的 TODO、未实现的接口、或 reference 构建过程中发现的盲点记录。
- 每个条目必须有 `evidence` 和 `status`。

prd-distill 消费规则：

- 当 PRD 提到的功能在 `generic_capabilities` 中 `status: verified` 时，不需要新增 REQ，但应在相关 REQ 的 `rules` 中注明"复用已有 XXX 能力"。
- 当 PRD 提到的功能在 `dimensioned_capabilities` 中，但 `existing_entries` 不包含目标维度值时，需要 ADD 类型的 REQ。
- 当 PRD 提到的功能在 `missing_capabilities` 中时，需要标记 `confidence: low` 并加入 `open_questions`。
