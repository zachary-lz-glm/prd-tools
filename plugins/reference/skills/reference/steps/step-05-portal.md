# 步骤 5：Portal HTML 生成

## 目标

生成 `_prd-tools/reference/portal.html`：一个完全自包含的 HTML 可视化页面，让用户在浏览器中浏览 reference 知识库，无需阅读原始 YAML。

## 何时生成

- Mode A 全量构建完成后（阶段 2 深度分析的最后一步）。
- Mode B 增量更新后，用户显式要求重新生成。
- Mode C 质量门控发现 reference 有更新后重新生成。

## 输入

读取 `_prd-tools/reference/` 下的全部 7 个文件：

| 文件 | 用途 |
|------|------|
| `00-portal.md` | 提取项目名称、层级、健康状态 |
| `project-profile.yaml` | 项目画像卡片数据 |
| `01-codebase.yaml` | 目录结构、枚举、模块、数据流 |
| `02-coding-rules.yaml` | 编码规则（severity 分级）、高风险区域、踩坑经验 |
| `03-contracts.yaml` | 契约表格（producer/consumer/alignment） |
| `04-routing-playbooks.yaml` | 路由信号、场景打法、QA 矩阵、golden samples |
| `05-domain.yaml` | 术语表、隐式规则、决策日志 |

## 输出

`_prd-tools/reference/portal.html` — 单文件，零外部依赖。

## 生成规则

### 1. 数据内联

Claude 逐个 Read 上述 7 个文件，将内容解析为 JavaScript 对象，内联到一个 `<script>` 标签中：

```html
<script>
const DATA = {
  portal: { /* 从 00-portal.md 解析 */ },
  profile: { /* project-profile.yaml 的 JSON */ },
  codebase: { /* 01-codebase.yaml 的 JSON */ },
  codingRules: { /* 02-coding-rules.yaml 的 JSON */ },
  contracts: { /* 03-contracts.yaml 的 JSON */ },
  routingPlaybooks: { /* 04-routing-playbooks.yaml 的 JSON */ },
  domain: { /* 05-domain.yaml 的 JSON */ }
};
</script>
```

