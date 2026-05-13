#!/usr/bin/env python3
"""Team Reference Inheritor — 团队知识库继承到成员仓

从团队仓的 team/ 目录读取聚合产物，按继承规则合并到成员仓的
_prd-tools/reference/ 目录。

Usage:
    python3 scripts/team-reference-inherit.py --repo-root <成员仓根路径>
    python3 scripts/team-reference-inherit.py --repo-root . --team-root ../dive-team-reference --dry-run

Output:
    继承报告输出到 stdout。
    产物写入成员仓 _prd-tools/reference/ 对应 YAML 文件。
    Exit code: 0 = 成功, 1 = 参数错误, 2 = 继承失败
"""

import argparse
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ── Helpers ──────────────────────────────────────────────────────────

def _read_yaml(path: Path) -> Optional[Dict]:
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Scope -> team file mapping
SCOPE_FILE_MAP = {
    "domain_terms": "05-domain.yaml",
    "contracts_cross_repo": "03-contracts.yaml",
    "coding_rules_fatal": "02-coding-rules.yaml",
}

# Scope -> list key within the YAML file
SCOPE_KEY_MAP = {
    "domain_terms": "terms",
    "contracts_cross_repo": "contracts",
    "coding_rules_fatal": "rules",
}

# Scope -> ID field within items
SCOPE_ID_MAP = {
    "domain_terms": "term",
    "contracts_cross_repo": "id",
    "coding_rules_fatal": "id",
}


def _add_inherit_meta(item: Dict) -> Dict:
    """Add team-common source metadata to an inherited item."""
    item = deepcopy(item)
    item["source"] = "team-common"
    item["read_only"] = True
    item["last_inherited"] = _iso_now()
    return item


# ── Inherit logic ────────────────────────────────────────────────────

