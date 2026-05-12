#!/usr/bin/env python3
"""prd-tools 版本迭代自检入口。

用法：
  python3 tools/selfcheck/run.py --all
  python3 tools/selfcheck/run.py --category docs
  python3 tools/selfcheck/run.py --all --format json
  python3 tools/selfcheck/run.py --all -v
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
CHECKS_DIR = HERE / "checks"


def discover_checks():
    """Load every checks/*.py exposing META dict and check() callable."""
    checks = []
    for f in sorted(CHECKS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            print(f"[selfcheck] failed to load {f.name}: {exc}", file=sys.stderr)
            continue
        meta = getattr(mod, "META", None)
        fn = getattr(mod, "check", None)
        if not meta or not callable(fn):
            continue
        checks.append((meta, fn))
    return checks


def run_one(meta, fn, repo_root, verbose=False):
    try:
        result = fn(repo_root=repo_root)
    except Exception as exc:
        result = {
            "status": "fail",
            "message": f"check raised: {exc!r}",
            "details": [],
            "fix_hint": "see traceback",
        }
    result.setdefault("status", "fail")
    result.setdefault("message", "")
    result.setdefault("details", [])
    result.setdefault("fix_hint", "")
    result["id"] = meta["id"]
    result["category"] = meta["category"]
    result["description"] = meta.get("description", "")
    return result


def format_text(results, verbose):
    lines = []
    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat):
        lines.append(f"\n### {cat}")
        for r in by_cat[cat]:
            icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}.get(r["status"], "?")
            lines.append(f"  {icon} [{r['id']}] {r['description']}")
            if r["status"] != "pass":
                lines.append(f"      {r['message']}")
                if r.get("fix_hint"):
                    lines.append(f"      → fix: {r['fix_hint']}")
                if verbose and r.get("details"):
                    for d in r["details"][:10]:
                        lines.append(f"        · {d}")
    summary = {"pass": 0, "warn": 0, "fail": 0}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    lines.append("")
    lines.append(
        f"Summary: {summary.get('pass', 0)} pass · "
        f"{summary.get('warn', 0)} warn · {summary.get('fail', 0)} fail"
    )
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true", help="run all checks")
    p.add_argument("--category", choices=["docs", "scripts", "contracts", "cross"])
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if not args.all and not args.category:
        p.error("--all or --category required")

    checks = discover_checks()
    if args.category:
        checks = [(m, fn) for m, fn in checks if m["category"] == args.category]

    results = [run_one(m, fn, REPO_ROOT, args.verbose) for m, fn in checks]

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_text(results, args.verbose))

    has_fail = any(r["status"] == "fail" for r in results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
