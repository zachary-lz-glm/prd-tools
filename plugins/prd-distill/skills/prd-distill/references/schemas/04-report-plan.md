# report.md + plan.md 模板

## report.md

渐进式披露（Progressive Disclosure）：同一文件内从结论到细节逐层展开，包含阻塞问题与待确认项，不需要跳到其他文件就能获取核心信息。

### 结构模板

```markdown
# 需求分析报告：<需求名称>

## 1. 需求摘要（30秒决策）
一句话摘要 + 变更类型统计（ADD/MODIFY/DELETE/NO_CHANGE 各几项）。

## 2. PRD 质量摘要
来自 `context/prd-quality-report.yaml`：
- AI-friendly PRD 总分和状态（pass / warning / fail）
- source 分布：explicit / inferred / missing_confirmation 各多少条
- 关键缺失项、硬降级原因、风险摘要
- 如果 `prd-quality-report.yaml` 状态为 fail 或 warning，必须在此说明对后续蒸馏的影响

## 3. 源码扫描命中摘要
| 来源 | 命中内容 | 用于哪些结论 | 缺口 |
列出代码搜索命中的关键函数/调用链/API consumer。

## 4. 影响范围
命中的层、能力面、关键文件/模块（表格形式）。

## 5. 关键结论
新增/修改/不改什么，每个结论带 REQ-ID、IMP-ID 和代码路径引用。
REQ-ID 应能回溯到 `spec/ai-friendly-prd.md` 的 REQ-ID。
每个结论必须标注 code_anchor 或 fallback reason。

## 6. 变更明细表（核心可操作内容）
| ID | 变更描述 | 类型 | 目标文件 | 关键函数/符号 | REQ-ID | IMP-ID | code_anchor / fallback | 验证来源 |
列出所有 IMP-* 项，精确到文件路径和关键 symbol，标注 code_verified / graph_verified / reference_only。
没有 code_anchor 的 ready MODIFY/DELETE 项必须标红为风险。
assumption_only / blocked 项不得进入确定实现行。

## 7. 字段清单（按功能模块分组）
| 字段 | 类型 | 必填 | 来源 | 契约ID |
从 requirement-ir 和 contract-delta 中提取，按业务模块分组。

## 8. 校验规则
| ID | 规则描述 | 错误文案/提示 | 目标文件 |
从 requirement-ir.rules 中提取可验证的校验规则。

## 9. 开发 Checklist（可直接执行）
- [ ] 1. <具体操作>（<目标文件>）— REQ-001, IMP-001
- [ ] 2. <具体操作>（<目标文件>）— REQ-002, IMP-002
...
按建议实现顺序排列，每项标注关联的 REQ/IMP/CONTRACT。

## 10. 契约风险
只列 alignment_status 为 needs_confirmation 或 blocked 的契约。

## 11. Top Open Questions
最多5个最关键的阻塞问题，带 Q-ID。
**必须吸收 `spec/ai-friendly-prd.md` §13 的 Open Questions**。
`missing_confirmation` 项必须进入此处或 §12 阻塞问题与待确认项。

## 12. 阻塞问题与待确认项

### 12.1 阻塞问题
每个阻塞问题必须包含 6 要素：
- **问题**：阻塞项的具体描述
- **线索**：代码/文档线索（文件路径:行号 + 线索描述）
- **影响**：哪些 REQ/IMP/CONTRACT 被阻塞
- **建议 Owner**：建议谁确认
- **需要证据**：确认人需要提供什么
- **默认策略**：如果不确认，默认采取什么行动

### 12.2 低置信度假设
⚠ 标注的低置信度结论，说明为什么置信度低、需要什么才能提升。
`inferred` 项只能作为低置信度假设、待确认项或风险呈现，不得伪装成原 PRD 明确事实。

### 12.3 Owner 确认项
需要特定角色确认的契约字段、枚举值、外部接口行为等。
`missing_confirmation` 项必须出现在此处或 §11 Top Open Questions。

如无阻塞问题，显式写"当前无阻塞问题"。

---
*详细证据链见 context/*
```

### 写作规则

