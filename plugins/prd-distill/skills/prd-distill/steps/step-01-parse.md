# step-01: 解析 + 路由匹配 + 代码锚定

## MANDATORY RULES

1. 蒸馏必须结合 `_reference/05-mapping.yaml` 中的路由表进行匹配
2. **reference 是快速通道，源码是最终权威** — 涉及功能是否已存在的判断，必须用 Grep/Read 验证源码
3. 每个字段/需求项必须标注 confidence（high / medium / low）和 source_ref
4. 不确定的映射必须标 `confidence: low`，禁止猜测后标为 high
5. Token 控制：蒸馏阶段 < 10K tokens
6. 支持两种输入：PRD 文件路径（.docx / .md）或自然语言描述
7. 本步骤做解析、路由匹配和初步代码验证，不做最终变更分类（分类在 step-02 进行）

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| PRD 文档 | 用户提供 | .docx / .md / 纯文本 |
| PRD 路由表 | `_reference/05-mapping.yaml` → `prd_routing` | YAML |
| 黄金样本 | `_reference/05-mapping.yaml` → `golden_samples` | YAML |
| PRD 结构模式 | `_reference/05-mapping.yaml` → `structural_patterns` | YAML |
| 能力清单 | `_reference/05-mapping.yaml` → `inventory` | YAML |
| 能力边界 | `_reference/05-mapping.yaml` → `capability_boundary` | YAML |
| 枚举定义 | `_reference/01-entities.yaml` → `enums` | YAML |
| 业务术语 | `_reference/06-glossary.yaml` → `terms`（含 `prd_keywords` + `synonyms`）| YAML |
| 后端技术文档（可选） | 用户提供 | .md 文件 |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 路由结果 | `_output/distilled-<name>-routing.md` | Markdown + YAML |

### 路由结果格式

```markdown
---
source: "PRD 文件名"
routed_at: "2026-04-24"
routed_by: "step-01-parse"
layer: <frontend|bff|backend>
---

# PRD 路由结果 — <活动名称>

## 摘要
| 项目 | 值 |
|------|-----|
| 活动类型 | 新增/已有 |
| 影响模块 | ... |
| 总需求数 | N |
| 路由命中数 | M |
| 未匹配数 | K |

## 路由匹配明细
| # | PRD 描述 | 匹配路由 | target | confidence | 验证来源 | 匹配方式 |
|---|---------|---------|--------|------------|---------|---------|
| 1 | ... | prd_pattern 名 | component/file/API | high/medium/low | code_verified/reference_only/code_contradicts | keyword_exact/synonym/structural_pattern/golden_sample/fallback |

## 未匹配需求
（需要进入 step-02 手动分类）

## 原始提取
（字段清单、联动关系、校验规则等原始数据，待 step-02 结构化）

## 结构化数据
\`\`\`yaml
meta:
  source: "..."
  layer: <frontend|bff|backend>
  routed_at: "..."

routing_results:
  - { prd_ref: "...", matched_pattern: "...", target: {...}, confidence: high, verification_source: code_verified, match_method: keyword_exact }
  - { prd_ref: "...", matched_pattern: "...", target: {...}, confidence: high, verification_source: code_verified, match_method: synonym, synonym_matched: "阶梯→梯度" }
  - { prd_ref: "...", matched_pattern: null, confidence: low, verification_source: reference_only, match_method: fallback }

raw_fields: [...]
raw_linkages: [...]
raw_validations: [...]
raw_business_rules: [...]
\`\`\`
```

## EXECUTION

### 执行步骤

1. **输入处理**
   - 如果是 .md：直接 Read
   - 如果是自然语言：直接使用文本
   - 如果是 .docx：按以下**分级回退**策略转换为 markdown（必须剥离 base64 图片，避免输出膨胀）：

     **第一优先：mammoth + sed 清理（效果最佳，输出精简，AI 友好）**
     ```bash
     npx mammoth --output-format markdown "$PRD_FILE" 2>/dev/null | sed 's/!\[.*\](data:image[^)]*)/[IMAGE]/g' > /tmp/prd-converted.md
     ```
     - 图片替换为 `[IMAGE]` 占位符
     - Word 表格展平为列表（反而更适合 LLM 解析）
     - 输出约 20KB（对比 pandoc 的 375KB 冗长表格）
     - 需要 Node.js/npm 环境

     **第二优先：pandoc + 清理（全平台，内容完整但较冗长）**
     ```bash
     pandoc "$PRD_FILE" --from docx --to markdown --wrap=none 2>/dev/null | sed 's/!\[[^\]]*\](data:image[^)]*)/[IMAGE]/g; s/!\[[^\]]*\](\/tmp\/prd-media\/[^)]*){[^}]*}/[IMAGE]/g' > /tmp/prd-converted.md
     ```
     - 保留 Word 表格结构（但单元格内容冗长，约 375KB）
     - 安装：`brew install pandoc`（macOS）/ `apt-get install pandoc`（Linux）/ `choco install pandoc`（Windows）
     - 无需 Node.js，适合后端环境

     **第三优先：textutil（仅 macOS，零依赖）**
     ```bash
     textutil -convert txt -stdout "$PRD_FILE" > /tmp/prd-converted.txt
     ```
     - 输出纯文本（非 markdown），但内容完整
     - 仅 macOS 自带，Linux/Windows 不可用

     **最终回退：提示用户**
     > 无法自动转换 .docx 文件。请提供以下任一格式的 PRD：
     > - `.md` 文件（可用 `pandoc prd.docx -o prd.md` 转换）
     > - 直接粘贴 PRD 文本内容
     > - 安装 pandoc 后重试：`brew install pandoc` / `apt install pandoc`

     **执行逻辑**：按优先级依次尝试，第一个成功的即使用。

