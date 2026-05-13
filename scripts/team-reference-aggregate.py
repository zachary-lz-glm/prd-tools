#!/usr/bin/env python3
"""Team Reference Aggregator — 团队公共知识库聚合

从各成员仓的 _prd-tools/reference/ 读取 5 个 YAML 产物，按聚合策略合并到
团队仓的 team/ 目录，同时写入 snapshots/ 全量镜像和 build/ 状态文件。

Usage:
    python3 scripts/team-reference-aggregate.py --team-root <团队仓根路径>
    python3 scripts/team-reference-aggregate.py --team-root . --dry-run

Output:
    聚合报告输出到 stdout。
    产物写入 team/*.yaml, snapshots/{layer}/{repo}/, build/aggregation-report.yaml, build/conflicts.yaml
    Exit code: 0 = 成功, 1 = 参数错误, 2 = 聚合失败
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
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


def _tool_version(repo_root: Path) -> str:
    v = _read_yaml(repo_root / ".prd-tools-team-version")
    if v and isinstance(v, str):
        return v.strip()
    vf = repo_root / "VERSION"
    if vf.is_file():
        return vf.read_text().strip()
    return "unknown"


REF_FILES = [
    "01-codebase.yaml",
    "02-coding-rules.yaml",
    "03-contracts.yaml",
    "04-routing-playbooks.yaml",
    "05-domain.yaml",
]


# ── Repo resolution (local_path or remote_url) ─────────────────────

def _resolve_repo_root(mr: Dict, cleanup_list: List[str]) -> Optional[Path]:
    """Resolve member repo root from local_path or remote_url.

    Priority:
      1. local_path exists with _prd-tools/reference/ -> use directly
      2. remote_url provided -> git clone --depth 1 to temp dir
      3. Error

    cleanup_list collects temp dirs to remove after aggregation.
    """
    repo_name = mr.get("repo", "")

    # Try local_path first
    local_path = mr.get("local_path", "")
    if local_path:
        repo_root = Path(local_path).expanduser().resolve()
        ref_dir = repo_root / "_prd-tools" / "reference"
        if ref_dir.is_dir():
            return repo_root
        # local_path set but reference not found — fall through to remote

    # Try remote_url
    remote_url = mr.get("remote_url", "")
    if remote_url:
        branch = mr.get("branch", "HEAD")
        tmpdir = tempfile.mkdtemp(prefix=f"prd-tools-{repo_name}-")
        try:
            cmd = ["git", "clone", "--depth", "1"]
            if branch != "HEAD":
                cmd += ["--branch", branch]
            cmd += [remote_url, tmpdir]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                print(f"  git clone failed for {repo_name}: {result.stderr.strip()}",
                      file=sys.stderr)
                shutil.rmtree(tmpdir, ignore_errors=True)
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"  git clone error for {repo_name}: {e}", file=sys.stderr)
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None

        ref_dir = Path(tmpdir) / "_prd-tools" / "reference"
        if not ref_dir.is_dir():
            print(f"  SKIP {repo_name}: _prd-tools/reference/ not found in cloned repo",
                  file=sys.stderr)
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None

        cleanup_list.append(tmpdir)
        return Path(tmpdir)

    # Neither worked
    return None


# ── Snapshot ─────────────────────────────────────────────────────────

def write_snapshots(team_root: Path, layer: str, repo_name: str,
                    repo_root: Path) -> Dict:
    """Mirror member repo's reference YAML files into snapshots/."""
    snap_dir = team_root / layer / "snapshots" / repo_name
    snap_dir.mkdir(parents=True, exist_ok=True)

    ref_dir = repo_root / "_prd-tools" / "reference"
    meta = {
        "commit_sha": _get_head_sha(repo_root),
        "synced_at": _iso_now(),
        "source_repo": repo_name,
    }
    copied = []
    for fname in REF_FILES:
        src = ref_dir / fname
        if src.is_file():
            _write_yaml(snap_dir / fname, _read_yaml(src) or {})
            copied.append(fname)

    _write_yaml(snap_dir / "_snapshot-meta.yaml", meta)
    return {"repo": repo_name, "layer": layer, "files_copied": copied,
            "commit_sha": meta["commit_sha"]}


