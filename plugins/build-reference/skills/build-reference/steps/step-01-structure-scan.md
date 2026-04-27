# step-01: 结构扫描（Phase 1）

## MANDATORY RULES

1. 只使用 Glob 和 Grep 工具扫描项目，不修改任何文件
2. 模块划分基于目录结构和文件依赖关系，不猜测业务含义
3. 所有文件路径必须是 Glob/Grep 实际找到的，不编造路径
4. 不确定归属的文件标 TODO，不强行归类
5. 扫描结果以 YAML 格式输出

## INPUT

| 输入 | 来源 | 格式 |
|------|------|------|
| 项目目录 | 用户指定或当前目录 | 文件系统路径 |
| 项目类型 | 自动检测 + 用户确认 | frontend / bff / backend |

## OUTPUT

| 输出 | 路径 | 格式 |
|------|------|------|
| 模块索引 | `_output/modules-index.yaml` | YAML |
| 进度更新 | `_output/build-reference-progress.yaml` | YAML |

### modules-index.yaml 结构

```yaml
version: "1.0"
project_type: frontend
project_path: "."
scan_at: "2026-04-24T10:00:00Z"
git_stats:
  total_files: N
  main_languages: [TypeScript, CSS]

modules:
  - name: "routing"
    description: "路由配置模块"
    key_files:
      - path: "src/App.tsx"
        role: "路由入口"
    five_questions:
      - "这组路由配置了哪些页面？"
      - "新增页面要改哪些文件？"
      - "路由懒加载是怎么做的？"
      - "路由之间有什么隐式依赖？"
      - "路由守卫/权限逻辑在哪？"
    status: pending

  - name: "components"
    description: "组件注册与渲染模块"
    key_files: [...]
    five_questions: [...]
    status: pending
```

## EXECUTION

### 执行步骤

1. **初始化**
   - 创建 `_output/` 目录
   - 创建 `_output/build-reference-progress.yaml`（phase_1: in_progress）
   - 初始化 `_reference/` 目录骨架（7 个空文件 + metadata 头）

2. **检测项目类型**
   - BFF 特征：`serverless.yml`、`config/template/render/`、`config/constant/campaignType.ts`
   - 前端特征：`src/components/FormField/`、`src/pages/`、`package.json` 含 React
   - 后端特征：`pom.xml`、`build.gradle`、`go.mod`、`src/main/java/`
   - 用 Glob 逐一检查特征文件
   - 向用户确认检测结果

3. **扫描目录结构**
   - Glob `**/*.{ts,tsx,js,jsx}` 获取源文件列表
   - 统计目录层级和文件分布
   - 识别入口文件（index.ts、app.tsx、main.ts 等）

4. **识别模块边界**
   - 按一级/二级目录划分候选模块
   - 每个模块找到关键入口文件
   - 为每个模块生成 5 个分析问题（Meta 五问框架）
   - 不确定归属的文件标 TODO

5. **生成模块索引**
   - 写入 `_output/modules-index.yaml`
   - 更新进度文件

## CONFIRMATION POINT

扫描完成后展示模块划分结果：

```
发现 N 个模块：
1. routing — 路由配置（X 个文件）
2. components — 组件注册（X 个文件）
3. store — 状态管理（X 个文件）
...
未归属文件：X 个（标记 TODO）
```

用户可以：
- 合并模块（两个模块合为一个）
- 拆分模块（一个模块拆为多个）
- 重命名模块
- 添加遗漏的模块
- 确认当前划分

确认完成后更新 `_output/modules-index.yaml`。

## VALIDATION

1. **路径有效性** — modules-index 中所有 key_files 路径实际存在
2. **覆盖完整** — 源文件总数的 90%+ 已归属到某个模块或标 TODO
3. **问题完整** — 每个模块有 5 个分析问题
4. **格式合规** — YAML 合法，符合 modules-index 结构

## NEXT STEP

确认完成 → 进入 [step-02-deep-analysis.md](./step-02-deep-analysis.md)
