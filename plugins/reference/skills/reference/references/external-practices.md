# 外部工程化实践

这些实践用于支撑设计判断，不是要照搬成僵硬流程。

## 规格驱动产物

Kiro specs 把功能工作拆成需求、设计、任务，并包含验收标准、架构/设计文档和可跟踪任务。这支持我们保留 Requirement IR、Layer Impact、Contract Delta 等可追踪 artifacts，同时默认给用户轻量 report/plan。来源：[Kiro Specs](https://kiro.dev/docs/specs/)。

Kiro steering 把长期项目知识放到 workspace markdown 文件中，并强调文件聚焦、示例、安全和定期维护。这支持 reference v3.1 作为项目记忆，而不是每次对话临时拼提示词。来源：[Kiro Steering](https://kiro.dev/docs/steering/)。

## 简洁的 Agent 工作流

Anthropic 建议先使用简单、可组合的工作流，只有当复杂度能明显提升效果时才增加复杂度。它们的工作流模式与本方案的映射关系很直接：

- Prompt chaining：PRD -> report/plan -> artifacts。
- Routing：用能力面适配器路由 frontend/BFF/backend 影响面。
- Parallelization：多层影响可并行分析，之后再聚合。
- Evaluator-optimizer：质量门控和反馈回流持续提升输出。

它们也强调透明性、工具返回的真实事实、清晰的人机接口。来源：[Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)。

## 上下文接口

Model Context Protocol 把工具、资源、提示词分成不同能力。这里的启发是：稳定 reference、可调用工具/搜索、可复用提示词/工作流不应该都塞进一个巨大提示词。来源：[MCP Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)、[MCP Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)、[MCP Prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)。

## 图谱增强检索

Microsoft GraphRAG 把知识图谱用于局部检索和全局问题回答：局部问题依赖实体邻域，全局问题依赖社区摘要。这支持 prd-tools 把业务概念先路由到局部代码符号/调用链，再汇总为 reference 和 report 的影响范围。来源：[Microsoft GraphRAG](https://microsoft.github.io/graphrag/)。

LightRAG 强调把图结构检索与向量/文本检索结合，兼顾局部关系和全局上下文。这支持我们不要只依赖 `_reference` 摘要，也不要只做全文 grep，而是沉淀图谱上下文再进入 report/plan。来源：[LightRAG](https://github.com/HKUDS/LightRAG)。

Code Property Graph 将 AST、控制流和数据流统一为可查询图，是函数级影响分析和安全/质量分析的经典基础。这支持 GitNexus 的符号、调用链、route consumer 结果作为高置信代码线索进入 reference。来源：[Code Property Graph](https://cpg.joern.io/)。

这些实践也提示 reference 的治理边界：单仓 reference 应该保存本仓已确认的局部事实，跨仓关系先作为候选边和 owner 待确认项；团队级知识库再聚合多个仓库的 confirmed 事实和社区摘要。

## 文档读取和版面理解

Azure AI Document Intelligence 的 Layout 能抽取文本、表格、选择标记、标题、章节、页眉页脚等结构，并支持输出 Markdown。这支持我们把 PRD 读取拆成独立 ingestion 层，而不是让 LLM 直接猜原始文档。来源：[Azure AI Document Intelligence Layout](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-layout)。

Google Document AI 提供 OCR、表单解析、版面解析、表格和实体抽取能力，适合复杂 PDF、扫描件和表格型需求文档。来源：[Google Cloud Document AI](https://cloud.google.com/document-ai/docs)。

AWS Textract 的 AnalyzeDocument 支持从文档中识别表格、表单和查询结果，适合把图片型或扫描型 PRD 的关键字段转为结构化证据。来源：[AWS Textract AnalyzeDocument](https://docs.aws.amazon.com/textract/latest/dg/API_AnalyzeDocument.html)。

IBM Docling 是开源文档转换工具，面向 PDF、Office 等文档的结构化转换，适合作为本地化 ingestion 的增强方向。来源：[Docling GitHub](https://github.com/docling-project/docling)。

## 仓库级指令

GitHub Copilot 的仓库级指令支持仓库级、路径级和 agent 指令，也支持 `AGENTS.md`，并由最近的指令优先生效。这支持我们把 reference 和能力面适配器放到项目内维护，而不是使用全局一刀切提示词。来源：[GitHub Copilot Repository Instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)。

## 对本工作流的启发

- 核心工作流要稳定、显式。
- 项目知识要持久化、可审阅、按范围组织。
- PRD 读取要先结构化、再推理；图片、表格、低置信度不能静默吞掉。
- 用能力面适配器做专门化，不拆成三套流程，也不绑定固定目录结构。
- 所有结论必须有 evidence。
- 图谱不是最终答案，而是高质量上下文生成器：先生成可审计图谱上下文，再精选进入 reference/report/plan。
- 单仓 reference 负责本仓权威事实；跨仓和团队级知识先保留确认状态，再进入未来聚合层。
- 每个真实 PRD 结束后，都要通过反馈回流让系统变准。
- 优先结构化输出，不只给文字总结。
