# 步骤 2d：路由与打法

## 目标

生成 `_prd-tools/reference/04-routing-playbooks.yaml`：PRD 路由信号、字段映射、场景打法、能力清单。

## 输入

- PRD / 技术方案文档（关键词提取）
- `_prd-tools/reference/01-codebase.yaml`（已生成）
- `_prd-tools/reference/02-coding-rules.yaml`（已生成，检查场景驱动步骤）
- `_prd-tools/reference/03-contracts.yaml`（已生成，字段引用）
- `templates/04-routing-playbooks.yaml`
- `references/schemas/02-capability-inventory.md`（capability_inventory schema）

## 输出

- `_prd-tools/reference/04-routing-playbooks.yaml`
- 更新 `02-coding-rules.yaml`：如果编码规则中混入了场景驱动步骤，移到 04 的 playbook 中

## 执行

### Part 1：路由信号与字段映射

1. 通过 `rg` / glob 在 PRD、技术方案中提取关键词，映射到代码模块。
2. 生成路由信号（只到能力面级别）和字段映射（`prd_field -> code_field -> contract_ref`）。
3. routing 条目必须有 `playbook_ref` 指向对应的 playbook。
4. field_mappings 中不放字段 type/required，只用 `contract_ref` 引用 03。

### Part 2：场景打法（Playbook）

5. 生成 playbook：场景驱动的实现步骤只在这里。
6. 检查 `02-coding-rules.yaml`，如果其中有场景驱动的开发步骤，移到 04 的 playbook 中，02 中改为 `ref_rule` 引用。

### Part 3：能力清单（capability_inventory）

7. 从 01-codebase 的源码扫描结果中提取能力清单，分 5 步：

   a. **generic 能力**：不按维度区分的功能模块、共享的 Schema/组件/服务、通用接口。标记 `scope: generic`。

   b. **dimensioned 能力**：从 switch-case/if-else 注册点、per-dimension 模板/组件/实现提取。`dimension` 根据项目实际架构命名（BFF 常见 campaign_type、前端常见 route/component、后端常见 service/model）。必须列出 `existing_entries`（已实现的维度值列表）。

   c. **coverage_matrix**：从 `03-contracts.yaml` 的接口 + 源码中的 if/switch 分支推断每个功能是 generic / per-dimension / hybrid。

   d. **missing_capabilities**：从源码中的 TODO、未实现的接口、构建过程中的盲点记录。

   e. **证据要求**：每个条目必须有 `evidence`（源码证据）和 `status`（verified / partial / needs_verification）。

## 边界规则

**只放**：信号到能力面映射 + playbook + capability_inventory + QA 矩阵 + golden samples。

**不放**：
- 枚举值——那是 01-codebase 的事
- 字段级契约（type/required）——那是 03-contracts 的事，用 `contract_ref` 引用
- 编码规则——那是 02-coding-rules 的事，步骤中用 `ref_rule` 引用

## Self-Check（生成后必须逐项验证）

- [ ] routing 条目都有 playbook_ref 指向本文件中的 playbook
- [ ] field_mappings 中无 type/required 字段，只有 contract_ref
- [ ] capability_inventory 的 generic_capabilities 都有 scope: generic
- [ ] dimensioned_capabilities 都列出了 existing_entries
- [ ] 每个 capability_inventory 条目有 evidence 和 status
- [ ] 02-coding-rules 中的场景驱动步骤已移到 playbook
- [ ] 文件有 boundary 字段声明
