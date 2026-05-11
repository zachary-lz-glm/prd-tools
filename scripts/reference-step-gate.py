#!/usr/bin/env python3
"""Reference Step Gate — 前置条件检查脚本

在每个阶段/步骤开始前调用，检查前置产出是否存在。
退出码: 0 = 通过, 2 = 前置条件缺失, 1 = 参数错误
"""

import argparse
import os
import sys
import yaml


STEP_TABLE = {
    "0": {
        "label": "Phase 0: Context Enrichment",
        "prerequisites": [],
    },
    "1": {
        "label": "Phase 1: Structure Scan",
        "prerequisites": [],
    },
    "2a": {
        "label": "Phase 2 Stage 1: codebase",
        "prerequisites": [
            ("_prd-tools/reference/project-profile.yaml", "Phase 1"),
        ],
        "alt_prerequisites": [
            ("_prd-tools/build/modules-index.yaml", "Phase 1"),
        ],
        "alt_logic": "any",  # Either project-profile.yaml OR modules-index.yaml
    },
    "2b": {
        "label": "Phase 2 Stage 2: coding-rules",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
        ],
    },
    "2c": {
        "label": "Phase 2 Stage 3: contracts",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
            ("_prd-tools/reference/02-coding-rules.yaml", "Stage 2"),
        ],
    },
    "2d": {
        "label": "Phase 2 Stage 4: routing",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
            ("_prd-tools/reference/03-contracts.yaml", "Stage 3"),
        ],
    },
    "2e": {
        "label": "Phase 2 Stage 5: domain",
        "prerequisites": [
            ("_prd-tools/reference/04-routing-playbooks.yaml", "Stage 4"),
        ],
    },
    "3": {
        "label": "Phase 3: Portal HTML",
        "prerequisites": [
            ("_prd-tools/reference/05-domain.yaml", "Stage 5"),
            ("_prd-tools/reference/00-portal.md", "Stage 5"),
        ],
    },
    "3.5": {
        "label": "Phase 3.5: Evidence Index",
        "prerequisites": [
            ("_prd-tools/reference/01-codebase.yaml", "Stage 1"),
        ],
    },
    "3.6": {
        "label": "Phase 3.6: Completion Gate",
        "prerequisites": [
            ("_prd-tools/reference/index/manifest.yaml", "Phase 3.5"),
            ("_prd-tools/reference/portal.html", "Phase 3"),
        ],
    },
    "4": {
        "label": "Phase 4: Feedback Ingest",
        "prerequisites": [
            ("_prd-tools/reference/00-portal.md", "Stage 5"),
        ],
    },
}


def file_exists_nonempty(root_dir, rel_path):
    """Check if a file exists and is non-empty."""
    full_path = os.path.join(root_dir, rel_path)
    if not os.path.isfile(full_path):
        return False, 0
    size = os.path.getsize(full_path)
    return size > 0, size


def check_workflow_state(root_dir, requested_step):
    """Check reference-workflow-state.yaml for step ordering violations."""
    state_path = os.path.join(root_dir, "_prd-tools", "reference-workflow-state.yaml")
    if not os.path.isfile(state_path):
        return None

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    except Exception:
        return None

    completed = state.get("completed_steps", [])
    if isinstance(completed, list) and requested_step in completed:
        return f"Step {requested_step} already completed (in workflow-state). Re-running is allowed but unusual."

    return None


def run_gate(root_dir, step_id):
    """Run the step gate check. Returns (passed, message)."""
    if step_id not in STEP_TABLE:
        return False, f"Unknown step ID: {step_id}. Valid: {', '.join(sorted(STEP_TABLE.keys()))}"

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
            # Check if there are alt_prerequisites that satisfy this
            if alt_prerequisites and alt_logic == "any":
                alt_ok = False
                for alt_path, alt_step in alt_prerequisites:
                    alt_exists, alt_size = file_exists_nonempty(root_dir, alt_path)
                    if alt_exists:
                        print(f"  [+] {alt_path} ({alt_step}) — exists, {alt_size} bytes (alternative for {rel_path})")
                        alt_ok = True
                        break
                if alt_ok:
                    print(f"  [~] {rel_path} ({source_step}) — MISSING but alternative satisfied")
                    continue

            print(f"  [x] {rel_path} ({source_step}) — MISSING")
            missing.append((rel_path, source_step))

    # Workflow state check
    state_msg = check_workflow_state(root_dir, step_id)
    if state_msg:
        print(f"  [!] workflow-state: {state_msg}")

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
    parser = argparse.ArgumentParser(description="Reference Step Gate — check prerequisites before each phase/stage")
    parser.add_argument("--step", required=True, help="Step ID (e.g., 0, 1, 2a, 2b, 2c, 2d, 2e, 3, 3.5, 3.6, 4)")
    parser.add_argument("--root", required=True, help="Path to project root directory")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)

    if not os.path.isdir(root_dir):
        print(f"ERROR: root directory does not exist: {root_dir}")
        sys.exit(1)

    passed, _ = run_gate(root_dir, args.step)
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
