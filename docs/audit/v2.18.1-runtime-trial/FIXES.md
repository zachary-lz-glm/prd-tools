# prd-tools v2.18.1 实跑修复清单

> **来源**：2026-05-12 在 dive-bff 用 GLM-5.1 实跑 `/prd-distill` 处理 "DIVE 2.0 油站新司机完单领券" PRD。18 steps 全 pass，最终分 84/100，但过程中至少 5 处被工具逼回返工，耗时 37 分 53 秒。
> **执行原则**：按 P0-1 → P2-2 顺序做；每条 FIX 一个独立 commit；遇到现状与本文描述不一致先停下回报，不要猜。
> **所有路径相对 `/Users/didi/work/prd-tools/`**。
> **当前分支**：`v2.0`。

---

## 🚨 执行须知（给 GLM 或任何执行者看）

本轮修复的核心问题很多都是"字段/指令被静默删除"。**不要在执行时犯同样的毛病——扩而不删、加而不精简**。

### 核心原则：修改 > 新增（所有层面）

不仅仅指"不要新建脚本文件"，还包括：

- ❌ **不要新增字段**：先查现有 schema 是否有字段能承载同样语义。例如想加 `confirmation_status`，先看 `requirement-ir.yaml` 的 `confirmation.status` 能不能扩展到 layer-impact 复用
- ❌ **不要新增枚举值**：先看现有枚举里有没有同义值。例如想加 `source: "inferred_from_prd"`，先看现有 `source: "graph | rg | reference | inferred"` 的 `inferred` 够不够用
- ❌ **不要新增文档段**：想"加一段 NOTE"时，先看现有文档哪个段落能放进去（boundary、强绑定规则、SSOT 表等）
- ❌ **不要新增 check 函数**：能用 contract validator 声明式规则达到的，就不写 Python 函数
- ❌ **不要新增 skill / hook / slash command**：本轮一律不碰 skill 系统
- ❌ **不要新增 shell 包装器**：10 行以内调用其他脚本的 wrapper 一律不写

### 每条 FIX 执行前的 3 问

对每条 FIX 的每一步改动，执行前必须自问：

1. **"v2.16.0 原本有这个字段/规则/段落吗？"** → 有就是"恢复"，照搬 v2.16 原文。
2. **"现有文件里有现成字段/段落能承载这个语义吗？"** → 有就扩展现有的，不加新的。
3. **"如果我觉得需要'新'，真的是不可替代吗？"** → 只有 v2.16 也没有、现有也没有、且确实不可替代时，才允许新增；并在 commit message 里写清楚为什么不可替代。

### 本 FIXES.md 里"允许的新增"总清单（仅 5 项）

只有这些能新建：

1. `scripts/ingest-docx.py`（P1-1）— 唯一新脚本
2. `contracts/reference-update-suggestions.contract.yaml`（P0-12）— 补齐缺失的 contract
3. `contracts/evidence.contract.yaml`（P0-13）— 同上
4. `contracts/readiness-report.contract.yaml`（P0-13）— 同上
5. `docs/team-reference-design.md`（P1-4）— 纯设计文档，不写代码

**除此之外，一律"修改现有"**。

### 严禁的行为

- ❌ 引申到没列出的其他文件
- ❌ 顺手"优化"看起来相关的代码
- ❌ 加"防御性"改动（除非 FIX 明确要求）
- ❌ 想"加个辅助检查 / 字段 / 段落 / skill" → **停下问用户**
- ❌ 死代码扫到了就顺手删（除非本 FIX 的目标就是那个死代码）

### 每条 FIX 完成后必须

1. 跑 `verify` 段的所有命令，都通过才算完成
2. 单独 commit，commit message 用 FIX 里给的
3. 不做 verify 写 `# SKIP: reason` 而不是直接跳过
4. 进下一条前检查 `git status` 是干净的

### 遇到问题时

- 现状和描述不一致 → **停下问用户**，不要猜测修复
- verify 命令失败 → 先 revert 本条 FIX，再问用户
- 一条 FIX 触达的文件比列的多 → **停下问用户**，可能 FIXES.md 漏写了
- 突然想加个"辅助文件/字段/段落"（不在本 FIXES.md 明确列出的）→ **停下问用户**

### 执行节奏建议

- P0-1 → P0-14 做完后先停一下，用户验证在 dive-bff 重跑一遍 `/prd-distill`
- 确认 dive-bff 产物符合预期后，再做 P1 和 P2
- 预估：P0 ~6h，P1 ~2.5h，P2 ~30min，总计 ~9h

---

## 总览

| # | 优先级 | 标题 | 触达文件数 | 预计耗时 |
|---|---|---|---|---|
| P0-1 | P0 | ai-friendly-prd 强制 13 段英文标题 + `### REQ-XXX` 锚点 | 3 | 30min |
| P0-2 | P0 | evidence 双账本合并为单一权威源 | 2 | 20min |
| P0-3 | P0 | schemas/03-context.md 的 schema_version 示例全部升到 contract 同步的版本 | 1 | 15min |
| P0-4 | P0 | 脚本参数命名统一为 `--distill-dir` + `--repo-root` | 2 | 15min |
| P0-5 | P0 | `distill-step-gate.py` 写 state 时正确更新 current_step | 1 | 10min |
| P0-6 | P0 | 恢复 v2.16.0 的"全栈契约建议"（前端/BFF/后端） | 4 | 40min |
| P0-7 | P0 | layer-impact.yaml 必须包含 frontend/bff/backend/external 四键并列 | 4 | 45min |
| P0-8 | P0 | 03-contracts.yaml 恢复 producer/consumers[]/checked_by[] 数组语义，弃用 direction 单字符串 | 3 | 30min |
| P0-9 | P0 | plan.md §7 校验规则矩阵 + §9 契约对齐表强制分层填写 | 2 | 25min |
| P0-10 | P0 | reference 04-routing-playbooks.yaml 恢复 cross_repo_handoffs 填充 | 2 | 30min |
| P0-11 | P0 | report.md / plan.md 章节强制按 schema 11-12 段生成，禁止自创 | 3 | 30min |
| P0-12 | P0 | reference-update-suggestions.yaml 字段完整填写（恢复 12 字段 schema） | 3 | 25min |
| P0-13 | P0 | evidence.yaml / alignment_summary / readiness schema 字段漂移全面修复 | 4 | 35min |
| P0-14 | P0 | 恢复 reference 人类可读性：枚举 label + see_enum 去重机制 | 5 | 40min |
| P1-1 | P1 | 新增 `scripts/ingest-docx.py` 取代手写 XML 解析 | 1 new | 40min |
| P1-2 | P1 | plan.md / report.md schema 写死 must-contain 段 | 3 | 25min |
| P1-3 | P1 | Step 8.6 "Completion Gate" 要么补实际检查要么删 | 2 | 15min |
| P1-4 | P1 | 新增"团队级公共 reference"机制（跨仓沉淀 + 继承） | 多 | 2h |
| P2-1 | P2 | context-pack.md 加 "必引用段落" 标识 | 2 | 15min |
| P2-2 | P2 | step-03-confirm.md 内嵌 HARD STOP 指令 | 1 | 10min |

合计 19 条，~9 小时。

> **全栈回归大背景（P0-6 至 P0-10 + P1-4）**：v2.16.0 originally 设计为 frontend/bff/backend 三层对等的知识沉淀工具。v2.17-v2.18.x 大迭代中 focus 集中在 BFF 场景（dive-bff），**模板字段大多保留**，但 **step 指令、contract validator、workflow 约束全部弱化**——结果是模板里字段还在但模型不填了（"静默降级"）。领导规划"通过 reference 构建 B 端营销全团队公共知识库（前端 + BFF + 后端）"，本修复清单的 P0-6 至 P0-10 + P1-4 就是为这个愿景重建地基。

---

## P0-1 — ai-friendly-prd 强制 13 段英文标题 + `### REQ-XXX` 锚点

### 现象

实跑时，模型先按 `spec/ai-friendly-prd.md §1 ~ §13`（中文章节）写完，到 `distill-quality-gate.py` 校验时因 `REQUIRED_SECTIONS` 是 13 个英文标准名 (`Overview`, `Problem Statement`, ...) 而 fail，不得不整篇重写。重写后又引入下一层问题：

- `requirement-ir.yaml` 的 `ai_prd_req_id: "CFG-001"` 在 ai-friendly-prd.md 里**找不到** `### CFG-001` 锚点。实际锚点变成了 `### FR-2: 配置页面基础信息（REQ-ID: CFG-001, source: explicit）` 这种复合标题——grep `^### CFG-001` 返回 0。
- 追溯链完全断裂，和下午 audit 的 P0-6 一模一样复现。

### 证据

- `scripts/distill-quality-gate.py:50-64` — `REQUIRED_SECTIONS` 列表（13 个英文段）
- `plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md:147` — 已有要求 "IR 的 ai_prd_req_id 必须在 ai-friendly-prd.md 中 grep 命中"，但**未要求是独立 `### REQ-XXX` 标题**
- `plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml` — 当前只要求 `min_h2: 13` 和 `pattern: "REQ-\\d+"`，太弱
- 实跑产物：`/Users/didi/work/dive-bff/_prd-tools/distill/gas-new-driver-coupon/spec/ai-friendly-prd.md` 的 `### FR-2` 里嵌了 `CFG-001`，但 IR 里的 `ai_prd_req_id: CFG-001` 搜不到独立锚点

### 修复

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md`

找到现有的 "ai-friendly-prd.md 生成" 段落，补上两条硬规则：

- **13 段必须用英文标准名**：Overview, Problem Statement, Target Users, Goals & Success Metrics, User Stories, Functional Requirements, Non-Functional Requirements, Technical Considerations, UI/UX Requirements, Out of Scope, Timeline & Milestones, Risks & Mitigations, Open Questions。顺序固定，不得翻译，不得合并。
- **每个 REQ-XXX 必须是独立 `### REQ-XXX` 三级标题锚点**：在 Functional / Non-Functional / Technical / UI/UX / Open Questions 这 5 段内，每条需求必须形如：
  ```
  ### REQ-CFG-001

  **Source**: explicit
  **Priority**: P0
  ...
  ```
  标题只放 `### REQ-XXX`，描述性文字放正文。不得写成 `### FR-2: 配置页面基础信息（REQ-ID: CFG-001）` 这种复合标题。

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml`

替换现有 rules 为：

```yaml
artifact: "spec/ai-friendly-prd.md"
schema_version: "2.0"
type: "markdown"
rules:
  - id: "has_13_standard_sections"
    type: "headings_equal"
    level: 2
    values:
      - "Overview"
      - "Problem Statement"
      - "Target Users"
      - "Goals & Success Metrics"
      - "User Stories"
      - "Functional Requirements"
      - "Non-Functional Requirements"
      - "Technical Considerations"
      - "UI/UX Requirements"
      - "Out of Scope"
      - "Timeline & Milestones"
      - "Risks & Mitigations"
      - "Open Questions"
    order_matters: true

  - id: "req_ids_have_heading_anchors"
    type: "req_id_anchor_match"
    ir_file: "context/requirement-ir.yaml"
    ir_field: "requirements[].ai_prd_req_id"
    heading_pattern: "^### (REQ-[A-Z0-9_-]+)$"
    note: "每个 ai_prd_req_id 必须在 ai-friendly-prd.md 中有独立 `### REQ-XXX` 三级标题"
```

#### 3. 更新 `scripts/distill-quality-gate.py`

在现有 `_check_afprd_sections` 函数后新增 `_check_req_id_anchors`：

```python
def _check_req_id_anchors(base):
    """Check each ai_prd_req_id in requirement-ir.yaml has a ### REQ-XXX heading in ai-friendly-prd.md."""
    import re, yaml
    afprd_path = os.path.join(base, 'spec/ai-friendly-prd.md')
    ir_path = os.path.join(base, 'context/requirement-ir.yaml')
    if not os.path.isfile(afprd_path) or not os.path.isfile(ir_path):
        return {'status': 'skip', 'reason': 'files missing'}

    with open(afprd_path) as f:
        afprd_text = f.read()
    with open(ir_path) as f:
        ir = yaml.safe_load(f) or {}

    headings = set(re.findall(r'^### (REQ-[A-Z0-9_-]+)\s*$', afprd_text, re.MULTILINE))
    missing = []
    for req in (ir.get('requirements') or []):
        afprd_id = req.get('ai_prd_req_id', '')
        for aid in [x.strip() for x in afprd_id.split(',') if x.strip()]:
            normalized = aid if aid.startswith('REQ-') else f'REQ-{aid}'
            if normalized not in headings and aid not in headings:
                missing.append({'ir_id': req.get('id'), 'ai_prd_req_id': aid})

    return {
        'status': 'pass' if not missing else 'fail',
        'total_heading_anchors': len(headings),
        'missing': missing,
    }
```

并在 `results` 装配处（约 line 441 `results['afprd_sections'] = ...` 附近）追加：

```python
results['req_id_anchors'] = _check_req_id_anchors(base)
```

以及 summary 列表（约 line 473）追加 `('req_id_anchors', 'REQ-ID heading anchors')`。

### verify

```bash
# 新 ai-friendly-prd 13 段英文标题
grep -cE "^## (Overview|Problem Statement|Target Users|Goals & Success Metrics|User Stories|Functional Requirements|Non-Functional Requirements|Technical Considerations|UI/UX Requirements|Out of Scope|Timeline & Milestones|Risks & Mitigations|Open Questions)$" <fixture ai-friendly-prd.md>
# 期望：13

