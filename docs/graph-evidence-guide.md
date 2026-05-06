# Graph Evidence 使用指南

> prd-tools v2.5.0 引入了图谱证据层。这篇文档只回答一个问题：**我现在要做什么，怎么做。**

---

## 0. 先理解一件事

v2.5.0 没有改变 prd-tools 的任何现有用法。

`/build-reference` 还是那个命令，`/prd-distill` 也还是那个命令。产出还是 6 个 reference 文件 + report/plan；阻塞问题和待确认项收口在 `report.md` §11。

核心变化是：**如果你装了 GitNexus 或 Graphify，build-reference 和 prd-distill 会自动从图谱拿数据，产出质量更高。** prd-distill 会先生成 `artifacts/graph-context.md`，再把函数级代码坐标、调用链、API consumer 和业务约束写进 `report.md` 与 `plan.md`。没装图谱工具时仍可用，只是回退到 rg/Read 和 `_reference`。

还有一个边界要记住：`_reference/` 默认是单仓知识库。图谱可以发现跨仓线索，但没有 owner 确认时只能写成 `needs_confirmation`、handoff 或团队知识库候选，不能当成其他仓的确定事实。

---

## 1. 图谱工具是什么，各自干什么

把你的项目想象成一栋大楼。

**GitNexus = 建筑结构图**

它扫描代码，画出精确的"承重墙和管线"：哪个函数调用哪个、哪个模块依赖哪个、改一根管线会影响几层楼。

- 输入：代码仓库
- 输出：调用链、依赖图、影响范围
- 典型问题："改了 field-registry.ts，还有哪些文件会受影响？"

**Graphify = 设计意图档案**

它同时读取代码、PRD、技术方案、截图、流程图，提取"为什么这面墙在这里、这条管线为什么绕路"：业务概念之间的关系、设计决策的原因、隐式规则。

- 输入：代码 + PRD + 技术方案 + 截图 + PDF
- 输出：业务概念图、设计原理、跨域关联
- 典型问题："冲单奖这个功能为什么分成了 BFF + 后端两步？历史决策是什么？"

**prd-tools = 装修指南**

它把结构图和设计档案加工成一份给开发团队用的"装修操作手册"：这次 PRD 要改哪些墙、改之前要确认什么、改完怎么验证。

---

## 2. 安装（一次性）

### GitNexus

如果机器有 Node/npx，在 `~/.claude/.mcp.json` 的 `mcpServers` 里加一段：

```json
"gitnexus": {
  "command": "npx",
  "args": ["-y", "gitnexus@latest", "mcp"],
  "env": {}
}
```

没有 Node 也可以用 Bun：

```json
"gitnexus": {
  "command": "bunx",
  "args": ["--bun", "gitnexus@latest", "mcp"],
  "env": {}
}
```

安装完成。重启 Claude Code 后，你会多出 7 个 MCP 工具（impact、context、query 等）。

### Graphify

```bash
uv tool install graphifyy
graphify install
```

安装完成。在 Claude Code 里你会多出 `/graphify`、`/graphify query`、`/graphify path`、`/graphify explain` 四个命令。

### 不想装？

不用装。prd-tools 照常工作，只是没有图谱增强。

---

## 3. 首次使用：给项目建 reference

以 `dive-bff` 为例，完整走一遍。

### 3.1 建图谱

先在项目根目录跑两条命令：

```bash
cd /Users/didi/work/dive-bff

# 建代码结构图（1-3 分钟）
npx -y gitnexus@latest analyze
# 没有 Node 时可用：bunx --bun gitnexus@latest analyze

# 建业务语义图（把 PRD 和技术方案也吃进去）
/graphify . --mode deep
```

跑完后项目里多了两个目录：

```
dive-bff/
├── .gitnexus/                    ← 代码结构图
│   └── graph.db
├── graphify-out/                 ← 业务语义图
│   ├── graph.json                ← 可查询的图谱数据
│   ├── graph.html                ← 可视化（浏览器打开就能看）
│   └── GRAPH_REPORT.md           ← 分析报告
```

