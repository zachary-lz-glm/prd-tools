# P2 修复清单

> **前置**：P0、P1 全部做完。P2 属于可读性/可维护性改进，可选做。每个 FIX 独立 commit，prefix `refactor(audit-p2): [P2-x] ...`。
>
> 如果时间/精力有限，P2 可跳过。但如果要做，仍然严格按 FIX 逐个来，每个 FIX 一个 commit。

---

## P2-1 — `*-step-gate.py` 默认 `tool_version` 过时（2.17.0）

### 问题
- `scripts/distill-step-gate.py:335` 和 `scripts/reference-step-gate.py:228` 都默认 `--tool-version 2.17.0`
- 当前 VERSION = 2.18.1
- workflow-state.yaml 里的 tool_version 会被当前默认值污染

### 修复
让脚本读 `VERSION` 文件而不是硬编码：

```python
# 脚本顶部
def _default_tool_version():
    try:
        version_file = Path(__file__).resolve().parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    return "unknown"

# 在 argparse 的 add_argument 里
parser.add_argument("--tool-version", default=_default_tool_version())
```

**两个脚本都改**。

### verify
```bash
python3 scripts/distill-step-gate.py --help | grep -i "tool-version"
python3 scripts/reference-step-gate.py --help | grep -i "tool-version"
```
**期望**：默认值显示为 `2.18.1`。

### commit
```
refactor(audit-p2): [P2-1] step-gate default tool-version reads VERSION file
```

---

## P2-2 — `--step 8.1` 报 "Unknown step ID"（实际是 `8.1-confirm`）

### 问题
workflow.md 和 SKILL.md 里写 "Step 8.1"，但 step-gate 里注册的 key 是 `8.1-confirm`。用户按文档跑 `--step 8.1` 报错。

### 修复
在 `distill-step-gate.py` 的 STEP_TABLE 查表前加 alias：

```python
STEP_ALIASES = {
    "8.1": "8.1-confirm",
}

def resolve_step(step_id):
    return STEP_ALIASES.get(step_id, step_id)

# 调用 STEP_TABLE 前：
args.step = resolve_step(args.step)
```

### verify
```bash
python3 scripts/distill-step-gate.py --distill-dir /tmp/nonexistent --step 8.1 2>&1 | rg -q "Unknown step" && echo "still broken" || echo "alias works (may fail for other reasons but not Unknown step)"
```

### commit
```
refactor(audit-p2): [P2-2] accept --step 8.1 as alias for 8.1-confirm
```

---

## P2-3 — `final-quality-gate.py` KEY_ANCHOR_FILES 硬编码 dive-bff 文件

### 问题
`scripts/final-quality-gate.py:75-84` 硬编码 `campaignType.ts / previewRewardType.ts / rewardCondition.ts / basic.ts / message.ts`。复用到其他项目永远 score cap 40。

### 修复
从 `_prd-tools/reference/04-routing-playbooks.yaml` 动态读 anchor 文件：

```python
def load_key_anchors(repo_root):
    """Load key anchor files from routing-playbooks, fall back to hardcoded."""
    rp = repo_root / "_prd-tools" / "reference" / "04-routing-playbooks.yaml"
    if rp.exists():
        try:
            import yaml
            data = yaml.safe_load(rp.read_text()) or {}
            # routing-playbooks schema has golden_samples / prd_routing with file refs
            anchors = []
            for route in data.get('prd_routing', []):
                for f in route.get('key_files', []):
                    anchors.append(f)
            if anchors:
                return anchors
        except Exception:
            pass
    return KEY_ANCHOR_FILES_DEFAULT  # 现有的硬编码作 fallback

KEY_ANCHOR_FILES_DEFAULT = [
    # ... 原有 dive-bff 清单保留作 fallback
]
```

### verify
```bash
rg -n "load_key_anchors|KEY_ANCHOR_FILES_DEFAULT" scripts/final-quality-gate.py
```

### commit
```
refactor(audit-p2): [P2-3] final-quality-gate reads anchors from routing-playbooks
```

---

## P2-4 — `context-pack.py` seed_queries 硬编码 dive-bff 业务词

