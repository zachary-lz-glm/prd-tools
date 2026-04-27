# step-00: 上下文富化（Phase 0）

## 设计理念

**不问人，只读物。** 项目历史中已经蕴含了项目负责人的全部隐性知识 ——

| 隐性知识 | 已有的物质载体 | 提取方式 |
|----------|---------------|---------|
| "这类需求怎么开发" | PRD + 对应 git diff | PRD ↔ diff 对照 → development_playbook |
| "踩过什么坑" | fixup/revert commit + TODO 注释 | git log 过滤 → war_stories |
| "改 A 坏 B" | 同一分支里多次修改同一文件 | diff 时序分析 → third_rails |
| "代码风格" | 已有代码本身 | Read 模板文件 → code_style |
| "业务规则" | 后端技术文档 + PRD | 文档解析 → business_context |
| "热点/稳定区" | git log --stat | 频率统计 → change_heatmap |

用户只需要**提供路径**，零问答。

## MANDATORY RULES

1. 只收集信息，不修改项目文件
2. Git 分析全自动执行，不阻塞用户
3. 用户只需提供文件路径/分支名，不要求抽象总结
4. 所有输出为 YAML 格式
5. 不猜测业务含义，只从已有素材中提取
6. 提供 2~3 个历史 PRD 即可产出高质量上下文，提供越多越准

## INPUT

| 输入 | 来源 | 格式 | 必须 |
|------|------|------|------|
| 项目 Git 历史 | 目标项目 `.git/` | Git log | 是 |
| 历史 PRD 文件 | 用户提供的文件路径 | .md / .docx / 纯文本 | 是（至少 2 个） |
| 对应 git 分支名 | 用户提供的分支名或 merge commit | string | 是（至少 2 个） |
| 后端技术文档 | 用户提供的文件路径（可选） | .md / .docx | 否 |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 上下文富化数据 | `_output/context-enrichment.yaml` | YAML |
| 进度更新 | `_output/build-reference-progress.yaml` | YAML |

## EXECUTION

### 1. 初始化

- 创建 `_output/` 目录（如不存在）
- 更新 `_output/build-reference-progress.yaml`：`phase_0: in_progress`

### 2. 收集输入（一次交互，非逐题问答）

使用 AskUserQuestion 一次收集所有素材路径：

> **请提供历史需求素材（至少 2 组，越多越准）：**
>
> **组 1:**
> - PRD 文件路径：
> - 对应的 git 分支名（或 merge commit hash）：
>
> **组 2:**
> - PRD 文件路径：
> - 对应的 git 分支名（或 merge commit hash）：
>
> **组 3（可选）:**
> - PRD 文件路径：
> - 对应的 git 分支名（或 merge commit hash）：
>
> **后端技术文档路径（可选，多个用逗号分隔）：**

用户填写完毕后，后续全部自动执行。

### 3. Git 历史深挖（全自动）

对目标项目执行以下命令，收集基础洞察。**所有命令必须排除非业务文件**（配置、mock、依赖锁、测试等）：

```bash
# 贡献者画像
git shortlog -sn --no-merges | head -10

# 热点变更模式（最近 6 个月）
git log --since='6 months ago' --format='%s' | sort | uniq -c | sort -rn | head -20

# 文件创建意图（最早的提交，只看业务源码）
git log --diff-filter=A --format='%ai %s' -- '*.ts' '*.tsx' ':!node_modules' ':!dist' ':!*.config.*' ':!*.mock.*' ':!*mock*' ':!*__test*' ':!*__mock*' | head -20

# 热点文件（最近 30 天修改最多的文件，排除非业务文件）
git log --since='30 days ago' --format='' --name-only -- '*.ts' '*.tsx' ':!node_modules' ':!dist' ':!*.config.*' ':!*.mock.*' ':!*.test.*' ':!*.spec.*' ':!*__test*' ':!*__mock*' ':!*mock*' | sort | uniq -c | sort -rn | head -15

# 最近 50 条 commit 概览
git log --oneline -50

# fixup/revert commit（踩坑信号）
git log --all --oneline --grep='fixup\|revert\|hotfix\|修复\|回滚' | head -20

# TODO/FIXME/HACK 注释统计（只看业务源码）
git grep -c 'TODO\|FIXME\|HACK\|XXX' -- '*.ts' '*.tsx' ':!node_modules' ':!dist' ':!*.config.*' ':!*.mock.*' ':!*.test.*' ':!*__test*' ':!*__mock*' | head -20
```

