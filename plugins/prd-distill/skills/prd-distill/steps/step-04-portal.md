# 步骤 4：Portal HTML 生成

## 目标

生成 `_prd-tools/distill/<slug>/portal.html`：一个完全自包含的 HTML 可视化页面，让用户在浏览器中一站式浏览蒸馏产出的报告、计划、影响分析和契约状态，无需逐个打开 Markdown 和 YAML 文件。

## 何时生成

- 步骤 3（计划、报告与反馈）完成后，作为蒸馏流程的最后一步。
- 在 readiness-report.yaml 生成之后、向用户输出完成摘要之前。

## 输入

读取 `_prd-tools/distill/<slug>/` 下的全部产出文件：

| 文件 | 用途 |
|------|------|
| `report.md` | 渐进式披露报告：解析 Markdown 章节（需求摘要、影响范围、代码命中、变更明细、字段清单、校验规则、Checklist、契约风险、阻塞问题等） |
| `plan.md` | 技术方案：解析 Phase/Step 结构和 `- [ ]` checklist 项，提取文件路径和行号 |
| `context/requirement-ir.yaml` | 结构化需求：REQ-ID、变更类型、目标层、置信度 |
| `context/evidence.yaml` | 证据台账：证据类型、来源、置信度统计 |
| `context/readiness-report.yaml` | 就绪度评分：status、score、decision、各维度分数、风险列表 |
| `context/graph-context.md` | 源码扫描上下文：解析 GCTX 条目、符号、file:line、角色 |
| `context/layer-impact.yaml` | 分层影响：各层 IMP-* 项、surface、target、变更类型 |
| `context/contract-delta.yaml` | 契约差异：alignment_status、producer/consumer、字段变更 |
| `context/reference-update-suggestions.yaml` | 回流建议：类型、优先级、置信度 |

## 输出

`_prd-tools/distill/<slug>/portal.html` — 单文件，零外部依赖。

## 生成规则

### 1. 数据内联

Claude 逐个 Read 上述文件，将内容解析为 JavaScript 对象，内联到 `<script>` 标签中：

```html
<script>
const DATA = {
  readiness: { /* readiness-report.yaml 的 JSON */ },
  requirementIR: { /* requirement-ir.yaml 的 JSON */ },
  evidence: { /* evidence.yaml 的 JSON */ },
  layerImpact: { /* layer-impact.yaml 的 JSON */ },
  contractDelta: { /* contract-delta.yaml 的 JSON */ },
  referenceSuggestions: { /* reference-update-suggestions.yaml 的 JSON */ },
  reportSections: { /* 从 report.md 解析的结构化章节 */ },
  planPhases: [ /* 从 plan.md 解析的 Phase/checklist 结构 */ ],
  graphContext: { /* 从 graph-context.md 解析的 GCTX 条目 */ }
};
</script>
```

YAML 内容转为 JSON 后嵌入。Markdown 内容解析为结构化数据（章节标题、表格、checklist 项）。如果某个文件不存在，对应 key 的值为 `null`。

### 2. 设计系统

所有 CSS 写在 `<style>` 标签中。不引用任何 CDN、外部字体、外部 CSS/JS 文件。

#### 设计理念

参考 Linear / Vercel Dashboard / Notion 风格：克制的装饰、大量留白、清晰的信息层级、微妙的动效。

#### 配色方案（CSS 变量）

```css
:root {
  /* Surface */
  --bg-page: #f5f5f7;
  --bg-card: #ffffff;
  --bg-sidebar: #0f0f11;
  --bg-sidebar-hover: rgba(255,255,255,0.06);
  --bg-sidebar-active: rgba(255,255,255,0.1);
  --bg-header: #0f0f11;
  --bg-inset: #f0f0f2;
  --bg-code: #1e1e20;

  /* Text */
  --text-primary: #1d1d1f;
  --text-secondary: #6e6e73;
  --text-tertiary: #aeaeb2;
  --text-inverse: #f5f5f7;
  --text-sidebar: rgba(255,255,255,0.7);
  --text-sidebar-active: #ffffff;

  /* Accent */
  --accent: #6C5CE7;
  --accent-hover: #5A4BD1;
  --accent-subtle: rgba(108,92,231,0.08);
  --accent-glow: rgba(108,92,231,0.25);

  /* Status */
  --success: #34C759;
  --success-bg: rgba(52,199,89,0.1);
  --warning: #FF9F0A;
  --warning-bg: rgba(255,159,10,0.1);
  --danger: #FF3B30;
  --danger-bg: rgba(255,59,48,0.1);
  --info: #5AC8FA;
  --info-bg: rgba(90,200,250,0.1);

  /* Border & Shadow */
  --border: rgba(0,0,0,0.06);
  --border-strong: rgba(0,0,0,0.12);
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 8px 30px rgba(0,0,0,0.08);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03);

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  /* Transition */
  --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
```

