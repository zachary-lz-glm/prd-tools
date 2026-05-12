# Changelog

> 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式。架构决策详见 [docs/adr/](docs/adr/)。

---

## [2.18.0] - 2026-05-12

### Added
- Artifact Contract MVP：通用 validate-artifact.py + 4 个核心 contract（requirement-ir、ai-friendly-prd、layer-impact、contract-delta）
- Context Budget：distill-step-gate.py 每步 forbidden_outputs 字段，违反时 warning
- Two-Pass Critic：critique-template.md 自检模板 + distill-workflow-gate.py critique_status 检查
- distill-quality-gate.py 集成 artifact_contracts 检查项，输出 artifact-validation.yaml

## [2.17.0] - 2026-05-12

### Added
- Workflow State 成熟：顺序验证（step 必须匹配 resume.next_step）、--allow-rerun 逃生口
- current_stage 字段写入 workflow-state.yaml
- human_checkpoints 写入：distill report_review + reference mode_selection
- Mode Selection Gate 脚本化：reference Step 1+ 必须有 mode_selection approved
- --confirm-mode 参数：AI agent 在用户确认模式后调用写入 checkpoint
- stage 边界 warning：spec 阶段存在 report.md/plan.md 时警告

## [2.16.3] - 2026-05-12

### Added
- 保真度优先架构修正：AI-friendly PRD 重新定位为索引层，requirement-ir 主输入回退到 document.md，新增 prd-coverage-gate.py
- 三段式工作流骨架：/prd-distill 拆为 spec/report/plan 三段式命令
- Workflow State v2：step gate 新增 --write-state，共享 workflow_state.py 模块
- 前置步骤门禁脚本（distill-step-gate.py / reference-step-gate.py 升级）
- Human workflow checkpoints（report review gate + mode selection gate）

### Changed
- ADR-0011/0012/0013 整合为统一迭代计划（ADR-0011 重写）


## [2.16.2] - 2026-05-11

### Added
- feat: add AI-friendly PRD compiler pipeline
- feat: render stable portal pages

### Fixed
- fix: install portal templates
- fix: add hard completion gates


## [2.16.1] - 2026-05-10

### Added
- feat: add branch-backed multi-layer benchmark
- feat: add evidence index benchmark harness


## [2.16.0] - 2026-05-08

### Added
- feat: prd-distill 支持 .docx 输入，提取图片并使用 Claude 原生多模态看图


## [2.15.0] - 2026-05-08

### Added
- feat: prd-distill 新增 portal.html 可视化页面生成步骤
- feat: reference 新增 portal.html 可视化页面生成步骤

### Changed
- docs: 重写三个 README，强化对外可读性


## [2.14.0] - 2026-05-08

### Changed
- refactor: 移除全部第三方依赖和辅助脚本，精简 distill 产出结构


## [2.13.0] - 2026-05-08

### Changed
- refactor: 移除 GitNexus/Graphify 第三方图谱工具依赖，回归原生能力


## [2.12.0] - 2026-05-08

### Added
- feat: add status dashboard MVP

### Changed
- docs: fold output guide into readme
- docs: streamline prd tools guidance
- refactor: remove reference command alias
- refactor: rename reference plugin internals

### Fixed
- fix: unify reference install workflow


## [2.11.1] - 2026-05-07

### Changed
- i18n: install.sh / doctor.sh 用户可见输出改中文
- refactor: install.sh 三层职责拆分 (ADR-0008)

### Fixed
- fix: doctor.sh gitnexus 内网 registry 检测 + uv mirror 检测 + 下一步提示
- fix: doctor.sh $P 邻接全角字符触发 set -u + 修正 markitdown-ocr 安装命令
- fix: install.sh 代理检测改用 SOCKS 优先 + 移除安装时索引


## [2.11.0] - 2026-05-07

### Changed
- refactor: _output/ + _reference/ 统一为 _prd-tools/，Spec Kit 对齐重组
- docs: 全面更新图谱集成文档 + 修复过时引用
- docs: 插件新增人类可读 README + SKILL.md 精简 + 外部工具描述更新
- docs: SKILL.md 添加 mermaid 一眼看懂流程图
- docs: simplify prd-tools entrypoints

### Fixed
- fix: install.sh GitNexus 索引启用 embeddings + HuggingFace 不可达容错
- fix: install.sh VISION_KEY unbound variable 防护


## [2.10.3] - 2026-05-07

### Fixed
- fix: post-commit 改为询问发版 + install.sh API Key 交互优化


## [2.10.2] - 2026-05-07

### Fixed
- fix: install.sh 安装后输出清晰的必做清单


## [2.10.1] - 2026-05-07

### Fixed
- fix: install.sh npx 调 gitnexus 时绕过公司内网 npm registry


## [2.10.0] - 2026-05-06

