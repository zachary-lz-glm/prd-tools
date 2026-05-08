# Architecture Decision Records

记录 PRD Tools 的架构决策（ADR）。参考 [adr.github.io](https://adr.github.io/)。

## 怎么看

| 你想了解 | 先看 | 再看 |
|---------|------|------|
| 每个版本改了什么 | [CHANGELOG.md](../../CHANGELOG.md) | 各插件 `CHANGELOG.md` |
| 为什么要这样改 | 对应编号的 ADR 文件 | — |
| 未来要做什么 | [0003-演进路线图](0003-演进路线图.md) | CHANGELOG 末尾"待开始" |

## 文件列表

| 文件 | 内容 |
|------|------|
| [0001-reference-SSOT优化](0001-reference-SSOT优化.md) | Reference 10 文件 → 6 文件，SSOT 去重 |
| [0002-渐进式披露输出优化](0002-渐进式披露输出优化.md) | report/plan 可读性增强，Progressive Disclosure |
| [0003-演进路线图](0003-演进路线图.md) | 4 个演进方向的可行性分析和路线图 |
| [0004-口径一致性修复](0004-口径一致性修复.md) | P0 版本口径清理 + 输出边界约束 |
| [0005-Agent-Skills融合落地方案](0005-Agent-Skills融合落地方案.md) | Agent Skills 架构、Slash 命令、Persona、Hook 规划 |
| [0006-图谱融合与知识库架构](0006-图谱融合与知识库架构.md) | GitNexus + Graphify 双图谱融合和跨项目知识库规划 |
| [0008-安装脚本职责拆分](0008-安装脚本职责拆分.md) | install.sh 拆为 install / doctor / 运行时自检三层 |
| [0009-PRD Tools 产品化 MVP 落地计划](0009-PRD-Tools-3.0产品化落地计划.md) | 原 3.0 计划收敛到 v2.0：readiness、status dashboard、评测和后续 MCP 路线 |

## ADR 格式

每个 ADR 包含 4 个固定章节：

| 章节 | 回答什么 |
|------|---------|
| **Context** | 为什么要做这个决策？遇到了什么问题？ |
| **Decision** | 做了什么？具体改了什么？ |
| **Consequences** | 带来什么影响？收益和风险？ |
| **References** | 行业参考和外部依据 |

## 写新的 ADR

1. 编号递增，文件名格式 `NNNN-中文简述.md`
2. 填写 Context / Decision / Consequences / References
3. 在本 README 文件列表中添加条目
4. 在根目录 `CHANGELOG.md` 对应版本条目中引用
