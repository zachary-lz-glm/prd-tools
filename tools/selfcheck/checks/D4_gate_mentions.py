"""D4: SKILL.md / workflow.md / commands/*.md 声明的 gate 脚本列表一致"""
import re
from pathlib import Path

META = {
    "id": "D4",
    "category": "docs",
    "description": "gate script mentions are consistent across SKILL / workflow / command",
}

GATE_RE = re.compile(r"[\w\-]+-(?:step|workflow|quality|coverage)-gate\.py")


def _collect(path):
    if not path.exists():
        return set()
    return set(GATE_RE.findall(path.read_text(encoding="utf-8")))


def check(repo_root):
    issues = []
    for skill in sorted(repo_root.glob("plugins/*/skills/*/SKILL.md")):
        skill_dir = skill.parent
        plugin_dir = skill_dir.parent.parent
        workflow = skill_dir / "workflow.md"
        # commands can live in plugin root commands/ or .claude/commands/
        cmd_candidates = list(plugin_dir.glob("commands/*.md")) + list(
            (plugin_dir / ".claude" / "commands").glob("*.md")
            if (plugin_dir / ".claude" / "commands").exists() else []
        )
        # also check root-level .claude/commands
        cmd_candidates += list((repo_root / ".claude" / "commands").glob("*.md")) if (repo_root / ".claude" / "commands").exists() else []

        skill_set = _collect(skill)
        workflow_set = _collect(workflow)
        cmd_set = set()
        for c in cmd_candidates:
            cmd_set |= _collect(c)

        # commands are authoritative; SKILL+workflow should mention every command-mentioned gate
        missing_in_skill = cmd_set - skill_set
        missing_in_workflow = cmd_set - workflow_set
        for g in missing_in_skill:
            issues.append(f"{skill.relative_to(repo_root)} missing mention of {g}")
        for g in missing_in_workflow:
            issues.append(f"{workflow.relative_to(repo_root)} missing mention of {g}")

    if issues:
        return {
            "status": "warn",
            "message": f"{len(issues)} gate reference gap(s)",
            "details": issues,
            "fix_hint": "add the missing gate script to SKILL.md Final Completion Gate / workflow.md Phase list",
        }
    return {"status": "pass", "message": "gate references consistent"}