- **自然语言为主**，避免纯 YAML/JSON 格式；用 Markdown 表格提高可扫描性。
- **具体到文件路径**：每个变更项都带目标文件路径（如 `model/business_object/xxx/`）。
- **关联 ID**：每个条目引用 REQ-*/IMP-*/CONTRACT-*，方便跳到 context/ 查证。
- **不隐藏低置信度**：低置信度项用 ⚠ 标注，进入 §12.2。
- **Checklist 可直接执行**：开发人员拿到就能按步骤干活，每项必须标注 REQ-ID、IMP-ID 和 code_anchor（或 fallback reason）。
- **线索式证据不能省略**：代码注释、已有结构体名、文件路径等线索必须保留。这些线索对开发定位问题有极高价值。
- **必须说明 AI-friendly PRD 质量状态**：§2 PRD 质量摘要必须从 `context/prd-quality-report.yaml` 提取，不得省略。
- **REQ-ID 必须可回溯**：关键结论中的 REQ-ID 应能回溯到 `spec/ai-friendly-prd.md` 的 REQ-ID。
- **inferred 不得伪装为事实**：`inferred` 只能作为低置信度假设、待确认项或风险呈现，不得写成原 PRD 明确事实。
- **missing_confirmation 必须暴露**：`missing_confirmation` 项必须进入 §11 Top Open Questions 或 §12 阻塞问题与待确认项，不得隐藏。
- **IMP 必须绑定 REQ**：变更明细表中每个 IMP 必须引用 REQ-ID 和 ai_prd_req_id，不得出现无 REQ 归属的变更项。
- **没有 code_anchor 的 ready MODIFY/DELETE 必须标红**：变更明细表和 Checklist 中，ready 状态的 MODIFY/DELETE 项如果没有 code_anchor，必须标注为风险并说明 fallback reason。
- **assumption_only / blocked 不得进入确定实现 checklist**：planning_eligibility 不为 ready 的项只能进入 §11/§12 或风险标注，不得写入 §9 开发 Checklist。

### 职责边界

- **report.md 是决策文档，不是所有细节的全集**。
- 不要把完整 YAML 证据链展开到 report 里，那是 context/ 的职责。
- 不要复制 PRD 原文，只引用 REQ-ID。
- 建议总长度控制在 300-650 行（Markdown 源码）。超限时精简优先级：字段清单 > 校验规则（先精简）；代码命中摘要 > 变更明细表 > 阻塞问题与线索 > 契约风险 > 影响范围（不精简）。

## plan.md

可 review 的函数级技术方案文档 + 可执行的开发计划。精确到文件路径、行号、关键函数/方法/结构体，包含架构决策、调用链、数据模型和回归范围。

### 结构模板

```markdown
# 技术方案：<需求名称>

## 1. 范围与假设
### 目标
本方案覆盖的 REQ 范围和预期产出。

### 非目标
明确排除的范围，避免过度设计。

### 前置条件与依赖
需要先完成的基础设施、其他团队接口、外部系统准备。

#### AI-friendly PRD Source 状态约束

| Source 类型 | 数量 | 在本计划中的处理 |
|---|---:|---|
| explicit | N | 可进入确定实现 checklist |
| inferred | N | 只能进入"待确认 / 假设前提"，需 owner 确认后才能转为确定任务 |
| missing_confirmation | N | 不得进入确定实现 checklist，只能进入"待确认 / 阻塞项" |

> 详见 `spec/ai-friendly-prd.md` 各 REQ-ID 的 source 标记和 `context/prd-quality-report.yaml` 的 counts。

## 2. 整体架构
### 代码坐标
| REQ | ai_prd_req_id | IMP-ID | 入口/函数/结构体 | 文件:行号 | 调用链角色 | code_anchor | 来源 |
来自代码搜索。必须标注搜索来源（rg/Read 等）。每个 MODIFY/DELETE 必须有 code_anchor 或 fallback reason。

### 方案概述
用文字描述+简单框图说明整体方案。

### 核心数据模型
关键结构体/Schema 用伪代码展示字段结构（从源码已有结构体推断）。

### 关键设计决策
列出主要 trade-off 和选择理由（如：为什么选方案 A 不选方案 B）。

### 与现有系统的交互
调用链、数据流、涉及的已有模块和接口。

## 3. 实现计划
### Phase 1: 基础设施
- [ ] **1.1** <任务描述>
  - requirement_id：REQ-001
  - impact_id：IMP-FE-001
  - 文件：`path/to/file.go:27`
  - 关键函数/结构体：`SymbolName`
  - code_anchor：ANCHOR-001（或 fallback: 无现有锚点，proposed location: xxx）
  - 操作：具体操作描述
  - 调用链影响：入口 -> 当前函数 -> 下游函数/consumer
  - 证据依据：`GCTX-001` / `EV-001`
  - 关联：REQ-001, IMP-FE-001
  - 验证：`grep -n "XXX" path/to/file.go`

### Phase 2: 核心功能
...

### Phase 3: 联调与收尾
...

## 4. API 设计
### Schema 变更
新增或修改的请求/响应字段表格。

### 接口变更
| 接口 | 方法 | 变更类型 | 字段变更 |

### 外部服务调用
调用的外部接口、预期请求/响应、超时和降级策略。

## 5. 数据存储
### 表/索引变更
新增表、新增字段、索引变更。

### 缓存变更
缓存 Key 设计、过期策略、一致性保证。

### Migration 要点
数据库迁移注意事项。

## 6. 配置与开关
### Feature Flag
开关名称、作用、默认值。

### 灰度策略
灰度维度（用户/城市/百分比）、回滚条件。

## 7. 校验规则汇总
| 规则 | 层 | 目标文件 | 错误提示 |
前端/BFF/后端校验规则矩阵。

## 8. QA 矩阵
| 场景 | 关键检查点 | 关联 REQ | 优先级 |
覆盖正常流 + 边界情况 + 异常流，P0/P1/P2 分级。

## 9. 契约对齐
| 契约 | 状态 | Producer | Consumer | 需确认内容 |
只列 needs_confirmation 和 blocked。

## 10. 风险与回滚
### 回滚方案
具体回滚步骤。

### 观测建议
需要关注的 metric、日志、报警。

### 已知坑点
源码线索暗示的潜在问题。

### 回归范围
哪些已有功能可能受影响，需要回归验证。

## 11. 工作量估算
| 模块 | 估算 | 说明 |
按模块估算人天，标注关键路径。
```