# REQ 锚点
grep -cE "^### REQ-" <fixture ai-friendly-prd.md>
# 期望：>=10

# contract 通过
python3 scripts/validate-artifact.py --artifact <fixture>/spec/ai-friendly-prd.md --contract plugins/prd-distill/skills/prd-distill/references/contracts/ai-friendly-prd.contract.yaml
```

### commit

```
fix(audit-p0): [P0-1] enforce 13 english sections + ### REQ-XXX heading anchors in ai-friendly-prd
```

---

## P0-2 — evidence 双账本合并为单一权威源

### 现象

实跑产物有**两本 evidence 账**：

- `_ingest/evidence-map.yaml` — 12 条 (`EV-BG-01`, `EV-CFG-01~05`, `EV-QRY-01` …)，由 Step 0 生成
- `context/evidence.yaml` — 7 条 (`EV-INGEST-01/02`, `EV-REF-001~004`, `EV-REF-CONSUMED`)，由 Step 1 生成

`requirement-ir.yaml` 引用的 `EV-CFG-03` 只存在于 `_ingest/evidence-map.yaml`；`EV-REF-001` 只存在于 `context/evidence.yaml`。两边没有合并索引。下游 portal / context-pack 要两处查，容易遗漏。

### 证据

- `_ingest/evidence-map.yaml` 定义 12 条
- `context/evidence.yaml` 定义 7 条（完全不重合）
- `context/requirement-ir.yaml` 引用的 9 个 EV-ID 跨两本账

### 修复

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md`

在 "Step 1 Evidence Ledger" 段明确：

> `context/evidence.yaml` 是**唯一权威 evidence 账本**。必须包含以下三类条目：
>
> 1. 原始 PRD block（从 `_ingest/evidence-map.yaml` 全量复制 `EV-BG-*`, `EV-CFG-*`, `EV-VIS-*` 等）
> 2. Ingestion 证据（`EV-INGEST-*`：文本提取、图片分析）
> 3. Reference 消费证据（`EV-REF-*`：消费 `_prd-tools/reference/*.yaml` 的摘要）
>
> `_ingest/evidence-map.yaml` 是 ingestion 阶段的原始产物，仅用于 step-0 输出验证，**不得被 requirement-ir.yaml / layer-impact.yaml / contract-delta.yaml 引用**。

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md`

在 `context/evidence.yaml` 小节顶部加 NOTE：

```markdown
> **单一权威源原则**：evidence.yaml 是所有下游产物（requirement-ir、layer-impact、contract-delta、report、plan）引用的**唯一 evidence 账本**。`_ingest/evidence-map.yaml` 仅用于 ingestion 追溯，不得被下游直接引用。
```

#### 3. 可选增强（如时间够）

`scripts/distill-step-gate.py` 的 Step 2 prerequisite 检查加一条：

```python
# Verify evidence.yaml includes all EV-IDs from evidence-map.yaml
```

### verify

```bash
# evidence.yaml 的 EV-ID 应该 ⊇ evidence-map.yaml 的 EV-ID
comm -23 <(grep -oE "id: EV-[A-Z0-9-]+" <fixture>/_ingest/evidence-map.yaml | sort) \
         <(grep -oE "id: EV-[A-Z0-9-]+" <fixture>/context/evidence.yaml | sort)