YAML 内容转为 JSON 后嵌入。如果某个文件不存在，对应 key 的值为 `null`。

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
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-primary); }
h2 { font-size: 20px; font-weight: 650; letter-spacing: -0.01em; color: var(--text-primary); }
h3 { font-size: 15px; font-weight: 600; color: var(--text-primary); }
h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }
body { font-size: 14px; line-height: 1.6; color: var(--text-primary); }
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
.badge-hard    { background: var(--danger-bg);  color: #D70015; }
.badge-soft    { background: var(--info-bg);    color: #0077C7; }
```

**表格 (Table)**:
```css
table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
th {
  padding: 10px 14px; text-align: left;
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-strong);
  background: transparent;
}
td { padding: 12px 14px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--accent-subtle); }
td code.path { background: var(--bg-inset); padding: 2px 8px; border-radius: var(--radius-sm); font-size: 12px; }
```

**搜索框**:
```css
.search-box {
  width: 100%; padding: 10px 14px 10px 36px;
  border: 1px solid var(--border-strong); border-radius: var(--radius-md);
  font-size: 14px; background: var(--bg-card);
  transition: all var(--transition-fast); outline: none;
}
.search-box:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
```

**代码块**:
```css
pre { background: var(--bg-code); color: #e0e0e2; padding: 16px 20px; border-radius: var(--radius-md); font-size: 13px; line-height: 1.6; overflow-x: auto; }
```

### 3. 页面结构

```
+---------------------------------------------------------------+
| Header: 项目名 / 层级 badge / 版本 / 最后验证日期              |
+----------+----------------------------------------------------+
| Sidebar  |  Content Area (max-width: 1000px, centered)        |
| (窄，    |                                                    |
|  图标+   |  卡片式内容，大量留白                               |
|  文字)   |                                                    |
|          |                                                    |
| ○ 画像   |                                                    |
| ○ 代码库 |                                                    |
| ○ 规则   |                                                    |
| ○ 契约   |                                                    |
| ○ 路由   |                                                    |
| ○ 领域   |                                                    |
+----------+----------------------------------------------------+
```

#### Header

深色渐变背景，包含：
- 项目名称（20px, 700 weight）
- 层级标签（frontend/bff/backend/multi-layer 药丸 badge）
- schema_version 和 tool_version（12px, tertiary color）
- last_verified 日期

#### Sidebar

- 深色背景 (#0f0f11)，宽度 200px
- 每个 nav item 带图标（Unicode emoji 或内联 SVG）+ 文字
- 选中项：左侧 2px 紫色竖条 + 半透明背景 + 白色文字
- 悬停：微妙背景变化，平滑过渡
- 移动端：折叠为汉堡菜单

#### Content Area

- 最大宽度 1000px，居中
- `padding: 32px 40px`
- section 切换用 `opacity` + `transform` 过渡

### 4. 各 Section 展示

#### 画像 Section

卡片布局：
- **基本信息**：卡片内用 key-value 行展示，key 用 secondary color，value 用 primary
- **技术栈**：tag 列表，每个技术用圆角 tag
- **关联项目**：带箭头图标的关联关系卡片
- **关键数据**：大号数字统计行

#### 代码库 Section

**目录树展示（关键优化）**：

目录树**不使用纯文本 + Unicode 树形符号**，而是用结构化 HTML 列表实现：

```html
<div class="tree-view">
  <div class="tree-node" data-depth="0">
    <span class="tree-toggle" onclick="toggleTree(this)">▼</span>
    <span class="tree-folder">src/</span>
  </div>
  <div class="tree-children" style="padding-left:20px">
    <div class="tree-node" data-depth="1">
      <span class="tree-icon">📄</span>
      <span class="tree-file">index.ts</span>
      <span class="tree-hint">入口: HelloApp</span>
    </div>
    <div class="tree-node" data-depth="1">
      <span class="tree-toggle" onclick="toggleTree(this)">▶</span>
      <span class="tree-folder">base/</span>
      <span class="tree-hint">抽象基类</span>
    </div>
    <div class="tree-children" style="display:none;padding-left:20px">
      <!-- 子节点 -->
    </div>
    <!-- 更多节点 -->
  </div>
</div>
```

CSS 样式：
```css
.tree-view { font-family: 'SF Mono', 'Fira Code', Consolas, monospace; font-size: 13px; line-height: 2; }
.tree-node { display: flex; align-items: center; gap: 6px; padding: 1px 0; }
.tree-toggle { cursor: pointer; width: 16px; text-align: center; color: var(--text-tertiary); user-select: none; transition: transform var(--transition-fast); }
.tree-folder { color: var(--accent); font-weight: 600; }
.tree-file { color: var(--text-primary); }
.tree-hint { color: var(--text-tertiary); font-size: 12px; margin-left: 8px; }
.tree-children { overflow: hidden; transition: max-height 0.2s ease; }
```

关键要求：
- **每行一个节点**，不用纯文本拼接（避免 CJK 字符宽度导致错位）
- **可折叠/展开**：点击文件夹可展开子节点
- **缩进用 padding-left**，不用空格或 tab
- **文件和文件夹有视觉区分**：文件夹紫色加粗，文件黑色
- **注释/说明用灰色**，放在节点右侧
- **图标**：文件夹用文件夹图标，文件用文件图标（emoji 或 SVG 内联）
- **默认展开前 2 层**，更深层默认折叠

**枚举表格**：
- 搜索框实时过滤
- 枚举值列用 monospace + accent color
- 值数量较多时只展示前 20 行 + "展开更多" 按钮

**模块卡片**：按功能分组，每个模块一张卡片，含文件列表和关键说明。

#### 规则 Section

- 过滤按钮组：全部 / Hard / Soft
- 每条规则用卡片展示：
  - ID + 标题 + severity badge
  - 规则描述
  - 高风险规则用左边框颜色区分
- Danger Zones 单独用红色警告卡片
- 踩坑经验用黄色左边框卡片

#### 契约 Section

- 契约概况卡片：aligned/needs_confirmation/blocked 数字统计
- 契约表格：
  - contract name / producer / consumers / alignment
  - alignment 颜色编码：aligned=绿、needs_confirmation=黄、blocked=红
  - 支持按 producer/consumer/alignment 过滤
  - 点击行可展开详情

#### 路由 Section

- 路由信号卡片列表
- Playbook 展开面板（可折叠）
- QA 矩阵表格（优先级 badge）
- Golden samples 高亮卡片

#### 领域 Section

- 术语搜索表（实时搜索框）
- 决策日志时间线（左侧竖线 + 节点）
- 隐式规则列表

### 5. 动效要求

```css
/* Section 切换 */
section { opacity: 0; transform: translateY(8px); transition: opacity 0.2s, transform 0.2s; display: none; }
section.active { display: block; opacity: 1; transform: translateY(0); }

/* 卡片悬停 */
.card { transition: box-shadow var(--transition-fast), transform var(--transition-fast); }
.card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }

