"""X1: workflow.md 声明的 step id 能在 step-gate 的 STEP_TABLE 里找到"""
import re
from pathlib import Path

META = {
    "id": "X1",
    "category": "cross",
    "description": "step ids in workflow.md exist in step-gate STEP_TABLE",
}

# 对应关系：workflow 所在 skill 目录 -> gate 脚本
SKILL_TO_GATE = {
    "prd-distill": "distill-step-gate.py",
    "reference": "reference-step-gate.py",
}

STEP_HEADING = re.compile(r"^## 步骤\s+([\d.]+(?:-[\w-]+)?)[:：]", re.MULTILINE)
STEP_TABLE_KEY = re.compile(r'^\s*"([\d.]+(?:-[\w-]+)?)"\s*:\s*{', re.MULTILINE)


def check(repo_root):
    issues = []
    for skill_name, gate_name in SKILL_TO_GATE.items():
        workflow = (
            repo_root / "plugins" / skill_name / "skills" / skill_name / "workflow.md"
        )
        gate = repo_root / "scripts" / gate_name
        if not workflow.exists() or not gate.exists():
            continue
        workflow_steps = set(STEP_HEADING.findall(workflow.read_text(encoding="utf-8")))
        gate_steps = set(STEP_TABLE_KEY.findall(gate.read_text(encoding="utf-8")))

        missing_in_gate = workflow_steps - gate_steps
        # exclude pure sub-labels like "1.5" if gate registers "1.5-afprd" etc.
        # allow workflow step X if any gate key starts with "X-" or "X."
        real_missing = set()
        for s in missing_in_gate:
            if any(g.startswith(s + "-") or g.startswith(s + ".") for g in gate_steps):
                continue
            real_missing.add(s)
        if real_missing:
            for s in real_missing:
                issues.append(
                    f"{workflow.relative_to(repo_root)} declares step '{s}' "
                    f"but {gate_name} STEP_TABLE has no matching key"
                )
    if issues:
        return {
            "status": "fail",
            "message": f"{len(issues)} phantom step(s)",
            "details": issues,
            "fix_hint": "either implement the step in gate STEP_TABLE or remove from workflow.md",
        }
    return {"status": "pass", "message": "workflow step ids match gate table"}