# 期望：空输出
```

### commit

```
fix(audit-p0): [P0-2] evidence.yaml as single source of truth, evidence-map.yaml read-only
```

---

## P0-3 — schemas/03-context.md 的 schema_version 与 contract 对齐

### 现象

下午 audit 的 P0-1 只修了 `contracts:` → `deltas:` 的顶层键，但 `schemas/03-context.md` 里的 `schema_version` 示例仍然混乱：

| 位置 | 当前值 | 对应 contract 期望 |
|---|---|---|
| `schemas/03-context.md:52` (evidence) | `"4.0"` | evidence 当前无独立 contract |
| `schemas/03-context.md:73` (requirement-ir) | `"5.0"` | `requirement-ir.contract.yaml:2` 要求 `"2.0"` |
| `schemas/03-context.md:144` (layer-impact) | `"5.0"` | `layer-impact.contract.yaml:2` 要求 `"2.0"` |
| `schemas/03-context.md:194` (contract-delta) | `"4.0"` | `contract-delta.contract.yaml:5` 要求 `"2.0"` |

模型按 schemas/03-context.md 写了 `schema_version: "5.0"`，被 contract validator 打回要 `"2.0"`，整文件重写。

### 证据

- `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md:52,73,144,194`
- `plugins/prd-distill/skills/prd-distill/references/contracts/*.contract.yaml` 全部是 `schema_version: "2.0"`

### 修复

更新 `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md` 的 4 处 `schema_version`：

| 行号 | 改为 |
|---|---|
| 52 (evidence) | `"2.0"` |
| 73 (requirement-ir) | `"2.0"` |
| 144 (layer-impact) | `"2.0"` |
| 194 (contract-delta) | `"2.0"` |

> **原则**：schemas/*.md 的示例版本必须与对应 `contracts/*.contract.yaml` 的 `schema_version` **完全一致**。未来升版本时两边同步。在 03-context.md 顶部加一段：
>
> ```
> > **版本同步规则**：本文件中每个 schema 的 `schema_version` 必须与 `references/contracts/<name>.contract.yaml` 的 `schema_version` 一致。升版时两边同步修改，并记入 CHANGELOG。
> ```

### verify

```bash
# 提取 03-context.md 中所有 schema_version 值，应全部是 "2.0"
grep -nE '^schema_version: "' plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md
# 期望：4 行全部 "2.0"

# 提取 contracts/*.contract.yaml 中 schema_version，应全部是 "2.0"
grep -nE '^schema_version: "' plugins/prd-distill/skills/prd-distill/references/contracts/*.contract.yaml
# 期望：4 行全部 "2.0"
```

### commit

```
fix(audit-p0): [P0-3] align schemas/03-context.md schema_version with contracts (all 2.0)
```

---

## P0-4 — 脚本参数命名统一

### 现象

实跑时模型连续三次试错：

```bash
python3 .prd-tools/scripts/context-pack.py --distill-dir _prd-tools/distill/xxx --repo-root . --index-dir _prd-tools/reference/index
# error: unrecognized arguments: --repo-root . --index-dir _prd-tools/reference/index

python3 .prd-tools/scripts/context-pack.py --help
# 发现是 --distill 和 --index

python3 .prd-tools/scripts/context-pack.py --distill _prd-tools/distill/xxx --index _prd-tools/reference/index
# 终于成功
```

三个脚本的命名约定不一致：

| 脚本 | 当前参数 |
|---|---|
| `distill-step-gate.py` | `--distill-dir`, `--repo-root` |
| `distill-workflow-gate.py` | `--distill-dir`, `--repo-root` |
| `final-quality-gate.py` | `--distill-dir` |
| **`context-pack.py`** | **`--distill`** (alias `--distill-dir`), `--index` |
| `render-distill-portal.py` | `--distill-dir`, `--template` |

`context-pack.py` 在 line 815 实际上已经 `add_argument('--distill', '--distill-dir', dest='distill')` 支持 alias，但 `--index` vs `--index-dir` 没有 alias。

### 修复

#### 1. 更新 `scripts/context-pack.py`

```python
# 约 line 817
ap.add_argument('--index', '--index-dir', dest='index', required=False,
                help='Path to evidence index directory (default: <distill>/../reference/index)')
```

#### 2. 检查其他脚本，统一为双向 alias

在每个有 `--distill-dir` 的脚本里，把 `add_argument('--distill-dir', ...)` 改成 `add_argument('--distill-dir', '--distill', dest='distill_dir', ...)`（保持 dest 不变以免其他地方引用），已经支持 alias 的保留。

需要检查：
- `scripts/distill-step-gate.py`
- `scripts/distill-workflow-gate.py`
- `scripts/final-quality-gate.py`
- `scripts/render-distill-portal.py`
- `scripts/validate-artifact.py`

> **原则**：所有 distill 脚本接受 `--distill-dir`（主）和 `--distill`（alias）。所有 index 相关脚本接受 `--index-dir`（主）和 `--index`（alias）。所有 repo root 相关脚本接受 `--repo-root`（主）和 `--repo`（alias）。

#### 3. 更新 `.claude/commands/prd-distill.md`

把 "Step IDs" 下方的所有示例命令行统一用 `--distill-dir` + `--repo-root`。

### verify

```bash
# 任一脚本都应接受 --distill-dir
python3 scripts/context-pack.py --distill-dir /tmp/x --index-dir /tmp/y 2>&1 | grep -v "unrecognized"

# 所有 distill 脚本 help 应包含 --distill-dir
for f in scripts/distill-*.py scripts/context-pack.py scripts/final-quality-gate.py scripts/render-distill-portal.py; do
  python3 "$f" --help 2>&1 | grep -q "distill-dir" || echo "MISSING in $f"
done
```

### commit

```
fix(audit-p0): [P0-4] unify CLI args --distill-dir/--index-dir/--repo-root across scripts
```

---

## P0-5 — distill-step-gate.py 写 state 时未更新 current_step

### 现象

实跑结束后 `workflow-state.yaml` 的状态：

```yaml
current_step: '1'           # 应该是 '9'（最后完成的 step）或 'completed'
current_stage: plan
status: in_progress         # 应该是 completed
completed_steps:
  - step: '0' ... passed
  - step: '1' ... passed
  ...
  - step: '9' ... passed    # 18 条都 passed
resume:
  next_step: completed      # 这里倒是对的
  next_action: completed
```

`current_step` 写死在 "1"，跟实际进度脱节。靠 `resume.next_step` 兜底用户能看出是完成了，但 `status` 还是 `in_progress` 会误导。

### 证据

- `/Users/didi/work/dive-bff/_prd-tools/distill/gas-new-driver-coupon/workflow-state.yaml:5-8`
- `scripts/distill-step-gate.py:297-305` — `_get_next_step` 计算了 next，但 write-state 时没回写 `current_step`

### 修复

定位 `scripts/distill-step-gate.py` 的 state 写入逻辑（应在 `--write-state` 分支附近）：

```python
# 当前伪代码（假设）
if args.write_state:
    state = load_state(...)
    state['completed_steps'].append({...})
    # 缺失这两行 ↓
    state['current_step'] = args.step        # 当前刚完成的 step
    if _get_next_step(args.step) == 'completed':
        state['status'] = 'completed'
        state['current_stage'] = 'completed'
    save_state(state, ...)
```

具体改法先读现有代码，把"追加 completed_steps"和"更新 current_step / status"做在同一个 write 事务里。

### verify

```bash
# 跑完一次完整 distill 后检查
python3 -c "
import yaml
s = yaml.safe_load(open('<fixture>/workflow-state.yaml'))
assert s['current_step'] == '9', f\"expected 9, got {s['current_step']}\"
assert s['status'] == 'completed', f\"expected completed, got {s['status']}\"
print('OK')
"
```

### commit

```
fix(audit-p0): [P0-5] distill-step-gate writes current_step/status alongside completed_steps
```

---

## P0-6 — 恢复 v2.16.0 的"全栈契约建议"（前端/BFF/后端三方）

### 现象

v2.16.0 的 `report.md` / `plan.md` 包含**按层分组的全栈契约建议**：前端契约、BFF→后端契约、后端契约都列出，每条带 `producer` + `consumers[]` + `checked_by[]`，明确"这个契约由谁产出、谁消费、哪些层确认过"。

实跑 v2.18.1 在 dive-bff 产物里这部分**回归丢失**：

- `context/contract-delta.yaml` 每条 delta 是**单一方向** `bff -> frontend`，`producer/consumer` 都是单值字符串，不再是 v2.16.0 的 `producer + consumers: []` 数组结构
- `report.md` §10「契约风险」只剩"列 needs_confirmation 和 blocked 的契约"文字，**没有按层分组**，没有 Producer/Consumer 列
- `plan.md` §9「契约对齐」表头 schema 里还写着 `| 契约 | 状态 | Producer | Consumer | 需确认内容 |` 但模型实跑没生成（因为上游 contract-delta 已是单值，无 Consumer 数组可填）
- 实跑明明源码扫描发现了 `CONTRACT-UPSTREAM-001` 包含 20 个 BFF→后端 API，但 contract-delta.yaml 只生成了 `bff -> frontend` 那一边，后端契约建议**整个丢失**

### 证据

- v2.16.0 schema：`git show v2.16.0:plugins/prd-distill/skills/prd-distill/references/output-contracts.md` line 459-481，`contracts:` 顶层键 + `producer + consumers[] + checked_by[]`
- v2.16.0 plan.md §9 模板：line 299-301 `| 契约 | 状态 | Producer | Consumer | 需确认内容 |`
- 当前 v2.18.1 contract-delta.contract.yaml line 11-19：`required` 不含 `consumers`，validator 不检查
- 当前 schemas/03-context.md line 200 起 contract-delta 示例：模型照抄变成单边
- 当前 output-contracts.md line 381-382 report.md §10 仅"列 needs_confirmation 和 blocked"，无分组要求
- 当前 04-report-plan.md schema line 211-213 plan.md §9 表头还在但缺执行细节
- 实跑产物 `/Users/didi/work/dive-bff/_prd-tools/distill/gas-new-driver-coupon/context/contract-delta.yaml` 全部 8 条 delta 都是 `direction: "bff -> frontend"` 或单一 `bff -> backend`，无 `consumers[]` 数组

### 修复

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/references/contracts/contract-delta.contract.yaml`

补强 required 字段：

```yaml
artifact: "context/contract-delta.yaml"
schema_version: "2.0"
required_top_level:
  - meta
  - schema_version
  - deltas
rules:
  - id: "delta_has_full_stack"
    each: "deltas"
    required:
      - id
      - producer
      - consumers          # 新增：必须是数组
      - change_type
      - alignment_status
      - requirement_id
      - layer
      - contract_surface

  - id: "consumers_is_array_of_layers"
    each: "deltas"
    require: "isinstance(consumers, list) and all(c in ['frontend','bff','backend','external'] for c in consumers)"

  - id: "checked_by_optional_array"
    each: "deltas"
    when:
      field: "checked_by"
      exists: true
    require: "isinstance(checked_by, list)"
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md`

contract-delta 段（约 line 194-230）的示例改为：

```yaml
schema_version: "2.0"
meta:
  primary_source: "_ingest/document.md"
  ai_prd_source: "spec/ai-friendly-prd.md"
  requirement_ir_ref: "context/requirement-ir.yaml"
deltas:
  - id: "CD-001"
    name: "新活动类型创建接口"
    requirement_id: "REQ-001"
    layer: "bff"
    producer: "bff"
    consumers: ["frontend", "backend"]   # 数组：所有需要适配此契约的层
    checked_by: ["bff", "frontend"]      # 数组：已确认对齐的层（缺 backend 即代表后端待确认）
    change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
    contract_surface: "endpoint | schema | event | payload | db_table | external_api"
    request_fields:
      - name: ""
        change_type: "ADD | MODIFY | DELETE | NO_CHANGE"
        required: false
        type: ""
        source: "prd | tech_doc | code | inferred"
    response_fields: []
    alignment_status: "aligned | needs_confirmation | blocked | not_applicable"
    evidence_refs: ["EV-001"]
    cross_layer_notes: ""
alignment_summary:
  status: "aligned | needs_confirmation | blocked | not_applicable"
  by_layer:
    frontend: { aligned: N, needs_confirmation: N, blocked: N }
    bff:      { aligned: N, needs_confirmation: N, blocked: N }
    backend:  { aligned: N, needs_confirmation: N, blocked: N }
  blockers: []
  next_actions: []
```

并在该段头部加一段说明：

```markdown
> **全栈契约原则**：每条 delta 必须明确 `producer`（单一产出层）、`consumers`（受影响的所有层数组）、`checked_by`（已对齐的层数组）。`consumers - checked_by` 即为"待确认层"，必须进入 report.md §10 的"按层分组建议"。
> **不允许** 用单一 `direction: "bff -> frontend"` 字符串替代 producer/consumers 结构——多端协作信息会丢失。
```

#### 3. 更新 `plugins/prd-distill/skills/prd-distill/references/output-contracts.md`（同时更新对应的 `references/schemas/04-report-plan.md`）

把 report.md §10「契约风险」**改为「契约对齐与建议」**，模板改为：

```markdown
## 10. 契约对齐与建议

按受影响层分组列出，**每层都要有自己的小段**（即使为空也要显式写"无变更"）：

### 10.1 前端契约（frontend as consumer/producer）
| 契约ID | 类型 | 当前状态 | 需前端确认 | 建议 Owner |
|---|---|---|---|---|
| CD-001 | endpoint (新增) | needs_confirmation | 表单字段命名、组件类型 | 前端 owner |

### 10.2 BFF 契约（bff as producer or middleware）
| 契约ID | 类型 | 当前状态 | 需BFF对齐项 | 建议 Owner |
|---|---|---|---|---|
| CD-002 | schema 联动 | aligned | - | - |

### 10.3 后端契约（backend as producer/consumer）
| 契约ID | 类型 | 当前状态 | 需后端确认 | 建议 Owner |
|---|---|---|---|---|
| CD-006 | upstream API | needs_confirmation | 枚举值、字段命名、新格式解析归属 | 后端 owner |

### 10.4 外部系统契约（external，可选）
仅当 `consumers` 含 `external` 时出现。如券系统、折扣卡系统、Push 系统、D-chat 等。

### 10.5 跨层对齐风险
- `consumers - checked_by` 不为空的契约必须出现在以上分组的"需确认"列
- `alignment_status: blocked` 的契约必须同时进入 §12 阻塞问题
```

plan.md §9 同步改为「契约对齐」全栈表：

```markdown
## 9. 契约对齐（全栈视图）

| 契约ID | Producer | Consumers | Checked By | 状态 | 需确认内容 |
|---|---|---|---|---|---|
| CD-001 | bff | [frontend, backend] | [bff] | needs_confirmation | 前端字段命名 + 后端新枚举值 |

只列 needs_confirmation 和 blocked。aligned 项可省略。
```

#### 4. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-02-classify.md`（contract-delta 生成步骤）

在 contract-delta 生成段加硬规则：

```markdown
- 每条 delta 的 `consumers` 必须是数组，至少包含 1 个除 producer 之外的层
- 同一契约影响多端时（如新增 endpoint 同时改前端调用 + 后端实现），**必须生成一条 delta 含 `consumers: [frontend, backend]`**，禁止拆成两条单边 delta
- 已对齐的层放入 `checked_by`，未对齐的层差集进入 report.md §10 对应小段
```

并在 step-03-confirm.md report.md 生成段的 self-check 加：

```markdown
- [ ] [M] report.md §10 含至少 4 个小段（前端/BFF/后端/外部），即使某层无变更也要显式写"无"
- [ ] [M] plan.md §9 全栈表包含 Producer/Consumers/Checked By 三列
```

### verify

```bash
# contract-delta 至少有一条 delta 的 consumers 数组长度 >= 2
python3 -c "
import yaml
c = yaml.safe_load(open('<fixture>/context/contract-delta.yaml'))
multi = [d for d in c['deltas'] if isinstance(d.get('consumers'), list) and len(d['consumers']) >= 2]
assert multi, 'expected at least one delta with consumers >= 2 layers'
print(f'OK: {len(multi)} multi-layer deltas')
"

# report.md §10 含 4 个分层小段
grep -cE "^### 10\.[1-4] (前端|BFF|后端|外部)" <fixture>/report.md
# expected: 4

# plan.md §9 表头含 Producer + Consumers + Checked By
grep -E "Producer.*Consumers.*Checked By" <fixture>/plan.md
# expected: 1 行命中
```

### relates_to

v2.16.0 的全栈契约设计；v2.18.1 P0R2-6 修 `contracts:` → `deltas:` 时**未保留** `consumers[]/checked_by[]` 的数组语义；本 fix 恢复多端协作能力。

### commit

```
fix(audit-p0): [P0-6] restore v2.16.0 full-stack contract suggestions (frontend/bff/backend grouping)
```

---

## P0-7 — layer-impact.yaml 必须包含 frontend/bff/backend/external 四键并列

### 现象

v2.16.0 的 `layer-impact.yaml` schema 是 `layers: { frontend: {impacts: []}, bff: {impacts: []}, backend: {impacts: []} }` 三层对等；生成时**无论哪层有没有影响都要显式列出**（空数组也写），让人一眼看清"这次需求动到的是哪几层"。

实跑 v2.18.1 在 dive-bff 的产物：

```yaml
layers:
  bff:
    capability_areas:
      - id: IMP-001
      ...  # 10 条全是 bff
```

**只有 `bff:` 一个 key**，完全没有 `frontend:` / `backend:` / `external:`。但这次 PRD 明明涉及：

- 前端：新增活动类型卡片、奖励表组件、券/卡切换联动、Push 占位符渲染
- 后端：CampaignType=44 枚举、EventRule 格式解析、D-chat 预算告警、DLP/冲单挑战数据接口
- 外部：油站券系统、折扣卡系统、ditag、Push 系统

三方影响都在 report.md §5-§8 被提到了，但 **layer-impact.yaml 作为结构化 IR 完全不承载这些**，下游 plan.md 的分层 checklist 也就无法按前端/后端任务分组给出。

### 根因

1. `contracts/layer-impact.contract.yaml:3-5` 的 `required_top_level` 只要 `layers`，**未要求 `layers` 下必须含 frontend/bff/backend** 三个 key
2. `schemas/03-context.md:144` 的 layer-impact 示例虽然写了三层，但没加"必须都存在"注释
3. `steps/step-02-classify.md` 第 80-97 行说"按适配器 surface 记录 Layer Impact"，**没说每个 REQ 要同时判断三层影响**
4. `references/layer-adapters.md` 虽然完整列出三层 surface 表，但 step 文件没强制"对每个 REQ 必须做 3×N_surfaces 遍历"

### 修复

> **设计原则**：本 FIX 是**恢复 v2.16.0 四层结构**，**不引入新字段**。所有"是否本仓扫描"、"是否已确认"、"置信度"的语义都复用现有字段：
> - `project-profile.yaml:layer` → 当前仓所属层（v2.16 已有）
> - `layer-impact.yaml layers.*.capability_areas[].code_anchors[].source: "graph | rg | reference | inferred"` → 证据来源（v2.16 已有）
> - `requirement-ir.yaml` 的 `confirmation.status` → 已有枚举 `confirmed | needs_confirmation | blocked`，本 FIX 复用到 layer-impact（允许字段跨文件）
> - `confidence: high | medium | low` → 置信度（v2.16 已有）
> - `fallback_reason` → v2.16 contract 已有
>
> **不新增** `current_repo_layer` / `scan_source` / `confirmation_status` / `proposed_location` 字段。用现有字段表达相同语义。

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/references/contracts/layer-impact.contract.yaml`

```yaml
artifact: "context/layer-impact.yaml"
schema_version: "2.0"
required_top_level:
  - schema_version
  - layers

rules:
  - id: "all_four_layers_present"
    require: "'frontend' in layers and 'bff' in layers and 'backend' in layers and 'external' in layers"
    severity: fail
    fix_hint: "layer-impact.yaml 必须同时含 frontend/bff/backend/external 四个 key。无影响的层显式写 'capability_areas: []  # no impact' 并注明原因"

  - id: "impact_has_req_id"
    each: "layers.*.capability_areas"
    required:
      - id
      - requirement_id
      - change_type
      - code_anchors

  - id: "code_anchors_or_fallback"
    each: "layers.*.capability_areas"
    require: "len(code_anchors) > 0 or fallback_reason exists"

  # 使用 requirement-ir 已有的 confirmation.status 字段，不引入新字段
  - id: "non_current_layer_needs_confirmation"
    each: "layers.*.capability_areas"
    when:
      field: "code_anchors[0].source"
      equals: "inferred"
    require: "confirmation.status == 'needs_confirmation'"
    note: "非本仓层的 IMP（source=inferred）必须继承 requirement-ir 已有的 confirmation.status 字段标为 needs_confirmation"
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/references/schemas/03-context.md`

layer-impact 示例改为：

```yaml
schema_version: "2.0"
meta:
  primary_source: "_ingest/document.md"
  # 当前仓所属层从 _prd-tools/reference/project-profile.yaml 的 layer 字段读，不在此重复
summary: ""

layers:
  # 所有 4 个 key 必须存在，即使为空
  frontend:
    capability_areas:
      - id: "IMP-FE-001"
        requirement_id: "REQ-001"
        change_type: "ADD | MODIFY | DELETE"
        surface: "ui_route | view_component | form_or_schema | ..."
        target: "src/pages/campaign/..."     # 沿用现有 target 字段，非本仓时填"建议位置"
        confidence: "medium"                  # 非当前仓默认 medium 或 low（现有字段）
        confirmation:                         # 复用 requirement-ir 已有的 confirmation 结构
          status: "needs_confirmation"        # 现有枚举 confirmed | needs_confirmation | blocked
          reason: "前端仓未挂载，基于 PRD + reference 推断"
        code_anchors:
          - source: "inferred"                # 复用现有 source 枚举 graph|rg|reference|inferred
            confidence: "medium"
            evidence: "基于 PRD UI 截图 + reference/04-routing-playbooks 的 frontend layer_steps"
        fallback_reason: "前端仓不在本地扫描范围内"

  bff:
    capability_areas:
      - id: "IMP-BFF-001"
        requirement_id: "REQ-001"
        change_type: "ADD"
        surface: "schema_or_template"
        target: "src/config/template/render/rules/details/"
        confidence: "high"
        confirmation:
          status: "confirmed"
        code_anchors:
          - file: "src/config/constant/campaignType.ts"
            line_start: 57
            line_end: 58
            symbol: "CampaignType"
            source: "rg"                      # 当前仓扫描得到
            confidence: "high"

  backend:
    capability_areas:
      - id: "IMP-BE-001"
        requirement_id: "REQ-001"
        change_type: "ADD"
        surface: "api_surface"
        target: "后端 magellan 仓 /campaign/create 附近"
        confidence: "low"
        confirmation:
          status: "needs_confirmation"
          reason: "后端仓不在本地，基于 reference/03-contracts CONTRACT-UPSTREAM-001 推断"
        code_anchors:
          - source: "inferred"
            confidence: "low"
            evidence: "reference/03-contracts.yaml 的 consumer_repos"
        fallback_reason: "后端仓不在本地扫描范围内"

  external:
    capability_areas: []     # 明确声明无外部系统变更

quality_gates: []
```

在已有的 `强绑定规则:` 段末尾（`schemas/03-context.md` 已有此段）追加一行即可，不单独加 NOTE 段：

```markdown
- **四层对等**：无论分析哪个仓，`layers` 下必须同时含 frontend/bff/backend/external 四 key（空层写 `capability_areas: []`）。非本仓层的 IMP 复用 `code_anchors[].source: "inferred"` + `confirmation.status: "needs_confirmation"` 标注（无需新字段）。
```

#### 3. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-02-classify.md`

在 Layer Impact 生成段加：

```markdown
### 三层影响强制分析

对每个 requirement，**必须按下列顺序分别判断 4 层**：

1. **frontend 影响**：这个需求会让前端 UI / 组件 / 表单 / 路由 / 客户端契约产生什么变化？
   - 若当前仓是 frontend：扫码填 code_anchors
   - 若不是：查 reference/03-contracts.yaml 的 frontend consumer 记录、reference/04-routing-playbooks 的 frontend layer_steps，推断 proposed_location
2. **bff 影响**：同上
3. **backend 影响**：同上
   - 即使本地没有后端仓，只要 PRD 提到数据/接口/枚举/校验/预算等后端职责，就必须生成 `IMP-BE-*` 条目
4. **external 影响**：涉及第三方系统（券、折扣卡、Push、DMS、权益、风控等）必须生成 `IMP-EXT-*`

**硬规则**：
- 4 个 layer key 必须同时存在于 layer-impact.yaml
- 空数组要显式写 `capability_areas: []` 并加 comment 说明理由
- 非当前仓层的 IMP confidence 不得 high，必须 needs_confirmation
```

#### 4. 不需要新 check 函数 —— 已覆盖

> **避免膨胀**：`all_four_layers_present` 已在 contract yaml 里定义（见 #1），`validate-artifact.py` 会读 contract 规则自动执行。**不需要**在 `distill-quality-gate.py` 再写 `_check_all_layers_present` 函数。
>
> 如果 validate-artifact.py 当前不支持 `require:` 表达式（只支持 `required:` 列表），则加到现有的 `required_top_level` 扩展语义。不新建函数。

### verify

```bash
# 4 个 key 必须都在
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/layer-impact.yaml'))
layers = d['layers']
for k in ['frontend', 'bff', 'backend', 'external']:
    assert k in layers, f'missing {k}'
print('OK: all 4 layers present')
"

# 非当前仓层的 IMP 必须 needs_confirmation
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/layer-impact.yaml'))
current = d.get('meta', {}).get('current_repo_layer', 'bff')
for name, layer in d['layers'].items():
    if name == current: continue
    for imp in layer.get('capability_areas') or []:
        assert imp.get('confirmation_status') == 'needs_confirmation', f'{imp[\"id\"]} should be needs_confirmation'
print('OK')
"
```

### commit

```
fix(audit-p0): [P0-7] layer-impact.yaml requires all 4 layers (frontend/bff/backend/external) with scan_source
```

---

## P0-8 — 03-contracts.yaml 恢复 producer/consumers[]/checked_by[] 数组，弃用 direction 单字符串

### 现象

v2.16.0 的 reference `templates/03-contracts.yaml` 设计原本就是**全栈契约**：

```yaml
contracts:
  - id: "CONTRACT-001"
    producer: "bff"
    consumers: ["frontend", "backend"]      # 数组
    checked_by: ["bff", "frontend"]          # 已确认的层
    producer_repo: ""                        # 团队公共库用的跨仓字段
    consumer_repos: []                       # 每个 consumer 的仓库/角色/确认状态
    team_reference_candidate: false
    team_scope: { type, related_repos, aggregation_status }
```

v2.18.1 的**模板文件还保留这些字段**（`plugins/reference/skills/reference/templates/03-contracts.yaml:18,21,40-44`），但 **step-02-deep-analysis.md 不再指令模型填写**，结果实际产物 `/Users/didi/work/dive-bff/_prd-tools/reference/03-contracts.yaml` 里：

- 所有 contract 都用 `direction: "frontend → bff"` **单字符串**，不是 producer/consumers[] 结构
- 完全没有 `producer_repo`, `consumer_repos`, `team_reference_candidate`, `team_scope`, `checked_by` 字段
- 上游契约 `CONTRACT-UPSTREAM-001` 那一段有 20 个后端 API 被列出来了，但**没有对应的 `consumer_repos: [{repo: bff, role: bff, verification: confirmed}, {repo: magellan, role: backend, verification: needs_confirmation}]`**

### 根因

- `plugins/reference/skills/reference/steps/step-02-deep-analysis.md` 行 45-48 描述 "03-contracts.yaml 生成" 时未 mention 团队字段
- v2.18.x 迭代把"全栈公共库"降级为"单仓字段表"，但模板字段忘删，形成"字段在、指令无"的静默漂移

### 修复

#### 1. 更新 `plugins/reference/skills/reference/steps/step-02-deep-analysis.md`

找到 `03-contracts.yaml` 生成描述（约 line 45-48），替换为：

```markdown
### 03-contracts.yaml 生成（全栈契约，团队公共库基础）

每个契约条目**必须**填充全栈字段，不得用单一 `direction` 字符串替代：

- `producer`: `"frontend | bff | backend | external"` 单值
- `consumers`: `["frontend", "bff", "backend", "external"]` **数组**（至少 1 个，除 producer 之外）
- `checked_by`: `["bff"]` **数组**，标注哪些层已 verify（未 verify 的层即 "待对齐"）
- `producer_repo`: producer 所在仓库名（团队公共库用来跨仓追踪，如 "dive-bff" / "genos" / "magellan"）
- `consumer_repos`: 每个 consumer 对应的仓库/角色/确认状态
  ```yaml
  consumer_repos:
    - repo: "genos"
      role: "frontend"
      verification: "needs_confirmation"
      owner_to_confirm: "前端 owner @xxx"
      evidence: []
  ```
- `team_reference_candidate`: true/false（是否适合升级到团队公共库）
- `team_scope.related_repos`: 跨仓关联的 repo list（不止一个仓时必填）
- `alignment_status`: `aligned | needs_confirmation | blocked | not_applicable`

**禁止**用 `direction: "frontend → bff"` 单字符串替代上述结构。遇到"这个接口前端调 BFF"时应拆成：`producer: bff, consumers: [frontend], checked_by: [bff], consumer_repos: [{repo: <frontend-repo>, role: frontend, verification: needs_confirmation}]`。

**理由**：团队规划基于 reference 构建 B 端营销全团队公共知识库。没有 producer/consumers[]/repo 结构，无法跨仓聚合同一契约的多视角。
```

#### 2. 更新 `plugins/reference/skills/reference/templates/03-contracts.yaml`

顶部 `boundary` 字段后追加 NOTE：

```yaml
# NOTE: 全栈公共库原则
#   每个 contract 必须用 producer(单值) + consumers(数组) + checked_by(数组) 结构。
#   禁止用 direction: "A→B" 字符串表达。
#   跨仓契约必须填 producer_repo + consumer_repos，为团队公共库聚合做准备。
```

#### 3. 更新 `plugins/reference/skills/reference/steps/step-03-quality-gate.md`

在"契约闭环"检查段加规则：

```markdown
- [ ] [fail] 所有 contracts[].producer 是字符串单值
- [ ] [fail] 所有 contracts[].consumers 是数组且长度 >= 1
- [ ] [fail] 所有 contracts[].checked_by 是数组（可以为空但必须存在）
- [ ] [warn] 使用了 `direction:` 字段的契约需重写为 producer/consumers[]
- [ ] [warn] 跨仓契约（consumers 含非当前仓角色）未填 consumer_repos
```

### verify

```bash
# dive-bff 的 03-contracts.yaml 重新生成后检查
python3 -c "
import yaml
d = yaml.safe_load(open('/Users/didi/work/dive-bff/_prd-tools/reference/03-contracts.yaml'))
for c in d.get('contracts', []):
    assert isinstance(c.get('producer'), str), f'{c[\"id\"]} producer not string'
    assert isinstance(c.get('consumers'), list) and len(c['consumers']) >= 1, f'{c[\"id\"]} consumers empty'
    assert 'checked_by' in c, f'{c[\"id\"]} missing checked_by'
    assert 'direction' not in c, f'{c[\"id\"]} still uses direction'
print(f'OK: all {len(d[\"contracts\"])} contracts use full-stack schema')
"
```

### commit

```
fix(audit-p0): [P0-8] 03-contracts.yaml restore producer/consumers[]/checked_by[] + team repo fields
```

---

## P0-9 — plan.md §7 校验规则矩阵 + §9 契约对齐表强制分层填写

### 现象

`schemas/04-report-plan.md:203-213` plan.md 模板还写着：

```markdown
## 7. 校验规则汇总
| 规则 | 层 | 目标文件 | 错误提示 |
前端/BFF/后端校验规则矩阵。

## 9. 契约对齐
| 契约 | 状态 | Producer | Consumer | 需确认内容 |
```

但实跑产物 `plan.md §7` 和 `§8 校验规则`（章节号偏了）只有 1 个表，全部都是 BFF 层，"层" 列要么都填 `bff` 要么都填 `all`。§9 契约对齐也被风险表替换。

### 根因

step-03-confirm.md 的 plan.md 生成 self-check 没强制"每层至少一行"。

### 修复

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md`

把 plan.md §7 改为更明确的三层矩阵：

```markdown
## 7. 校验规则汇总（分层矩阵）

**必须分 3 层填，每层至少 1 行**（无规则时显式写 "无" 并注明理由）。

### 7.1 前端校验
| 规则 ID | 规则描述 | 目标文件 | 错误文案 | 来源 |
|---|---|---|---|---|
| VAL-FE-001 | ... | src/pages/... | ... | REQ-xxx |

### 7.2 BFF 校验
| 规则 ID | 规则描述 | 目标文件 | 错误文案 | 来源 |
|---|---|---|---|---|
| VAL-BFF-001 | ... | src/config/... | ... | REQ-xxx |

### 7.3 后端校验
| 规则 ID | 规则描述 | 目标文件 | 错误文案 | 来源 |
|---|---|---|---|---|
| VAL-BE-001 | ... | （后端仓推断）magellan/validator.go | ... | REQ-xxx |

### 7.4 跨层一致性要求
同一业务规则（如 "加油升数 1-99"）在 3 层的校验都要列出，明确**主守层**（通常是 BE）和**快速拦截层**（通常是 FE 或 BFF）。
```

把 §9 改为：

```markdown
## 9. 契约对齐（全栈视图）

| 契约ID | Producer | Consumers | Checked By | 状态 | 需前端确认 | 需BFF确认 | 需后端确认 |
|---|---|---|---|---|---|---|---|
| CD-001 | bff | [frontend, backend] | [bff] | needs_confirmation | 字段命名 | - | 新枚举值 |

只列 needs_confirmation 和 blocked。"需 X 确认"列在相应层未进入 checked_by 时才填。
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md`

plan.md 生成 self-check 追加：

```markdown
- [ ] [M] plan.md §7 含 7.1/7.2/7.3 三个小节，每节至少 1 行或显式"无"
- [ ] [M] plan.md §9 表头含 Producer + Consumers + Checked By + 至少 1 个"需X确认"列
- [ ] [M] plan.md Implementation Checklist 按 Phase 分组，每个 Phase 标注责任层（[前端] / [BFF] / [后端] / [全栈]）
```

### verify

```bash
grep -c "^### 7\.[123]" <fixture>/plan.md       # expected: 3
grep -E "Checked By" <fixture>/plan.md           # expected: 1
grep -cE "\[前端\]|\[BFF\]|\[后端\]|\[全栈\]" <fixture>/plan.md  # expected: >= 1
```

### commit

```
fix(audit-p0): [P0-9] plan.md §7/§9 enforce 3-layer validation matrix + contract table
```

---

## P0-10 — reference 04-routing-playbooks.yaml 恢复 cross_repo_handoffs 填充

### 现象

v2.16.0 template `04-routing-playbooks.yaml` 的 `prd_routing` 和 `playbooks` 段都有 `handoff_surfaces` / `cross_repo_handoffs` 字段：

```yaml
prd_routing:
  - id: "ROUTE-001"
    target_surfaces: ["bff.schema_or_template"]
    handoff_surfaces:
      - repo: "genos"
        layer: "frontend"
        reason: "新增表单 UI 和客户端契约"
        expected_owner: "前端 owner"
        verification: "needs_confirmation"

playbooks:
  - id: "PLAYBOOK-001"
    layer_steps:
      frontend: []    # 前端的 step
      bff: []         # BFF 的 step
      backend: []     # 后端的 step
    cross_repo_handoffs:
      - repo: "magellan"
        layer: "backend"
        handoff_reason: "新枚举值需后端支持"
        verification: "needs_confirmation"
        owner_to_confirm: "backend owner"
```

实跑产物 `/Users/didi/work/dive-bff/_prd-tools/reference/04-routing-playbooks.yaml`：

- `handoff_surfaces` 字段完全没有
- `cross_repo_handoffs` 字段完全没有
- `layer_steps.frontend` 和 `layer_steps.backend` 全空或缺失

### 根因

同 P0-8：template 保留了字段，但 step-02-deep-analysis.md 不再指令填写。

### 修复

#### 1. 更新 `plugins/reference/skills/reference/steps/step-02-deep-analysis.md`

在 `04-routing-playbooks.yaml` 生成段加硬规则：

```markdown
### 04-routing-playbooks.yaml 生成（全栈路由 + 跨仓 handoff）

每个 `prd_routing` 条目**必须**填：

- `target_surfaces`: 本仓负责的 surface 列表（如 `["bff.schema_or_template", "bff.linkage_options"]`）
- `handoff_surfaces`: 非本仓层的建议 handoff 列表（数组）
  ```yaml
  handoff_surfaces:
    - repo: "<best guess repo name>"
      layer: "frontend | backend | external"
      reason: "为什么需要这层配合（来自 PRD 或契约分析）"
      expected_owner: "前端 owner / 后端 owner / 外部系统 owner"
      verification: "confirmed | needs_confirmation | unknown"
  ```

每个 `playbook` 条目**必须**填：

- `layer_steps.frontend`, `layer_steps.bff`, `layer_steps.backend` 三个 key 都要存在（空列表也要写）
- `cross_repo_handoffs`: 跨仓协作清单（非本仓层有动作时必填）

**理由**：团队规划通过 reference 构建 B 端营销全团队公共知识库。routing-playbook 是跨团队协作的入口 — 没有 handoff 字段，前端/后端看不到自己要干什么。
```

#### 2. 更新 `plugins/reference/skills/reference/steps/step-03-quality-gate.md`

加检查：

```markdown
- [ ] [fail] 每个 prd_routing[] 条目有 handoff_surfaces 字段（可以空数组，但不能缺键）
- [ ] [warn] 跨层 PRD（target_surfaces 含多层，或 PRD 明显涉及前端+BFF+后端）但 handoff_surfaces 为空 → 必须填
- [ ] [fail] 每个 playbook[].layer_steps 含 frontend/bff/backend 三个 key
```

### verify

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('/Users/didi/work/dive-bff/_prd-tools/reference/04-routing-playbooks.yaml'))
for r in d.get('prd_routing', []):
    assert 'handoff_surfaces' in r, f'{r[\"id\"]} missing handoff_surfaces'
for p in d.get('playbooks', []):
    ls = p.get('layer_steps', {})
    for k in ['frontend', 'bff', 'backend']:
        assert k in ls, f'{p[\"id\"]} layer_steps missing {k}'
print('OK')
"
```

### commit

```
fix(audit-p0): [P0-10] routing-playbooks.yaml restore handoff_surfaces + layer_steps 3-layer
```

---

## P0-11 — report.md / plan.md 章节强制按 schema 11-12 段生成，禁止自创

### 现象

`plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md` 明确定义了：

- report.md：12 章节（`## 1. 需求摘要` → `## 12. 阻塞问题与待确认项`）
- plan.md：11 章节（`## 1. 范围与假设` → `## 11. 工作量估算`）

实跑产物 `/Users/didi/work/dive-bff/_prd-tools/distill/gas-new-driver-coupon/`：

**report.md 实际章节** vs schema：

| schema 定义 | 实跑生成 | 是否对齐 |
|---|---|---|
| `## 1. 需求摘要（30秒决策）` | `## §1 需求理解摘要` | ⚠ 名称不同 |
| `## 2. PRD 质量摘要` | `## §2 变更类型` | ❌ 完全错位 |
| `## 3. 源码扫描命中摘要` | `## §3 PRD 质量摘要` | ❌ 错位 |
| `## 4. 影响范围` | `## §4 BFF 层影响范围` | ⚠ 单层化 |
| `## 5. 关键结论` | `## §5 关键字段和契约变化` | ⚠ 名称不同 |
| `## 6. 变更明细表` | `## §6 校验规则摘要` | ❌ 错位 |
| `## 7. 字段清单` | `## §7 Checklist` | ❌ 错位 |
| `## 8. 校验规则` | `## §8 契约风险` | ❌ 错位 |
| `## 9. 开发 Checklist` | `## §9 Reference 消费状态` | ❌ schema 无此章 |
| `## 10. 契约风险` | `## §10 开发顺序建议` | ❌ schema 无此章 |
| `## 11. Top Open Questions` | `## §11 Top Open Questions` | ✓ |
| `## 12. 阻塞问题与待确认项` | `## §12 Reference 缺失警告` | ❌ schema 无此章 |

**plan.md 实际章节**（schema 11 段）：

- 实际全是 `## Phase 1` ~ `## Phase 5` + `## 回滚方案` + `## 开发时间估算` + `## 风险矩阵` + `## Implementation Checklist` + `## Verification Commands` + `## Blockers`
- **完全没有** schema 定义的 "1. 范围与假设 / 2. 整体架构 / 3. 实现计划 / 4. API 设计 / 5. 数据存储 / 6. 配置与开关 / 7. 校验规则汇总 / 8. QA 矩阵 / 9. 契约对齐 / 10. 风险与回滚 / 11. 工作量估算"

### 根因

1. `steps/step-03-confirm.md:40-97` 虽然列出了 11 个章节，但 schema 文件 `04-report-plan.md` 却是 12 个（P0-2 已发现的漂移问题）
2. **最关键的缺失**：没有任何 gate/validator 检查"实际生成的 report.md/plan.md 的 H2 标题是否严格等于 schema 定义的章节标题"
3. `distill-quality-gate.py` 只检查 `required_files` 存在和 `plan_actionability`（checklist 数量），不检查章节结构
4. 实跑时模型按照 "P1-2 中补充的 Implementation Checklist + Verification Commands + Blockers" 硬规则生成，但这几段是硬塞在 Phase 段之后的，原 11 章节被整个顶掉

### 修复

#### 1. 在 `scripts/final-quality-gate.py` 新增 `_check_section_structure` 函数（不新建脚本）

> **重要**：不要新建 `section-structure-gate.py`。这个检查逻辑应作为一个函数加到已有的 `final-quality-gate.py`，与其他 checks 并列。避免脚本泛滥。

在 `scripts/final-quality-gate.py` 里追加：

```python
REPORT_SECTIONS = [
    "1. 需求摘要（30秒决策）",
    "2. PRD 质量摘要",
    "3. 源码扫描命中摘要",
    "4. 影响范围",
    "5. 关键结论",
    "6. 变更明细表（核心可操作内容）",
    "7. 字段清单（按功能模块分组）",
    "8. 校验规则",
    "9. 开发 Checklist（可直接执行）",
    "10. 契约对齐与建议",        # P0-6 改名
    "11. Top Open Questions",
    "12. 阻塞问题与待确认项",
]

PLAN_SECTIONS = [
    "1. 范围与假设",
    "2. 整体架构",
    "3. 实现计划",
    "4. API 设计",
    "5. 数据存储",
    "6. 配置与开关",
    "7. 校验规则汇总（分层矩阵）",   # P0-9 改名
    "8. QA 矩阵",
    "9. 契约对齐（全栈视图）",       # P0-9 改名
    "10. 风险与回滚",
    "11. 工作量估算",
]

def extract_h2(path):
    with open(path) as f:
        text = f.read()
    return re.findall(r'^## (.+)$', text, re.MULTILINE)

def validate(path, expected):
    got = extract_h2(path)
    # 去掉章节号前的 §
    got = [g.lstrip('§').strip() for g in got]
    errors = []
    for i, exp in enumerate(expected):
        if i >= len(got):
            errors.append(f"missing section {i+1}: '{exp}'")
        elif not got[i].startswith(exp.split('.')[0] + '.'):
            errors.append(f"section {i+1} mismatch: expected '{exp}', got '{got[i]}'")
    extra = got[len(expected):]
    if extra:
        errors.append(f"unexpected extra sections: {extra}")
    return errors

def main():
    distill_dir = sys.argv[sys.argv.index('--distill-dir')+1]
    all_errors = {}
    for name, sections in [('report.md', REPORT_SECTIONS), ('plan.md', PLAN_SECTIONS)]:
        p = Path(distill_dir) / name
        if p.is_file():
            errs = validate(p, sections)
            if errs:
                all_errors[name] = errs
    if all_errors:
        for name, errs in all_errors.items():
            print(f"[FAIL] {name}:")
            for e in errs:
                print(f"  - {e}")
        sys.exit(2)
    print("[PASS] all H2 headings match schema")

# END OF NEW FUNCTIONS
# Register the check in the main() / run_all_checks() orchestrator:
#   results['section_structure'] = _check_section_structure(distill_dir)
# Do NOT create a new script file.
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md`

在 "report.md 生成" 段加硬规则：

```markdown
### report.md H2 章节强制要求

**必须**按以下 12 个标题顺序生成（不得增删、不得改名、不得加 §x 前缀）：

1. `## 1. 需求摘要（30秒决策）`
2. `## 2. PRD 质量摘要`
3. `## 3. 源码扫描命中摘要`
4. `## 4. 影响范围`
5. `## 5. 关键结论`
6. `## 6. 变更明细表（核心可操作内容）`
7. `## 7. 字段清单（按功能模块分组）`
8. `## 8. 校验规则`
9. `## 9. 开发 Checklist（可直接执行）`
10. `## 10. 契约对齐与建议`（分前端/BFF/后端/外部 4 小节，见 P0-6）
11. `## 11. Top Open Questions`
12. `## 12. 阻塞问题与待确认项`

**禁止**的做法：
- ❌ 写成 `## §1 xxx`（加 § 前缀）
- ❌ 写 `## Reference 消费状态` / `## Reference 缺失警告`（schema 无此章，应并入 §3 或 §12）
- ❌ 把 §4 写成 `## 4. BFF 层影响范围`（应含 4 层，见 P0-7）
- ❌ 章节顺序打乱

### plan.md H2 章节强制要求

**必须**按以下 11 个标题顺序生成：

1. `## 1. 范围与假设`
2. `## 2. 整体架构`
3. `## 3. 实现计划`（Phase 子章用 H3 `### Phase 1:` 等，不是 H2）
4. `## 4. API 设计`
5. `## 5. 数据存储`
6. `## 6. 配置与开关`
7. `## 7. 校验规则汇总（分层矩阵）`（见 P0-9）
8. `## 8. QA 矩阵`
9. `## 9. 契约对齐（全栈视图）`（见 P0-9）
10. `## 10. 风险与回滚`
11. `## 11. 工作量估算`

Implementation Checklist / Verification Commands / Blockers 段（P1-2 要求）作为 H3 子章放入：

- Implementation Checklist → `### 3.N Implementation Checklist`（§3 实现计划 的子章）
- Verification Commands → `### 3.N Verification Commands`（§3 实现计划 的子章）
- Blockers → `### 10.N Blockers`（§10 风险与回滚 的子章）
```

#### 3. 在 Step 8.5 Final Quality Gate 加入 section 结构检查

更新 `scripts/final-quality-gate.py`，在 existing checks 后追加：

```python
# 调用 section-structure-gate
import subprocess
r = subprocess.run(['python3', 'scripts/section-structure-gate.py',
                    '--distill-dir', distill_dir],
                   capture_output=True, text=True)
results['section_structure'] = {
    'status': 'pass' if r.returncode == 0 else 'fail',
    'stdout': r.stdout,
}
```

### verify

```bash
# report.md 12 个章节都在且顺序对
python3 scripts/section-structure-gate.py --distill-dir <fixture>
# expected: exit 0, print "[PASS]"

# 手动 grep
grep -nE "^## [0-9]+\." <fixture>/report.md | wc -l   # expected: 12
grep -nE "^## [0-9]+\." <fixture>/plan.md | wc -l     # expected: 11
grep -cE "^## §" <fixture>/report.md                  # expected: 0（不能有 § 前缀）
```

### commit

```
fix(audit-p0): [P0-11] strict H2 section structure for report.md (12) and plan.md (11)
```

---

## P0-12 — reference-update-suggestions.yaml 字段完整填写（恢复 12 字段 schema）

### 现象

`references/output-contracts.md:815-838` 和 `schemas/03-context.md` 都**完整保留**了 v2.16.0 的 schema：

```yaml
suggestions:
  - id: "REF-UPD-001"
    type: "new_term | new_route | new_contract | new_playbook | contradiction | golden_sample_candidate"
    target_file: "..."
    summary: ""
    current_repo_scope:
      authority: "single_repo"
      action: "apply_to_current_repo | record_as_signal | needs_owner_confirmation"
    owner_to_confirm: []
    team_reference_candidate: false
    team_scope:
      type: "contract | domain_term | playbook | decision | routing_signal | golden_sample"
      related_repos: []
      aggregation_status: "candidate | confirmed | rejected | not_applicable"
    evidence: ["EV-001"]
    priority: "high | medium | low"
    confidence: "high | medium | low"
    proposed_patch: ""
```

实跑产物 `context/reference-update-suggestions.yaml` **只用了 6 个简化字段**：

```yaml
- id: REF-SUG-001
  target_file: "01-codebase.yaml"
  section: "CampaignType enum"       # schema 里没有 section
  action: "add_entry"                 # schema 要求是 current_repo_scope.action
  description: "..."                  # schema 里是 summary
  reason: "..."                       # schema 里没有 reason
```

**丢失的 7 个关键字段**：

| 字段 | 用途 | 丢失后果 |
|---|---|---|
| `type` | 分类为 new_term/new_contract/new_playbook 等 6 类 | 公共库无法按类型聚合 |
| `current_repo_scope.action` | 三选一语义：立即应用/记为信号/需确认 | 无法自动决定是否立即写入 reference |
| `owner_to_confirm` | 需确认的 owner 列表 | 跨团队协作路径断裂 |
| **`team_reference_candidate`** | **是否适合升到团队公共库** | **公共库愿景的关键标记丢失** |
| **`team_scope`** | **聚合类型 + related_repos + aggregation_status** | **无法跨仓聚合** |
| `priority` | high/medium/low | 无法排序回流优先级 |
| `confidence` | high/medium/low | 无法区分"已 verify" vs "推断" |
| `proposed_patch` | 建议的具体 YAML patch | 回流时需人工改写 |
| `evidence` | 证据 ID 引用 | 断追溯链 |

### 根因

1. `steps/step-03-confirm.md` 的 "生成 reference-update-suggestions" 段**只要求模型按 schema 生成**，但没列出**必填字段清单**
2. 没有 contract validator 检查 schema 符合度（只有 file existence 检查）
3. 模型倾向于简化未明确要求的字段

### 修复

#### 1. 新增 `contracts/reference-update-suggestions.contract.yaml`

```yaml
artifact: "context/reference-update-suggestions.yaml"
schema_version: "2.0"
required_top_level:
  - schema_version
  - suggestions
rules:
  - id: "each_has_full_schema"
    each: "suggestions"
    required:
      - id
      - type                          # 必填 6 类枚举之一
      - target_file
      - summary
      - current_repo_scope             # 必填对象
      - team_reference_candidate       # 必填布尔
      - priority
      - confidence
      - evidence

  - id: "type_enum_valid"
    each: "suggestions"
    require: "type in ['new_term','new_route','new_contract','new_playbook','contradiction','golden_sample_candidate']"

  - id: "action_enum_valid"
    each: "suggestions"
    require: "current_repo_scope.action in ['apply_to_current_repo','record_as_signal','needs_owner_confirmation']"

  - id: "team_candidate_requires_scope"
    each: "suggestions"
    when:
      field: "team_reference_candidate"
      equals: true
    required_on_match:
      - team_scope

  - id: "team_scope_enum_valid"
    each: "suggestions"
    when:
      field: "team_reference_candidate"
      equals: true
    require: "team_scope.type in ['contract','domain_term','playbook','decision','routing_signal','golden_sample']"
    note: "team_scope.aggregation_status 初始必须是 candidate，升级由 /team-reference 聚合脚本做"
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md`

在 "reference-update-suggestions 生成" 段重写为：

```markdown
### reference-update-suggestions.yaml 生成（团队公共库的入口）

**每条 suggestion 必须填满以下字段**（按 schema v2.0）：

```yaml
- id: REF-UPD-XXX                    # 必填
  type: "<枚举>"                      # 必填，6 选 1
  target_file: "_prd-tools/reference/<xxx>.yaml"   # 必填
  summary: "一句话说明这条建议做什么"  # 必填，不要简化成 description
  current_repo_scope:                 # 必填对象
    authority: "single_repo"
    action: "<枚举>"                   # 必填，3 选 1
  owner_to_confirm: ["<owner>"]       # 需确认时必填
  team_reference_candidate: true|false   # 必填布尔，默认 false
  team_scope:                         # 当 team_reference_candidate=true 时必填
    type: "<枚举>"                    # 6 选 1
    related_repos: ["dive-bff", "genos", "magellan"]
    aggregation_status: "candidate"   # 初始必为 candidate
  priority: "high|medium|low"         # 必填
  confidence: "high|medium|low"       # 必填
  evidence: ["EV-001"]                # 必填数组
  proposed_patch: |                   # 建议的 YAML patch，直接可 apply
    contracts:
      - id: "CONTRACT-NEW"
        ...
```

**团队公共库候选判定**（即 `team_reference_candidate: true` 的条件）：

- 契约影响 2+ 个仓 → `type=contract, team_reference_candidate=true`
- 术语首次出现且为全团队业务概念 → `type=domain_term, team_reference_candidate=true`
- Playbook 是跨前端/后端的完整流程 → `type=playbook, team_reference_candidate=true`
- 否则（单仓内部规则）→ `team_reference_candidate=false`

**禁止简化为 `{id, target_file, section, action, description, reason}` 6 字段**。完整字段是公共库聚合的基础。
```

#### 3. 在 Step 7 (reference update) 的 gate 调用 validator

`scripts/distill-step-gate.py` 的 Step 7 prerequisite 检查加：

```python
# Step 7: validate reference-update-suggestions.yaml against contract
if not subprocess_call('scripts/validate-artifact.py',
    '--artifact', f'{distill_dir}/context/reference-update-suggestions.yaml',
    '--contract', 'plugins/prd-distill/skills/prd-distill/references/contracts/reference-update-suggestions.contract.yaml'):
    return FAIL
```

### verify

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/reference-update-suggestions.yaml'))
required = {'id','type','target_file','summary','current_repo_scope','team_reference_candidate','priority','confidence','evidence'}
for s in d['suggestions']:
    missing = required - set(s.keys())
    assert not missing, f'{s[\"id\"]} missing {missing}'
print(f'OK: all {len(d[\"suggestions\"])} suggestions have full schema')
"

# 至少 1 条 team candidate
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/reference-update-suggestions.yaml'))
candidates = [s for s in d['suggestions'] if s.get('team_reference_candidate')]
assert candidates, 'expected at least 1 team_reference_candidate'
print(f'OK: {len(candidates)} team candidates')
"
```

### commit

```
fix(audit-p0): [P0-12] reference-update-suggestions.yaml restore 12-field schema + team candidate flag
```

---

## P0-13 — evidence.yaml / alignment_summary / readiness schema 字段漂移全面修复

### 现象

多个 context 产物的实际字段与 schema 定义**完全不同名**，模型各自发明了 schema：

#### (A) evidence.yaml 顶层键和字段名漂移

| schema 定义（`output-contracts.md:377-386`） | 实跑产物 | 状态 |
|---|---|---|
| `items:` | `entries:` | ❌ 顶层键不同 |
| `kind: "prd \| tech_doc \| code \| ..."` | `type: prd_source` | ❌ 字段名+枚举都不同 |
| `locator: "page/section/line/symbol"` | `section: "全文"` | ❌ 字段名不同 |
| `summary, source, confidence` | 相同 | ✓ |

#### (B) contract-delta.yaml alignment_summary 字段漂移

| schema 定义（`output-contracts.md:807-810`） | 实跑产物 | 状态 |
|---|---|---|
| `alignment_summary.status: "aligned \| needs_confirmation \| blocked"` | `alignment_summary.aligned: 1` | ❌ 完全不同结构 |
| `alignment_summary.blockers: []` | `alignment_summary.needs_confirmation: 7` | ❌ |
| `alignment_summary.next_actions: []` | `alignment_summary.blocked: 0` | ❌ |
| — | `alignment_summary.total: 8` | ❌ schema 无此字段 |

模型把它理解成了"各状态的计数 bucket"，schema 的原意是"**整体**状态 + 阻塞清单 + 下一步"。

#### (C) readiness-report.yaml schema 版本和结构完全不符

| schema 定义（`schemas/05-readiness.md:6-28`） | 实跑产物 | 状态 |
|---|---|---|
| `schema_version: "3.0"` | `schema_version: "1.0"` | ❌ |
| `scores: {prd_ingestion, evidence_coverage, code_search, contract_alignment, task_executability}` | `dimensions: [{dimension: prd_clarity, ...}]` | ❌ 结构完全变了 |
| `decision: "ready_for_dev \| needs_owner_confirmation \| blocked"` | `decision: proceed_with_cautions` | ❌ 枚举不存在 |
| `status: "pass \| warning \| fail"` | `status: ready_with_risks` | ❌ 枚举不存在 |
| `provider_value.reference: {reused_playbooks, reused_contracts, examples}` | **完全缺失** | ❌ 无法衡量 reference 被复用多少 |
| `summary: {title, top_reason}` | **缺失** | ❌ |

`provider_value.reference` 字段尤其关键：它是衡量**团队公共库价值**的核心指标（每次 PRD 用了多少已沉淀的 playbooks/contracts），丢失后公共库 ROI 无法度量。

### 根因

- schemas/*.md 里虽然定义了正确字段，但步骤文件里没有"**字段名必须严格等于 schema**"的硬约束
- 没有 contract validator 检查 evidence.yaml / readiness-report.yaml（只有 requirement-ir/layer-impact/contract-delta/ai-friendly-prd 有 contract）

### 修复

#### 1. 新增 3 个 contract 文件

**`references/contracts/evidence.contract.yaml`**：

```yaml
artifact: "context/evidence.yaml"
schema_version: "2.0"
required_top_level:
  - schema_version
  - items                     # 必须用 items，不是 entries
rules:
  - id: "each_has_required"
    each: "items"
    required:
      - id
      - kind                   # 枚举字段，不是 type
      - source
      - locator                # 不是 section
      - summary
      - confidence
  - id: "kind_enum_valid"
    each: "items"
    require: "kind in ['prd','tech_doc','code','git_diff','negative_code_search','human','api_doc','reference']"
```

**`references/contracts/readiness-report.contract.yaml`**：

```yaml
artifact: "context/readiness-report.yaml"
schema_version: "3.0"
required_top_level:
  - schema_version
  - status
  - score
  - decision
  - scores
  - risks
  - provider_value             # 必填，团队公共库价值度量
rules:
  - id: "status_enum"
    require: "status in ['pass','warning','fail']"
  - id: "decision_enum"
    require: "decision in ['ready_for_dev','needs_owner_confirmation','blocked']"
  - id: "scores_5_dims"
    path: "scores"
    required:
      - prd_ingestion
      - evidence_coverage
      - code_search
      - contract_alignment
      - task_executability
  - id: "provider_value_has_reference"
    path: "provider_value.reference"
    required:
      - reused_playbooks
      - reused_contracts
      - examples
    note: "provider_value.reference 是团队公共库 ROI 指标，必须统计"
```

**更新 `references/contracts/contract-delta.contract.yaml`**（补 alignment_summary 规则）：

```yaml
rules:
  # ... 已有规则 ...
  - id: "alignment_summary_schema"
    path: "alignment_summary"
    required:
      - status
      - blockers
      - next_actions
    forbidden:
      - aligned_count      # 禁止用计数代替 status
      - needs_confirmation_count
      - blocked_count
      - total
    note: "alignment_summary 是'整体状态+阻塞+下一步'结构，不是各状态计数"
```

#### 2. 更新 3 个 step 文件

- `step-01-parse.md` 的 "生成 evidence.yaml" 段：加字段名硬约束（`items:` 不是 `entries:`，`kind:` 不是 `type:`，`locator:` 不是 `section:`）
- `step-02-classify.md` 的 "生成 contract-delta.yaml" 段：加 alignment_summary 格式约束
- `step-03-confirm.md` 的 "生成 readiness-report.yaml" 段：加 provider_value.reference 填充要求

每段都复制 schema 里的完整字段清单作为模板。

#### 3. 在对应 step gate 调用 validator

`scripts/distill-step-gate.py`：
- Step 1 后 validate evidence.yaml
- Step 4 后 validate contract-delta.yaml 的 alignment_summary
- Step 6 后 validate readiness-report.yaml

### verify

```bash
# evidence 用 items 不是 entries
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/evidence.yaml'))
assert 'items' in d, 'must use items as top-level key'
for it in d['items']:
    assert 'kind' in it and 'locator' in it, f'{it.get(\"id\")} missing kind/locator'
print('OK')
"

# alignment_summary 是 status 不是 count
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/contract-delta.yaml'))
s = d.get('alignment_summary', {})
assert 'status' in s, 'alignment_summary.status missing'
assert 'aligned' not in s, 'should not use aligned as count field'
print('OK')
"

# readiness 有 provider_value.reference
python3 -c "
import yaml
d = yaml.safe_load(open('<fixture>/context/readiness-report.yaml'))
pv = d.get('provider_value', {}).get('reference', {})
for k in ['reused_playbooks', 'reused_contracts', 'examples']:
    assert k in pv, f'provider_value.reference.{k} missing'
print('OK')
"
```

### commit

```
fix(audit-p0): [P0-13] enforce schema field names for evidence/alignment_summary/readiness (anti-drift)
```

---

## P0-14 — 恢复 reference 人类可读性：枚举 label + see_enum 去重机制

### 背景

用户反馈：**现在 reference/01-codebase.yaml 的枚举对人类可读性差**。举例：

```yaml
# 当前实跑产物
enums:
  - name: "CampaignType"
    file: "src/config/constant/campaignType.ts"
    values:
      Order: 1
      AISelectableOrder: 10
      Duration: 11
      ...
      GasStation: 26          # 这是啥？完全看不出业务含义
      NoThresholdGasStation: 27
      ...
```

人读到 `GasStation: 26` 完全不知道业务含义，必须跳回源码才能理解。而 AI 可以通过 `_prd-tools/reference/index/entities.json`（evidence index）直接检索，所以 reference/*.yaml 的定位应该是**人类可读**——但当前没有任何人类向说明。

### 现象：v2.16.0 → v2.18.1 的系统性删除

v2.16.0 原设计是"每个枚举值有一行 label 说明业务含义"，并有严格的 SSOT 规则避免 05-domain 和 01-codebase.label 重复。v2.17-v2.18 某次迭代**系统性地**删掉了整条机制：

| 位置 | v2.16.0 原文 | 当前状态 |
|---|---|---|
| 1. `templates/01-codebase.yaml` 注释 | `# 枚举（值的业务含义用 label 一行说明，不放跨层字段级信息）` | 简化为 `# 枚举` ❌ |
| 2. `templates/01-codebase.yaml` 字段 | `values: - {name, value, label: "<一句话业务含义>"}` | 变成 `values: {Name: Value}` map ❌ |
| 3. `reference-v4.md:82` SSOT 表 | `\| 枚举值和 label \| 01-codebase.enums \| ... \|` | `\| 枚举值 \| 01-codebase.enums \| ... \|`（删了"和 label"）❌ |
| 4. `reference-v4.md:75` 05-domain 说明 | `术语（只收录无法归入 01 枚举 label 的概念）` | 删了"枚举 label" ❌ |
| 5. `workflow.md` 分工规则 | `术语只在 05-domain（枚举 label 在 01-codebase 的 enums 中）` | **整行删除** ❌ |
| 6. `step-02-deep-analysis.md:62` | `检查 01-codebase 中的枚举 label...改为 see_enum: "<EnumName>"` | **整段删除** ❌ |
| 7. `step-02-deep-analysis.md:76` | 术语 see_enum 去重规则 | **整段删除** ❌ |
| 8. `step-03-quality-gate.md` | `05-domain 的术语不应与 01-codebase 的枚举 label 重复` | 整条 gate 删除 ❌ |
| 9. `templates/05-domain.yaml` boundary | `术语只收录无法归入 01-codebase 枚举 label 的业务概念` | 整句删除 ❌ |

### 根因

v2.16 设计哲学是 **"reference/*.yaml 给人读，index/ 给机器读"**，两者分工：

- `_prd-tools/reference/*.yaml` = 人类可读知识库（含 label、note、rationale）
- `_prd-tools/reference/index/{entities.json, edges.json, inverted-index.json}` = AI 结构化检索层

实跑验证了这点：`dive-bff/_prd-tools/reference/index/entities.json` 有 1957 个实体、4271 条边、倒排索引完整——**AI 要的信息都在 index 里**，reference/*.yaml 本该放更多人类向说明。

v2.17-v2.18 迭代中可能有人觉得"label 只是业务术语，应归 05-domain"，于是把 01 的 label 删了，**但没在 05-domain 里补齐枚举术语词典**，结果两边都没有。分工规则（`see_enum` 机制）也一并删除。

### 修复

#### 1. 恢复 `templates/01-codebase.yaml`

```yaml
# 枚举（每个值的业务含义用 label 一行说明，给人读；机器可读的结构在 _prd-tools/reference/index/）
enums:
  <EnumName>:
    definition_file: "<path:line>"
    description: "<整个枚举的业务作用，一段话>"
    values:
      - name: "<NAME>"
        value: "<value>"
        label: "<一句话业务含义>"
        notes: ""                        # 可选：复杂逻辑/踩坑说明
    evidence:
      - "EV-001"
```

**数组格式**（不是 map），每个 value 自成对象，带 label 和 notes。

参考理想产物：

```yaml
CampaignType:
  definition_file: "src/config/constant/campaignType.ts:1"
  description: "DIVE 营销活动类型枚举，决定表单 schema 和奖励规则分派"
  values:
    - name: "Order"
      value: 1
      label: "冲单奖：完成指定单数后发奖"
    - name: "GasStation"
      value: 26
      label: "实时油站奖：司机在指定油站完加油单即时发放油站券/折扣卡"
    - name: "NoThresholdGasStation"
      value: 27
      label: "无门槛油站券：不限完单数，活动期间首次加油即发券"
    - name: "FirstRefuelingGasStation"
      value: 28
      label: "首次加油油站券：针对新司机首次加油发券"
```

#### 2. 恢复 `references/reference-v4.md` SSOT 表和 05-domain 描述

第 82 行恢复"和 label"：`| 枚举值和 **label** | 01-codebase.enums | ... |`

第 75 行恢复：`术语（只收录无法归入 01 枚举 label 的概念）`

顶部新增"产物定位"段：

```markdown
## 产物定位（人类 vs 机器）

| 文件 | 读者 | 用途 |
|---|---|---|
| `_prd-tools/reference/*.yaml` (01-05, project-profile) | **人类** | 翻阅、review、沉淀业务知识。必须含 label、description、notes 等人类向说明 |
| `_prd-tools/reference/00-portal.md` / `portal.html` | **人类** | 浏览入口 |
| `_prd-tools/reference/index/entities.json` | **机器** | BM25 + 实体检索，回答"这个符号在哪" |
| `_prd-tools/reference/index/edges.json` | **机器** | 调用/继承/实现关系图 |
| `_prd-tools/reference/index/inverted-index.json` | **机器** | 倒排索引 |

**原则**：reference/*.yaml 应为**人类可读性多加信息**，不要为机器方便简化字段。机器需要的已在 `index/` 里。
```

#### 3. 恢复 `workflow.md` + `step-02-deep-analysis.md` + `step-03-quality-gate.md`

分别恢复 v2.16.0 的以下行/段（逐字复制）：

- `workflow.md`：`- 术语只在 05-domain（枚举 label 在 01-codebase 的 enums 中）。`
- `step-02-deep-analysis.md` 阶段 5：恢复第 19 条 `检查 01-codebase 中的枚举 label，如果 05-domain 的术语与枚举 label 重复，删除 05 中的重复条目，改为 see_enum: "<EnumName>"`
- `step-02-deep-analysis.md` 去重规则：恢复第 4 条（see_enum 机制）
- `step-03-quality-gate.md`：恢复 `05-domain 的术语不应与 01-codebase 的枚举 label 重复`

并在 step-02 加 **label 生成启发式**（新增内容，v2.16 也没有）：

```markdown
### 枚举 label 生成启发式

为每个枚举值生成 label 时，按优先级：

1. **源码注释** — 枚举定义附近的 TSDoc/JSDoc 是最佳来源
2. **i18n/文案** — 有对应 i18n key 时，用翻译后的中文短语
3. **PRD 历史** — `_prd-tools/distill/*/spec/ai-friendly-prd.md` 或 `_ingest/document.md` 里的业务描述
4. **UI 映射** — 源码里 `enum → UI label` 的 Map（如 `previewRewardType.ts`）直接抄
5. **实在没有** — 写 `label: "<未找到业务含义，待 PM 补充>"`（不要编造）

label 是**一句话**（< 30 字），不是段落；背景放 `notes:` 字段。
```

