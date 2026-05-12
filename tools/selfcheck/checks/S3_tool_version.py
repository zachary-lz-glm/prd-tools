"""S3: *-step-gate.py --tool-version 默认值 = VERSION"""
import re
from pathlib import Path

META = {
    "id": "S3",
    "category": "scripts",
    "description": "step-gate scripts default --tool-version matches VERSION",
}


def check(repo_root):
    version_file = repo_root / "VERSION"
    if not version_file.exists():
        return {"status": "warn", "message": "VERSION file missing, skip"}
    expected = version_file.read_text().strip()

    issues = []
    for gate in (repo_root / "scripts").glob("*-step-gate.py") if (repo_root / "scripts").exists() else []:
        src = gate.read_text(encoding="utf-8")
        # Look for default=... near --tool-version
        for m in re.finditer(
            r'"--tool-version".*?default\s*=\s*([^,\s)]+)', src, re.DOTALL
        ):
            val = m.group(1).strip().strip('"').strip("'")
            # If it's a literal string (starts with digit or quote in original), compare
            if val and val != expected and not val.startswith("_"):
                # val may be a function call or literal; only flag obvious literal
                if re.match(r"^[\d.]+$", val):
                    issues.append(
                        f"{gate.relative_to(repo_root)}: default tool-version='{val}', VERSION='{expected}'"
                    )

    if issues:
        return {
            "status": "warn",
            "message": f"{len(issues)} stale default(s)",
            "details": issues,
            "fix_hint": "make the default read VERSION file (see P2-1 in docs/audit/v2.18.1/P2-fixes.md)",
        }
    return {"status": "pass", "message": "step-gate defaults aligned or parameterized"}
