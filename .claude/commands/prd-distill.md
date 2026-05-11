# /prd-distill

You are running the PRD Tools `prd-distill` workflow. This command is a thin compatibility wrapper for clients or model gateways that do not reliably auto-trigger Claude Code skills.

Before analyzing the PRD, you MUST read and follow:

1. `.claude/skills/prd-distill/SKILL.md`
2. `.claude/skills/prd-distill/workflow.md`

Hard gates:

- Generate `spec/ai-friendly-prd.md` before `context/requirement-ir.yaml`.
- `context/requirement-ir.yaml` must contain `ai_prd_req_id`.
- Ready MODIFY/DELETE work must be connected to layer-impact code anchors or an explicit fallback reason.
- If `_prd-tools/reference/index/` exists, run `.prd-tools/scripts/context-pack.py`.
- Generate `context/final-quality-gate.yaml`.
- Render `portal.html` with `.prd-tools/scripts/render-distill-portal.py`.
- Run `.prd-tools/scripts/distill-quality-gate.py --distill-dir _prd-tools/distill/<slug> --repo-root .`.
- Do not handwrite `portal.html`.
- Do not claim `/prd-distill` is complete if the quality gate exits with code 2.

Now continue with the user's `/prd-distill` request.
