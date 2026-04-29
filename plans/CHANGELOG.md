# PRD Tools 架构迭代日志

> 记录每个版本的架构决策、变更动机和影响范围。
> 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式 + [ADR](https://adr.github.io/) 编号体系。

## 目录结构说明

```text
plans/
├── CHANGELOG.md                # 你正在看这个：版本迭代日志
├── 0001-reference-SSOT优化.md   # ADR: reference 知识库去重
├── 0002-渐进式披露输出优化.md    # ADR: report/plan 可读性
├── 0003-演进路线图.md            # ADR: 4 个演进方向
└── 0004-口径一致性修复.md        # ADR: P0 口径清理
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

## [2.2.0] - 2026-04-28

### Added
- PRD 工程化解析（prd-ingest）：支持 .docx / .md / .txt / .pdf 的结构化读取
- PRD 读取质量门禁（extraction-quality.yaml）
- 文档说明优化

---

## 待开始

- **演进路线图**已规划 4 个方向，详见 [ADR-0003](0003-演进路线图.md)
  - Phase 1：能力面适配器优化（1-2 周）
  - Phase 2：多轮构建（2-4 周）
  - Phase 3：三方视角 Skill（4-8 周）
  - Phase 4：营销知识库（持续）
