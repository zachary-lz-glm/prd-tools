# prd-tools × Agent Skills 融合落地方案

> ADR-0005 | 2026-05-01 | 状态：规划中（v2.5.1 已实施图谱融合，详见 ADR-0006）

## Context

**现状**：prd-tools v2.5.1 是一个 Claude Code 插件，包含 2 个 Skill（build-reference + prd-distill），覆盖 DEFINE + PLAN 阶段。团队 1-5 人，以技术为主。

**已完成**：
- v2.5.0：图谱证据规范层（GitNexus + Graphify 双图谱集成规范）
- v2.5.1：图谱融合端到端补齐（模板、步骤、质量门控、prd-distill 消费，详见 ADR-0006）

**目标**：借鉴 Agent Skills 的架构设计（Anti-rationalization、Agent Persona、并行审查、Slash 命令、Reference Checklist、Session Hook），在 prd-tools 上原地扩展，使其成为覆盖全生命周期的 B 端营销团队工具集。

**Agent Skills 核心设计模式**：
1. 每个 Skill 有「借口反驳表」+「验证门」（Anti-rationalization + Verification）
2. 三层组合：Skills（怎么做）+ Personas（谁来做）+ Commands（什么时候做）
3. `/ship` 命令的 fan-out 并行审查模式（3 个 Persona 并行出具报告 → 合并 → GO/NO-GO）
4. Session Hook 自动注入 meta-skill
5. 共享 Reference Checklist（按需加载，控制 token）

**图谱工具已集成**：
- GitNexus（代码结构图谱）：已接入 build-reference step-01/02，产出 `_prd-tools/build/graph/code-evidence.yaml`
- Graphify（业务语义图谱）：已接入 build-reference step-01/02，产出 `_prd-tools/build/graph/business-evidence.yaml`
- 双证据字段（`evidence` + `graph_evidence_refs`）已在 01-05 模板中就位
- prd-distill 已支持轻量级图谱补查（affected_symbols / business_constraints）

---

## 最终架构（v3.0.0）

```
prd-tools/                                  # v3.0.0
├── .claude-plugin/marketplace.json         # 更新：新增 3 个 plugin
├── .claude/
│   ├── commands/                           # 【新增】7 个 Slash 命令
│   │   ├── spec.md                         #   /spec → 调用 prd-distill 做需求蒸馏
│   │   ├── reference.md                    #   /reference → 调用 build-reference 建知识库
│   │   ├── plan.md                         #   /plan → 任务拆解 + 排期
│   │   ├── review.md                       #   /review → 三视角并行审查
│   │   ├── ship.md                         #   /ship → 上线检查 + GO/NO-GO
│   │   ├── feedback.md                     #   /feedback → 反馈回流到 reference
│   │   └── simplify.md                     #   /simplify → 输出精简
│   └── settings.local.json                 # 更新权限
├── agents/                                 # 【新增】3 个 Agent Persona
│   ├── marketing-reviewer.md               #   营销视角审查
│   ├── biz-analyst.md                      #   业务合理性审查
│   └── tech-feasibility.md                 #   技术可行性审查
├── references/                             # 【新增】营销团队共享 Checklist
│   ├── b2b-content-guidelines.md           #   B端内容规范
│   ├── campaign-launch-checklist.md        #   活动上线清单
│   ├── customer-segmentation.md            #   客户分层标准
│   └── marketing-metrics.md                #   营销指标定义
├── hooks/                                  # 【新增】Session 生命周期 Hook
│   ├── hooks.json                          #   Hook 注册
│   └── session-start.sh                    #   自动注入 meta-skill
├── plugins/
│   ├── build-reference/                    # v2.5.1 图谱融合已补齐 → v3.0.0 加 Anti-rationalization
│   │   ├── .claude-plugin/plugin.json
│   │   ├── CHANGELOG.md
│   │   └── skills/build-reference/
│   │       ├── SKILL.md                    #   已含图谱增强 + 双证据字段 → +Anti-rationalization +Verification
│   │       ├── workflow.md
│   │       ├── agents/openai.yaml
│   │       ├── steps/                      #   6 个 step（step-01/02/03 已含图谱指令）
│   │       ├── references/                 #   → 软链接到根 references/（去重）
│   │       └── templates/                  #   6 个模板（01-05 + project-profile，已含 graph_sources）
│   ├── prd-distill/                        # v2.5.1 图谱消费已补齐 → v3.0.0 加 Anti-rationalization
│   │   ├── .claude-plugin/plugin.json
│   │   ├── CHANGELOG.md
│   │   └── skills/prd-distill/
│   │       ├── SKILL.md                    #   已含图谱增强 → +Anti-rationalization +Verification
│   │       ├── workflow.md                 #   已含 Step 3/4 图谱引用
│   │       ├── agents/openai.yaml
│   │       ├── steps/                      #   3 个 step（step-02 已含图谱增强）
│   │       ├── references/                 #   → 软链接到根 references/（去重）
│   │       └── scripts/ingest_prd.py       #   不变
│   ├── prd-review/                         # 【新增】三视角并行审查 Skill
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/prd-review/
│   │       ├── SKILL.md
│   │       └── workflow.md
│   ├── prd-ship/                           # 【新增】上线检查 + GO/NO-GO Skill
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/prd-ship/
│   │       ├── SKILL.md
│   │       └── workflow.md
│   └── prd-feedback/                       # 【新增】反馈回流 Skill
│       ├── .claude-plugin/plugin.json
│       └── skills/prd-feedback/
│           ├── SKILL.md
│           └── workflow.md
├── scripts/
│   ├── release.sh                          # 增强：支持 8 个版本位置同步
│   ├── install-hooks.sh                    # 增强：安装 session hook
│   └── hooks/pre-commit                    # 增强：校验新文件
├── docs/
│   └── adr/
│       ├── 0003-演进路线图.md
│       ├── 0005-本方案.md
│       └── 0006-图谱融合与知识库架构.md     # v2.5.1 已实施
├── CLAUDE.md                               # 更新：新架构说明
├── README.md                               # 更新：全生命周期文档
├── VERSION                                 # 3.0.0
└── install.sh                              # 增强：安装新目录
```

