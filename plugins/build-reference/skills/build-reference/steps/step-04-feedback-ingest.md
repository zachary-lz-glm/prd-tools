# step-04: 反馈回流（Feedback Ingestion）

## MANDATORY RULES

1. **只修改有矛盾证据的条目** — 不做推测性更新
2. **每条更新必须人工确认** — 不自动写入 reference
3. **以源码为最终真相** — reference 与源码矛盾时，以源码为准
4. **更新后验证** — 每次更新后验证修改的 YAML 仍合法
5. **记录回流历史** — 每次回流生成 report 供后续追溯

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 蒸馏输出 | `_output/distilled-*.md` | Markdown + YAML |
| Reference 文件 | `_reference/01~06.yaml` | YAML |
| 项目源代码 | 项目目录 | 源文件 |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 回流报告 | `_output/feedback-ingest-report.yaml` | YAML |
| 更新后的 Reference | `_reference/01~06.yaml` | YAML |

### feedback-ingest-report.yaml 结构

```yaml
version: "1.0"
project: "<项目标识>"
ingested_at: "2026-04-24T10:00:00Z"
source_file: "_output/distilled-<name>.md"

contradictions_found: 0
updates_proposed: 0
updates_applied: 0
updates_skipped: 0

updates:
  - id: "U-001"
    contradiction: "reference 标记 CampaignType.X 已实现，但源码中不存在"
    reference_file: "05-mapping.yaml"
    reference_section: "inventory.CampaignType.capabilities[2]"
    affected_dimensions:
      - "01-entities.yaml#enums.CampaignType"
      - "05-mapping.yaml#inventory.CampaignType"
      - "04-constraints.yaml#enum_validations"
    source_evidence: "Grep src/config/constant/campaignType.ts 未找到 X 枚举值"
    proposed_fix: "将 implemented: true 改为 implemented: false，change_type 改为 ADD"
    status: "applied" | "skipped" | "modified"
    applied_at: "2026-04-24T10:05:00Z"

reference_files_updated:
  - "01-entities.yaml"
  - "05-mapping.yaml"
  - "04-constraints.yaml"
```

## EXECUTION

### 执行步骤

1. **扫描蒸馏输出**

   遍历 `_output/distilled-*.md`，提取两类反馈：

   **类型 A：矛盾条目（code_contradicts_reference）**
   提取所有包含 `verification_source: code_contradicts_reference` 的条目。
   对于每个矛盾条目，提取：
   - 变更项 ID（如 CI-003）
   - 描述（reference 说了什么 vs 源码实际）
   - 涉及的文件/组件
   - PRD 原始需求

   **类型 B：自动回流建议（reference_update_suggestions）**
   读取蒸馏报告末尾的 `reference_update_suggestions` YAML 块，提取：
   - `new_routing_pattern`：新路由模式建议（来自 fallback 匹配项）
   - `contradiction`：reference 矛盾修复建议
   - `synonym_gap`：同义词补充建议（来自 synonym 匹配项）
   - `golden_sample_gap`：黄金样本补充建议
   每条建议已包含 `suggested_pattern` / `affected_file` / `priority` 等结构化信息，可直接展示给用户。

2. **定位受影响的 Reference 条目（按维度定位）**

   矛盾可能影响多个维度的文件。对每个矛盾条目：
   - **01-entities.yaml**：搜索相关的枚举/类型定义
   - **05-mapping.yaml**：搜索相关的 prd_routing 或 inventory 条目
   - **04-constraints.yaml**：搜索相关的枚举校验规则
   - **03-conventions.yaml**：搜索相关的代码模式
   - 记录每个受影响的 `{文件, 章节/字段}` 路径

3. **验证当前源码状态**

   对每个矛盾条目，用 Grep/Glob 验证源码**当前**实际状态：
   - 05-mapping 说 `implemented: true` → Grep 搜索源码确认是否真的存在
   - 01-entities 的枚举说包含某值 → Grep 确认枚举定义
   - 02-architecture 说文件路径存在 → Glob 确认路径

4. **生成更新建议**

   基于源码验证结果，生成具体更新建议列表。每条建议包含：

   ```
   U-001: [05-mapping.yaml > inventory.CampaignType > capabilities[2]]
   关联维度: 01-entities.yaml > enums.CampaignType, 04-constraints.yaml > enum_validations
   矛盾：mapping 标记 implemented: true，但源码中 campaignType.ts 不包含 "NEW_TYPE"
   建议：implemented: true → false, change_type: NO_CHANGE → ADD
   源码证据：Grep "NEW_TYPE" on campaignType.ts → 0 matches
   ```

5. **人工确认（CONFIRMATION POINT）**

   逐条展示更新建议，用户可：
   - ✅ 确认应用（更新 reference）
   - ✏️ 修改后应用（用户调整建议内容）
   - ⏭️ 跳过（保持 reference 不变）
   - 🔍 查看源码上下文（展示相关源码片段）

6. **应用更新**

   对用户确认的更新：
   - 用 Edit 工具修改对应 reference YAML 文件
   - 按维度更新所有受影响的文件（一个矛盾可能涉及 entities + mapping + constraints）
   - 更新所有受影响文件的 `last_verified` 为当天
   - 验证修改后的 YAML 格式合法

7. **生成回流报告**

   写入 `_output/feedback-ingest-report.yaml`，记录所有处理结果。

### 边界情况处理

- **无矛盾条目**：输出"未检测到 reference 矛盾，无需回流"，直接结束
- **矛盾条目过多（>10）**：提示"检测到 N 条矛盾，建议重新执行全量构建（选项 A）"
- **源码已变更（矛盾已自行修复）**：标记为 `auto_resolved`，不计入 updates_proposed
- **Reference 文件不存在**：报错"请先运行 /build-reference 全量构建"

## CONFIRMATION POINT

每条更新建议必须人工确认后才写入 reference。

全部处理完成后展示摘要：

```
反馈回流完成！
- 矛盾检测：N 条
- 已修复：M 条（分布在 X 个 reference 文件中）
- 已跳过：K 条
- 已自动解决：L 条
- 输出报告：_output/feedback-ingest-report.yaml
```

## VALIDATION

1. **YAML 合法** — 更新后的 reference 文件仍可被解析
2. **last_verified 更新** — 所有修改的文件 last_verified 为当天
3. **报告完整** — feedback-ingest-report.yaml 包含所有处理结果
4. **无遗漏** — 所有 code_contradicts_reference 条目都有处理结果

## NEXT STEP

回流完成 → Reference 已更新。用户可继续使用 `/prd-distill`，下次蒸馏时矛盾应减少。
