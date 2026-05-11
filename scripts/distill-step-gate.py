#!/usr/bin/env python3
"""Distill Step Gate — 前置条件检查脚本

在每个步骤开始前调用，检查前置产出是否存在。
退出码: 0 = 通过, 2 = 前置条件缺失, 1 = 参数错误
"""

import argparse
import os
import sys
import yaml


STEP_TABLE = {
    "0": {
        "label": "Step 0: PRD Ingestion",
        "prerequisites": [],
    },
    "1": {
        "label": "Step 1: Evidence Ledger",
        "prerequisites": [
            ("_ingest/document.md", "Step 0"),
        ],
    },
    "1.5-afprd": {
        "label": "Step 1.5: AI-friendly PRD",
        "prerequisites": [
            ("_ingest/document.md", "Step 0"),
            ("context/evidence.yaml", "Step 1"),
        ],
    },
    "1.5-quality": {
        "label": "Step 1.5: PRD Quality Report",
        "prerequisites": [
            ("spec/ai-friendly-prd.md", "Step 1.5"),
            ("context/evidence.yaml", "Step 1"),
        ],
    },
    "2": {
        "label": "Step 2: Requirement IR",
        "prerequisites": [
            ("spec/ai-friendly-prd.md", "Step 1.5"),
            ("context/prd-quality-report.yaml", "Step 1.5"),
        ],
    },
    "2.5": {
        "label": "Step 2.5: Query Plan",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
        ],
        "conditional_prerequisites": [
            # Only when reference index exists
            ("_prd-tools/reference/index/entities.json", "reference index",
             ["context/query-plan.yaml", "Step 2.5"]),
        ],
    },
    "3.1": {
        "label": "Step 3.1: Graph Context",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
        ],
        "conditional_prerequisites": [
            ("_prd-tools/reference/index/entities.json", "reference index",
             ["context/query-plan.yaml", "Step 2.5"]),
        ],
    },
    "3.2": {
        "label": "Step 3.2: Layer Impact",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
        ],
    },
    "4": {
        "label": "Step 4: Contract Delta",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/layer-impact.yaml", "Step 3.2"),
        ],
    },
    "5": {
        "label": "Step 5: Plan",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
            ("context/layer-impact.yaml", "Step 3.2"),
            ("context/contract-delta.yaml", "Step 4"),
        ],
    },
    "6": {
        "label": "Step 6: Readiness",
        "prerequisites": [
            ("plan.md", "Step 5"),
            ("context/contract-delta.yaml", "Step 4"),
        ],
    },
    "8": {
        "label": "Step 8: Report",
        "prerequisites": [
            ("context/requirement-ir.yaml", "Step 2"),
            ("context/graph-context.md", "Step 3.1"),
            ("context/layer-impact.yaml", "Step 3.2"),
            ("context/contract-delta.yaml", "Step 4"),
        ],
    },
    "8.5": {
        "label": "Step 8.5: Final Quality Gate",
        "prerequisites": [
            ("report.md", "Step 8"),
            ("plan.md", "Step 5"),
        ],
    },
    "8.6": {
        "label": "Step 8.6: Distill Completion Gate",
        "prerequisites": [
            ("context/final-quality-gate.yaml", "Step 8.5"),
        ],
    },
    "9": {
        "label": "Step 9: Portal HTML",
        "prerequisites": [
            ("context/final-quality-gate.yaml", "Step 8.5"),
        ],
    },
}


def file_exists_nonempty(base_dir, rel_path):
    """Check if a file exists and is non-empty."""
    full_path = os.path.join(base_dir, rel_path)
    if not os.path.isfile(full_path):
        return False, 0
    size = os.path.getsize(full_path)
    return size > 0, size


def check_workflow_state(distill_dir, requested_step):
    """Check workflow-state.yaml for step ordering violations."""
    state_path = os.path.join(distill_dir, "workflow-state.yaml")
    if not os.path.isfile(state_path):
        return None  # No state file — first run, OK

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    except Exception:
        return None  # Can't read — skip check

    completed = state.get("completed_steps", [])
    if isinstance(completed, list) and requested_step in completed:
        return f"Step {requested_step} already completed (in workflow-state.yaml). Re-running completed steps is allowed but unusual."

    return None


def run_gate(distill_dir, repo_root, step_id):
    """Run the step gate check. Returns (passed, message)."""
    if step_id not in STEP_TABLE:
        return False, f"Unknown step ID: {step_id}. Valid: {', '.join(sorted(STEP_TABLE.keys()))}"

    step_info = STEP_TABLE[step_id]
    label = step_info["label"]
    prerequisites = step_info["prerequisites"]
    conditional = step_info.get("conditional_prerequisites", [])

    print(f"=== Distill Step Gate: {label} ===")

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

    # Workflow state check
    state_msg = check_workflow_state(distill_dir, step_id)
    if state_msg:
        print(f"  [!] workflow-state.yaml: {state_msg}")

    if missing:
        missing_files = [m[0] for m in missing]
        missing_steps = [m[1] for m in missing]
        print(f"RESULT: FAIL — {len(missing)} prerequisite(s) missing.")
        print(f"  请先完成 {', '.join(missing_steps)}，生成缺失文件后再继续 {label}。")
        print(f"  缺失文件: {', '.join(missing_files)}")
        return False, "prerequisites missing"
    else:
        print(f"RESULT: PASS — all prerequisites satisfied. Proceed with {label}.")
        return True, "ok"


def main():
    parser = argparse.ArgumentParser(description="Distill Step Gate — check prerequisites before each step")
    parser.add_argument("--step", required=True, help="Step ID (e.g., 0, 1, 1.5-afprd, 2, 2.5, 3.1, 3.2, 4, 5, 6, 8, 8.5, 8.6, 9)")
    parser.add_argument("--distill-dir", required=True, help="Path to distill output directory")
    parser.add_argument("--repo-root", required=True, help="Path to project root directory")
    args = parser.parse_args()

    distill_dir = os.path.abspath(args.distill_dir)
    repo_root = os.path.abspath(args.repo_root)

    if not os.path.isdir(distill_dir):
        print(f"ERROR: distill-dir does not exist: {distill_dir}")
        sys.exit(1)

    passed, _ = run_gate(distill_dir, repo_root, args.step)
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
