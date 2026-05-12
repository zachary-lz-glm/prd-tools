#!/usr/bin/env python3
"""Reference Step Gate — 前置条件检查脚本

在每个步骤开始前调用，检查前置产出是否存在。
退出码: 0 = 通过, 2 = 前置条件缺失, 1 = 参数错误

新增 --write-state: 通过/失败时写入 workflow-state.yaml v2
"""

import argparse
import os
import sys

import yaml

# Import shared workflow state module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workflow_state import WorkflowState


STEP_TABLE = {
    "0": {
        "label": "Phase 0: Context Enrichment",
        "prerequisites": [],
        "output": ["_prd-tools/build/context-enrichment.yaml"],
    },
    "1": {
        "label": "Phase 1: Structure Scan",
        "prerequisites": [],
        "output": [
            "_prd-tools/build/modules-index.yaml",
            "_prd-tools/reference/project-profile.yaml",
        ],
    },
    "2a": {
        "label": "Phase 2 Stage 1: codebase",
        "prerequisites": [
            ("_prd-tools/reference/project-profile.yaml", "Phase 1"),
        ],
        "alt_prerequisites": [
            ("_prd-tools/build/modules-index.yaml", "Phase 1"),
        ],
        "alt_logic": "any",
        "output": ["_prd-tools/reference/01-codebase.yaml"],
    },
    "2b": {
        "label": "Phase 2 Stage 2: coding-rules",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
        ],
        "output": ["_prd-tools/reference/02-coding-rules.yaml"],
    },
    "2c": {
        "label": "Phase 2 Stage 3: contracts",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
            ("_prd-tools/reference/02-coding-rules.yaml", "Stage 2"),
        ],
        "output": ["_prd-tools/reference/03-contracts.yaml"],
    },
    "2d": {
        "label": "Phase 2 Stage 4: routing",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
            ("_prd-tools/reference/03-contracts.yaml", "Stage 3"),
        ],
        "output": ["_prd-tools/reference/04-routing-playbooks.yaml"],
    },
    "2e": {
        "label": "Phase 2 Stage 5: domain",
        "prerequisites": [
            ("_prd-tools/reference/04-routing-playbooks.yaml", "Stage 4"),
        ],
        "output": [
            "_prd-tools/reference/05-domain.yaml",
            "_prd-tools/reference/00-portal.md",
        ],
    },
    "3": {
        "label": "Phase 3: Portal HTML",
        "prerequisites": [
            ("_prd-tools/reference/05-domain.yaml", "Stage 5"),
            ("_prd-tools/reference/00-portal.md", "Stage 5"),
        ],
        "output": ["_prd-tools/reference/portal.html"],
    },
    "3.5": {
        "label": "Phase 3.5: Evidence Index",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
        ],
        "output": [
            "_prd-tools/reference/index/entities.json",
            "_prd-tools/reference/index/edges.json",
            "_prd-tools/reference/index/inverted-index.json",
            "_prd-tools/reference/index/manifest.yaml",
        ],
    },
    "3.6": {
        "label": "Phase 3.6: Completion Gate",
        "prerequisites": [
            ("_prd-tools/reference/index/manifest.yaml", "Phase 3.5"),
            ("_prd-tools/reference/portal.html", "Phase 3"),
        ],
        "output": [],
    },
    "4": {
        "label": "Phase 4: Feedback Ingest",
        "prerequisites": [
            ("_prd-tools/reference/00-portal.md", "Stage 5"),
        ],
        "output": ["_prd-tools/build/feedback-report.yaml"],
    },
}

# Ordered step sequence for resume pointer
REFERENCE_STEP_ORDER = ["0", "1", "2a", "2b", "2c", "2d", "2e", "3", "3.5", "3.6", "4"]


def file_exists_nonempty(root_dir, rel_path):
    """Check if a file exists and is non-empty."""
    full_path = os.path.join(root_dir, rel_path)
    if not os.path.isfile(full_path):
        return False, 0
    size = os.path.getsize(full_path)
    return size > 0, size


def _get_next_step(current_step: str) -> str:
    """Return the next step ID after current_step, or 'completed'."""
    try:
        idx = REFERENCE_STEP_ORDER.index(current_step)
        if idx + 1 < len(REFERENCE_STEP_ORDER):
            return REFERENCE_STEP_ORDER[idx + 1]
        return "completed"
    except ValueError:
        return current_step


def run_gate(root_dir, step_id):
    """Run the step gate check. Returns (passed, message, missing_files)."""
    if step_id not in STEP_TABLE:
        return (
            False,
            f"Unknown step ID: {step_id}. Valid: {', '.join(sorted(STEP_TABLE.keys()))}",
            [],
        )

    step_info = STEP_TABLE[step_id]
    label = step_info["label"]
    prerequisites = step_info["prerequisites"]
    alt_prerequisites = step_info.get("alt_prerequisites", [])
    alt_logic = step_info.get("alt_logic", "all")

    print(f"=== Reference Step Gate: {label} ===")

    missing = []
    for rel_path, source_step in prerequisites:
        exists, size = file_exists_nonempty(root_dir, rel_path)
        if exists:
            print(f"  [+] {rel_path} ({source_step}) — exists, {size} bytes")
        else:
            print(f"  [x] {rel_path} ({source_step}) — MISSING")
            missing.append((rel_path, source_step))

    # Alternative prerequisites (e.g., "any" = at least one must exist)
    if alt_prerequisites and alt_logic == "any":
        alt_ok = False
        for rel_path, source_step in alt_prerequisites:
            exists, size = file_exists_nonempty(root_dir, rel_path)
            if exists:
                print(f"  [+] {rel_path} ({source_step}) — exists (alt), {size} bytes")
                alt_ok = True
                break
            else:
                print(f"  [~] {rel_path} ({source_step}) — missing (alt)")
        if not alt_ok and missing:
            # All primary AND all alt missing → add alt to missing list
            for rel_path, source_step in alt_prerequisites:
                missing.append((rel_path, f"{source_step} (alt)"))

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


