# step-03: 质量门控（Phase 3）

## MANDATORY RULES

1. 三轮独立检查，不可跳过任何一轮
2. 自动化检查优先（Round 1），人工检查为主（Round 2-3）
3. 发现问题必须修复后才能通过，不能标 TODO 绕过
4. 质量评分量化，不使用模糊描述
5. Round 4 场景验证（development_playbook 测试）

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| Reference 文件 | `_reference/` | YAML / Markdown |
| 项目源代码 | 项目目录 | 源文件 |
| 模块索引 | `_output/modules-index.yaml` | YAML |
| 上下文富化 | `_output/context-enrichment.yaml` | YAML |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 质量报告 | `_output/quality-report.yaml` | YAML |
| 最终 Reference | `_reference/` | YAML / Markdown |
| 进度更新 | `_output/build-reference-progress.yaml` | YAML |

### quality-report.yaml 结构

```yaml
version: "1.0"
project: "<项目标识>"
quality_at: "2026-04-24T10:00:00Z"
overall_score: 0        # 0-100
ready: false            # true when score >= 80

rounds:
  round_1_auto:
    score: 0
    checks:
      - name: "文件路径有效性"
        passed: true
        details: "检查了 N 个路径，全部存在"
      - name: "YAML 格式合法性"
        passed: true
        details: null
      - name: "元数据完整性"
        passed: true
        details: null
      - name: "TODO 计数"
        passed: true
        details: "N 个 TODO，阈值 < 15"
      - name: "行数限制"
        passed: true
        details: "最大文件 05-mapping.yaml: N 行"
      - name: "change_type 覆盖率"
        passed: true
        details: "prd_routing N 条全部有 change_type，inventory M 条有 change_type"
      - name: "default_action 兼容"
        passed: true
        details: "所有有 change_type 的条目也有 default_action"
      - name: "代码模式匹配"
        passed: true
        details: "检查了 N 个代码模式，M 个匹配"
      - name: "跨文件枚举一致"
        passed: true
        details: "01-entities 枚举与 04-constraints 校验规则完全一致"
      - name: "孤立条目检测"
        passed: true
        details: "N 个孤立条目已报告"
      - name: "实体索引完整"
        passed: true
        details: "实体索引中 M 个指向全部有效"

  round_2_human:
    score: 0
    sample_size: 3
    hallucinations_found: 0
    business_knowledge_added: 0

  round_3_e2e:
    score: 0
    test_prd: null
    hit_rate: 0
    false_positive_rate: 0

todos:
  total: 0
  by_confidence:
    low: 0
    medium: 0
  items: []
```

## EXECUTION

### Round 1: 完整性检查（自动化）

逐项检查：

| 检查项 | 方式 | 通过标准 |
|--------|------|---------|
| 7 文件齐全 | Glob `_reference/*` | 8 个文件全部存在（00-index.md + 01~07.yaml） |
| YAML 格式合法 | 尝试解析每个 .yaml | 无解析错误 |
| 元数据完整 | 检查 version/layer/project/last_verified | 每个文件都有 |
| 文件路径存在 | 遍历所有 target_file / key_files / definition_file | 100% 存在 |
| TODO 计数 | `grep -c todo:` | < 15 个 |
| 行数限制 | `wc -l` | 每文件 ≤ 300 行（05-mapping 例外） |
| 枚举无重复 | 检查 01-entities 的枚举列表 | 无重复值 |
| change_type 覆盖率 | 遍历 05-mapping 的 prd_routing 和 inventory capabilities | 每个条目有有效 change_type |
| default_action 兼容 | 检查有 change_type 的条目是否也有 default_action | 100% 兼容 |
| 代码模式匹配 | Grep 03-conventions 中描述的代码模式到源码 | ≥90% 匹配 |
| 跨文件枚举一致 | 01-entities 的枚举值 vs 04-constraints 的枚举校验规则 | 完全一致 |
| 孤立条目检测 | 05-mapping 的 inventory 中 implemented:true 但无 prd_routing 引用 | 报告但不断 |
| 实体索引完整 | 00-index.md 实体索引中指向的文件和章节存在 | 100% 有效 |