---

## 分阶段实施计划

### Phase 0：已完成（v2.5.0 + v2.5.1）— 图谱融合

**v2.5.0**：图谱证据规范层（reference-v4.md 图谱证据层、step-01/02 双图谱查询策略、prd-distill step-02 双维度影响分析）

**v2.5.1**：图谱融合端到端补齐（详见 ADR-0006）

| 改动 | 说明 |
|------|------|
| 6 个模板加 `graph_sources` + `graph_evidence_refs` | AI 填模板时能产出图谱数据 |
| step-01 加图谱证据文件创建 + EV/GEV 桥接 | `_prd-tools/build/graph/` 实际产出 |
| step-02 加前置加载 + per-phase 填充 | 图谱数据流入 01-05 |
| step-03 加图谱检查 | 质量门控校验图谱一致性 |
| prd-distill 3 个文件补图谱消费 | affected_symbols/business_constraints/contract-delta |

---

### Phase 1：Anti-rationalization + Verification（v2.5.1 → v2.6.0）— 约改动 6 个文件

**目标**：给现有 2 个 Skill 加上 Anti-rationalization + Verification，不改架构。

#### 1.1 增强 build-reference SKILL.md

**文件**：`plugins/build-reference/skills/build-reference/SKILL.md`

在现有内容末尾追加两个 section：

```markdown
## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "项目结构没变，reference 不需要更新" | 接口和业务逻辑可能已变化。运行 Mode B2 健康检查，用证据说话 |
| "先跑 prd-distill，后面再补 reference" | 没有 reference 的蒸馏是无源之水。先 build 再 distill 是铁律 |
| "这个项目太简单，不需要 contracts" | 简单项目也需要 03-contracts。Hyrum's Law：只要有用户依赖，就是契约 |
| "历史 PRD 找不到了，跳过 context enrichment" | 没有 context 的 reference 缺少领域知识锚点。用 Mode F 单独收集 |
| "去重检查太花时间" | 去重是 SSOT 的基石。v2.3 的教训：重复信息导致矛盾，debug 成本远高于去重 |
| "图谱不可用，图谱字段留空就行" | graph_sources: [] 是合法的。但 graph-sync-report 必须生成并记录不可用原因 |

## Verification Checklist

- [ ] `_prd-tools/reference/` 6 个文件全部生成，schema_version = "4.0"
- [ ] 每个事实至少有 1 条 evidence（kind/source/locator/confidence）
- [ ] 03-contracts 包含所有跨层/跨系统接口的字段级信息
- [ ] Quality Gate 报告状态为 pass（允许 warning，不允许 fail）
- [ ] 去重检查 5 条规则全部通过
- [ ] 00-portal.md 的健康状态为 green 或 yellow（不允许 red）
- [ ] 枚举值 / switch 分支 / 导出类型与源代码一致（确定性验证）
- [ ] `_prd-tools/build/graph/graph-sync-report.yaml` 已生成，provider 状态已记录
- [ ] 图谱可用时：至少一个 reference 文件有非空 graph_sources；图谱不可用时：所有 graph_sources 为 []
```