### 写作规则

- **精确到文件和行号**：每个任务给出目标文件路径，尽量带行号。不确定行号时标注"约在 XX 附近"，不要编造。
- **精确到函数级**：MODIFY/DELETE 任务必须给出入口函数、关键函数/方法/结构体、调用方/被调用方和回归影响；ADD 任务必须给出相邻参考实现或负向搜索证据。
- **每个实现任务必须绑定 REQ→IMP→Anchor**：requirement_id、impact_id、code_anchor id（或 fallback reason）缺一不可。
- **没有 anchor 的 ADD 任务**：必须说明 proposed location（目标模块/文件/相邻组件）。
- **没有 anchor 的 MODIFY/DELETE 任务**：必须进入 needs_confirmation 或 blocked，不得作为确定实现项。
- **Graph Context 优先**：先消费代码搜索结果，再写 plan。不能只根据 `_prd-tools/reference/` 写计划。
- **给出验证命令**：每个关键步骤附带 grep/go test 等验证命令。
- **给出参考实现**：类似功能的已有代码路径，开发人员可以参照。
- **代码线索不可省略**：每个任务必须保留文件路径、行号、参考结构体名、proxy 路径等线索。
- **Checklist 格式**：用 `- [ ]` 格式，开发人员可以直接勾选。
- **按 Phase 分组**：体现依赖关系，Phase 间标注前置条件。
- **missing_confirmation 不得进入确定实现 checklist**：ai-friendly-prd 中标注为 `missing_confirmation` 的需求不得写入确定实现 checklist，只能写入"待确认"或"假设前提"章节。P0 requirement 为 `missing_confirmation` 时必须标注为 blocked 或 needs_confirmation。
- **inferred 需确认后才能确定**：确定实现 checklist 只能包含 `explicit`，或已在 report/questions 中明确确认路径的 `inferred`。未确认的 `inferred` 只能进入"待确认 / 假设前提"。
- **REQ-ID 必须可回溯**：每个计划项应引用 requirement-ir 的 REQ-ID，并尽量能追溯到 `spec/ai-friendly-prd.md` 的 REQ-ID。

### 职责边界

- **plan.md 是可 review 的技术方案，不是二次报告**。
- 不要重复 report.md 的分析结论，只写"做什么、怎么做、为什么这样做"。
- 不要复制 PRD 原文。
- 建议总长度控制在 300-700 行（Markdown 源码）。超限时精简优先级：工作量估算 > 配置与开关 > 数据存储细节（先精简）；实现计划 > QA 矩阵 > 风险与回滚（不精简）。
