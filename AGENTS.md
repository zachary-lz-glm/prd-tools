# PRD Tools - 项目约定

## 版本管理

两个插件使用统一版本号（lockstep versioning）。版本号存在于 5 个位置，必须保持一致：

| # | 文件 | 字段 |
|---|------|------|
| 1 | `VERSION` | 整个文件内容 |
| 2 | `plugins/build-reference/.claude-plugin/plugin.json` | `version` |
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
| `plugins/build-reference/` | build-reference 插件 |
| `plugins/prd-distill/` | prd-distill 插件 |
| `docs/adr/` | 架构决策记录 |
| `scripts/` | 项目工具脚本 |
| 其他根目录文件 | 全局共享 |

## CHANGELOG 结构

| 文件 | 职责 |
|------|------|
| `CHANGELOG.md` | 项目级版本迭代总览 |
| `plugins/*/CHANGELOG.md` | 各插件独立版本变更 |

