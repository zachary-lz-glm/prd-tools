# PRD Tools：Claude Code / Codex 技能

两个可安装的 AI 工程技能，用于把 PRD 变成可执行、可验证、可回流的工程计划。Claude Code 使用 slash command，Codex 使用原生 skill 触发。

当前版本：`2.1.0`

## 工作流

```text
PRD
  -> report.md
  -> plan.md
  -> questions.md
  -> artifacts/Requirement IR + Layer Impact + Contract Delta
  -> Reference 回流
  -> 项目 Reference v3.1
```

## 技能

### /build-reference

构建项目级 `_reference/`，适用于前端、BFF、后端。v2.1 默认使用“能力面适配器”，不绑定固定目录结构。

```text
_reference/
├── 00-index.md 或 README.md
├── project-profile.yaml
├── contracts.yaml 或 08-contracts.yaml
├── playbooks.yaml 或 09-playbooks.yaml
└── artifacts/ 或 01~09 兼容细节
```

核心能力：

- 从源码、历史 PRD、技术方案和分支 diff 构建 Reference v3.1。
- 用前端/BFF/后端能力面适配器保持通用流程，同时适配不同项目结构。
- 沉淀跨层契约、开发 playbook、QA 矩阵和 golden sample。
- 从 `/prd-distill` 输出中回流术语、路由、契约、playbook 和矛盾修复建议。

### /prd-distill

读取 PRD、技术方案、reference 和源码，输出：

```text
_output/prd-distill/<slug>/
├── report.md
├── plan.md
├── questions.md
└── artifacts/
    ├── evidence.yaml
    ├── requirement-ir.yaml
    ├── layer-impact.yaml
    ├── contract-delta.yaml
    └── reference-update-suggestions.yaml
```

核心能力：

- 每个需求都有变更类型、证据、置信度和开放问题。
- 每层影响都按能力面经过源码或负向搜索锚定。
- 多层需求自动产出契约差异和契约对齐状态。
- 默认给人读 `report.md`、`plan.md`、`questions.md`，证据链放 `artifacts/`。

## 安装

### curl

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash
```

指定目标项目：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash -s /path/to/project
```

默认会同时安装到：

```text
.claude/skills/   # Claude Code
.agents/skills/   # Codex
```

安装后会在目标项目写入 `.prd-tools-version`，用于确认使用方当前安装版本。

只安装 Claude Code：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | INSTALL_CODEX=0 bash
```

只安装 Codex：

```bash
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | INSTALL_CLAUDE=0 bash
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

Claude Code：

```bash
TARGET="/path/to/your/project"
git clone --depth 1 https://github.com/zachary-lz-glm/prd-tools.git /tmp/prd-tools
mkdir -p "$TARGET/.claude/skills"
cp -r /tmp/prd-tools/plugins/build-reference/skills/build-reference "$TARGET/.claude/skills/"
cp -r /tmp/prd-tools/plugins/prd-distill/skills/prd-distill "$TARGET/.claude/skills/"
printf "version=%s\nsource=manual\nclaude=1\ncodex=0\n" "$(cat /tmp/prd-tools/VERSION)" > "$TARGET/.prd-tools-version"
```

Codex：

```bash
TARGET="/path/to/your/project"
git clone --depth 1 https://github.com/zachary-lz-glm/prd-tools.git /tmp/prd-tools
mkdir -p "$TARGET/.agents/skills"
cp -r /tmp/prd-tools/plugins/build-reference/skills/build-reference "$TARGET/.agents/skills/"
cp -r /tmp/prd-tools/plugins/prd-distill/skills/prd-distill "$TARGET/.agents/skills/"
printf "version=%s\nsource=manual\nclaude=0\ncodex=1\n" "$(cat /tmp/prd-tools/VERSION)" > "$TARGET/.prd-tools-version"
```

## 使用方式

### Claude Code

首次使用或项目结构变化后：

```text
/build-reference
```

拿到新 PRD 后：

```text
/prd-distill
```

### Codex

安装后从目标项目根目录重新打开 Codex 或新建会话。Codex 不使用 `/prd-distill` 这类 slash command，推荐用自然语言显式触发 skill。

首次使用或项目结构变化后：

```text
使用 build-reference skill，为当前项目构建 v3.1 reference：F 上下文收集 → A 全量构建 → B2 健康检查 → C 质量门控。
```

拿到新 PRD 后：

```text
使用 prd-distill skill，基于当前项目 _reference/ 和 PRD /path/to/prd.docx 生成 report.md、plan.md、questions.md 和 artifacts 证据链。
```

## 设计原则

- Reference 是持久项目知识，不是一次性提示词。
- 源码和技术文档是最终证据，reference 是快速通道。
- 层差异通过能力面适配器表达，不拆成三套工作流。
- 多层需求必须显式处理契约。
- 每次真实需求结束后，把矛盾和新增知识回流到 reference。

## 版本机制

- 仓库根目录 `VERSION` 是工具版本。
- Claude 插件元数据里的 `version` 与 `VERSION` 保持一致。
- 安装脚本会在目标项目写 `.prd-tools-version`，记录版本、安装时间、来源和安装目标。
- schema 使用 `schema_version`，工具使用 `tool_version`；老版本 `version: "3.0"` 可兼容读取。