2. **加载领域知识**
   - 读取 `_reference/05-mapping.yaml`（路由表 + 能力清单 + 能力边界）
   - 读取 `_reference/01-entities.yaml`（枚举定义 + 核心类型）
   - 读取 `_reference/06-glossary.yaml`（业务术语表）
   - 确定 `layer`（frontend / bff / backend）
   - 提取 `prd_routing`（PRD 关键词 → 目标映射）
   - 提取 `inventory`（能力清单）
   - 提取 `capability_boundary`（能力边界）
   - 提取层专属扩展（前端的 `bff_linkage_chain`、BFF 的 `activity_templates` 等）

3. **PRD 解析 + 路由匹配（5 级匹配链）**
   - 逐段解析 PRD 内容，识别独立的功能需求描述
   - 对每个需求描述，按以下**5 级优先级链**依次匹配：

   **第 1 级：精确关键词匹配（prd_routing.prd_keywords）**
   - 在 `prd_routing` 的 `prd_keywords` 数组中精确匹配
   - 命中 → `confidence: confidence_rule`（通常为 high）
   - 标记 `match_method: keyword_exact`

   **第 2 级：同义词匹配（06-glossary.prd_keywords + synonyms）**
   - 如果第 1 级未命中，读取 `06-glossary.yaml` 中所有 `terms` 的 `prd_keywords` 和 `synonyms`
   - 用同义词在 `prd_routing` 的 `prd_keywords` 中匹配
   - 命中 → `confidence: high`（同义词匹配可信度等同精确匹配）
   - 标记 `match_method: synonym`
   - 示例：PRD 写"阶梯奖励" → glossary synonyms 映射到 "rewardCondition" → 匹配路由 "新增奖励条件/梯度"

   **第 3 级：结构模式匹配（05-mapping.structural_patterns）**
   - 如果第 2 级未命中，分析 PRD 段落的**文档结构**：
     - 是否含"表格 + 数值列 + 可变行数" → 梯度/奖励条件
     - 是否含"二选一 / 互斥 / 根据XX选择" → 字段联动
     - 是否含"条件展示 / 勾选后出现" → visible 联动
     - 是否含"新增选项 / 类型 / 分类" → 新增枚举
     - 是否含"批量 / 导入 / 模板" → 批量配置
   - 在 `05-mapping.yaml` 的 `structural_patterns` 中查找匹配
   - 命中 → `confidence: medium`
   - 标记 `match_method: structural_pattern`
   - 使用 `routing_fallback` 指向对应的 prd_routing 条目

   **第 4 级：黄金样本相似度匹配（05-mapping.golden_samples）**
   - 如果第 3 级未命中，对比 PRD 描述与 `golden_samples` 的相似度：
     - PRD 描述"新增 XX 活动类型" → 匹配 golden_sample 中 `prd_pattern_matched: "新增活动类型"` 的样本
     - 参考样本的 `files_changed` 推断目标文件
   - 命中 → `confidence: medium`
   - 标记 `match_method: golden_sample`
   - 在路由结果中附加 `reference_sample: <golden_sample.name>`

   **第 5 级：兜底（未匹配）**
   - 全部未命中 → `matched_pattern: null`，`confidence: low`
   - 根据通用规则推断 `change_type`（PRD 含"新增"→ADD，"修改"→MODIFY，"删除"→DELETE）
   - 标记 `match_method: fallback`
   - 需在 step-03 中强制人工确认

   - 匹配结果包含：
     - `target`：按层解析（前端→component, BFF→files, 后端→api_endpoint）
     - `confidence_rule`：路由表中的默认置信度
     - `check_capabilities`：是否需要进一步检查 inventory
     - `match_method`：匹配方式（keyword_exact / synonym / structural_pattern / golden_sample / fallback）

