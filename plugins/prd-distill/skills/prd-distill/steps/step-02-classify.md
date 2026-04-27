# step-02: 分类 + 结构化

## MANDATORY RULES

1. 每个功能需求项必须标注 `change_type`：ADD / MODIFY / DELETE / NO_CHANGE
2. 分类逻辑按层（frontend / bff / backend）适配，使用层专属分类规则
3. 分类结果必须引用 step-01 的路由匹配结果，不可凭空编造
4. 不确定的分类标 `confidence: low`，禁止猜测后标为 high
5. **每个 ADD/MODIFY 判断必须锚定源码** — 不允许仅凭 reference 的 implemented 标记决定变更类型
6. 分类的目标是服务多个下游消费者：前端/BFF/后端开发者、QA、PM
7. 本步骤不要求人工确认，自动分类后输出草稿供 step-03 确认

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 路由结果 | `_output/distilled-<name>-routing.md` | Markdown + YAML |
| 能力清单 | `_reference/05-mapping.yaml` → `inventory` | YAML |
| 能力边界 | `_reference/05-mapping.yaml` → `capability_boundary` | YAML |
| 变更分类标准 | `_reference/05-mapping.yaml` → `change_type_rules` | YAML |
| 枚举定义 | `_reference/01-entities.yaml` → `enums` | YAML |
| 约束规则 | `_reference/04-constraints.yaml` → `fatal_errors` | YAML |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 蒸馏草稿 | `_output/distilled-<name>-draft.md` | Markdown + YAML |

### 蒸馏草稿格式

```markdown
---
source: "PRD 文件名"
distilled_at: "2026-04-24"
distilled_by: "step-02-classify"
layer: <frontend|bff|backend>
version: "2.0"
---

# PRD 蒸馏报告 — <活动名称>

## 📋 摘要
| 项目 | 值 |
|------|-----|
| 活动类型 | 新增/已有 |
| 层 | frontend / bff / backend |
| 影响模块 | ... |
| 总字段数 | N |
| 整体置信度 | high / medium |

## 🔄 变更分类（新增章节）

### 汇总
| 层 | ADD | MODIFY | DELETE | NO_CHANGE |
|----|-----|--------|--------|-----------|
| 当前层 | N | M | K | L |

### 明细
| ID | PRD 引用 | 描述 | 层 | 变更类型 | 目标 | 置信度 |
|----|---------|------|----|---------| -----|--------|
| CI-001 | §3.1 | 新增梯度奖励表格... | 前端 | ADD | FormDxgyFormList | high |

## ⚠️ 需确认项
（🔴 必须确认，🟡 建议确认）

## 📊 字段清单
（按模块分表，每行新增 `变更类型` 列）

## 🔗 联动关系

## ✅ 校验规则

## 📐 业务规则

## 📦 变更范围
（目标文件/组件/API + 变更类型 + 说明）

## 结构化数据
\`\`\`yaml
meta: ...
change_items:
  - id: CI-001
    prd_ref: "§3.1"
    description: "..."
    change_type: ADD
    layer: frontend
    target: { component: "FormDxgyFormList" }
    confidence: high
ambiguities: ...
fields: ...
linkages: ...
validations: ...
business_rules: ...
change_scope: ...
\`\`\`
```

## EXECUTION

### 执行步骤

1. **加载路由结果**
   - 读取 `_output/distilled-<name>-routing.md`
   - 获取所有路由匹配结果和未匹配需求

2. **逐项分类（核心逻辑）**

   对每个路由匹配结果，按以下通用规则确定 `change_type`：

   **通用分类规则：**
   - PRD 明确说"新增"/"添加"/"支持XX" → **ADD**
   - PRD 明确说"修改"/"调整"/"变更"/"更新" → **MODIFY**
   - PRD 明确说"移除"/"删除"/"废弃"/"下线" → **DELETE**
   - PRD 描述匹配现有能力，无需改动 → **NO_CHANGE**

   **层专属分类逻辑：**

   | change_type | 前端判断 | BFF 判断 | 后端判断 |
   |-------------|---------|---------|---------|
   | ADD | 组件不在 inventory 或 `implemented: false` | `target.files.create` 非空或新活动类型 | 新 API 或新数据模型字段 |
   | MODIFY | 组件存在但 PRD 需要新能力（`implemented: false` 的能力项） | 已有文件需新增字段（`modify_required`/`modify_conditional`） | 已有 API 合同变更 |
   | DELETE | PRD 明确说要移除功能/组件 | PRD 说移除字段/废弃活动类型 | API 废弃或字段移除 |
   | NO_CHANGE | `implemented: true` 且 PRD 描述匹配现有行为 | 字段已存在模板中，只需枚举值 | 后端自行处理 |

