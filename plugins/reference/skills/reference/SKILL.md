---
name: reference
description: 为前端、BFF、后端通用的 PRD-to-code 工作流构建、更新、健康检查或回流项目 reference 知识库。适用于用户调用 /reference，要求建立项目知识库、检查 _prd-tools/reference 是否过期、沉淀接口契约/业务术语/开发打法、把 PRD 交付经验反馈回流、准备后续 /prd-distill 时。
---

# reference

Claude Code 中通过 `/reference` 触发。

人类可读文档见插件根目录 `README.md`。

## Step Gate Enforcement（硬约束）

**每步执行前必须运行 step gate，并传入 `--write-state`：**

```bash
python3 .prd-tools/scripts/reference-step-gate.py --step <step_id> --root . --write-state
```

Step IDs: `0`, `1`, `2a`, `2b`, `2c`, `2d`, `2e`, `3`, `3.5`, `3.6`, `4`

If the step gate exits with code 2 (FAIL):
- **STOP immediately** — do not proceed with the step.
- Read the error message — it tells you which prerequisite is missing.
- Complete the missing prerequisite step first, then re-run the step gate.
- Only proceed after the step gate exits with code 0 (PASS).

**Workflow State File**: `_prd-tools/build/reference-workflow-state.yaml`

- Before each step, read this file. If it does not exist, the step gate with `--write-state` will create it.
- After each step, the gate updates it with output files and hashes.
- The next step MUST read this state file before proceeding — do not rely on conversation memory.

**禁止行为：**
- 不得跳过 step gate 直接执行步骤
- 不得在 gate 失败后手动创建缺失文件绕过检查
- 不得合并多个步骤为一次执行

## Final Completion Gate（硬约束）

/reference 全量构建完成必须满足以下条件，缺一不可：

1. `_prd-tools/reference/` 下 00-05 共 6 个主文件 + `project-profile.yaml` 存在且非空。
2. 必须运行 `python3 .prd-tools/scripts/build-index.py --repo <项目路径> --out _prd-tools/reference/index`，生成 `index/` 下 4 个文件。
3. 必须运行 `python3 .prd-tools/scripts/render-reference-portal.py --root . --template .prd-tools/assets/reference-portal-template.html --out _prd-tools/reference/portal.html` 生成 `portal.html`。AI 不得手写 portal.html。
4. 必须运行 `python3 .prd-tools/scripts/reference-quality-gate.py --root .`，且 exit code 不为 2。
5. index 缺失时，不得宣称 /reference 完成。
6. portal.html 缺失时，不得宣称 /reference 完成。
7. 最终回复必须列出 index manifest 摘要（实体数、边数、term 数）。
8. quality-gate 报告的 warning 必须在最终回复中说明。
9. portal.html 是脚本渲染产物，风格由固定模板决定，AI 不得手写或修改其内容。

## 触发条件

- 用户说"构建/更新/检查 reference"、"项目知识库"、"初始化"。
- `/reference` 命令。
- prd-distill 完成后用户要求回流经验。

不触发：只解释代码、直接改代码、无源码无上下文。

## 工作模式选择

`/reference` 必须先进入人机模式选择，不得默认一路全自动构建。

先检查 `_prd-tools/reference/` 是否存在：
- 不存在 → 建议 Mode F（上下文收集）→ Mode A（全量构建）。
- 已存在 → 按用户目标执行 B/B2/C/E。

| 模式 | 何时 | 输出 |
|---|---|---|
| F 上下文收集 | 首次建设前 | `_prd-tools/build/context-enrichment.yaml` |
| A 全量构建 | 首次或重建 | `_prd-tools/reference/` |
| B 增量更新 | git diff 或新证据 | 更新后的 `_prd-tools/reference/` |
| B2 健康检查 | 是否过期/缺证据 | `_prd-tools/build/health-check.yaml` |
| C 质量门控 | 证据/契约闭环/幻觉 | `_prd-tools/build/quality-report.yaml` |
| E 反馈回流 | prd-distill 输出回收 | `_prd-tools/build/feedback-report.yaml` |
| T 团队聚合 | 在团队仓执行，从成员仓聚合 | `team/*.yaml` + `snapshots/` + `build/conflicts.yaml` |
| T2 团队继承 | 在成员仓执行，从团队仓继承 | 更新后的 `_prd-tools/reference/` |

### Mode Selection Gate

执行任何会写 `_prd-tools/reference/` 的动作前，必须先向用户展示当前状态和模式选项，并等待确认。

展示内容：

- 当前 `_prd-tools/reference/` 是否存在。
- 当前 `_prd-tools/build/` 是否存在历史上下文或质量报告。
- 推荐模式和原因。
- 可选模式：F→A、F only、A only、B、B2、C、E、T、T2、Chat。

默认推荐：

- 首次建设：推荐 `F→A`，但必须等用户确认。
- 已有 reference：推荐 `B2` 健康检查或 `B` 增量更新，除非用户明确要求重建。
- 团队仓（`project-profile.yaml` 含 `layer: team-common`）：推荐 `T` 团队聚合。
- 成员仓且已配置 `team_reference.upstream_local_path`：可推荐 `T2` 团队继承。

