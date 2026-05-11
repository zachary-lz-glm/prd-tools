# PRD Tools

PRD Tools 把 PRD 从"自然语言需求"转成"有证据、可执行、可测试"的开发计划，运行在 Claude Code 中，零外部依赖。

## Quick Start

```bash
# 1. 安装（指定目标项目目录）
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/v2.0/install.sh | bash -s /path/to/project

# 2. 重启 Claude Code，然后构建项目知识库
/reference

# 3. 蒸馏一个新 PRD
/prd-distill path/to/prd.md
```

安装完成后目标项目下生成 `.claude/skills/`（两个 skill）、`.prd-tools/scripts/`（零依赖 runtime 辅助脚本）和 `.prd-tools-version`（版本标记）。

离线安装：下载 `install.sh` 到本地后 `bash install.sh /path/to/project`。

## 两个 Skill

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| `/reference` | 扫描项目源码、历史 PRD、技术方案，构建 `_prd-tools/reference/` 知识库 | 首次接入、项目结构大变、需求结束后回流新知识 |
| `/prd-distill` | 读取 PRD + 知识库 + 源码，输出结构化分析报告和开发计划 | 每次拿到新 PRD 时 |

详细使用说明见 [`plugins/reference/README.md`](plugins/reference/README.md) 和 [`plugins/prd-distill/README.md`](plugins/prd-distill/README.md)。

### reference 支持模式

| 模式 | 用途 |
|---|---|
| `F 上下文收集` | 收集历史 PRD、技术方案、分支 diff |
| `A 全量构建` | 首次构建项目知识库 |
| `B 增量更新` | 根据代码变化更新部分 reference |
| `B2 健康检查` | 检查 reference 是否完整、过期或矛盾 |
| `C 质量门控` | 检查证据闭环、源码一致性、幻觉风险 |
| `E 反馈回流` | 把 prd-distill 产出的新知识写回 reference |

## 支持的输入

`.md` / `.txt` / `.docx` 文件，或直接粘贴需求文本。`.docx` 用原生 `unzip` 提取文本和图片，Claude 直接看图理解 UI 截图和流程图，零外部依赖。

## 产出文件

### 项目知识库：`_prd-tools/reference/`

```text
_prd-tools/reference/
├── 00-portal.md                # 人类导航 + 按场景阅读指南
├── project-profile.yaml        # 项目画像（技术栈、入口、能力面）
├── 01-codebase.yaml            # 代码库静态清单
├── 02-coding-rules.yaml        # 编码规则和踩坑经验
├── 03-contracts.yaml           # 跨层和外部契约（字段级）
├── 04-routing-playbooks.yaml   # PRD 路由信号 + 场景打法 + QA 矩阵
├── 05-domain.yaml              # 业务领域知识（术语、隐式规则、决策日志）
├── portal.html                 # 可视化浏览器页面（脚本渲染，零外部依赖，双击即可打开）
└── index/                      # Evidence Index：给 prd-distill 用的机器检索辅助层
    ├── manifest.yaml
    ├── entities.json
    ├── edges.json
    └── inverted-index.json
```

核心原则：**每个事实只存在于一个文件（SSOT）**，其他文件通过 ID 引用。

### PRD 蒸馏产物

```text
_prd-tools/distill/<slug>/
├── _ingest/           # PRD 读取证据（source-manifest、document、quality gate）
├── spec/              # AI-friendly PRD（规范化中间层）
│   └── ai-friendly-prd.md  # 13-section 对 AI agent 友好的 PRD
├── report.md          # 需求摘要 → 变更明细 → 字段清单 → 校验规则 → 契约风险 → 阻塞问题
├── plan.md            # 实现顺序（精确到文件路径）、QA 矩阵、回滚方案
├── portal.html        # 可视化浏览器页面（脚本渲染，零外部依赖，双击即可打开）
└── context/           # 机器可读的中间产物
    ├── prd-quality-report.yaml  # AI-friendly PRD 质量评分
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── query-plan.yaml
    ├── context-pack.md
    ├── final-quality-gate.yaml
    ├── readiness-report.yaml
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

**人类阅读顺序**：`report.md` → `plan.md` → `context/readiness-report.yaml`。也可以直接在浏览器中打开 `portal.html` 一站式浏览所有内容。YAML 文件供审计和工具消费，普通评审不需要看。

## How It Works

```text
PRD / 技术方案 / 源码 / 历史 diff
        ↓
/reference
        ↓
项目知识库 _prd-tools/reference/
        ↓
/prd-distill
        ↓
report / plan / context
        ↓