#### 4. 更新 `templates/05-domain.yaml`

boundary 恢复并增强：

```yaml
boundary: "业务领域知识：术语、背景、隐式规则、历史决策。不放代码路径（见01-codebase）、不放编码规则（见02-coding-rules）、不放契约字段（见03-contracts）。术语只收录**无法归入 01-codebase 枚举 label** 的业务概念；若已在 01 中定义，用 see_enum: 引用，不复制。"

terms:
  - term: ""
    definition: ""
    synonyms: []
    prd_keywords: []
    see_enum: ""                 # 新增：引用 01-codebase 的枚举名（避免重复）
    related_enum: ""
    notes: ""
    evidence: ["EV-001"]
```

#### 5. 其他 reference 文件补充人类向字段（轻度）

同理检查：

- `templates/03-contracts.yaml` 每个 contract 加 `business_context: "<这个契约的业务目的>"`（可选但推荐）
- `templates/04-routing-playbooks.yaml` 每个 playbook 加 `scenario_description: "<什么场景会走这个 playbook，一段话>"`
- `templates/02-coding-rules.yaml` 每条 rule 加 `why: "<为什么要这条规则，背景/历史>"`

这些不强制但要在 step-02-deep-analysis.md 里写"推荐填写"，给人读时更有帮助。

