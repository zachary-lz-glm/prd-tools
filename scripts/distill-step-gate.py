#!/usr/bin/env python3
"""Distill Step Gate — 前置条件检查脚本

在每个步骤开始前调用，检查前置产出是否存在。
退出码: 0 = 通过, 2 = 前置条件缺失, 1 = 参数错误

新增 --write-state: 通过/失败时写入 workflow-state.yaml v2
新增 stage 概念: spec / report / plan（三段式工作流）
"""

import argparse
import os
import sys
from pathlib import Path

import yaml


def _default_tool_version():
    try:
        version_file = Path(__file__).resolve().parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    return "unknown"

# Import shared workflow state module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workflow_state import WorkflowState


# Stage mapping: each step belongs to a stage
STEP_STAGES = {
    "0": "spec",
    "1": "spec",
    "1.5-afprd": "spec",
    "1.5-quality": "spec",
    "2": "spec",
    "2.5": "report",
    "3.1": "report",
    "3.2": "report",
    "4": "report",
    "8": "report",
    "8.1-confirm": "report",
    "5": "plan",
    "6": "plan",
    "8.5": "plan",
    "8.6": "plan",
    "9": "plan",
}

STEP_TABLE = {
    # ── spec 阶段 ──
    "0": {
        "label": "Step 0: PRD Ingestion",
        "stage": "spec",
        "prerequisites": [],
        "output": [
            "_ingest/document.md",
            "_ingest/source-manifest.yaml",
            "_ingest/document-structure.json",
            "_ingest/evidence-map.yaml",
            "_ingest/extraction-quality.yaml",
        ],
        "forbidden_outputs": ["report.md", "plan.md"],
    },
    "1": {
        "label": "Step 1: Evidence Ledger",
        "stage": "spec",
        "prerequisites": [
            ("_ingest/document.md", "Step 0"),
            ("_ingest/document-structure.json", "Step 0"),
            ("_ingest/evidence-map.yaml", "Step 0"),
            ("_ingest/source-manifest.yaml", "Step 0"),
        ],
        "output": ["context/evidence.yaml"],
        "forbidden_outputs": ["report.md", "plan.md"],
    },
    "1.5-afprd": {
        "label": "Step 1.5: AI-friendly PRD",
        "stage": "spec",
        "prerequisites": [
            ("_ingest/document.md", "Step 0"),
            ("context/evidence.yaml", "Step 1"),
        ],
        "output": ["spec/ai-friendly-prd.md"],
        "forbidden_outputs": ["report.md", "plan.md"],
    },
    "1.5-quality": {
        "label": "Step 1.5: PRD Quality Report",
        "stage": "spec",
        "prerequisites": [
            ("spec/ai-friendly-prd.md", "Step 1.5"),
            ("context/evidence.yaml", "Step 1"),
        ],
        "output": ["context/prd-quality-report.yaml"],
        "forbidden_outputs": ["report.md", "plan.md"],
    },
    "2": {
        "label": "Step 2: Requirement IR",
        "stage": "spec",
        "prerequisites": [
            ("spec/ai-friendly-prd.md", "Step 1.5"),
            ("context/prd-quality-report.yaml", "Step 1.5"),
            ("_ingest/document.md", "Step 0"),
            ("_ingest/document-structure.json", "Step 0"),
            ("_ingest/evidence-map.yaml", "Step 0"),
        ],
        "output": ["context/requirement-ir.yaml"],
        "forbidden_outputs": ["report.md", "plan.md"],
    },
    # ── report 阶段 ──
    "2.5": {
        "label": "Step 2.5: Query Plan",
        "stage": "report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
        ],
        "output": ["context/query-plan.yaml"],
        "forbidden_outputs": ["plan.md"],
    },
    "3.5": {
        "label": "Step 3.5: Context Pack",
        "stage": "report",
        "prerequisites": [
            ("context/layer-impact.yaml", "Step 3.2"),
            ("context/query-plan.yaml", "Step 2.5"),
        ],
        "output": ["context/context-pack.md"],
        "forbidden_outputs": ["plan.md"],
    },
    "3.1": {
        "label": "Step 3.1: Graph Context",
        "stage": "report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
        ],
        "conditional_prerequisites": [
            ("_prd-tools/reference/index/entities.json", "reference index",
             ["context/query-plan.yaml", "Step 2.5"]),
        ],
        "output": ["context/graph-context.md"],
        "forbidden_outputs": ["plan.md"],
    },
    "3.2": {
        "label": "Step 3.2: Layer Impact",
        "stage": "report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
        ],
        "output": ["context/layer-impact.yaml"],
        "forbidden_outputs": ["plan.md"],
    },
    "3.6": {
        "label": "Step 3.6: Critique Pass",
        "stage": "report",
        "prerequisites": [],
        "output": [],
    },
    "4": {
        "label": "Step 4: Contract Delta",
        "stage": "report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/layer-impact.yaml", "Step 3.2"),
        ],
        "output": ["context/contract-delta.yaml"],
        "forbidden_outputs": ["plan.md"],
    },
    "8": {
        "label": "Step 8: Report",
        "stage": "report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
            ("context/layer-impact.yaml", "Step 3.2"),
            ("context/contract-delta.yaml", "Step 4"),
        ],
        "output": ["report.md"],
        "forbidden_outputs": ["plan.md"],
    },
    "8.1-confirm": {
        "label": "Step 8.1: Report Review Gate",
        "stage": "report",
        "prerequisites": [
            ("report.md", "Step 8"),
        ],
        "output": ["context/report-confirmation.yaml"],
    },
    # ── plan 阶段 ──
    "5": {
        "label": "Step 5: Plan",
        "stage": "plan",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
            ("context/layer-impact.yaml", "Step 3.2"),
            ("context/contract-delta.yaml", "Step 4"),
            ("report.md", "Step 8"),
            ("context/report-confirmation.yaml", "Step 8.1"),
        ],
        "output": ["plan.md"],
    },
    "6": {
        "label": "Step 6: Readiness",
        "stage": "plan",
        "prerequisites": [
            ("plan.md", "Step 5"),
            ("context/contract-delta.yaml", "Step 4"),
        ],
        "output": ["context/readiness-report.yaml"],
    },
    "7": {
        "label": "Step 7: Reference Feedback",
        "stage": "plan",
        "prerequisites": [
            ("plan.md", "Step 5"),
        ],
        "output": ["context/reference-update-suggestions.yaml"],
    },
    "8.5": {
        "label": "Step 8.5: Final Quality Gate",
        "stage": "plan",
        "prerequisites": [
            ("report.md", "Step 8"),
            ("plan.md", "Step 5"),
        ],
        "output": ["context/final-quality-gate.yaml"],
    },
    "8.6": {
        "label": "Step 8.6: Reference Update Staging",
        "stage": "plan",
        "prerequisites": [
            ("context/final-quality-gate.yaml", "Step 8.5"),
            ("context/reference-update-suggestions.yaml", "Step 7"),
        ],
        "output": ["context/completion-report.yaml"],
    },
    "8.6.1": {
        "label": "Step 8.6.1: Gate Checklist",
        "stage": "plan",
        "prerequisites": [
            ("context/final-quality-gate.yaml", "Step 8.5"),
        ],
        "output": [],
    },
    "9": {
        "label": "Step 9: Portal HTML",
        "stage": "plan",
        "prerequisites": [
            ("context/final-quality-gate.yaml", "Step 8.5"),
        ],
        "output": ["portal.html"],
    },
}

