# PRD Tools — Claude Code Skills

两个 Claude Code Skill，用于项目级领域知识构建和 PRD 蒸馏。

## Skills

### /build-reference — 领域知识构建

自动扫描项目代码库，生成 7 个 YAML 领域知识文件（reference），供 PRD 蒸馏使用。

- **Phase 1**：结构扫描 → 模块地图（modules-index.yaml）
- **Phase 2**：深度分析 → 7 个 YAML reference 文件
- **Phase 3**：质量门控 → 路径验证 + TODO 校准

### /prd-distill — PRD 蒸馏

读取领域知识 + 原始 PRD 文档，生成结构化的蒸馏报告（Markdown + YAML）。

- **Step 1**：解析 PRD + reference 路由匹配 + 代码锚定验证
- **Step 2**：分类 + 结构化输出
- **Step 3**：确认 + 最终报告

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