### verify

```bash
# 01-codebase.yaml 所有枚举值都有 label
python3 -c "
import yaml
d = yaml.safe_load(open('/Users/didi/work/dive-bff/_prd-tools/reference/01-codebase.yaml'))
enums = d.get('enums', [])
enums_iter = enums if isinstance(enums, list) else [{'name': k, **v} for k, v in enums.items()]
missing = []
for e in enums_iter:
    values = e.get('values', [])
    if isinstance(values, dict):
        missing.append(f'{e.get(\"name\")}: uses map format (should be array with label)')
        continue
    for v in values:
        if not v.get('label'):
            missing.append(f'{e.get(\"name\")}.{v.get(\"name\")} missing label')
assert not missing, missing[:5]
print(f'OK: all enum values have label')
"

# see_enum 引用正确
python3 -c "
import yaml
domain = yaml.safe_load(open('/Users/didi/work/dive-bff/_prd-tools/reference/05-domain.yaml'))
codebase = yaml.safe_load(open('/Users/didi/work/dive-bff/_prd-tools/reference/01-codebase.yaml'))
enums = codebase.get('enums', [])
enum_names = {e['name'] for e in enums} if isinstance(enums, list) else set(enums.keys())
for t in domain.get('terms', []):
    if t.get('see_enum'):
        assert t['see_enum'] in enum_names, f'see_enum {t[\"see_enum\"]} not in 01-codebase'
print('OK')
"
```

