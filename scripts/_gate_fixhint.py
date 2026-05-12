"""Shared fix_hint table for gate scripts. Each check emits a hint
pointing to the concrete step / file / line to edit."""

FIX_HINTS = {
    # distill-workflow-gate
    "missing_evidence_yaml": "Run Step 1. See workflow.md §步骤 1 / steps/step-01-parse.md",
    "missing_contract_delta": "Run Step 4. See workflow.md §步骤 4 / references/output-contracts.md §contract-delta",
    "report_not_approved": "Ask user to approve report.md; set context/report-confirmation.yaml.status=approved",
    "plan_missing_section": "Add section per workflow.md §plan template (10 sections). See steps/step-03-confirm.md plan checklist.",
    "critique_fail": "Re-run Two-Pass Critic or address critique findings. See references/critique-template.md",
    # distill-quality-gate
    "ai_friendly_prd_h2_low": "Add missing H2 sections to spec/ai-friendly-prd.md. Target: 13 sections (see references/contracts/ai-friendly-prd.contract.yaml).",
    # prd-coverage-gate
    "block_not_covered": "Add evidence for uncovered block to context/evidence-map.yaml. See workflow.md §Evidence Ledger.",
    # reference-step-gate
    "missing_coding_rules": "Run reference Phase 2 Stage 2 first. See workflow.md §阶段 2 / steps/step-02-deep-analysis.md Stage 2.",
}


def fix_hint(check_id: str) -> str:
    return FIX_HINTS.get(check_id, "")
