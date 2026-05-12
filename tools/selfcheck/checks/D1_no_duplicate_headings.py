"""D1: workflow.md 没有重复章节（同名 heading 出现 2 次 = fail）"""
import re
from pathlib import Path

META = {
    "id": "D1",
    "category": "docs",
    "description": "workflow.md has no duplicate section headings",
}


def _targets(repo_root):
    return sorted(repo_root.glob("plugins/*/skills/*/workflow.md"))


def check(repo_root):
    dups = []
    for path in _targets(repo_root):
        seen = {}
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^## ", line):
                key = line.strip()
                if key in seen:
                    dups.append(
                        f"{path.relative_to(repo_root)}: "
                        f"'{key}' appears at L{seen[key]} and L{lineno}"
                    )
                else:
                    seen[key] = lineno
    if dups:
        return {
            "status": "fail",
            "message": f"{len(dups)} duplicate heading(s)",
            "details": dups,
            "fix_hint": "remove the duplicate block in workflow.md; if content differs, rename one (e.g. 'Step 8.6.1')",
        }
    return {"status": "pass", "message": f"{len(_targets(repo_root))} workflow.md file(s) clean"}
