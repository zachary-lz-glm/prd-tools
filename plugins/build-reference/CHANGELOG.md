# Changelog

All notable changes to the **build-reference** plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.11.1] - 2026-05-07

### Changed
- refactor: install.sh 三层职责拆分 (ADR-0008)

- refactor: install.sh 三层职责拆分 (ADR-0008)

### Changed
- refactor: _output/ + _reference/ 统一为 _prd-tools/，Spec Kit 对齐重组
- docs: 全面更新图谱集成文档 + 修复过时引用
- docs: 插件新增人类可读 README + SKILL.md 精简 + 外部工具描述更新
- docs: SKILL.md 添加 mermaid 一眼看懂流程图
- docs: simplify prd-tools entrypoints

### Added
- feat: reference 单仓治理 + graph-context 图谱中间层 + install 改进

### Fixed
- fix: 修复安装归档路径与输出口径漂移

- fix: 修复安装归档路径与输出口径漂移

### Added
- feat: v2.8 质量复盘 — 输出契约全面升级 + 契约校验自动化

- feat: v2.8 质量复盘 — 输出契约全面升级 + 契约校验自动化

### Changed
- (待补充)

- (待补充)

### Changed
- (待补充)

- (待补充)

### Fixed
- 6 个模板（01-05 + project-profile）增加 `graph_sources: []` 和 `graph_evidence_refs: []` 字段
- step-01-structure-scan 增加图谱证据文件创建指令、EV/GEV 证据 ID 桥接规则
- step-02-deep-analysis 增加前置图谱证据加载、per-phase 模板字段填充指令
- step-03-quality-gate 增加图谱证据检查（GEV 孤立引用、置信度校验、provider 一致性）
- SKILL.md 升级图谱增强 section（双证据字段说明、置信度映射表）

### Changed
- 所有 `graph_source` 单值改为 `graph_sources: []` 数组
- 文件级 `graph_providers` 改为结构化列表 `[{provider, graph, available}]`
- Graphify 置信度映射收紧：EXTRACTED 需有 source locator 才能标 high

## [2.5.0] - 2026-04-30

### Added
- **图谱证据层**：GitNexus（代码结构）+ Graphify（业务语义）双图谱集成
- reference-v4.md 新增「图谱证据层」章节：统一证据格式、provider 映射、置信度映射
- step-01-structure-scan.md 增加双图谱查询策略，自动回退 rg/glob
- step-02-deep-analysis.md 按数据源分工 6 阶段生成 reference
- `_output/graph/` 输出目录：code-graph-evidence.yaml、business-graph-evidence.yaml
- evidence kind 新增 `knowledge_graph`

### Changed
- workflow.md 新增三层架构说明和图谱增强阶段描述
- SKILL.md 增加「图谱增强」章节

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
