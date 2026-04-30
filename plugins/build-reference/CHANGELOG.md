# Changelog

All notable changes to the **build-reference** plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.4.1] - 2026-04-29

### Fixed
- 8 个文件的版本号、schema_version、文件引用从 v2.2/v3.1 统一到 v2.4/v4.0
- step-00-context-enrichment.md 全面重写为 v4.0 文件映射
- step-01-structure-scan.md schema_version 修正为 4.0
- output-contracts.md 标题和 YAML 字段修正
- project-profile.yaml 模板 schema_version 修正
- plugin.json 移除非标准 changelog 数组，仅保留 version 字段

### Removed
- Codex 兼容代码（install.sh、SKILL.md、README.md）

## [2.4.0] - 2026-04-29

### Added
- output-contracts.md 完整定义 reference 产出模板和边界

### Changed
- Reference 结构从 10 文件精简到 6 文件（SSOT + Boundary 声明）
- 删除旧版 10 个模板，新建 6 个模板（00-portal.md ~ 05-domain.yaml）
- references/reference-v3.md → references/reference-v4.md

## [2.3.0] - 2026-04-29

### Changed
- 能力面适配器替代路径优先规则
- step-02-deep-analysis.md 增加去重检查步骤

## [2.2.0] - 2026-04-29

### Added
- PRD 工程化解析（prd-ingest）质量门禁联动
- 输出契约明确 prd-ingest 和 artifacts 的边界

### Changed
- SKILL.md 增加 PRD 读取规则和暂停条件

## [2.1.0] - 2026-04-28

### Added
- 能力面适配器替代路径优先规则
- 安装版本标记（`.prd-tools-version`）

### Changed
- Reference 默认视图瘦身：合并重复的输出文件
- 明确 `03-conventions` / `08-contracts` / `09-playbooks` 边界

### Fixed
- 安装脚本防止双层嵌套 skill 目录

## [2.0.0] - 2026-04-28

### Added
- Reference v3.1：10 文件结构
- 4 阶段工作流：上下文收集 → 结构扫描 → 深度分析 → 质量门控
- 反馈回流机制
- Golden sample 支持

## [1.1.0] - 2026-04-27

### Added
- 确定性事实校验（verified_by 轨迹）
- 按严重级别分级的质量门控（fatal / warning / info）
- 结构化幻觉检测

## [1.0.0] - 2026-04-27

### Added
- 初始版本发布
- 4 步工作流（结构扫描 → 深度分析 → 质量门控 → 反馈回流）
- 安装脚本和 Plugin manifest
