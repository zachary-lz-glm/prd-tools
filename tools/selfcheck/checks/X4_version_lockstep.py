"""X4: VERSION / plugin.json / marketplace.json 五处版本号一致（CLAUDE.md 约定）"""
import json
import re
from pathlib import Path

META = {
    "id": "X4",
    "category": "cross",
    "description": "VERSION matches all 5 declared locations (lockstep)",
}


def check(repo_root):
    version_file = repo_root / "VERSION"
    if not version_file.exists():
        return {"status": "fail", "message": "VERSION file missing"}
    expected = version_file.read_text().strip()

    issues = []

    # plugin.json x2
    for pj in sorted(repo_root.glob("plugins/*/.claude-plugin/plugin.json")):
        try:
            v = json.loads(pj.read_text(encoding="utf-8")).get("version")
        except Exception as exc:
            issues.append(f"{pj.relative_to(repo_root)}: parse error {exc!r}")
            continue
        if v != expected:
            issues.append(f"{pj.relative_to(repo_root)}: version={v} (expected {expected})")

    # marketplace.json plugins[*].version
    mp = repo_root / ".claude-plugin" / "marketplace.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
            for i, p in enumerate(data.get("plugins", [])):
                if p.get("version") != expected:
                    issues.append(
                        f"marketplace.json plugins[{i}].version={p.get('version')} (expected {expected})"
                    )
        except Exception as exc:
            issues.append(f"marketplace.json: parse error {exc!r}")

    if issues:
        return {
            "status": "fail",
            "message": f"{len(issues)} version mismatch(es)",
            "details": issues,
            "fix_hint": "run scripts/release.sh to bump versions; never edit version files manually",
        }
    return {"status": "pass", "message": f"all 5 locations at {expected}"}