反馈回流到 _prd-tools/reference/
```

PRD Tools 不把"前端/BFF/后端"写死成固定目录结构，而是通过**能力面**（如路由、组件、表单 schema、状态流、契约、校验等）适配不同项目。路径只是搜索候选，最终结论必须来自源码、类型定义、调用链或测试证据。

## When to Use / When Not

适用：

- 前端、BFF、后端业务项目，需要频繁根据 PRD 改代码
- 跨团队字段、接口、契约协作较多的项目
- 希望让 AI 输出可执行工程计划而非泛泛分析的团队

不适用：

- 一次性 demo、无长期维护价值的小项目
- 没有源码、没有 PRD 的纯脑暴场景
- 希望 AI 直接跳过分析、大范围改代码的场景

## 推荐落地路径

**首次接入**：

1. 安装 PRD Tools，准备 1-3 个历史 PRD 和技术方案。
2. `/reference` Mode F（上下文收集）→ Mode A（全量构建）。
3. Mode B2（健康检查）+ Mode C（质量门控）。
4. 用一个新 PRD 运行 `/prd-distill`，检查输出质量。

**日常使用**：

1. 新需求进来 → `/prd-distill`。
2. 研发和 QA 看 `report.md` + `plan.md`。
3. 需求完成 → `/reference` Mode E（反馈回流）写回新知识。

## 质量门禁脚本

安装后 `.prd-tools/scripts/` 包含两个 completion gate 脚本，可独立运行检查产出完整性：

### reference-quality-gate.py

检查 `/reference` 产出是否满足最低完成标准：

```bash
python3 .prd-tools/scripts/reference-quality-gate.py --root .
```

检查项：required reference files 存在且非空、index 四文件存在且非空、portal.html 存在且非空且包含脚本渲染标记、YAML 基本可读、schema_version 存在、自然语言英文占比（warning）。Exit code：0 = pass/warning，2 = fail。

### distill-quality-gate.py

检查 `/prd-distill` 产出是否满足 AI-friendly pipeline 最低完成标准：

```bash
python3 .prd-tools/scripts/distill-quality-gate.py \
  --distill-dir _prd-tools/distill/<slug> --repo-root .
```

检查项：required distill files 存在且非空、ai-friendly-prd.md 包含 13 章节、prd-quality-report.yaml 有 status/score、requirement-ir.yaml 有 ai_prd_req_id 和 planning eligibility、layer-impact.yaml 有 code_anchors 或 fallback、reference/index 存在时 query-plan.yaml 和 context-pack.md 必须存在、final-quality-gate.yaml 存在、report.md 包含 PRD 质量摘要、plan.md 不把 missing_confirmation 当确定任务。Exit code：0 = pass/warning，2 = fail。

## Portal 页面渲染

`portal.html` 由固定 HTML 模板 + Python 渲染脚本生成，AI 不得手写。渲染流程：

1. 编辑对应插件的 `portal-template.html`（修改布局、样式、占位符）
2. 运行渲染脚本：
   - reference: `python3 .prd-tools/scripts/render-reference-portal.py --root . --template .prd-tools/assets/reference-portal-template.html --out _prd-tools/reference/portal.html`
   - distill: `python3 .prd-tools/scripts/render-distill-portal.py --distill-dir _prd-tools/distill/<slug> --template .prd-tools/assets/distill-portal-template.html --out _prd-tools/distill/<slug>/portal.html`
3. 脚本读取模板，注入数据，输出 `portal.html`
4. 任何对 `portal.html` 的直接手写修改都会在下次渲染时被覆盖

## 输出语言规则

- YAML/JSON schema key 保持英文。
- 代码路径、函数名、类名、接口名、字段名、API path、枚举值、配置 key 保持原样。
- 源码事实不翻译、不改写、不补业务含义。
- 人类可读说明可以用中文，但不能为了中文友好给 enum、字段、接口补释义。

## 质量原则

- 源码和技术文档是最终证据，reference 是加速器。
- 不确定就标低置信度，不让 AI 补脑。
- 多层需求必须显式处理契约。
- 业务关键规则不能只靠前端守。
- 每个输出都要能回溯 evidence。
- 每次真实需求结束后，把新增知识和踩坑回流到 reference。

## 版本与发版

仓库根目录 `VERSION` 是工具版本，5 处版本号保持一致（lockstep versioning）。

使用 Conventional Commits 规范提交，post-commit hook 自动触发发版：

| 提交前缀 | 版本变更 |
|---|---|
| `feat:` | minor（2.10.3 → 2.11.0） |
| `fix:` | patch（2.10.3 → 2.10.4） |
| `feat!:` / `BREAKING CHANGE:` | major（2.10.3 → 3.0.0） |
| `docs:` / `chore:` / `refactor:` | 不触发 |

临时禁用：`PRD_TOOLS_NO_AUTO_RELEASE=1 git commit -m "feat: ..."`
