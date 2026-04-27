# PRD Tools — Claude Code Skills

两个 Claude Code Skill，用于项目级领域知识构建和 PRD 蒸馏。

## Skills

### /build-reference — 领域知识构建

自动扫描项目代码库，生成 8 个领域知识文件（7 YAML + 1 MD），供 PRD 蒸馏使用。

**工作流（4 阶段）：**

| 阶段 | 名称 | 说明 |
|------|------|------|
| Phase 0 | 上下文富化 | Git 历史深挖 + 历史 PRD↔Diff 对照分析（可选但推荐） |
| Phase 1 | 结构扫描 | 目录扫描 → 模块地图（modules-index.yaml） |
| Phase 2 | 深度分析 | 按关注点维度产出 8 个 reference 文件 |
| Phase 3 | 质量门控 | 路径验证 + 深度 Lint + TODO 校准 |

**模式选择：**

| 选项 | 说明 |
|------|------|
| A. 全量构建 | 首次使用，从零构建完整 reference |
| B. 增量更新 | 根据代码变更增量更新 |
| B2. 健康检查 | 检查 reference 是否过期（含深度 Lint） |
| C. 质量检查 | 对已有 reference 做质量门控验证 |
| E. 反馈回流 | 从蒸馏结果中提取矛盾，回流更新 reference |
| F. 上下文收集 | 从历史需求素材中自动提取项目知识 |

**生成的 reference 文件：**

```
_reference/
├── 00-index.md              # 导航索引 + 实体索引
├── 01-entities.yaml         # 实体：枚举、核心类型、数据结构
├── 02-architecture.yaml     # 结构：目录结构、注册机制、数据流、第三轨
├── 03-conventions.yaml      # 规范：命名、代码模式、踩坑历史
├── 04-constraints.yaml      # 约束：白名单、校验规则、致命错误
├── 05-mapping.yaml          # 映射：PRD 路由表、字段映射、开发指南
├── 06-glossary.yaml         # 术语：业务术语表、同义词
└── 07-business-context.yaml # 业务：业务域概览、决策记录、隐式规则
```

### /prd-distill — PRD 蒸馏

读取领域知识 + 原始 PRD 文档，生成结构化的蒸馏报告（Markdown + YAML）。

- **Step 1**：解析 PRD + reference 路由匹配 + 代码锚定验证
- **Step 2**：变更分类（ADD/MODIFY/DELETE）+ 源码验证 + 风险标记
- **Step 3**：变更分类确认 + 置信度检查 + 人工确认 → 最终蒸馏报告

支持前端、BFF、后端三层通用。

## 安装

### 方式一：curl 一键安装（推荐）

无需 git，一行命令安装到任意项目：

```bash
# 安装到当前项目
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash

# 或指定目标项目路径
curl -fsSL https://raw.githubusercontent.com/zachary-lz-glm/prd-tools/main/install.sh | bash -s /path/to/project
```

安装后文件位于 `<项目>/.claude/skills/build-reference/` 和 `<项目>/.claude/skills/prd-distill/`。

### 方式二：Claude Code Plugin Marketplace

适合团队协作，安装后所有成员自动获得 Skill。

```bash
cd /your-project && claude
```

1. 输入 `/plugin` → 选择 Add Marketplace → 输入：
   ```
   git@github.com:zachary-lz-glm/prd-tools.git
   ```
2. 切换到 Discover 标签 → 找到 `build-reference` 和 `prd-distill` → Space 启用
3. 安装时选择 **Install for all collaborators on this repository** (project scope)
4. 重启 Claude Code → 输入 `/build-reference` 验证

### 方式三：手动 git clone

```bash
TARGET="/path/to/your/project"

git clone --depth 1 https://github.com/zachary-lz-glm/prd-tools.git /tmp/prd-tools

cp -r /tmp/prd-tools/plugins/build-reference/skills/build-reference "$TARGET/.claude/skills/"
cp -r /tmp/prd-tools/plugins/prd-distill/skills/prd-distill "$TARGET/.claude/skills/"

rm -rf /tmp/prd-tools
```

### 非 Claude Code 环境

Skill 文件是纯 Markdown（`.md`），不依赖任何运行时。安装后：

- **Claude Code**：`/build-reference`、`/prd-distill` 直接使用
- **Cursor / Windsurf / 其他**：将 `.claude/skills/<skill>/SKILL.md` 的内容作为指令发给 AI

## 使用流程

```bash
# 第一步：构建领域知识（首次使用或项目结构变更后）
/build-reference

# 第二步：PRD 蒸馏（每次拿到新 PRD 时）
/prd-distill
```

## 更新

- **curl 安装**：重新执行安装命令即可覆盖
- **Marketplace**：`/plugin` → Marketplaces 标签 → 选择更新
- **手动安装**：重新执行 clone + cp

## 注意事项

- Marketplace 只需添加一次，重启后自动加载
- 遇到问题：`/plugin` → Errors 标签查看错误详情
- Skill 文件是纯 Markdown，不依赖 Node.js 或任何运行时
