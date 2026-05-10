# Bundle Attribution Notes: AI_dive_simba_shift

## 概述

分支 `AI_dive_simba_shift` (frontend 层) 对应 **3 个 PRD**：

- `simba-shift-signin-award`: DIVE-Simba新增班次签到奖-L1.docx
- `simba-shift-rider-type`: DIVE-simba新增shift骑手类型-L1.docx
- `simba-shift-order-scope`: DIVE-Simba支持区分班次内外订单-L1.docx

## 归因原则

1. Diff **不能天然归属于某一个 PRD**，因为三个 PRD 共用同一分支。
2. 每个 changed file 通过信号词匹配做初步归因：
   - **独占匹配**（high）：文件路径只命中一个 PRD 的信号词
   - **共享候选**（shared_candidate）：文件路径同时命中多个 PRD 的信号词
   - **共享信号**（shared）：只命中 shift/simba 等通用信号
   - **待审核**（needs_review）：无明确信号匹配，需人工判断
3. 低置信度归因已标记 `needs_review`，**不要强行归因**。

## 归因统计

| 置信度 | 文件数 |
|--------|--------|
| high | 0 |
| medium | 0 |
| shared | 0 |
| shared_candidate | 0 |
| needs_review | 7 |

## 待审核文件（needs_review）

- `app/dive/src/components/FormField/DxgyFormList/ConditionMethodCmp.tsx` (+62/-8)
- `app/dive/src/components/FormField/DxgyFormList/EditableConditionMethodRow.tsx` (+35/-22)
- `app/dive/src/components/FormField/DxgyFormList/index.tsx` (+2/-2)
- `app/dive/src/components/FormField/RewardConditionCmp/index.tsx` (+35/-19)
- `app/dive/src/components/FormField/TipsTag/index.tsx` (+29/-6)
- `app/dive/src/locales/i18n-info.js` (+2/-2)
- `app/dive/src/setupProxy.js` (+1/-1)
