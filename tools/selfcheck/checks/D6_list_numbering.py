"""D6: 编号列表里没有重复序号（"4. ... 4. ..." 这种 bug）"""
import re
from pathlib import Path

META = {
    "id": "D6",
    "category": "docs",
    "description": "numbered lists in step files have no duplicate numbers within a run",
}

NUM_RE = re.compile(r"^(\d+)\. ")


def _scan_file(path):
    """Scan a file for ordered-list runs and detect duplicate numbers within the same run.

    A "run" is a contiguous block of lines starting with `N. `. Non-list or blank
    lines end a run. Duplicate number within a run = bug.
    """
    issues = []
    current_run = {}  # number -> first line it appeared at in this run
    run_started = None

    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = NUM_RE.match(line)
        if m:
            n = m.group(1)
            if n in current_run:
                issues.append(
                    f"{path}: run starting L{run_started}: "
                    f"number {n} at L{current_run[n]} and again at L{lineno}"
                )
            else:
                current_run[n] = lineno
            if run_started is None:
                run_started = lineno
        else:
            # reset on non-list line
            current_run = {}
            run_started = None
    return issues


def check(repo_root):
    targets = (
        list(repo_root.glob("plugins/*/skills/*/workflow.md"))
        + list(repo_root.glob("plugins/*/skills/*/steps/*.md"))
    )
    issues = []
    for path in targets:
        for issue in _scan_file(path):
            rel = path.relative_to(repo_root)
            issues.append(issue.replace(str(path), str(rel)))
    if issues:
        return {
            "status": "fail",
            "message": f"{len(issues)} duplicate number(s) in numbered lists",
            "details": issues,
            "fix_hint": "renumber the list so every item has a unique sequential number",
        }
    return {"status": "pass", "message": "all numbered lists sequential"}
