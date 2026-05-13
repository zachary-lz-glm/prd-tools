# Changelog

All notable changes to the **prd-distill** plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.19.0] - 2026-05-13

### Added
- feat(team-ref): [P1-4] introduce team common reference scaffolding (aggregation + inheritance)
- feat(scripts): [P1-1] add ingest-docx.py to replace ad-hoc XML parsing in Step 0

### Changed
- refactor(audit): self-audit postfix P2 — 13/13 fixes
- refactor(audit-p2): [P2-9] unify plan.md section count to 11 across docs
- refactor(audit-p2): [P2-7] materialize Phase 3.6 Critique Pass in workflow.md
- refactor(audit-p2): [P2-6] split duplicate Step 8.6 headings
- refactor(audit-p2): [P2-5] remove deprecated graph/ subtree from output-contracts

### Fixed
- fix(audit-p2): [P2-2] step-03-confirm.md inline HARD STOP instruction between report and plan
- fix(audit-p2): [P2-1] context-pack.md tiers anchors (must/should/optional) with visual markers
- fix(audit-p1): [P1-2] plan.md must-contain Checklist/Verify; report.md blocker 6-elements enforced
- fix(audit-p0): [P0-13] enforce schema field names for evidence/alignment_summary/readiness (anti-drift)
- fix(audit-p0): [P0-12] reference-update-suggestions.yaml restore 12-field schema + team candidate flag
- fix(audit-p0): [P0-11] strict H2 section structure for report.md (12) and plan.md (11)
- fix(audit-p0): [P0-9] plan.md §7/§9 enforce 3-layer validation matrix + contract table
- fix(audit-p0): [P0-7] layer-impact.yaml requires all 4 layers (frontend/bff/backend/external)
- fix(audit-p0): [P0-6] restore v2.16.0 full-stack contract suggestions (frontend/bff/backend grouping)
- fix(audit-p0): [P0-3] align schemas/03-context.md schema_version with contracts (all 2.0)
- fix(audit-p0): [P0-2] evidence.yaml as single source of truth, evidence-map.yaml read-only
- fix(audit-p0): [P0-1] enforce 13 english sections + ### REQ-XXX heading anchors in ai-friendly-prd
- fix(audit): self-audit postfix — P0 1/1, P1 8/8, audit report
- fix(audit): self-audit dryrun 29 findings — P0 6/6, P1 13/13, P2 10/10
- fix(audit-p0r2): [P0R2-12] document-structure.json exclusion_types taught to AI
- fix(audit-p0r2): [P0R2-11] gate failures suggest checking template/gate, not just artifact
- fix(audit-p0r2): [P0R2-7] docx ingestion uses python zipfile standard path
- fix(audit-p0r2): [P0R2-6] contract-delta requires meta + requirement_id + layer
- fix(audit-p0r2): [P0R2-5] IR evidence field unified as object with source_blocks/source_block_ids
- fix(audit-p0r2): [P0R2-4] media-analysis.yaml top-level key unified as `media`
- fix(audit-p0r2): [P0R2-3] evidence-map.yaml top-level key unified as `blocks`
- fix(audit-p0r2): [P0R2-2] gate accepts overall_score as score alias
- fix(audit-p0r2): [P0R2-1] ai-friendly-prd section format matches gate regex
- fix(audit-p1): [P1-10] document overall_score formula in output-contracts
- fix(audit-p1): [P1-8] tag Self-Check items as [M]achine / [H]uman
- fix(audit-p1): [P1-6] enforce IR ↔ ai-friendly-prd REQ id consistency
- fix(audit-p1): [P1-4] fix duplicate step number in step-01-parse.md
- fix(audit-p1): [P1-3] align source_blocks / source_block_ids semantics
- fix(audit-p1): [P1-2] SKILL.md lists distill-workflow-gate.py
- fix(audit-p1): [P1-1] normalize smart quotes in workflow.md yaml templates
- fix(audit-p0): [P0-5] code_scan must cover build/ for registry changes
- fix(audit-p0): [P0-4] align contract-delta.contract.yaml with real schema
- fix(audit-p0): [P0-2] remove duplicate Step 2.5/2.6 in workflow.md
- fix: 全盘修复 gate/workflow/command 一致性问题

- fix: 全盘修复 gate/workflow/command 一致性问题

### Added
- feat: Evidence Index 准确性提升 — 多行签名、跨文件边、增量更新、领域术语桥接

- feat: Evidence Index 准确性提升 — 多行签名、跨文件边、增量更新、领域术语桥接

### Added
- Artifact Contract MVP：validate-artifact.py + 4 个 contract 文件
- Context Budget：forbidden_outputs 字段，spec 阶段禁止 report.md/plan.md
- Two-Pass Critic：critique-template.md + workflow gate critique_status 检查
- distill-quality-gate.py 集成 artifact_contracts 检查

