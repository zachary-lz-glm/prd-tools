# 步骤 2：深度分析（索引）

本步骤拆分为 5 个子步骤，按顺序执行。每个子步骤文件自包含目标、输入、输出、执行指令和自检清单。

## 核心原则

**后生成的文件必须检查先生成的文件，避免内容重叠。**

## 执行顺序

| 序号 | 子步骤文件 | 输出文件 | 关键去重动作 |
|---|---|---|---|
| 1 | `step-02a-codebase.md` | `01-codebase.yaml` | 建立基础事实 |
| 2 | `step-02b-coding-rules.md` | `02-coding-rules.yaml` | 检查 01 的 registries，移入规则 |
| 3 | `step-02c-contracts.md` | `03-contracts.yaml` | 从 01 移入字段级信息和 endpoint 详情 |
| 4 | `step-02d-routing.md` | `04-routing-playbooks.yaml` | 从 02 移入场景驱动步骤 |
| 5 | `step-02e-domain-portal.md` | `05-domain.yaml` + `00-portal.md` | 检查术语与静态事实边界 |

每个子步骤末尾有 Self-Check 清单，生成后必须逐项验证通过再进入下一步。

## 共享去重检查规则

按以下规则检查所有已生成文件，发现重叠时合并到对应权威文件：

1. **字段级信息**：01-codebase 或 04-routing-playbooks 中出现字段 type/required 等契约信息 → 删除并添加 `contract_ref: "CONTRACT-xxx"` 引用 03-contracts。
2. **编码规则**：04-routing-playbooks 的步骤中包含编码级规则 → 将规则移到 02-coding-rules，步骤中只写 `ref_rule: "RULE-xxx"`。
3. **实现步骤**：01-codebase 的模块描述中包含场景驱动的实现步骤 → 将步骤移到 04-routing-playbooks 的 playbook 中。
4. **术语解释**：05-domain 只放业务术语和隐式规则；与静态事实重复时保留更合适的权威位置。
5. **外部集成**：01-codebase 的 external_systems 中展开了 endpoint 列表 → 将 endpoint 详情移到 03-contracts，01 中只保留系统名和 `contract_ref`。

## 确定性验证

记录以下事实前必须读取源码（不能从文件名或 import 推断）：

- enum 值、switch/registry 分支、导出的类型/方法、字段名
- endpoint 路径、request/response payload 字段、校验规则、下游集成 payload 映射

如果无法验证，写 `TODO`、`confidence: low`、`needs_domain_expert: true`。

## 输出质量

- 每个非显然条目都有 evidence。
- 跨层假设写入 `03-contracts.yaml`。
- 场景知识写入 `04-routing-playbooks.yaml`，不要散落在说明文字中。
- 代码写法写入 `02-coding-rules.yaml`，不要复制契约和 playbook。
- 层专属事实使用适配器中的 surface 名称。
- 每个文件都有 `boundary` 字段声明。
