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

### 2. 纯内联样式

- 所有 CSS 写在 `<style>` 标签中。
- 不引用任何 CDN、外部字体、外部 CSS/JS 文件。
- 使用系统字体栈：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`。

### 3. 设计要求

**统一视觉原则**：

reference portal 和 prd-distill portal 必须使用同一套视觉语言，优先采用 prd-distill portal 的产品化样式：顶部渐变 Header、横向 sticky Nav、居中内容容器、白色信息卡片、8px 圆角、统一 tag/badge/score 色板。不要再使用深色左侧 sidebar 作为 reference 的专属样式。

**页面结构**：

```
+-----------------------------------------------+
| Header: 项目名 / 层级 / 版本 / 最后验证日期    |
+-----------------------------------------------+
| Sticky Top Nav: 画像 / 代码库 / 规则 / 契约... |
+-----------------------------------------------+
| Centered Content Area                          |
|  (根据 nav 选择切换 section)                   |
+-----------------------------------------------+
```

**Header**：
- 显示项目名称（从 `project-profile.yaml` 的 `project` 字段）。
- 层级标签（frontend/bff/backend/multi-layer）。
- schema_version 和 tool_version。
- last_verified 日期。

**顶部导航**：
- 6 个 section：画像、代码库、规则、契约、路由、领域。
- 点击切换右侧内容区。
- 当前选中项高亮。
- 移动端横向滚动，不使用独立侧栏。

**各 Section 展示**：

| Section | 关键展示 |
|---------|---------|
| 画像 | 卡片形式：技术栈标签、入口列表、能力面表格、关联仓库 |
| 代码库 | 目录树（等宽字体、可折叠）、枚举列表、模块卡片 |
| 规则 | severity 徽章（fatal=红、warning=橙、info=蓝）、分类过滤、danger zones 警告框 |
| 契约 | 表格：contract name / producer / consumers / alignment（颜色编码：aligned=绿、needs_confirmation=黄、blocked=红）|
| 路由 | 路由信号卡片、playbook 展开面板、QA 矩阵表格、golden samples |
| 领域 | 术语搜索表、决策日志时间线、隐式规则列表 |

**搜索/过滤**：
- 术语表提供搜索框，实时过滤。
- 契约表格支持按 producer/consumer/alignment 状态过滤。
- 路由 playbook 支持按信号关键词搜索。
- 编码规则支持按 category 和 severity 过滤。

**响应式**：
- 桌面：顶部 sticky nav + 居中内容容器。
- 平板/手机：顶部 nav 横向滚动，内容全宽。

**配色方案**（使用 CSS 变量）：

```css
:root{
  --bg:#f8f9fa;
  --card:#ffffff;
  --border:#e2e8f0;
  --text:#1a202c;
  --text2:#4a5568;
  --accent:#3b82f6;
  --accent2:#8b5cf6;
  --green:#10b981;
  --red:#ef4444;
  --orange:#f59e0b;
  --tag-bg:#edf2f7;
}
```

基础布局样式建议：

```css
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.header{background:linear-gradient(135deg,#1e40af,#7c3aed);color:#fff;padding:32px 40px}
.header h1{font-size:28px;font-weight:700;margin-bottom:8px}
.header .meta{display:flex;gap:24px;font-size:14px;opacity:.9;flex-wrap:wrap}
.nav{background:#fff;border-bottom:1px solid var(--border);padding:0 40px;display:flex;overflow-x:auto;position:sticky;top:0;z-index:100}
.nav a{padding:12px 20px;font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;border-bottom:3px solid transparent;white-space:nowrap}
.nav a.active,.nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.container{max-width:1200px;margin:0 auto;padding:24px 40px}
.section{display:none}.section.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
```

**交互**：
- 所有 section 通过纯 JavaScript 切换（`display: none/block` 或 class toggle）。
- 可折叠区域用 `<details>/<summary>` 或自定义 toggle。
- 无需任何 JavaScript 框架。
- 搜索用 `input` 事件监听 + DOM 过滤。

### 4. 模板结构

Claude 生成 HTML 时应遵循以下骨架：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project} Reference Portal</title>
  <style>
    /* 所有 CSS 内联于此，建议与 prd-distill portal 统一视觉语言 */
  </style>
</head>
<body>
  <div class="header">...</div>
  <div class="nav">...</div>
  <div class="container">
    <div class="section active" id="s-profile">...</div>
    <div class="section" id="s-codebase">...</div>
    <div class="section" id="s-rules">...</div>
    <div class="section" id="s-contracts">...</div>
    <div class="section" id="s-routing">...</div>
    <div class="section" id="s-domain">...</div>
  </div>
  <script>
    const DATA = { /* 内联数据 */ };
    /* 导航切换、搜索过滤、折叠逻辑 */
  </script>
</body>
</html>
```

### 5. 质量要求

- **file:// 协议可用**：双击文件即可在浏览器中打开，无需 HTTP 服务器。
- **零外部依赖**：不加载任何 CDN、字体、CSS/JS 文件。
- **无 console 报错**：所有 JavaScript 变量先声明后使用。
- **空数据处理**：如果某个 reference 文件不存在或为空，对应 section 显示"该部分尚未构建"提示，不报错。
- **编码**：UTF-8，中文内容正常显示。
- **大小**：控制在合理范围（通常 < 500KB）。如数据量巨大，截断展示但保留完整数据在 `<script>` 中。

### 6. 生成后验证

生成 portal.html 后，Claude 应：

1. 确认文件存在于 `_prd-tools/reference/portal.html`。
2. 在完成摘要中告知用户：
   - portal.html 已生成。
   - 可通过浏览器直接打开查看。
   - 文件路径：`_prd-tools/reference/portal.html`。
