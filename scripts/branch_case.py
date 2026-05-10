#!/usr/bin/env python3
"""
branch_case.py — Branch-backed Benchmark Case Manager

Creates and manages benchmark cases that map PRD documents to their
implementation branches, generating diff summaries and oracle drafts
for evaluating prd-distill output quality.

Subcommands:
  create        Create case directory with case.yaml and README.md
  add-target    Add a multi-repo target (frontend/bff) to an existing case
  diff          Generate branch-diff-summary.yaml from git diff
  draft-oracle  Generate oracle-draft.yaml from diff summary
  merge-oracle  Merge multi-layer oracle drafts into unified oracle
  bundle        Generate bundle attribution for multi-PRD branches

Usage:
  python3 scripts/branch_case.py create \\
    --case-id simba-shift-signin-award \\
    --title "Simba 新增班次签到奖" \\
    --prd "/path/to/PRD.docx" \\
    --repo "/path/to/repo" \\
    --base master --impl AI_dive_simba_shift \\
    --bundle AI_dive_simba_shift

  # Multi-repo targets
  python3 scripts/branch_case.py add-target \\
    --case-id simba-shift-signin-award --layer frontend \\
    --repo /path --base master --impl <branch>

  python3 scripts/branch_case.py diff --case-id simba-shift-signin-award --layer frontend
  python3 scripts/branch_case.py draft-oracle --case-id simba-shift-signin-award --layer frontend
  python3 scripts/branch_case.py merge-oracle --case-id simba-shift-signin-award
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "benchmarks" / "branch-cases"

# ──────────────────────────────────────────
# Bundle signal definitions
# ──────────────────────────────────────────

BUNDLE_SIGNALS = {
    "simba-shift-signin-award": {
        "prd_file": "DIVE-Simba新增班次签到奖-L1.docx",
        "signals": [
            "签到", "sign", "signin", "checkin", "attendance",
            "班次签到", "ShiftCheckin", "shiftCheckin",
            "签到奖", "checkin_award",
        ],
    },
    "simba-shift-rider-type": {
        "prd_file": "DIVE-simba新增shift骑手类型-L1.docx",
        "signals": [
            "骑手类型", "rider", "courier", "ridertype",
            "foodRiderType", "rider_type", "courier_type",
            "shift.*type", "rider.*select",
        ],
    },
    "simba-shift-order-scope": {
        "prd_file": "DIVE-Simba支持区分班次内外订单-L1.docx",
        "signals": [
            "班次内", "班次外", "inside", "outside",
            "order.*scope", "shift.*order", "shift.*inside",
            "shift.*outside", "班次.*订单", "insideShift",
            "outsideShift", "shift_order",
        ],
    },
}

# Shared signals that appear in all three simba PRDs
SHARED_SIGNALS = [
    "shift", "simba", "班次", "acelera",
    "ShiftCheckin", "shiftCheckin",
]

# ──────────────────────────────────────────
# Frontend file filter
# ──────────────────────────────────────────

FRONTEND_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".vue"}

# ──────────────────────────────────────────
# Anchor truncation limit
# ──────────────────────────────────────────

MAX_ANCHORS_PER_LAYER = 80


# ──────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────


def _run_git(repo, *args):
    """Run git command in repo, return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  git error: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout


def _yaml_str(s):
    """Escape YAML string."""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _write_yaml(path, lines):
    """Write lines as YAML file."""
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _case_dir(case_id):
    """Get case directory path."""
    return BENCHMARKS_DIR / case_id


def _extract_yaml_value(text, key):
    """Extract a value from simple YAML key: value lines."""
    m = re.search(rf'^{key}:\s+"?(.+?)"?\s*$', text, re.MULTILINE)
    return m.group(1) if m else ""


def _unquote(s):
    """Remove surrounding quotes from YAML value."""
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _set_yaml_value(text, key, value):
    """Set a top-level key in a simple YAML text, returning updated text."""
    pattern = rf'^({key}:\s*).*$'
    new_line = f'{key}: {_yaml_str(value)}'
    if re.search(pattern, text, re.MULTILINE):
        return re.sub(pattern, new_line, text, flags=re.MULTILINE)
    # Key not found, append
    return text.rstrip("\n") + "\n" + new_line + "\n"


def _is_frontend_file(path):
    """Check if a file path is a frontend source file under src/."""
    # Support monorepo paths like app/dive/src/...
    src_idx = path.find("/src/")
    if src_idx >= 0:
        rel_after_src = path[src_idx + 1:]  # "src/..."
    elif path.startswith("src/"):
        rel_after_src = path
    else:
        return False
    ext = os.path.splitext(rel_after_src)[1].lower()
    return ext in FRONTEND_EXTENSIONS


# ──────────────────────────────────────────
# Create subcommand
# ──────────────────────────────────────────


def cmd_create(args):
    """Create case directory with case.yaml and README.md."""
    case_id = args.case_id
    d = _case_dir(case_id)
    d.mkdir(parents=True, exist_ok=True)

    bundle_id = args.bundle or ""
    branch_mode = "bundle" if bundle_id else "single"

    # case.yaml
    case_yaml = [
        f'schema_version: "1.0"',
        f'case_id: {_yaml_str(case_id)}',
        f'title: {_yaml_str(args.title)}',
        f'prd_source: {_yaml_str(args.prd)}',
        f'repo: {_yaml_str(args.repo)}',
        f'base_ref: {_yaml_str(args.base)}',
        f'impl_ref: {_yaml_str(args.impl)}',
        f'branch_mode: {_yaml_str(branch_mode)}',
    ]
    if bundle_id:
        case_yaml.append(f'bundle_id: {_yaml_str(bundle_id)}')
    case_yaml += [
        f'status: "draft"',
        f'notes: []',
    ]
    _write_yaml(d / "case.yaml", case_yaml)
    print(f"Created: {d / 'case.yaml'}")

    # README.md
    readme_lines = [
        f"# {args.title}",
        "",
        f"| 字段 | 值 |",
        f"|------|-----|",
        f"| Case ID | `{case_id}` |",
        f"| PRD | `{Path(args.prd).name}` |",
        f"| 仓库 | `{args.repo}` |",
        f"| Base | `{args.base}` |",
        f"| Impl | `{args.impl}` |",
        f"| 模式 | `{branch_mode}` |",
    ]
    if bundle_id:
        readme_lines += [
            f"| Bundle | `{bundle_id}` |",
            "",
            f"**注意**：此分支与另外 2 个 PRD 共享同一实现分支 `{args.impl}`。",
            f"Diff 无法天然归属于某一个 PRD。code_anchors 的归因基于信号词匹配，",
            f"低置信度项已标记 `needs_review` 或 `shared_candidate`。",
        ]
    readme_lines += [
        "",
        "## 文件说明",
        "",
        "| 文件 | 用途 |",
        "|------|------|",
        "| `case.yaml` | Case 元数据 |",
        "| `branch-diff-summary.yaml` | 分支 diff 分析（`diff` 命令生成） |",
        "| `oracle-draft.yaml` | Oracle 草稿（`draft-oracle` 命令生成） |",
        "",
    ]
    _write_yaml(d / "README.md", readme_lines)
    print(f"Created: {d / 'README.md'}")
    print(f"Case directory: {d}")


