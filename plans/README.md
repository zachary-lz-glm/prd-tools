# Plans — 架构决策与迭代日志

这个目录记录 PRD Tools 的架构决策（ADR）和版本迭代历史。

## 怎么看

| 你想了解 | 先看 | 再看 |
|---------|------|------|
| 每个版本改了什么 | [CHANGELOG.md](CHANGELOG.md) | — |
| 为什么要这样改 | 对应编号的 ADR 文件 | — |
| 未来要做什么 | [0003-演进路线图.md](0003-演进路线图.md) | CHANGELOG 末尾"待开始" |

## 文件列表

| 文件 | 类型 | 内容 |
|------|------|------|
| [CHANGELOG.md](CHANGELOG.md) | 版本日志 | 每个版本的 Added / Changed / Fixed / Removed |
| [0001-reference-SSOT优化.md](0001-reference-SSOT优化.md) | ADR | Reference 10 文件 → 6 文件，SSOT 去重 |
| [0002-渐进式披露输出优化.md](0002-渐进式披露输出优化.md) | ADR | report/plan 可读性增强，Progressive Disclosure |
| [0003-演进路线图.md](0003-演进路线图.md) | ADR | 4 个演进方向的可行性分析和路线图 |
| [0004-口径一致性修复.md](0004-口径一致性修复.md) | ADR | P0 版本口径清理 + 输出边界约束 |

## ADR 格式

每个 ADR 包含 4 个固定章节（参考 [adr.github.io](https://adr.github.io/)）：

| 章节 | 回答什么 |
|------|---------|
| **Context** | 为什么要做这个决策？遇到了什么问题？ |
| **Decision** | 做了什么？具体改了什么？ |
| **Consequences** | 带来什么影响？收益和风险？ |
| **References** | 行业参考和外部依据 |

## 命名规则

```text
NNNN-中文简述.md
```

- 编号从 0001 递增，保持时间顺序
- 文件名用中文，方便团队理解
- 一个决策一个文件，不合并

## 写新的 ADR

新增决策时：

1. 复制最近一个 ADR 的格式
2. 编号递增
3. 填写 Context / Decision / Consequences / References
4. 在 CHANGELOG.md 对应版本条目中引用
