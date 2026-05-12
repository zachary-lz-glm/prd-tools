"""C1: 所有 contract YAML 可解析"""
from pathlib import Path

META = {
    "id": "C1",
    "category": "contracts",
    "description": "all contract YAML files parse",
}


def check(repo_root):
    try:
        import yaml
    except ImportError:
        return {"status": "warn", "message": "PyYAML not installed, skip"}

    failed = []
    for f in sorted(repo_root.glob("plugins/*/skills/*/references/contracts/*.yaml")):
        try:
            yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception as exc:
            failed.append(f"{f.relative_to(repo_root)}: {exc}")
    if failed:
        return {
            "status": "fail",
            "message": f"{len(failed)} unparseable",
            "details": failed,
            "fix_hint": "check yaml syntax (indentation, smart quotes)",
        }
    return {"status": "pass", "message": "all contracts parse"}