### commit

```
fix(audit-p0): [P0-14] restore human-readable enum labels + see_enum dedup (reference vs index boundary)
```

---

## P1-4 — 新增"团队级公共 reference"机制（跨仓沉淀 + 继承）

### 背景

领导规划通过 reference 构建 B 端营销**全团队公共知识库**，包含前端（genos / dive-editor）、BFF（dive-bff / dive-template-bff）、后端（magellan）多仓共享的：

- 跨仓契约（同一 endpoint 在 3 个仓有 producer/consumer 视角）
- 业务术语统一词典（如 "DFR" / "GasStation" / "DLP" 在 3 层含义一致）
- 跨仓 golden sample（一次需求走完 3 仓的完整实现）
- 领域知识（完单奖励、预算告警、活动类型等业务概念）

当前 v2.18.1 架构是**单仓自治**：每个仓自建 `_prd-tools/reference/`，互不感知。模板字段虽含 `team_reference_candidate` / `team_scope` / `related_repos`，但没有任何机制沉淀到公共库、也没有读取公共库的能力。

### 现象

1. 每个仓各自扫描各自的 codebase，`01-codebase.yaml` 只含本仓事实
2. `03-contracts.yaml` 只记录本仓 producer/consumer 视角，跨仓契约只能标 `needs_confirmation`
3. `05-domain.yaml` 的术语每个仓各写一份，容易不一致
4. 新仓（如 dive-template-bff）接入时无法继承 dive-bff 已沉淀的业务知识
5. prd-distill 在 dive-bff 产出的 report，前端/后端章节基于 PRD 推断，没有 dive-team-common reference 作为"团队公共知识库"支撑

