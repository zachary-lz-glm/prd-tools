# /build-reference — 领域知识构建工具

## 入口行为

当用户输入 `/build-reference` 时，按以下流程执行：

### 1. 检查项目状态

扫描当前目录，判断项目类型：

- 读取 `package.json`（如存在）检测项目特征
- 通过 Glob 扫描关键目录（`src/`、`app/`、`components/` 等）
- 读取 `_reference/00-index.md`（如存在）判断已有 reference 状态

### 2. 检查断点续传

读取 `_output/build-reference-progress.yaml`。

- 文件存在且包含未完成的阶段 → 使用 AskUserQuestion 询问用户：
  - **继续上次进度**（从上次中断的阶段恢复）
  - **重新开始**（清除旧进度，从 Phase 1 开始）
- 文件不存在或所有阶段已完成 → 全新开始

### 3. 模式选择

使用 AskUserQuestion 展示以下选项：

**选项 A: 全量构建** — 首次使用，从零构建完整 reference（7 个 YAML 文件）

选择后引导用户：
1. 确认项目路径（默认当前目录）
2. 确认项目类型：前端 / BFF / 后端（自动检测结果需用户确认）
3. 进入 3 阶段工作流（按 `workflow.md` 执行）

**选项 B: 增量更新** — 已有 reference，根据代码变更增量更新

选择后：
1. 检查 `_reference/` 目录完整性（7 个文件是否齐全）
2. 对比 `last_verified` 日期与 git log，识别变更范围
3. 只重新扫描变更影响的文件
4. 保留未变更部分，只更新受影响的章节
5. 更新 `last_verified` 日期
6. 检查 `_output/reference-health.yaml`（如存在）中的衰减告警

**选项 B2: 健康检查** — 快速检查 reference 是否过期（含深度 Lint）

选择后：
1. 读取 `_output/reference-health.yaml`（如不存在则创建）
2. 遍历所有 reference 文件中的文件路径，用 Glob 验证存在
3. 检查 `last_verified` 是否超过 14 天
4. 检查上次 `/prd-distill` 中报告的 `code_contradicts_reference` 数量
5. **深度 Lint 检查**：
   - **代码模式匹配**：Grep reference 中描述的代码模式（如注册 switch-case、模板函数签名）到源码，验证模式仍然匹配
   - **跨文件枚举一致性**：01-entities 的枚举值与 04-constraints 的枚举校验规则一致
   - **孤立条目检测**：05-mapping 的 inventory 中标记为 `implemented: true` 但从未被 prd_routing 引用的条目
   - **实体索引有效性**：00-index.md 实体索引中指向的文件和章节是否存在
6. 输出健康报告：
   ```
   Reference 健康状态：
   - 文件路径有效性：N/M 通过
   - 上次验证：X 天前
   - 蒸馏矛盾报告：X 次
   - 代码模式匹配：N/M 通过
   - 跨文件枚举一致性：✅ 一致 / ❌ 不一致（差异详情）
   - 孤立条目：N 个
   - 实体索引有效性：M/N 有效
   - 状态：✅ 健康 / ⚠️ 需更新 / ❌ 需重建
   ```

**选项 C: 质量检查** — 对已有 reference 做质量门控验证

选择后：
1. 读取所有 7 个 reference 文件
2. 执行 Phase 3 的三轮 Critic 检查
3. 输出质量报告 + 改进建议

**选项 D: 帮助** — 展示使用指南

展示以下内容：
- reference 7 文件结构说明（按关注点维度）
- YAML 规范要点
- 各层（前端/BFF/后端）的差异
- 示例 reference 文件路径

**选项 E: 反馈回流** — 从 `/prd-distill` 蒸馏结果中提取 reference 矛盾，人工确认后回流更新

选择后：
1. 扫描 `_output/distilled-*.md`，提取所有 `verification_source: code_contradicts_reference` 条目
2. 如未找到矛盾条目：提示"未检测到 reference 矛盾，无需回流"
3. 如找到矛盾条目：读取 `steps/step-04-feedback-ingest.md` 执行反馈回流流程
4. 输出 `_output/feedback-ingest-report.yaml`（回流报告）

### 4. 执行工作流

模式选择完成后：

- **全量构建** → 读取 `workflow.md` 并按阶段执行
- **增量更新** → 读取 `workflow.md` 跳到 Phase 2（只分析变更部分）
- **质量检查** → 读取 `steps/step-03-quality-gate.md` 执行
- **帮助** → 展示后重新回到模式选择
- **反馈回流** → 读取 `steps/step-04-feedback-ingest.md` 执行

## 输出目录结构

构建完成后，目标项目根目录下生成：

```
_reference/
├── 00-index.md              # 导航索引 + 实体索引
├── 01-entities.yaml         # 实体：枚举、核心类型、数据结构、注册信息
├── 02-architecture.yaml     # 结构：目录结构、注册机制、数据流、模块依赖
├── 03-conventions.yaml      # 规范：命名、代码模式（gold patterns）、反模式
├── 04-constraints.yaml      # 约束：白名单、校验规则、致命错误、检查清单
├── 05-mapping.yaml          # 映射：PRD 路由表、能力边界、字段映射、变更分类
└── 06-glossary.yaml         # 术语：业务术语表、同义词、工作量标准
```

## 文件索引

| 文件 | 职责 |
|------|------|
| `workflow.md` | 3 阶段工作流编排 |
| `steps/step-01-structure-scan.md` | Phase 1: 结构扫描 |
| `steps/step-02-deep-analysis.md` | Phase 2: 深度分析（按关注点维度产出 7 文件） |
| `steps/step-03-quality-gate.md` | Phase 3: 质量门控（含深度 Lint） |
| `steps/step-04-feedback-ingest.md` | 反馈回流（从 prd-distill 蒸馏结果回流更新 reference） |
