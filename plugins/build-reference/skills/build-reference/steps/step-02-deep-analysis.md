# step-02: 深度分析（Phase 2）

## MANDATORY RULES

1. 每个模块独立分析，使用 Sub-agent 并行处理
2. 只写确定的内容，不确定的标 TODO + confidence: low
3. 文件路径必须用 Glob/Grep 验证存在，不猜测
4. 每个 Sub-agent 返回摘要 ≤ 1000 tokens（~35 行）
5. 遵循 YAML 规范（snake_case、`# ---` 分隔、每文件 ≤ 300 行）
6. 自定义字段必须写清注释（含义 + 取值范围）
7. **部落知识挖掘**：必须挖掘代码注释、隐式约定、非显而易见的模式
8. **业务逻辑提取**：不仅记录代码做什么，还要记录为什么这样做
9. **跨模块依赖图**：必须绘制模块间的数据流和调用关系

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 模块索引 | `_output/modules-index.yaml` | YAML |
| 项目源代码 | 项目目录 | 源文件 |
| 项目类型 | modules-index 中确认 | frontend / bff / backend |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 7 个 reference 文件 | `_reference/00-index.md` + `01~06.yaml` | Markdown + YAML |
| 进度更新 | `_output/build-reference-progress.yaml` | YAML |

### reference 文件结构（按关注点维度，7 个文件）

知识按**本质属性**分文件，不按工作流步骤分。每个文件是一个独立的知识维度，可被多个工作流步骤按需引用。

| 文件 | 维度 | 回答的问题 | 说明 |
|------|------|-----------|------|
| `00-index.md` | 导航 | 知识库有什么？在哪？ | 门面，含按维度导航 + 实体索引 |
| `01-entities.yaml` | 实体 | 项目里有什么东西？ | 枚举、核心类型、数据结构、注册信息 |
| `02-architecture.yaml` | 结构 | 项目怎么组织的？ | 目录结构、注册机制、数据流、模块依赖 |
| `03-conventions.yaml` | 规范 | 代码该怎么写？ | 命名规范、代码模式（gold patterns）、注册模式、反模式 |
| `04-constraints.yaml` | 约束 | 什么必须为真？ | 白名单、校验规则、致命错误、i18n 规则 |
| `05-mapping.yaml` | 映射 | PRD 怎么对应代码？ | PRD 路由表、能力边界、字段映射、变更分类 |
| `06-glossary.yaml` | 术语 | 人话 ↔ 机器话？ | 业务术语、同义词、工作量标准、报告格式 |