自动修复可修复的问题（如缺失元数据头），报告无法自动修复的问题。

### Round 2: 准确性检查（人工 + AI）

1. **抽样验证**：随机选 3~5 个模块，人工对照源码验证 reference 内容
2. **幻觉检测**：检查是否编造了不存在的文件/函数/变量
3. **业务知识补充**：标注 AI 无法从代码推断的业务规则
4. **custom 字段注释检查**：自定义字段是否写清了注释

具体操作：
- 展示抽样模块的 reference 内容
- 用户逐条确认或修正
- 记录幻觉数和补充条目数

### Round 3: 实用性检查（端到端测试）

1. **选择测试 PRD**：从已有示例中选一个相关的 PRD
2. **模拟蒸馏**：用 `/prd-distill` 的逻辑（读取 05-mapping.yaml 的路由表）对测试 PRD 做路由匹配
3. **评估结果**：
   - 命中率：正确匹配的 PRD 需求 / 总需求
   - 误报率：错误匹配的 / 总匹配
   - 漏报率：未匹配的 / 总需求
4. **目标**：命中率 ≥ 80%

### Round 4: 场景验证（Playbook 测试）

目标：验证 development_playbook 是否能让 AI 正确规划变更。

1. 从 `05-mapping.yaml` 的 `development_playbook` 中选 2 个 scenario
2. 构造模拟 PRD 需求描述（一句话），例如：
   - "新增一种签到活动，支持连续签到 7 天递增奖励"
   - "在基础信息页新增一个'骑手类型'下拉选项"
3. 让当前 Agent 基于 reference 文件规划变更（只读 reference，不读源码）：
   - 列出需要修改的文件清单
   - 列出修改顺序
   - 标注已知坑点
4. 对照 playbook checklist 评估：
   - **文件覆盖率**：AI 列出的文件 vs playbook 要求的文件 ≥ 80%
   - **顺序正确性**：AI 的修改顺序 vs playbook 的 step 顺序 ≥ 70%
   - **坑避免率**：AI 是否避开了 common_mistakes 和 war_stories ≥ 90%
5. 记录结果到质量报告

### TODO 校准

汇总所有 TODO 项：
1. 按 confidence 排序（low 优先）
2. 逐项展示给用户：
   - 确认正确的 → 删 TODO，升 confidence 为 high
   - 确认错误的 → 修正内容
   - 无法确认的 → 保留 TODO，标 needs_domain_expert
3. 全部处理完或剩余 < 3 个 → 通过

## CONFIRMATION POINT

三轮检查完成后：

1. 展示质量报告摘要：
   ```
   Round 1 自动检查：✅ PASS (N/M 项通过)
   Round 2 人工验证：✅ PASS (N 个幻觉已修正，M 条业务知识已补充)
   Round 3 端到端测试：✅ PASS (命中率 XX%，误报率 XX%)
   Round 4 场景验证：✅ PASS (文件覆盖率 XX%，顺序正确性 XX%，坑避免率 XX%)
   总分：XX/100
   TODO 剩余：N 个
   ```
2. 如果总分 < 80：列出改进建议，询问是否重新执行 Phase 2 的部分模块
3. 如果总分 ≥ 80：标记 ready: true，Reference 构建完成

## VALIDATION

1. **总分 ≥ 80** — 才能标记为 ready
2. **Round 1 全部通过** — 自动化检查无失败项
3. **TODO < 5** — 最终版本 TODO 数量可控
4. **命中率 ≥ 80%** — Round 3 端到端测试达标

## NEXT STEP

质量门控通过 → Reference 构建完成。提示用户：
- 可以使用 `/prd-distill` 进行 PRD 蒸馏
- Reference 文件需定期更新（14 天周期）
- 下次代码变更后可使用 `/build-reference` 增量更新模式