### 修复

#### 1. 新增"公共 reference 仓"约定

约定一个**团队级中心仓**（例如 `dive-team-reference`），结构：

```text
dive-team-reference/
├── .prd-tools-team-version       # "2.19.0"
├── reference/
│   ├── 00-portal.md              # 团队级导航
│   ├── project-profile.yaml      # layer: "team-common", team_scope: {...}
│   ├── 01-codebase.yaml          # 跨仓代码地图（引用 3 个仓的模块）
│   ├── 02-coding-rules.yaml      # 全团队共享的 fatal 规则
│   ├── 03-contracts.yaml         # 3 仓已 checked_by 的跨仓契约（团队级 SSOT）
│   ├── 04-routing-playbooks.yaml # 跨 3 仓的 playbook（frontend/bff/backend 都填）
│   └── 05-domain.yaml            # 全团队术语、业务决策
└── build/
    └── aggregation-report.yaml   # 聚合哪些仓、哪些 team_reference_candidate 被接受
```

每个仓的 `_prd-tools/reference/project-profile.yaml` 新增字段：

```yaml
team_reference:
  upstream_repo: "git@git.xiaojukeji.com:dive-marketing/dive-team-reference.git"
  upstream_local_path: "../dive-team-reference"      # 本地 clone 路径
  inherit_scopes:
    - domain_terms               # 继承 05-domain 的术语
    - contracts_cross_repo       # 继承 03-contracts 中 team_reference_candidate=true 的契约
    - coding_rules_fatal         # 继承 02-coding-rules 的 fatal 规则
  last_synced: "2026-05-12T22:00:00+08:00"
```

#### 2. 聚合/继承脚本本轮**不写**，只定规范

> **重要**：本轮只落脚手架（schema 字段 + 约定）。聚合和继承逻辑留到后续迭代。
>
> **不要**创建 `team-reference-aggregate.py` 或 `team-reference-inherit.py`（包括 stub）。stub 脚本等于占位符代码，没有实际价值，反而膨胀 `scripts/`。
>
> 未来真要实现时，在 `docs/team-reference-design.md` 记录以下接口设计供参考：
>
> - 聚合：读成员仓 03-contracts/05-domain/04-routing-playbooks 的 `team_reference_candidate: true` 条目 → 跨仓合并同一 contract_id → 写团队仓
> - 继承：读团队仓 reference/ → 镜像到本仓（标 `source: team-common, read_only: true`），本仓已有的不覆盖
>
> 本轮只需保证 schema 里**有正确字段**供未来聚合读取。

#### 3. prd-distill 消费团队 reference（指令层，不写脚本）

`plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md` 加：

```markdown
### 团队公共 reference 消费（可选）

如果当前仓 `_prd-tools/reference/project-profile.yaml` 的 `team_reference.upstream_local_path` 存在：

1. Read `<upstream_local_path>/reference/05-domain.yaml` 作为全团队业务术语
2. Read `<upstream_local_path>/reference/03-contracts.yaml` 获取跨仓契约基线
3. Read `<upstream_local_path>/reference/04-routing-playbooks.yaml` 的跨仓 playbook

这些信息在 report/plan 中允许高于本仓 reference 的权威性——它们是"全团队已 checked_by 的共识"。
```

