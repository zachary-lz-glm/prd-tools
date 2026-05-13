# prd-distill

> 把 PRD 蒸馏成有证据支撑的技术报告和开发计划。采用**三段式工作流** `spec → report → plan`，中间夹用户确认门控，所有结论可追溯到 PRD 原文、源码或负向搜索。

## 快速使用

`/prd-distill` 提供 4 个入口：

```text
/prd-distill spec <PRD 文件或需求文本>   → 只跑 spec 阶段，产出 AI-friendly PRD + requirement-ir
/prd-distill report <slug>              → 跑 report 阶段，生成 report.md 后暂停等待确认
/prd-distill plan <slug>                → 用户 approved 后生成 plan.md
/prd-distill <PRD 文件或需求文本>        → 引导式入口（spec 完成后停下，不自动跑 plan）
```

**输入格式：** `.md` / `.txt` / `.docx` 文件，或直接粘贴需求文本。`.docx` 用原生 `unzip` 提取文本和图片，Claude 直接看图理解 UI 截图和流程图，零外部依赖。

```text
/prd-distill spec docs/新司机完单奖励PRD.md
/prd-distill spec 需要在活动页面新增一种优惠券类型，type_id=45
```

如果项目已有 `_prd-tools/reference/`（通过 `/reference` 命令生成），蒸馏质量会显著提升。

## 三段式工作流

| 阶段 | 核心问题 | 是否读源码 | 是否需要用户确认 |
|------|----------|------------|------------------|
| **spec** | PRD 本身到底说了什么 | 默认不读 | 不强制（但输出 Open Questions） |
| **report** | 这个 PRD 放到当前项目会影响什么 | 必须读 reference / index / 源码 | **必须确认** |
| **plan** | 在确认后的影响分析基础上怎么实施 | 只消费 confirmed report 和 context | — |

```text
PRD 原文
   ↓
[spec]  → spec/ai-friendly-prd.md (13 章节) + context/requirement-ir.yaml
   ↓
[report] → context/layer-impact.yaml + contract-delta.yaml + report.md
   ↓
⚠ Report Review Gate：用户 approved / needs_revision / blocked
   ↓ approved
[plan] → plan.md（单仓）或 team-plan.md + plans/plan-{repo}.md（团队）
```

**Report Review Gate** 是核心设计：report 生成后必须暂停，用户确认写入 `context/report-confirmation.yaml`。`status: approved` 才允许生成 plan；`needs_revision` 时必须回到对应上游产物修正（AI-friendly PRD / requirement-ir / layer-impact / contract-delta），不能直接在 plan 里打补丁。

## AI-friendly PRD（规范化中间层）

现实 PRD 往往不够结构化，容易让 AI 误读。spec 阶段必定先产出 `spec/ai-friendly-prd.md`，13 个固定章节：

```
1. Overview              8.  Technical Considerations
2. Problem Statement     9.  UI/UX Requirements
3. Target Users          10. Out of Scope
4. Goals & Metrics       11. Timeline & Milestones
5. User Stories          12. Risks & Mitigations
6. Functional Reqs       13. Open Questions
7. Non-Functional Reqs
```

每条关键条目必须标注 **Source**：

| Source | 含义 | 去处 |
|---|---|---|
| `explicit` | 原 PRD 明写 | 可进 plan 确定任务 |
| `inferred` | 从上下文合理推断 | 默认 assumption_only，需 report 再次确认 |
| `missing_confirmation` | 缺失或冲突 | **绝对不能进 plan 确定任务**，必须进 §13 Open Questions |

Source 标记一路继承：AI-friendly PRD → requirement-ir → layer-impact 每个 IMP → plan.md checklist。这让"AI 是否真的读懂 PRD"变成可审查的产物。

## 产出