### 问题
`scripts/context-pack.py:452-460` 硬编码 `CampaignType / getDetailsTemplate / courierDxGy / gasStation`。其他项目命中率很低。

### 修复
同 P2-3 思路，从 routing-playbooks 提取：

```python
def load_seed_queries(repo_root):
    # 从 reference/04-routing-playbooks.yaml 的 golden_samples / prd_routing 提取
    # fallback 到现有硬编码
    ...
```

### verify
```bash
rg -n "load_seed_queries" scripts/context-pack.py
```

### commit
```
refactor(audit-p2): [P2-4] context-pack seed_queries derived from routing-playbooks
```

---

## P2-5 — `output-contracts.md` 仍描述 `graph/` 子目录（v2.18 已删 agent）

### 问题
`plugins/prd-distill/skills/prd-distill/references/output-contracts.md:31-35`:
```
└── graph/
    ├── sync-report.yaml
    ├── code-evidence.yaml
    └── business-evidence.yaml
```
这些在 v2.18 "删除 agent" commit 后已经不生成。

### 修复
删除该目录描述块。如果其他地方还有引用 `graph/sync-report.yaml` 等路径，同步删或改成"(deprecated in v2.18)"。

### verify
```bash
rg -n "graph/sync-report|graph/code-evidence|graph/business-evidence" plugins/
```
**期望**：无命中。

### commit
```
refactor(audit-p2): [P2-5] remove deprecated graph/ subtree from output-contracts
```

---

## P2-6 — `workflow.md` Step 8.6 出现两次（同标题，不同内容）

### 问题
`workflow.md` 里 "## 步骤 8.6：Distill Completion Gate" 出现两次，L746 是详细版（硬约束描述），L776 是条件步骤版（检查清单）。标题相同内容不同。

### 修复
两种处理方式，选一：
- **方式 A**：把 L776 的标题改为 "## 步骤 8.6.1：Gate 检查清单"，内容保留。
- **方式 B**：把 L776-L788 的内容合并到 L746 那段，形成一个完整的 8.6。

**推荐方式 A**（侵入性小）。

### verify
```bash
rg -c "^## 步骤 8\.6：" plugins/prd-distill/skills/prd-distill/workflow.md
```
**期望**：`1`。

### commit
```
refactor(audit-p2): [P2-6] split duplicate Step 8.6 headings
```

---

## P2-7 — Phase 3.6 Critique Pass 是"幻影步骤"

### 问题
- `SKILL.md` step 列表里有 `3.6`
- `workflow.md` 从 L26 Phase 表到 L261 Phase 3.5 结束，Phase 4 直接接上，**Phase 3.6 整段缺失**
- 若 step-gate 的 STEP_TABLE 里有 `3.6`，用户按 SKILL 跑 `--step 3.6` 会得到 cryptic 错误

### 修复
两种方式：
- **A**：在 `workflow.md` 补上 Phase 3.6 章节（参考 `references/critique-template.md` 描述 Two-Pass Critic）。
- **B**：从 SKILL.md step 列表删掉 3.6，保持"3.6 未实装"现状。

**推荐方式 A**。3.6 是 Two-Pass Critic 的入口，有存在意义。

补写的章节应包含：
- 何时触发（高风险 step 后）
- 输入：context/critique/<step>.yaml 或 空白新建
- 输出：critique 结论，fail 时退回上一步
- 运行方式（若有脚本）或 LLM 手动检查清单

### verify
```bash
rg -c "^## 步骤 3\.6" plugins/prd-distill/skills/prd-distill/workflow.md
rg -c "^## Phase 3\.6" plugins/prd-distill/skills/prd-distill/workflow.md
```
**期望**：至少其中一个命中 `1`。

### commit
```
refactor(audit-p2): [P2-7] materialize Phase 3.6 Critique Pass in workflow.md
```

---

## P2-8 — `step-04-portal.md` `<current_step>4</current_step>` 与 step-gate `--step 9` 错配

### 问题
step 文件内部声明 `<current_step>4</current_step>`，但 step-gate 用 `--step 9` 调用 portal。语义错位。

### 修复
**以 step-gate 为准**（脚本是执行方，文档应对齐）：
- 把 `step-04-portal.md` 内部的 `<current_step>4</current_step>` 改为 `<current_step>9</current_step>`。
- 如果文件名 `step-04-portal.md` 本身也引起语义混淆，**不改文件名**（改名影响太多引用，留到下次重构）。