### 各文件元数据（统一）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <项目标识>
last_verified: "<日期>"
verify_cadence: "14d"
```

## EXECUTION

### 执行步骤

1. **读取模块索引**
   - 加载 `_output/modules-index.yaml`
   - 获取模块列表和 5 问清单

2. **Sub-agent 并行分析**
   - 对每个模块启动一个 Sub-agent（使用 Agent tool）
   - Sub-agent Prompt 模板：

   ```
   你正在分析 {project_name} 的 {module_name} 模块。

   ## 任务
   阅读以下文件并回答 5 个问题：
   {five_questions}

   ## 输出格式
   严格 YAML 格式，不确定的标记 TODO：
   module: {module_name}
   files_scanned: [...]
   answers: [...]
   key_files: [...]
   non_obvious_patterns: [...]

   ## 规则
   1. 只写确定的内容，不确定的一律标 TODO
   2. 文件路径必须是实际存在的
   3. 不要写废话，每行都要有信息量
   4. 总长度控制在 35 行以内
   ```

   - 收集所有 Sub-agent 的返回结果

3. **部落知识挖掘（Tribal Knowledge Mining）**

   基于 Meta 的发现：**代码注释中的隐式知识产出最多价值**。对每个模块额外执行：

   **3a. 注释中的隐式规则挖掘**
   - Grep 搜索 `// TODO`、`// FIXME`、`// HACK`、`// NOTE`、`// XXX`、`// WARNING` 等标记
   - Grep 搜索中文注释（`// [\u4e00-\u9fff]`），这些通常是业务逻辑说明
   - 提取注释中提到的隐式约定，例如：
     - "这个字段必须和 xxx 一起使用"
     - "这里有个坑：xxx"
     - "留着做备份，目前并没有用上"
   - 将发现的隐式规则写入 `03-conventions.yaml` 的 `non_obvious_patterns` 部分

   **3b. Git 历史中的变更模式挖掘**
   - 执行 `git log --oneline -30 -- <module_path>` 获取最近变更
   - 执行 `git log --all --oneline --diff-filter=A -- <module_path>` 找到首次创建
   - 分析 commit message 中的业务意图
   - 记录热点文件（频繁修改的文件）和冷文件（长期不变的文件）

   **3c. 非显而易见的模式（Non-Obvious Patterns）**
   - 搜索代码中不在 README/文档中但影响行为的隐式约定：
     - 命名约定（文件名必须匹配组件名）
     - 隐式依赖（A 模块的某个功能依赖 B 模块的某个全局变量）
     - 副作用（修改某个文件会影响另一个文件的运行时行为）
     - 编译/构建时约束（某些文件必须在其他文件之前编译）
   - 每个发现的模式记录：`{ pattern, detail, source: "code_comment" | "git_history" | "code_structure" }`

   **3d. 模式挖掘（Pattern Mining）— 从代码反推路由规则**

   目标：将代码中隐含的 PRD→代码映射关系显式化，为 `05-mapping.yaml` 的 `prd_routing` 和 `golden_samples` 提供数据。

   **3d-1. Switch-case / if-else 分支扫描**
   - Grep 搜索 `switch\s*\(` 和 `case\s+` 定位所有分发逻辑
   - 对每个 switch-case：
     - 记录 switch 变量名（通常是 `campaign_type`、`trigger_type` 等）
     - 记录每个 case 分支对应的处理函数/文件
     - 推导出 "PRD 说 XX → 走 YY 分支 → 改 ZZ 文件" 的路由规则
   - 将发现的分支模式编码为 `prd_routing` 候选项：
     ```yaml
     # 示例：从 switch-case 反推出的路由
     - prd_pattern: "新增活动类型"
       evidence: "details/index.ts switch(campaignType) 有 25 个分支"
       target:
         files:
           create: ["details/[NewType].ts"]
           modify_required: ["details/index.ts"]  # 需加 switch 分支
     ```

   **3d-2. Import 依赖链追踪**
   - 对每个关键文件（如 basic.ts、detail.ts），Read 其 import 语句
   - 追踪 `import ... from` 链，构建 `{文件 → 依赖文件}` 映射
   - 识别"枢纽文件"（被 ≥3 个文件 import 的文件），这些是变更的高影响目标
   - 结果写入 `02-architecture.yaml` 的 `import_dependency_hub`

   **3d-3. 黄金样本提取（Golden Sample Extraction）**
   - 选择 2-3 个已实现的典型实体（BFF: 活动类型；前端: 组件；后端: API）
   - 对每个样本：
     1. Grep 搜索该实体的所有文件引用
     2. Read 关键文件，记录"新增此实体时改了哪些文件、按什么模式改"
     3. 总结为 `golden_sample` 条目
   - 选择标准：选最简单（文件变更最少）且有相似实体的样本
   - 结果写入 `05-mapping.yaml` 的 `golden_samples`

   **3d-4. 差异分析（Diff Analysis）**
   - 选择 2 对相似实体（如 GasStation vs NoThresholdGasStation）
   - 分别 Read 两者在关键文件中的代码片段
   - 对比差异，推导出"什么 PRD 差异导致什么代码差异"
   - 将差异编码为 `change_type_rules` 的补充规则
   - 示例：PRD 说"有门槛" vs "无门槛" → detail.ts 中是否需要 min_amount 字段

4. **业务逻辑提取**

   不只记录"代码做了什么"，还要记录"为什么这样做"：

   **4a. 业务规则提取**
   - 读取配置文件中的常量和枚举，记录每个值的业务含义
   - 读取条件判断逻辑（if/switch），记录每个分支的业务场景
   - 读取校验规则，记录每个校验的业务原因

   **4b. 数据流追踪**
   - 追踪关键数据从入口到出口的完整路径
   - 记录数据在每个节点的变换规则
   - 特别注意：数据在哪个节点被过滤、聚合、转换

   **4c. 业务术语映射**
   - 建立代码变量名 → 业务术语的映射表
   - 记录同义词（不同模块对同一概念的不同命名）
   - 这部分信息写入 `06-glossary.yaml` 的 `terms` 部分

