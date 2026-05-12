"""D4: gate script mentions are consistent within each skill's own scope.
Only checks that a skill's SKILL.md / workflow.md mention gates whose
prefix matches that skill (e.g. prd-distill only needs distill-*-gate.py)."""
import re
from pathlib import Path

META = {
    "id": "D4",
    "category": "docs",
    "description": "gate script mentions are consistent per-skill",
}

GATE_RE = re.compile(r"[\w\-]+-(?:step|workflow|quality|coverage)-gate\.py")

SKILL_GATE_PREFIX = {
    "prd-distill": ("distill-",),
    "reference": ("reference-",),
}


def _collect(path):
    if not path.exists():
        return set()
    return set(GATE_RE.findall(path.read_text(encoding="utf-8")))


def check(repo_root):
    issues = []
    for skill in sorted(repo_root.glob("plugins/*/skills/*/SKILL.md")):
        skill_name = skill.parent.name  # e.g. "prd-distill"
        allowed_prefixes = SKILL_GATE_PREFIX.get(skill_name, ())
        skill_dir = skill.parent
        plugin_dir = skill_dir.parent.parent
        workflow = skill_dir / "workflow.md"

        cmd_candidates = list(plugin_dir.glob("commands/*.md")) + \
            list((plugin_dir / ".claude" / "commands").glob("*.md")
                 if (plugin_dir / ".claude" / "commands").exists() else []) + \
            list((repo_root / ".claude" / "commands").glob("*.md")
                 if (repo_root / ".claude" / "commands").exists() else [])

        skill_set = _collect(skill)
        workflow_set = _collect(workflow)
        cmd_set = set()
        for c in cmd_candidates:
            cmd_set |= _collect(c)

        # Only consider gates whose prefix matches this skill
        cmd_set_filtered = {g for g in cmd_set
                            if any(g.startswith(p) for p in allowed_prefixes)}

        for g in cmd_set_filtered - skill_set:
            issues.append(f"{skill.relative_to(repo_root)} missing mention of {g}")
        for g in cmd_set_filtered - workflow_set:
            issues.append(f"{workflow.relative_to(repo_root)} missing mention of {g}")

    if issues:
        return {
            "status": "warn",
            "message": f"{len(issues)} within-skill gate gap(s)",
            "details": issues,
            "fix_hint": "add the missing gate script to the SAME skill's SKILL.md / workflow.md",
        }
    return {"status": "pass", "message": "gate references consistent per-skill"}