#### 1.2 增强 prd-distill SKILL.md

**文件**：`plugins/prd-distill/skills/prd-distill/SKILL.md`

同样追加：

```markdown
## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "PRD 写得很清楚，不需要做 ingestion 质量检查" | 越清晰的 PRD 越容易让 AI 跳过边界条件。quality gate 是安全网 |
| "需求很简单，直接出 plan 就行" | 简单需求的 plan 5 分钟就能出。但如果需求理解错了，返工远不止 5 分钟 |
| "reference 好像过期了，凑合用" | 过期 reference = 过期地图。先跑 build-reference Mode B2，再蒸馏 |
| "这个需求只改前端，不需要 contract delta" | 只改前端也可能影响 BFF 契约。layer-impact 分析会告诉你答案 |
| "questions.md 是可选的" | questions.md 只收集阻塞问题。如果生成了问题，说明有必须解决的风险 |
| "AI 自己能判断哪些需求重要" | Beyoncé Rule：如果一个需求在 PRD 里出现了，它就是重要的 |
| "图谱不可用，影响分析就够了" | 图谱不可用时靠源码 Read + rg/glob 完全可行。但如果有图谱，应优先消费 reference 中的 graph_evidence_refs |

## Verification Checklist

- [ ] PRD ingestion 完成，quality status 为 pass 或 warn（不允许 block）
- [ ] 每个 Requirement IR 条目至少有 1 条 PRD/tech_doc 类型 evidence
- [ ] 每个 change_type (ADD/MODIFY/DELETE) 都有源代码搜索证据支撑
- [ ] 多层变更已生成 contract-delta.yaml，alignment_status 无 blocked
- [ ] report.md 9 章结构完整，长度在 200-400 行
- [ ] plan.md 包含文件路径 + 行号 + 验证命令，长度在 150-350 行
- [ ] questions.md 只包含阻塞级问题（无阻塞则为空文件）
- [ ] reference-update-suggestions.yaml 已生成，类型为 6 种之一
- [ ] 图谱可用时：layer-impact 中 MODIFY 类型的 impact 条目有 affected_symbols 或 business_constraints
```

#### 1.3 去重：抽取共享 references 到根目录

**问题**：`external-practices.md`、`layer-adapters.md`、`output-contracts.md`、`selectable-reward-golden-sample.md` 在两个插件里是完全相同的副本。

**做法**：
1. 将这 4 个文件移动到根 `references/` 目录
2. 两个插件内的 `references/` 改为软链接指向根目录
3. `reference-v4.md` 保留在 build-reference 内（只有它用）

#### 1.4 新增根目录 references/ 下的营销团队 Checklist

新建 4 个文件：

**`references/b2b-content-guidelines.md`**（B端内容规范）
- 框架：标题/文案调性标准、行业术语表、禁用词列表、品牌一致性规则
- 来源：从团队现有营销物料中提炼（需用户提供样本）

**`references/campaign-launch-checklist.md`**（活动上线清单）
- 框架：上线前检查项（文案审核、链接测试、埋点确认、A/B 方案、回滚方案）
- 来源：从团队历史上线流程中提炼

**`references/customer-segmentation.md`**（客户分层标准）
- 框架：客户分级定义（KA/SMB/长尾）、分层维度、触达策略映射
- 来源：从团队 CRM 配置/运营策略中提炼

**`references/marketing-metrics.md`**（营销指标定义）
- 框架：核心 KPI 定义（MQL/SQL/CAC/LTV/转化率）、计算公式、数据源
- 来源：从团队 BI 报表中提炼

> **注意**：Phase 1 只创建骨架模板，内容标记为 `<!-- TODO: 需团队补充 -->`。Phase 3 时由用户提供真实内容填充。

#### 1.5 更新版本和 CHANGELOG

- VERSION → 2.6.0
- 更新根 CHANGELOG.md、两个插件 CHANGELOG.md
- 更新 CLAUDE.md 说明新 section 约定