### 4. PRD ↔ Git Diff 对照分析（全自动，核心步骤）

对用户提供的每组 PRD + 分支，执行以下分析：

#### 4a. 提取 git diff

**所有 diff 命令必须排除非业务文件**，避免被配置/mock/测试文件的变更干扰分析：

```bash
# 排除规则（所有 diff 命令共用）
EXCLUDE="-- ':!node_modules' ':!dist' ':!build' ':!*.config.*' ':!*.mock.*' ':!*.test.*' ':!*.spec.*' ':!package*.json' ':!*.lock' ':!*__test*' ':!*__mock*' ':!*mock*' ':!*.md' ':!.eslintrc*' ':!.prettierrc*'"

# 方式 1：分支名（只看业务源码变更）
git diff main...<branch_name> -- '*.ts' '*.tsx' $EXCLUDE

# 方式 2：merge commit
git diff <merge_commit>^...<merge_commit> -- '*.ts' '*.tsx' $EXCLUDE

# 统计变更文件（排除非业务文件）
git diff --stat main...<branch_name> -- '*.ts' '*.tsx' $EXCLUDE

# 变更文件列表（排除非业务文件）
git diff --name-only --diff-filter=M main...<branch_name> -- '*.ts' '*.tsx' $EXCLUDE   # 修改的业务文件
git diff --name-only --diff-filter=A main...<branch_name> -- '*.ts' '*.tsx' $EXCLUDE   # 新增的业务文件
```

#### 4b. 读取 PRD 内容

- `.md` 文件 → 直接 Read
- `.docx` 文件 → 分级回退转换（pandoc → mammoth → textutil → 提示用户）
- 纯文本 → 直接使用

#### 4c. PRD ↔ Diff 对照推理

对每组数据，AI 自动推理以下维度：

**development_playbook 种子：**

```
PRD 说了什么 → 实际改了哪些文件 → 按什么顺序改 → 用了什么模式
```

具体步骤：
1. 从 PRD 提取需求意图（新增活动类型？新增字段？修改逻辑？）
2. 从 diff 统计提取变更文件列表和顺序（按首次出现排序）
3. 从 diff 内容提取变更模式（在枚举对象中添加 key:value？复制模板文件？switch-case 添加分支？）
4. 将 PRD 意图 + 变更文件 + 变更模式组装为 playbook scenario 候选项
5. 多组 PRD 交叉对比：如果 2+ 组 PRD 触发了相同模式的文件变更 → 归纳为通用 scenario

**war_stories 种子：**

从 diff 中识别踩坑信号：
- fixup commit（`git log --oneline <branch> | grep -i fixup`）→ 说明第一次改错了
- 同一文件在分支内被修改 3+ 次 → 说明该文件容易出错
- diff 中删除了代码又添加了类似代码 → 说明试错了
- PRD 描述与实际 diff 不匹配 → 说明有隐式约束

将这些信号编码为 war_stories 候选项，格式：
```yaml
- id: "WS-???"
  module: "<从 diff 文件路径推断>"
  title: "<从现象总结>"
  pitfall: "<坑是什么>"
  symptom: "<从 fixup/revert 的 diff 内容提取>"
  source: "git_diff_analysis"
  confidence: medium  # 自动提取的，需要 Phase 2 验证
```

**third_rails 种子：**

从 diff 中识别高风险文件：
- 被多组 PRD 的 diff 同时涉及的文件 → 高影响枢纽
- diff 中包含 switch-case / if-else 分发逻辑的修改 → 注册入口
- import 被其他文件广泛引用的文件（结合 3 的 git grep 分析）

将这些编码为 third_rails 候选项，格式：
```yaml
- file: "<路径>"
  reason: "<从 diff 上下文推断>"
  impact: "<影响范围>"
  confidence: medium
```

**change_heatmap 种子：**

```bash
# 所有样本分支的文件变更频率汇总
git log --since='6 months ago' --format='' --name-only | sort | uniq -c | sort -rn | head -30
```

