# step-03: 确认 + 输出

## MANDATORY RULES

1. 所有 `confidence: low` 的项必须强制人工确认
2. 所有 `confidence: medium` 的项必须列出供用户确认
3. 用户的修改必须同步更新到 Markdown 表格和 YAML 块
4. 最终输出文件必须通过格式验证
5. 变更分类（ADD/MODIFY/DELETE/NO_CHANGE）必须经用户确认

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 蒸馏草稿 | `_output/distilled-<name>-draft.md` | Markdown + YAML |
| 用户确认 | 交互 | 文本 |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 最终蒸馏报告 | `_output/distilled-<name>.md` | Markdown + YAML |
| 蒸馏进度 | `_output/distill-progress.yaml` | YAML |

## EXECUTION

### 执行步骤

1. **展示变更分类摘要**（新增）

   展示变更分类汇总表和明细：

   ```
   变更分类汇总：
   | 层 | ADD | MODIFY | DELETE | NO_CHANGE |
   |----|-----|--------|--------|-----------|
   | 前端 | 2 | 1 | 0 | 5 |

   变更明细：
   | ID | 描述 | 变更类型 | 目标 | 置信度 | 验证来源 |
   |----|------|---------|------|--------|---------|
   | CI-001 | 新增梯度奖励表格 | ADD | FormDxgyFormList | high | code_verified |
   | CI-002 | 修改基础字段 | MODIFY | basic.ts | high | code_verified |
   | CI-003 | 新增枚举值 | ADD | campaignType | high | code_contradicts_reference |

   ⚠️ reference 与源码不一致的项：
   - CI-003: reference 标记已实现，但源码中未找到对应枚举 → 以源码为准，确认为 ADD
   ```

   用户可：
   - 确认分类准确
   - 修改某项的分类（如 ADD → MODIFY）
   - 标记某项为忽略

2. **展示开发建议（如有 matched_scenarios）**

   如果 step-01 匹配到了 playbook scenario（从 draft 的 `matched_scenarios` 字段读取），展示：

   ```
   📋 开发建议（基于 development_playbook）

   匹配场景：新增活动类型（置信度: high）
   预估变更文件数：7-10

   推荐执行顺序：
   | 步骤 | 操作 | 目标文件 | 验证方式 |
   |------|------|---------|---------|
   | 1 | 添加枚举值 | campaignType.ts | Grep 确认 |
   | 2 | 创建 detail 模板 | details/{NewType}.ts | Grep 确认 |
   | ... | ... | ... | ... |

   ⚠️ 常见错误：
   - 忘记 switch 注册
   - 忘记 preview 占位符
   - 枚举值重复
   ```

   用户可确认或调整建议。

3. **展示风险提示（如有 risk_flags）**

   如果 step-02 标记了风险项（从 draft 的 change_items 中 risk_flags 字段读取），在确认流程前展示：

   ```
   ⚠️ 风险提示（基于 war_stories + third_rails）

   🔴 危险区域（third_rails）：
   - CI-003 涉及 details/index.ts — switch-case 注册入口，漏改一个分支就运行时报错
     建议：修改前必须 Grep 所有枚举值确认

   🟡 已知坑点（war_stories）：
   - CI-005 涉及 rewardCondition — 梯度 key 容易和 basic 字段混淆
     预防：生成时必须区分 ctx.rewardCondition 和 ctx.basic

   🔵 场景提醒（playbook warnings）：
   - 新增活动类型场景常见错误：忘记 preview 占位符
   ```

   用户确认已知晓风险后继续。

4. **置信度分级确认**

   按置信度从低到高处理：

   **🔴 Low 置信度项（强制确认）**
   - 逐项展示：字段名 + PRD 原文引用 + AI 的建议映射 + 变更类型
   - 用户可：
     - 确认（更新 confidence 为 high）
     - 修改映射（更新值，confidence 更新为 high）
     - 修改变更类型（如从 ADD 改为 MODIFY）
     - 标记为忽略（从字段清单中移除）

   **🟡 Medium 置信度项（建议确认）**
   - 批量展示：列出所有 medium 项
   - 用户可批量确认或逐个修改

   **🟢 High 置信度项（简要确认）**
   - 展示统计数量
   - 用户一键确认

5. **需确认项处理**

   对蒸馏过程中发现的歧义（ambiguities）：
   - 逐项展示问题 + AI 建议 + 严重级别
   - blocker 级别的必须解决
   - suggestion 级别的可跳过

6. **同步更新**

   用户确认后，同步更新：
   - Markdown 表格中的字段信息（含 `change_type` 列）
   - 变更分类汇总表
   - 嵌入 YAML 块中的 `change_items` 和 `fields`
   - 置信度分布统计
   - 在 YAML 块中 `change_scope` 之后追加：
     ```yaml
     matched_scenarios: [...]  # 从 step-01 传递的 playbook 匹配结果
     risk_summary:             # 从 step-02 汇总的风险标记
       total_flags: N
       third_rails: X
       war_stories: Y
       playbook_warnings: Z
       details: [...]
     ```

7. **保存最终版本**

   - 写入 `_output/distilled-<name>.md`（最终版）
   - 删除 draft 和 routing 中间文件
   - 更新 `_output/distill-progress.yaml`（全部 completed）

