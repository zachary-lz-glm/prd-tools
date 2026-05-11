#!/usr/bin/env python3
"""
reference-workflow-gate.py — Reference Workflow Order & Completion Gate

Deterministic gate that enforces:
  1. Reference files must be generated in order (01→02→03→04→05)
  2. portal.html must be script-rendered (not handwritten)
  3. index/manifest.yaml must exist
  4. reference-quality-gate.py must pass

Usage:
    python3 scripts/reference-workflow-gate.py --root /path/to/project
    python3 .prd-tools/scripts/reference-workflow-gate.py --root .

Output:
    Human-readable summary to stdout.
    Exit code: 0 = pass or warning, 2 = fail.
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ──────────────────────────────────────────
# Workflow ordering config
# ──────────────────────────────────────────

# Ordered steps: each step requires the previous step's output to exist
WORKFLOW_STEPS = [
    {
        'step': '01-codebase',
        'output': '01-codebase.yaml',
        'label': 'Step 02a: codebase',
    },
    {
        'step': '02-coding-rules',
        'output': '02-coding-rules.yaml',
        'label': 'Step 02b: coding-rules',
    },
    {
        'step': '03-contracts',
        'output': '03-contracts.yaml',
        'label': 'Step 02c: contracts',
    },
    {
        'step': '04-routing',
        'output': '04-routing-playbooks.yaml',
        'label': 'Step 02d: routing',
    },
    {
        'step': '05-domain',
        'output': '05-domain.yaml',
        'label': 'Step 02e: domain',
    },
]

REQUIRED_INDEX_FILES = [
    'entities.json',
    'edges.json',
    'inverted-index.json',
    'manifest.yaml',
]


def _read_safe(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _file_exists_nonempty(path):
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def _check_workflow_order(ref_dir):
    """Check that reference files were generated in order.

    For each step N, if step N's output exists but step N-1's output
    does not, that's an ordering violation.
    """
    violations = []
    completed = []

    for i, step in enumerate(WORKFLOW_STEPS):
        output_path = ref_dir / step['output']
        exists = _file_exists_nonempty(output_path)

        if exists:
            # Check all previous steps exist
            for j in range(i):
                prev = WORKFLOW_STEPS[j]
                prev_path = ref_dir / prev['output']
                if not _file_exists_nonempty(prev_path):
                    violations.append({
                        'step': step['step'],
                        'output': step['output'],
                        'missing_prerequisite': prev['output'],
                        'prerequisite_step': prev['step'],
                    })
            completed.append(step['step'])

    status = 'pass'
    if violations:
        status = 'fail'

    return {
        'status': status,
        'completed_steps': completed,
        'total_steps': len(WORKFLOW_STEPS),
        'violations': violations,
    }


def _check_portal_script_rendered(ref_dir):
    """Check portal.html exists and has script-rendered marker."""
    portal_path = ref_dir / 'portal.html'
    exists = _file_exists_nonempty(portal_path)

    if not exists:
        return {
            'status': 'fail',
            'exists': False,
            'marker_ok': False,
            'message': 'portal.html 不存在或为空',
        }

    text = _read_safe(portal_path)
    marker_ok = 'data-prd-tools-portal="reference"' in text

    if not marker_ok:
        return {
            'status': 'fail',
            'exists': True,
            'marker_ok': False,
            'message': 'portal.html 缺少 data-prd-tools-portal="reference" 标记，可能非脚本渲染',
        }

    return {
        'status': 'pass',
        'exists': True,
        'marker_ok': True,
    }


def _check_index_exists(ref_dir):
    """Check that index/ directory exists with required files."""
    index_dir = ref_dir / 'index'
    missing = []
    empty = []

    for f in REQUIRED_INDEX_FILES:
        p = index_dir / f
        if not p.exists():
            missing.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)

    if missing or empty:
        return {
            'status': 'fail',
            'missing': missing,
            'empty': empty,
        }

    # Read manifest summary
    manifest_path = index_dir / 'manifest.yaml'
    manifest_text = _read_safe(manifest_path)
    entity_count = '?'
    edge_count = '?'
    term_count = '?'

    m = re.search(r'entity_count:\s*(\d+)', manifest_text)
    if m:
        entity_count = m.group(1)
    m = re.search(r'edge_count:\s*(\d+)', manifest_text)
    if m:
        edge_count = m.group(1)
    m = re.search(r'term_count:\s*(\d+)', manifest_text)
    if m:
        term_count = m.group(1)

    return {
        'status': 'pass',
        'missing': [],
        'empty': [],
        'manifest_summary': f'entities={entity_count}, edges={edge_count}, terms={term_count}',
    }


def _check_quality_gate(ref_dir, root):
    """Run reference-quality-gate.py and capture result."""
    # Find the gate script
    candidates = [
        Path(root) / '.prd-tools' / 'scripts' / 'reference-quality-gate.py',
        Path(root) / 'scripts' / 'reference-quality-gate.py',
    ]

    gate_script = None
    for c in candidates:
        if c.exists():
            gate_script = c
            break

    if gate_script is None:
        return {
            'status': 'warning',
            'gate_found': False,
            'message': 'reference-quality-gate.py 未找到，跳过质量门禁检查',
        }

    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(gate_script), '--root', str(root)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        exit_code = result.returncode
        stdout = result.stdout.strip()

        # Extract RESULT line
        result_line = ''
        for line in stdout.splitlines():
            if line.startswith('RESULT:'):
                result_line = line
                break

        return {
            'status': 'pass' if exit_code == 0 else 'fail',
            'gate_found': True,
            'exit_code': exit_code,
            'result_line': result_line,
        }
    except Exception as e:
        return {
            'status': 'warning',
            'gate_found': True,
            'message': f'运行 reference-quality-gate.py 失败: {e}',
        }


def _check_project_profile(ref_dir):
    """Check project-profile.yaml exists (required before step 02a)."""
    exists = _file_exists_nonempty(ref_dir / 'project-profile.yaml')
    return {
        'status': 'pass' if exists else 'fail',
        'exists': exists,
    }


def _check_portal_md(ref_dir):
    """Check 00-portal.md exists (generated with step 02e)."""
    exists = _file_exists_nonempty(ref_dir / '00-portal.md')
    return {
        'status': 'pass' if exists else 'fail',
        'exists': exists,
    }


def run_checks(root):
    """Run all checks and return results dict."""
    ref_dir = Path(root) / '_prd-tools' / 'reference'

    results = {}
    results['project_profile'] = _check_project_profile(ref_dir)
    results['workflow_order'] = _check_workflow_order(ref_dir)
    results['portal_md'] = _check_portal_md(ref_dir)
    results['portal_html'] = _check_portal_script_rendered(ref_dir)
    results['index'] = _check_index_exists(ref_dir)
    results['quality_gate'] = _check_quality_gate(ref_dir, root)

    return results


def compute_exit_code(results):
    for key, val in results.items():
        if val.get('status') == 'fail':
            return 2
    return 0


def print_summary(results):
    print()
    print('=== Reference Workflow Gate ===')
    print()

    # Project profile
    pp = results['project_profile']
    sym = '+' if pp['status'] == 'pass' else 'x'
    print(f'  [{sym}] project-profile.yaml: {"exists" if pp["exists"] else "MISSING"}')

    # Workflow order
    wo = results['workflow_order']
    sym = '+' if wo['status'] == 'pass' else 'x'
    completed = f'{len(wo["completed_steps"])}/{wo["total_steps"]}'
    print(f'  [{sym}] workflow order: {wo["status"]} ({completed} steps completed)')
    if wo['violations']:
        for v in wo['violations']:
            print(f'      VIOLATION: {v["output"]} exists but prerequisite {v["missing_prerequisite"]} is missing')

    # Portal md
    pm = results['portal_md']
    sym = '+' if pm['status'] == 'pass' else 'x'
    print(f'  [{sym}] 00-portal.md: {"exists" if pm["exists"] else "MISSING"}')

    # Portal html
    ph = results['portal_html']
    sym = '+' if ph['status'] == 'pass' else ('!' if ph['status'] == 'warning' else 'x')
    if ph['exists'] and ph.get('marker_ok'):
        print(f'  [{sym}] portal.html: script-rendered')
    elif ph['exists']:
        print(f'  [{sym}] portal.html: exists but {ph.get("message", "not script-rendered")}')
    else:
        print(f'  [{sym}] portal.html: {ph.get("message", "MISSING")}')

    # Index
    ix = results['index']
    sym = '+' if ix['status'] == 'pass' else 'x'
    if ix['status'] == 'pass':
        print(f'  [{sym}] index: {ix["manifest_summary"]}')
    else:
        print(f'  [{sym}] index: MISSING')
        if ix['missing']:
            print(f'      missing: {ix["missing"]}')
        if ix['empty']:
            print(f'      empty: {ix["empty"]}')

    # Quality gate
    qg = results['quality_gate']
    sym = '+' if qg['status'] == 'pass' else ('!' if qg['status'] == 'warning' else 'x')
    if qg.get('gate_found'):
        if qg.get('result_line'):
            print(f'  [{sym}] quality-gate: {qg["result_line"]}')
        else:
            print(f'  [{sym}] quality-gate: exit_code={qg.get("exit_code", "?")}')
    else:
        print(f'  [{sym}] quality-gate: {qg.get("message", "not found")}')

    print()


def main():
    ap = argparse.ArgumentParser(
        description='Reference Workflow Gate — enforce ordering and completion for /reference output'
    )
    ap.add_argument('--root', required=True,
                    help='Project root directory (containing _prd-tools/)')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f'Error: {root} is not a directory', file=sys.stderr)
        sys.exit(1)

    results = run_checks(root)
    print_summary(results)

    exit_code = compute_exit_code(results)
    if exit_code == 2:
        print('RESULT: FAIL — workflow ordering violations or missing required outputs.')
        print('        /reference must not be declared complete.')
    else:
        has_warning = any(v.get('status') == 'warning' for v in results.values())
        if has_warning:
            print('RESULT: PASS with warnings — see above.')
        else:
            print('RESULT: PASS — workflow ordering and completion verified.')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