# Ordered step sequence for resume pointer
# Key fix: report(8) and report_confirmation(8.1) BEFORE plan(5)
DISTILL_STEP_ORDER = [
    "0", "1", "1.5-afprd", "1.5-quality", "2",       # spec
    "2.5", "3.1", "3.2", "3.5", "4", "8", "8.1-confirm",    # report
    "5", "6", "8.5", "8.6", "9",                       # plan
]


def file_exists_nonempty(base_dir, rel_path):
    """Check if a file exists and is non-empty."""
    full_path = os.path.join(base_dir, rel_path)
    if not os.path.isfile(full_path):
        return False, 0
    size = os.path.getsize(full_path)
    return size > 0, size


def report_confirmation_approved(distill_dir):
    """Check report-confirmation.yaml explicitly approves plan generation."""
    path = os.path.join(distill_dir, "context", "report-confirmation.yaml")
    if not os.path.isfile(path):
        return False, "context/report-confirmation.yaml is missing"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        return False, f"context/report-confirmation.yaml is unreadable: {exc}"

    status = data.get("status")
    if not status:
        return False, "context/report-confirmation.yaml has no status field"
    if status != "approved":
        return False, f"context/report-confirmation.yaml status is {status!r}, expected 'approved'"

    return True, "approved"


def _get_next_step(current_step: str) -> str:
    """Return the next step ID after current_step, or 'completed'."""
    try:
        idx = DISTILL_STEP_ORDER.index(current_step)
        if idx + 1 < len(DISTILL_STEP_ORDER):
            return DISTILL_STEP_ORDER[idx + 1]
        return "completed"
    except ValueError:
        return current_step


