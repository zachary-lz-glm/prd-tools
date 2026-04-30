# 步骤 1：结构扫描

## 目标

创建 `_output/modules-index.yaml`，记录项目层级、能力面、关键文件、入口点、潜在契约面和证据。同时构建图谱证据（如图谱工具可用）。

## 输入

- 当前项目路径或用户提供的路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- `references/layer-adapters.md`。

## 执行

### 代码结构层（优先使用 GitNexus）

1. 检查当前项目是否有 `.gitnexus/` 索引（`mcp__gitnexus__list_repos`）。
2. 如果有索引：
   a. `mcp__gitnexus__query` — 获取所有模块和符号。
   b. `mcp__gitnexus__context` — 获取每个模块的调用者和被调用者。
   c. 将图谱结果映射到 capability_surfaces 结构（key_files、entrypoints、symbols）。
   d. 记录图谱证据到 `_output/graph/code-graph-evidence.yaml`。
3. 如果没有索引：
   a. 回退到原有 `rg`/glob 扫描流程。
   b. 建议用户运行 `npx gitnexus analyze` 以获得更好的扫描质量。

### 业务语义层（优先使用 Graphify）

4. 检查当前项目是否有 `graphify-out/graph.json`。
5. 如果有图谱：
   a. `/graphify query "项目核心模块和它们的业务职责"` — 提取业务语义。
   b. 将 God Nodes 映射为核心模块，Surprising Connections 映射为跨域依赖。
   c. 将 rationale_for 节点映射为设计原理和编码规则候选。
   d. 记录图谱证据到 `_output/graph/business-graph-evidence.yaml`。
6. 如果没有图谱：
   a. 回退到逐文件 Read 提取业务语义。
   b. 建议用户运行 `/graphify . --mode deep` 以获得业务语义提取。

### 通用扫描（始终执行）

7. 根据代码形态判断层级；不确定时让用户确认。
8. 加载对应能力面适配器，路径只作为候选。
9. 排除依赖、构建产物、测试、mock、fixture、生成物、`_reference`、`_output` 和 `.git`。
10. 合并图谱发现和 rg/glob 扫描的结果，去重。
11. 识别能力面、关键文件、入口点、注册点、数据流线索和潜在契约面。

### 图谱发现 vs 人工扫描的融合规则

| 场景 | 处理方式 |
|------|---------|
| 图谱和扫描都发现 | 优先使用图谱数据（AST 精度更高），人工扫描补充业务语义 |
| 只有图谱发现 | 保留，标注 `evidence.kind: knowledge_graph` |
| 只有人工扫描发现 | 保留，标注 `status: candidate` |
| 图谱和扫描结果冲突 | 以源码确认结果为准，记录冲突到 evidence |

## 输出

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
scan_at: ""
graph_providers: []                    # 可用图谱 provider 列表
capability_surfaces:
  - id: ""
    layer: ""
    surface: ""
    responsibility: ""
    key_files: []
    entrypoints: []
    symbols: []
    status: "candidate | verified | negative_search"
    likely_contracts: []
    evidence: []
    graph_source: "gitnexus | graphify | none"  # 该 surface 的主要图谱来源
unclassified_files: []
```

图谱证据输出到：

```yaml
# _output/graph/code-graph-evidence.yaml
graph_evidence:
  - id: "GEV-001"
    provider: "gitnexus"
    graph: "code"
    query: ""
    result_summary: ""
    source: ".gitnexus/"
    source_files: []
    used_for: ["01-codebase.yaml"]
    confidence: "high"
```

```yaml
# _output/graph/business-graph-evidence.yaml
graph_evidence:
  - id: "GEV-B001"
    provider: "graphify"
    graph: "business"
    query: "项目核心模块和它们的业务职责"
    result_summary: ""
    source: "graphify-out/graph.json"
    source_files: []
    used_for: ["05-domain.yaml", "04-routing-playbooks.yaml"]
    confidence: "medium"
```

## 校验

- 所有关键文件都存在。
- 当前层适配器的核心能力面已检查。
- 无法归类的文件要列入 `unclassified_files`，不要猜测归属。
- 如果图谱工具可用，至少一个 capability_surface 标注了 `graph_source`。