### verify
```bash
rg -n "<current_step>" plugins/prd-distill/skills/prd-distill/steps/step-04-portal.md
```
**期望**：`<current_step>9</current_step>`。

### commit
```
refactor(audit-p2): [P2-8] step-04-portal current_step aligns to gate --step 9
```

---

## P2-9 — plan.md 章节数三处说法不一（10 / 11 / 12）

### 问题
- `workflow.md:565` "10 个章节"
- `steps/step-03-confirm.md:117` "必须包含以下 12 个章节"（实际列 11 个）
- `steps/step-03-confirm.md:203` "§1-§11，§11 可选"

### 修复
**以 step-03-confirm.md 实际列的章节数为准**。先读文件确认实际数量，然后把三处说法统一到这个数（大概率是 11）。

### verify
```bash
rg -n "plan.md.*章节|章节.*plan" plugins/prd-distill/skills/prd-distill/
```
**期望**：所有命中的章节数一致。

### commit
```
refactor(audit-p2): [P2-9] unify plan.md section count across docs
```

---

## P2-10 — Mode Selection YAML 三份副本字段不一致

### 问题
Mode Selection YAML 在 SKILL.md / command.md / workflow.md 三处示例，字段不一致（`confirmed_by` 存在与否、`selected_mode` 命名等），脚本实际写的又是第四种。

### 修复

1. 在 `plugins/*/skills/*/references/` 下新增 `mode-selection.schema.md`（或复用 canonical 目录），写明权威 schema：
   ```yaml
   human_checkpoints:
     mode_selection:
       status: approved  # enum: pending, approved, skipped
       selected_mode: "F_then_A"  # enum from command.md
       timestamp: "2026-05-12T..."
   ```
2. 其他三处文档改为**引用**这份 schema，不重写字段：
   ```markdown
   Mode Selection 写入的 YAML 结构见 `references/mode-selection.schema.md`。
   ```
3. 对照脚本 `set_human_checkpoint("mode_selection", ...)` 的实际实现（`scripts/workflow_state.py` 或类似），确保写入字段与 schema 一致。

### verify
```bash
test -f plugins/reference/skills/reference/references/mode-selection.schema.md || \
test -f plugins/prd-distill/skills/prd-distill/references/mode-selection.schema.md
```

### commit
```
refactor(audit-p2): [P2-10] single canonical mode-selection schema
```

---

## P2-11 — Portal 漏渲染 EV-PRD-010/011 + graph-context 编造接口路径

### 问题（两件小事合并）

**A. Portal 漏渲染 EV-PRD**
产物 `portal.html` 只渲染 EV-PRD-001~009，EV-PRD-010/011 存在于 evidence.yaml 但 portal 没渲染。根因：渲染脚本只把"被 IR 引用的 EV"塞进 portal，不做全集校验。

**B. graph-context 编造接口路径**
graph-context.md 里写"推测接口路径为 `/schema/dlpTripChallengeStatus`"——纯编。真实接口有前缀（`/gulfstream/dive-editor/v2/bff/schema/...`），推测不准且 confidence 无标注。

### 修复

**A**：在 `scripts/render-distill-portal.py` 里（或 portal 渲染对应脚本），把"只渲染被引用的 EV"改为"渲染全集"。或者加一条 Self-Check 约束：`portal.html` 的 EV 集合必须 ⊇ evidence.yaml 的 EV 集合。

**B**：在 graph-context 生成 step 里加一条 Self-Check：
```markdown
- [M] 所有"推测"/"speculative"信息必须加 `⚠ speculative, confidence=<low|medium>, verify before use` 前缀，否则不得出现在 graph-context.md。
```

### verify
```bash
# A: portal 渲染脚本里有全集校验
rg -n "evidence.yaml" scripts/render-distill-portal.py || rg -n "portal.*evidence" scripts/
# B: step 文件有 speculative 约束
rg -c "speculative" plugins/prd-distill/skills/prd-distill/steps/
```

### commit
```
refactor(audit-p2): [P2-11] portal renders full EV set + speculative tagging
```
