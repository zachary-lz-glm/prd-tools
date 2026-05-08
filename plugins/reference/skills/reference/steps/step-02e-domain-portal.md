# 步骤 2e：业务领域与导航

## 目标

生成 `_prd-tools/reference/05-domain.yaml`、`_prd-tools/reference/00-portal.md`，并按需更新 `project-profile.yaml`。

## 输入

- PRD / 技术方案 / QA 记录
- `_prd-tools/reference/01-codebase.yaml`（已生成，枚举 label 用于去重）
- `_prd-tools/reference/02-coding-rules.yaml`（已生成）
- `_prd-tools/reference/03-contracts.yaml`（已生成）
- `_prd-tools/reference/04-routing-playbooks.yaml`（已生成）
- `templates/05-domain.yaml`、`templates/00-portal.md`、`templates/project-profile.yaml`
- `references/schemas/00-directory-structure.md`（产出目录结构）

## 输出

- `_prd-tools/reference/05-domain.yaml`
- `_prd-tools/reference/00-portal.md`
- 更新 `_prd-tools/reference/project-profile.yaml`（如需要）

## 执行

### Part 1：业务领域

1. 从 PRD、技术方案、QA 记录中提取领域概念和隐式规则。
2. 生成 `05-domain.yaml`：业务域概览、术语（只收录非枚举概念）、隐式业务规则、历史决策。
3. 读取 `01-codebase.yaml` 中的枚举 label，如果 05-domain 的术语与枚举 label 重复，删除 05 中的重复条目，改为 `see_enum: "<EnumName>"`。

### Part 2：导航门户

4. 生成 `00-portal.md`：项目画像摘要、按场景阅读指南、文件地图、健康状态。
   - 文件地图覆盖 01~05 全部文件
   - 按场景给出阅读路径（如"新需求开发"、"BUG 排查"、"契约变更"）
5. 检查 `project-profile.yaml` 的 `capability_surfaces` 是否与 `modules-index.yaml` 一致，如不一致则更新。

## 边界规则

**05-domain 只放**：业务领域知识（术语、背景、隐式规则、决策日志）。

**不放**：
- 代码路径——那是 01-codebase 的事
- 编码规则——那是 02-coding-rules 的事
- 契约字段——那是 03-contracts 的事
- 枚举值列表——那是 01-codebase 的 enums 的事，术语重复时用 `see_enum` 引用

## Self-Check（生成后必须逐项验证）

- [ ] 术语与 01-codebase 的枚举 label 不重复（重复的用 see_enum 引用）
- [ ] 无代码路径、编码规则、契约字段
- [ ] 00-portal.md 覆盖所有 01-05 文件的导航
- [ ] project-profile.yaml 的 capability_surfaces 与 modules-index.yaml 一致
- [ ] 文件有 boundary 字段声明
