# build-reference Workflow

## 概述

4 阶段工作流，用于从项目源代码中提取领域知识，按关注点维度生成标准化的 8 个 reference 文件（7 YAML + 1 MD）。

```
项目负责人知识(Phase 0) → Phase 1(结构扫描) → Phase 2(深度分析) → Phase 3(质量门控) → _reference/
```

## 4 阶段定义

| 阶段 | 名称 | 输入 | 输出 | 人工确认 | 必要性 |
|------|------|------|------|---------|--------|
| 0 | 上下文富化 | 项目 Git 历史 + 历史 PRD + git 分支 diff | `context-enrichment.yaml` | **是** — 提供素材路径（一次交互） | 可选但强烈推荐 |
| 1 | 结构扫描 | 项目目录 + Git 历史 | `modules-index.yaml` | **是** — 确认模块划分 | 必须 |
| 2 | 深度分析 | `modules-index.yaml` + 源代码 + `context-enrichment.yaml` | 8 个 reference 文件 | **是** — 逐模块确认 | 必须 |
| 3 | 质量门控 | 生成的 reference 文件 | 质量报告 + 最终 reference | **是** — 校准 TODO 项 | 必须 |

## 进度追踪

进度存储在 `_output/build-reference-progress.yaml` 中。

### progress.yaml 格式

```yaml
session_id: "br-{timestamp}"
created_at: "2026-04-24T10:00:00Z"
current_phase: 0
project_type: "frontend"       # frontend / bff / backend
project_path: "."
phases:
  phase_0:
    status: not_started         # not_started | in_progress | completed | skipped | failed
    started_at: null
    completed_at: null
    prd_samples_collected: false
  phase_1:
    status: not_started
    started_at: null
    completed_at: null
    modules_found: 0
  phase_2:
    status: not_started
    started_at: null
    completed_at: null
    files_generated: 0
  phase_3:
    status: not_started
    started_at: null
    completed_at: null
    quality_score: null
last_updated: "2026-04-24T10:00:00Z"
```

### 断点续传逻辑

1. 读取 `_output/build-reference-progress.yaml`
2. 找到 `current_phase` 值
3. 从该阶段的 `status` 判断恢复点：
   - `completed` → 从下一阶段开始
   - `in_progress` / `failed` → 重新执行当前阶段（阶段设计为幂等）
   - `not_started` → 从该阶段开始
4. 所有阶段完成 → 清除进度

## 阶段间数据传递

| 阶段 | 写入文件 | 读取文件 |
|------|---------|---------|
| Phase 0 | `_output/context-enrichment.yaml` | 项目 Git 历史 + 历史 PRD + git 分支 diff |
| Phase 1 | `_output/modules-index.yaml` | 项目目录（Glob/Grep） |
| Phase 2 | `_reference/00-index.md` + `01~07.yaml` | `_output/modules-index.yaml` + 源代码 + `_output/context-enrichment.yaml` |
| Phase 3 | `_output/quality-report.yaml` | `_reference/` 全部文件 + 源代码 |

## 确认流程

每个阶段完成后进入人工确认：

- **Phase 1** → 展示模块划分结果，用户可合并/拆分/重命名模块
- **Phase 2** → 逐模块展示提取的知识，用户确认或修改
- **Phase 3** → 展示质量报告 + TODO 清单，用户逐项校准

## 错误处理

### 可恢复错误

- 模块识别不完整 → 补充扫描 + 人工确认
- 文件路径不存在 → 标记 TODO，Phase 3 校准
- Token 超限 → 拆分为更小的扫描单元

### 不可恢复错误

- 项目目录为空或无法访问 → 立即暂停 + 明确错误信息
- `_reference/` 权限不足 → 提示修复权限

## 执行准则

Agent 执行工作流时必须遵守：

1. **只写确定的内容** — 不确定的一律标 TODO + confidence: low
2. **文件路径必须实际存在** — 用 Glob/Grep 验证，不猜测
3. **遵循 YAML 规范** — `00-index.md` 中定义的格式标准
4. **每文件 ≤ 300 行** — 05-mapping.yaml 例外（含核心路由表）
5. **阶段间只通过文件通信** — 确保断点续传可行
6. **Sub-agent 返回摘要** — 每个子任务 ≤ 1000 tokens
7. **文件过滤** — 以下文件/目录不参与知识提取（所有阶段、所有步骤通用）：
   - **排除目录**：`node_modules`, `dist`, `build`, `.git`, `.husky`, `.vscode`, `.idea`, `coverage`, `__tests__`, `__mocks__`, `mock`, `mocks`, `.claude`, `_output`, `_reference`, `.next`, `.nuxt`
   - **排除文件**：`.` 开头的配置文件（`.eslintrc*`, `.prettierrc*`, `.babelrc*`, `.env*`, `.npmrc`, `.editorconfig`）
   - **排除模式**：`*.config.ts`, `*.config.js`, `webpack.*`, `vite.*`, `rollup.*`, `jest.setup.*`, `tsconfig.*`, `jest.config.*`, `babel.config.*`, `postcss.config.*`, `tailwind.config.*`
   - **排除依赖锁**：`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`
   - **排除 mock**：`**/mock/**`, `**/mocks/**`, `**/__mocks__/**`, `**/fixtures/**`, `**/stubs/**`, `*.mock.ts`, `*.mock.js`, `*.fixture.*`
   - **唯一例外**：仅在 Phase 1 "检测项目类型"阶段读取 `package.json` 的 `dependencies`/`scripts` 字段
8. **核心文件优先** — 分析模块时，优先读取业务源码文件，配置文件不参与知识提取：
   - **BFF 优先**：`config/template/**`, `config/constant/**`, `handler/**`, `service/**`
   - **前端优先**：`src/components/**`, `src/pages/**`, `src/store/**`, `src/hooks/**`
   - **后端优先**：`src/modules/**`, `src/controller/**`, `src/service/**`, `src/model/**`

