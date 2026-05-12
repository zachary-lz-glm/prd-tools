"""C3: validate-artifact.py 对 dive-bff 快照产物通过（如存在）"""
import subprocess
import sys
from pathlib import Path

META = {
    "id": "C3",
    "category": "contracts",
    "description": "validate-artifact passes against dive-bff snapshot if available",
}

SNAPSHOT_BASE = Path(
    "/Users/didi/work/dive-bff/_prd-tools/distill/gas-station-new-driver.v2.18.0_snapshot"
)

ARTIFACTS = [
    ("contract-delta.contract.yaml", "context/contract-delta.yaml"),
    ("ai-friendly-prd.contract.yaml", "spec/ai-friendly-prd.md"),
    ("layer-impact.contract.yaml", "context/layer-impact.yaml"),
    ("requirement-ir.contract.yaml", "context/requirement-ir.yaml"),
]


def check(repo_root):
    validator = repo_root / "scripts" / "validate-artifact.py"
    if not validator.exists():
        return {"status": "warn", "message": "validate-artifact.py missing"}
    if not SNAPSHOT_BASE.exists():
        return {"status": "warn", "message": "dive-bff snapshot not found, skip live validation"}

    contracts_dir = repo_root / "plugins" / "prd-distill" / "skills" / "prd-distill" / "references" / "contracts"
    failures = []
    for contract_name, artifact_rel in ARTIFACTS:
        contract = contracts_dir / contract_name
        artifact = SNAPSHOT_BASE / artifact_rel
        if not contract.exists() or not artifact.exists():
            continue
        r = subprocess.run(
            [sys.executable, str(validator), "--contract", str(contract), "--artifact", str(artifact)],
            capture_output=True,
            timeout=30,
        )
        if r.returncode != 0:
            failures.append(
                f"{contract_name} vs {artifact_rel}: exit {r.returncode}"
            )
    if failures:
        return {
            "status": "fail",
            "message": f"{len(failures)} validation failure(s)",
            "details": failures,
            "fix_hint": "run the validate-artifact command manually to see specific missing/extra fields",
        }
    return {"status": "pass", "message": "all sampled artifacts pass"}
