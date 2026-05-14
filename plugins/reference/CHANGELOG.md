# Changelog

All notable changes to the **reference** plugin are documented here.

## [2.19.4] - 2026-05-14

### Added
- feat: 上游接口文档支持 + PRD 项目相关性过滤

### Changed
- refactor: reference 阶段重编 Phase 1-6 + 步骤编号规范
- refactor: 工作流步骤重编 + report §4 需求映射优化
- refactor: 删除冗余 schemas/ 和 contracts/ 目录
- refactor: 瘦身 v2.0 — 砍门禁 + 拆团队模式 + 去聚合化 + 恢复 portal

### Fixed
- fix: 修复 quality-gate.py 运行时崩溃 + 清理孤立文件

- 团队聚合增加 index 同步步骤和 4 条硬约束（禁止推断内容、跨层规则过滤、producer 验证、同名术语合并），新增 endpoint_producer_unverified 冲突类型

## [2.19.0] - 2026-05-13

- 团队公共知识库聚合与继承（T/T2 模式）+ self-audit 全盘修复

## [2.18.1] - 2026-05-12

- Evidence Index 准确性提升（多行签名、跨文件边、增量更新）

## [2.17.0] - 2026-05-12

- Mode Selection Gate 脚本化 + 顺序验证 + --allow-rerun 逃生口

## [2.16.3] - 2026-05-12

- Workflow State v2 + step gate --write-state + Human checkpoints

## [2.16.1] - 2026-05-10

- 多层 benchmark + Evidence Index benchmark

## [2.15.0] - 2026-05-08

- 重写 README，强化对外可读性

## [2.14.0] - 2026-05-08

- 移除第三方依赖，精简产出结构

## [2.13.0] - 2026-05-08

- 移除 GitNexus/Graphify 依赖，回归原生能力

## [2.12.0] - 2026-05-08

- 状态面板 MVP + 安装流程统一

## [2.11.0] - 2026-05-07

- 输出目录统一为 _prd-tools/ + README + SKILL.md 流程图

## [2.10.0] - 2026-05-06

- 单仓治理 + graph-context 图谱中间层

## [2.9.0] - 2026-05-06

- 输出契约全面升级 + 契约校验自动化

## [2.5.1] - 2026-05-01

- 图谱融合端到端补齐（模板字段 + 步骤指令 + 证据检查）

## [2.5.0] - 2026-04-30

- 图谱证据层：GitNexus + Graphify 双图谱集成

## [2.4.1] - 2026-04-29

- 口径一致性修复（版本号/schema_version 统一）

## [2.4.0] - 2026-04-29

- output-contracts.md 完整定义 reference 产出模板

## [2.3.0] - 2026-04-29

- 能力面适配器替代路径优先规则

## [2.2.0] - 2026-04-29

- PRD 工程化解析（prd-ingest）+ 读取质量门禁

## [2.1.0] - 2026-04-28

- 能力面适配器 + 安装版本标记

## [2.0.0] - 2026-04-28

- Reference v3.1：10 文件结构 + 4 阶段工作流 + 反馈回流

## [1.1.0] - 2026-04-27

- 确定性事实校验 + 分级质量门控 + 幻觉检测

## [1.0.0] - 2026-04-27

- 初始版本：4 步工作流 + 安装脚本 + Plugin manifest
