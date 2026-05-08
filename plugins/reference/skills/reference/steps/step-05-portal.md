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

**页面结构**：

```
+-----------------------------------------------+
| Header: 项目名 / 层级 / 版本 / 最后验证日期    |
+--------+--------------------------------------+
| Sidebar|  Content Area                        |
| Nav    |  (根据 sidebar 选择切换)              |
|        |                                      |
| 画像   |                                      |
| 代码库 |                                      |
| 规则   |                                      |
| 契约   |                                      |
| 路由   |                                      |
| 领域   |                                      |
+--------+--------------------------------------+
```

**Header**：
- 显示项目名称（从 `project-profile.yaml` 的 `project` 字段）。
- 层级标签（frontend/bff/backend/multi-layer）。
- schema_version 和 tool_version。
- last_verified 日期。

**Sidebar 导航**：
- 6 个 section：画像、代码库、规则、契约、路由、领域。
- 点击切换右侧内容区。
- 当前选中项高亮。
- 移动端折叠为汉堡菜单。

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
- 桌面：固定 sidebar + 内容区。
- 平板：sidebar 可折叠。
- 手机：sidebar 变为顶部汉堡菜单，内容全宽。

**配色方案**（使用 CSS 变量）：

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-sidebar: #1a1a2e;
  --text-primary: #2d3436;
  --text-secondary: #636e72;
  --text-sidebar: #e0e0e0;
  --accent: #6c5ce7;
  --accent-light: #a29bfe;
  --border: #dfe6e9;
  --success: #00b894;
  --warning: #fdcb6e;
  --danger: #e17055;
  --info: #74b9ff;
  --fatal: #d63031;
}
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
    /* 所有 CSS 内联于此 */
  </style>
</head>
<body>
  <header id="app-header">...</header>
  <div id="app-layout">
    <nav id="sidebar">...</nav>
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
