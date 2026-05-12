# Team Common Reference 设计文档

> 状态：脚手架（schema 字段 + 约定已落地，聚合/继承逻辑待后续迭代）

## 背景

领导规划通过 reference 构建 B 端营销全团队公共知识库，包含前端（genos / dive-editor）、BFF（dive-bff / dive-template-bff）、后端（magellan）多仓共享的知识。

## 目录结构约定

```text
dive-team-reference/
├── .prd-tools-team-version       # "2.19.0"
├── reference/
│   ├── 00-portal.md              # 团队级导航
│   ├── project-profile.yaml      # layer: "team-common"
│   ├── 01-codebase.yaml          # 跨仓代码地图
│   ├── 02-coding-rules.yaml      # 全团队共享的 fatal 规则
│   ├── 03-contracts.yaml         # 3 仓已 checked_by 的跨仓契约（SSOT）
│   ├── 04-routing-playbooks.yaml # 跨 3 仓的 playbook
│   └── 05-domain.yaml            # 全团队术语、业务决策
└── build/
    └── aggregation-report.yaml   # 聚合报告
```

## 成员仓配置

每个仓的 `_prd-tools/reference/project-profile.yaml` 新增：

```yaml
team_reference:
  upstream_repo: "git@git.xxx:dive-team-reference.git"
  upstream_local_path: "../dive-team-reference"
  inherit_scopes:
    - domain_terms
    - contracts_cross_repo
    - coding_rules_fatal
  last_synced: "2026-05-12T22:00:00+08:00"
```

## 聚合接口设计（待实现）

1. 读成员仓 03-contracts/05-domain/04-routing-playbooks 的 `team_reference_candidate: true` 条目
2. 跨仓合并同一 contract_id → 写团队仓
3. 冲突检测：同 ID 不同内容时标记为 `conflict`

## 继承接口设计（待实现）

1. 读团队仓 reference/ → 镜像到本仓（标 `source: team-common, read_only: true`）
2. 本仓已有的不覆盖
3. prd-distill 消费团队 reference 时，权威性高于本仓推断

## 范围

- 本轮（v2.18.1）：schema 字段 + 约定 + 设计文档
- v2.19+：实现聚合/继承脚本