3. **生成 change_items**

   每个分类项生成一个 `change_item`：

   ```yaml
   - id: CI-001
     prd_ref: "§3.1"                    # PRD 原文引用
     description: "新增梯度奖励表格"     # 人类可读描述
     change_type: ADD                    # ADD / MODIFY / DELETE / NO_CHANGE
     layer: frontend                     # 当前层
     target: { component: "FormDxgyFormList" }  # 层专属目标
     capability: "多行梯度表格"          # 涉及的能力项（可选）
     confidence: high                    # 分类置信度
     verification_source: code_verified  # 验证来源（code_verified / reference_only / code_contradicts_reference）
     code_evidence: "Grep搜索 FormDxgyFormList 目录，未找到梯度表格渲染逻辑"  # 代码证据摘要
   ```

4. **源码二次验证（对 ADD/MODIFY 项）**

   对每个 `change_type: ADD` 或 `change_type: MODIFY` 的项，执行源码验证：

   **ADD 验证：**
   - Grep 搜索目标位置是否存在对应代码（组件/文件/枚举/API）
   - 如果源码中**已存在** → 降级为 MODIFY 或 NO_CHANGE，更新 `verification_source: code_contradicts_reference`
   - 如果源码中**不存在** → 确认 ADD，标注 `verification_source: code_verified`

   **MODIFY 验证：**
   - Read 目标文件，确认该组件/字段确实存在
   - Grep 搜索 PRD 要求的具体能力是否已在代码中实现
   - 如果已实现 → 降级为 NO_CHANGE
   - 如果未实现但文件存在 → 确认 MODIFY
   - 记录 `code_evidence`（简短描述在源码中看到了什么）

   **不允许出现的错误模式：**
   - reference 说 `implemented: false` 但源码已实现 → 必须纠正
   - reference 说 `implemented: true` 但源码已删除 → 必须纠正
   - AI 不搜索源码直接判断 → **严格禁止**

5. **结构化字段清单**

   将 step-01 的原始字段提取结果，结合分类信息结构化：
   - 每个字段标注 `change_type`（从所属需求项继承）
   - 每个字段标注层专属信息（前端→d_component, BFF→target_file, 后端→api_field）
   - 保持模块分组（basic / group / rules / message / preview）

5. **处理未匹配需求**

   对 step-01 中未匹配路由的需求：
   - 根据 PRD 描述推断 `change_type`（通常为 ADD，置信度 low）
   - 不映射到具体目标，标注 `target: null`
   - 标记为需确认项

6. **生成蒸馏草稿**

   - 按上述格式生成 Markdown + YAML
   - 变更分类章节放在摘要之后（最重要的新增信息）
   - 写入 `_output/distilled-<name>-draft.md`
   - 更新 `_output/distill-progress.yaml`（step_02: completed, items_classified: N）

### 多消费者视图

同一个 change_items 数据，按消费者视角过滤：

- **前端开发者**：过滤 `layer: frontend` 的 ADD/MODIFY 项，展示 component 和 capability
- **BFF 开发者**：过滤 `layer: bff` 的 ADD/MODIFY 项，展示 files 和 template
- **后端开发者**：过滤 `layer: backend` 的 ADD/MODIFY 项，展示 api_endpoint 和 data_model
- **QA 测试**：展示所有 validations 和 business_rules，不论层
- **项目经理**：展示变更分类汇总表和风险项

这些是同一数据的读取过滤，不是独立输出。

## VALIDATION

1. **分类完整性** — 每个路由匹配结果都有 change_type
2. **分类一致性** — change_type 与 PRD 描述一致（ADD 不用于已有功能）
3. **ID 唯一** — 每个 change_item 的 id 全局唯一
4. **YAML 合法** — 嵌入的 YAML 块可被解析器解析
5. **字段覆盖** — 所有 step-01 提取的原始字段都已分配到 change_item

## NEXT STEP

分类完成 → 进入 [step-03-confirm.md](./step-03-confirm.md)