## [2.17.0] - 2026-05-12

### Added
- 顺序验证：step gate 检查 resume.next_step，不匹配时 exit 2
- --allow-rerun 逃生口
- current_stage 写入 workflow-state.yaml
- Step 8.1-confirm 通过时写入 human_checkpoints.report_review
- stage 边界 warning（spec 阶段存在 report.md 时警告）

## [2.16.3] - 2026-05-12

### Added
- 保真度优先：AI-friendly PRD 重新定位为索引层，requirement-ir 主输入回退到 document.md
- 新增 prd-coverage-gate.py（5 项保真度检查）
- 三段式工作流：/prd-distill 拆为 spec/report/plan 三段式命令
- Workflow State v2 + step gate --write-state
- Human workflow checkpoints（report review gate）

### Changed
- ADR-0011 整合为统一迭代计划
- requirement-ir schema 新增 primary_source 和 source_blocks 字段

- chore: release v2.16.1

### Added
- AI-friendly PRD Compiler：新增 `spec/ai-friendly-prd.md` 和 `context/prd-quality-report.yaml`。
- requirement-ir 对齐 AI-friendly PRD，新增 `ai_prd_req_id`、source、confirmation、planning eligibility 等字段。
- REQ → IMP → code_anchor 强绑定，增强 layer-impact、graph-context、report/plan 的可追溯性。
- distill 完成门禁脚本 `distill-quality-gate.py`，检查 AI-friendly PRD、IR、anchors、final gate。

### Fixed
- 强化 `/prd-distill` 完成门禁：关键产物缺失时不得宣称完成。

## [2.16.1] - 2026-05-10

### Added
- branch-backed multi-layer benchmark。
- Evidence Index benchmark harness。

## [2.16.0] - 2026-05-08

### Added
- prd-distill 支持 `.docx` 输入，提取图片并使用 Claude 原生多模态看图。

## [2.15.0] - 2026-05-08

### Changed
- 重写 README，强化对外可读性。

## [2.14.0] - 2026-05-08

### Changed
- 移除全部第三方依赖和辅助脚本，精简 distill 产出结构。

## [2.13.0] - 2026-05-08

### Changed
- 移除 GitNexus/Graphify 第三方图谱工具依赖，回归原生能力。

## [2.12.0] - 2026-05-08

### Added
- status dashboard MVP。

### Changed
- 精简 prd-tools guidance。
- 重命名 reference plugin internals。

### Fixed
- 统一 reference install workflow。

## [2.11.1] - 2026-05-07

### Changed
- install.sh 三层职责拆分（ADR-0008）。

## [2.11.0] - 2026-05-07

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

## [2.9.0] - 2026-05-06

### Added
- v2.8 质量复盘：输出契约全面升级 + 契约校验自动化。

## [2.8.0] - 2026-05-06

### Added
- prd-distill v2.8 质量复盘：修复图片 confidence、questions 合并、plan 升级技术方案、线索保留。

- **MarkItDown 集成**：用 microsoft/markitdown 替换手写 OOXML 解析和 pdftotext，作为文件转换后端
- **LLM Vision 图片分析**：自动检测环境变量，启用 markitdown-ocr 分析 PRD 流程图/截图/设计稿
- **智谱（bigmodel.cn）自动适配**：检测 ANTHROPIC_BASE_URL 含 bigmodel.cn 时自动转换 OpenAI 兼容端点
- 新增格式支持：pptx/xlsx/html/epub（原仅 docx/pdf/md/txt）
- PEP 723 依赖声明：ingest_prd.py 头部声明 MarkItDown 依赖

### Changed
- `ingest_prd.py` 完全重写（645行→~400行），保留原有输出格式不变
- SKILL.md / workflow.md 更新格式列表、图片分析说明
- report.md / plan.md / report.md §10 增加职责边界和长度约束

### Removed
- 手写 OOXML 解析代码（parse_docx 函数及底层 XML helpers）
- pdftotext 依赖（由 MarkItDown 内置 PDF 解析替代）

## [2.5.1] - 2026-05-01

### Fixed
- output-contracts.md 补全 layer-impact 的 `affected_symbols`/`business_constraints` 和 contract-delta 的 `graph_evidence_refs`
- SKILL.md 加图谱增强 section，workflow.md Step 3/4 加图谱引用

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
- 反馈回流：reference-update-suggestions → reference

## [1.1.0] - 2026-04-27

### Added
- 确定性事实校验（verified_by 轨迹）
- 按严重级别分级的质量门控

## [1.0.0] - 2026-04-27

### Added
- 初始版本发布
- 3 步工作流（解析和路由 → 分类 → 确认）
- Plugin manifest
