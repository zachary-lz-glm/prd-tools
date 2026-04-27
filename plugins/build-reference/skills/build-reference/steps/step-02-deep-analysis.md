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
10. **只分析业务源码**（遵循 workflow.md 准则 7-8）：
    - 排除目录：`node_modules`, `dist`, `build`, `coverage`, `__tests__`, `__mocks__`, `mock`, `mocks`, `.claude`, `_output`, `_reference`
    - 排除模式：`*.config.*`, `*.mock.*`, `*.test.*`, `*.spec.*`, `*.fixture.*`, `*.d.ts`
    - 排除配置：`.eslintrc*`, `.prettierrc*`, `tsconfig.*`, `jest.*`, `webpack.*`, `vite.*`
    - Grep 搜索注释/模式时，加 glob 过滤：`--glob '!node_modules' --glob '!*.config.*' --glob '!*.mock.*' --glob '!*.test.*'`
11. **核心文件优先**（遵循 workflow.md 准则 8）：
    - BFF：`config/template/**`, `config/constant/**`, `handler/**`
    - 前端：`src/components/**`, `src/pages/**`, `src/store/**`
    - 后端：`src/modules/**`, `src/controller/**`, `src/service/**`
    - Sub-agent Prompt 中明确指定优先分析的文件路径

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 模块索引 | `_output/modules-index.yaml` | YAML |
| 项目源代码 | 项目目录 | 源文件 |
| 项目类型 | modules-index 中确认 | frontend / bff / backend |
| 格式模板 | `templates/01~07.yaml` | YAML |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 8 个 reference 文件 | `_reference/00-index.md` + `01~07.yaml` | Markdown + YAML |
| 进度更新 | `_output/build-reference-progress.yaml` | YAML |

### reference 文件结构（按关注点维度，8 个文件）

知识按**本质属性**分文件，不按工作流步骤分。每个文件是一个独立的知识维度，可被多个工作流步骤按需引用。

