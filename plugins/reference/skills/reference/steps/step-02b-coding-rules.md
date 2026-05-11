# 步骤 2b：编码规则

## 目标

生成 `_prd-tools/reference/02-coding-rules.yaml`：编码规范、约束、高风险区域和踩坑经验。

## 输入

- 项目源码（注释：`# WHY:`、`# NOTE:`、`# HACK:`）
- git diff 历史（提取隐含规则）
- `_prd-tools/reference/01-codebase.yaml`（已生成，检查 registries 中的规则描述）
- `templates/02-coding-rules.yaml`
- `references/schemas/00-directory-structure.md`（产出目录结构）

## 输出

- `_prd-tools/reference/02-coding-rules.yaml`

## 执行

1. 从源码注释（`# WHY:`、`# NOTE:`、`# HACK:`）提取编码规则和踩坑经验。
2. 从 git diff 历史提取隐含规则（返工模式、常见修复）。
3. 读取 `01-codebase.yaml`，检查 `registries` 条目——如果 registries 中包含了"怎么注册"的规则描述，将规则部分移到 02 的 `rules` 中。
4. 生成 `02-coding-rules.yaml`，包含：
   - `rules`：编码规范与约束，用 `severity` 区分 `hard`（必须遵守）和 `soft`（推荐）
   - `danger_zones`：高风险区域（原 third_rails），必须有明确的源码位置证据
   - `pitfalls`：踩坑经验

## 边界规则

**只放**：编码规则（severity 区分软硬）、高风险区域、踩坑经验。

**不放**：
- 契约字段（type/required）——那是 03-contracts 的事
- 场景驱动的实现步骤——那是 04-routing-playbooks 的事，本文件中的规则用 `ref_rule` 被引用

## 确定性验证

记录以下事实前必须读取源码：

- 校验规则
- 下游集成 payload 映射
- 注册点模式

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## Self-Check（生成后必须逐项验证）

- [ ] rules 中无字段级契约信息（type/required）
- [ ] rules 中无场景驱动的实现步骤（那是 04 的职责）
- [ ] severity 区分了 hard/soft
- [ ] danger_zones 有明确的源码位置证据
- [ ] 文件有 boundary 字段声明
