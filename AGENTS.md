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

# [prd-tools] recent context, 2026-05-11 9:01pm GMT+8

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (7,767t read) | 0t work

### May 10, 2026
S345 补修 multi-repo branch benchmark 的 BFF target 对称性，为5个case创建targets/bff/目录并修改branch_case.py支持BFF层 (May 10 at 12:20 PM)
S346 Task #15: 修复 draft-oracle 排除 needs_review 文件进入 code_anchors（bundle 案例下归因不明确的文件应路由到 blockers/risk_notes） (May 10 at 12:33 PM)
S347 为 prd-tools 项目从 5 个 Simba Shift + DIVE 业务 PRD 生成正式 oracle.yaml 基准测试文件 (May 10 at 12:39 PM)
S348 构建 prd-tools 基准测试系统，完成 Task 22 验证和冒烟测试 (May 10 at 1:53 PM)
S349 prd-tools branch-backed multi-layer benchmark patch 发版全流程 (May 10 at 1:57 PM)
S350 全网收集最近AI大事，聚焦PRD-to-Code相关方向，整理出有收益的报告 (May 10 at 2:18 PM)
### May 11, 2026
S351 将 v2.0 分支代码合并到 main 分支并推送到远程仓库 (May 11 at 10:27 AM)
S353 为 prd-tools 新增 AI-friendly PRD Compiler MVP，将原始 PRD 编译为 13-section 规范化 AI-friendly PRD，作为 distill 流程的中间层 (May 11 at 10:58 AM)
S354 为 prd-tools 的 /reference 和 /prd-distill 插件添加硬完成门禁（Completion Gate），确保关键产出文件不被跳过 (May 11 at 2:31 PM)
2438 5:26p 🔵 用户请求仅为"PM"，信息不足
2439 " 🔵 prd-tools 项目统一产出目录结构
2440 5:27p 🔵 portal.html 功能边界定义
2441 " 🟣 reference 目录新增 portal.html 和 Evidence Index 索引层
2442 " ✅ prd-distill 插件目录结构 schema 同步更新
2443 5:28p 🔵 output-contracts.md 已包含 Evidence Index 但缺少 portal.html
2444 " ✅ output-contracts.md 同步新增 reference 下 portal.html 条目
2445 5:29p 🟣 prd-distill SKILL.md 新增 Final Completion Gate 硬约束
2446 " 🟣 workflow.md 新增步骤 8.6 Distill Completion Gate
2447 5:30p ✅ output-contracts.md 新增 Distill Completion Gate 章节
2448 " 🔵 final-quality-gate.py 脚本已存在
2449 " 🟣 新增 reference-quality-gate.py 脚本
2450 5:31p ✅ 任务 5 完成，任务 6 开始
2451 5:32p 🟣 新增 distill-quality-gate.py 脚本
2452 " 🔵 install.sh 存在，任务 7 可能涉及安装脚本更新
2453 " ✅ install.sh 新增两个质量门禁脚本的部署
2454 5:33p ✅ 任务 7 完成，任务 8 开始
2455 " 🔵 README.md 存在，任务 8 可能涉及文档更新
2456 " 🔵 README.md 结构概览
2457 5:34p ✅ README.md 新增质量门禁脚本和中文输出规则章节
2459 " ✅ 任务 8 完成，任务 9 开始
2461 5:35p ✅ 所有 Python 脚本编译检查和 lint 验证通过
2462 " 🔴 output-contracts.md 两个插件副本不同步
2463 " 🔵 安装验证确认两个插件的 Completion Gate 和中文规则已完整集成
2464 5:36p 🔴 reference-quality-gate.py 冒烟测试通过
2465 " 🔴 distill-quality-gate.py 冒烟测试通过
2466 5:37p 🔴 reference-quality-gate.py 全文件冒烟测试通过
2468 " 🔴 distill-quality-gate.py 全文件冒烟测试通过
2471 " 🔴 distill-quality-gate.py 缺失 ai_prd_req_id 场景验证通过
2473 5:38p 🔴 output-contracts.md 两插件副本仅空格对齐差异
2474 " 🔴 output-contracts.md 空格对齐差异确认并修复
2476 " 🔴 output-contracts.md 空格差异待统一
2478 5:40p 🔴 00-directory-structure.md 两插件副本也出现不同步
2479 " 🔴 同步检查在错误工作目录下执行导致误报 MISMATCH
2480 " 🔴 macOS cat 不支持 -A 选项导致 diff 调试失败
2481 5:41p 🔴 工作目录问题确认：文件路径在当前目录下不存在
2482 5:42p 🔴 output-contracts.md 空格对齐差异确认需修复
2483 " 🔴 output-contracts.md 空格差异精确定位
2484 " 🔴 output-contracts.md 空格对齐已修复，00-directory-structure.md 确认同步
2485 " 🔴 所有共享文件同步验证最终通过
2486 5:43p 🔴 00-directory-structure.md 二进制级别同步确认
2487 " ✅ 最终全面验证全部通过
2488 " 🟣 完整安装验证通过：5 个脚本部署、关键词搜索确认所有新功能集成
2489 5:44p ✅ 本次变更涉及 12 个文件的完整清单
2490 " ✅ prd-tools v2.16 Completion Gate 体系完整实现总结
2491 5:45p 🟣 prd-tools Completion Gate 体系全部任务完成
2492 5:46p ✅ Completion Gate 体系已提交：commit 632e4e7
2493 5:47p 🟣 新增 portal 模板和渲染脚本任务计划
2494 " 🟣 Portal 模板化改造：从 Claude 内联生成改为模板+脚本渲染
2495 5:48p 🟣 Portal 模板化改造：全面读取现有规范准备创建模板和渲染脚本
S355 Phase 2: Portal 模板+渲染脚本实现 — 将 portal.html 生成从 Claude 内联手写改为固定模板+Python 脚本渲染 (May 11 at 5:48 PM)
**Investigated**: 探索了 reference 和 distill 两个插件的 SKILL.md 文件，定位了所有需要更新的 portal/gate/render 相关行。Reference SKILL.md 164行，关键行：37(Completion Gate item 3)、140(执行步骤8)、154-155(参考文件表)。Distill SKILL.md 关键行：218(执行步骤16)、225(参考文件表)、240(完成消息)。

**Learned**: Phase 2 的核心文件已由主会话创建完成：2个portal模板HTML（reference+distill）、2个渲染Python脚本（render-reference-portal.py ~280行、render-distill-portal.py ~300行）、2个步骤文档已重写（step-05-portal.md 202→48行、step-04-portal.md 248→44行）。SKILL.md文件尚未更新以引用新的渲染脚本。两个插件共享文件同步约束（output-contracts.md等需byte-identical）。

**Completed**: ✅ 4个代码文件创建（2模板+2脚本）✅ 2个步骤文档重写 ✅ SKILL.md文件分析定位更新行。❌ SKILL.md更新未执行 ❌ output-contracts.md/install.sh/quality-gate/README更新未执行 ❌ 冒烟测试未运行

**Next Steps**: 1. 更新 reference SKILL.md：行37改为引用render-reference-portal.py命令，行140改为脚本渲染描述，行154-155更新参考文件表。2. 更新 distill SKILL.md：行218改为引用render-distill-portal.py命令，行225更新参考文件表，行240更新完成消息。3. 更新 output-contracts.md 添加模板和渲染脚本条目。4. 更新 install.sh 添加2个渲染脚本和2个模板的安装。5. 更新 quality-gate 脚本检查渲染脚本存在性。6. 更新 README.md。7. 运行冒烟测试。8. git commit + release.sh --auto
</claude-mem-context>