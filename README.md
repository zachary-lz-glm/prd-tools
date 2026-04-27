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

### 方式一：Claude Code Marketplace（推荐）

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

### 方式二：命令行安装（所有 AI 工具通用）

```bash
# 将 <项目路径> 替换为实际路径
mkdir -p /tmp/skills <项目路径>/.claude/skills

git archive --remote=git@github.com:zachary-lz-glm/prd-tools.git HEAD:plugins | tar -x -C /tmp/skills

cp -r /tmp/skills/build-reference/skills/build-reference <项目路径>/.claude/skills/
cp -r /tmp/skills/prd-distill/skills/prd-distill <项目路径>/.claude/skills/

rm -rf /tmp/skills
```

安装后：
- **Claude Code**：`/build-reference`、`/prd-distill` 直接使用
- **Cursor / 其他**：将 SKILL.md 内容作为指令发给 AI

## 使用流程

```bash
# 第一步：构建领域知识（首次使用或项目结构变更后）
/build-reference

# 第二步：PRD 蒸馏（每次拿到新 PRD 时）
/prd-distill
```

## 更新

- **Marketplace**：`/plugin` → Marketplaces 标签 → 选择更新
- **手动安装**：重新执行安装命令即可

## 注意事项

- Marketplace 只需添加一次，重启后自动加载
- 遇到问题：`/plugin` → Errors 标签查看错误详情
- Skill 文件是纯 Markdown，不依赖 Node.js 或任何运行时