def _get_head_sha(repo_root: Path) -> str:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return "unknown"
    head = repo_root / ".git" / "HEAD"
    if not head.is_file():
        return "unknown"
    ref_line = head.read_text().strip()
    if ref_line.startswith("ref: "):
        ref_path = repo_root / ".git" / ref_line[5:]
        if ref_path.is_file():
            return ref_path.read_text().strip()[:12]
    return ref_line[:12]


# ── Aggregation: 03-contracts.yaml ───────────────────────────────────

def aggregate_contracts(member_data: Dict[str, Any], conflicts: List[Dict],
                        policy: str) -> Dict[str, Any]:
    """Merge contracts from all member repos.

    Strategy (union_by_id):
      - Same contract_id: merge producer/consumers/checked_by/consumer_repos
      - Producer mismatch -> conflict
      - Fields: use producer repo's definition
    """
    all_contracts = {}  # contract_id -> merged dict

    for repo_name, data in member_data.items():
        contracts = (data or {}).get("contracts", [])
        if not contracts:
            continue
        for c in contracts:
            cid = c.get("id", "")
            if not cid:
                continue
            # Only aggregate team_reference_candidate items
            if not c.get("team_reference_candidate", False):
                continue

            if cid not in all_contracts:
                all_contracts[cid] = deepcopy(c)
                all_contracts[cid]["_source_repos"] = [repo_name]
                continue

            merged = all_contracts[cid]
            merged["_source_repos"].append(repo_name)

            # Producer check
            existing_producer = merged.get("producer", "")
            new_producer = c.get("producer", "")
            if existing_producer and new_producer and existing_producer != new_producer:
                conflicts.append({
                    "type": "contract_producer_mismatch",
                    "contract_id": cid,
                    "divergent_claims": [
                        {"repo": merged["_source_repos"][0], "claim": f"producer={existing_producer}"},
                        {"repo": repo_name, "claim": f"producer={new_producer}"},
                    ],
                    "suggested_resolution": "ask owner",
                })
                merged["aggregation_status"] = "conflict"

            # Merge consumers (union)
            existing_consumers = set(merged.get("consumers", []))
            for cons in c.get("consumers", []):
                if cons not in existing_consumers:
                    merged.setdefault("consumers", []).append(cons)
                    existing_consumers.add(cons)

            # Merge checked_by (union)
            existing_checked = set(merged.get("checked_by", []))
            for cb in c.get("checked_by", []):
                if cb not in existing_checked:
                    merged.setdefault("checked_by", []).append(cb)
                    existing_checked.add(cb)

            # Merge consumer_repos (union by repo name)
            existing_repo_names = {
                r.get("repo", "") for r in merged.get("consumer_repos", [])
            }
            for cr in c.get("consumer_repos", []):
                if cr.get("repo", "") not in existing_repo_names:
                    merged.setdefault("consumer_repos", []).append(cr)
                    existing_repo_names.add(cr.get("repo", ""))

            # Set aggregation_status
            if merged.get("aggregation_status") != "conflict":
                all_consumers = set(merged.get("consumers", []))
                all_checked = set(merged.get("checked_by", []))
                merged["aggregation_status"] = (
                    "confirmed" if all_consumers.issubset(all_checked) else "candidate"
                )

    # Clean up internal field and set repo_scope
    result_contracts = []
    for cid, c in sorted(all_contracts.items()):
        c.pop("_source_repos", None)
        result_contracts.append(c)

    return {
        "repo_scope": {
            "authority": "team_common",
            "aggregation_policy": policy,
            "aggregated_at": _iso_now(),
        },
        "contracts": result_contracts,
    }


# ── Aggregation: 05-domain.yaml ──────────────────────────────────────