#### Typography

```css
/* 标题层级 */
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-primary); }
h2 { font-size: 20px; font-weight: 650; letter-spacing: -0.01em; color: var(--text-primary); }
h3 { font-size: 15px; font-weight: 600; color: var(--text-primary); }
h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }

/* 正文 */
body { font-size: 14px; line-height: 1.6; color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-tertiary { color: var(--text-tertiary); font-size: 12px; }
code { font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', Consolas, monospace; font-size: 0.9em; }
```

#### 组件样式

**卡片 (Card)**:
```css
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
  border: none;
  transition: box-shadow var(--transition-fast);
}
.card:hover { box-shadow: var(--shadow-md); }
```

**徽章 (Badge)**:
```css
/* 状态徽章 - 圆角药丸形 */
.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 100px;
  font-size: 12px; font-weight: 600; letter-spacing: 0.01em;
}
.badge-success { background: var(--success-bg); color: #248A3D; }
.badge-warning { background: var(--warning-bg); color: #C27500; }
.badge-danger  { background: var(--danger-bg);  color: #D70015; }
.badge-info    { background: var(--info-bg);    color: #0077C7; }
.badge-neutral { background: var(--bg-inset);   color: var(--text-secondary); }

/* 变更类型标签 */
.badge-add     { background: rgba(52,199,89,0.12); color: #248A3D; }
.badge-modify  { background: rgba(108,92,231,0.12); color: var(--accent); }
.badge-delete  { background: rgba(255,59,48,0.12);  color: #D70015; }
.badge-nochange{ background: var(--bg-inset);        color: var(--text-tertiary); }

/* 置信度标签 */
.confidence-high   { background: var(--success-bg); color: #248A3D; }
.confidence-medium { background: var(--warning-bg); color: #C27500; }
.confidence-low    { background: var(--danger-bg);  color: #D70015; }
```

**表格 (Table)**:
```css
table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  font-size: 13px;
}
th {
  padding: 10px 14px; text-align: left;
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-strong);
  background: transparent; position: static; /* 不需要 sticky */
}
td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--accent-subtle); }
/* 文件路径列 */
td code.path {
  background: var(--bg-inset); padding: 2px 8px;
  border-radius: var(--radius-sm); font-size: 12px;
}
```

**进度条 (Progress)**:
```css
.progress-bar {
  height: 6px; background: var(--bg-inset);
  border-radius: 100px; overflow: hidden;
}
.progress-fill {
  height: 100%; border-radius: 100px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
```

**搜索框**:
```css
.search-box {
  width: 100%; padding: 10px 14px 10px 36px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  font-size: 14px; background: var(--bg-card);
  transition: all var(--transition-fast);
  outline: none;
}
.search-box:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}
```

**代码块**:
```css
pre {
  background: var(--bg-code); color: #e0e0e2;
  padding: 16px 20px; border-radius: var(--radius-md);
  font-size: 13px; line-height: 1.6;
  overflow-x: auto; margin: 8px 0;
}
```

### 3. 页面结构

```
+---------------------------------------------------------------+
| Header: 渐变背景 / 评分环形图 / PRD 标题 / 项目 / 时间        |
+----------+----------------------------------------------------+
| Sidebar  |  Content Area (max-width: 1000px, centered)        |
| (窄，    |                                                    |
|  图标+   |  卡片式内容，大量留白                               |
|  文字)   |                                                    |
|          |                                                    |
| ○ 总览   |                                                    |
| ○ 源码   |                                                    |
| ○ 影响   |                                                    |
| ○ 契约   |                                                    |
| ○ 计划   |                                                    |
| ○ QA     |                                                    |
| ○ 阻塞   |                                                    |
| ○ 回流   |                                                    |
+----------+----------------------------------------------------+
```

#### Header

