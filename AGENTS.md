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

# [prd-tools] recent context, 2026-05-11 10:57am GMT+8

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (11,261t read) | 17,817t work | 37% savings

### May 10, 2026
S341 基于 PRD-分支映射创建 5 个 Branch-backed Benchmark Case，含 bundle 归因策略 (May 10 at 11:43 AM)
S342 设计BFF测试实施方案并为GLM编写提示词，同时讨论将测试扩展为前后端联合benchmark的架构 (May 10 at 11:58 AM)
S343 设计前后端联合benchmark架构，将BFF和前端仓库纳入统一的prd-tools评测体系 (May 10 at 12:00 PM)
S344 用户要求检查 prd-tools 项目中 branch-case 基准数据生成的质量，并完成全部验收检查 (May 10 at 12:00 PM)
S345 补修 multi-repo branch benchmark 的 BFF target 对称性，为5个case创建targets/bff/目录并修改branch_case.py支持BFF层 (May 10 at 12:20 PM)
S346 Task #15: 修复 draft-oracle 排除 needs_review 文件进入 code_anchors（bundle 案例下归因不明确的文件应路由到 blockers/risk_notes） (May 10 at 12:33 PM)
S347 为 prd-tools 项目从 5 个 Simba Shift + DIVE 业务 PRD 生成正式 oracle.yaml 基准测试文件 (May 10 at 12:39 PM)
2338 1:45p 🔵 prd-tools 基准测试体系：Simba Shift 三案例 oracle-draft 结构与 PRD 映射
2339 " 🔵 prd-tools 基准测试扩展至5个案例：新增可选择定制奖和运力线冲单奖
2340 1:46p 🔵 prd-tools 存在两套基准测试目录结构：cases/ 与 branch-cases/，oracle schema 成熟度不同
2341 " ✅ prd-tools 任务17状态变更为 in_progress
2342 " 🟣 在 benchmarks/cases/ 下为5个PRD案例创建正式目录结构
2343 1:48p ✅ prd-tools 使用 worktree 隔离环境进行基准案例开发
2344 1:49p 🟣 首个新案例正式 oracle.yaml 生成完成：simba-shift-rider-type
2345 " 🔵 prd-tools oracle 生成使用 worktree 隔离 + agent 并行写入模式
2346 1:50p 🟣 simba-shift-signin-award 正式 oracle.yaml 生成完成
2347 1:51p 🟣 simba-shift-order-scope 正式 oracle.yaml 生成完成，3/5 Simba案例已完成
2348 " 🟣 dive-customization-xtr-gas-benefits 正式 oracle.yaml 生成完成，4/5案例已完成
2349 " 🟣 全部5个新案例正式 oracle.yaml 生成完成，prd-tools 基准测试体系扩展至6个案例
2350 1:52p 🟣 prd-tools 基准测试5个新案例 oracle 全部验证通过，任务17完成
S348 构建 prd-tools 基准测试系统，完成 Task 22 验证和冒烟测试 (May 10 at 1:53 PM)
2351 1:54p 🟣 完成5个案例的预言（prophecy）生成
2352 " 🔵 prd-tools 项目 oracle 基准结构与评分系统
2353 " 🔵 5个新基准案例缺少 case.yaml 配置文件
2354 1:55p 🟣 新建任务20：为 benchmark_score.py 添加分层评分能力
2355 " 🟣 prd-tools 基准测试创建4个后续任务：case.yaml、分层评分、lint通过、冒烟测试
2356 1:56p 🔵 benchmark_score.py lint 逻辑要求每个案例必须有 case.yaml + expected/ 目录下4个文件
2357 " 🔵 5个基准案例对应3个不同的 Git 实现分支
2358 1:57p 🟣 5个案例的 case.yaml 全部创建完成，taskId 19 完成，开始 lint 修复
2359 " 🟣 benchmark_score.py run_lint() 支持双模式：oracle-based（新）和 expected-based（旧）
2360 " 🟣 benchmark_score.py 新增 code_anchor 分层评分：按 layer 统计 bff/frontend/unknown 准确率
S349 prd-tools branch-backed multi-layer benchmark patch 发版全流程 (May 10 at 1:57 PM)
2361 2:06p 🔴 修复 _parse_oracle 在段落切换时丢弃最后一个项目的问题
2362 " 🔵 benchmark 用例 simba-shift-signin-award 结构与图层评分配置
2363 2:15p ✅ prd-tools branch-backed multi-layer benchmark patch 发版
2364 2:16p ✅ prd-tools patch 发版四项校验全部通过
2365 " 🔵 prd-tools install.sh 安装流程审查
2367 " 🟣 prd-tools branch-backed multi-layer benchmark 提交成功
2366 " 🔵 prd-tools 仓库当前状态和脚本清单
2368 " 🔵 release.sh 执行后留下未提交的版本/CHANGELOG 改动
2370 2:17p 🔵 release.sh 已将版本更新至 2.16.1 但未完成 commit
2369 " 🔵 prd-tools 当前发版状态：HEAD 领先 v2.16.0 两个提交
2371 " 🟣 prd-tools v2.16.1 release commit 和 tag 创建成功
2372 " 🟣 prd-tools v2.16.1 发版完成并推送成功
### May 11, 2026
2373 10:19a 🔵 dive-bff 项目安装后初始状态探索
2378 10:24a 🔵 用户研究方向：PRD to Code AI领域调研
2379 " 🔵 PRD to Code领域2026年行业调研：核心趋势与关键资源
2380 10:25a 🔵 AI软件工程Agent生态：Devin/OpenHands/SWE-Agent三足鼎立
2381 " 🔵 PRD to Code 2026：PRD复兴运动与AI代理编码最佳实践
2383 10:26a 🔵 Anthropic Claude 4系列模型迭代路线：从Opus 4到Mythos
2384 " 🔵 Vibe Coding 2026：从流行词到主流开发范式的结构性转变
2385 " 🔵 OpenAI Codex产品线快速迭代：从GPT-5到GPT-5.5的Agent编码进化
S350 全网收集最近AI大事，聚焦PRD-to-Code相关方向，整理出有收益的报告 (May 11 at 10:27 AM)
2390 10:35a 🔵 AI行业调研：PRD-to-Code方向2026年5月全景分析
2391 " ⚖️ prd-tools战略定位决策：PRD-to-Code中间件定位
2393 10:42a 🔵 用户关注AI友好的PRD编写方法
2394 10:50a 🔵 prd-tools 项目进度查询
2395 10:53a ⚖️ 计划开发 PRD 转 AI-friendly PRD 的工具能力
2396 10:55a ✅ v2.0 分支合并到 main 分支（快进合并）
2397 10:56a 🔴 合并后出现 3 个文件的合并冲突

Access 18k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>