### Added
- feat: reference 单仓治理 + graph-context 图谱中间层 + install 改进

### Fixed
- fix: 修复安装归档路径与输出口径漂移


## [2.9.0] - 2026-05-06

### Added
- feat: v2.8 质量复盘 — 输出契约全面升级 + 契约校验自动化


## [2.8.0] - 2026-05-06

### Added
- feat: prd-distill v2.8 质量复盘 — 修复图片confidence + questions合并 + plan升级技术方案 + 线索保留

### Changed
- docs: README 同步 v2.7 — MarkItDown/外部工具/安装向导/自动发版


## [2.7.0] - 2026-05-06

### Added
- feat: 版本迭代自动化 — release.sh --auto + post-commit hook 自动发版


## [2.6.0] - 2026-05-04

### Added
- **MarkItDown 集成**：用 microsoft/markitdown 替换手写 OOXML 解析和 pdftotext，作为 prd-ingest 的文件转换后端
- **LLM Vision 图片分析**：自动检测环境变量（OPENAI_API_KEY 或智谱 ANTHROPIC_AUTH_TOKEN），启用 markitdown-ocr 插件分析 PRD 中的流程图、截图、设计稿内容
- **智谱（bigmodel.cn）自动适配**：检测到 ANTHROPIC_BASE_URL 含 bigmodel.cn 时，自动转换为 OpenAI 兼容端点（glm-4v-flash）
- **新增格式支持**：pptx/xlsx/html/epub（原仅 docx/pdf/md/txt）
- **install.sh 完全重写**（~40 行 → 395 行 7 步向导）：自动代理检测、uv 安装、MarkItDown+OCR、GitNexus CLI 安装+自动索引、Graphify MCP、Claude Code MCP 配置、安装状态汇总
- PEP 723 依赖声明：Graphify 和 MarkItDown 的脚本头部声明独立依赖，无需手动 pip install

### Changed
- `ingest_prd.py` 完全重写（645行→~400行），保留原有 prd-ingest 输出格式不变
- SKILL.md / workflow.md 更新格式列表、图片分析说明、LLM Vision 环境变量配置

### Removed
- 手写 OOXML 解析代码（parse_docx 函数及底层 XML helpers）
- pdftotext 依赖（由 MarkItDown 内置 PDF 解析替代）

## [2.5.1] - 2026-05-01

### Fixed
- **图谱融合端到端补齐**：修复 v2.5.0 图谱证据层规范完整但实现断裂的问题（详见 [ADR-0006](docs/adr/0006-图谱融合与知识库架构.md)）
- 6 个模板（01-05 + project-profile）增加 `graph_sources: []` 和 `graph_evidence_refs: []` 字段，AI 填模板时能产出图谱数据
- step-01-structure-scan 增加图谱证据文件创建指令（必执行）、EV/GEV 证据 ID 桥接规则
- step-02-deep-analysis 增加前置图谱证据加载、per-phase 模板字段填充指令
- step-03-quality-gate 增加图谱证据检查（GEV 孤立引用、置信度校验、provider 一致性）
- reference SKILL.md 升级图谱增强 section（双证据字段说明、置信度映射表）
- prd-distill output-contracts.md 补全 layer-impact 的 `affected_symbols`/`business_constraints`（放 impact 条目内）和 contract-delta 的 `graph_evidence_refs`
- prd-distill SKILL.md 加图谱增强 section，workflow.md Step 3/4 加图谱引用
- `graph-sync-report.yaml` 必须始终产出，记录 provider 可用状态和不可用原因

### Changed
- 所有 `graph_source` 单值改为 `graph_sources: []` 数组（支持多 provider 交汇）
- 文件级 `graph_providers` 改为结构化列表 `[{provider, graph, available}]`
- Graphify 置信度映射收紧：EXTRACTED 需有 source locator 才能标 high

---

## [2.5.0] - 2026-04-30

### Added
- **图谱证据层（Graph Evidence）**：GitNexus + Graphify 双图谱集成，作为 reference 的结构化证据源
- reference-v4.md 新增「图谱证据层」章节：统一图谱证据格式 `graph_evidence`、provider 映射、置信度映射规则
- reference 文件按数据源分工：01/03 ← GitNexus（代码维度），02/04/05 ← Graphify（业务维度）
- step-01-structure-scan.md 增加双图谱查询策略（代码层 GitNexus + 业务层 Graphify），自动回退 rg/glob
- step-02-deep-analysis.md 按数据源分 6 阶段生成 reference，图谱不可用时回退到原有流程
- prd-distill step-02-classify.md 增加双维度影响分析（代码影响 GitNexus + 业务影响 Graphify）
- `_output/graph/` 目录：business-graph-evidence.yaml、code-graph-evidence.yaml
- evidence kind 新增 `knowledge_graph`