def aggregate_domain(member_data: Dict[str, Any], conflicts: List[Dict],
                     policy: str) -> Dict[str, Any]:
    """Merge domain terms from all member repos.

    Strategy (union_dedupe):
      - Same term, same definition: merge synonyms + evidence
      - Same term, different definition: keep both, mark divergence
    """
    merged_terms = {}
    merged_rules = {}
    merged_decisions = {}

    for repo_name, data in member_data.items():
        if not data:
            continue

        # Terms
        for t in data.get("terms", []):
            term_name = t.get("term", "")
            if not term_name:
                continue
            if term_name not in merged_terms:
                merged_terms[term_name] = deepcopy(t)
                merged_terms[term_name]["_sources"] = [repo_name]
                continue

            existing = merged_terms[term_name]
            existing["_sources"].append(repo_name)
            existing_def = existing.get("definition", "")
            new_def = t.get("definition", "")

            if existing_def == new_def:
                # Merge synonyms
                existing_syns = set(existing.get("synonyms", []))
                for syn in t.get("synonyms", []):
                    if syn not in existing_syns:
                        existing.setdefault("synonyms", []).append(syn)
                        existing_syns.add(syn)
                # Merge evidence
                existing_evs = {e.get("id", "") for e in existing.get("evidence", [])}
                for ev in t.get("evidence", []):
                    if ev.get("id", "") not in existing_evs:
                        existing.setdefault("evidence", []).append(ev)
            else:
                # Divergence: keep both definitions
                existing.setdefault("divergence", []).append({
                    "repo": repo_name,
                    "definition": new_def,
                })

        # Implicit rules (by id)
        for r in data.get("implicit_rules", []):
            rid = r.get("id", "")
            if rid and rid not in merged_rules:
                merged_rules[rid] = r

        # Decision log (by id)
        for d in data.get("decision_log", []):
            did = d.get("id", "")
            if did and did not in merged_decisions:
                merged_decisions[did] = d

    # Clean up internal fields
    terms = []
    for name, t in sorted(merged_terms.items()):
        t.pop("_sources", None)
        terms.append(t)

    return {
        "repo_scope": {
            "authority": "team_common",
            "aggregation_policy": policy,
            "aggregated_at": _iso_now(),
        },
        "domain_overview": "Aggregated from team member repos. See individual terms for sources.",
        "terms": terms,
        "implicit_rules": list(merged_rules.values()),
        "decision_log": list(merged_decisions.values()),
    }


# ── Aggregation: 02-coding-rules.yaml ────────────────────────────────

def aggregate_coding_rules(member_data: Dict[str, Any], conflicts: List[Dict],
                           policy: str) -> Dict[str, Any]:
    """Merge coding rules — only severity=fatal.

    Strategy (fatal_only):
      - Only aggregate rules with severity=fatal
      - Same rule_id with different description -> conflict
    """
    merged_rules = {}
    merged_danger_zones = {}

    for repo_name, data in member_data.items():
        if not data:
            continue

        for r in data.get("rules", []):
            if r.get("severity") != "fatal":
                continue
            rid = r.get("id", "")
            if not rid:
                continue
            if rid not in merged_rules:
                merged_rules[rid] = deepcopy(r)
                merged_rules[rid]["_source_repo"] = repo_name
                continue

            existing = merged_rules[rid]
            if existing.get("description") != r.get("description"):
                conflicts.append({
                    "type": "coding_rule_conflict",
                    "rule_id": rid,
                    "divergent_claims": [
                        {"repo": existing["_source_repo"], "description": existing.get("description", "")},
                        {"repo": repo_name, "description": r.get("description", "")},
                    ],
                    "suggested_resolution": "ask owner to align rule descriptions",
                })

        for dz in data.get("danger_zones", []):
            dz_id = dz.get("id", "")
            if dz_id and dz_id not in merged_danger_zones:
                merged_danger_zones[dz_id] = dz

    rules = []
    for rid, r in sorted(merged_rules.items()):
        r.pop("_source_repo", None)
        rules.append(r)

    return {
        "repo_scope": {
            "authority": "team_common",
            "aggregation_policy": policy,
            "aggregated_at": _iso_now(),
        },
        "rules": rules,
        "danger_zones": list(merged_danger_zones.values()),
        "war_stories": [],
    }


# ── Aggregation: 04-routing-playbooks.yaml ───────────────────────────

