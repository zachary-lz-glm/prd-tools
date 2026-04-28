# 外部工程化实践

这些实践用于支撑设计判断，不是要照搬成僵硬流程。

## 规格驱动产物

Kiro specs 把功能工作拆成需求、设计、任务，并包含验收标准、架构/设计文档和可跟踪任务。这支持我们保留 Requirement IR、Layer Impact、Contract Delta 等可追踪 artifacts，同时默认给用户轻量 report/plan/questions。来源：[Kiro Specs](https://kiro.dev/docs/specs/)。

Kiro steering 把长期项目知识放到 workspace markdown 文件中，并强调文件聚焦、示例、安全和定期维护。这支持 reference v3.1 作为项目记忆，而不是每次对话临时拼提示词。来源：[Kiro Steering](https://kiro.dev/docs/steering/)。

## 简洁的 Agent 工作流

Anthropic 建议先使用简单、可组合的工作流，只有当复杂度能明显提升效果时才增加复杂度。它们的工作流模式与本方案的映射关系很直接：

- Prompt chaining：PRD -> report/plan/questions -> artifacts。
- Routing：用能力面适配器路由 frontend/BFF/backend 影响面。
- Parallelization：多层影响可并行分析，之后再聚合。
- Evaluator-optimizer：质量门控和反馈回流持续提升输出。

它们也强调透明性、工具返回的真实事实、清晰的人机接口。来源：[Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)。

## 上下文接口

Model Context Protocol 把工具、资源、提示词分成不同能力。这里的启发是：稳定 reference、可调用工具/搜索、可复用提示词/工作流不应该都塞进一个巨大提示词。来源：[MCP Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)、[MCP Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)、[MCP Prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)。

## 仓库级指令

GitHub Copilot 的仓库级指令支持仓库级、路径级和 agent 指令，也支持 `AGENTS.md`，并由最近的指令优先生效。这支持我们把 reference 和能力面适配器放到项目内维护，而不是使用全局一刀切提示词。来源：[GitHub Copilot Repository Instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)。

## 对本工作流的启发

- 核心工作流要稳定、显式。
- 项目知识要持久化、可审阅、按范围组织。
- 用能力面适配器做专门化，不拆成三套流程，也不绑定固定目录结构。
- 所有结论必须有 evidence。
- 每个真实 PRD 结束后，都要通过反馈回流让系统变准。
- 优先结构化输出，不只给文字总结。