4. **能力检查（仅 check_capabilities=true 的项）**
   - 从 `inventory` 中查找对应项
   - 检查 `capabilities[].implemented` 状态
   - 记录已实现和未实现的能力项

5. **代码锚定验证（Code Grounding）— 核心步骤**

   **原则：reference 提供初始假设，源码提供最终证据。不允许 AI 仅凭 reference 判断功能是否已实现。**

   对以下场景**必须**深入源码验证：

   **场景 A：reference 标记 `implemented: true`，需验证源码是否真的支持**
   - 用 Grep 在 `target_file` 中搜索相关关键词/函数名/组件名
   - 用 Read 读取目标文件的关键段落，确认能力确实存在
   - 如果源码中**找不到**对应实现 → 标记 `verification_source: code_contradicts_reference`，将 confidence 降级为 low，并在需确认项中说明

   **场景 B：reference 标记 `implemented: false`，需确认源码是否已更新**
   - 用 Grep 搜索是否有新增的相关代码（reference 可能过期）
   - 如果源码中**已找到**对应实现 → 标记 `verification_source: code_contradicts_reference`，升级为已实现
   - 如果确认未实现 → 标记 `verification_source: code_verified`

   **场景 C：路由匹配 confidence < high（未匹配或 low）**
   - 必须用 Grep 搜索项目中是否有相关组件/字段/API
   - 搜索策略：
     - 前端：搜索组件目录 `src/components/FormField/` 中是否有匹配的组件
     - BFF：搜索 `config/template/render/` 和 `config/constant/` 中是否有匹配的模板/枚举
     - 后端：搜索 API 路由和数据模型定义
   - 如果源码中找到 → 更新匹配结果，标注 `verification_source: code_verified`
   - 如果源码中也找不到 → 标记 `verification_source: reference_only`，保持 confidence: low

   **场景 D：涉及枚举值/字段映射**
   - 新增枚举值：用 Grep 搜索枚举定义文件，确认该枚举是否已存在
   - 字段映射：用 Grep 搜索目标文件中是否已有该字段名
   - 不允许 AI 猜测字段是否存在，必须搜索确认

   **验证结果标记（每个路由匹配项）：**
   - `verification_source: code_verified` — 已用源码验证，结论可信
   - `verification_source: reference_only` — 仅参考 reference（用于明确的通用组件如 Select/Input）
   - `verification_source: code_contradicts_reference` — 源码与 reference 不一致，需人工确认

6. **原始数据提取**
   - 从 PRD 中提取所有字段（名称、类型、默认值、校验规则）
   - 提取联动关系（字段间依赖）
   - 提取校验规则（必填、范围、格式等）
   - 提取业务规则（枚举、可见性条件等）
   - 提取奖励条件（梯度、门槛等）
   - 为每个提取项标注 `source_ref`（PRD 原文段落引用）

7. **生成路由结果**
   - 按 Markdown + YAML 格式生成
   - 写入 `_output/distilled-<name>-routing.md`
   - 更新 `_output/distill-progress.yaml`（step_01: completed）

### 层差异处理

| 步骤 | 前端 | BFF | 后端 |
|------|------|-----|------|
| 路由匹配 | prd_pattern → component | prd_pattern → files | prd_pattern → api_endpoint |
| 能力检查 | inventory[*].capabilities.implemented | inventory[*].capabilities.implemented | inventory[*].capabilities.implemented |
| 字段标注 | d_component + component | target_file + bff_name | api_field + method |
| 目标格式 | `{ component: "Name" }` | `{ files: { create, modify_required, modify_conditional } }` | `{ api_endpoint: "...", data_model: "..." }` |

## VALIDATION

1. **路由覆盖率** — PRD 中 80%+ 的需求描述成功匹配到路由
2. **字段完整性** — PRD 中所有明确提到的字段都已提取
3. **置信度标注** — 每个匹配项都有 confidence 值
4. **来源引用** — 每个提取项都有 source_ref
5. **YAML 块合法** — 嵌入的 YAML 可被解析器解析
6. **层信息正确** — layer 字段与 `05-mapping.yaml` 一致
7. **验证来源标注** — 每个路由匹配项都有 `verification_source` 值
8. **代码锚定覆盖** — ADD/MODIFY 类型的匹配项必须为 `code_verified`（至少覆盖 check_capabilities=true 的项）

## NEXT STEP

路由匹配完成 → 进入 [step-02-classify.md](./step-02-classify.md)
