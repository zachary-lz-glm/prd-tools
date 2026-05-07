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


<claude-mem-context>
# Memory Context

# [prd-tools] recent context, 2026-05-07 3:01pm GMT+8

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (9,705t read) | 496,480t work | 98% savings

### May 7, 2026
S110 诊断 build-reference 工作流在 dive-bff 项目上 GitNexus 查询返回空结果的根因 (May 7 at 12:03 PM)
S111 诊断并定位 build-reference 在 dive-bff 项目上 GitNexus 查询返回空结果的完整根因 (May 7 at 12:30 PM)
S115 诊断并修复 install.sh 中 GitNexus 索引不生成 embeddings 导致语义搜索不可用的问题 (May 7 at 12:35 PM)
S116 简化 PRD-to-技术文档工作流，将多命令入口收敛为单一 /tech-doc 主命令 (May 7 at 12:44 PM)
S125 为prd-distill设计多Agent架构与上下文管理方案，评估收益后实施到skill文档和模板 (May 7 at 12:51 PM)
S126 研究 GitHub 热榜项目以提升 prd-tools 收益，并准备提交 prd-tools 入口精简重构的代码变更 (May 7 at 1:53 PM)
S132 用户请求提交 prd-tools 项目的最新改动 (May 7 at 1:59 PM)
808 2:06p ✅ 精简后的契约验证通过
810 2:07p 🔵 入口精简后遗留旧命令引用，版本号一致性验证通过
811 2:08p 🔵 全量扫描确认旧命令引用残留分布
812 " 🔵 调研 GitNexus exploring skill 的代码探索工作流
814 " 🔵 全面复查精简后核心文件状态
815 2:09p 🔵 精简后文件状态最终确认：所有变更已提交无残留
816 " ✅ v2.0 分支入口精简重构最终验证全部通过
817 2:13p 🔵 用户深入了解 prd-distill 蒸馏流程的工作机制
818 2:14p 🔵 prd-distill 完整蒸馏流程架构详解
819 2:15p 🔵 build-reference 与 prd-distill 的闭环关系
820 2:16p ✅ 为 build-reference 和 prd-distill 的 SKILL.md 新增 mermaid 流程图
821 2:18p ✅ 用户请求提交最新改动
822 " ✅ prd-tools 项目 v2.0 分支有待提交的 SKILL 文件修改
823 2:19p ✅ build-reference 和 prd-distill 的 SKILL.md 新增 mermaid 流程图
S133 改进 prd-tools 项目文档可读性：更新过时的第三方工具描述、为 skill 插件创建独立的人类可读 README、精简 SKILL.md 为纯机器指令 (May 7 at 2:20 PM)
824 2:21p 🔵 用户反馈流程图未说明第三方 GitHub 库的使用方式
825 2:26p ✅ 计划改进 prd-tools 项目文档可读性
826 2:27p 🔵 prd-tools 项目文档结构现状审查
827 2:28p 🔵 调研 Claude Code Skill 文档最佳实践
828 " ⚖️ 决定精简 SKILL.md 并为插件创建独立 README
829 2:29p ⚖️ 文档重构任务计划：5 个任务覆盖文档可读性改进全流程
830 " ✅ 开始调研外部工具最新状态
831 2:30p 🔵 调研 MarkItDown 最新能力和版本状态
832 2:31p 🔵 调研 Graphify 知识图谱工具最新状态
833 2:32p 🔵 确认本地安装的外部工具版本和能力
834 2:33p ✅ 外部工具调研任务完成
835 " 🔵 用户调研 GitHub 上热门的 harness 相关库以融合 prd-tools
836 2:34p 🔵 插件目录结构确认
837 " 🔵 GitHub 2026 热门开源测试自动化/Harness 工具调研结果
838 " 🔵 2026 CI/CD 工具格局调研：Harness 平台定位与竞争态势
839 2:35p 🟣 创建 build-reference 插件面向人类的 README.md
840 " 🔵 Harness Open Source（原 Gitness）开源平台详细调研
841 2:36p 🔵 AI Agent 框架与 PRD 自动化工具全景调研：发现多个可与 prd-tools 融合的候选
842 2:37p 🟣 两个插件 README 全部创建完成，开始精简 SKILL.md
843 " 🔵 Gitness（harness/harness）与 AI 编码工具的 2026 结合点
844 " 🔄 精简 build-reference SKILL.md 为纯机器指令
846 2:38p 🔄 精简 prd-distill SKILL.md 为纯机器指令
845 2:39p 🔵 Spec-to-Code 与 AI Agent 生态调研：发现 Claude Code 自治项目生成器
847 " 🔵 GitHub Spec Kit：Spec-Driven Development（SDD）运动的核心开源工具，与 prd-tools 高度互补
S134 调研 GitHub 上热门的 harness 相关库，寻找可与 prd-tools 深度融合的候选项目 (May 7 at 2:40 PM)
848 2:43p ✅ 文档重构 Git diff 确认
849 2:44p ✅ 文档重构提交完成
S135 改进 prd-tools 项目文档可读性：更新过时的第三方工具描述、为 skill 插件创建独立人类可读 README、精简 SKILL.md 为纯机器指令 (May 7 at 2:44 PM)
850 2:46p ⚖️ prd-tools 与 Spec Kit 深度融合战略方向
851 2:48p 🔵 prd-tools 项目约定与版本管理机制
852 2:49p ✅ 用户执行 Git Push 推送操作
855 " ✅ prd-tools v2.0 分支推送至远程仓库
853 2:50p 🔵 Spec Kit 技术调研：开源 spec-to-code 工具详细能力画像
854 " 🔵 Dify Knowledge Pipeline 与 Langflow Agent 编排能力调研
856 " 🔵 prd-tools v2.10.3 完整架构梳理：双插件闭环流水线
857 " 🔵 Spec Kit 三件套模板结构（spec→plan→tasks）与 prd-tools 融合映射
858 " 🔵 Dify Knowledge Base API 完整能力画像：文档管理 + 外部知识库 + RAG Pipeline
859 " 🔵 GitNexus 当前索引状态：3 个项目仓库已索引

Access 496k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>