| 文件 | 维度 | 回答的问题 | 格式模板 |
|------|------|-----------|---------|
| `00-index.md` | 导航 | 知识库有什么？在哪？ | 本文件步骤 7 定义 |
| `01-entities.yaml` | 实体 | 项目里有什么东西？ | `templates/01-entities.yaml` |
| `02-architecture.yaml` | 结构 | 项目怎么组织的？ | `templates/02-architecture.yaml` |
| `03-conventions.yaml` | 规范 | 代码该怎么写？ | `templates/03-conventions.yaml` |
| `04-constraints.yaml` | 约束 | 什么必须为真？ | `templates/04-constraints.yaml` |
| `05-mapping.yaml` | 映射 | PRD 怎么对应代码？ | `templates/05-mapping.yaml` |
| `06-glossary.yaml` | 术语 | 人话 ↔ 机器话？ | `templates/06-glossary.yaml` |
| `07-business-context.yaml` | 业务 | 为什么这样做？ | `templates/07-business-context.yaml` |

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

   ## 文件过滤（严格遵守）
   只读取业务源码，跳过以下文件：
   - 排除：node_modules, dist, build, coverage, __tests__, __mocks__, mock, mocks
   - 排除：*.config.*, *.mock.*, *.test.*, *.spec.*, *.fixture.*, *.d.ts
   - 排除：.eslintrc*, .prettierrc*, tsconfig.*, jest.*, webpack.*, vite.*
   - 优先读取核心文件：{core_files_for_module}

   ## 输出格式
   严格 YAML 格式，不确定的标记 TODO：
   module: {module_name}
   files_scanned: [...]
   answers:
     - question: "..."
       answer: "..."
       verified_by: ["file.ts:45", "file.ts:67"]  # 必填：事实来源的文件:行号
       confidence: high | medium | low
   key_files: [...]
   non_obvious_patterns: [...]

   ## 规则
   1. 只写确定的内容，不确定的一律标 TODO + confidence: low
   2. 文件路径必须是实际存在的（用 Glob/Grep 验证）
   3. 不要写废话，每行都要有信息量
   4. 总长度控制在 35 行以内
   5. 只分析业务源码，不要读取配置文件、mock 文件、测试文件
   6. **每条事实必须附带 verified_by** — 指向定义该事实的源文件:行号
   7. **不要从文件名或 import 语句推断代码行为** — 必须读取函数体
   ```

   - 收集所有 Sub-agent 的返回结果

3. **确定性事实验证（Deterministic Fact Verification）** — 🔴 强制步骤，不可跳过

   在进入部落知识挖掘之前，对所有具有单一权威来源的事实进行源码级验证。这些事实的**部分正确比全错更糟糕**，因为下游代码生成完全信任它们。

   **验证协议：每个事实必须从源文件 Read 后写入，禁止推断。**

   **3-0. 枚举值完备性验证**
   - 从 Sub-agent 返回的枚举列表中，逐个定位 `definition_file`：
     1. `Grep 'enum\s+\w+<EnumName>'` 找到定义文件
     2. `Read` 该文件，提取**完整的**枚举成员列表（每个成员名 + 值）
     3. 与 Sub-agent 报告的值逐条比对
     4. **任何不匹配**：以源码为准重写，标记 `confidence: high`
     5. **任何遗漏**：补充缺失成员，标记 `confidence: high`
   - 验证完成后，枚举条目必须附带 `verified_by: ["path/to/enum-file.ts:XX"]`

   **3-0a. switch-case 分支完备性验证**
   - 对每个 `registration_mechanism` 或 `switch-case` 分发点：
     1. `Read` 包含 switch 的文件
     2. 计数所有 `case` 分支（包括 `default`）
     3. 与 Sub-agent 报告的分支数比对
     4. **任何不匹配**：以源码为准重写，标记 `confidence: high`
     5. 记录无对应处理模板的分支（如 `AISelectableOrder`、`Turbo`）
   - 验证完成后，分支计数必须附带 `verified_by: ["path/to/switch-file.ts:XX"]`

   **3-0b. 接口/类方法完备性验证**
   - 对每个核心类型（如 `InjectContext`、`ComponentModel`）：
     1. `Read` 定义文件
     2. 列出**所有**导出的方法签名（含参数和返回类型）
     3. 与 Sub-agent 报告的方法列表比对
     4. **任何遗漏或多余**：以源码为准重写
   - 验证完成后，方法列表必须附带 `verified_by: ["path/to/definition-file.ts:XX"]`

   **3-0c. 数据流路径验证**
   - 对每个 `data_flow` 描述：
     1. 从入口文件开始，`Read` 并追踪实际调用链
     2. 验证描述中的每一层（如 "Controller → Service → ComponentModel"）确实存在且调用关系正确
     3. 如果中间层不是独立层（如 ComponentModel 内嵌 Builder），修正描述
   - 验证完成后，数据流描述必须附带 `verified_by: ["entry-file.ts:XX", "next-file.ts:YY"]`

   **3-0d. 字段映射路径验证**
   - 对 `05-mapping.yaml` 中的每个 `field_mapping`：
     1. `Grep` 验证 `target_file` 路径存在
     2. `Grep` 验证 `code_field` 在目标文件中实际存在
     3. **任何不存在**：标记为 `TODO` + `confidence: low`，不要猜测替代路径
   - 验证完成后，映射条目必须附带 `verified_by: ["path/to/target-file.ts"]`

   **验证失败处理：**
   - 如果某项验证无法完成（文件不存在、无法解析）：标记 `TODO` + `confidence: low` + `needs_domain_expert: true`
   - 所有验证结果记录到 `_output/verification-log.yaml`（供 Phase 3 审计）

3. **部落知识挖掘（Tribal Knowledge Mining）**

   基于 Meta 的发现：**代码注释中的隐式知识产出最多价值**。对每个模块额外执行：

   **3a. 注释中的隐式规则挖掘**
   - Grep 搜索 `// TODO`、`// FIXME`、`// HACK`、`// NOTE`、`// XXX`、`// WARNING` 等标记
   - Grep 搜索中文注释（`// [\u4e00-\u9fff]`），这些通常是业务逻辑说明
   - 提取注释中提到的隐式约定
   - 将发现的隐式规则写入 `03-conventions.yaml` 的 `non_obvious_patterns` 部分

   **3b. Git 历史中的变更模式挖掘**
   - 执行 `git log --oneline -30 -- <module_path>` 获取最近变更
   - 执行 `git log --all --oneline --diff-filter=A -- <module_path>` 找到首次创建
   - 分析 commit message 中的业务意图
   - 记录热点文件和冷文件

   **3c. 非显而易见的模式（Non-Obvious Patterns）**
   - 搜索代码中不在 README/文档中但影响行为的隐式约定：
     - 命名约定、隐式依赖、副作用、编译时约束
   - 每个发现的模式记录：`{ pattern, detail, source: "code_comment" | "git_history" | "code_structure" }`

   **3d. 模式挖掘（Pattern Mining）— 从代码反推路由规则**

   目标：将代码中隐含的 PRD→代码映射关系显式化，为 `05-mapping.yaml` 的 `prd_routing` 和 `golden_samples` 提供数据。

   **3d-1. Switch-case / if-else 分支扫描**
   - Grep 搜索 `switch\s*\(` 和 `case\s+` 定位所有分发逻辑
   - 对每个 switch-case：记录变量名、每个 case 分支对应的处理函数/文件
   - 推导出路由规则并编码为 `prd_routing` 候选项

   **3d-2. Import 依赖链追踪**
   - Read 关键文件的 import 语句，构建 `{文件 → 依赖文件}` 映射
   - 识别"枢纽文件"（被 ≥3 个文件 import），写入 `02-architecture.yaml` 的 `import_dependency_hub`

   **3d-3. 黄金样本提取（Golden Sample Extraction）**
   - 选择 2-3 个已实现的典型实体
   - 记录"新增此实体时改了哪些文件、按什么模式改"
   - 结果写入 `05-mapping.yaml` 的 `golden_samples`

   **3d-4. 差异分析（Diff Analysis）**
   - 选择 2 对相似实体，对比代码差异
   - 推导"什么 PRD 差异导致什么代码差异"，编码为 `change_type_rules` 补充规则

   **3e. 第三轨识别（Third Rail Detection）**

   基于 Phase 0 种子 + 枢纽文件分析：

   - 读取 `_output/context-enrichment.yaml` 的 `third_rail_seeds` 和 `change_heatmap`
   - 识别被 ≥3 个文件 import 的"枢纽文件"（从 3d-2 的 import_dependency_hub 中提取）
   - 将枢纽文件 + 种子中的高风险文件合并，用 Grep/Read 源码验证后编码为 third_rails 条目
   - 每个 third_rail 包含：file, reason, impact, guidance, related_war_story（如有）
   - 执行 `git log --since='30 days ago' --format='' --name-only | sort | uniq -c | sort -rn | head -15` 补充 change_heatmap
   - 种子中 confidence: medium 的条目，经验证后升级为 high
   - 写入 `02-architecture.yaml` 的 `third_rails` 和 `change_heatmap` 节

   **3f. 踩坑历史收集（War Stories Collection）**

   基于 Phase 0 种子 + 代码注释挖掘：

   1. 读取 `_output/context-enrichment.yaml` 的 `war_story_seeds` 和 `fixup_signals`
   2. 将种子中的踩坑信号编码为 war_stories 条目，用 Grep/Read 源码验证
   3. 补充代码注释中的 HACK/FIXME/NOTE 标记（已在 3a 中挖掘的隐式规则）
   4. 每条 war_story 必须有：id, module, pitfall, symptom, prevention, source
   5. 种子中 confidence: medium 的条目，经验证后升级为 high
   6. 写入 `03-conventions.yaml` 的 `war_stories` 节

   **3g. 代码风格深潜（Code Style Deep Dive）**

   基于 Phase 0 种子 + 源码验证：

   - 读取 `_output/context-enrichment.yaml` 的 `code_style_seeds` 作为初始参考
   - **错误处理风格**：Grep `try|catch|throw|Error` 分析错误处理模式
   - **函数结构**：Read 3 个模板文件，统计模板函数长度分布
   - **注释风格**：Grep `//` 分析中英文注释比例和用途
   - **导入排序**：Read 关键文件头部 import 语句，识别排序偏好
   - 每个维度记录：pattern, example_source, anti_pattern, note
   - 写入 `03-conventions.yaml` 的 `code_style` 节

   **3h. 业务上下文提取（Business Context Extraction）**

   从 Phase 0 种子 + PRD 样本 + Git 历史中提取业务决策：

   1. 读取 `_output/context-enrichment.yaml` 的 `business_context_seeds` 和 `backend_doc_extracts`
   2. 从 Git commit message 中提取业务意图（grep feat/fix/refactor 模式）
   3. 从 `prd_diff_correlations` 中归纳业务术语和隐式规则
   4. 将业务知识编码为：domain, decision_log, implicit_business_rules, milestones
   5. 写入 `07-business-context.yaml`