def aggregate_playbooks(member_data: Dict[str, Any], conflicts: List[Dict],
                        policy: str) -> Dict[str, Any]:
    """Merge routing playbooks — only cross-layer ones.

    Strategy (cross_layer_only):
      - Only aggregate playbooks whose target_surfaces involve 2+ layers
      - layer_steps per layer: use playbook_owner's version (not union)
      - Multiple owners claiming same layer -> conflict
    """
    merged_routing = {}
    merged_playbooks = {}
    merged_handoffs = set()
    merged_golden = {}

    for repo_name, data in member_data.items():
        if not data:
            continue

        # prd_routing: merge handoff_surfaces per route
        for pr in data.get("prd_routing", []):
            pr_id = pr.get("id", "")
            if not pr_id:
                continue
            surfaces = pr.get("target_surfaces", [])
            layers_involved = {s.get("layer", "") for s in surfaces if s.get("layer")}
            if len(layers_involved) < 2:
                continue
            if pr_id not in merged_routing:
                merged_routing[pr_id] = deepcopy(pr)
                merged_routing[pr_id]["_source_repo"] = repo_name
                continue
            # Merge handoff_surfaces
            existing_handoffs = merged_routing[pr_id].get("handoff_surfaces", [])
            existing_h_keys = {
                (h.get("repo", ""), h.get("layer", "")) for h in existing_handoffs
            }
            for h in pr.get("handoff_surfaces", []):
                key = (h.get("repo", ""), h.get("layer", ""))
                if key not in existing_h_keys:
                    merged_routing[pr_id].setdefault("handoff_surfaces", []).append(h)
                    existing_h_keys.add(key)

        # playbooks: only cross-layer
        for pb in data.get("playbooks", []):
            pb_id = pb.get("id", "")
            if not pb_id:
                continue
            # Check layer_steps for multi-layer presence
            layer_steps = pb.get("layer_steps", {})
            active_layers = [l for l in ("frontend", "bff", "backend", "external")
                             if layer_steps.get(l)]
            if len(active_layers) < 2:
                continue

            if pb_id not in merged_playbooks:
                merged_playbooks[pb_id] = deepcopy(pb)
                merged_playbooks[pb_id]["_source_repo"] = repo_name
                continue

            # Merge layer_steps: each layer goes to its owner
            existing = merged_playbooks[pb_id]
            for layer in ("frontend", "bff", "backend", "external"):
                new_steps = layer_steps.get(layer)
                if not new_steps:
                    continue
                existing_steps = existing.get("layer_steps", {}).get(layer)
                if not existing_steps:
                    existing.setdefault("layer_steps", {})[layer] = new_steps
                else:
                    # Both repos have steps for this layer -> conflict
                    conflicts.append({
                        "type": "playbook_layer_steps_conflict",
                        "playbook_id": pb_id,
                        "layer": layer,
                        "divergent_claims": [
                            {"repo": existing["_source_repo"], "steps_count": len(existing_steps)},
                            {"repo": repo_name, "steps_count": len(new_steps)},
                        ],
                        "suggested_resolution": "determine playbook_owner per layer",
                    })

            # Merge cross_repo_handoffs
            for h in pb.get("cross_repo_handoffs", []):
                hkey = (h.get("repo", ""), h.get("layer", ""))
                if hkey not in merged_handoffs:
                    merged_handoffs.add(hkey)
                    existing.setdefault("cross_repo_handoffs", []).append(h)

        # golden_samples with team_reference_candidate
        for gs in data.get("golden_samples", []):
            if gs.get("team_reference_candidate", False):
                gs_id = gs.get("id", "")
                if gs_id and gs_id not in merged_golden:
                    merged_golden[gs_id] = gs

    routing = []
    for pr_id, pr in sorted(merged_routing.items()):
        pr.pop("_source_repo", None)
        routing.append(pr)

    playbooks = []
    for pb_id, pb in sorted(merged_playbooks.items()):
        pb.pop("_source_repo", None)
        playbooks.append(pb)

    return {
        "repo_scope": {
            "authority": "team_common",
            "aggregation_policy": policy,
            "aggregated_at": _iso_now(),
        },
        "prd_routing": routing,
        "playbooks": playbooks,
        "golden_samples": list(merged_golden.values()),
    }


# ── Aggregation: 01-codebase.yaml (index only) ──────────────────────

