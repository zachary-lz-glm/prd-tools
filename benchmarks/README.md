# PRD Tools Benchmark

评估 `reference` 和 `prd-distill` 插件产出质量的离线评分系统。

## 两种评分体系

| | Snapshot Score | Oracle Quality Score |
|---|---|---|
| **回答什么问题** | 输出"像不像"上次？ | 输出"对不对"？ |
| **数据来源** | 上一版输出（baseline） | 人工标注标准答案（oracle.yaml） |
| **评分依据** | 文本关键词命中回归 | 需求点召回 + 代码锚点命中 + 阻塞项质量 - 错误结论惩罚 |
| **用途** | 回归检测、防退化 | **真正的质量分** |
| **命令** | `score` / `compare` | `oracle` |

> **重要**: oracle_score 才是质量分，snapshot_score 只是回归相似度。新增 case 优先写 oracle.yaml。

## 快速开始

```bash
# Oracle 质量评分（推荐）
scripts/benchmark.sh oracle gasstation-dxgy /path/to/distill/xxx

# Snapshot 回归评分
scripts/benchmark.sh score gasstation-dxgy /path/to/distill/xxx

# 列出所有 case
scripts/benchmark.sh list

# 校验 expected 文件格式
scripts/benchmark.sh lint

# 保存 baseline
scripts/benchmark.sh save-baseline gasstation-dxgy <version> /path/to/distill/xxx

# 与 baseline 对比
scripts/benchmark.sh compare gasstation-dxgy <version> /path/to/distill/xxx
```

## Oracle 评分

### 评分维度（总分 100）

| 维度 | 满分 | 说明 |
|------|------|------|
| requirement_recall | 35 | 核心需求是否出现在正确的交付物中 |
| code_anchor_accuracy | 30 | 关键代码锚点是否在 graph-context/plan 中被引用 |
| blocker_quality | 20 | 已知阻塞项是否被正确识别和报告 |
| plan_actionability | 15 | plan 是否包含 checklist、文件路径、验证命令 |
| false_positive_penalty | -10 | 禁止出现的错误结论，命中每条 -3 分 |

### 权重

| 优先级 | 权重 |
|--------|------|
| P0 | 2.0 |
| P1 | 1.0 |
| P2 | 0.5 |

### 等级

| 分数 | 等级 |
|------|------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| 0-59 | F |

### 通过规则

- `quality_score >= 60` **且** 无 P0 requirement missed → `passed: true`
- P0 requirement missed → 硬性 `passed: false`
- forbidden_claims 命中 → 每条 -3 分（最多 -10）

### oracle.yaml 格式

```yaml
schema_version: "1.0"
case_id: my-case

requirements:
  - id: REQ-XXX
    priority: P0
    meaning: "需求含义简述"
    acceptable_terms:        # 任一交付物包含这些词即算命中
      - 关键词1
      - 关键词2
    must_flag_conflict: true # 可选：要求报告标记矛盾
    conflict_signals:
      - 矛盾
    must_appear_in:          # 必须出现在哪些交付物中
      - requirement-ir
      - report
      - plan

code_anchors:
  - id: CODE-XXX
    priority: P0
    meaning: "锚点含义"
    path: src/path/to/file.ts
    symbol: SymbolName
    must_appear_in:
      - graph-context
      - plan

blockers:
  - id: BLOCK-XXX
    priority: P0
    meaning: "阻塞项含义"
    acceptable_terms:
      - 关键词1
    must_appear_in:
      - report

forbidden_claims:
  - id: FALSE-XXX
    meaning: "不能出现的错误结论"
    forbidden_terms:
      - 错误结论关键词
```

### must_appear_in 目标映射

| 名称 | 对应文件 |
|------|----------|
| report | `report.md` |
| plan | `plan.md`（团队模式：`team-plan.md` 或 `plans/plan-{repo}.md`） |
| ai-friendly-prd | `spec/ai-friendly-prd.md` |
| requirement-ir | `context/requirement-ir.yaml` |
| graph-context | `context/graph-context.md` |
| layer-impact | `context/layer-impact.yaml` |
| contract-delta | `context/contract-delta.yaml` |
| readiness-report | `context/readiness-report.yaml` |
| prd-quality-report | `context/prd-quality-report.yaml` |
| final-quality-gate | `context/final-quality-gate.yaml` |
| report-confirmation | `context/report-confirmation.yaml` |

## Snapshot 评分

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| output_contract | 20% | 必需文件和报告章节是否完整 |
| requirement_recall | 25% | 关键需求是否被识别（加权 P0×2 / P1×1） |
| code_anchor_recall | 25% | 关键代码锚点是否命中（path 60% + symbol 40%） |
| blocker_recall | 20% | 已知问题是否被检出 |
| plan_actionability | 10% | 开发计划是否包含 checklist、文件路径、验证命令 |

## 新增 Case

1. 在 `benchmarks/cases/` 下新建目录，放入：
   - `case.yaml` — case 配置
   - `oracle.yaml` — **人工标准答案（优先）**
   - `expected/` — 文本命中期望（snapshot 用）

2. `expected/` 下四个文件：
   - `requirements.yaml` — 关键需求点
   - `code-anchors.yaml` — 关键代码锚点
   - `blockers.yaml` — 必须识别的问题
   - `output-contract.yaml` — 必需文件和报告章节

3. 运行 `scripts/benchmark.sh lint` 验证格式。

## 回归判定（Snapshot）

| 条件 | 动作 |
|------|------|
| total_score 下降 >= 5 分 | 需要检查 |
| requirement_recall 下降 | 阻塞合并 |
| code_anchor_recall 下降 | 阻塞合并 |
| blocker_recall 下降 | 阻塞合并 |
| plan_actionability 下降 >= 10 分 | 需人工确认 |

## 典型工作流

```bash
# 1. 开发新版本后，跑 oracle 质量评分
scripts/benchmark.sh oracle gasstation-dxgy ./test-output

# 2. 也跑 snapshot 回归评分
scripts/benchmark.sh score gasstation-dxgy ./test-output

# 3. 满意后保存 baseline
scripts/benchmark.sh save-baseline gasstation-dxgy 2.20.0 ./test-output

# 4. 下次改动后对比
scripts/benchmark.sh compare gasstation-dxgy 2.20.0 ./new-output
scripts/benchmark.sh oracle gasstation-dxgy ./new-output
```
