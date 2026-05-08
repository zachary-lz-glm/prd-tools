# ADR-0001：Reference 知识库 SSOT 优化（10 文件 → 6 文件）

| 字段 | 值 |
|------|---|
| 状态 | 已实施 |
| 版本 | v2.3.0 |
| 日期 | 2026-04-29 |
| 提交 | 9928c61 |
| Supersedes | v3.1 reference 结构 |

## Context（为什么做）

老板反馈 reference 生成的知识边界模糊、内容重叠严重。

根因分析：

1. 旧版 10 个文件混用 3 种分类维度（内容性质 / 关注点 / 使用场景），同一条知识平均出现 2-5 次
2. 模板字段语义重叠：`01-entities` 的字段信息和 `08-contracts` 的契约信息大量重复
3. 7 个模板缺少 boundary 声明，生成时无法判断"这条知识该放哪"

全网调研证实：行业共识是 **SSOT（Single Source of Truth）**，知识去重是 RAG / AI 知识库的最佳实践。

## Decision（做了什么）

**按"知识在开发生命周期中的角色"单一维度重新分类，10 文件 → 6 文件。**

```text
旧结构（v3.1, 10 文件）              新结构（v4.0, 6 文件）
├── 00-index.md                      ├── 00-portal.md（导航 + 场景阅读指南）
├── 01-entities.yaml                 ├── 01-codebase.yaml（静态清单）
├── 02-architecture.yaml      ─┐     ├── 02-coding-rules.yaml（编码规则）
├── 03-conventions.yaml       ─┼─→   ├── 03-contracts.yaml（契约·SSOT）
├── 04-constraints.yaml       ─┘     ├── 04-routing-playbooks.yaml（路由+打法）
├── 05-routing.yaml           ─┐     └── 05-domain.yaml（业务领域）
├── 06-glossary.yaml          ─┼─→
├── 07-business-context.yaml   ─┘
├── 08-contracts.yaml         ──→
└── 09-playbooks.yaml         ─┘
```

三个核心机制：

1. **Boundary 声明**：每个文件模板顶部声明"只放什么、不放什么"
2. **跨文件 ID 引用**：字段级信息只存在于 `03-contracts`，其他文件通过 `contract_ref` 引用
3. **去重检查**：step-02 末尾增加 5 条显式去重规则

## Consequences（影响）

### 收益

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 同一知识重复次数 | 2-5 次 | 1 次 | 80%+ |
| 总信息量 | ~88KB / 2200 行 | ~55KB / 1500 行 | -37% |
| AI context window 浪费 | ~20% | 低 | -20% token |
| 维护同步点 | 2-5 处 | 1 处 | 60%+ |

### 风险

- 去重更多靠 prompt 约束，尚未有 deterministic duplicate checker
- 兼容读取旧版 v3.1 文件，迁移由 reference 增量更新逐步完成

### 变更文件

- 重写 6 个模板（`templates/`）
- 新建 `references/reference-v4.md`
- 重写 `steps/step-02-deep-analysis.md`、`steps/step-03-quality-gate.md`
- 删除旧版 10 个模板 + `reference-v3.md`

## References

- [Diátaxis Framework](https://diataxis.fr/) — 文档按学习目标分类，启发了单一维度分类思路
- [SSOT（Single Source of Truth）](https://en.wikipedia.org/wiki/Single_source_of_truth) — 数据库设计、微服务契约管理中的成熟实践
- [DDD Bounded Context](https://martinfowler.com/bliki/BoundedContext.html) — 每个 reference 文件是一个明确边界的知识上下文
