"""S2: 用到 yaml 调用的 Python 文件都 import 了 yaml"""
import ast
from pathlib import Path

META = {
    "id": "S2",
    "category": "scripts",
    "description": "every file calling yaml.* imports yaml",
}


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _uses_yaml(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "yaml":
                return True
    return False


def check(repo_root):
    missing = []
    for py in (repo_root / "scripts").rglob("*.py") if (repo_root / "scripts").exists() else []:
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _uses_yaml(tree) and "yaml" not in _imports(tree):
            missing.append(f"{py.relative_to(repo_root)}: uses yaml.* but does not import yaml")
    for py in (repo_root / "tools").rglob("*.py") if (repo_root / "tools").exists() else []:
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _uses_yaml(tree) and "yaml" not in _imports(tree):
            missing.append(f"{py.relative_to(repo_root)}: uses yaml.* but does not import yaml")
    if missing:
        return {
            "status": "fail",
            "message": f"{len(missing)} file(s) call yaml.* without importing yaml",
            "details": missing,
            "fix_hint": "add `import yaml` to the file header",
        }
    return {"status": "pass", "message": "yaml usage consistent with imports"}