你可以先打开 `graphify-out/graph.html` 看看——它会展示项目里的核心概念（God Nodes）、意外关联（Surprising Connections），以及设计原理（rationale_for）。

### 3.2 跑 build-reference

```
/build-reference
```

就这个命令，跟以前一样。但 v2.5.0 的 build-reference 内部做了这些事：

```
                    你看到的                        背后发生的
                    ───────                        ──────────

1. 选择模式            → A 全量构建

2. 结构扫描            → 问 GitNexus：有哪些模块、函数、调用链？
                        问 Graphify：核心业务概念是什么？
                        两个答案合并，不够的用 rg/glob 补

3. 深度分析            → 按数据源分工写 reference：
                        01-codebase.yaml ← GitNexus 的模块和符号
                        03-contracts.yaml ← GitNexus 的跨文件契约
                        02-coding-rules.yaml ← Graphify 的设计原理
                        04-routing-playbooks.yaml ← Graphify 的业务模式
                        05-domain.yaml ← Graphify 的领域术语

4. 写出 _reference/     → 6 个文件，格式跟以前一样
```

### 3.3 看产出

```bash
ls _reference/
# 00-portal.md  project-profile.yaml  01-codebase.yaml
# 02-coding-rules.yaml  03-contracts.yaml  04-routing-playbooks.yaml  05-domain.yaml

ls _output/graph/
# code-graph-evidence.yaml        ← GitNexus 提供了什么证据
# business-graph-evidence.yaml    ← Graphify 提供了什么证据
```

打开任意一个 reference 文件。如果某条事实来自图谱，你会看到：

```yaml
evidence:
  - id: "EV-001"
    kind: "knowledge_graph"        # ← 图谱提供的，不是人工读的
    source: "gitnexus"
    locator: "src/config/field-registry.ts:handleLogin"
    summary: "GitNexus 确认 handleLogin 被 3 个模块调用"
```

**关键**：reference 文件格式完全没变。图谱只是让数据更准确、更快。你以前的阅读方式、使用方式不需要任何调整。

---

## 4. 日常使用：处理新 PRD

拿到一个新 PRD（比如"DIVE 2.0 新增运力线冲单奖"）。

### 4.1 先更新图谱（如果代码有变动）

```bash
# 代码改了？增量更新代码图谱
npx -y gitnexus@latest analyze --incremental
# 没有 Node 时可用：bunx --bun gitnexus@latest analyze --incremental

# 加了新 PRD 文档？增量更新业务图谱
/graphify . --update
```

### 4.2 跑 prd-distill

```
/prd-distill
```

跟以前一样。但 v2.5.0 在分类需求后，会**自动做两步额外检查**：

**第一步：问 GitNexus — 改代码会影响谁？**

```
需求："新增运力线冲单奖"
  ↓
提取关键词：冲单奖、运力线、奖励类型
  ↓
GitNexus impact 查询：
  "冲单奖" 相关字段 → 影响 3 个模块、12 个函数
  ↓
自动标记风险：影响面 > 5 个模块 → risk_level 提升
```

**第二步：问 Graphify — 业务上有什么要注意的？**

```
需求："新增运力线冲单奖"
  ↓
Graphify 追踪业务关联：
  "冲单奖" → 历史上跟"可选择奖"共用奖励计算逻辑
  → 设计时考虑了 XTR 油站权益的特殊处理
  → 有一个隐式规则：冲单奖和班次签到奖互斥
  ↓
自动写入 business_constraints
```

### 4.3 看产出

打开 `report.md`。影响分析部分现在有三个维度的数据：

- **代码影响**："修改 reward-type.enum.ts 将影响 rewardService、rewardController、rewardExporter 共 3 个模块"
- **契约影响**："新增 rewardType 字段会影响 /api/reward consumer 的字段读取和导出链路"
- **业务影响**："冲单奖与班次签到奖存在互斥规则，新增时需确认互斥逻辑是否需要调整"