---

### Phase 2：Slash 命令 + Agent Persona（v2.6.0 → v2.7.0）— 约新增 15 个文件

**目标**：建立命令体系和审查人设，让工具从"2 个孤立 Skill"变成"完整的开发生命周期"。

#### 2.1 创建 `.claude/commands/` 目录（7 个命令）

**`/spec`** → 映射到 prd-distill
```markdown
---
description: 需求蒸馏 — 将 PRD 转化为可执行的开发计划
---
Invoke the prd-tools:prd-distill skill.
确认 PRD 来源（文件/粘贴），运行 ingestion，生成 report + plan + questions。
```

**`/reference`** → 映射到 build-reference
```markdown
---
description: 知识库构建 — 构建或更新项目 reference v4.0
---
Invoke the prd-tools:build-reference skill。
```

**`/plan`** → 任务拆解（复用 prd-distill 的 plan 输出 + 新增排期逻辑）
```markdown
---
description: 任务排期 — 基于 plan.md 生成可分配的开发任务列表
---
读取 plan.md，按依赖关系排序，生成分配给具体开发者的任务清单。
```

**`/review`** → **三视角并行审查（核心新功能）**
```markdown
---
description: 三视角并行审查 — 营销/业务/技术三方同时评审
---
Fan-out 模式：同时启动 marketing-reviewer、biz-analyst、tech-feasibility
三个 Agent，各自独立出具报告，合并为一份综合评审结论。
```

**`/ship`** → 上线检查 + GO/NO-GO
```markdown
---
description: 上线决策 — 运行上线前检查清单，给出 GO/NO-GO 结论
---
运行上线清单，检查埋点、回滚方案、监控告警，输出 GO/NO-GO。
```

**`/feedback`** → 反馈回流
```markdown
---
description: 反馈回流 — 将开发中发现的新知识更新回 reference
---
调用 build-reference 的 E mode，读取 prd-distill 输出的 reference-update-suggestions。
```

**`/simplify`** → 输出精简
```markdown
---
description: 输出精简 — 简化 report/plan 输出，突出关键信息
---
```

#### 2.2 创建 `agents/` 目录（3 个 Persona）

每个 Persona 文件遵循 Agent Skills 的标准格式（YAML frontmatter + Review Framework + Output Format + Rules + Composition）。

**`agents/marketing-reviewer.md`**（营销视角审查员）

```yaml
---
name: marketing-reviewer
description: 营销策略专家。从目标客户匹配度、文案调性、品牌合规、转化漏斗角度审查方案。
---
```

审查维度：
1. **目标客户匹配度** — 方案是否针对正确的客户分层（对照 `references/customer-segmentation.md`）
2. **文案调性一致性** — 文案是否符合 B 端专业调性（对照 `references/b2b-content-guidelines.md`）
3. **品牌合规** — 是否违反品牌规范、使用禁用词
4. **转化漏斗合理性** — 用户旅程是否有断点、CTA 是否清晰
5. **活动规则可理解性** — 普通用户能否 30 秒内理解活动规则

输出格式：Critical / Important / Suggestion 三级，每条附文件定位 + 修复建议。
规则：必须对照 `references/b2b-content-guidelines.md` 和 `references/customer-segmentation.md`。

**`agents/biz-analyst.md`**（业务分析师）

```yaml
---
name: biz-analyst
description: 业务合理性审查专家。从 ROI、预算合规、业务规则完备性角度审查方案。
---
```

审查维度：
1. **ROI 预估合理性** — 预期收益计算是否自洽（对照 `references/marketing-metrics.md`）
2. **预算合规** — 是否超预算、预算分配是否合理
3. **业务规则完备性** — 边界条件、异常分支是否覆盖
4. **数据隐私合规** — 用户数据收集/使用是否合规
5. **竞品差异化** — 方案是否有差异化价值

输出格式：同上。
规则：必须对照 `references/marketing-metrics.md`。

**`agents/tech-feasibility.md`**（技术可行性审查员）

```yaml
---
name: tech-feasibility
description: 技术架构师。从技术方案可行性、接口兼容性、性能影响角度审查方案。
---
```

审查维度：
1. **技术方案可行性** — 现有技术栈能否支持、工期是否合理
2. **接口兼容性** — 是否破坏现有接口契约（对照 `_prd-tools/reference/03-contracts`）
3. **性能影响** — 是否引入性能瓶颈、N+1 查询、无限循环风险
4. **数据迁移风险** — 是否涉及数据迁移、迁移方案是否安全
5. **可回滚性** — 上线后能否快速回滚