### 单仓模式

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # PRD 原始读取（source-manifest/document/media/extraction-quality 等）
├── spec/
│   └── ai-friendly-prd.md         # 13 章节规范化中间层
├── report.md                      # 12 章节渐进式披露报告
├── plan.md                        # 11 章节技术方案 + 开发计划 + QA 矩阵
└── context/
    ├── prd-quality-report.yaml    # AI-friendly PRD 6 维度评分
    ├── requirement-ir.yaml        # 结构化需求（含 ai_prd_req_id + source + planning.eligibility）
    ├── evidence.yaml              # 证据台账（PRD/技术文档/源码/负向搜索/reference 消费）
    ├── query-plan.yaml            # reference index 查询计划（辅助层）
    ├── context-pack.md            # 精简代码上下文（辅助层）
    ├── graph-context.md           # 源码扫描的函数级上下文
    ├── layer-impact.yaml          # 分层影响（每 IMP 带 code_anchors）
    ├── contract-delta.yaml        # 字段级契约差异
    ├── critique/<step_id>.yaml    # 高风险步骤的二次审查结果
    ├── report-confirmation.yaml   # 用户对 report 的确认状态
    ├── readiness-report.yaml      # 就绪度评分 + provider 增益
    ├── final-quality-gate.yaml    # 5 项加权评分（辅助层）
    └── reference-update-suggestions.yaml  # 回流建议
```

### 团队模式（自动识别 `layer: team-common`）

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # 同单仓
├── spec/                          # 同单仓
├── report.md                      # §10 强制 4 子节：10.1 FE / 10.2 BFF / 10.3 BE / 10.4 External
├── team-plan.md                   # 团队级总览 + 跨仓时序 + Sub-Plan 索引
├── plans/                         # 动态命名（来自 member_repos[].repo）
│   ├── plan-genos.md
│   ├── plan-dive-bff.md
│   └── plan-magellan.md
└── context/
    ├── layer-impact.yaml          # 4 层完整填充（anchors 来自 snapshots）
    ├── contract-delta.yaml        # 全栈 consumers[]
    └── ...                        # 其余同单仓
```

团队模式下**禁止 rg/glob**，所有代码坐标从 `team/01-codebase.yaml` 的 `cross_repo_entities` + `snapshots/{layer}/{repo}/` 下钻读取。

## 质量保障机制

- **Reference 强制消费**：若 `_prd-tools/reference/` 存在，Step 0 消费门禁（路由/规则/契约/术语）→ Step 2.5 桥接 index → Step 3.1 reference-first 扫描，缺一不可
- **Critique Pass（Two-Pass Critic）**：Step 1.5（AI-friendly PRD）、Step 2（requirement-ir）、Step 3.2（layer-impact）、Step 4（contract-delta）完成后各做一次二次审查，fail 阻断后续步骤
- **REQ → IMP → code_anchor 强绑定**：每个 MODIFY/DELETE 任务必须有 `code_anchor(layer/file/symbol/line/source)` 或 fallback reason
- **Completion Gate**：`quality-gate.py distill` 13 项检查，exit code ≠ 2 才能宣称完成

## 什么时候用

| 场景 | 用它 |
|------|------|
| 拿到新 PRD，需要评估影响范围 | 是 |
| 需要给前端/BFF/后端拆任务、对齐接口 | 是 |
| 字段/枚举/schema 的契约风险识别 | 是 |
| 需要生成 QA 测试矩阵 | 是 |
| 跨仓多团队协作的大 PRD（团队模式） | 是 |
| 直接改代码，不需要分析 | 否 |
| 没有任何可分析的输入 | 否 |

## 典型工作流

1. **spec** — `/prd-distill spec <PRD>`，产出 AI-friendly PRD + requirement-ir，检查 source 标记和 Open Questions
2. **report** — `/prd-distill report <slug>`，读 reference/源码做影响分析，生成 report.md
3. **确认** — 阅读 report.md 的摘要、影响范围、契约风险、Top Open Questions，回复 approved / needs_revision / blocked
4. **plan** — `/prd-distill plan <slug>`（需 approved），生成函数级 plan.md
5. **执行与回流** — 按 plan 开发，交付后 `/reference` Mode E 把 `reference-update-suggestions.yaml` 回流