8. **收集反馈（可选）**

   使用 AskUserQuestion 收集反馈评分：
   > **蒸馏质量评分**（1-5 分）：
   > - 路由匹配是否准确？
   > - 变更分类是否准确？
   > - 字段提取是否完整？
   > - 置信度标注是否合理？
   > - 有什么改进建议？

   反馈保存到 `_output/feedback/distill-<timestamp>.yaml`。

## CONFIRMATION POINT

确认完成后展示最终摘要：

```
蒸馏完成！
- 变更分类：ADD X / MODIFY Y / DELETE Z / NO_CHANGE W
- 字段总数：N（high: X, medium: Y, low: 0）
- 变更范围：N 个文件/组件（新增 X / 修改 Y / 不变 Z）
- 整体置信度：high
- 📋 开发建议：匹配到 N 个场景（scenario 名称）
- ⚠️ 风险提示：N 个风险标记（third_rails: X, war_stories: Y, playbook_warnings: Z）

📊 蒸馏质量指标
| 指标 | 值 | 说明 |
|------|-----|------|
| 路由覆盖率 | X% (M/N 需求项命中路由) | ≥80% 为健康 |
| 代码锚定率 | X% (M/N 项 code_verified) | ≥80% 为健康 |
| 置信度分布 | high:X / medium:Y / low:Z | low 越少越好 |
| 匹配方式分布 | keyword_exact:X / synonym:X / structural:X / golden:X / fallback:X | fallback 越少越好 |
| 变更分类确定性 | X% (M/N 项经源码确认) | ≥90% 为健康 |

输出文件：_output/distilled-<name>.md
```

提示用户下一步：
- **前端/BFF/后端**：将蒸馏报告提供给 AI Agent 或开发团队，结合 `_reference/` 进行代码开发
- **BFF（如有 bff-gen）**：可使用 `/bff-gen` 继续代码生成

## VALIDATION

1. **无 low 置信度** — 最终版本中无未处理的 low 项
2. **变更分类完整** — 每个 change_item 都有有效的 change_type
3. **格式完整** — Markdown 表格 + YAML 块结构完整
4. **YAML 合法** — 嵌入的 YAML 块可被解析器解析
5. **字段一致** — Markdown 表格和 YAML 块中的字段信息一致
6. **文件已保存** — 最终文件存在于 `_output/` 目录

## NEXT STEP

确认完成 → 蒸馏流程结束。用户可使用蒸馏报告进行后续开发。

### 矛盾回流提示（LLM Wiki 反馈闭环）

如果蒸馏过程中检测到 `verification_source: code_contradicts_reference` 条目（在步骤 1 的变更分类摘要中已标注），在最终摘要后**额外展示**：

```
⚠️ 检测到 N 条 reference 与源码矛盾（code_contradicts_reference）。
建议运行 /build-reference → 选择"反馈回流"更新知识库，让 reference 越用越准。
```

此提示不自动执行回流，只提醒用户。用户可：
- 忽略（继续后续开发）
- 运行 `/build-reference` → 选择 **选项 E: 反馈回流** 处理矛盾

### 自动回流建议（新增）

在最终报告末尾，自动生成 `reference_update_suggestions` 结构化建议，供 `/build-reference → 增量更新` 一键采纳：

```yaml
# 自动附加到蒸馏报告末尾
reference_update_suggestions:
  # 类型1：新路由模式建议（有 fallback 匹配项时触发）
  - type: "new_routing_pattern"
    suggestion: "新增路由模式：'<PRD描述摘要>'"
    evidence: "CI-XXX 未匹配任何 prd_pattern（match_method: fallback），但 PRD §X 明确描述了此需求"
    suggested_pattern:
      prd_pattern: "<建议的模式名>"
      prd_keywords: ["<从 PRD 中提取的关键词>"]
      change_type: <ADD|MODIFY>
      target: { files: { create: [...], modify_required: [...] } }
    priority: "high"  # 有 fallback 项时为 high

  # 类型2：reference 矛盾修复
  - type: "contradiction"
    suggestion: "inventory 中 <ItemName>.implemented 可能过期"
    evidence: "CI-XXX 标记 code_contradicts_reference，源码中有新逻辑但 reference 未记录"
    affected_file: "05-mapping.yaml → inventory.<ItemName>"
    priority: "high"

  # 类型3：同义词补充（同义词匹配成功但 prd_keywords 缺失时触发）
  - type: "synonym_gap"
    suggestion: "prd_keywords 缺少 '<关键词>'"
    evidence: "CI-XXX 通过 synonym 匹配成功，建议将 '<关键词>' 加入 prd_keywords"
    affected_file: "05-mapping.yaml → prd_routing[<pattern>].prd_keywords"
    priority: "medium"

  # 类型4：黄金样本补充（匹配到 golden_sample 但没有对应的 prd_routing 时触发）
  - type: "golden_sample_gap"
    suggestion: "golden_sample '<name>' 缺少对应的 prd_routing 条目"
    evidence: "CI-XXX 通过 golden_sample 匹配，但无直接路由，建议新增 prd_routing"
    priority: "medium"
```

**触发条件：**
- `match_method: fallback` 的项数 > 0 → 触发 new_routing_pattern
- `verification_source: code_contradicts_reference` 的项数 > 0 → 触发 contradiction
- `match_method: synonym` 的项数 > 0 → 触发 synonym_gap
- `match_method: golden_sample` 但无对应 prd_routing → 触发 golden_sample_gap

**使用方式：** 用户运行 `/build-reference → 增量更新` 时，自动读取最近蒸馏报告中的 `reference_update_suggestions`，展示建议并支持一键采纳。