# ──────────────────────────────────────────
# Add-target subcommand
# ──────────────────────────────────────────


def cmd_add_target(args):
    """Add a multi-repo target (frontend/bff) to an existing case."""
    case_id = args.case_id
    layer = args.layer  # e.g. "frontend" or "bff"
    d = _case_dir(case_id)

    case_path = d / "case.yaml"
    if not case_path.exists():
        print(f"Error: case.yaml not found in {d}", file=sys.stderr)
        sys.exit(1)

    case_text = case_path.read_text(encoding="utf-8")

    # Extract legacy fields
    legacy_repo = _extract_yaml_value(case_text, "repo")
    legacy_base = _extract_yaml_value(case_text, "base_ref")
    legacy_impl = _extract_yaml_value(case_text, "impl_ref")
    legacy_bundle = _extract_yaml_value(case_text, "bundle_id")

    # Check if targets field already exists
    has_targets = "targets:" in case_text

    # Build the target entry
    target_entry_lines = []
    target_entry_lines.append(f'    layer: {_yaml_str(layer)}')
    target_entry_lines.append(f'    repo: {_yaml_str(args.repo)}')
    target_entry_lines.append(f'    base_ref: {_yaml_str(args.base)}')
    target_entry_lines.append(f'    impl_ref: {_yaml_str(args.impl)}')
    if args.bundle:
        target_entry_lines.append(f'    bundle_id: {_yaml_str(args.bundle)}')
    target_entry_lines.append(f'    status: "draft"')
    target_block = "\n".join(target_entry_lines)

    if not has_targets:
        # Migrate: create targets field from legacy repo/base/impl as bff target
        # Determine legacy bundle_id
        legacy_bundle_line = ""
        if legacy_bundle:
            legacy_bundle_line = f'\n    bundle_id: {_yaml_str(legacy_bundle)}'

        targets_section = (
            f'\ntargets:\n'
            f'  - layer: "bff"\n'
            f'    repo: {_yaml_str(legacy_repo)}\n'
            f'    base_ref: {_yaml_str(legacy_base)}\n'
            f'    impl_ref: {_yaml_str(legacy_impl)}'
            f'{legacy_bundle_line}\n'
            f'    status: "draft"\n'
            f'  - {target_block.lstrip()}\n'
        )
        # Insert targets before status field
        case_text = case_text.replace(
            'status: "draft"',
            targets_section + 'status: "draft"',
            1,
        )
    else:
        # Check if this layer already exists in targets
        if f'layer: {_yaml_str(layer)}' in case_text:
            # Update existing target — find and replace the block
            # Parse existing targets to find the one matching layer
            # Simpler approach: rebuild the targets section
            existing_targets = _parse_targets(case_text)
            # Update or append
            found = False
            for t in existing_targets:
                if t.get("layer") == layer:
                    t["repo"] = args.repo
                    t["base_ref"] = args.base
                    t["impl_ref"] = args.impl
                    if args.bundle:
                        t["bundle_id"] = args.bundle
                    t["status"] = "draft"
                    found = True
                    break
            if not found:
                new_target = {
                    "layer": layer,
                    "repo": args.repo,
                    "base_ref": args.base,
                    "impl_ref": args.impl,
                    "status": "draft",
                }
                if args.bundle:
                    new_target["bundle_id"] = args.bundle
                existing_targets.append(new_target)

            # Rebuild targets section
            case_text = _rebuild_targets_in_yaml(case_text, existing_targets)
        else:
            # Append new target entry
            # Find the last target entry and append after it
            # Insert before the closing of targets section (before status/notes)
            insert_marker = 'status: "draft"'
            new_entry = f'  - {target_entry_lines[0].strip()}\n'
            for line in target_entry_lines[1:]:
                new_entry += f'  {line.strip()}\n'

            # Insert before the final status: "draft" line
            last_status_pos = case_text.rfind(insert_marker)
            if last_status_pos >= 0:
                case_text = (
                    case_text[:last_status_pos]
                    + new_entry
                    + case_text[last_status_pos:]
                )

    # Upgrade schema_version to 1.1
    case_text = case_text.replace('schema_version: "1.0"', 'schema_version: "1.1"', 1)
    if 'schema_version: "1.1"' not in case_text:
        case_text = _set_yaml_value(case_text, "schema_version", "1.1")

    case_path.write_text(case_text, encoding="utf-8")
    print(f"Updated: {case_path}")

    # Create targets/<layer>/ directory
    target_dir = d / "targets" / layer
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {target_dir}")

    # Auto-backfill targets/bff from root legacy files when adding a non-bff target
    if layer != "bff":
        bff_target_dir = d / "targets" / "bff"
        if not bff_target_dir.exists():
            bff_target_dir.mkdir(parents=True, exist_ok=True)
            for fname in ("branch-diff-summary.yaml", "oracle-draft.yaml"):
                root_file = d / fname
                if root_file.exists():
                    content = root_file.read_text(encoding="utf-8")
                    # Inject layer: "bff" after schema_version line if missing
                    if "layer:" not in content:
                        content = content.replace(
                            'schema_version:',
                            'layer: "bff"\nschema_version:',
                            1,
                        )
                    (bff_target_dir / fname).write_text(content, encoding="utf-8")
                    print(f"Backfilled: {bff_target_dir / fname}")


def _parse_targets(case_text):
    """Parse targets list from case.yaml text."""
    targets = []
    current = {}
    in_targets = False

    for line in case_text.split("\n"):
        stripped = line.strip()

        if stripped == "targets:":
            in_targets = True
            continue

        if not in_targets:
            continue

        # Detect end of targets section: a line at indent 0 that is not a comment
        if line and not line[0].isspace() and stripped and not stripped.startswith("#"):
            in_targets = False
            if current:
                targets.append(current)
                current = {}
            continue

        if stripped.startswith("- layer:"):
            if current:
                targets.append(current)
            current = {"layer": _unquote(stripped.split(":", 1)[1].strip())}
        elif current:
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                current[k.strip()] = _unquote(v.strip())

    if current:
        targets.append(current)
    return targets


