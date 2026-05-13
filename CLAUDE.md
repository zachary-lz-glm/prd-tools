# PRD Tools - 项目约定

## 版本管理

两个插件使用统一版本号（lockstep versioning）。版本号存在于 5 个位置，必须保持一致：

| # | 文件 | 字段 |
|---|------|------|
| 1 | `VERSION` | 整个文件内容 |
| 2 | `plugins/reference/.claude-plugin/plugin.json` | `version` |
| 3 | `plugins/prd-distill/.claude-plugin/plugin.json` | `version` |
| 4 | `.claude-plugin/marketplace.json` | `plugins[0].version` |
| 5 | `.claude-plugin/marketplace.json` | `plugins[1].version` |

### 发版流程

```bash
# 一键发版（自动更新 5 处版本 + 生成 CHANGELOG + 提交 + 打 tag）
scripts/release.sh patch     # 2.4.1 → 2.4.2
scripts/release.sh minor     # 2.4.1 → 2.5.0
scripts/release.sh major     # 2.4.1 → 3.0.0
scripts/release.sh 2.5.0     # 显式指定

# 预览模式（不修改任何文件）
scripts/release.sh --dry-run patch
```

### Git Hook（一次性安装）

```bash
scripts/install-hooks.sh
```

安装后，每次 commit 会自动校验：版本一致性 + CHANGELOG 必须随 VERSION 更新 + tag 不重复。

## Commit 规范

使用 conventional commit 前缀：

| 前缀 | CHANGELOG 分类 | 说明 |
|------|---------------|------|
| `feat:` | Added | 新功能 |
| `fix:` | Fixed | 修复 |
| `refactor:` | Changed | 重构 |
| `docs:` | Changed | 文档 |
| `chore:` | Changed（root）/ 跳过（插件） | 杂项 |

发版脚本按前缀自动分类 CHANGELOG 条目。

## 文件边界

| 路径 | 归属 |
|------|------|
| `plugins/reference/` | reference 插件 |
| `plugins/prd-distill/` | prd-distill 插件 |
| `docs/adr/` | 架构决策记录 |
| `scripts/` | 项目工具脚本 |
| 其他根目录文件 | 全局共享 |

## CHANGELOG 结构

| 文件 | 职责 |
|------|------|
| `CHANGELOG.md` | 项目级版本迭代总览 |
| `plugins/*/CHANGELOG.md` | 各插件独立版本变更 |

## 反膨胀规则（防止 scripts/ 和规范无限增长）

历史教训：v2.16 → v2.18 迭代中 scripts/ 从 0 增长到 19 个（9666 行），其中 3 个是死代码（0 引用）。同时 schema/规范字段被静默删除，然后迭代者继续"加新字段/新文件"来修复，形成恶性循环。

### 新增文件前必须通过的 3 问

在 `scripts/`、`contracts/`、`steps/`、`references/` 下**新建任何文件前**，必须能回答：

1. **"为什么不能扩展现有文件？"** — 如果答案是"新文件更清爽"，不够。必须是"现有文件的边界明确不属于这件事"。
2. **"谁会调用它？"** — 有明确的 caller 才能建。stub / 占位符 / "未来可能用到" 不算。
3. **"3 个月后如果没人用会不会发现？"** — 如果不会，就别建。

任一问题答不上来，就修改现有文件。

### 硬性上限

| 目录 | 上限 | 超限时 |
|------|------|--------|
| `scripts/` | 20 个 .py 文件 | 先审 0 引用脚本是否可删 |
| `plugins/*/skills/*/references/` | 10 个 .md 文件 | 先合并近义文件 |
| `plugins/*/skills/*/steps/` | 6 个 .md 文件 | 先检查能否合并 step |
| `contracts/` | 每个 context artifact 对应 1 个 | 不再增加 |

超限必须在 commit 中显式说明理由。

### 禁止的模式

- ❌ **stub 脚本**：打印 "not implemented yet" 的占位脚本。写设计文档代替（`docs/xxx-design.md`）
- ❌ **shell 包装器**：10 行以内调用其他脚本的 wrapper。改成 Makefile target 或 README 命令
- ❌ **"为了复用"的新抽象**：只有 1 个调用者的通用库。内联回原处
- ❌ **并行规范文件**：同一主题在两个地方写规则（如 `reference-v4.md` 和 `output-contracts.md` 都写契约规则）。合并为单一权威源（SSOT）
- ❌ **防御性 validator**：为了"万一"检查而加的 check。必须有真实踩过的坑作为理由

### 死代码检查（每月或发版前）

```bash
# 扫所有 scripts/，找被引用次数 = 0 的
for s in scripts/*.py; do
  name=$(basename "$s" .py)
  refs=$(grep -rl "$name" plugins/ scripts/ .claude/ \
    --include="*.md" --include="*.py" --include="*.yaml" 2>/dev/null | grep -v "^$s" | wc -l)
  [ "$refs" = "0" ] && echo "0-ref: $s"
done
```

0 引用的脚本 30 天内仍未被引用 → 删除（可从 git 历史找回）。

### 给 AI 执行者的特别提醒

AI（包括 Claude、GLM 等）在执行任务时有强烈的"新增倾向"——新增比修改可见性高、责任小、易于展示。执行 prd-tools 任务时必须反向偏置：

- 收到修复任务 → 默认改现有文件
- 只有当 FIX 文档**明确列出**的新文件才能建
- 想加"辅助脚本 / 辅助 schema / 辅助规范"时 → 停下问用户
- 见到"应该加 gate 检查 X" → 先考虑加到现有 `*-quality-gate.py` 的函数
- 见到"应该有个配置 Y" → 先考虑加到现有 `project-profile.yaml` 的字段

**衡量好的修复**不是"加了多少文件"，而是"改了多少处、清理了多少处、删了多少死代码"。

## 团队级工具原则

prd-tools 是团队级通用工具，服务于多个项目和多种技术栈。以下约束适用于所有插件和脚本：

- **禁止硬编码**：不得针对特定项目（如 dive-bff、genos）的枚举名、字段名、API 路径等写死逻辑。所有数据必须从目标代码库动态提取。
- **AI 产出必须标注来源**：任何由 AI 推断（非直接从源码提取）的内容必须标注来源（如 `label_source: inferred`），让下游使用者区分"确定的"和"推断的"。