## 步骤文件执行

执行具体阶段时，读取 `steps/step-XX-*.md` 文件并按其中的指令执行。每个步骤文件包含完整的执行逻辑，可独立运行。

步骤编号对应关系：
- `steps/step-01-structure-scan.md` → Phase 1
- `steps/step-02-deep-analysis.md` → Phase 2
- `steps/step-03-quality-gate.md` → Phase 3

## 知识维度说明

8 个文件按**关注点维度**组织，不按工作流步骤。每个维度是独立的知识层，可被多个工作流步骤按需引用。

| 文件 | 维度 | 核心问题 |
|------|------|---------|
| 01-entities | 实体 | 项目里有什么东西？ |
| 02-architecture | 结构 | 项目怎么组织的？ |
| 03-conventions | 规范 | 代码该怎么写？踩过什么坑？ |
| 04-constraints | 约束 | 什么必须为真？ |
| 05-mapping | 映射 | PRD 怎么对应代码？新需求该怎么动手？ |
| 06-glossary | 术语 | 人话 ↔ 机器话？ |
| 07-business-context | 业务 | 为什么这样做？业务决策和历史？ |

**工作流步骤按需加载参考：**

| 工作流步骤 | 需加载的文件 |
|-----------|------------|
| PRD 蒸馏（路由匹配） | 05-mapping（含 development_playbook）+ 01-entities + 06-glossary + 07-business-context |
| 项目分析（结构扫描） | 02-architecture（含 third_rails + change_heatmap）+ 01-entities |
| 变更计划（分类规划） | 03-conventions（含 war_stories）+ 04-constraints + 05-mapping（含 development_playbook）|
| 代码生成 | 03-conventions（含 code_style + war_stories）+ 02-architecture + 01-entities |
| 代码验证 | 04-constraints + 03-conventions（含 war_stories）|
| 输出报告 | 06-glossary + 07-business-context |

## 知识维护策略（基于 Meta + Anthropic）

### 自维护机制

Reference 知识会随代码演进而过期。遵循 Meta 的 "Context that decays is worse than no context at all" 原则：

**定期验证（14 天周期）：**
- 验证所有文件路径仍然存在（Glob 检查）
- 检测新增/删除的文件
- 比对 git diff 是否引入新的模式
- 重新运行 Phase 3 Round 1 自动验证

**变更触发更新：**
- 新增活动类型时 → 增量更新 01-entities 的枚举和 05-mapping 的路由表
- package.json 依赖变更时 → 全量更新 02-architecture
- 目录结构变更时 → 重新执行 Phase 1 结构扫描
- reference 中 `code_contradicts_reference` 被报告 → 标记该条目需重新验证

**质量衰减监控：**
- 每次 `/prd-distill` 使用时记录 `code_contradicts_reference` 的数量
- 如果同一模块累计 3 次被报告矛盾 → 自动标记该模块 reference 需重建
- 在 `_output/reference-health.yaml` 中追踪健康状态

### Compass 原则（Meta）

每个 reference 文件遵循 "指南针而非百科全书" 原则：
- 每个文件 ≤ 300 行（05-mapping.yaml 例外，核心路由表）
- 每行都必须有信息量，不写废话
- 只记录项目特有的知识（模型已知的通用知识不写）
- 格式：`Quick Commands` + `Key Files` + `Non-Obvious` + `See Also`

### Sub-agent 隔离原则（Anthropic）

深度分析时遵循 Anthropic 的 Sub-agent 模式：
- 每个模块用独立 Sub-agent 分析，返回 ≤ 1000 tokens 摘要
- 详细搜索上下文隔离在 Sub-agent 内，主 Agent 只做综合分析
- 通过文件系统传递知识（Sub-agent 写临时文件 → 主 Agent 读取合并）

### 反馈回流（LLM Wiki 知识复利机制）

基于 Karpathy LLM Wiki 的"知识复利增长"思想，建立从使用经验回流到 reference 的闭环。

**触发方式：**
1. **自动提示（prd-distill 侧）**：`/prd-distill` 完成时如检测到 `code_contradicts_reference`，自动提示用户运行 `/build-reference → 反馈回流`
2. **手动触发（build-reference 侧）**：用户运行 `/build-reference` 选择 **选项 E: 反馈回流**

**回流流程（详见 `steps/step-04-feedback-ingest.md`）：**
1. 扫描 `_output/distilled-*.md`，提取 `verification_source: code_contradicts_reference` 条目
2. 提取矛盾详情（reference 说了什么 vs 源代码实际状态）
3. 定位 reference 中受影响的 YAML 文件和具体条目
4. Grep 当前源码验证实际状态
5. 生成更新建议列表，人工逐条确认
6. 更新 reference 文件 + last_verified
7. 输出 `_output/feedback-ingest-report.yaml`

**回流后效：**
- reference 越用越准，矛盾的映射关系在下次蒸馏时不再出现
- `_output/reference-health.yaml` 中 contradiction 次数下降
- 实体索引随 reference 更新自动刷新

### 深度 Lint（LLM Wiki Lint 增强）

在传统路径有效性验证基础上，增加内容一致性检查（Option B2 健康检查 + Phase 3 质量门控）：

1. **代码模式匹配**：Grep reference 中描述的代码模式到源码，验证 ≥90% 匹配
2. **跨文件枚举一致性**：01-entities 的枚举值 vs 04-constraints 的枚举校验规则，确认完全一致
3. **孤立条目检测**：05-mapping 的 inventory 中 `implemented: true` 但无 prd_routing 引用的条目
4. **实体索引有效性**：00-index.md 实体索引中指向的文件和章节存在