STEP_ALIASES = {
    "8.1": "8.1-confirm",
    "8.6.1": "8.6",
}


def _resolve_step(step_id):
    return STEP_ALIASES.get(step_id, step_id)


def run_gate(distill_dir, repo_root, step_id):
    """Run the step gate check. Returns (passed, message, missing_files)."""
    if step_id not in STEP_TABLE:
        return False, f"Unknown step ID: {step_id}. Valid: {', '.join(sorted(STEP_TABLE.keys()))}", []

    step_info = STEP_TABLE[step_id]
    label = step_info["label"]
    prerequisites = step_info["prerequisites"]
    conditional = step_info.get("conditional_prerequisites", [])

    print(f"=== Distill Step Gate: {label} ===")

    # Forbidden outputs check (context budget enforcement)
    forbidden = step_info.get("forbidden_outputs", [])
    for fpath in forbidden:
        if os.path.isfile(os.path.join(distill_dir, fpath)):
            print(f"  [!] WARNING: {fpath} exists but is forbidden at this stage (stale from previous run?)")

    missing = []
    for rel_path, source_step in prerequisites:
        exists, size = file_exists_nonempty(distill_dir, rel_path)
        if exists:
            print(f"  [+] {rel_path} ({source_step}) — exists, {size} bytes")
        else:
            print(f"  [x] {rel_path} ({source_step}) — MISSING")
            missing.append((rel_path, source_step))

    # Conditional prerequisites: only checked if trigger file exists
    for trigger_path, trigger_label, req_info in conditional:
        req_path, req_step = req_info[0], req_info[1]
        trigger_full = os.path.join(repo_root, trigger_path)
        if os.path.isfile(trigger_full):
            exists, size = file_exists_nonempty(distill_dir, req_path)
            if exists:
                print(f"  [+] {req_path} ({req_step}) — exists, {size} bytes (conditional: {trigger_label} present)")
            else:
                print(f"  [x] {req_path} ({req_step}) — MISSING (conditional: {trigger_label} present)")
                missing.append((req_path, req_step))
        else:
            print(f"  [~] {req_path} ({req_step}) — SKIPPED ({trigger_label} not present)")

    # Human confirmation check before plan generation.
    # This is the core of the three-stage workflow: plan requires approved report.
    if step_id == "5":
        approved, approval_msg = report_confirmation_approved(distill_dir)
        if approved:
            print("  [+] context/report-confirmation.yaml — approved")
        else:
            print(f"  [x] Report Review Gate — {approval_msg}")
            missing.append(("context/report-confirmation.yaml: status approved", "Step 8.1"))

    missing_files = [m[0] for m in missing]

    if missing:
        missing_steps = [m[1] for m in missing]
        print(f"RESULT: FAIL — {len(missing)} prerequisite(s) missing.")
        print(f"  请先完成 {', '.join(missing_steps)}，生成缺失文件后再继续 {label}。")
        print(f"  缺失文件: {', '.join(missing_files)}")
        return False, "prerequisites missing", missing_files
    else:
        print(f"RESULT: PASS — all prerequisites satisfied. Proceed with {label}.")
        return True, "ok", []