### 本次 scope 仅做机制原型（后续完善）

鉴于这是**新增能力**（不是修 bug），本轮只做**零脚本**的脚手架：

- ✅ 约定目录结构和字段（P1-4 本条文档化即可）
- ✅ template / schema 加 `team_reference:` 字段（修改现有 YAML）
- ✅ step-02-deep-analysis.md 指令填写 `team_reference_candidate`（改现有 md）
- ✅ 在 `docs/team-reference-design.md` 写聚合/继承的接口设计（纯文档）
- ❌ **不写** `team-reference-aggregate.py` / `team-reference-inherit.py`（包括 stub）
- ❌ **不创建** `/team-reference` skill（等聚合脚本真做出来再加）
- ⏸ 实际聚合/继承逻辑 v2.19 或 v2.20 再做

这样下一次 dive-bff 跑 `/reference` 至少能**正确标注** `team_reference_candidate: true`，为后续聚合做准备。

### verify

```bash
# dive-bff reference 重新生成后，应有至少 1 个跨仓契约被标为团队候选
grep -c "team_reference_candidate: true" /Users/didi/work/dive-bff/_prd-tools/reference/03-contracts.yaml
# expected: >= 1

# project-profile.yaml 有 team_reference 字段占位
grep "team_reference:" /Users/didi/work/dive-bff/_prd-tools/reference/project-profile.yaml
# expected: 1 行

# 设计文档存在（供未来写脚本时参考）
ls docs/team-reference-design.md
# expected: 文件存在
```

### commit

```
feat(team-ref): [P1-4] introduce team common reference scaffolding (aggregation + inheritance)
```

---

## P1-1 — 新增 `scripts/ingest-docx.py` 工具化

### 现象

实跑 Step 0 解压 docx 时，模型手写 4 段 Python：第 1 段 permission denied，第 2 段只得 "0 images"，第 3 段发现 tag namespace 错，第 4 段才成功。其中还踩坑：图片实际在 `docx_tmp/media/`，模型先试 `docx_tmp/word/media/*`。整个 ingestion 耗掉约 10 分钟。

### 修复

#### 1. 新建 `scripts/ingest-docx.py`

功能：
- 接收 `--input <path/to/file.docx>` 和 `--output <distill-dir>/_ingest/`
- 解压 docx，自动修复权限 (`chmod -R u+rw docx_tmp/`)
- 解析 `word/document.xml` 提取段落和表格 → `document.md`
- 解析 image rels (`word/_rels/document.xml.rels`) → `document-structure.json`
- 拷贝 `docx_tmp/media/*.png` 或 `word/media/*.png`（都试一下）→ `media/`
- 生成 `source-manifest.yaml`（含 media_count, size_bytes, extraction_method）
- 生成 `extraction-quality.yaml`（含 text_completeness, image_extraction_status）
- 清理 `docx_tmp/`

骨架：

```python
#!/usr/bin/env python3
"""Ingest a docx PRD file into _ingest/ with document.md, media/, structure.json, manifests."""
import argparse, os, sys, shutil, zipfile, subprocess, json, hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

def extract_paragraphs_and_tables(xml_path): ...
def extract_image_rels(rels_path): ...
def copy_media(docx_tmp, media_out): ...
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', '--distill-dir', dest='output', required=True,
                    help='Distill directory (will write to <output>/_ingest/)')
    args = ap.parse_args()
    ...
```

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-01-parse.md`

在 Step 0 描述里把 "手写 Python 解析" 改成：

```bash
python3 .prd-tools/scripts/ingest-docx.py --input "<prd.docx>" --distill-dir _prd-tools/distill/<slug>
```

文件类型不是 docx 时（md/pdf/txt），保留 fallback 到手写脚本。

### verify

```bash
python3 scripts/ingest-docx.py --help
# expected: 显示 usage

# 干跑一个 fixture docx
python3 scripts/ingest-docx.py --input docs/fixtures/sample.docx --distill-dir /tmp/test-distill
ls /tmp/test-distill/_ingest/
# expected: document.md, document-structure.json, source-manifest.yaml, extraction-quality.yaml, media/
```

### commit

```
feat(scripts): [P1-1] add ingest-docx.py to replace ad-hoc XML parsing in Step 0
```

---

## P1-2 — plan.md / report.md schema 写死 must-contain 段

### 现象

实跑时 `final-quality-gate.py` 跑了 3 轮才通过：

- 第 1 轮 59 分：plan.md 缺 "Implementation Checklist"、"Verification Commands" → 模型手动加
- 第 2 轮 75 分：`blocker_quality: 0`，脚本检查 report.md 中 blocker 周围窗口是否含 "建议/owner/风险" → 模型改 report.md §11 每条 blocker 加 `owner`, `suggestion`, `risk`, `mitigation`
- 第 3 轮 84 分通过

这 3 个强制段在 step / schema 文档里**没有硬性要求**，模型靠试错才发现。

### 证据

- `scripts/final-quality-gate.py:68-70` (`RE_BLOCKER_QUALITY`)
- `scripts/final-quality-gate.py:445` (`plan_actionability`)
- `plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md` 的 plan.md 模板没有 Implementation Checklist 和 Verification Commands 段

### 修复

#### 1. 更新 `plugins/prd-distill/skills/prd-distill/references/schemas/04-report-plan.md`

在 plan.md 模板末尾追加固定段：

```markdown
## Implementation Checklist

按 Phase 分组，每项标注关联 REQ-ID/IMP-ID：
- [ ] Task 1.1: <具体操作>（<目标文件>）— REQ-001, IMP-001
- [ ] ...

## Verification Commands

```bash
# 每个关键改动配一个验证命令（grep / build / test）
rg 'SymbolName' src/path/to/file.ts
npm run build
npm test
```

## Blockers (with owner/suggestion)

| # | Blocker | Owner | Suggestion | Status |
|---|---------|-------|-----------|--------|
| 1 | ... | PM / FE / BE | ... | needs_confirmation |
```

同时更新 report.md 模板的 §12 (阻塞问题) 每条必须含 6 要素（之前已定义，但要明确"在 report.md 同一段内展示，不是放到 requirement-ir 里"）。

#### 2. 更新 `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md`

在"生成 plan.md"部分加 self-check：

```markdown
- [ ] [M] plan.md 含 Implementation Checklist 段（至少 5 个 `- [ ]` 任务）
- [ ] [M] plan.md 含 Verification Commands 段（至少 3 条 `rg` 或 `npm` 命令）
- [ ] [M] report.md §12 每个 blocker 含 owner + suggestion + risk + mitigation 中至少 3 项
```

#### 3. 可选：更新 `final-quality-gate.py` 的 fix_hint

`check_plan_actionability` 返回 warning 时，在 `top_gaps` 里附建议：

```python
if not result['checklist_count']:
    gaps.append("plan.md missing Implementation Checklist — see schemas/04-report-plan.md template")
```

### verify

```bash
# 空模板测试
python3 scripts/final-quality-gate.py --distill-dir /tmp/empty-fixture 2>&1 | grep "Implementation Checklist"
# expected: 错误消息指向正确位置
```

### commit

```
fix(audit-p1): [P1-2] plan.md must-contain Checklist/Verify; report.md blocker 6-elements enforced
```

---

## P1-3 — Step 8.6 "Distill Completion Gate" 有名无实

### 现象

实跑 workflow-state：

```yaml
- step: '8.6'
  label: 'Step 8.6: Distill Completion Gate'
  gate_status: passed
  output_files: []   # 空
```

Step 8.6 被调用后直接 passed，没做任何检查也没产出 artifact。名字叫"Completion Gate"但实际是个空洞。

### 证据

- `workflow-state.yaml` 的 step 8.6 entry `output_files: []`
- `scripts/distill-step-gate.py:~STEP_TABLE` 的 "8.6" 条目（需读一下看是否有 output）

### 修复

二选一：

**方案 A（推荐）**：Step 8.6 改为"Reference Update Staging"，实际检查：

1. `context/reference-update-suggestions.yaml` 存在且 suggestions 数 >= 0
2. 所有 IMP 项的 `code_anchor` 对应文件真的存在
3. 写入 `context/completion-report.yaml` 含 `final_checklist_ok: true/false`

**方案 B**：删除 Step 8.6，把检查合并到 8.5 Final Quality Gate。

推荐 A，改动更小，更改 `scripts/distill-step-gate.py` 的 STEP_TABLE["8.6"] 加 prerequisites 和 output 字段。

### verify

```bash
# Step 8.6 完成后应有 completion-report.yaml 产出（或完全消失）
ls <fixture>/context/completion-report.yaml
```

### commit

```
fix(audit-p1): [P1-3] step 8.6 Completion Gate actually validates code_anchors and writes report
```

---

## P2-1 — context-pack.md 加"必引用段落"标识

### 现象

`final-quality-gate.yaml` 显示：

```yaml
context_pack_consumed:
  anchors_in_pack: 127
  consumed_by_report: 24     (19%)
  consumed_by_plan: 30       (24%)
```

context-pack.md 里有 127 个代码锚点，但 report/plan 只引用了 19-24%。原因是 pack 没有给出"哪些必须引用"的提示，模型自行裁剪。

### 修复

#### 1. 更新 `scripts/context-pack.py`

在 pack 渲染模板里，对每个 section 加优先级标签：

```markdown
## 🔴 Must-Reference Anchors (key_anchors)

以下锚点对应 REQ 的 ready 项和 P0 优先级，**report 和 plan 必须全部引用**：

- `src/config/constant/campaignType.ts:57-58` (IMP-001, REQ-001) — CampaignType 枚举新增
- ...

## 🟡 Should-Reference Anchors (supporting)

以下对应 P1/P2 或 needs_confirmation，建议引用但不强制：
...

## ⚪ Optional Anchors (context only)

背景信息，可选引用。
```

#### 2. 更新 `step-03-confirm.md` / step-03 段中的 "writing report/plan" 章节

明确 "🔴 Must-Reference 段的每个锚点必须出现在 report.md §5/§6 或 plan.md Implementation Checklist 里"。

### verify

```bash
# context-pack.md 应包含 3 个分级标题
grep -cE "^## (🔴|🟡|⚪)" <fixture>/context/context-pack.md
# expected: 3
```

### commit

```
fix(audit-p2): [P2-1] context-pack.md tiers anchors (must/should/optional) with visual markers
```

---

## P2-2 — step-03-confirm.md 内嵌 HARD STOP 指令

### 现象

实跑时模型能正确暂停等用户确认 report，但这是因为 `.claude/commands/prd-distill.md:77` 有 "STOP after Step 8.1" 指令。如果换 agent 只看 step-03-confirm.md（不看 command.md），会一口气生成 report+plan 一起交。

### 证据

- `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md` 当前无 `HARD STOP` / `report-confirmation` 字样
- 下午 audit 的 P0-3 指出过

### 修复

更新 `plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md`，把 `## 目标` 下的 outputs 拆成两阶段：

```markdown
## 目标

本步骤分为两个阶段，中间必须 HARD STOP。

### 阶段 A — 生成 report.md 后立即暂停

生成以下产物后 **HARD STOP**，写入 `context/report-confirmation.yaml`（status: pending），向用户展示 report 摘要并询问 approved / needs_revision / blocked。

- `_prd-tools/distill/<slug>/report.md`
- `_prd-tools/distill/<slug>/context/report-confirmation.yaml`

**绝对不得在用户回复前生成 plan.md。**

### 阶段 B — 用户 approved 后才继续

仅当 `report-confirmation.yaml` 的 `status: approved` 时，生成：

- `_prd-tools/distill/<slug>/plan.md`
- `_prd-tools/distill/<slug>/context/reference-update-suggestions.yaml`
```

### verify

```bash
grep -cE "HARD STOP" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
# expected: >= 1
grep -c "report-confirmation" plugins/prd-distill/skills/prd-distill/steps/step-03-confirm.md
# expected: >= 2
```

### commit

```
fix(audit-p2): [P2-2] step-03-confirm.md inline HARD STOP instruction between report and plan
```

---

## 完成后验证

所有 P0 修完后，在 `prd-tools` 根目录执行一遍 selfcheck：

```bash
python3 tools/selfcheck/run.py --all
# 目标：0 fail，warn 可保留（但新增 warn 必须 commit message 解释）
```

然后用 `/self-audit --plugin prd-distill --artifact-path /Users/didi/work/dive-bff/_prd-tools` 复跑，预期：

- P0 数量 6 → 0（本文 5 条 P0 全修）
- P1 数量 13 → ≤10
- selfcheck 覆盖率 14% → ≥35%（新增的 check 能捕获 P0-1 / P0-3 / P0-5 这几类）

---

## 不在本次 scope

这些问题识别到了但**先不改**（理由见括号）：

- **Step 0 支持 md/pdf/txt 输入**（ingest-docx 先覆盖最常见 docx，其他格式保留 fallback）
- **Schema_version 从 2.0 再往上升级**（本轮目标是对齐，不是升版）
- **workflow.md Step 文件 ↔ Gate Step ID 映射表**（下午 P0-4，P0-4 本文已靠 command.md 补全 step IDs 列表间接缓解；完整映射表作为下轮 improvement）
- **distill-quality-gate 更细的 AC testability 检查**（复杂度高，风险大）

这些放到下一轮迭代。