分类：hot（>10次/6月）, warm（3-10次）, cold（稳定）

### 5. 后端技术文档解析（可选，全自动）

如果用户提供了后端技术文档路径：

1. Read 文档内容
2. 提取以下信息：
   - API 接口变更说明 → 映射到 BFF 层的对应关系
   - 业务规则描述 → implicit_business_rules 候选项
   - 数据模型变更 → 字段映射补充
   - 约束条件 → constraints 补充
3. 将提取结果结构化为 business_context 候选项

### 6. 综合推理（全自动）

基于上述所有素材，AI 综合推理以下维度：

**6a. 业务域概览**

从 PRD 样本 + commit message 中归纳：
- 核心用户角色（从 PRD 中的功能描述推断）
- 核心价值（从 PRD 标题和背景推断）
- 关键业务流（从 commit message 中的 feat/fix 模式推断）

**6b. 术语映射**

从 PRD ↔ 代码 diff 中提取术语映射：
- PRD 中的中文描述 → diff 中对应的英文变量名
- 多个 PRD 中同一概念的不同表述 → 同义词列表

**6c. 代码风格**

从 diff 中的代码片段提取风格特征：
- 错误处理模式
- 函数签名风格
- 注释语言偏好
- import 排序习惯

### 7. 生成输出

将所有分析结果写入 `_output/context-enrichment.yaml`：

```yaml
version: "2.0"
collected_at: "<时间戳>"
project_path: "<项目路径>"
source_summary:
  prd_count: N
  branch_count: N
  has_backend_docs: true/false

# --- Git 基础洞察（从 step 3）---
git_insights:
  contributors:
    - name: "<贡献者>"
      commits: N
  hot_change_patterns:
    - pattern: "<变更模式>"
      frequency: N
  hot_files:
    - file: "<路径>"
      commits_30d: N
  file_creation_intents:
    - date: "<日期>"
      message: "<commit message>"
  fixup_signals:
    - commit: "<hash>"
      message: "<message>"
      file: "<涉及文件>"

# --- PRD ↔ Diff 对照结果（从 step 4）---
prd_diff_correlations:
  - prd_file: "<路径>"
    branch: "<分支名>"
    prd_intent: "<AI 推断的需求意图>"
    files_changed:
      create: ["<新增文件列表>"]
      modify: ["<修改文件列表>"]
    change_order: ["<按首次出现排序的文件列表>"]
    change_patterns:
      - file: "<路径>"
        pattern: "<变更模式描述>"
        code_snippet: "<关键变更片段（3-5行）>"

# --- 开发指南种子（从 step 4c 归纳）---
playbook_seeds:
  - scenario: "<归纳出的场景名>"
    evidence:
      - prd_file: "<PRD 路径>"
        branch: "<分支名>"
        intent: "<该 PRD 的意图>"
    files_involved: ["<涉及文件列表>"]
    change_order: ["<归纳的变更顺序>"]
    patterns_observed: ["<观察到的变更模式>"]
    estimated_files: "<N-M>"
    confidence: medium  # 需要 Phase 2 验证

# --- 踩坑历史种子（从 step 4c 提取）---
war_story_seeds:
  - id: "WS-???"
    module: "<模块>"
    title: "<标题>"
    pitfall: "<坑>"
    symptom: "<表现>"
    evidence:
      commit: "<fixup/revert commit hash>"
      file: "<文件>"
    source: "git_diff_analysis"
    confidence: medium

# --- 第三轨种子（从 step 4c 提取）---
third_rail_seeds:
  - file: "<路径>"
    reason: "<为什么危险>"
    impact: "<影响范围>"
    hit_count: N  # 在多少组 PRD diff 中出现
    confidence: medium

# --- 变更热力图（从 step 4c + step 3）---
change_heatmap:
  hot:   # 6 个月内 > 10 次提交
    - file: "<路径>"
      commits_6m: N
      note: "<说明>"
  warm:  # 6 个月内 3-10 次提交
    - file: "<路径>"
      commits_6m: N
      note: "<说明>"
  cold:  # 90 天内未修改
    - file: "<路径>"
      note: "<说明>"

# --- 业务上下文种子（从 step 5 + 6a）---
business_context_seeds:
  domain_summary: "<从 PRD + commit 归纳>"
  core_users: ["<从 PRD 功能描述推断>"]
  key_flows: ["<从 commit feat 模式推断>"]
  implicit_rules:
    - rule: "<从后端文档或 PRD 约束提取>"
      source: "<来源文件>"
  terminology:
    - prd_term: "<中文>"
      code_term: "<英文>"
      synonyms: ["<同义词列表>"]
      source_prd: "<来源 PRD>"

# --- 代码风格种子（从 step 6c）---
code_style_seeds:
  error_handling: "<从 diff 中观察到的错误处理模式>"
  function_signature: "<从 diff 中观察到的函数签名风格>"
  comment_language: "<从 diff 中观察到的注释语言>"
  import_style: "<从 diff 中观察到的 import 排序>"

# --- 后端文档提取（可选，从 step 5）---
backend_doc_extracts:
  - source: "<文档路径>"
    api_changes: ["<API 变更描述>"]
    business_rules: ["<业务规则>"]
    field_mappings: ["<字段映射>"]

todos: []  # 无法自动推断的项，标 TODO 等 Phase 2 补充
```