def _rebuild_targets_in_yaml(case_text, targets):
    """Replace the targets section in case.yaml text with rebuilt targets."""
    lines = case_text.split("\n")
    new_lines = []
    in_targets = False
    targets_written = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "targets:" and not targets_written:
            in_targets = True
            # Write new targets section
            new_lines.append("targets:")
            for t in targets:
                new_lines.append(f'  - layer: {_yaml_str(t["layer"])}')
                new_lines.append(f'    repo: {_yaml_str(t["repo"])}')
                new_lines.append(f'    base_ref: {_yaml_str(t["base_ref"])}')
                new_lines.append(f'    impl_ref: {_yaml_str(t["impl_ref"])}')
                if t.get("bundle_id"):
                    new_lines.append(f'    bundle_id: {_yaml_str(t["bundle_id"])}')
                new_lines.append(f'    status: {_yaml_str(t.get("status", "draft"))}')
            targets_written = True
            i += 1
            continue

        if in_targets:
            # Skip old target lines until we hit a non-indented line
            if line and not line[0].isspace() and stripped:
                in_targets = False
                new_lines.append(line)
            # else skip (old target content)
        else:
            new_lines.append(line)

        i += 1

    return "\n".join(new_lines)


# ──────────────────────────────────────────
# Diff subcommand
# ──────────────────────────────────────────


def _parse_diff_stat(repo, base, impl, layer=None):
    """Get changed files with additions/deletions."""
    output = _run_git(repo, "diff", "--numstat", f"{base}...{impl}")
    if not output.strip():
        # Branch already merged — use first-parent commit diff
        output = _merged_branch_diff(repo, impl)
    if not output.strip():
        return []
    files = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            adds, dels, path = parts[0], parts[1], parts[2]
            # Handle renames
            if "=>" in path:
                old_new = path.split("=>")
                path = old_new[-1].strip().strip("}")
                change_type = "renamed"
            elif adds == "-" and dels == "-":
                continue  # binary file
            else:
                change_type = "added" if path not in _run_git(
                    repo, "ls-tree", "-r", "--name-only", base
                ) else "modified"
            files.append({
                "path": path.strip(),
                "change_type": change_type,
                "additions": int(adds) if adds != "-" else 0,
                "deletions": int(dels) if dels != "-" else 0,
            })
    return files


def _merged_branch_diff(repo, impl):
    """Generate synthetic diff stat for a merged branch using first-parent commits."""
    # Get all first-parent non-merge commits on the branch
    commits = _run_git(repo, "log", "--first-parent", "--no-merges",
                       "--format=%H", impl).strip().split("\n")
    if not commits or not commits[0]:
        return ""

    # Aggregate file changes across all feature commits
    file_stats = {}  # path -> {adds, dels}
    for commit_hash in commits:
        output = _run_git(repo, "diff-tree", "--numstat", "-r", commit_hash)
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                adds, dels, path = parts[0], parts[1], parts[2]
                if adds == "-" and dels == "-":
                    continue  # binary
                path = path.strip()
                # Skip non-src files for cleaner output
                if not path.startswith("src/"):
                    continue
                if path not in file_stats:
                    file_stats[path] = {"adds": 0, "dels": 0}
                file_stats[path]["adds"] += int(adds) if adds != "-" else 0
                file_stats[path]["dels"] += int(dels) if dels != "-" else 0

    # Reconstruct numstat format
    lines = []
    for path, stats in sorted(file_stats.items()):
        lines.append(f"{stats['adds']}\t{stats['dels']}\t{path}")
    return "\n".join(lines)


