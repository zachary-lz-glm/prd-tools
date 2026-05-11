# 步骤 2a：代码库静态清单

## 目标

生成 `_prd-tools/reference/01-codebase.yaml`：代码库中已存在的事实清单。

## 输入

- `_prd-tools/build/modules-index.yaml`
- `_prd-tools/build/context-enrichment.yaml`（如存在）
- 项目源码
- `templates/01-codebase.yaml`
- `references/reference-v4.md`（文件边界规则）
- `references/layer-adapters.md`（当前层能力面定义）
- `references/schemas/00-directory-structure.md`（产出目录结构）
- `references/schemas/03-context.md`（evidence schema）

## 输出

- `_prd-tools/reference/01-codebase.yaml`

## 执行

1. 使用 `rg` / glob 扫描项目目录结构。
2. 通过 Read 读取源码，提取模块、符号、入口、数据流。
3. 为分析过程中发现的事实建立 evidence 台账。每条 evidence 格式：

   ```yaml
   evidence:
     - id: "EV-001"
       kind: "code | prd | tech_doc | git_diff | negative_code_search | human | api_doc"
       source: ""
       locator: ""
       summary: ""
   confidence: "high | medium | low"
   ```

4. 生成 `01-codebase.yaml`，包含以下 section：
   - `directory_tree`：目录结构（树形文本）
   - `enums`：枚举值（从源码读取，不从文件名推断）
   - `modules`：模块（能力面 + 入口点）
   - `registries`：注册点（只记录"在哪里注册"，不记录"怎么写"）
   - `data_flows`：数据流（只记录通用结构流）
   - `external_systems`：外部系统（只记录名称和文件位置）
   - `structures`：核心结构体（只有字段名列表）

## 边界规则

**只放**：静态事实（目录、枚举、模块、注册点、数据流、外部系统名称、结构体字段名列表）。

**不放**：
- 字段级契约（type/required/compatibility）——那是 03-contracts 的事，用 `contract_ref` 引用
- 编码规则（"怎么注册"、"踩坑经验"）——那是 02-coding-rules 的事
- 场景驱动的实现步骤——那是 04-routing-playbooks 的事
- 业务术语解释——那是 05-domain 的事

## 确定性验证

记录以下事实前必须读取源码（不能从文件名或 import 推断）：

- enum 值
- switch/registry 分支
- 导出的类型/方法
- 字段名
- endpoint 路径

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## Self-Check（生成后必须逐项验证）

- [ ] 所有 evidence ID 格式为 EV-xxx 且有 source 和 locator
- [ ] enum 值来自源码读取，不是从文件名推断
- [ ] structures.fields 只有字段名列表，无 type/required
- [ ] external_systems 只有名称和文件位置，无 endpoint 详情
- [ ] 文件有 boundary 字段声明
