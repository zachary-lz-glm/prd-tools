# Portal 设计系统

两个 portal（reference 和 prd-distill）共享的视觉设计系统。生成 portal.html 时按此规范编写 CSS。

## 设计理念

参考 Linear / Vercel Dashboard / Notion 风格：克制的装饰、大量留白、清晰的信息层级、微妙的动效。

## 配色方案

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

## Typography

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

## 组件样式

### 卡片 (Card)

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

### 徽章 (Badge)

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
.badge-hard    { background: var(--danger-bg);  color: #D70015; }
.badge-soft    { background: var(--info-bg);    color: #0077C7; }

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

### 表格 (Table)

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

### 进度条 (Progress)

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

### 搜索框 (Search)

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

### 代码块 (Code)

```css
pre {
  background: var(--bg-code); color: #e0e0e2;
  padding: 16px 20px; border-radius: var(--radius-md);
  font-size: 13px; line-height: 1.6;
  overflow-x: auto; margin: 8px 0;
}
```

## 动效模式

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

/* 树形展开（reference portal 专用） */
.tree-children { transition: max-height 0.25s ease; }
```

## CSS 编写顺序

按以下顺序组织 CSS，确保可维护性：

```
1. CSS Reset (*, body)
2. CSS Variables (:root)
3. Typography (body, h1-h4, p, code, pre)
4. Layout (#app-header, #app-layout, #sidebar, #content)
5. Components (.card, .badge, .progress-bar, .search-box, table)
6. Sections (各 section 特有样式)
7. Tree View (.tree-view, .tree-node, .tree-folder, .tree-file)（reference portal 专用）
8. Animations (@keyframes, transitions)
9. Responsive (@media)
```

## 质量要求

- **file:// 协议可用**：双击文件即可在浏览器中打开，无需 HTTP 服务器。
- **零外部依赖**：不加载任何 CDN、字体、CSS/JS 文件。
- **无 console 报错**：所有 JavaScript 变量先声明后使用。
- **空数据处理**：如果某个文件不存在或为空，对应 section 显示提示（"该部分尚未构建" / "该部分尚未生成"），不报错。
- **编码**：UTF-8，中文内容正常显示。
- **大小**：控制在合理范围（通常 < 500KB）。如数据量巨大，截断展示但保留完整数据在 `<script>` 中。
- **视觉一致性**：所有卡片、表格、徽章使用统一的 CSS 变量，不硬编码颜色值。
