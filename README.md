# PRD Tools：Claude Code 技能

两个可安装的 Claude Code 技能，用于把 PRD 变成可执行、可验证、可回流的工程计划。

## 工作流

```text
PRD
  -> Requirement IR
  -> Layer Impact
  -> Contract Delta
  -> 开发计划 / QA 计划
  -> Reference 回流
  -> 项目 Reference v3
```

## 技能

### /build-reference

构建项目级 `_reference/`，适用于前端、BFF、后端。

```text
_reference/
├── 00-index.md
├── 01-entities.yaml
├── 02-architecture.yaml
├── 03-conventions.yaml
├── 04-constraints.yaml
├── 05-routing.yaml
├── 06-glossary.yaml
├── 07-business-context.yaml
├── 08-contracts.yaml
└── 09-playbooks.yaml
```

核心能力：

- 从源码、历史 PRD、技术方案和分支 diff 构建 Reference v3。
- 用前端/BFF/后端适配器保持通用流程，同时保留层专属关注点。
- 沉淀跨层契约、开发 playbook、QA 矩阵和 golden sample。
- 从 `/prd-distill` 输出中回流术语、路由、契约、playbook 和矛盾修复建议。

### /prd-distill

读取 PRD、技术方案、reference 和源码，输出：

```text
_output/prd-distill/<slug>/
├── evidence.yaml
├── requirement-ir.yaml
├── layer-impact.yaml
├── contract-delta.yaml
├── dev-plan.md
├── qa-plan.md
├── reference-update-suggestions.yaml
└── distilled-report.md
```

核心能力：

- 每个需求都有变更类型、证据、置信度和开放问题。
- 每层影响都经过源码或负向搜索锚定。
- 多层需求自动产出契约差异和契约对齐状态。
- 产出开发计划、QA 计划和 Reference 回流建议。

## 安装

### curl

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash
```

指定目标项目：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash -s /path/to/project
```

### Claude Code 插件市场

在目标项目里打开 Claude Code：

```bash
claude
```

1. 输入 `/plugin`
2. 添加插件市场
3. 输入：
   ```text
   git@github.com:zachary-lz-glm/prd-tools.git
   ```
4. 在插件发现列表中启用 `build-reference` 和 `prd-distill`

### 手动安装

```bash
TARGET="/path/to/your/project"
git clone --depth 1 https://github.com/zachary-lz-glm/prd-tools.git /tmp/prd-tools
mkdir -p "$TARGET/.claude/skills"
cp -r /tmp/prd-tools/plugins/build-reference/skills/build-reference "$TARGET/.claude/skills/"
cp -r /tmp/prd-tools/plugins/prd-distill/skills/prd-distill "$TARGET/.claude/skills/"
```

## 使用方式

首次使用或项目结构变化后：

```text
/build-reference
```

拿到新 PRD 后：

```text
/prd-distill
```

## 设计原则

- Reference 是持久项目知识，不是一次性提示词。
- 源码和技术文档是最终证据，reference 是快速通道。
- 层差异通过适配器表达，不拆成三套工作流。
- 多层需求必须显式处理契约。
- 每次真实需求结束后，把矛盾和新增知识回流到 reference。