STEPS_REQUIRING_MODE_SELECTION = {"1", "2a", "2b", "2c", "2d", "2e", "3", "3.5", "3.6", "4"}


def main():
    parser = argparse.ArgumentParser(
        description="Reference Step Gate — check prerequisites before each step"
    )
    parser.add_argument(
        "--step",
        help="Step ID (0, 1, 2a, 2b, 2c, 2d, 2e, 3, 3.5, 3.6, 4)",
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Path to project root directory",
    )
    parser.add_argument(
        "--write-state",
        action="store_true",
        help="Write/update workflow-state.yaml on pass or fail",
    )
    parser.add_argument(
        "--allow-rerun",
        action="store_true",
        help="Skip ordering check (allow running a step out of sequence)",
    )
    parser.add_argument(
        "--confirm-mode",
        help="Record mode selection (F_then_A, F_only, A_only, B, B2, C, E). Does not run step gate.",
    )
    parser.add_argument(
        "--tool-version",
        default="2.17.0",
        help="Tool version for workflow state file",
    )
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)

    if not os.path.isdir(root_dir):
        print(f"ERROR: root directory does not exist: {root_dir}")
        sys.exit(1)

    state_path = os.path.join(root_dir, "_prd-tools", "build", "reference-workflow-state.yaml")

    # --confirm-mode: just write mode selection checkpoint and exit
    if args.confirm_mode:
        valid_modes = {"F_then_A", "F_only", "A_only", "B", "B2", "C", "E"}
        if args.confirm_mode not in valid_modes:
            print(f"ERROR: invalid mode {args.confirm_mode!r}. Valid: {', '.join(sorted(valid_modes))}")
            sys.exit(1)
        state = WorkflowState(state_path, "reference", args.tool_version)
        state.set_human_checkpoint("mode_selection", "approved", {"selected_mode": args.confirm_mode})
        state.save()
        print(f"  [+] Mode selection confirmed: {args.confirm_mode}")
        print(f"  [state] Written to {state_path}")
        sys.exit(0)

    if not args.step:
        print("ERROR: --step is required (unless using --confirm-mode)")
        sys.exit(1)

    # Ordering check
    if os.path.isfile(state_path) and not args.allow_rerun:
        state_check = WorkflowState(state_path, "reference", args.tool_version)
        expected = state_check.get_resume().get("next_step")
        if expected and expected != "completed" and args.step != expected:
            if state_check.is_step_completed(args.step):
                print(f"  [!] WARNING: Step {args.step} already completed — unusual rerun")
            else:
                print(f"  [x] ORDERING ERROR: expected step {expected!r}, got {args.step!r}")
                print(f"      Use --allow-rerun to override ordering check.")
                sys.exit(2)

    # Mode Selection Gate: steps >= 1 require mode_selection approved
    if args.step in STEPS_REQUIRING_MODE_SELECTION:
        if os.path.isfile(state_path):
            state_check = WorkflowState(state_path, "reference", args.tool_version)
            checkpoint = state_check.get_human_checkpoint("mode_selection")
            if not checkpoint or checkpoint.get("status") != "approved":
                print(f"  [x] MODE SELECTION REQUIRED: run --confirm-mode <mode> before Phase 1+")
                print(f"      用户必须先选择 reference 构建模式。")
                sys.exit(2)
            else:
                print(f"  [+] Mode selection: {checkpoint.get('selected_mode', '?')} (approved)")
        else:
            print(f"  [x] MODE SELECTION REQUIRED: no workflow state found. Run --confirm-mode <mode> first.")
            sys.exit(2)

    passed, message, missing_files = run_gate(root_dir, args.step)

    # Write workflow state if requested
    if args.write_state:
        state = WorkflowState(state_path, "reference", args.tool_version)

        step_info = STEP_TABLE[args.step]
        label = step_info["label"]
        output_files = step_info.get("output", [])

        if passed:
            if state.is_step_completed(args.step):
                print(f"  [!] WARNING: Step {args.step} ({label}) already completed — unusual rerun")

            state.mark_step_passed(args.step, label, output_files, root_dir)
            next_step = _get_next_step(args.step)
            next_label = STEP_TABLE.get(next_step, {}).get("label", "completed")
            state.set_resume(next_step, next_label)
        else:
            state.mark_step_blocked(args.step, label, missing_files)
            state.set_resume(args.step, f"Retry {label} after completing prerequisites")

        state.save()
        print(f"  [state] Written to {state_path}")

    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()