"""D5: step 文件内部 <current_step> 值与文件名数字前缀一致（允许别名表）"""
import re
from pathlib import Path

META = {
    "id": "D5",
    "category": "docs",
    "description": "<current_step> in step file matches filename prefix",
}

# 允许的别名（例如 step-04-portal.md 的 current_step 就是 9，对应 --step 9）
ALIASES = {
    # key = filename stem, value = allowed current_step values
    "step-04-portal": {"9"},
}

STEP_TAG_RE = re.compile(r"<current_step>([\w.-]+)</current_step>")
STEM_RE = re.compile(r"^step-([\d.]+)(?:-|$)")


def check(repo_root):
    mismatches = []
    for path in sorted(repo_root.glob("plugins/*/skills/*/steps/step-*.md")):
        stem = path.stem
        src = path.read_text(encoding="utf-8")
        m = STEP_TAG_RE.search(src)
        if not m:
            continue
        declared = m.group(1)
        expected_from_name = STEM_RE.match(stem)
        allowed = set()
        if stem in ALIASES:
            allowed = ALIASES[stem]
        elif expected_from_name:
            raw = expected_from_name.group(1)
            # "01" and "1" are equivalent; accept both forms
            allowed = {raw, raw.lstrip("0") or "0"}
        if allowed and declared not in allowed:
            mismatches.append(
                f"{path.relative_to(repo_root)}: <current_step>{declared}</current_step> "
                f"but filename implies one of {sorted(allowed)}"
            )

    if mismatches:
        return {
            "status": "fail",
            "message": f"{len(mismatches)} mismatch(es)",
            "details": mismatches,
            "fix_hint": "align <current_step> to filename or register alias in tools/selfcheck/checks/D5_current_step.py ALIASES",
        }
    return {"status": "pass", "message": "all step tags aligned"}