5. **跨模块依赖图生成**

   分析模块间的依赖关系，写入 `02-architecture.yaml` 的 `cross_module_dependencies` 部分：

   ```yaml
   cross_module_dependencies:
     - from: "basic"
       to: "rules"
       type: "data_flow"
       detail: "basic 中的 campaign_type 决定 rules 中 rewardCondition 的渲染模式"
       critical: true

   dependency_rules:
     - "修改 campaignType 枚举必须同步更新 rules 中的 switch-case"
     - "新增活动类型必须注册到 routing 和 group 模块"
   ```

6. **按维度合并到标准文件**

   将各模块的分析结果按知识维度合并到 7 个标准文件：

   | 目标文件 | 从模块分析中提取的内容 |
   |----------|----------------------|
   | **01-entities.yaml** | 枚举定义（枚举值 + 业务含义 + 定义文件）、核心类型（Builder/Schema 等）、数据结构、注册信息 |
   | **02-architecture.yaml** | 目录结构、注册机制、数据流、跨模块依赖图、分层架构 |
   | **03-conventions.yaml** | 命名规范、代码模式（gold patterns 含完整代码范例）、注册模式、反模式、模板函数签名、non_obvious_patterns |
   | **04-constraints.yaml** | 白名单、枚举校验规则、致命错误清单、i18n key 规则、字段类型约束 |
   | **05-mapping.yaml** | PRD 路由表（prd_pattern → target）、能力边界（can_do/cannot_do）、能力清单（inventory）、字段映射、变更分类标准、黄金样本（golden_samples）、PRD 结构模式（structural_patterns） |
   | **06-glossary.yaml** | 业务术语表（code ↔ business）、同义词映射、工作量标准、报告格式定义 |
   | **00-index.md** | 导航索引（按维度）+ 实体索引（见下方格式） |

7. **实体索引提取**（LLM Wiki 实体交叉引用）

   基于 LLM Wiki 的实体页面思想，识别跨文件出现的核心域实体，生成实体索引表。这允许 Agent 按需加载特定 YAML，而非全量加载浪费 token。

   **提取规则：**
   - 识别在 ≥2 个 YAML 文件中出现的域概念（枚举名、核心类型、关键数据结构、业务术语）
   - 不记录通用技术概念（如 Promise、Array、interface），只记录**项目特有**实体
   - 记录每个实体在哪些 YAML 文件的哪些章节出现

   **执行步骤：**
   1. 遍历已生成的 01~06.yaml，提取所有枚举名、关键类型名、核心数据结构名
   2. 统计每个实体在哪些文件中出现，记录出现的章节/字段
   3. 筛选出现在 ≥2 个文件中的实体
   4. 生成实体索引表，嵌入 `00-index.md` 的 `## 实体索引` 节

   **实体索引表格式（嵌入 00-index.md）：**

   ```markdown
   ## 实体索引

   > 跨文件核心域实体。Agent 可按需加载对应 YAML，而非全量加载。

   | 实体 | entities | architecture | conventions | constraints | mapping | glossary |
   |------|----------|-------------|-------------|-------------|---------|----------|
   | CampaignType | enum_def | data_flow | registration | whitelist | routing, inventory | glossary |
   | StepName | enum_def | data_flow | render_steps | - | routing | - |
   | Builder | type_def | architecture | template_fn | - | capability | - |
   ```

8. **按项目类型定制**
   - **前端**：05-mapping 的 prd_routing → `target: { component }` + inventory capabilities（implemented/change_type）
   - **BFF**：05-mapping 的 prd_routing → `target: { files: { create, modify_required, modify_conditional } }` + inventory
   - **后端**：05-mapping 的 prd_routing → `target: { api_endpoint, data_model }` + inventory

9. **保存文件**
   - 写入 `_reference/` 目录
   - 更新进度文件（phase_2: completed）

### 各文件内容指导

