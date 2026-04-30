# Changelog

All notable changes to the **prd-distill** plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.5.0] - 2026-04-30

### Added
- **双维度影响分析**：step-02-classify.md 增加 GitNexus（代码爆炸半径）+ Graphify（业务关联）图谱增强
- layer-impact.yaml 新增 `affected_symbols`（GitNexus）和 `business_constraints`（Graphify）字段
- 图谱不可用时自动回退到原有分析流程

## [2.4.1] - 2026-04-29

### Fixed
- output-contracts.md 版本号和 schema_version 统一到 v2.4/v4.0
- report.md / plan.md / questions.md 增加职责边界和长度约束
- step-03-confirm.md 增加输出文件职责边界
- plugin.json 移除非标准 changelog 数组，仅保留 version 字段

### Removed
- Codex 兼容代码（SKILL.md）

## [2.4.0] - 2026-04-29

### Added
- report.md 渐进式披露 9 章结构（30 秒决策 → 变更明细 → 字段清单 → 契约风险）
- plan.md checklist 格式、文件行号、验证命令、参考实现
- output-contracts.md 完整定义 report.md 和 plan.md 模板

### Changed
- report.md 定位从"轻量摘要"升级为"决策文档"
- plan.md 定位从"合并计划"升级为"可执行开发手册"

## [2.3.0] - 2026-04-29

### Changed
- Reference 读取兼容 v4.0 六文件结构
- step-01-parse.md、step-02-classify.md 更新 reference 文件名引用

## [2.2.0] - 2026-04-29

### Added
- PRD 工程化解析（prd-ingest）：支持 .docx / .md / .txt / .pdf 结构化读取
- PRD 读取质量门禁（extraction-quality.yaml：pass / warn / block）
- 图片/复杂表格未确认时强制进入 warning / question / block
- prd-ingest 完整输出目录

### Changed
- 输出契约明确 prd-ingest 和 artifacts 的边界
- SKILL.md 增加 PRD 读取规则和暂停条件

## [2.1.0] - 2026-04-28

### Changed
- Layer Impact 改为能力面 surface 而非硬编码路径
- prd-distill 默认输出瘦身为 report / plan / questions，证据链迁入 artifacts/

## [2.0.0] - 2026-04-28

### Added
- 完整 7 步蒸馏工作流：PRD → Ingestion → Evidence → Requirement IR → Layer Impact → Contract Delta → Plan → Report
- 3 步工作流：解析和路由 → 分类 → 确认
- 契约差异分析（contract-delta）：producer / consumer / alignment_status
- 反馈回流：reference-update-suggestions → build-reference

## [1.1.0] - 2026-04-27

### Added
- 确定性事实校验（verified_by 轨迹）
- 按严重级别分级的质量门控

## [1.0.0] - 2026-04-27

### Added
- 初始版本发布
- 3 步工作流（解析和路由 → 分类 → 确认）
- Plugin manifest
