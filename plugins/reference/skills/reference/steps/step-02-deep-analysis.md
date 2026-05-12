<workflow_state>
  <workflow>reference</workflow>
  <current_step>2</current_step>
  <allowed_inputs>_prd-tools/build/modules-index.yaml, references/reference-v4.md, references/layer-adapters.md, templates/, references/output-contracts.md</allowed_inputs>
  <must_not_read_by_default>prd-distill schemas, _prd-tools/distill/</must_not_read_by_default>
  <must_not_produce>report.md, plan.md</must_not_produce>
</workflow_state>

## MUST NOT

- MUST NOT skip running step gate before starting this step
- MUST NOT produce files listed in `<must_not_produce>`
- MUST NOT read files listed in `<must_not_read_by_default>` unless explicitly needed
- MUST NOT proceed if step gate exits with code 2

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
- `references/output-contracts.md`（索引，按需加载 `schemas/` 下具体 schema）
- `templates/` 下的模板

## 执行

按以下顺序生成文件，后生成的文件必须检查先生成的文件，避免内容重叠：

### 阶段 1：代码库静态清单

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

4. 生成 `01-codebase.yaml`：目录结构、枚举、映射对象、模块（能力面+入口点）、注册点（只记录在哪里）、数据流（只记录通用结构流）、外部系统（只记录名称和文件位置）、核心结构体（只有字段名列表）。

> 你正在生成 01-codebase.yaml。记住：字段级契约留给 03-contracts，编码规则留给 02-coding-rules，场景打法留给 04-routing-playbooks，业务术语留给 05-domain。

### 阶段 2：编码规则

5. 从源码注释（`# WHY:`、`# NOTE:`、`# HACK:`）和历史 diff 提取编码规则和踩坑经验。
6. 生成 `02-coding-rules.yaml`：编码规范与约束（用 severity 区分 hard/soft）、高风险区域（danger_zones，必须有源码位置证据）、踩坑经验。
7. 检查 01-codebase 中的 registries，如果 registries 中包含了"怎么注册"的规则描述，将规则部分移到 02 的 rules 中。

> 你正在生成 02-coding-rules.yaml。记住：契约字段留给 03-contracts，场景驱动步骤留给 04-routing-playbooks。

### 阶段 3：契约

8. 通过源码 Read 追踪 import/调用关系，精确填充 producer/consumer 关系。
9. 生成 `03-contracts.yaml`：跨层和外部契约、字段级定义（type/required/compatibility）。
10. 检查 01-codebase 中的 structures.fields，如果包含 type/required 信息，删除并添加 `contract_ref` 指向 03 中的契约。
11. 检查 01-codebase 中的 external_systems，如果展开了 endpoint 列表，将 endpoint 详情移到 03，01 中只保留系统名和 contract_ref。
12. 每个契约必须有 `alignment_status`（aligned / misaligned / unchecked）。
13. 跨仓契约如果未确认，标注 `needs_confirmation`，不写 `confirmed`。

> 你正在生成 03-contracts.yaml。记住：编码规则留给 02-coding-rules，开发步骤留给 04-routing-playbooks，枚举值列表留给 01-codebase 的 enums。

### 阶段 4：路由与打法

14. 通过 `rg` / glob 在 PRD、技术方案中提取关键词，映射到代码模块。
15. 生成 `04-routing-playbooks.yaml`：PRD 路由信号（只到能力面级别）、字段映射（prd_field → code_field → contract_ref）、场景打法（步骤只在这里）。
16. 检查 02-coding-rules 中是否有场景驱动的开发步骤，如有，移到 04 的 playbook 中，02 中改为 `ref_rule` 引用。
17. routing 条目必须有 `playbook_ref` 指向对应的 playbook。
18. field_mappings 中不放字段 type/required，只用 `contract_ref` 引用 03。

#### 能力清单（capability_inventory）