Header 使用深色渐变背景，包含：
- **评分环形图**：SVG 圆环动画显示 readiness score，颜色根据状态变化（pass=绿 85-100，warning=黄 60-84，fail=红 0-59）。环内显示大号分数数字。
- **标题区**：PRD 标题（18px, 700 weight）、项目名 + decision 标签 + 生成时间（13px, secondary color）
- **评分维度条**：水平排列 5 个小指标卡（prd_ingestion / evidence_coverage / code_search / contract_alignment / task_executability），每个显示标签 + 分数 + 迷你进度条

```html
<header id="app-header">
  <div class="header-score-ring">
    <svg><!-- 圆环进度 --></svg>
    <span class="score-number">72</span>
  </div>
  <div class="header-info">
    <h1>PRD 标题</h1>
    <div class="header-meta">
      <span class="badge badge-warning">warning</span>
      <span class="text-tertiary">项目名 · 2026-05-08</span>
    </div>
  </div>
  <div class="header-dimensions">
    <!-- 5 个维度迷你卡片 -->
  </div>
</header>
```

#### Sidebar

- 深色背景 (#0f0f11)，宽度 200px
- 每个 nav item 带图标（用 Unicode emoji 或 SVG 内联）+ 文字
- 选中项：左侧 2px 紫色竖条 + 半透明背景 + 白色文字
- 悬停：微妙背景变化，平滑过渡
- 移动端：折叠为汉堡菜单

#### Content Area

- 最大宽度 1000px，居中显示
- `padding: 32px 40px`
- section 切换使用 `opacity` + `transform` 过渡，不是瞬间显示/隐藏

### 4. 各 Section 设计要求

#### Section 1：Dashboard（总览）

**Executive Summary 卡片**：
- 大号数字统计行：变更总数 / ADD 数 / MODIFY 数 / DELETE 数，每个数字下方有灰色小标签
- 数字用 `font-size: 32px; font-weight: 700; letter-spacing: -0.02em`，ADD 绿色、MODIFY 紫色、DELETE 红色

**Top Conclusions**：
- 带编号的结论列表，每条前面有紫色圆点
- 每条结论带关联 REQ-ID 标签（小号 badge）

**关键风险摘要**：
- 用 `border-left: 3px solid var(--warning)` 的警告卡片
- 风险条目带 priority 徽章

**证据分布**：
- 小型横向柱状图或 badge 列表显示各类型证据数量

#### Section 2：源码命中

- 搜索框在顶部，带放大镜 Unicode 字符
- 表格行带圆角，行间有微妙分隔
- `role_in_flow` 用不同颜色的小标签展示
- 未命中条目用淡灰背景区分
- 按钮式过滤器：全部 / entrypoint / validator / transformer / persistence / external_call

#### Section 3：影响分析（Layer Impact）

- 按层分组，每层一个白色卡片
- 卡片顶部：层名（大号）+ 变更数量 badge + 展开/折叠按钮
- 卡片内容：
  - 受影响能力面用 tag 列表展示
  - 每个 IMP-* 项用紧凑行展示：target（代码样式）→ planned_delta（简述）→ confidence badge
- 无影响的层显示带对勾的 "该层无影响" 绿色提示

#### Section 4：契约差异（Contract Delta）

- alignment_status 概况卡片：4 个数字（aligned / needs_confirmation / blocked / not_applicable），各带颜色
- 契约表格：
  - alignment 用彩色药丸 badge
  - 点击行展开详情面板（平滑高度过渡），显示 request_fields / response_fields 的字段列表
  - 展开时行背景微变

#### Section 5：开发计划（Plan Overview）

- Phase 用大号标题 + 依赖描述分隔
- 每个 Phase 内的 Step 用卡片包裹
- Checklist 项：
  - 自定义复选框（圆角方形，勾选动画）
  - 任务描述 + 文件路径（monospace 灰底）+ 行号
  - 关联标签（REQ-001 / IMP-003 / CONTRACT-001）用小 badge
  - 验证命令用 code block 展示
- **交互式 checklist**：点击勾选，状态存 localStorage（key = `prd-distill-checklist-{slug}`）
- Phase 完成进度：Phase 标题旁显示 `3/7` 和迷你进度条

#### Section 6：QA 矩阵

- 表格：场景 | 关键检查点 | 关联 REQ | 优先级
- 优先级用 badge：P0=红色、P1=橙色、P2=蓝色
- 过滤按钮组

#### Section 7：阻塞问题

- 如有阻塞问题：
  - §11.1 阻塞问题用红色左边框卡片，每个问题含 6 要素
  - §11.2 低置信度假设用黄色左边框卡片
  - §11.3 Owner 确认项按角色分组，用蓝色左边框
- 如无阻塞问题：绿色大号对勾图标 + "当前无阻塞问题" 文字

#### Section 8：回流建议

- 卡片列表，每张卡片：
  - 顶部：ID + 类型 badge + 优先级 badge（右上角）
  - 中部：summary 文字
  - 底部：target_file（代码样式）+ 置信度 badge

### 5. 动效要求

```css
/* Section 切换 */
section { opacity: 0; transform: translateY(8px); transition: opacity 0.2s, transform 0.2s; display: none; }
section.active { display: block; opacity: 1; transform: translateY(0); }

/* 卡片悬停 */
.card { transition: box-shadow var(--transition-fast), transform var(--transition-fast); }
.card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }

/* 进度条动画 */
.progress-fill { animation: fillIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
@keyframes fillIn { from { width: 0; } }

/* 评分环形图动画 */
.score-ring-progress { animation: ringIn 1s cubic-bezier(0.4, 0, 0.2, 1) forwards; stroke-dashoffset: [target]; }
```

### 6. 交互要求

- Sidebar 导航：点击切换右侧内容区，当前选中项高亮（左侧竖条 + 背景色变化）。
- 移动端：sidebar 折叠为汉堡菜单。
- 可折叠区域：自定义 toggle + CSS max-height 过渡（不用 details/summary，视觉不够灵活）。
- 搜索/过滤：源码命中表和 QA 矩阵支持实时搜索，输入框带放大镜图标。
- 契约行展开：点击行展开字段详情，平滑高度过渡。
- Checklist 持久化：plan 的 checklist 勾选状态保存到 `localStorage`，key 为 `prd-distill-checklist-{slug}`。
- 无需任何 JavaScript 框架，纯原生 JS。

### 7. 模板结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PRD Distill: {title}</title>
  <style>
    /* 全部 CSS 内联 — 使用上面的设计系统变量和组件样式 */
    /* 重置 → 变量 → 布局 → Header → Sidebar → Content → 组件 → 动效 → 响应式 */
  </style>
</head>
<body>
  <header id="app-header">
    <!-- 评分环形图 + 标题 + 维度指标 -->
  </header>
  <div id="app-layout">
    <nav id="sidebar">
      <!-- 图标 + 文字导航 -->
    </nav>
    <main id="content">
      <section id="sec-overview">...</section>
      <section id="sec-code-hits">...</section>
      <section id="sec-impact">...</section>
      <section id="sec-contracts">...</section>
      <section id="sec-plan">...</section>
      <section id="sec-qa">...</section>
      <section id="sec-blockers">...</section>
      <section id="sec-suggestions">...</section>
    </main>
  </div>
  <script>
    const DATA = { /* 内联数据 */ };
    /* 导航切换、搜索过滤、折叠逻辑、checklist 持久化 */
  </script>
</body>
</html>
```

### 8. CSS 编写顺序

按以下顺序组织 CSS，确保可维护性：

```
1. CSS Reset (*, body)
2. CSS Variables (:root)
3. Typography (body, h1-h4, p, code, pre)
4. Layout (#app-header, #app-layout, #sidebar, #content)
5. Components (.card, .badge, .progress-bar, .search-box, table)
6. Sections (各 section 特有样式)
7. Animations (@keyframes, transitions)
8. Responsive (@media)
```

### 9. 质量要求

- **file:// 协议可用**：双击文件即可在浏览器中打开，无需 HTTP 服务器。
- **零外部依赖**：不加载任何 CDN、字体、CSS/JS 文件。
- **无 console 报错**：所有 JavaScript 变量先声明后使用。
- **空数据处理**：如果某个产出文件不存在或为空，对应 section 显示"该部分尚未生成"提示，不报错。
- **编码**：UTF-8，中文内容正常显示。
- **大小**：控制在合理范围（通常 < 500KB）。如数据量巨大，截断展示但保留完整数据在 `<script>` 中。
- **视觉一致性**：所有卡片、表格、徽章使用统一的 CSS 变量，不硬编码颜色值。

### 10. 生成后验证

生成 portal.html 后，Claude 应：

1. 确认文件存在于 `_prd-tools/distill/<slug>/portal.html`。
2. 在完成摘要中告知用户：
   - portal.html 已生成，可在浏览器中直接打开。
   - 文件路径：`_prd-tools/distill/<slug>/portal.html`。