def _parse_diff_symbols(repo, base, impl, path, layer=None):
    """Extract symbols from diff hunks."""
    output = _run_git(repo, "diff", f"{base}...{impl}", "--", path)
    symbols = []
    seen = set()

    # BFF/TypeScript patterns
    bff_patterns = [
        (r'^\+\s*(export\s+)?(const|let|var)\s+(\w+)', 'const'),
        (r'^\+\s*(export\s+)?(function)\s+(\w+)', 'function'),
        (r'^\+\s*(export\s+)?(class)\s+(\w+)', 'class'),
        (r'^\+\s*(export\s+)?(interface)\s+(\w+)', 'interface'),
        (r'^\+\s*(export\s+)?(enum)\s+(\w+)', 'enum'),
        (r'^\+\s*(export\s+)?type\s+(\w+)', 'const'),
        (r'^\+\s*case\s+(\d+)', 'switch_case'),
    ]

    # Frontend-specific patterns (Vue/React)
    fe_patterns = [
        # defineComponent
        (r'^\+\s*(export\s+)?default\s+defineComponent\(', 'component'),
        (r'^\+\s*defineComponent\s*\(', 'component'),
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*defineComponent', 'component'),
        # Composables / hooks
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*use\w+', 'hook'),
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*use[A-Z]', 'hook'),
        # Route definitions
        (r'^\+\s*(const|let)\s+(\w+).*route', 'route'),
        (r'^\+\s*path:\s*[\'"]([^\'"]+)[\'"]', 'route'),
        # Config / env
        (r'^\+\s*(export\s+)?(const|let)\s+(\w+)(Config|CONFIG|Conf|CONF)', 'config'),
        (r'^\+\s*(export\s+)?(const|let)\s+(\w+).*ENV', 'config'),
        # i18n
        (r'^\+\s*(const|let)\s+(\w+).*(i18n|locale|t\()', 'i18n'),
        (r'^\+\s*(export\s+)?(const|let)\s+(\w+).*translation', 'i18n'),
        # Tracking / analytics
        (r'^\+\s*(const|let)\s+(\w+).*(track|analytics|report|埋点|曝光)', 'tracking'),
        (r'^\+\s*(const|let)\s+(\w+).*(Track|Analytics|Report)', 'tracking'),
        # Vue <script setup> named exports
        (r'^\+\s*(const|let|function)\s+(\w+)', 'variable'),
        # Vue template refs and reactive
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*ref\(', 'ref'),
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*reactive\(', 'reactive'),
        (r'^\+\s*(const|let)\s+(\w+)\s*=\s*computed\(', 'computed'),
    ]

    # Standard TS/JS patterns (shared)
    shared_patterns = [
        (r'^\+\s*(export\s+)?(const|let|var)\s+(\w+)', 'const'),
        (r'^\+\s*(export\s+)?(function)\s+(\w+)', 'function'),
        (r'^\+\s*(export\s+)?(class)\s+(\w+)', 'class'),
        (r'^\+\s*(export\s+)?(interface)\s+(\w+)', 'interface'),
        (r'^\+\s*(export\s+)?(enum)\s+(\w+)', 'enum'),
        (r'^\+\s*(export\s+)?type\s+(\w+)', 'const'),
        (r'^\+\s*case\s+(\d+)', 'switch_case'),
    ]

    if layer == "frontend":
        # Use frontend patterns first, then fall back to shared
        patterns = fe_patterns + shared_patterns
    else:
        patterns = bff_patterns

    for line in output.split("\n"):
        for pattern, kind in patterns:
            m = re.match(pattern, line)
            if m:
                sym_name = m.group(m.lastindex)
                key = (path, sym_name, kind)
                if key not in seen:
                    seen.add(key)
                    symbols.append({
                        "path": path,
                        "symbol": sym_name,
                        "kind": kind,
                        "confidence": "medium",
                    })
    return symbols


def _get_change_type(repo, base, impl, path):
    """Determine change type for a file."""
    # Check if file exists in base
    base_check = _run_git(repo, "ls-tree", f"{base}", "--", path)
    impl_check = _run_git(repo, "ls-tree", f"{impl}", "--", path)
    if not base_check.strip() and impl_check.strip():
        return "added"
    elif base_check.strip() and not impl_check.strip():
        return "deleted"
    else:
        return "modified"


def _get_diff_targets(args, case_text):
    """Resolve (repo, base, impl, bundle_id, output_dir, layer_name) for diff."""
    case_id = args.case_id
    d = _case_dir(case_id)
    layer = getattr(args, "layer", None)

    if not layer:
        # Legacy mode: use top-level repo/base/impl
        repo = _extract_yaml_value(case_text, "repo")
        base = _extract_yaml_value(case_text, "base_ref")
        impl = _extract_yaml_value(case_text, "impl_ref")
        bundle_id = _extract_yaml_value(case_text, "bundle_id")
        return [(repo, base, impl, bundle_id, d, None)]

    # Layer mode: resolve from targets
    targets = _parse_targets(case_text)
    target = None
    for t in targets:
        if t.get("layer") == layer:
            target = t
            break

    if not target:
        print(f"Error: target layer '{layer}' not found in case.yaml", file=sys.stderr)
        sys.exit(1)

    repo = target["repo"]
    base = target["base_ref"]
    impl = target["impl_ref"]
    bundle_id = target.get("bundle_id", "") or _extract_yaml_value(case_text, "bundle_id")
    output_dir = d / "targets" / layer
    output_dir.mkdir(parents=True, exist_ok=True)

    return [(repo, base, impl, bundle_id, output_dir, layer)]


def _do_diff_for_target(case_id, repo, base, impl, bundle_id, output_dir, layer, is_bundle):
    """Run diff logic for a single target, writing output to output_dir."""
    print(f"  Layer: {layer or 'bff (legacy)'}")
    print(f"  Repo: {repo}")
    print(f"  Diff: {base}...{impl}")

    # Fetch only if branch not available locally
    local_check = _run_git(repo, "rev-parse", "--verify", impl)
    if not local_check.strip():
        _run_git(repo, "fetch", "origin", impl, "--quiet")

    # Parse diff stat
    files = _parse_diff_stat(repo, base, impl, layer=layer)
    print(f"  Changed files (raw): {len(files)}")

    # For frontend layer, filter to src/ frontend files only
    if layer == "frontend":
        files = [f for f in files if _is_frontend_file(f["path"])]
        print(f"  Frontend files (filtered): {len(files)}")

    # Fix change types (best effort for merged branches)
    for f in files:
        if f["change_type"] not in ("added", "modified", "deleted", "renamed"):
            f["change_type"] = _get_change_type(repo, base, impl, f["path"])
            if f["change_type"] not in ("added", "modified", "deleted", "renamed"):
                f["change_type"] = "modified"  # default for merged branches

    # Extract symbols from each changed file
    all_symbols = []
    for f in files:
        syms = _parse_diff_symbols(repo, base, impl, f["path"], layer=layer)
        all_symbols.extend(syms)

    print(f"  Symbols extracted: {len(all_symbols)}")

    # Attribution for bundle cases
    if is_bundle and bundle_id in ("AI_dive_simba_shift",):
        _apply_bundle_attribution(files, all_symbols, case_id, bundle_id)
    else:
        # Single branch — all high confidence
        for f in files:
            f["attribution"] = {
                "confidence": "high",
                "prd_signals": [],
                "reason": "single-branch case, all changes attributable",
            }
        for s in all_symbols:
            s["confidence"] = "high"

    # Generate branch-diff-summary.yaml
    layer_label = layer or "bff"
    lines = [
        f'schema_version: "1.0"',
        f'case_id: {_yaml_str(case_id)}',
        f'layer: {_yaml_str(layer_label)}',
        f'base_ref: {_yaml_str(base)}',
        f'impl_ref: {_yaml_str(impl)}',
        f'changed_files:',
    ]

    for f in files:
        lines.append(f'  - path: {_yaml_str(f["path"])}')
        lines.append(f'    change_type: {_yaml_str(f["change_type"])}')
        lines.append(f'    additions: {f["additions"]}')
        lines.append(f'    deletions: {f["deletions"]}')
        attr = f.get("attribution", {})
        lines.append(f'    attribution:')
        lines.append(f'      confidence: {_yaml_str(attr.get("confidence", "high"))}')
        prd_sigs = attr.get("prd_signals", [])
        if prd_sigs:
            lines.append(f'      prd_signals:')
            for sig in prd_sigs:
                lines.append(f'        - {_yaml_str(sig)}')
        else:
            lines.append(f'      prd_signals: []')
        lines.append(f'      reason: {_yaml_str(attr.get("reason", ""))}')

    lines.append(f'symbols:')
    for s in all_symbols:
        lines.append(f'  - path: {_yaml_str(s["path"])}')
        lines.append(f'    symbol: {_yaml_str(s["symbol"])}')
        lines.append(f'    kind: {_yaml_str(s["kind"])}')
        lines.append(f'    confidence: {_yaml_str(s["confidence"])}')

    lines.append(f'risk_notes: []')

    out_path = output_dir / "branch-diff-summary.yaml"
    _write_yaml(out_path, lines)
    print(f"Written: {out_path}")

    # If layer is bff, also update root-level branch-diff-summary.yaml (compatibility)
    if layer == "bff":
        d = _case_dir(case_id)
        root_path = d / "branch-diff-summary.yaml"
        _write_yaml(root_path, lines)
        print(f"Updated (root compat): {root_path}")

    # Also generate bundle summary if this is a bundle case
    if is_bundle:
        _generate_bundle_summary(bundle_id, files, all_symbols, case_id, layer=layer)

    return files, all_symbols


def cmd_diff(args):
    """Generate branch-diff-summary.yaml from git diff."""
    case_id = args.case_id
    d = _case_dir(case_id)
    if not (d / "case.yaml").exists():
        print(f"Error: case.yaml not found in {d}", file=sys.stderr)
        sys.exit(1)

    case_text = (d / "case.yaml").read_text(encoding="utf-8")
    bundle_id = _extract_yaml_value(case_text, "bundle_id")
    is_bundle = bool(bundle_id)

    layer = getattr(args, "layer", None)

    if not layer:
        # Legacy mode: use top-level repo/base/impl, output to root
        repo = _extract_yaml_value(case_text, "repo")
        base = _extract_yaml_value(case_text, "base_ref")
        impl = _extract_yaml_value(case_text, "impl_ref")
        _do_diff_for_target(case_id, repo, base, impl, bundle_id, d, None, is_bundle)
    else:
        # Layer mode
        targets = _get_diff_targets(args, case_text)
        for repo, base, impl, bid, output_dir, lname in targets:
            _do_diff_for_target(case_id, repo, base, impl, bid, output_dir, lname, is_bundle)


# ──────────────────────────────────────────
# Bundle attribution helpers
# ──────────────────────────────────────────


def _apply_bundle_attribution(files, symbols, case_id, bundle_id):
    """Apply signal-based attribution for bundle cases."""
    case_signals = BUNDLE_SIGNALS.get(case_id, {}).get("signals", [])
    other_case_ids = [cid for cid in BUNDLE_SIGNALS if cid != case_id]

    for f in files:
        # Normalize monorepo paths for signal matching
        path_raw = f["path"].lower()
        src_idx = path_raw.find("/src/")
        if src_idx >= 0:
            path_lower = path_raw[src_idx + 1:]  # "src/..."
        else:
            path_lower = path_raw
        hits_this = 0
        hits_other = 0
        matched_signals = []

        # Check path against this case's signals
        for sig in case_signals:
            if re.search(sig.lower(), path_lower):
                hits_this += 1
                matched_signals.append(sig)

        # Check path against other cases' signals
        for other_id in other_case_ids:
            other_signals = BUNDLE_SIGNALS.get(other_id, {}).get("signals", [])
            for sig in other_signals:
                if re.search(sig.lower(), path_lower):
                    hits_other += 1

        # Check shared signals
        hits_shared = 0
        for sig in SHARED_SIGNALS:
            if re.search(sig.lower(), path_lower):
                hits_shared += 1

        if hits_this > 0 and hits_other == 0 and hits_shared <= 1:
            conf = "high"
            reason = f"Path matches {len(matched_signals)} exclusive signals"
        elif hits_this > 0 and hits_other > 0:
            conf = "shared_candidate"
            reason = f"Path matches signals from multiple PRDs"
        elif hits_shared > 1 and hits_this == 0:
            conf = "shared"
            reason = f"Path matches shared shift/simba signals only"
        elif hits_this > 0 and hits_shared > 0:
            conf = "medium"
            reason = f"Path matches case signals + shared signals"
        else:
            conf = "needs_review"
            reason = "No clear signal match, manual attribution needed"

        f["attribution"] = {
            "confidence": conf,
            "prd_signals": matched_signals[:5],
            "reason": reason,
        }

    # Apply attribution to symbols too
    for s in symbols:
        path_attr = next(
            (f["attribution"]["confidence"] for f in files if f["path"] == s["path"]),
            "needs_review"
        )
        s["confidence"] = path_attr


def _generate_bundle_summary(bundle_id, files, all_symbols, source_case_id, layer=None):
    """Generate bundle-level summary directory."""
    layer_dir = layer or "bff"
    bundle_dir = BENCHMARKS_DIR / "_bundles" / bundle_id / layer_dir
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Collect all unique files and symbols
    lines = [
        f'schema_version: "1.0"',
        f'bundle_id: {_yaml_str(bundle_id)}',
        f'layer: {_yaml_str(layer_dir)}',
        f'prd_cases:',
    ]
    for cid in BUNDLE_SIGNALS:
        lines.append(f'  - {_yaml_str(cid)}')

    lines.append(f'total_changed_files: {len(files)}')
    lines.append(f'total_symbols: {len(all_symbols)}')
    lines.append(f'changed_files:')

    # Deduplicate files
    seen_paths = set()
    for f in files:
        if f["path"] in seen_paths:
            continue
        seen_paths.add(f["path"])
        attr = f.get("attribution", {})
        lines.append(f'  - path: {_yaml_str(f["path"])}')
        lines.append(f'    change_type: {_yaml_str(f["change_type"])}')
        lines.append(f'    additions: {f["additions"]}')
        lines.append(f'    deletions: {f["deletions"]}')
        lines.append(f'    attribution:')
        lines.append(f'      confidence: {_yaml_str(attr.get("confidence", "needs_review"))}')
        prd_sigs = attr.get("prd_signals", [])
        if prd_sigs:
            lines.append(f'      prd_signals:')
            for sig in prd_sigs:
                lines.append(f'        - {_yaml_str(sig)}')
        else:
            lines.append(f'      prd_signals: []')
        lines.append(f'      reason: {_yaml_str(attr.get("reason", ""))}')

    _write_yaml(bundle_dir / "branch-diff-summary.yaml", lines)
    print(f"Updated bundle summary: {bundle_dir / 'branch-diff-summary.yaml'}")

    # Generate attribution-notes.md
    notes = [
        f"# Bundle Attribution Notes: {bundle_id}",
        f"",
        f"## 概述",
        f"",
        f"分支 `{bundle_id}` ({layer_dir} 层) 对应 **3 个 PRD**：",
        f"",
    ]
    for cid, info in BUNDLE_SIGNALS.items():
        notes.append(f"- `{cid}`: {info['prd_file']}")
    notes += [
        "",
        "## 归因原则",
        "",
        "1. Diff **不能天然归属于某一个 PRD**，因为三个 PRD 共用同一分支。",
        "2. 每个 changed file 通过信号词匹配做初步归因：",
        "   - **独占匹配**（high）：文件路径只命中一个 PRD 的信号词",
        "   - **共享候选**（shared_candidate）：文件路径同时命中多个 PRD 的信号词",
        "   - **共享信号**（shared）：只命中 shift/simba 等通用信号",
        "   - **待审核**（needs_review）：无明确信号匹配，需人工判断",
        "3. 低置信度归因已标记 `needs_review`，**不要强行归因**。",
        "",
        "## 归因统计",
        "",
    ]

    conf_counts = {}
    for f in files:
        c = f.get("attribution", {}).get("confidence", "needs_review")
        conf_counts[c] = conf_counts.get(c, 0) + 1

    notes.append("| 置信度 | 文件数 |")
    notes.append("|--------|--------|")
    for c in ["high", "medium", "shared", "shared_candidate", "needs_review"]:
        notes.append(f"| {c} | {conf_counts.get(c, 0)} |")

    notes += [
        "",
        "## 待审核文件（needs_review）",
        "",
    ]
    needs_review = [f for f in files if f.get("attribution", {}).get("confidence") == "needs_review"]
    if needs_review:
        for f in needs_review:
            notes.append(f"- `{f['path']}` (+{f['additions']}/-{f['deletions']})")
    else:
        notes.append("（无）")

    _write_yaml(bundle_dir / "attribution-notes.md", notes)
    print(f"Updated: {bundle_dir / 'attribution-notes.md'}")


# ──────────────────────────────────────────
# Draft Oracle subcommand
# ──────────────────────────────────────────


def _anchor_sort_priority(anchor):
    """Sort key for anchor truncation: higher = kept first."""
    ct = anchor.get("change_type", "modified")
    if ct == "added":
        type_score = 100
    elif ct in ("route", "component", "config"):
        type_score = 80
    else:
        type_score = 50

    # Diff size proxy: more additions = more important
    adds = anchor.get("additions", 0)
    size_score = min(adds, 50)

    # Has named symbols
    has_syms = 10 if anchor.get("symbols") else 0

    return type_score + size_score + has_syms


def _do_draft_oracle_for_target(case_id, case_text, diff_path, output_dir, layer, is_bundle, include_needs_review=False):
    """Generate oracle-draft.yaml for a single target layer."""
    diff_text = diff_path.read_text(encoding="utf-8")

    # Parse changed files from diff summary
    files = _parse_diff_summary_files(diff_text)
    symbols = _parse_diff_summary_symbols(diff_text)

    # Separate attributable files from needs_review (bundle cases only)
    attributable_confs = {"high", "medium", "shared_candidate", "shared"}
    needs_review_files = []
    attributable_files = []

    for f in files:
        attr_conf = f.get("attribution_confidence", "high")
        if is_bundle and attr_conf not in attributable_confs and not include_needs_review:
            needs_review_files.append(f)
        else:
            attributable_files.append(f)

    # Build code_anchors only from attributable files
    code_anchors = []
    anchor_id = 0

    for f in attributable_files:
        attr_conf = f.get("attribution_confidence", "high")

        # Get symbols for this file
        file_syms = [s for s in symbols if s["path"] == f["path"]]

        anchor_id += 1
        layer_prefix = "CODE-FE" if layer == "frontend" else "CODE-BFF"
        anchor = {
            "id": f"{layer_prefix}-{anchor_id:03d}",
            "path": f["path"],
            "change_type": f.get("change_type", "modified"),
            "attribution_confidence": attr_conf,
            "layer": layer or "bff",
            "additions": f.get("additions", 0),
        }

        if file_syms:
            anchor["symbols"] = [s["symbol"] for s in file_syms[:5]]

        # Determine meaning
        if attr_conf in ("high",):
            anchor["meaning"] = f"High confidence: directly attributable to this PRD"
        elif attr_conf in ("shared_candidate", "shared"):
            anchor["meaning"] = f"Shared: also relevant to other PRDs in bundle"
        elif attr_conf in ("medium",):
            anchor["meaning"] = f"Medium confidence: matches case signals but may overlap"
        else:
            anchor["meaning"] = f"Low confidence: needs manual review"

        code_anchors.append(anchor)

    # Sort by priority and truncate if over MAX_ANCHORS_PER_LAYER
    total_anchors = len(code_anchors)
    truncated_count = 0
    if total_anchors > MAX_ANCHORS_PER_LAYER:
        code_anchors.sort(key=_anchor_sort_priority, reverse=True)
        truncated_count = total_anchors - MAX_ANCHORS_PER_LAYER
        code_anchors = code_anchors[:MAX_ANCHORS_PER_LAYER]

    # Layer-aware forbidden claims
    forbidden_claims = [
        '"不得声称需要新增 Controller，除非 diff 真的新增了 controller"',
        '"不得声称需要新增 Service，除非 diff 真的新增了 service"',
        '"不得把后端职责错归到 BFF"',
        '"不得把非本 PRD 的 bundle 改动当成本 PRD 必做项"',
    ]
    if layer == "frontend":
        forbidden_claims += [
            '"前端 anchor 不得声称后端逻辑变更"',
            '"不得把 CSS/样式调整当成功能变更"',
            '"route 变更必须关联具体页面路径"',
            '"i18n key 变更不得被忽略"',
            '"tracking/埋点变更必须在 oracle 中体现"',
        ]
    elif layer == "bff":
        forbidden_claims += [
            '"BFF anchor 不得声称前端 UI 逻辑变更"',
            '"不得把数据库/后端服务职责错归到 BFF"',
        ]

    # Generate oracle-draft.yaml
    lines = [
        f'schema_version: "1.0"',
        f'case_id: {_yaml_str(case_id)}',
        f'layer: {_yaml_str(layer or "bff")}',
        f'status: "draft"',
        f'oracle_source: "branch_diff"',
        f'',
        f'# Requirements: TODO — 需从 PRD 正文人工/AI 审核补齐',
        f'requirements:',
        f'  - id: "REQ-TBD"',
        f'    title: "TODO: 从 PRD 提取"',
        f'    intent: "TODO"',
        f'    change_type: "TODO"',
        f'    confidence: "TODO"',
        f'',
        f'code_anchors:',
    ]

    for a in code_anchors:
        lines.append(f'  - id: {_yaml_str(a["id"])}')
        lines.append(f'    path: {_yaml_str(a["path"])}')
        lines.append(f'    change_type: {_yaml_str(a["change_type"])}')
        lines.append(f'    attribution_confidence: {_yaml_str(a["attribution_confidence"])}')
        lines.append(f'    layer: {_yaml_str(a["layer"])}')
        if "symbols" in a:
            syms_str = ", ".join(a["symbols"])
            lines.append(f'    symbols: [{syms_str}]')
        lines.append(f'    meaning: {_yaml_str(a["meaning"])}')

    lines += [
        f'',
        f'blockers:',
    ]
    # Add needs_review as blockers (from pre-filtered list for bundle cases)
    if needs_review_files:
        for f in needs_review_files:
            msg = f"Attribution unclear for {f['path']}: needs manual review"
            lines.append(f'  - {_yaml_str(msg)}')
    else:
        lines.append(f'  []')

    lines += [
        f'',
        f'forbidden_claims:',
    ]
    for fc in forbidden_claims:
        lines.append(f'  - {fc}')

    # risk_notes
    lines += [f'', f'risk_notes:']
    risk_notes = []
    if truncated_count > 0:
        risk_notes.append(
            f'"Anchor 截断：共 {total_anchors} 个 anchor，'
            f'保留前 {MAX_ANCHORS_PER_LAYER} 个（按优先级排序），'
            f'截断 {truncated_count} 个"'
        )
    if needs_review_files:
        risk_notes.append(
            f'"{len(needs_review_files)} 个文件归因不明确（needs_review），'
            f'已列入 blockers，未进入 code_anchors"'
        )
    if risk_notes:
        for rn in risk_notes:
            lines.append(f'  - {rn}')
    else:
        lines.append(f'  []')

    out_path = output_dir / "oracle-draft.yaml"
    _write_yaml(out_path, lines)
    print(f"Written: {out_path} ({len(code_anchors)} anchors)")

    # If layer is bff, also update root-level oracle-draft.yaml (compatibility)
    if layer == "bff":
        d = _case_dir(case_id)
        root_path = d / "oracle-draft.yaml"
        root_path.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Updated (root compat): {root_path}")


def cmd_draft_oracle(args):
    """Generate oracle-draft.yaml from branch-diff-summary.yaml."""
    case_id = args.case_id
    d = _case_dir(case_id)

    case_text = (d / "case.yaml").read_text(encoding="utf-8")
    bundle_id = _extract_yaml_value(case_text, "bundle_id")
    is_bundle = bool(bundle_id)

    layer = getattr(args, "layer", None)
    include_nr = getattr(args, "include_needs_review", False)

    if not layer:
        # Legacy mode: use root branch-diff-summary.yaml, output to root
        diff_path = d / "branch-diff-summary.yaml"
        if not diff_path.exists():
            print(f"Error: {diff_path} not found. Run `diff` first.", file=sys.stderr)
            sys.exit(1)
        _do_draft_oracle_for_target(case_id, case_text, diff_path, d, None, is_bundle, include_needs_review=include_nr)
    else:
        # Layer mode
        diff_path = d / "targets" / layer / "branch-diff-summary.yaml"
        if not diff_path.exists():
            print(f"Error: {diff_path} not found. Run `diff --layer {layer}` first.",
                  file=sys.stderr)
            sys.exit(1)
        output_dir = d / "targets" / layer
        _do_draft_oracle_for_target(case_id, case_text, diff_path, output_dir, layer, is_bundle, include_needs_review=include_nr)


# ──────────────────────────────────────────
# Merge Oracle subcommand
# ──────────────────────────────────────────


def cmd_merge_oracle(args):
    """Merge multi-layer oracle drafts into unified oracle."""
    case_id = args.case_id
    d = _case_dir(case_id)

    case_text = (d / "case.yaml").read_text(encoding="utf-8")

    # Collect all layer oracle drafts
    layers_oracles = {}

    # Check targets directory for layer-specific oracles
    targets_dir = d / "targets"
    if targets_dir.exists():
        for layer_dir in sorted(targets_dir.iterdir()):
            if not layer_dir.is_dir():
                continue
            oracle_path = layer_dir / "oracle-draft.yaml"
            if oracle_path.exists():
                layers_oracles[layer_dir.name] = oracle_path

    # Also check root for legacy bff oracle
    root_oracle = d / "oracle-draft.yaml"
    if root_oracle.exists() and "bff" not in layers_oracles:
        layers_oracles["bff"] = root_oracle

    if not layers_oracles:
        print("Error: No oracle drafts found. Run `draft-oracle` first.", file=sys.stderr)
        sys.exit(1)

    print(f"  Found oracle drafts for layers: {list(layers_oracles.keys())}")

    # Parse all oracles
    merged_anchors = []
    merged_forbidden = []
    merged_forbidden_set = set()
    all_risk_notes = []

    for layer_name, oracle_path in sorted(layers_oracles.items()):
        oracle_text = oracle_path.read_text(encoding="utf-8")
        anchors = _parse_oracle_anchors(oracle_text)
        forbidden = _parse_oracle_forbidden_claims(oracle_text)
        risk_notes = _parse_oracle_risk_notes(oracle_text)

        for a in anchors:
            # Ensure layer field
            a["layer"] = layer_name
            merged_anchors.append(a)

        for fc in forbidden:
            if fc not in merged_forbidden_set:
                merged_forbidden_set.add(fc)
                merged_forbidden.append(fc)

        for rn in risk_notes:
            all_risk_notes.append(f"[{layer_name}] {rn}")

    # Write merged oracle
    lines = [
        f'schema_version: "1.1"',
        f'case_id: {_yaml_str(case_id)}',
        f'status: "draft"',
        f'oracle_source: "merged_branch_diff"',
        f'layers:',
    ]
    for layer_name in sorted(layers_oracles.keys()):
        lines.append(f'  - {_yaml_str(layer_name)}')

    lines += [
        f'',
        f'# Requirements: TODO — 需从 PRD 正文人工/AI 审核补齐',
        f'requirements:',
        f'  - id: "REQ-TBD"',
        f'    title: "TODO: 从 PRD 提取"',
        f'    intent: "TODO"',
        f'    change_type: "TODO"',
        f'    confidence: "TODO"',
        f'',
        f'code_anchors:',
    ]

    for a in merged_anchors:
        lines.append(f'  - id: {_yaml_str(a["id"])}')
        lines.append(f'    path: {_yaml_str(a["path"])}')
        lines.append(f'    change_type: {_yaml_str(a["change_type"])}')
        lines.append(f'    attribution_confidence: {_yaml_str(a.get("attribution_confidence", "high"))}')
        lines.append(f'    layer: {_yaml_str(a["layer"])}')
        if "symbols" in a:
            syms_str = ", ".join(a["symbols"])
            lines.append(f'    symbols: [{syms_str}]')
        if "meaning" in a:
            lines.append(f'    meaning: {_yaml_str(a["meaning"])}')

    lines += [
        f'',
        f'forbidden_claims:',
    ]
    for fc in merged_forbidden:
        lines.append(f'  - {_yaml_str(fc)}')

    lines += [
        f'',
        f'risk_notes:',
    ]
    if all_risk_notes:
        for rn in all_risk_notes:
            lines.append(f'  - {_yaml_str(rn)}')
    else:
        lines.append(f'  []')

    out_path = d / "oracle-draft.multi.yaml"
    _write_yaml(out_path, lines)
    print(f"Written: {out_path} ({len(merged_anchors)} anchors from {len(layers_oracles)} layers)")


def _parse_oracle_anchors(text):
    """Parse code_anchors from oracle-draft.yaml text."""
    anchors = []
    current = {}
    in_anchors = False

    for line in text.split("\n"):
        stripped = line.strip()

        if stripped == "code_anchors:":
            in_anchors = True
            continue

        if not in_anchors:
            continue

        # End of code_anchors section
        if line and not line[0].isspace() and stripped and not stripped.startswith("#"):
            if current:
                anchors.append(current)
                current = {}
            in_anchors = False
            continue

        if stripped.startswith("- id:"):
            if current:
                anchors.append(current)
            current = {"id": _unquote(stripped.split(":", 1)[1].strip())}
        elif current:
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k == "symbols":
                    # Parse [sym1, sym2, ...]
                    v_inner = v.strip("[]")
                    current["symbols"] = [s.strip().strip("'\"") for s in v_inner.split(",") if s.strip()]
                elif k in ("additions", "deletions"):
                    try:
                        current[k] = int(v)
                    except ValueError:
                        current[k] = v
                else:
                    current[k] = _unquote(v)

    if current:
        anchors.append(current)
    return anchors


def _parse_oracle_forbidden_claims(text):
    """Parse forbidden_claims list from oracle-draft.yaml text."""
    claims = []
    in_claims = False

    for line in text.split("\n"):
        stripped = line.strip()

        if stripped == "forbidden_claims:":
            in_claims = True
            continue

        if not in_claims:
            continue

        if line and not line[0].isspace() and stripped:
            in_claims = False
            continue

        if stripped.startswith("- "):
            claim = stripped[2:].strip()
            claim = _unquote(claim)
            if claim and claim != "[]":
                claims.append(claim)

    return claims


def _parse_oracle_risk_notes(text):
    """Parse risk_notes from oracle-draft.yaml text."""
    notes = []
    in_notes = False

    for line in text.split("\n"):
        stripped = line.strip()

        if stripped == "risk_notes:":
            in_notes = True
            continue

        if not in_notes:
            continue

        if line and not line[0].isspace() and stripped:
            in_notes = False
            continue

        if stripped.startswith("- "):
            note = stripped[2:].strip()
            note = _unquote(note)
            if note and note != "[]":
                notes.append(note)

    return notes


# ──────────────────────────────────────────
# Diff summary parsing helpers
# ──────────────────────────────────────────


def _parse_diff_summary_files(text):
    """Parse changed files from branch-diff-summary.yaml."""
    files = []
    current = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- path:"):
            if current:
                files.append(current)
            current = {"path": _unquote(stripped.split(":", 1)[1].strip())}
        elif current:
            if stripped.startswith("change_type:"):
                current["change_type"] = _unquote(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("additions:"):
                try:
                    current["additions"] = int(stripped.split(":")[1].strip())
                except ValueError:
                    current["additions"] = 0
            elif stripped.startswith("deletions:"):
                try:
                    current["deletions"] = int(stripped.split(":")[1].strip())
                except ValueError:
                    current["deletions"] = 0
            elif stripped.startswith("confidence:"):
                current["attribution_confidence"] = _unquote(stripped.split(":", 1)[1].strip())
    if current:
        files.append(current)
    return files


def _parse_diff_summary_symbols(text):
    """Parse symbols from branch-diff-summary.yaml."""
    symbols = []
    current = {}
    in_symbols = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == "symbols:":
            in_symbols = True
            continue
        if not in_symbols:
            continue
        if stripped.startswith("- path:"):
            if current:
                symbols.append(current)
            current = {"path": _unquote(stripped.split(":", 1)[1].strip())}
        elif current:
            if stripped.startswith("symbol:"):
                current["symbol"] = _unquote(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("kind:"):
                current["kind"] = _unquote(stripped.split(":", 1)[1].strip())
    if current:
        symbols.append(current)
    return symbols


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description="Branch-backed Benchmark Case Manager")
    sub = ap.add_subparsers(dest="command")

    # create
    p_create = sub.add_parser("create", help="Create case directory")
    p_create.add_argument("--case-id", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--prd", required=True)
    p_create.add_argument("--repo", required=True)
    p_create.add_argument("--base", required=True)
    p_create.add_argument("--impl", required=True)
    p_create.add_argument("--bundle", default="")

    # add-target
    p_add_target = sub.add_parser("add-target", help="Add multi-repo target to case")
    p_add_target.add_argument("--case-id", required=True)
    p_add_target.add_argument("--layer", required=True,
                              help="Target layer name (e.g. frontend, bff)")
    p_add_target.add_argument("--repo", required=True,
                              help="Repository path for this target")
    p_add_target.add_argument("--base", required=True,
                              help="Base ref (e.g. master)")
    p_add_target.add_argument("--impl", required=True,
                              help="Implementation branch name")
    p_add_target.add_argument("--bundle", default="",
                              help="Optional bundle ID")

    # diff
    p_diff = sub.add_parser("diff", help="Generate diff summary")
    p_diff.add_argument("--case-id", required=True)
    p_diff.add_argument("--layer", default=None,
                        help="Target layer (e.g. frontend, bff). Omit for legacy behavior.")

    # draft-oracle
    p_oracle = sub.add_parser("draft-oracle", help="Generate oracle draft")
    p_oracle.add_argument("--case-id", required=True)
    p_oracle.add_argument("--layer", default=None,
                          help="Target layer (e.g. frontend, bff). Omit for legacy behavior.")
    p_oracle.add_argument("--include-needs-review", action="store_true", default=False,
                          help="Include needs_review files in code_anchors (default: risk_notes only for bundle cases)")

    # merge-oracle
    p_merge = sub.add_parser("merge-oracle", help="Merge multi-layer oracle drafts")
    p_merge.add_argument("--case-id", required=True)

    args = ap.parse_args()
    if args.command == "create":
        cmd_create(args)
    elif args.command == "add-target":
        cmd_add_target(args)
    elif args.command == "diff":
        cmd_diff(args)
    elif args.command == "draft-oracle":
        cmd_draft_oracle(args)
    elif args.command == "merge-oracle":
        cmd_merge_oracle(args)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
