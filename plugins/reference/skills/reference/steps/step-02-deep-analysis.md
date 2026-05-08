# 步骤 2：深度分析

## 目标

生成 reference v4.0：

```text
_prd-tools/reference/00-portal.md
_prd-tools/reference/project-profile.yaml
_prd-tools/reference/01-codebase.yaml
_prd-tools/reference/02-coding-rules.yaml
_prd-tools/reference/03-contracts.yaml
_prd-tools/reference/04-routing-playbooks.yaml
_prd-tools/reference/05-domain.yaml
```

## 输入

- `_prd-tools/build/modules-index.yaml`
- `_prd-tools/build/context-enrichment.yaml`，如存在
- `references/reference-v4.md`
- `references/layer-adapters.md`
- `references/output-contracts.md`
- `templates/` 下的模板

## 执行

按以下顺序生成文件，后生成的文件必须检查先生成的文件，避免内容重叠：

### 阶段 1：代码库静态清单

1. 使用 `rg` / glob 扫描项目目录结构。
2. 通过 Read 读取源码，提取模块、符号、入口、数据流。
3. 为分析过程中发现的事实建立 evidence 台账。
4. 生成 `01-codebase.yaml`：目录结构、枚举、模块（能力面+入口点）、注册点（只记录在哪里）、数据流（只记录通用结构流）、外部系统（只记录名称和文件位置）、核心结构体（只有字段名列表）。

### 阶段 2：编码规则

5. 从源码注释（`# WHY:`、`# NOTE:`、`# HACK:`）和历史 diff 提取编码规则和踩坑经验。
6. 生成 `02-coding-rules.yaml`：编码规范与约束（用 severity 区分软硬）、高风险区域（third_rails → danger_zones）、踩坑经验。
7. 检查 01-codebase 中的 registries，如果 registries 中包含了"怎么注册"的规则描述，将规则部分移到 02 的 rules 中。

### 阶段 3：契约

8. 通过源码 Read 追踪 import/调用关系，精确填充 producer/consumer 关系。
9. 生成 `03-contracts.yaml`：跨层和外部契约、字段级定义（type/required/compatibility）。
10. 检查 01-codebase 中的 structures.fields，如果包含 type/required 信息，删除并添加 `contract_ref` 指向 03 中的契约。
11. 检查 01-codebase 中的 external_systems，如果展开了 endpoint 列表，将 endpoint 详情移到 03，01 中只保留系统名和 contract_ref。

### 阶段 4：路由与打法

12. 通过 `rg` / glob 在 PRD、技术方案中提取关键词，映射到代码模块。
13. 生成 `04-routing-playbooks.yaml`：PRD 路由信号（只到能力面级别）、字段映射（prd_field → code_field → contract_ref）、场景打法（步骤只在这里）。
14. **生成 capability_inventory**（能力清单）：
    a. 从阶段 1 的源码扫描结果中提取通用能力：不按维度区分的功能模块、共享的 Schema/组件/服务、通用接口。标记 `scope: generic`。
    b. 从 switch-case/if-else 注册点、per-dimension 模板/组件/实现提取 dimensioned 能力。`dimension` 根据项目实际架构命名（BFF 常见 campaign_type、前端常见 route/component、后端常见 service/model）。必须列出 `existing_entries`（已实现的维度值列表）。
    c. 从 `03-contracts.yaml` 的接口 + 源码中的 if/switch 分支推断 `coverage_matrix`：每个功能是 generic/per-dimension/hybrid。
    d. 从源码中的 TODO、未实现的接口、构建过程中的盲点记录到 `missing_capabilities`。
    e. 每个条目必须有 `evidence`（源码证据）和 `status`（verified/partial/needs_verification）。
15. 检查 02-coding-rules 中是否有场景驱动的开发步骤，如有，移到 04 的 playbook 中。
16. routing 条目必须有 `playbook_ref` 指向对应的 playbook。
17. field_mappings 中不放字段 type/required，只用 `contract_ref` 引用 03。

### 阶段 5：业务领域

17. 从 PRD、技术方案、QA 记录中提取领域概念和隐式规则。
18. 生成 `05-domain.yaml`：业务域概览、术语（只收录非枚举概念）、隐式业务规则、历史决策。
19. 检查 01-codebase 中的枚举 label，如果 05-domain 的术语与枚举 label 重复，删除 05 中的重复条目，改为 `see_enum: "<EnumName>"`。

### 阶段 6：导航

20. 生成 `00-portal.md`：项目画像摘要、按场景阅读指南、文件地图、健康状态。
21. 更新 `project-profile.yaml`（如需要）。

## 去重检查（生成完成后必执行）

按以下规则检查所有已生成文件，发现重叠时合并到对应权威文件：

1. **字段级信息**：如果 01-codebase 或 04-routing-playbooks 中出现了字段 type/required 等契约信息，删除该内容并添加 `contract_ref: "CONTRACT-xxx"` 引用 03-contracts。
2. **编码规则**：如果 04-routing-playbooks 的步骤中包含了编码级规则（如"需要注册到 factory"），将规则移到 02-coding-rules，步骤中只写 `ref_rule: "RULE-xxx"`。
3. **实现步骤**：如果 01-codebase 的模块描述中包含了场景驱动的实现步骤，将步骤移到 04-routing-playbooks 的 playbook 中。
4. **术语解释**：如果 05-domain 的术语与 01-codebase 的枚举 label 完全重复，删除 05-domain 中的重复条目，改为 `see_enum: "<EnumName>"`。
5. **外部集成**：如果 01-codebase 的 external_systems 中展开了 endpoint 列表，将 endpoint 详情移到 03-contracts，01 中只保留系统名和 `contract_ref`。

## 确定性验证

记录以下事实前必须读取源码：

- enum 值
- switch/registry 分支
- 导出的类型/方法
- 字段名
- endpoint 路径
- request/response payload 字段
- 校验规则
- 下游集成 payload 映射

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## 输出质量

- 每个非显然条目都有 evidence。
- 跨层假设写入 `03-contracts.yaml`。
- 场景知识写入 `04-routing-playbooks.yaml`，不要散落在说明文字中。
- 代码写法写入 `02-coding-rules.yaml`，不要复制契约和 playbook。
- 层专属事实使用适配器中的 surface 名称。
- 每个文件都有 `boundary` 字段声明。