用户确认后，将选择写入 `_prd-tools/build/reference-workflow-state.yaml`。YAML 结构见 `references/mode-selection.schema.md`。

如果用户选择 Chat，只讨论方案，不生成或修改 reference 产物。

## 输入

- 当前项目路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- 历史 PRD、技术方案、接口文档、分支 diff。
- 已有 `_prd-tools/reference/` 和 `_prd-tools/build/`。

无历史样例时也可构建，但标注业务语义低置信度。

## 输出结构

```text
_prd-tools/reference/           # 长期知识库（v4.0，6 文件）
├── 00-portal.md               # 人类导航 + 场景阅读指南
├── project-profile.yaml       # 项目画像
├── 01-codebase.yaml           # 代码库静态清单
├── 02-coding-rules.yaml       # 编码规则
├── 03-contracts.yaml          # 跨层和外部契约
├── 04-routing-playbooks.yaml  # PRD 路由信号 + 场景打法
├── 05-domain.yaml             # 业务领域知识
├── portal.html                # 可视化浏览器页面（零外部依赖）
└── index/                     # Evidence Index（辅助层，v2.16+）
    ├── entities.json          # 代码实体索引
    ├── edges.json             # 实体关系索引
    ├── inverted-index.json    # 倒排索引（term→entity）
    └── manifest.yaml          # 索引元数据

_prd-tools/build/              # 过程和质量报告
├── context-enrichment.yaml
├── modules-index.yaml
├── health-check.yaml
├── quality-report.yaml
└── feedback-report.yaml
```

兼容读取 v3.1（`01-entities.yaml` ~ `09-playbooks.yaml`），自动映射到 v4.0。

## 能力面适配器

前端、BFF、后端共用流程，不绑定固定目录。读取 `references/layer-adapters.md`。

路径只是候选，结论必须来自源码、配置、类型定义、注册点、调用链、测试或负向搜索。

## 文件边界（v4.0 SSOT）

| 文件 | 只放 | 不放 |
|---|---|---|
| `01-codebase` | 静态事实（目录、枚举、模块、注册点、数据流） | 字段级契约、编码规则、实现步骤 |
| `02-coding-rules` | 编码规则（severity 区分软硬）、踩坑经验 | 契约字段、打法步骤 |
| `03-contracts` | 跨层和外部契约的字段级定义（唯一权威来源） | 编码规则、开发步骤、枚举值列表 |
| `04-routing-playbooks` | 信号→能力面映射 + playbook + QA 矩阵 | 枚举值、字段级契约、编码规则 |
| `05-domain` | 业务领域知识（术语、背景、隐式规则、决策日志） | 代码路径、编码规则、契约字段 |

跨文件引用：`contract_ref` → `03-contracts`，`ref_rule` → `02-coding-rules`，`playbook_ref` → `04-routing-playbooks`。

## 证据规则

- 源码、PRD、技术文档、API 文档、git diff 是权威证据。reference 是加速器。
- 当前仓源码只能证明当前仓事实；跨仓必须由对方 owner 确认。
- 枚举、字段、方法签名不能从文件名或 import 推断，必须读源文件。
- 搜不到也是证据 → `negative_code_search`（记录 query 和范围）。
- 不确定写 `confidence: low`，进入开放问题。
- 关键事实必须有 `evidence`、`verified_by` 或负向搜索。

## 执行步骤

1. 识别项目路径、层级、已有 `_prd-tools/reference/` 和 `_prd-tools/build/`。
2. 根据用户目标选择模式。
3. 限定在当前项目内搜索，不跨兄弟项目。
4. 标注 `reference_scope.authority: single_repo`，跨仓线索写确认状态字段。
5. 用 `rg`/glob 找候选，再 Read 源码确认事实。
6. 生成或更新 `_prd-tools/reference/`。
7. 构建 Evidence Index（辅助层）：`python3 .prd-tools/scripts/build-index.py --repo <项目路径> --out _prd-tools/reference/index`。
8. 生成 `portal.html`（详见 `steps/step-05-portal.md`）。
9. 执行健康检查或质量门控。
10. 给用户摘要：新增/更新文件、质量状态、风险、下一步。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 完整构建/健康检查/质量门控/反馈回流时 |
| `references/reference-v4.md` | 确认文件职责、边界、质量规则时 |
| `references/layer-adapters.md` | 判断前端/BFF/后端能力面时 |
| `references/output-contracts.md` | 输出契约索引（按需加载 `schemas/` 下具体文件） |
| `templates/*.yaml` | 创建 reference 骨架时 |
| `references/selectable-reward-golden-sample.md` | 需要示例或校准复杂需求时 |
| `references/portal-design-system.md` | 生成 portal.html 时读取设计系统 |
| `steps/step-05-portal.md` | 生成 portal.html 可视化页面时 |

## 完成标准

完成后必须说明：
- `_prd-tools/reference/` 新增或更新了哪些文件。
- reference 健康状态：pass / warning / fail。
- 哪些关键事实证据充分，哪些 low confidence。
- 是否存在跨层契约 owner 未确认。
- 下一步：运行 `prd-distill`，还是继续补历史样例或修复 reference。
