# prd-distill

> 把 PRD 蒸馏成有证据支撑的技术报告和开发计划。所有结论可追溯到 PRD 原文、源码或负向搜索。

## 快速使用

```text
/prd-distill <PRD 文件或需求文本>
```

**输入格式：** `.md` / `.txt` / `.docx` 文件，或直接粘贴需求文本。`.docx` 用原生 `unzip` 提取文本和图片，Claude 直接看图理解 UI 截图和流程图，零外部依赖。

```text
/prd-distill docs/新司机完单奖励PRD.md
/prd-distill 需要在活动页面新增一种优惠券类型，type_id=45
```

如果项目已有 `_prd-tools/reference/`（通过 `/reference` 命令生成），蒸馏质量会显著提升。

## 工作流

```text
PRD 原文
   ↓
Step 0-2: Ingestion → Evidence → Requirement IR
   ↓
Step 3-4: Graph Context → Layer Impact → Contract Delta
   ↓
Step 8: report.md（12 章节渐进式披露报告）
   ↓
⚠ Report Review Gate：用户 approved / needs_revision / blocked
   ↓ approved
Step 5-8.6: plan.md + readiness + quality gate
```

**Report Review Gate** 是核心设计：report 生成后必须暂停，用户确认写入 `context/report-confirmation.yaml`。`status: approved` 才允许生成 plan。

## 产出

### 单仓模式

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # PRD 原始读取（document/media/extraction-quality 等）
├── report.md                      # 12 章节渐进式披露报告
├── plan.md                        # 11 章节技术方案 + 开发计划 + QA 矩阵
└── context/
    ├── requirement-ir.yaml        # 结构化需求
    ├── evidence.yaml              # 证据台账
    ├── query-plan.yaml            # reference index 查询计划（辅助层）
    ├── context-pack.md            # 精简代码上下文（辅助层）
    ├── graph-context.md           # 源码扫描的函数级上下文
    ├── layer-impact.yaml          # 分层影响（每 IMP 带 code_anchors）
    ├── contract-delta.yaml        # 字段级契约差异
    ├── report-confirmation.yaml   # 用户对 report 的确认状态
    ├── readiness-report.yaml      # 就绪度评分
    ├── final-quality-gate.yaml    # 质量门禁（辅助层）
    └── reference-update-suggestions.yaml  # 回流建议
```

### 团队模式（自动识别 `layer: team-common`）

```text
_prd-tools/distill/<slug>/
├── _ingest/                       # 同单仓
├── report.md                      # §10 强制 5 子节：FE / BFF / BE / External / 跨层
├── team-plan.md                   # 团队级总览 + 跨仓时序 + Sub-Plan 索引
├── plans/                         # 动态命名（来自 team_repos[].repo）
│   ├── plan-genos.md
│   └── plan-dive-bff.md
└── context/
    ├── layer-impact.yaml          # 4 层完整填充
    ├── contract-delta.yaml        # 跨仓 consumers[]
    └── ...                        # 其余同单仓
```

团队模式下**禁止 rg/glob**，所有代码坐标从各仓 `references/{repo}/` 下钻读取。

## 质量保障机制

- **Reference 强制消费**：若 `_prd-tools/reference/` 存在，Step 0 消费门禁（路由/规则/契约/术语）→ Step 2.5 桥接 index → Step 3.1 reference-first 扫描，缺一不可
- **REQ → IMP → code_anchor 强绑定**：每个 MODIFY/DELETE 任务必须有 `code_anchor(layer/file/symbol/line/source)` 或 fallback reason

## 什么时候用

| 场景 | 用它 |
|------|------|
| 拿到新 PRD，需要评估影响范围 | 是 |
| 需要给前端/BFF/后端拆任务、对齐接口 | 是 |
| 字段/枚举/schema 的契约风险识别 | 是 |
| 需要生成 QA 测试矩阵 | 是 |
| 跨仓多团队协作的大 PRD（团队模式） | 是 |
| 直接改代码，不需要分析 | 否 |

团队模式详见 `/team-distill`。