19. 从 01-codebase 的源码扫描结果中提取能力清单：

    a. **generic 能力**：不按维度区分的功能模块、共享的 Schema/组件/服务、通用接口。标记 `scope: generic`。

    b. **dimensioned 能力**：从 switch-case/if-else 注册点、per-dimension 模板/组件/实现提取。`dimension` 根据项目实际架构命名（BFF 常见 campaign_type、前端常见 route/component、后端常见 service/model）。必须列出 `existing_entries`（已实现的维度值列表）。

    c. **coverage_matrix**：从 `03-contracts.yaml` 的接口 + 源码中的 if/switch 分支推断每个功能是 generic / per-dimension / hybrid。

    d. **missing_capabilities**：从源码中的 TODO、未实现的接口、构建过程中的盲点记录。

    e. 每个条目必须有 `evidence`（源码证据）和 `status`（verified / partial / needs_verification）。

> 你正在生成 04-routing-playbooks.yaml。记住：枚举值留给 01-codebase，字段级契约留给 03-contracts，编码规则留给 02-coding-rules。

### 阶段 5：业务领域

20. 从 PRD、技术方案、QA 记录中提取领域概念和隐式规则。
21. 生成 `05-domain.yaml`：业务域概览、术语（只收录非枚举概念）、隐式业务规则、历史决策。
22. 如果 05-domain 的术语与 01-codebase 中已有定义重复，删除 05 中的重复条目，改为引用指向 01-codebase。

> 你正在生成 05-domain.yaml。记住：代码路径留给 01-codebase，编码规则留给 02-coding-rules，契约字段留给 03-contracts，枚举值列表留给 01-codebase 的 enums。

### 阶段 6：导航

23. 生成 `00-portal.md`：项目画像摘要、按场景阅读指南、文件地图、健康状态。
24. 更新 `project-profile.yaml`（如需要）。
25. 运行脚本生成 `portal.html`：`python3 .prd-tools/scripts/render-reference-portal.py --root . --template .prd-tools/assets/reference-portal-template.html --out _prd-tools/reference/portal.html`（**AI 不得手写 portal.html**，必须通过脚本渲染生成）

## 去重检查（生成完成后必执行）

按以下规则检查所有已生成文件，发现重叠时合并到对应权威文件：

1. **字段级信息**：如果 01-codebase 或 04-routing-playbooks 中出现了字段 type/required 等契约信息，删除该内容并添加 `contract_ref: "CONTRACT-xxx"` 引用 03-contracts。
2. **编码规则**：如果 04-routing-playbooks 的步骤中包含了编码级规则（如"需要注册到 factory"），将规则移到 02-coding-rules，步骤中只写 `ref_rule: "RULE-xxx"`。
3. **实现步骤**：如果 01-codebase 的模块描述中包含了场景驱动的实现步骤，将步骤移到 04-routing-playbooks 的 playbook 中。
4. **术语解释**：如果 05-domain 的术语与 01-codebase 中已有定义重复，删除 05-domain 中的重复条目，改为引用指向 01-codebase。
5. **外部集成**：如果 01-codebase 的 external_systems 中展开了 endpoint 列表，将 endpoint 详情移到 03-contracts，01 中只保留系统名和 `contract_ref`。

## 事实生成硬约束

- 禁止使用 `120+`、`几十个`、`大量` 这类模糊统计；没有确定计数来源时写 `unknown`，并把补计数放入 `open_questions` 或 `next_actions`。
- 禁止臆造 owner、IM 群、频道、上下游系统职责、部署平台细节。当前仓无法证明的内容写成候选线索，并标记 `verification: needs_confirmation`。
- `confidence: high` 必须在同一条目或相邻上下文中出现 `evidence`、`verified_by`、`source` 或 `locator`。
- 对跨仓 API、前端消费方、后端 producer 的描述必须区分 `confirmed` / `inferred` / `needs_confirmation`。

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