### Changed
- workflow.md 新增三层架构说明：Graphify（业务维度）+ GitNexus（代码维度）+ prd-tools（治理维度）
- SKILL.md 增加「图谱增强」章节和核心原则说明

## [2.4.1] - 2026-04-29

### Fixed
- **口径一致性修复**：8 个文件的版本号、schema_version、文件引用从 v2.2/v3.1 统一到 v2.4/v4.0（详见 [ADR-0004](docs/adr/0004-口径一致性修复.md)）
- report.md / plan.md / questions.md 增加职责边界和长度约束，防止输出膨胀

## [2.4.0] - 2026-04-29

### Added
- **渐进式披露输出**：report.md 从 6 章扩展到 9 章渐进式披露结构（30 秒决策 → 变更明细 → 字段清单 → 契约风险）（详见 [ADR-0002](docs/adr/0002-渐进式披露输出优化.md)）
- plan.md 增加 checklist 格式、文件行号、验证命令、参考实现
- output-contracts.md 完整定义 report.md 和 plan.md 模板

### Changed
- report.md 定位从"轻量摘要"升级为"决策文档"——一屏可读结论，按需展开细节
- plan.md 定位从"合并计划"升级为"可执行开发手册"

## [2.3.0] - 2026-04-29

### Changed
- **Reference 结构从 10 文件精简到 6 文件**，引入 SSOT + Boundary 声明 + 去重检查（详见 [ADR-0001](docs/adr/0001-reference-SSOT优化.md)）
- 分类维度从"内容性质/关注点/使用场景"三维度统一为"知识在开发生命周期中的角色"
- 删除旧版 10 个模板 + reference-v3.md，新建 6 个模板 + reference-v4.md

### Removed
- `templates/00-index.md`、`01-entities.yaml`、`02-architecture.yaml`、`03-conventions.yaml`、`04-constraints.yaml`、`05-routing.yaml`、`06-glossary.yaml`、`07-business-context.yaml`、`08-contracts.yaml`、`09-playbooks.yaml`
- `references/reference-v3.md`

## [2.2.0] - 2026-04-29

### Added
- **PRD 工程化解析（prd-ingest）**：支持 .docx / .md / .txt / .pdf 的结构化读取
- PRD 读取质量门禁（extraction-quality.yaml：pass / warn / block）
- 图片/复杂表格未确认时强制进入 warning / question / block
- prd-ingest 完整输出：source-manifest、document.md、document-structure.json、evidence-map、media/、tables/、extraction-quality、conversion-warnings

### Changed
- 输出契约明确 prd-ingest 和 artifacts 的边界
- SKILL.md 增加 PRD 读取规则和暂停条件

## [2.1.0] - 2026-04-28

### Added
- 能力面适配器替代路径优先规则，前端/BFF/后端各自有独立能力面定义
- 安装版本标记（`.prd-tools-version`）

### Changed
- Reference 默认视图瘦身：合并重复的输出文件
- 明确 `03-conventions` / `08-contracts` / `09-playbooks` 边界
- prd-distill 默认输出瘦身为 report / plan / questions，证据链迁入 artifacts/
- Layer Impact 改为能力面 surface 而非硬编码路径

### Fixed
- 安装脚本防止双层嵌套 skill 目录

## [2.0.0] - 2026-04-28

### Added
- **完整 7 步蒸馏工作流**：PRD → Ingestion → Evidence → Requirement IR → Layer Impact → Contract Delta → Plan → Report
- Reference v3.1：10 文件结构（entities / architecture / conventions / constraints / routing / glossary / business-context / contracts / playbooks）
- reference 4 阶段工作流：上下文收集 → 结构扫描 → 深度分析 → 质量门控
- prd-distill 3 步工作流：解析和路由 → 分类 → 确认
- 契约差异分析（contract-delta）：producer / consumer / alignment_status
- 反馈回流机制：prd-distill → reference-update-suggestions → reference
- Golden sample 支持

## [1.1.0] - 2026-04-27

### Added
- 确定性事实校验（verified_by 轨迹）
- 按严重级别分级的质量门控（fatal / warning / info）
- 结构化幻觉检测

## [1.0.0] - 2026-04-27

### Added
- **初始版本发布**
- reference：4 步工作流（结构扫描 → 深度分析 → 质量门控 → 反馈回流）
- prd-distill：3 步工作流（解析和路由 → 分类 → 确认）
- 安装脚本（install.sh）
- Plugin manifest（.claude-plugin/plugin.json）
- Marketplace manifest（.claude-plugin/marketplace.json）

---

## 待开始

- **演进路线图**已规划 4 个方向，详见 [ADR-0003](docs/adr/0003-演进路线图.md)
  - Phase 1：能力面适配器优化（1-2 周）
  - Phase 2：多轮构建（2-4 周）
  - Phase 3：三方视角 Skill（4-8 周）
  - Phase 4：营销知识库（持续）