4. **业务逻辑提取**

   **4a. 业务规则提取** — 读取常量/枚举/条件判断，记录业务含义
   **4b. 数据流追踪** — 追踪关键数据从入口到出口的完整路径和变换规则
   **4c. 业务术语映射** — 建立代码变量名 → 业务术语映射表，写入 `06-glossary.yaml`

5. **跨模块依赖图生成**

   分析模块间的依赖关系，写入 `02-architecture.yaml` 的 `cross_module_dependencies` 部分。

6. **按维度合并到标准文件**

   将各模块的分析结果按知识维度合并到 7 个标准文件。**写入每个文件前，先读取对应的格式模板**（`templates/01~07.yaml`），按模板结构填充实际数据。

   | 目标文件 | 从模块分析中提取的内容 | 格式模板 |
   |----------|----------------------|---------|
   | **01-entities.yaml** | 枚举定义、核心类型、数据结构、注册信息 | `templates/01-entities.yaml` |
   | **02-architecture.yaml** | 目录结构、注册机制、数据流、跨模块依赖、third_rails、change_heatmap | `templates/02-architecture.yaml` |
   | **03-conventions.yaml** | 命名规范、代码模式、反模式、non_obvious_patterns、war_stories、code_style | `templates/03-conventions.yaml` |
   | **04-constraints.yaml** | 白名单、枚举校验规则、致命错误、i18n 规则 | `templates/04-constraints.yaml` |
   | **05-mapping.yaml** | PRD 路由表、能力边界、inventory、字段映射、变更分类、golden_samples、development_playbook、structural_patterns | `templates/05-mapping.yaml` |
   | **06-glossary.yaml** | 业务术语表、同义词映射、工作量标准 | `templates/06-glossary.yaml` |
   | **07-business-context.yaml** | 业务域概览、决策记录、隐式业务规则、里程碑 | `templates/07-business-context.yaml` |
   | **00-index.md** | 导航索引 + 实体索引 | 本文件步骤 7 定义 |

