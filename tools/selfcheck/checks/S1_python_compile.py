"""S1: 所有 Python 脚本语法可编译"""
import py_compile
import tempfile
from pathlib import Path

META = {
    "id": "S1",
    "category": "scripts",
    "description": "all *.py in scripts/ and tools/ compile",
}


def check(repo_root):
    failed = []
    roots = [repo_root / "scripts", repo_root / "tools"]
    for root in roots:
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            try:
                with tempfile.NamedTemporaryFile(suffix=".pyc", delete=True) as tmp:
                    py_compile.compile(str(py), cfile=tmp.name, doraise=True)
            except py_compile.PyCompileError as exc:
                failed.append(f"{py.relative_to(repo_root)}: {exc.msg.strip()}")
            except Exception as exc:
                failed.append(f"{py.relative_to(repo_root)}: {exc!r}")
    if failed:
        return {
            "status": "fail",
            "message": f"{len(failed)} file(s) do not compile",
            "details": failed,
            "fix_hint": "run `python3 -m py_compile <file>` to see the exact error",
        }
    return {"status": "pass", "message": "all python files compile"}
