"""D3: SKILL.md 提到的 step 文件都真实存在"""
import re
from pathlib import Path

META = {
    "id": "D3",
    "category": "docs",
    "description": "SKILL.md step file references resolve to real files",
}


def _skills(repo_root):
    return sorted(repo_root.glob("plugins/*/skills/*/SKILL.md"))


def check(repo_root):
    missing = []
    for skill in _skills(repo_root):
        skill_dir = skill.parent
        src = skill.read_text(encoding="utf-8")
        # steps/step-XX-yyy.md
        for m in re.finditer(r"steps/(step-[\w.-]+\.md)", src):
            target = skill_dir / "steps" / m.group(1)
            if not target.exists():
                missing.append(
                    f"{skill.relative_to(repo_root)} references "
                    f"steps/{m.group(1)} (does not exist)"
                )
    if missing:
        return {
            "status": "fail",
            "message": f"{len(missing)} broken step reference(s)",
            "details": missing,
            "fix_hint": "either create the step file or update the SKILL.md reference",
        }
    return {"status": "pass", "message": "all step references resolve"}
