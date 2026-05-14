# reference

> 构建项目知识库 `_prd-tools/reference/`，把源码结构、业务术语、跨层契约、开发套路沉淀为 PRD-to-code 可复用的长期记忆。

## 快速开始

在 Claude Code 中进入目标项目，运行：

```
/reference
```

首次使用自动引导：收集历史 PRD，然后全量构建。之后可按需增量更新、健康检查或反馈回流。

## 产出物

构建完成后在项目根目录生成 `_prd-tools/reference/`，包含 6 个文件：

| 文件 | 内容 |
|------|------|
| `project-profile.yaml` | 项目画像：技术栈、入口、能力面 |
| `01-codebase.yaml` | 代码库清单：目录、模块、符号、数据流 |
| `02-coding-rules.yaml` | 编码规则：设计规范 + 踩坑经验 |
| `03-contracts.yaml` | 跨层契约：API endpoint、schema、字段定义 |
| `04-routing-playbooks.yaml` | PRD 路由信号 + 场景打法 + QA 矩阵 |
| `05-domain.yaml` | 业务领域：术语、背景、隐式规则 |

构建过程中产生的中间报告（扫描快照、健康检查、质量门控等）存放在 `_prd-tools/build/`。

**与 prd-distill 的关系：** reference 是可选的，但有了它 prd-distill 的输出质量会显著提升。

## 工作模式

| 模式 | 说明 | 触发条件 |
|------|------|---------|
| **F** 上下文收集 | 收集历史 PRD、技术方案、分支 diff | 首次接入 |
| **A** 全量构建 | 从零构建整个知识库 | 首次或需要重建 |
| **B** 增量更新 | 只更新受 git diff 影响的部分 | 源码或契约变化后 |
| **B2** 健康检查 | 检查是否过期、缺证据、边界混乱 | 怀疑知识库过期时 |
| **C** 质量门控 | 证据追溯、契约闭环、幻觉风险检查 | 上线前质量确认 |
| **E** 反馈回流 | 从 prd-distill 输出回收新知识 | PRD 交付完成后 |
| **T** 团队收集 | 原样收集各成员仓 reference 到 `references/{repo}/` | 团队仓 (`layer: team-common`) |

/reference 进入时必须先做模式选择（Mode Selection Gate），不允许默认全自动跑。

## 什么时候用

- **团队第一次接入 PRD Tools** — Mode F，然后 Mode A
- **项目结构、接口或业务规则大改** — Mode B 或 Mode A
- **PRD 交付后想沉淀经验** — Mode E
- **怀疑知识库过期或有幻觉** — 先 Mode B2，再 Mode C
- **多团队共享领域知识** — 团队仓 Mode T 收集各成员仓 reference 原样副本

**不适合的场景：** 只是解释代码、直接改代码、没有源码也没有上下文。

## 首次接入步骤

1. **准备材料** — 1-3 个历史 PRD、技术方案和对应分支 diff
2. **构建知识库** — `/reference` → Mode F（收集上下文）→ Mode A（全量构建）
3. **验证质量** — 运行 Mode B2（健康检查）+ Mode C（质量门控）

## 外部依赖

无。reference 使用原生 `rg`/`glob` + 文件读取构建知识库，不需要安装额外工具。

## 常见问题

**Q: `_prd-tools/reference/` 要提交到 git 吗？**
A: 建议 `.gitignore` 排除。这是本地生成的知识库，每个开发者自行维护。

**Q: 支持哪些项目类型？**
A: 前端、BFF、后端都支持。通过能力面适配器自动识别项目层级和结构。

**Q: 多仓项目怎么办？**
A: 单仓维护：每个仓独立维护自己的 `_prd-tools/reference/`，跨仓契约标记为待确认。多团队协作：使用团队模式——在独立的团队仓执行 Mode T 收集各成员仓 reference 到 `references/{repo}/`，PRD 蒸馏时按需读取。
