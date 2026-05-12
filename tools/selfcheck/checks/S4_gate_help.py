"""S4: 所有 gate 脚本 --help 可执行不报错"""
import subprocess
import sys
from pathlib import Path

META = {
    "id": "S4",
    "category": "scripts",
    "description": "all gate scripts respond to --help without error",
}


def check(repo_root):
    failures = []
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.exists():
        return {"status": "warn", "message": "scripts/ not found"}

    for gate in sorted(scripts_dir.glob("*-gate.py")):
        try:
            r = subprocess.run(
                [sys.executable, str(gate), "--help"],
                capture_output=True,
                timeout=10,
            )
            if r.returncode != 0:
                failures.append(
                    f"{gate.relative_to(repo_root)}: --help exit {r.returncode}: "
                    f"{r.stderr.decode(errors='replace').splitlines()[:1]}"
                )
        except subprocess.TimeoutExpired:
            failures.append(f"{gate.relative_to(repo_root)}: --help timed out")
        except Exception as exc:
            failures.append(f"{gate.relative_to(repo_root)}: {exc!r}")
    if failures:
        return {
            "status": "fail",
            "message": f"{len(failures)} gate(s) broken",
            "details": failures,
            "fix_hint": "run the gate manually with --help to see the error",
        }
    return {"status": "pass", "message": "all gate scripts respond to --help"}