/* 树形展开 */
.tree-children { transition: max-height 0.25s ease; }
```

### 6. 交互要求

- Sidebar 导航：点击切换内容区，当前项高亮（左侧竖条 + 背景色变化）。
- 移动端：sidebar 折叠为汉堡菜单。
- 可折叠区域：自定义 toggle + CSS 过渡。
- 搜索：术语表、枚举表、契约表支持实时搜索。
- 树形目录：点击文件夹展开/折叠，默认展开前 2 层。
- 过滤按钮：编码规则、契约状态支持分类过滤。
- 无需任何 JavaScript 框架。

### 7. 模板结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project} Reference Portal</title>
  <style>
    /* CSS Reset → Variables → Typography → Layout → Components → Sections → Animations → Responsive */
  </style>
</head>
<body>
  <header id="app-header">
    <!-- 项目名 / 层级 / 版本 / 日期 -->
  </header>
  <div id="app-layout">
    <nav id="sidebar">
      <!-- 图标 + 文字导航 -->
    </nav>
    <main id="content">
      <section id="sec-profile">...</section>
      <section id="sec-codebase">...</section>
      <section id="sec-rules">...</section>
      <section id="sec-contracts">...</section>
      <section id="sec-routing">...</section>
      <section id="sec-domain">...</section>
    </main>
  </div>
  <script>
    const DATA = { /* 内联数据 */ };
    /* 导航切换、搜索过滤、折叠逻辑、树形展开 */
  </script>
</body>
</html>
```

### 8. CSS 编写顺序

```
1. CSS Reset (*, body)
2. CSS Variables (:root)
3. Typography (body, h1-h4, p, code, pre)
4. Layout (#app-header, #app-layout, #sidebar, #content)
5. Components (.card, .badge, table, .search-box)
6. Sections (各 section 特有样式)
7. Tree View (.tree-view, .tree-node, .tree-folder, .tree-file)
8. Animations (@keyframes, transitions)
9. Responsive (@media)
```

### 9. 质量要求

- **file:// 协议可用**：双击文件即可在浏览器中打开，无需 HTTP 服务器。
- **零外部依赖**：不加载任何 CDN、字体、CSS/JS 文件。
- **无 console 报错**：所有 JavaScript 变量先声明后使用。
- **空数据处理**：如果某个 reference 文件不存在或为空，对应 section 显示"该部分尚未构建"提示，不报错。
- **编码**：UTF-8，中文内容正常显示。
- **大小**：控制在合理范围（通常 < 500KB）。如数据量巨大，截断展示但保留完整数据在 `<script>` 中。
- **视觉一致性**：所有卡片、表格、徽章使用统一的 CSS 变量，不硬编码颜色值。

### 10. 生成后验证

生成 portal.html 后，Claude 应：

1. 确认文件存在于 `_prd-tools/reference/portal.html`。
2. 在完成摘要中告知用户：
   - portal.html 已生成。
   - 可通过浏览器直接打开查看。
   - 文件路径：`_prd-tools/reference/portal.html`。
