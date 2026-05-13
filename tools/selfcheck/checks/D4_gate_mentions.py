"""D4: quality-gate.py mentions are consistent within each skill's own scope."""
import re
from pathlib import Path

META = {
    "id": "D4",
    "category": "docs",
    "description": "quality-gate.py mentions are consistent per-skill",
}

GATE_RE = re.compile(r"quality-gate\.py\s+(?:distill|final|reference)")

SKILL_GATE_SUBCOMMANDS = {
    "prd-distill": {"distill", "final"},
    "reference": {"reference"},
}


def _collect_subcommands(path):
    if not path.exists():
        return set()
    return {m.group(1) for m in re.finditer(r"quality-gate\.py\s+(distill|final|reference)", path.read_text(encoding="utf-8"))}


def check(repo_root):
    issues = []
    for skill in sorted(repo_root.glob("plugins/*/skills/*/SKILL.md")):
        skill_name = skill.parent.name
        allowed = SKILL_GATE_SUBCOMMANDS.get(skill_name, set())
        if not allowed:
            continue
        skill_dir = skill.parent
        plugin_dir = skill_dir.parent.parent
        workflow = skill_dir / "workflow.md"

        cmd_candidates = list(plugin_dir.glob("commands/*.md")) + \
            list((plugin_dir / ".claude" / "commands").glob("*.md")
                 if (plugin_dir / ".claude" / "commands").exists() else []) + \
            list((repo_root / ".claude" / "commands").glob("*.md")
                 if (repo_root / ".claude" / "commands").exists() else [])

        skill_cmds = _collect_subcommands(skill)
        workflow_cmds = _collect_subcommands(workflow)
        cmd_cmds = set()
        for c in cmd_candidates:
            cmd_cmds |= _collect_subcommands(c)

        cmd_cmds_filtered = cmd_cmds & allowed

        for sub in cmd_cmds_filtered - skill_cmds:
            issues.append(f"{skill.relative_to(repo_root)} missing mention of quality-gate.py {sub}")

    if issues:
        return {
            "status": "warn",
            "message": f"{len(issues)} within-skill gate gap(s)",
            "details": issues,
            "fix_hint": "add the missing quality-gate.py subcommand to the SAME skill's SKILL.md",
        }
    return {"status": "pass", "message": "quality-gate.py references consistent per-skill"}
