# 步骤 2c：契约

## 目标

生成 `_prd-tools/reference/03-contracts.yaml`：跨层和外部契约的字段级定义（唯一权威来源）。

## 输入

- 项目源码（import/call 关系）
- `_prd-tools/reference/01-codebase.yaml`（已生成，提取字段级信息）
- `templates/03-contracts.yaml`
- `references/schemas/00-directory-structure.md`（产出目录结构）

## 输出

- `_prd-tools/reference/03-contracts.yaml`
- 更新 `01-codebase.yaml`：删除移入本文件的信息，添加 `contract_ref` 引用

## 执行

1. 通过源码 Read 追踪 import/调用关系，精确填充 producer/consumer 关系。
2. 生成 `03-contracts.yaml`：跨层和外部契约、字段级定义（type/required/compatibility）。
3. 读取 `01-codebase.yaml`，执行以下迁移：
   - 如果 `structures.fields` 包含 type/required 信息，从 01 中删除并添加 `contract_ref` 指向 03 中的契约。
   - 如果 `external_systems` 展开了 endpoint 列表，将 endpoint 详情移到 03，01 中只保留系统名和 `contract_ref`。
4. 每个契约必须有 `alignment_status`（aligned / misaligned / unchecked）。
5. 跨仓契约如果未确认，标注 `needs_confirmation`，不写 `confirmed`。

## 边界规则

**只放**：跨层和外部契约的字段级定义（producer/consumer、endpoint/schema/event、type/required/compatibility）。

**不放**：
- 编码规则——那是 02-coding-rules 的事
- 开发步骤——那是 04-routing-playbooks 的事
- 枚举值列表——那是 01-codebase 的 enums 的事

## 确定性验证

记录以下事实前必须读取源码：

- endpoint 路径
- request/response payload 字段
- 字段 type 和 required 状态
- 导入/调用链

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## Self-Check（生成后必须逐项验证）

- [ ] 01-codebase 中所有 contract_ref 指向本文件中存在的契约 ID
- [ ] 每个契约都有 producer 和 consumers
- [ ] request_fields/response_fields 有 type 和 required
- [ ] alignment_status 每个契约都填写了
- [ ] 跨仓契约的 verification 不是 confirmed 的标注了 needs_confirmation
- [ ] 文件有 boundary 字段声明
