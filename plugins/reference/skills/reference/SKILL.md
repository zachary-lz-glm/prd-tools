---
name: reference
description: 为前端、BFF、后端通用的 PRD-to-code 工作流构建、更新、健康检查或回流项目 reference 知识库。适用于用户调用 /reference，要求建立项目知识库、检查 _prd-tools/reference 是否过期、沉淀接口契约/业务术语/开发打法、把 PRD 交付经验反馈回流、准备后续 /prd-distill 时。
---

# reference

通过 `/reference` 触发。

人类可读文档见插件根目录 `README.md`。

## 触发条件

- 用户说"构建/更新/检查 reference"、"项目知识库"、"初始化"。
- `/reference` 命令。
- prd-distill 完成后用户要求回流经验。

不触发：只解释代码、直接改代码、无源码无上下文。

## 工作模式选择

`/reference` 先检查 `_prd-tools/reference/` 是否存在：
- 不存在 → 建议 Mode F（上下文收集）→ Mode A（全量构建）。
- 已存在 → 按用户目标执行 B/B2/C/E。

向用户展示当前状态和模式选项，等用户确认后再执行。

| 模式 | 何时 | 输出 |
|---|---|---|
| F 上下文收集 | 首次建设前 | `_prd-tools/build/context-enrichment.yaml` |
| A 全量构建 | 首次或重建 | `_prd-tools/reference/` |
| B 增量更新 | git diff 或新证据 | 更新后的 `_prd-tools/reference/` |
| B2 健康检查 | 是否过期/缺证据 | `_prd-tools/build/health-check.yaml` |
| C 质量门控 | 证据/契约闭环/幻觉 | `_prd-tools/build/quality-report.yaml` |
| E 反馈回流 | prd-distill 输出回收 | `_prd-tools/build/feedback-report.yaml` |

团队模式（Mode T 收集）详见 `/team-reference`。

## 输入

- 当前项目路径。
- 可选层级提示：`frontend | bff | backend | multi-layer`。
- 历史 PRD、技术方案、接口文档、分支 diff。
- 已有 `_prd-tools/reference/` 和 `_prd-tools/build/`。

无历史样例时也可构建，但标注业务语义低置信度。

## 输出结构

```text
_prd-tools/reference/           # 长期知识库（v4.0，6 文件）
├── 00-portal.md                # 人类导航入口
├── project-profile.yaml       # 项目画像
├── 01-codebase.yaml           # 代码库静态清单
├── 02-coding-rules.yaml       # 编码规则
├── 03-contracts.yaml          # 跨层和外部契约
├── 04-routing-playbooks.yaml  # PRD 路由信号 + 场景打法
├── 05-domain.yaml             # 业务领域知识
└── index/                     # Evidence Index（辅助层）
    ├── entities.json
    ├── edges.json
    ├── inverted-index.json
    └── manifest.yaml

_prd-tools/build/              # 过程和质量报告
├── context-enrichment.yaml
├── modules-index.yaml
├── health-check.yaml
├── quality-report.yaml
└── feedback-report.yaml
```

兼容读取 v3.1，自动映射到 v4.0。

## 能力面适配器

前端、BFF、后端共用流程。读取 `references/layer-adapters.md`。路径只是候选，结论必须来自源码确认。

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

- 源码、PRD、技术文档、API 文档、git diff 是权威证据。
- 枚举、字段、方法签名必须读源文件确认。
- 搜不到也是证据 → `negative_code_search`。
- 不确定写 `confidence: low`。
- 关键事实必须有 `evidence`、`verified_by` 或负向搜索。

## 执行步骤

1. 识别项目路径、层级、已有 reference。
2. 根据用户目标选择模式。
3. 限定在当前项目内搜索。
4. 用 `rg`/glob 找候选，再 Read 源码确认事实。
5. 生成或更新 `_prd-tools/reference/`。
6. 构建 Evidence Index：`python3 .prd-tools/scripts/build-index.py --repo <项目路径> --out _prd-tools/reference/index`。
7. 执行健康检查或质量门控。
8. 给用户摘要：新增/更新文件、质量状态、风险。

## 参考文件

| 文件 | 何时读取 |
|---|---|
| `workflow.md` | 完整构建/健康检查/质量门控/反馈回流时 |
| `references/reference-v4.md` | 确认文件职责、边界、质量规则时 |
| `references/layer-adapters.md` | 判断前端/BFF/后端能力面时 |
| `references/output-contracts.md` | 输出契约索引 |
| `templates/*.yaml` | 创建 reference 骨架时 |

## 完成标准

完成后必须说明：
- `_prd-tools/reference/` 新增或更新了哪些文件。
- reference 健康状态：pass / warning / fail。
- 哪些关键事实证据充分，哪些 low confidence。
- 是否存在跨层契约 owner 未确认。