输出格式：同上。
规则：必须对照 `_prd-tools/reference/` 中的 contracts 和 capability surfaces。

每个 Persona 末尾的 Composition 规则：
- 可通过 `/review` 命令并行调用
- 可单独调用（如只想要营销视角审查）
- Persona 之间不可互相调用

#### 2.3 创建 `hooks/` 目录

**`hooks/hooks.json`**：
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

**`hooks/session-start.sh`**：
读取 meta-skill 文件，构造 JSON payload（priority: "IMPORTANT"），注入到会话中。

#### 2.4 新增 prd-review Skill

**`plugins/prd-review/skills/prd-review/SKILL.md`**

核心设计：参照 Agent Skills 的 `/ship` fan-out 模式，用于方案审查阶段。

```
工作流：
1. 读取 _prd-tools/distill/<slug>/ 下的 report.md + plan.md
2. 读取 _prd-tools/reference/ 获取项目上下文
3. Phase A：并行启动 3 个 Persona
   - marketing-reviewer → 营销审查报告
   - biz-analyst → 业务审查报告
   - tech-feasibility → 技术审查报告
4. Phase B：合并三份报告为综合评审
   - 分类汇总（Critical / Important / Suggestion）
   - 交叉引用（消除重复发现）
5. Phase C：输出结论
   - APPROVE / REQUEST CHANGES
   - 阻塞项清单 + 修复建议
```

**图谱增强**：
- tech-feasibility Persona 可使用 GitNexus `impact()` 补充 blast radius 评估
- biz-analyst Persona 可使用 Graphify 查询业务约束和隐式规则

Anti-rationalization 表：

| Rationalization | Reality |
|---|---|
| "方案已经和业务对齐过了" | 口头对齐 ≠ 结构化审查。三视角能发现盲区 |
| "时间紧，跳过审查直接开发" | 审查发现一个 Critical 问题，就能节省数天返工 |
| "技术方案很简单，不需要技术视角" | 简单方案也可能有接口兼容问题。让证据说话 |
| "只需要技术审查就行，营销不用看" | 营销不看 = 方案可能偏离目标客户。B 端营销的成功取决于客户匹配度 |

Verification Checklist：
- [ ] 3 个 Persona 全部运行完毕，各自输出独立报告
- [ ] 合并报告包含所有 Critical/Important/Suggestion 发现
- [ ] 交叉引用消除了重复发现
- [ ] 输出明确的 APPROVE 或 REQUEST CHANGES 结论
- [ ] REQUEST CHANGES 时附有阻塞项清单 + 修复建议

#### 2.5 更新 marketplace.json 和版本

- marketplace.json 新增 prd-review plugin
- VERSION → 2.7.0
- 更新所有 CHANGELOG

---

### Phase 3：完整生命周期 + 团队 Reference 填充（v2.7.0 → v3.0.0）

**目标**：补齐 SHIP 阶段，填充营销团队真实 Checklist 内容。

#### 3.1 新增 prd-ship Skill

**`plugins/prd-ship/skills/prd-ship/SKILL.md`**

```
工作流：
1. 读取 review 结论（必须是 APPROVE 状态，否则拒绝继续）
2. 运行上线前检查清单（对照 references/campaign-launch-checklist.md）
3. 检查埋点方案完整性、A/B 实验配置、回滚方案、监控告警
4. 输出 GO/NO-GO 决策
5. GO 时：生成分阶段发布计划 + 回滚脚本
6. NO-GO 时：列出阻塞项 + 预估修复时间
```

**图谱增强**：
- 使用 GitNexus `detect_changes()` 检查未预期的代码变更影响
- 使用 Graphify 验证上线内容与业务规则的一致性

Anti-rationalization 表：

| Rationalization | Reality |
|---|---|
| "上线清单太繁琐，我们以前都不用" | 以前不出事不代表以后不出事。清单是安全网，不是负担 |
| "先上线再说，有问题再修" | B 端客户对故障容忍度极低。一次事故可能丢失大客户 |
| "回滚方案不需要" | 没有回滚方案的上线 = 赌博。30 分钟写回滚方案 vs 数小时紧急修复 |

#### 3.2 新增 prd-feedback Skill