更新进度文件：`phase_0: completed`

### 8. 展示摘要

输出完成后展示摘要（非交互，仅展示）：

```
上下文富化完成！
- 素材：N 个 PRD + N 个分支 + N 个后端文档
- Git 洞察：N 个贡献者，M 个热点模式，K 个热点文件
- PRD ↔ Diff 对照：归纳出 N 个开发场景，M 个踩坑信号，K 个高风险文件
- 变更热力图：hot N / warm M / cold K
- 置信度：所有种子均为 medium（需 Phase 2 代码验证后升级为 high）

输出：_output/context-enrichment.yaml

下一步：运行 /build-reference → Option A（全量构建），Phase 2 会自动引用此文件
```

## Phase 2 消费指南

`step-02-deep-analysis.md` 中以下步骤读取本文件：

| step-02 步骤 | 读取的字段 | 用途 |
|-------------|-----------|------|
| 3e 第三轨识别 | `third_rail_seeds` + `change_heatmap` | 从种子 + 枢纽文件分析 → 写入 02-architecture.yaml |
| 3f 踩坑历史 | `war_story_seeds` + `fixup_signals` | 从种子 + 代码注释验证 → 写入 03-conventions.yaml |
| 3h 业务上下文 | `business_context_seeds` + `backend_doc_extracts` | 从种子 + Git 历史验证 → 写入 07-business-context.yaml |
| 3d 黄金样本 | `prd_diff_correlations` | PRD ↔ diff 对照结果直接作为 golden_sample 数据源 |
| 3d 模式挖掘 | `playbook_seeds` | 归纳的场景 → 验证后写入 05-mapping.yaml 的 development_playbook |
| 3g 代码风格 | `code_style_seeds` | 从种子 + 模板文件验证 → 写入 03-conventions.yaml |

关键改动：**Phase 2 不再依赖 `interview` 字段**，改为消费 `*_seeds` 字段。所有种子 confidence 为 medium，Phase 2 通过 Grep/Read 源码验证后升级为 high。

## VALIDATION

1. **YAML 合法** — context-enrichment.yaml 可被解析
2. **Git 数据非空** — 至少有 contributors 和 hot_change_patterns
3. **PRD 对照有效** — 至少有 2 组 prd_diff_correlations
4. **种子非空** — 至少有 1 个 playbook_seed 或 1 个 war_story_seed
5. **文件路径真实** — prd_file、branch 对应的文件/分支必须可访问

## 向后兼容

如果 `_output/context-enrichment.yaml` 已存在且包含旧版 `interview` 字段：
- 保留 `interview` 数据，不删除
- 新版 `*_seeds` 字段与旧版 `interview` 字段共存
- Phase 2 优先使用 `*_seeds`，`interview` 作为补充数据源

## NEXT STEP

Phase 0 完成 → 返回 SKILL.md 的模式选择菜单。

如果是全量构建流程中触发（Option A 检测到无 context-enrichment），则提示用户提供素材路径后自动执行 Phase 0，再继续进入 Phase 1。
