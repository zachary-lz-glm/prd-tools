# PRD Tools 架构迭代日志

> 记录每个版本的架构决策、变更动机和影响范围。
> 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式 + [ADR](https://adr.github.io/) 编号体系。

## 目录结构说明

```text
plans/
├── CHANGELOG.md                 # 你正在看这个：版本迭代日志
├── 0001-reference-SSOT优化.md    # ADR: reference 知识库去重
├── 0002-渐进式披露输出优化.md     # ADR: report/plan 可读性
├── 0003-演进路线图.md             # ADR: 4 个演进方向
├── 0004-口径一致性修复.md         # ADR: P0 口径清理
└── README.md                    # 导航索引 + ADR 格式说明
```

**阅读顺序**：先看 CHANGELOG 了解全局 → 按编号看感兴趣的 ADR 详情。

---

## [2.4.1] - 2026-04-29

### Fixed
- **口径一致性修复**：8 个文件的版本号、schema_version、文件引用从 v2.2/v3.1 统一到 v2.4/v4.0（详见 [ADR-0004](0004-口径一致性修复.md)）
- report.md / plan.md / questions.md 增加职责边界和长度约束，防止输出膨胀

## [2.4.0] - 2026-04-29

### Added
- **渐进式披露输出**：report.md 从 6 章扩展到 9 章渐进式披露结构（30 秒决策 → 变更明细 → 字段清单 → 契约风险）（详见 [ADR-0002](0002-渐进式披露输出优化.md)）
- plan.md 增加 checklist 格式、文件行号、验证命令、参考实现
- output-contracts.md 完整定义 report.md 和 plan.md 模板

### Changed
- report.md 定位从"轻量摘要"升级为"决策文档"——一屏可读结论，按需展开细节
- plan.md 定位从"合并计划"升级为"可执行开发手册"

## [2.3.0] - 2026-04-29

### Changed
- **Reference 结构从 10 文件精简到 6 文件**，引入 SSOT + Boundary 声明 + 去重检查（详见 [ADR-0001](0001-reference-SSOT优化.md)）
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
- build-reference 4 阶段工作流：上下文收集 → 结构扫描 → 深度分析 → 质量门控
- prd-distill 3 步工作流：解析和路由 → 分类 → 确认
- 契约差异分析（contract-delta）：producer / consumer / alignment_status
- 反馈回流机制：prd-distill → reference-update-suggestions → build-reference 反馈回流
- Golden sample 支持

## [1.1.0] - 2026-04-27

### Added
- 确定性事实校验（verified_by 轨迹）
- 按严重级别分级的质量门控（fatal / warning / info）
- 结构化幻觉检测

## [1.0.0] - 2026-04-27

### Added
- **初始版本发布**
- build-reference：4 步工作流（结构扫描 → 深度分析 → 质量门控 → 反馈回流）
- prd-distill：3 步工作流（解析和路由 → 分类 → 确认）
- 安装脚本（install.sh）
- Plugin manifest（.claude-plugin/plugin.json）
- Marketplace manifest（.claude-plugin/marketplace.json）

---

## 待开始

- **演进路线图**已规划 4 个方向，详见 [ADR-0003](0003-演进路线图.md)
  - Phase 1：能力面适配器优化（1-2 周）
  - Phase 2：多轮构建（2-4 周）
  - Phase 3：三方视角 Skill（4-8 周）
  - Phase 4：营销知识库（持续）
