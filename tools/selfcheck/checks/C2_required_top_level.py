"""C2: 每个 contract 的 required_top_level 字段在对应 output-contracts.md 里能找到"""
from pathlib import Path

META = {
    "id": "C2",
    "category": "contracts",
    "description": "contract required_top_level fields documented in output-contracts.md",
}


def check(repo_root):
    try:
        import yaml
    except ImportError:
        return {"status": "warn", "message": "PyYAML not installed, skip"}

    issues = []
    for contract_path in sorted(repo_root.glob("plugins/*/skills/*/references/contracts/*.yaml")):
        refs_dir = contract_path.parent.parent
        oc = refs_dir / "output-contracts.md"
        if not oc.exists():
            continue
        oc_text = oc.read_text(encoding="utf-8")
        try:
            c = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        for field in c.get("required_top_level") or []:
            if not isinstance(field, str):
                continue
            # crude: field name appears in output-contracts.md somewhere
            if field not in oc_text:
                issues.append(
                    f"{contract_path.relative_to(repo_root)}: "
                    f"required_top_level '{field}' not mentioned in "
                    f"{oc.relative_to(repo_root)}"
                )
    if issues:
        return {
            "status": "fail",
            "message": f"{len(issues)} undocumented required field(s)",
            "details": issues,
            "fix_hint": "either document the field in output-contracts.md or remove from required_top_level",
        }
    return {"status": "pass", "message": "all required_top_level fields documented"}