def inherit_scope(local_data: Dict, team_data: Dict, scope: str,
                  force_override: bool = False) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Inherit items from team data into local data for a given scope.

    Returns:
        (added_items, skipped_items, overridden_items)
    """
    list_key = SCOPE_KEY_MAP.get(scope)
    id_field = SCOPE_ID_MAP.get(scope)
    if not list_key or not id_field:
        return [], [], []

    team_items = team_data.get(list_key, []) or []
    local_items = local_data.get(list_key, []) or []

    # Index local items by ID
    local_index = {}
    for item in local_items:
        item_id = item.get(id_field, "")
        if item_id:
            local_index[item_id] = item

    added = []
    skipped = []
    overridden = []

    for team_item in team_items:
        item_id = team_item.get(id_field, "")
        if not item_id:
            continue

        inherited = _add_inherit_meta(team_item)

        if item_id in local_index:
            local_item = local_index[item_id]
            if local_item.get("source") == "team-common":
                # Previously inherited item -> update
                # Find and replace in-place
                for i, li in enumerate(local_items):
                    if li.get(id_field) == item_id:
                        local_items[i] = inherited
                        overridden.append(inherited)
                        break
            elif force_override:
                # Force override (e.g. fatal coding rules)
                for i, li in enumerate(local_items):
                    if li.get(id_field) == item_id:
                        local_items[i] = inherited
                        overridden.append(inherited)
                        break
            else:
                # Local item exists and is not team-common -> skip
                skipped.append({
                    "id": item_id,
                    "reason": "local_item_exists",
                    "local_source": local_item.get("source", "self"),
                })
        else:
            # New item from team
            local_items.append(inherited)
            added.append(inherited)

    # Write back
    local_data[list_key] = local_items
    return added, skipped, overridden


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Team Reference Inheritor — 从团队仓继承公共知识到成员仓"
    )
    parser.add_argument(
        "--repo-root", required=True,
        help="成员仓根路径（含 _prd-tools/reference/）",
    )
    parser.add_argument(
        "--team-root",
        help="团队仓根路径（默认读 project-profile.yaml 的 team_reference.upstream_local_path）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="预览继承结果，不写入文件",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    dry_run = args.dry_run

    if not repo_root.is_dir():
        print(f"Error: {repo_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    # ── 1. Read member repo config ──
    ref_dir = repo_root / "_prd-tools" / "reference"
    if not ref_dir.is_dir():
        print(f"Error: {ref_dir} not found", file=sys.stderr)
        print("  Hint: run /reference Mode A first to build local reference",
              file=sys.stderr)
        sys.exit(1)

    profile = _read_yaml(ref_dir / "project-profile.yaml")
    if not profile:
        print(f"Error: {ref_dir / 'project-profile.yaml'} not found", file=sys.stderr)
        sys.exit(1)

    team_ref = profile.get("team_reference", {})
    inherit_scopes = team_ref.get("inherit_scopes", [])

    if not inherit_scopes:
        print("No inherit_scopes configured in project-profile.yaml")
        print("Nothing to inherit.")
        sys.exit(0)

    # Resolve team root
    if args.team_root:
        team_root = Path(args.team_root).resolve()
    else:
        upstream = team_ref.get("upstream_local_path", "")
        if not upstream:
            print("Error: team_reference.upstream_local_path not set and --team-root not provided",
                  file=sys.stderr)
            sys.exit(1)
        team_root = Path(upstream).expanduser().resolve()

    team_dir = team_root / "team"
    if not team_dir.is_dir():
        print(f"Error: {team_dir} not found", file=sys.stderr)
        print("  Hint: run /reference Mode T (team aggregation) in team repo first",
              file=sys.stderr)
        sys.exit(1)

    print("=== Team Reference Inheritor ===")
    print()
    print(f"Repo root:    {repo_root}")
    print(f"Team root:    {team_root}")
    print(f"Scopes:       {', '.join(inherit_scopes)}")
    print(f"Dry run:      {dry_run}")
    print()

    # ── 2. Inherit each scope ──
    total_added = 0
    total_skipped = 0
    total_overridden = 0
    scope_reports = []

    for scope in inherit_scopes:
        team_file = SCOPE_FILE_MAP.get(scope)
        if not team_file:
            print(f"  SKIP {scope}: unknown scope")
            continue

        team_data = _read_yaml(team_dir / team_file)
        if not team_data:
            print(f"  SKIP {scope}: {team_file} not found in team/")
            continue

        local_data = _read_yaml(ref_dir / team_file)
        if not local_data:
            print(f"  SKIP {scope}: {team_file} not found in local reference")
            continue

        # coding_rules_fatal: force override
        force = (scope == "coding_rules_fatal")

        added, skipped, overridden = inherit_scope(local_data, team_data, scope,
                                                    force_override=force)
        total_added += len(added)
        total_skipped += len(skipped)
        total_overridden += len(overridden)

        scope_reports.append({
            "scope": scope,
            "file": team_file,
            "added": len(added),
            "skipped": len(skipped),
            "overridden": len(overridden),
        })

        status_parts = []
        if added:
            status_parts.append(f"{len(added)} added")
        if overridden:
            status_parts.append(f"{len(overridden)} updated")
        if skipped:
            status_parts.append(f"{len(skipped)} skipped (local exists)")
        status_str = ", ".join(status_parts) or "no changes"
        print(f"  {scope:30s} -> {status_str}")

        # Write back (even in dry-run, we modified local_data in memory)
        if not dry_run:
            _write_yaml(ref_dir / team_file, local_data)

    # ── 3. Update last_synced ──
    if not dry_run:
        profile["team_reference"]["last_synced"] = _iso_now()
        _write_yaml(ref_dir / "project-profile.yaml", profile)

    # ── Report ──
    print()
    if dry_run:
        print(f"[DRY RUN] Would inherit: {total_added} new, {total_overridden} updated, {total_skipped} skipped")
    else:
        print(f"Inherited: {total_added} new, {total_overridden} updated, {total_skipped} skipped")
        if total_skipped > 0:
            print()
            print("Skipped items (local version takes precedence):")
            for sr in scope_reports:
                if sr["skipped"] > 0:
                    print(f"  {sr['scope']}: {sr['skipped']} items")

    if total_added == 0 and total_overridden == 0:
        print("\nRESULT: NO CHANGES — local reference is up to date")
    else:
        suffix = " (dry run)" if dry_run else ""
        print(f"\nRESULT: SUCCESS{suffix}")
    sys.exit(0)


if __name__ == "__main__":
    main()