**`plugins/prd-feedback/skills/prd-feedback/SKILL.md`**

```
工作流：
1. 读取 _prd-tools/distill/<slug>/spec/reference-update-suggestions.yaml
2. 按类型分组（new_term / new_route / new_contract / new_playbook / contradiction / golden_sample）
3. 逐条验证：用源代码确认建议的准确性
4. 展示 diff 给用户确认
5. 确认后写入 _prd-tools/reference/ 对应文件
6. 运行 build-reference Mode C 质量门
```

**图谱增强**：
- 验证时可用 GitNexus 查询确认新增契约的 consumer 是否完整
- 验证时可用 Graphify 查询确认新增术语的语义一致性

#### 3.3 填充营销团队 Reference 内容

此时需要用户提供：
- 历史营销活动 PRD 样本（3-5 份）
- 团队内容规范文档
- 客户分层策略文档
- BI 报表中的指标定义
- 上线 SOP 文档

将这些真实内容填充到 `references/` 下的 4 个 Checklist 文件中，替换 Phase 1 的骨架模板。

#### 3.4 创建 meta-skill

**`skills/using-prd-tools/SKILL.md`**

```yaml
---
name: using-prd-tools
description: 指导 AI 何时使用 prd-tools 的各个 Skill。每次会话自动加载。
---
```

```markdown
Overview: prd-tools 是 B 端营销团队的开发全生命周期工具集。

| 场景 | 使用 |
|---|---|
| 新项目/首次使用 | /reference → /spec |
| 日常 PRD 开发 | /spec → /plan → /review → /ship → /feedback |
| 知识库过期 | /reference（Mode B2 健康检查）|
| 只做营销审查 | /review（单独使用）|
| 上线决策 | /ship |
| 经验沉淀 | /feedback |
```

#### 3.5 更新 install.sh

增强安装脚本：
- 复制 `.claude/commands/` 到目标项目
- 复制 `agents/` 到目标项目
- 复制 `references/` 到目标项目
- 安装 session hook

#### 3.6 版本升级到 3.0.0

- 更新 VERSION、所有 CHANGELOG、CLAUDE.md、README.md
- 更新 release.sh 支持 8 个版本位置（+3 个新 plugin）
- 更新 pre-commit hook

---

## 版本对照表

| 版本 | 核心变更 | 借鉴 Agent Skills 的什么 | 状态 |
|------|---------|------------------------|------|
| **v2.5.0** | 图谱证据规范层（reference-v4.md、step-01/02 查询策略） | — | 已发布 |
| **v2.5.1** | 图谱融合端到端补齐（模板、步骤、质量门控、prd-distill） | — | 已发布（ADR-0006） |
| **v2.6.0** | Anti-rationalization + Verification + Reference 去重 + 营销 Checklist 骨架 | 每个 Skill 的标准 section 结构 | 待实施 |
| **v2.7.0** | Slash 命令 + 3 个 Persona + prd-review Skill + Session Hook | 三层组合架构 + fan-out 并行审查 | 待实施 |
| **v3.0.0** | prd-ship + prd-feedback + 营销 Reference 填充 + meta-skill | 全生命周期覆盖 + 渐进式披露 | 待实施 |

---

## 关键文件清单

### 已完成的文件（v2.5.0 + v2.5.1）

| 文件 | 改动 |
|------|------|
| `templates/01-codebase.yaml` | +graph_sources +graph_evidence_refs +graph_providers |
| `templates/02-coding-rules.yaml` | +graph_sources（rules/danger_zones/war_stories 分 provider） |
| `templates/03-contracts.yaml` | +graph_sources +graph_evidence_refs |
| `templates/04-routing-playbooks.yaml` | +graph_sources +graph_evidence_refs |
| `templates/05-domain.yaml` | +graph_sources +graph_evidence_refs |
| `templates/project-profile.yaml` | +graph_sources +graph_evidence_refs +graph_providers |
| `steps/step-01-structure-scan.md` | +图谱证据文件创建 +EV/GEV 桥接 |
| `steps/step-02-deep-analysis.md` | +前置图谱加载 +per-phase 填充 |
| `steps/step-03-quality-gate.md` | +图谱证据检查 |
| `build-reference/SKILL.md` | +图谱增强升级（双证据、置信度映射、_prd-tools/build/graph/） |
| `prd-distill/SKILL.md` | +图谱增强 section |
| `prd-distill/workflow.md` | +Step 3/4 图谱引用 |
| `prd-distill/references/output-contracts.md` | +affected_symbols +business_constraints +graph_evidence_refs |
| `docs/adr/0006-图谱融合与知识库架构.md` | 新建 |

