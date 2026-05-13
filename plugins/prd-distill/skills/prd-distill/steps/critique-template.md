# Two-Pass Critic Template

## 何时使用

在以下高风险步骤**完成后**，立即执行 critique pass：

- Step 1.5: AI-friendly PRD 生成后
- Step 2: Requirement IR 生成后
- Step 3.2: Layer Impact 生成后
- Step 4: Contract Delta 生成后

## Critique Pass 规则

1. **只读本步骤产物 + 上一步产物 + 对应 contract**。不扩大上下文。
2. **输出 `context/critique/<step_id>.yaml`**。
3. **不修改原产物**。如果发现问题，记录到 critique 文件，由下一步或人工决定是否修正。

## 输出格式

```yaml
schema_version: "1.0"
step: "<step_id>"
artifact: "<被检查的产物路径>"
status: "pass | warning | fail"
findings:
  - id: "F-001"
    severity: "fatal | warning"
    rule: "<对应 contract rule_id 或自由描述>"
    issue: "<具体问题>"
    fix: "<建议修正方式>"
```

## 检查维度

### AI-friendly PRD (Step 1.5)

- 13 个章节是否齐全
- REQ-ID 是否连续且唯一
- source 标记（explicit/inferred/missing_confirmation）是否合理
- 是否有明显遗漏的 PRD 内容（对比 document-structure.json 的 block 数量）

### Requirement IR (Step 2)

- 每条 requirement 是否有 source_blocks（保真度）
- acceptance_criteria 是否存在且可测试
- missing_confirmation 是否正确标记为 blocked
- 是否有重复或矛盾的 requirement

### Layer Impact (Step 3.2)

- 每个 impact 是否有 requirement_id
- code_anchors 是否非空（或有 fallback_reason）
- change_type 是否合理（不应全部是 ADD）
- 是否覆盖了所有 requirement 涉及的层

### Contract Delta (Step 4)

- 每个 delta 是否有 requirement_id 和 layer
- producer/consumer 是否明确
- 是否有跨层契约被遗漏

## Gate 集成

`quality-gate.py distill` 在检查高风险步骤时，如果 `context/critique/<step_id>.yaml` 存在且 `status: fail`，则该步骤标记为需要修正。

warning 不阻断流程，但必须进入 `readiness-report.yaml` 的 risks 部分。
