"""D2: workflow.md 代码块不含智能引号"""
import re
from pathlib import Path

META = {
    "id": "D2",
    "category": "docs",
    "description": "yaml code blocks in workflow.md have no smart quotes",
}

SMART_QUOTES = "“”‘’"


def _targets(repo_root):
    return sorted(repo_root.glob("plugins/*/skills/*/workflow.md"))


def check(repo_root):
    bad = []
    for path in _targets(repo_root):
        src = path.read_text(encoding="utf-8")
        for i, block in enumerate(re.findall(r"```ya?ml\n(.*?)\n```", src, re.DOTALL)):
            offenders = [q for q in SMART_QUOTES if q in block]
            if offenders:
                bad.append(
                    f"{path.relative_to(repo_root)} yaml block #{i}: "
                    f"contains {' '.join(offenders)}"
                )
    if bad:
        return {
            "status": "fail",
            "message": f"{len(bad)} yaml block(s) with smart quotes",
            "details": bad,
            "fix_hint": "replace U+201C/201D with ASCII \" and U+2018/2019 with ASCII '",
        }
    return {"status": "pass", "message": "all yaml blocks clean"}
