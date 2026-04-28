# 步骤 1：结构扫描

## 目标

创建 `_output/modules-index.yaml`，记录项目层级、模块、关键文件、入口点、潜在契约面和证据。

## 输入

- 当前项目路径或用户提供的路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- `references/layer-adapters.md`。

## 执行

1. 根据代码形态判断层级；不确定时让用户确认。
2. 加载对应适配器的扫描根目录。
3. 使用限定范围的 `rg`/glob，不扫描兄弟项目。
4. 排除依赖、构建产物、测试、mock、fixture、生成物、`_reference`、`_output` 和 `.git`。
5. 识别模块、关键文件、入口点、注册点、数据流线索和潜在契约面。

## 输出

```yaml
version: "3.0"
project: ""
layer: "frontend | bff | backend | multi-layer"
adapter: "frontend | bff | backend"
scan_at: ""
modules:
  - id: ""
    path: ""
    responsibilities: []
    key_files: []
    entrypoints: []
    likely_contracts: []
    evidence: []
unclassified_files: []
```

## 校验

- 所有关键文件都存在。
- 当前层适配器的核心扫描根目录已检查。
- 无法归类的文件要列入 `unclassified_files`，不要猜测归属。