打开 `plan.md`。实现计划会优先消费 `artifacts/graph-context.md`：

```text
REQ -> GitNexus query/context/impact/api_impact -> GCTX 函数级线索
REQ -> Graphify query/path/explain -> GCTX-B 业务约束
GCTX/GCTX-B -> plan.md 的文件、行号、关键函数、调用链、回归范围
```

以前这些只能靠 AI 读代码猜。现在是图谱查出来，再由源码/PRD/技术文档证据确认。

---

## 5. 快速查询：不想跑完整流程

有时候你只想快速查一个东西，不需要跑完整的 build-reference 或 prd-distill。

### 查代码影响

直接在 Claude Code 里问：

> "改了 dive-bff 的 field-registry.ts，会影响哪些模块？"

Claude Code 会调用 GitNexus MCP 工具，直接返回调用链和影响范围。

### 查业务概念

> /graphify explain "冲单奖"

Graphify 会告诉你这个概念在项目里的来龙去脉：什么时候引入的、跟哪些概念关联、有没有设计原理注释。

### 查两个概念之间的关系

> /graphify path "冲单奖" "运力线"

Graphify 会画出两个概念之间的关联路径。

---

## 6. 图谱更新：保持数据新鲜

图谱建好之后不是一劳永逸的。代码改了，图谱要跟着变。

### 方式 A：手动（推荐初期使用）

```bash
# 代码改了
npx -y gitnexus@latest analyze --incremental          # 30 秒左右
# 没有 Node 时可用：bunx --bun gitnexus@latest analyze --incremental

# 文档改了
/graphify . --update                        # 1-2 分钟
```

### 方式 B：自动（推荐稳定后使用）

在项目的 `.claude/settings.json` 里加 hooks：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "cd $PROJECT_DIR && (npx -y gitnexus@latest analyze --incremental || bunx --bun gitnexus@latest analyze --incremental) 2>/dev/null || true"
          },
          {
            "type": "command",
            "command": "cd $PROJECT_DIR && graphify . --update 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

之后每次 commit，图谱自动增量更新。

---

## 7. 什么时候做什么：速查表

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   第一次接入项目？                                        │
│   ├── gitnexus analyze                                  │
│   ├── /graphify . --mode deep                           │
│   └── /build-reference  A 全量构建                       │
│                                                         │
│   拿到新 PRD？                                           │
│   ├── (可选) 更新图谱                                     │
│   └── /prd-distill                                      │
│                                                         │
│   代码改了要更新 reference？                               │
│   ├── gitnexus analyze --incremental                    │
│   ├── /graphify . --update                              │
│   └── /build-reference  B 增量更新                       │
│                                                         │
│   只想查一下影响？                                        │
│   ├── 代码影响 → 直接问 Claude Code                       │
│   └── 业务概念 → /graphify query / path / explain        │
│                                                         │
│   PRD 做完了要回流知识？                                   │
│   └── /build-reference  E 反馈回流                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 8. 注意事项

**图谱 ≠ reference。** 图谱是原始数据，reference 是精选后的知识库。build-reference 会自动过滤图谱噪声，只把确认后的本仓事实写进 reference。

**Graphify 的推断不是高置信度。** Graphify 标记为 INFERRED 的关系，build-reference 会自动降级为 medium/low，不会直接当事实用。

**没装图谱工具不影响使用。** 每一步都有回退机制——没有 GitNexus 就用 rg/glob，没有 Graphify 就逐文件 Read。prs-tools 照常工作，只是没有图谱增强。

**不要把完整图谱塞进上下文。** build-reference 和 prd-distill 内部只用 query 拉小子图，不会把整个 graph.json 读进去。手动查询时也注意控制范围。

**图谱本地存储，不外传。** GitNexus 的 `.gitnexus/` 和 Graphify 的 `graphify-out/` 都在项目本地，建议加入 `.gitignore`。团队共享图谱可以只提交 `GRAPH_REPORT.md`，或由未来团队知识库聚合各仓 confirmed/candidate 事实。
