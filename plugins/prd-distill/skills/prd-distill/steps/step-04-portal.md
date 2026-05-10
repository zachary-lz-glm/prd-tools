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

### 2. 纯内联样式

- 所有 CSS 写在 `<style>` 标签中。
- 不引用任何 CDN、外部字体、外部 CSS/JS 文件。
- 使用系统字体栈：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`。

### 3. 页面结构

页面分为 9 个可视化 Section，通过顶部 sticky Nav 导航切换。必须与 reference portal 使用同一套视觉语言：顶部渐变 Header、横向 sticky Nav、居中内容容器、白色信息卡片、8px 圆角、统一 tag/badge/score 色板。

```
+---------------------------------------------------------------+
| Header: 就绪度评分徽章 / PRD 标题 / 项目名 / 时间戳          |
+---------------------------------------------------------------+
| Sticky Top Nav: 总览 / 源码命中 / 影响分析 / 契约差异...       |
+---------------------------------------------------------------+
| Centered Content Area                                          |
|  (根据 nav 选择切换 section)                                   |
+---------------------------------------------------------------+
```

### 4. 各 Section 设计要求

#### Section 1：Dashboard Header（总览）

**Header（始终可见）**：
- 就绪度评分：大号数字 + 颜色编码徽章（pass=绿色 85-100，warning=黄色 60-84，fail=红色 0-59）
- decision 标签：`ready_for_dev` / `needs_owner_confirmation` / `blocked`
- PRD 标题、项目名、生成时间戳
- 评分维度小卡片（prd_ingestion / evidence_coverage / code_search / contract_alignment / task_executability），每项显示分数和进度条

**Executive Summary（总览内容区）**：
- Top conclusions：从 report.md §4 提取的关键结论列表
- 变更类型统计：ADD/MODIFY/DELETE/NO_CHANGE 各几项，用彩色数字展示
- 关键风险摘要：从 readiness-report.yaml risks 提取
- 证据统计：各类型证据数量（prd / code / tech_doc / negative_code_search 等）

#### Section 2：源码命中

- 交互式表格，列为：`| GCTX-ID | 符号 | 文件:行号 | 类型 | 角色 | 调用方 | 被调用方 | 置信度 |`
- 数据来源：`graph-context.md` 的函数级上下文条目
- 搜索未命中的条目单独展示
- 支持按角色（entrypoint/validator/transformer/persistence/external_call/consumer）过滤
- 支持按置信度过滤

#### Section 3：影响分析（Layer Impact）

- 按层分组的卡片（frontend / BFF / backend），每层一个卡片
- 每张卡片显示：
  - 影响数量和变更类型分布
  - 受影响能力面（surface）列表
  - 受影响文件/模块列表
  - 每个 IMP-* 项的摘要：target、planned_delta、confidence 徽章
- 无影响的层显示"该层无影响"

#### Section 4：契约差异（Contract Delta）

- 表格：`| ID | 名称 | Producer | Consumers | 变更类型 | 对齐状态 |`
- alignment_status 颜色编码：
  - `aligned` = 绿色徽章
  - `needs_confirmation` = 黄色徽章
  - `blocked` = 红色徽章
  - `not_applicable` = 灰色徽章
- 点击契约行可展开查看 request_fields / response_fields 详情
- 顶部显示 alignment_summary 概况

#### Section 5：开发计划（Plan Overview）

- 按 Phase 分组的可折叠面板
- 每个 Phase 内的 Step 用 `- [ ]` checklist 展示
- 每个 checklist 项包含：
  - 任务描述
  - 文件路径（可点击复制的代码路径样式）
  - 行号（如有）
  - 关联 REQ/IMP/CONTRACT 标签
  - 验证命令（代码样式展示）
- **交互式 checklist**：点击可切换勾选状态，状态保存在 localStorage
- Phase 间的前置依赖标注

#### Section 6：QA 矩阵

- 表格：`| 场景 | 关键检查点 | 关联 REQ | 优先级 |`
- 优先级徽章：P0=红色、P1=橙色、P2=蓝色
- 支持按优先级过滤

#### Section 7：阻塞问题

- 高亮警告区域
- §11.1 阻塞问题：每个问题卡片包含 6 要素（问题、线索、影响、建议 Owner、需要证据、默认策略）
- §11.2 低置信度假设：带警告图标的列表
- §11.3 Owner 确认项：按 Owner 角色分组的列表
- 如无阻塞问题，显示绿色"当前无阻塞问题"提示

#### Section 8：回流建议

- 卡片列表：`| ID | 类型 | 目标文件 | 摘要 | 优先级 | 置信度 |`
- 优先级颜色编码（high=红、medium=黄、low=蓝）
- 类型标签：new_term / new_route / new_contract / new_playbook / contradiction / golden_sample_candidate

### 5. 配色方案（CSS 变量）

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

### 6. 交互要求

- Top Nav 导航：点击切换内容区，当前选中项高亮。
- 移动端：导航横向滚动，内容全宽。
- 可折叠区域：用 `<details>/<summary>` 或自定义 toggle。
- 搜索/过滤：源码命中表和 QA 矩阵支持实时搜索。
- Checklist 持久化：plan 的 checklist 勾选状态保存到 `localStorage`，刷新后保留。
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
    /* 所有 CSS 内联于此 */
  </style>
</head>
<body>
  <div class="header">...</div>
  <div class="nav">...</div>
  <div class="container">
    <div class="section active" id="s-overview">...</div>
    <div class="section" id="s-code-hits">...</div>
    <div class="section" id="s-impact">...</div>
    <div class="section" id="s-contracts">...</div>
    <div class="section" id="s-plan">...</div>
    <div class="section" id="s-qa">...</div>
    <div class="section" id="s-blockers">...</div>
    <div class="section" id="s-suggestions">...</div>
  </div>
  <script>
    const DATA = { /* 内联数据 */ };
    /* 导航切换、搜索过滤、折叠逻辑、checklist 持久化 */
  </script>
</body>
</html>
```

### 8. 质量要求

- **file:// 协议可用**：双击文件即可在浏览器中打开，无需 HTTP 服务器。
- **零外部依赖**：不加载任何 CDN、字体、CSS/JS 文件。
- **无 console 报错**：所有 JavaScript 变量先声明后使用。
- **空数据处理**：如果某个产出文件不存在或为空，对应 section 显示"该部分尚未生成"提示，不报错。
- **编码**：UTF-8，中文内容正常显示。
- **大小**：控制在合理范围（通常 < 500KB）。如数据量巨大，截断展示但保留完整数据在 `<script>` 中。

### 9. 生成后验证

生成 portal.html 后，Claude 应：

1. 确认文件存在于 `_prd-tools/distill/<slug>/portal.html`。
2. 在完成摘要中告知用户：
   - portal.html 已生成，可在浏览器中直接打开。
   - 文件路径：`_prd-tools/distill/<slug>/portal.html`。