7. **实体索引提取**（LLM Wiki 实体交叉引用）

   识别跨文件出现的核心域实体，生成实体索引表嵌入 `00-index.md`：

   - 识别在 ≥2 个 YAML 文件中出现的域概念
   - 不记录通用技术概念，只记录**项目特有**实体
   - 生成实体索引表：

   ```markdown
   ## 实体索引

   > 跨文件核心域实体。Agent 可按需加载对应 YAML，而非全量加载。

   | 实体 | entities | architecture | conventions | constraints | mapping | glossary |
   |------|----------|-------------|-------------|-------------|---------|----------|
   | CampaignType | enum_def | data_flow | registration | whitelist | routing, inventory | glossary |
   ```

8. **按项目类型定制**
   - **前端**：05-mapping 的 prd_routing → `target: { component }` + inventory capabilities
   - **BFF**：05-mapping 的 prd_routing → `target: { files: { create, modify_required, modify_conditional } }` + inventory
   - **后端**：05-mapping 的 prd_routing → `target: { api_endpoint, data_model }` + inventory

9. **保存文件**
   - 写入 `_reference/` 目录
   - 更新进度文件（phase_2: completed）

### 工作流步骤按需加载参考

| 工作流步骤 | 需加载的 reference 文件 |
|-----------|----------------------|
| PRD 蒸馏（路由匹配） | 05-mapping + 01-entities + 06-glossary + 07-business-context |
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

1. **8 文件齐全** — _reference/ 下有 00-index.md + 01~07.yaml
2. **YAML 合法** — 每个文件可被 YAML 解析器解析
3. **元数据完整** — 每个文件有 version/layer/project/last_verified
4. **路径有效** — 所有 target_file / key_files / definition_file 路径存在
5. **TODO 可控** — TODO 总数 < 15 个
6. **格式合规** — 每个文件结构与对应 templates/ 模板一致

## NEXT STEP

确认完成 → 进入 [step-03-quality-gate.md](./step-03-quality-gate.md)
