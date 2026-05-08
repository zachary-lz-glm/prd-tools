# 步骤 1：结构扫描

## 目标

创建 `_prd-tools/build/modules-index.yaml`，记录项目层级、能力面、关键文件、入口点、潜在契约面和证据。

## 输入

- 当前项目路径或用户提供的路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- `references/layer-adapters.md`。

## 执行

### 1. 项目文件扫描

1. 使用 `rg` / glob 扫描项目目录，范围限定在当前项目，不跨项目搜索。
2. 排除 `node_modules`、`dist`、`build`、`coverage`、测试、mock、fixture、生成物、`_prd-tools`、`.git`。
3. 识别关键配置文件（`package.json`、`tsconfig.json`、`Dockerfile` 等）判断技术栈。
4. 读取文件前先确认路径存在。

### 2. 层级判断与适配器加载

5. 根据代码形态判断层级；不确定时让用户确认。
6. 加载对应能力面适配器（`references/layer-adapters.md`），路径只作为候选。

### 3. 能力面识别

7. 识别能力面、关键文件、入口点、注册点、数据流线索和潜在契约面。
8. 结论必须来自源码、配置、类型定义、注册点、调用链、测试或负向搜索。

### 4. 输出生成

9. 生成 `_prd-tools/build/modules-index.yaml`。
10. 同时沉淀 `_prd-tools/reference/project-profile.yaml` 的初始版本。

## 输出

```yaml
schema_version: "4.0"
tool_version: "<tool-version>"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
scan_at: ""
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
unclassified_files: []
```

## 校验

- 所有关键文件都存在。
- 当前层适配器的核心能力面已检查。
- 无法归类的文件要列入 `unclassified_files`，不要猜测归属。
