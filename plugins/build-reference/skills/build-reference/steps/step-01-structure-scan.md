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

### 图谱证据文件创建（必执行）

无论图谱工具是否可用，本步骤**必须**执行以下操作：

1. 创建 `_output/graph/` 目录（如不存在）。
2. 根据实际查询结果写入图谱证据文件：
   - 如有 GitNexus 查询结果 → 写入 `_output/graph/code-graph-evidence.yaml`。
   - 如有 Graphify 查询结果 → 写入 `_output/graph/business-graph-evidence.yaml`。
3. **始终**写入 `_output/graph/graph-sync-report.yaml`，即使两个图谱都不可用。
4. **始终**写入 `_output/graph/GRAPH_STATUS.md`，给用户展示本次图谱阶段状态和可视化入口。

`graph-sync-report.yaml` 格式：

```yaml
schema_version: "1.0"
generated_at: "<ISO-8601>"
project: "<project>"
repo_path: "<absolute-path>"
branch: "<git-branch>"
commit: "<git-commit-short>"
providers:
  gitnexus:
    available: true|false
    reason: "ok | tool_missing | index_missing"
    result_count: 0
  graphify:
    available: true|false
    reason: "ok | tool_missing | graph_missing"
    result_count: 0
fusion_summary:
  total_surfaces: 0
  gitnexus_primary: 0
  graphify_primary: 0
  both: 0
  neither: 0
```

`GRAPH_STATUS.md` 必须包含：

```markdown
# Graph Status

## Providers
| Provider | Status | Reason | Result Count | User Action |
|---|---|---|---:|---|
| GitNexus | available/unavailable | ok/index_missing/tool_missing/stale | 0 | `npx gitnexus analyze --incremental` |
| Graphify | available/unavailable | ok/graph_missing/tool_missing/stale | 0 | `/graphify . --mode deep` |

## Visual Pages
- Graphify visual page: `graphify-out/graph.html`
- Graphify report: `graphify-out/GRAPH_REPORT.md`
- GitNexus local index: `.gitnexus/`

## How This Run Used Graphs
- `01-codebase.yaml`: GitNexus / fallback scan
- `02-coding-rules.yaml`: Graphify / fallback docs+code scan
- `03-contracts.yaml`: GitNexus / fallback code scan
- `04-routing-playbooks.yaml`: Graphify + GitNexus / fallback scan
- `05-domain.yaml`: Graphify / fallback docs scan
```

如果 Graphify 的 `graphify-out/graph.html` 不存在，仍然写出预期路径，并提示用户运行 `/graphify . --mode deep` 后即可打开。不要只把状态藏在 YAML 里。

provider 不可用时必须记录原因（`tool_missing` 或 `index_missing` / `graph_missing`），不能假装跑过。

### 证据 ID 桥接规则

reference 使用两套独立的证据追踪机制，**不能互相替代**：

| 证据类型 | ID 格式 | 用途 | 写入字段 |
|---------|---------|------|---------|
| 审计证据 | `EV-001` | 源码、文档、人工确认等可审计的原始证据 | `evidence` |
| 代码图谱溯源 | `GEV-001` | GitNexus 的结构化发现（模块、符号、调用链） | `graph_evidence_refs` |
| 业务图谱溯源 | `GEV-B001` | Graphify 的业务语义发现（概念、规则、原理） | `graph_evidence_refs` |

核心规则：

- reference 模板中 `evidence` 字段只放 `EV-xxx` ID（可审计证据）。
- reference 模板中 `graph_evidence_refs` 字段只放 `GEV-xxx` / `GEV-Bxxx` ID（图谱溯源）。
- 关键 reference 条目（契约字段、枚举值、业务规则）必须至少有 EV 审计证据或明确标注豁免原因。
- 图谱结论需源码确认时，创建对应的 EV-xxx 条目，并在 GEV 条目的 `used_for` 中记录关联。
- GitNexus AST `confidence: high` 的结构发现（模块列表、符号定义、调用链）不需要额外 EV 确认。
- Graphify `EXTRACTED` 且有 `source locator` 的条目可直接标 `confidence: high`；`INFERRED` 默认 `medium`/`low`。

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
    graph_sources: []           # gitnexus, graphify，可为空
    graph_evidence_refs: []     # GEV-xxx / GEV-Bxxx 列表
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
- 如果图谱工具可用，至少一个 capability_surface 有非空 `graph_sources` 和 `graph_evidence_refs`。
- `_output/graph/graph-sync-report.yaml` 必须存在，且 `providers` 的 `reason` 字段已填写。