#### 01-entities.yaml（实体维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 枚举定义 ---
enums:
  CampaignType:
    definition_file: "<路径>"
    values:
      - name: "ORDER"
        business_meaning: "订单活动"
      - name: "GAS_STATION"
        business_meaning: "加油站活动"
    # 层特有字段
    registration: "src/config/template/render/rules/details/index.ts"  # BFF
    # component_mapping: "src/components/FormField/"  # 前端
    # api_endpoint: "POST /api/v1/campaign/create"  # 后端

  StepName:
    definition_file: "<路径>"
    values:
      - name: "BASIC"
        business_meaning: "基础信息"
        render_order: 1

# --- 核心类型 ---
types:
  Builder:
    definition_file: "<路径>"
    description: "Schema 构建器"
    key_methods: ["parseOnce", "parse"]
    usage_note: "所有模板函数通过 Builder.parseOnce 生成 Schema"

# --- 核心数据结构 ---
structures:
  ValidationResult:
    definition_file: "<路径>"
    fields: [...]
```

#### 02-architecture.yaml（结构维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 目录结构 ---
directory_structure: |
  <用缩进表示的目录树，标注每个目录的职责>

# --- 注册机制 ---
registration_mechanisms:
  campaign_type_registration:
    location: "src/config/template/render/rules/details/index.ts"
    pattern: "switch-case"
    description: "新增活动类型必须在 switch 中添加分支"
  linkage_registration:
    location: "..."

# --- 数据流 ---
data_flow:
  - path: "Controller → Service → ComponentModel → Schema"
    description: "主渲染流程"
    layers: ["controller", "service", "model"]

# --- 跨模块依赖 ---
cross_module_dependencies: [...]

dependency_rules: [...]
```

#### 03-conventions.yaml（规范维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 命名规范 ---
naming:
  constants: "UPPER_SNAKE_CASE"
  types: "PascalCase"
  functions: "camelCase"
  files: "kebab-case"
  enum_values: "kebab-case 字符串"

# --- 代码模式（Gold Patterns）---
patterns:
  template_function:
    description: "所有模板函数签名一致"
    example: |
      export function getXxxTemplate(ctx: TemplateContext): Schema[] {
        return Builder.parseOnce(template, { ...ctx })
      }
    files_to_follow: ["src/config/template/render/basic.ts"]

  campaign_registration:
    description: "新增活动类型的标准注册流程"
    steps:
      - "1. 在 campaignType.ts 添加枚举值"
      - "2. 在 details/index.ts 添加 switch-case"
      - "3. 创建 details/[NewType].ts 模板"

# --- 反模式（禁止做的事）---
anti_patterns:
  - pattern: "硬编码枚举值"
    detail: "必须使用常量定义，不允许 magic string"
    detection: "Grep 搜索字符串字面量匹配已知枚举值"

# --- 非显而易见的模式 ---
non_obvious_patterns:
  - pattern: "模板函数必须返回 Schema[]"
    detail: "即使只有一个元素也必须用数组包裹"
    source: "code_comment"
```

#### 04-constraints.yaml（约束维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 白名单 ---
whitelists:
  target_projects: ["dive-bff", "dive-template-bff"]
  i18n_prefixes: ["dive_", "marketing_"]

# --- 枚举校验 ---
enum_validations:
  - entity: "CampaignType"
    valid_values: ["ORDER", "GAS_STATION", "COURIER_RUSH", "SHIFT_CHECKIN"]
    source_file: "src/config/constant/campaignType.ts"

# --- 致命错误（生成代码绝不能违反）---
fatal_errors:
  - rule: "生成的字段必须是 01-entities.yaml 中的合法字段"
    severity: "fatal"
  - rule: "import 路径必须使用相对路径"
    severity: "fatal"

# --- 警告规则 ---
warnings:
  - rule: "新增文件应遵循现有目录结构"
    severity: "warning"

# --- 检查清单 ---
checklists:
  add_new_campaign_type:
    - "campaignType.ts 添加枚举"
    - "details/index.ts 添加 switch"
    - "创建新模板文件"
    - "更新 preview options"
```

