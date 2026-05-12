"""Shared fix_hint table for gate scripts. Each check emits a hint
pointing to the concrete step / file / line to edit, plus a direction
tag telling the AI whether to fix the artifact, the template, or both."""

FIX_HINTS = {
    # distill-workflow-gate
    "missing_evidence_yaml": {
        "hint": "Run Step 1. See workflow.md §步骤 1 / steps/step-01-parse.md",
        "direction": "fix_artifact",
    },
    "missing_contract_delta": {
        "hint": "Run Step 4. See workflow.md §步骤 4 / references/output-contracts.md §contract-delta",
        "direction": "fix_artifact",
    },
    "report_not_approved": {
        "hint": "Ask user to approve report.md; set context/report-confirmation.yaml.status=approved",
        "direction": "fix_artifact",
    },
    "plan_missing_section": {
        "hint": "Add section per workflow.md §plan template (10 sections). See steps/step-03-confirm.md plan checklist.",
        "direction": "fix_artifact",
    },
    "critique_fail": {
        "hint": "Re-run Two-Pass Critic or address critique findings. See references/critique-template.md",
        "direction": "fix_artifact",
    },
    # distill-quality-gate
    "ai_friendly_prd_h2_low": {
        "hint": "Section format mismatch. workflow template may use `## §N Name` but gate expects `## N. Name`. DO NOT rewrite the 13 sections — check template vs gate regex first. See scripts/distill-quality-gate.py AFPRD_SECTIONS.",
        "direction": "check_template",
    },
    # prd-coverage-gate
    "block_not_covered": {
        "hint": "Add real evidence for uncovered block to evidence-map.yaml. DO NOT invent blocks — if the count is suspicious (e.g. all blocks missing), likely cause is top-level key mismatch (evidence_map vs blocks), check scripts/prd-coverage-gate.py and workflow template.",
        "direction": "check_both",
    },
    # reference-step-gate
    "missing_coding_rules": {
        "hint": "Run reference Phase 2 Stage 2 first. See workflow.md §阶段 2 / steps/step-02-deep-analysis.md Stage 2.",
        "direction": "fix_artifact",
    },
}


def fix_hint(check_id: str) -> str:
    entry = FIX_HINTS.get(check_id, "")
    if isinstance(entry, dict):
        return entry.get("hint", "")
    return entry


def fix_direction(check_id: str) -> str:
    entry = FIX_HINTS.get(check_id, {})
    if isinstance(entry, dict):
        return entry.get("direction", "fix_artifact")
    return "fix_artifact"