def main():
    parser = argparse.ArgumentParser(description="Distill Step Gate — check prerequisites before each step")
    parser.add_argument("--step", required=True, help="Step ID (e.g., 0, 1, 1.5-afprd, 2, 2.5, 3.1, 3.2, 4, 8, 8.1-confirm, 5, 6, 8.5, 8.6, 9)")
    parser.add_argument("--distill-dir", required=True, help="Path to distill output directory")
    parser.add_argument("--repo-root", "--repo", dest="repo_root", required=True, help="Path to project root directory")
    parser.add_argument("--write-state", action="store_true",
                        help="Write/update workflow-state.yaml on pass or fail")
    parser.add_argument("--allow-rerun", action="store_true",
                        help="Skip ordering check (allow running a step out of sequence)")
    parser.add_argument("--tool-version", default=_default_tool_version(),
                        help="Tool version for workflow state file")
    args = parser.parse_args()

    distill_dir = os.path.abspath(args.distill_dir)
    repo_root = os.path.abspath(args.repo_root)

    # Resolve step aliases (e.g. "8.1" -> "8.1-confirm")
    args.step = _resolve_step(args.step)

    if not os.path.isdir(distill_dir):
        print(f"ERROR: distill-dir does not exist: {distill_dir}")
        sys.exit(1)

    # Ordering check: verify requested step matches state.resume.next_step
    state_path = os.path.join(distill_dir, "workflow-state.yaml")
    if os.path.isfile(state_path) and not args.allow_rerun:
        state_check = WorkflowState(state_path, "prd-distill", args.tool_version)
        expected = state_check.get_resume().get("next_step")
        if expected and expected != "completed" and args.step != expected:
            if state_check.is_step_completed(args.step):
                print(f"  [!] WARNING: Step {args.step} already completed — unusual rerun")
            else:
                print(f"  [x] ORDERING ERROR: expected step {expected!r}, got {args.step!r}")
                print(f"      Use --allow-rerun to override ordering check.")
                sys.exit(2)

    passed, message, missing_files = run_gate(distill_dir, repo_root, args.step)

    # Write workflow state if requested
    if args.write_state:
        state = WorkflowState(state_path, "prd-distill", args.tool_version)

        step_info = STEP_TABLE[args.step]
        label = step_info["label"]
        output_files = step_info.get("output", [])

        if passed:
            state.mark_step_passed(args.step, label, output_files, distill_dir)
            state.set_stage(STEP_STAGES.get(args.step, "unknown"))
            next_step = _get_next_step(args.step)
            next_label = STEP_TABLE.get(next_step, {}).get("label", "completed")
            state.set_resume(next_step, next_label)
            if next_step == "completed":
                state.mark_workflow_completed()
            # Write human checkpoint for report review
            if args.step == "8.1-confirm":
                rc_path = os.path.join(distill_dir, "context", "report-confirmation.yaml")
                rc_status = "pending"
                if os.path.isfile(rc_path):
                    try:
                        with open(rc_path, encoding='utf-8') as f:
                            rc = yaml.safe_load(f) or {}
                        rc_status = "approved" if rc.get("status") == "approved" else "pending"
                    except Exception:
                        rc_status = "pending"
                state.set_human_checkpoint("report_review", rc_status)
        else:
            state.mark_step_blocked(args.step, label, missing_files)
            state.set_resume(args.step, f"Retry {label} after completing prerequisites")

        state.save()
        print(f"  [state] Written to {state_path}")

    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()