#### 05-mapping.yaml（映射维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 能力边界 ---
capability_boundary:
  can_do:
    - name: "Schema 生成"
      example: "为活动生成表单 Schema"
      how: "通过 Builder + template 函数"
  cannot_do:
    - "不负责 options 内容（由后端 API 返回）"

# --- PRD 路由表 ---
prd_routing:
  - prd_pattern: "新增活动类型"
    prd_keywords: ["新增活动", "新奖励类型", "新 campaign type"]
    change_type: ADD
    target:
      files:
        create: [...]
        modify_required: [...]
        modify_conditional: [...]
    confidence_rule: high
    check_capabilities: true
    default_action: may_need_code
    note: "需在 switch-case 中添加新分支"

# --- 能力清单 ---
inventory:
  <ItemName>:
    target_file: "<路径>"
    description: "<一句话>"
    capabilities:
      - pattern: "<业务描述>"
        prd_keywords: [...]
        implemented: <boolean>
        change_type: <ADD|MODIFY|DELETE|NO_CHANGE>
        how: "<实现方式>"
        files_to_modify: [...]

# --- 字段映射 ---
field_mappings:
  - prd_field: "骑手类型"
    code_field: "rider_type"
    target_file: "src/config/template/render/basic.ts"
    confidence: high

# --- 变更分类标准 ---
change_type_rules:
  ADD: "PRD 明确说新增/添加/支持XX"
  MODIFY: "PRD 明确说修改/调整/变更/更新"
  DELETE: "PRD 明确说移除/删除/废弃/下线"
  NO_CHANGE: "PRD 描述匹配现有能力，无需改动"

# --- 黄金样本（参考实现）---
golden_samples:
  - name: "<样本名称，如'新增油站活动'>"
    reference_entity: "<参考实体名，如 GasStation>"
    similar_to: ["<相似实体>"]
    prd_pattern_matched: "<匹配的 prd_pattern>"
    files_changed:
      - path: "<文件路径>"
        change: "<改了什么>"
        pattern: "<按什么模式改，如'在枚举对象中添加 key: value'>"
        code_snippet: "<关键代码片段（3-5行），展示变更模式>"
    summary: "<一句话总结：新增此类实体需要改哪些文件、按什么顺序>"

  # BFF 示例：
  - name: "新增油站活动"
    reference_entity: "GasStation"
    similar_to: ["NoThresholdGasStation", "FirstRefuelingGasStation"]
    prd_pattern_matched: "新增活动类型"
    files_changed:
      - path: "src/config/constant/campaignType.ts"
        change: "添加 GasStation 枚举"
        pattern: "在枚举对象中添加 key: value"
        code_snippet: "GasStation: 26,"
      - path: "src/config/template/render/rules/details/gasStation.ts"
        change: "新建文件"
        pattern: "导出 getGasStationDetailsTemplate 函数，使用 Builder.parseOnce"
      - path: "src/config/template/render/rules/details/index.ts"
        change: "switch-case 添加分支"
        pattern: "case 'GasStation': return getGasStationDetailsTemplate"
    summary: "新增活动类型需要：1)加枚举 2)建 detail 模板 3)加 switch 分支"

# --- PRD 结构模式（从 PRD 文档结构推断意图）---
structural_patterns:
  - pattern: "表格含数值列+行数可变"
    indicates: "新增奖励条件/梯度"
    prd_keywords_hint: ["梯度", "阶梯", "tier"]
    confidence: medium
    routing_fallback: "新增奖励条件/梯度"

  - pattern: "二选一/互斥/根据XX选择不同配置"
    indicates: "添加字段联动"
    prd_keywords_hint: ["互斥", "二选一", "条件"]
    confidence: medium
    routing_fallback: "添加字段联动"

  - pattern: "条件展示/勾选后出现/满足条件后显示"
    indicates: "添加字段联动 (visible)"
    prd_keywords_hint: ["条件展示", "勾选", "可见"]
    confidence: medium
    routing_fallback: "添加字段联动"

  - pattern: "新增选项/类型/分类"
    indicates: "新增枚举值"
    prd_keywords_hint: ["新增", "类型", "选项"]
    confidence: medium
    routing_fallback: "新增活动类型"

  - pattern: "批量操作/批量导入/批量创建"
    indicates: "新增批量配置"
    prd_keywords_hint: ["批量", "导入", "模板"]
    confidence: medium
    routing_fallback: "新增批量配置"