def aggregate_codebase_index(contracts_data: Dict[str, Any],
                             domain_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build cross_repo_entities index from contracts and domain terms.

    Does NOT aggregate full codebase — only builds a lightweight index
    of cross-repo code coordinates.
    """
    entities = []
    seen_terms = set()

    for c in contracts_data.get("contracts", []):
        cid = c.get("id", "")
        term = c.get("name") or c.get("endpoint") or cid
        if not term or term in seen_terms:
            continue
        seen_terms.add(term)

        defined_in_repo = c.get("producer_repo", "")
        consumers = c.get("consumer_repos", [])

        if defined_in_repo and consumers:
            entity = {
                "term": term,
                "defined_in": {
                    "repo": defined_in_repo,
                },
                "consumed_by": [
                    {"repo": cr.get("repo", "")} for cr in consumers if cr.get("repo")
                ],
            }
            # Add file info if available from request/response fields
            req_fields = c.get("request_fields", [])
            if req_fields:
                src_file = req_fields[0].get("source", "")
                if src_file:
                    entity["defined_in"]["file"] = src_file
            entities.append(entity)

    return {
        "repo_scope": {
            "authority": "team_common",
            "aggregated_at": _iso_now(),
        },
        "cross_repo_entities": entities,
    }


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Team Reference Aggregator — 聚合成员仓 reference 到团队仓"
    )
    parser.add_argument(
        "--team-root", required=True,
        help="团队仓根路径（含 team/project-profile.yaml）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="预览聚合结果，不写入文件",
    )
    args = parser.parse_args()

    team_root = Path(args.team_root).resolve()
    dry_run = args.dry_run

    if not team_root.is_dir():
        print(f"Error: {team_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    # ── 1. Read config ──
    profile_path = team_root / "team" / "project-profile.yaml"
    profile = _read_yaml(profile_path)
    if not profile:
        print(f"Error: {profile_path} not found", file=sys.stderr)
        print("  Hint: create team/project-profile.yaml with team_reference.member_repos[]",
              file=sys.stderr)
        sys.exit(1)

    team_ref = profile.get("team_reference", {})
    member_repos = team_ref.get("member_repos", [])
    if not member_repos:
        print(f"Error: no member_repos configured in {profile_path}", file=sys.stderr)
        sys.exit(1)

    agg_policy = team_ref.get("aggregation_policy", {})
    version = _tool_version(team_root)

    print("=== Team Reference Aggregator ===")
    print()
    print(f"Team root:   {team_root}")
    print(f"Version:     {version}")
    print(f"Member repos: {len(member_repos)}")
    print(f"Dry run:     {dry_run}")
    print()

    # ── 2. Resolve member repos ──
    cleanup_dirs: List[str] = []
    valid_repos = []
    for mr in member_repos:
        repo_name = mr.get("repo", "")
        layer = mr.get("layer", "")
        if not repo_name or not layer:
            print(f"  SKIP {repo_name or '??'}: missing repo/layer", file=sys.stderr)
            continue

        repo_root = _resolve_repo_root(mr, cleanup_dirs)
        if repo_root is None:
            source = mr.get("local_path") or mr.get("remote_url", "??")
            print(f"  SKIP {repo_name}: no _prd-tools/reference/ found "
                  f"(local_path={mr.get('local_path', '')}, "
                  f"remote_url={mr.get('remote_url', '')})", file=sys.stderr)
            continue

        valid_repos.append({**mr, "_resolved_root": str(repo_root)})
        source_desc = "local" if mr.get("local_path") and Path(
            mr["local_path"]).expanduser().resolve() == repo_root else "remote"
        print(f"  OK   {repo_name} ({layer}) via {source_desc} -> {repo_root}")

    if not valid_repos:
        _cleanup(cleanup_dirs)
        print("\nError: no valid member repos found", file=sys.stderr)
        sys.exit(2)

    print()

    # ── 3. Read all member data ──
    # {file_name: {repo_name: yaml_data}}
    member_data: Dict[str, Dict[str, Any]] = {f: {} for f in REF_FILES}
    snapshot_reports = []

    for mr in valid_repos:
        repo_name = mr["repo"]
        repo_root = Path(mr["_resolved_root"])
        layer = mr["layer"]
        ref_dir = repo_root / "_prd-tools" / "reference"

        # Snapshot (skip in dry-run)
        if not dry_run:
            snap_report = write_snapshots(team_root, layer, repo_name, repo_root)
            snapshot_reports.append(snap_report)
        else:
            snapshot_reports.append({
                "repo": repo_name, "layer": layer,
                "files_copied": REF_FILES, "commit_sha": "(dry-run)",
            })

        # Read each YAML
        for fname in REF_FILES:
            data = _read_yaml(ref_dir / fname)
            member_data[fname][repo_name] = data or {}

    # ── 4. Aggregate ──
    conflicts: List[Dict] = []

    print("Aggregating...")
    contracts_result = aggregate_contracts(
        member_data["03-contracts.yaml"], conflicts,
        agg_policy.get("contracts", "union_by_id"),
    )
    print(f"  03-contracts: {len(contracts_result.get('contracts', []))} contracts")

    domain_result = aggregate_domain(
        member_data["05-domain.yaml"], conflicts,
        agg_policy.get("domain_terms", "union_dedupe"),
    )
    print(f"  05-domain:    {len(domain_result.get('terms', []))} terms")

    rules_result = aggregate_coding_rules(
        member_data["02-coding-rules.yaml"], conflicts,
        agg_policy.get("coding_rules", "fatal_only"),
    )
    print(f"  02-rules:     {len(rules_result.get('rules', []))} fatal rules")

    playbooks_result = aggregate_playbooks(
        member_data["04-routing-playbooks.yaml"], conflicts,
        agg_policy.get("playbooks", "cross_layer_only"),
    )
    print(f"  04-playbooks: {len(playbooks_result.get('playbooks', []))} cross-layer playbooks")

    codebase_result = aggregate_codebase_index(contracts_result, domain_result)
    print(f"  01-codebase:  {len(codebase_result.get('cross_repo_entities', []))} cross-repo entities")

    if conflicts:
        print(f"\n  Conflicts:    {len(conflicts)}")
        for c in conflicts:
            print(f"    - [{c['type']}] {c.get('contract_id') or c.get('rule_id') or c.get('playbook_id', '')}")

    # ── 5. Write outputs ──
    team_dir = team_root / "team"
    build_dir = team_root / "build"
    team_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("\n[DRY RUN] No files written.")
        print(f"\nWould write to:")
        print(f"  {team_dir / '01-codebase.yaml'}")
        print(f"  {team_dir / '02-coding-rules.yaml'}")
        print(f"  {team_dir / '03-contracts.yaml'}")
        print(f"  {team_dir / '04-routing-playbooks.yaml'}")
        print(f"  {team_dir / '05-domain.yaml'}")
        if conflicts:
            print(f"  {build_dir / 'conflicts.yaml'}")
        print(f"  {build_dir / 'aggregation-report.yaml'}")
    else:
        # Meta header for team files
        meta = {
            "schema_version": "4.0",
            "tool_version": version,
            "layer": "team-common",
            "last_verified": _iso_now()[:10],
        }

        codebase_result.update(meta)
        _write_yaml(team_dir / "01-codebase.yaml", codebase_result)

        rules_result.update(meta)
        _write_yaml(team_dir / "02-coding-rules.yaml", rules_result)

        contracts_result.update(meta)
        _write_yaml(team_dir / "03-contracts.yaml", contracts_result)

        playbooks_result.update(meta)
        _write_yaml(team_dir / "04-routing-playbooks.yaml", playbooks_result)

        domain_result.update(meta)
        _write_yaml(team_dir / "05-domain.yaml", domain_result)

        # Conflicts
        _write_yaml(build_dir / "conflicts.yaml", {
            "generated_at": _iso_now(),
            "total_conflicts": len(conflicts),
            "conflicts": conflicts,
        })

        # Aggregation report
        _write_yaml(build_dir / "aggregation-report.yaml", {
            "generated_at": _iso_now(),
            "tool_version": version,
            "member_repos": [
                {"repo": mr["repo"], "layer": mr["layer"]} for mr in valid_repos
            ],
            "snapshots": snapshot_reports,
            "summary": {
                "contracts": len(contracts_result.get("contracts", [])),
                "domain_terms": len(domain_result.get("terms", [])),
                "fatal_rules": len(rules_result.get("rules", [])),
                "cross_layer_playbooks": len(playbooks_result.get("playbooks", [])),
                "cross_repo_entities": len(codebase_result.get("cross_repo_entities", [])),
                "conflicts": len(conflicts),
            },
        })

        print(f"\nFiles written to {team_root}")
        print(f"  team/ -> 5 aggregated YAML files")
        print(f"  snapshots/ -> {len(snapshot_reports)} member repo mirrors")
        print(f"  build/aggregation-report.yaml")
        if conflicts:
            print(f"  build/conflicts.yaml ({len(conflicts)} conflicts)")

    # ── Exit ──
    if conflicts:
        print(f"\nRESULT: SUCCESS with {len(conflicts)} conflict(s) — review build/conflicts.yaml")
    else:
        print("\nRESULT: SUCCESS — no conflicts")
    _cleanup(cleanup_dirs)
    sys.exit(0)


def _cleanup(dirs: List[str]) -> None:
    """Remove temp dirs created by git clone."""
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