### 待修改的现有文件（Phase 1 → v2.6.0）

| 文件 | 改动 |
|------|------|
| `plugins/build-reference/skills/build-reference/SKILL.md` | +Anti-rationalization +Verification |
| `plugins/prd-distill/skills/prd-distill/SKILL.md` | +Anti-rationalization +Verification |
| `CLAUDE.md` | +新 section 约定说明 |
| `VERSION` | 2.6.0 |
| `CHANGELOG.md`（根 + 2 个插件） | 新版本记录 |

### 待新建的文件

**Phase 1**（4 个）：
- `references/b2b-content-guidelines.md`
- `references/campaign-launch-checklist.md`
- `references/customer-segmentation.md`
- `references/marketing-metrics.md`

**Phase 2**（~15 个）：
- `.claude/commands/` × 7 个命令文件
- `agents/` × 3 个 Persona 文件
- `hooks/` × 2 个文件（hooks.json + session-start.sh）
- `plugins/prd-review/` × 3 个文件（plugin.json + SKILL.md + workflow.md）

**Phase 3**（~10 个）：
- `plugins/prd-ship/` × 3 个文件
- `plugins/prd-feedback/` × 3 个文件
- `skills/using-prd-tools/SKILL.md` × 1 个文件
- 更新 install.sh、release.sh、pre-commit hook

---

## 验证方案

### Phase 0 验证（已完成）
1. 在有 GitNexus 索引的项目跑 `/reference`，确认 `_prd-tools/build/graph/code-evidence.yaml` 生成
2. 确认 `01-codebase.yaml` modules 有 `graph_sources: ["gitnexus"]`
3. 确认质量门控报告包含 `graph_evidence_check`
4. 确认 prd-distill 的 layer-impact 包含 `affected_symbols`（GitNexus 可用时）

### Phase 1 验证
1. 在一个已有 `_prd-tools/reference/` 的项目上运行 `/reference`，确认 SKILL.md 末尾新增的 section 被正确读取
2. 运行 `/prd-distill` 处理一个真实 PRD，确认 Anti-rationalization 表阻止了常见偷懒行为
3. 检查 Verification Checklist 是否在输出末尾出现且全部打勾

### Phase 2 验证
1. 在目标项目安装插件，运行 `/review`，确认 3 个 Persona 并行启动并各自输出报告
2. 检查合并报告格式正确（Critical/Important/Suggestion 分级）
3. 运行 `/spec` 和 `/reference`，确认命令映射正确

### Phase 3 验证
1. 完整跑一遍 `/reference → /spec → /plan → /review → /ship → /feedback` 全流程
2. 在 `/ship` 阶段确认 GO/NO-GO 输出格式正确
3. 在 `/feedback` 阶段确认 reference 更新正确写入
4. 新开一个会话，确认 session-start hook 自动注入 meta-skill

---

## 风险和注意事项

1. **Reference 内容需要真实数据**：Phase 3 的 4 个营销 Checklist 必须由用户提供真实素材填充，骨架模板没有实际价值
2. **Persona 视角需要校准**：三视角审查的有效性取决于 Persona 定义的精准度，上线后需要根据实际使用反馈迭代
3. **Token 消耗**：fan-out 并行审查会消耗较多 token（3 个 Persona 同时运行），建议只在里程碑节点使用
4. **版本同步**：从 5 个版本位置扩展到 8 个，release.sh 必须同步更新
5. **向后兼容**：现有 `_prd-tools/reference/` v4.0 结构和 `_prd-tools/` 结构不变，所有新功能都是增量
6. **图谱依赖是可选的**：所有 Phase 的核心功能不依赖 GitNexus/Graphify，图谱增强是质量提升而非功能前提
7. **图谱证据需要 validator**：当前依赖 AI 按文档生成，v3.0 后应补 deterministic validator（ADR-0006 记录）

---

## 参考

- Agent Skills 仓库：https://github.com/addyosmani/agent-skills
- Agent Skills 文档：skill-anatomy.md（Skill 格式规范）、agents/README.md（Persona 架构说明）
- prd-tools 现有 ADR：ADR-0003（演进路线图）、ADR-0006（图谱融合与知识库架构）