# --- 层专属扩展 ---
# 前端: bff_linkage_chain, workload_calibration
# BFF: activity_templates, d_component_families, step_linkage_map, linkage_triggers
# 后端: api_contracts, data_models
```

#### 06-glossary.yaml（术语维度）

```yaml
version: "2.0"
layer: <frontend|bff|backend>
project: <string>
last_verified: "<日期>"

# --- 业务术语表 ---
terms:
  - code: "CampaignType"
    business: "活动类型"
    synonyms: ["campaign", "活动", "活动类型"]
    description: "运营活动的分类标识"
    prd_keywords: ["新增活动", "新活动类型", "新 campaign"]  # PRD 中可能的关键词

  - code: "rewardCondition"
    business: "梯度奖励"
    synonyms: ["奖励条件", "奖励梯度", "阶梯奖励", "tier"]
    prd_keywords: ["梯度", "阶梯", "奖励条件", "门槛"]

  - code: "message"
    business: "触达/推送"
    synonyms: ["推送", "Push", "消息", "通知", "卡片", "触达"]
    prd_keywords: ["推送", "触达", "消息模板"]

  - code: "placeholder"
    business: "占位符"
    synonyms: ["模板变量", "变量替换", "变量"]
    prd_keywords: ["占位符", "模板变量"]

  - code: "linkage"
    business: "字段联动"
    synonyms: ["联动", "visible", "disabled", "条件展示", "条件显隐"]
    prd_keywords: ["联动", "条件展示", "勾选后显示", "二选一", "互斥"]

  - code: "preview"
    business: "预览"
    synonyms: ["预览", "人群分页", "受众分群"]
    prd_keywords: ["预览", "人群", "分页"]

  - code: "batch"
    business: "批量"
    synonyms: ["批量", "批量创建", "批量导入"]
    prd_keywords: ["批量", "导入", "批量模板"]

# --- 工作量标准 ---
workload_standards:
  S: "新增 1-2 个字段，不涉及新文件"
  M: "新增 3-5 个字段，或涉及 1 个新文件"
  L: "新增活动类型，涉及多文件变更"

# --- 报告格式 ---
report_format:
  change_types: [ADD, MODIFY, DELETE, NO_CHANGE]
  confidence_levels: [high, medium, low]
  verification_sources: [code_verified, reference_only, code_contradicts_reference]
```

### 工作流步骤按需加载参考

各工作流步骤（如 prd-distill 的 step-01~03）按需加载以下文件：

| 工作流步骤 | 需加载的 reference 文件 |
|-----------|----------------------|
| PRD 蒸馏（路由匹配） | 05-mapping（含 golden_samples + structural_patterns）+ 01-entities + 06-glossary（含 prd_keywords 同义词）|
| 项目分析（结构扫描） | 02-architecture + 01-entities |
| 变更计划（分类规划） | 03-conventions + 04-constraints + 05-mapping |
| 代码生成 | 03-conventions + 02-architecture + 01-entities |
| 代码验证 | 04-constraints + 03-conventions |
| 输出报告 | 06-glossary |

## CONFIRMATION POINT

逐模块展示提取的知识：

1. 展示该模块的 5 个问题及答案
2. 标注 TODO 和 low confidence 项
3. 用户可逐项确认、修改、补充
4. 确认后更新对应 YAML 文件

全部模块确认完成后：
- 展示完整 `_reference/` 目录结构
- 统计 TODO 数量和 confidence 分布
- 询问是否进入 Phase 3 质量门控

## VALIDATION

1. **7 文件齐全** — _reference/ 下有 00-index.md + 01~06.yaml
2. **YAML 合法** — 每个文件可被 YAML 解析器解析
3. **元数据完整** — 每个文件有 version/layer/project/last_verified
4. **路径有效** — 所有 target_file / key_files / definition_file 路径存在
5. **TODO 可控** — TODO 总数 < 15 个

## NEXT STEP

确认完成 → 进入 [step-03-quality-gate.md](./step-03-quality-gate.md)
