#!/usr/bin/env python3
"""
reference-quality-gate.py — Reference Completion Gate

Deterministic quality gate that checks whether /reference output
meets minimum completion standards.

Usage:
    python3 scripts/reference-quality-gate.py --root /path/to/project
    python3 .prd-tools/scripts/reference-quality-gate.py --root .

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
# Required files config
# ──────────────────────────────────────────

REQUIRED_REF_FILES = [
    '00-portal.md',
    'project-profile.yaml',
    '01-codebase.yaml',
    '02-coding-rules.yaml',
    '03-contracts.yaml',
    '04-routing-playbooks.yaml',
    '05-domain.yaml',
]

REQUIRED_INDEX_FILES = [
    'entities.json',
    'edges.json',
    'inverted-index.json',
    'manifest.yaml',
]

REQUIRED_OTHER = [
    'portal.html',
]

# YAML fields that should exist in key reference files
SCHEMA_VERSION_FIELDS = {
    'project-profile.yaml': 'schema_version',
    '01-codebase.yaml': 'schema_version',
    '02-coding-rules.yaml': 'schema_version',
    '03-contracts.yaml': 'schema_version',
    '04-routing-playbooks.yaml': 'schema_version',
    '05-domain.yaml': 'schema_version',
}

# Natural language field names to check for English ratio
NL_FIELD_PATTERNS = [
    re.compile(r'(?:summary|description|responsibility|rationale|risk|notes|warnings?):\s*["\']?(.+)', re.I),
]


def _read_safe(path):
    """Read file, return text or empty string."""
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _file_exists_nonempty(path):
    """Check file exists and is non-empty."""
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def _check_yaml_readable(path):
    """Basic YAML readability: no obvious parse-breaking issues."""
    text = _read_safe(path)
    if not text.strip():
        return False
    # Check for obvious binary content
    if '\x00' in text:
        return False
    return True


def _check_schema_version(path, field_name):
    """Check if a YAML file contains a schema_version field."""
    text = _read_safe(path)
    if not text.strip():
        return False
    pattern = re.compile(rf'^{re.escape(field_name)}:\s*.+', re.M)
    return bool(pattern.search(text))


def _english_ratio(text):
    """Estimate English character ratio in natural language text."""
    if not text.strip():
        return 0.0
    # Extract values from NL fields
    nl_texts = []
    for pat in NL_FIELD_PATTERNS:
        for m in pat.finditer(text):
            nl_texts.append(m.group(1))
    if not nl_texts:
        # Fallback: sample the whole text
        sample = text[:5000]
    else:
        sample = ' '.join(nl_texts[:200])

    # Count ASCII letters vs CJK characters
    ascii_letters = sum(1 for c in sample if c.isascii() and c.isalpha())
    cjk_chars = sum(1 for c in sample if '\u4e00' <= c <= '\u9fff')
    total = ascii_letters + cjk_chars
    if total == 0:
        return 0.0
    return ascii_letters / total


def run_checks(root):
    """Run all checks and return results dict."""
    ref_dir = Path(root) / '_prd-tools' / 'reference'
    index_dir = ref_dir / 'index'

    results = {
        'required_files': {'status': 'pass', 'missing': [], 'empty': []},
        'index_files': {'status': 'pass', 'missing': [], 'empty': []},
        'portal_html': {'status': 'pass', 'exists': False},
        'yaml_readable': {'status': 'pass', 'failed': []},
        'schema_version': {'status': 'pass', 'missing': []},
        'english_ratio': {'status': 'pass', 'ratio': 0.0, 'warning': False},
    }

    # 1. Required reference files
    for f in REQUIRED_REF_FILES:
        p = ref_dir / f
        if not p.exists():
            results['required_files']['missing'].append(f)
        elif p.stat().st_size == 0:
            results['required_files']['empty'].append(f)
    if results['required_files']['missing'] or results['required_files']['empty']:
        results['required_files']['status'] = 'fail'

    # 2. Index files
    for f in REQUIRED_INDEX_FILES:
        p = index_dir / f
        if not p.exists():
            results['index_files']['missing'].append(f)
        elif p.stat().st_size == 0:
            results['index_files']['empty'].append(f)
    if results['index_files']['missing'] or results['index_files']['empty']:
        results['index_files']['status'] = 'fail'

    # 3. portal.html
    portal_path = ref_dir / 'portal.html'
    results['portal_html']['exists'] = _file_exists_nonempty(portal_path)
    if not results['portal_html']['exists']:
        results['portal_html']['status'] = 'fail'

    # 4. YAML readability
    for f in REQUIRED_REF_FILES:
        if f.endswith('.yaml'):
            p = ref_dir / f
            if p.exists() and not _check_yaml_readable(p):
                results['yaml_readable']['failed'].append(f)
    if results['yaml_readable']['failed']:
        results['yaml_readable']['status'] = 'warning'

    # 5. Schema version
    for f, field in SCHEMA_VERSION_FIELDS.items():
        p = ref_dir / f
        if p.exists() and not _check_schema_version(p, field):
            results['schema_version']['missing'].append(f)
    if results['schema_version']['missing']:
        results['schema_version']['status'] = 'warning'

    # 6. English ratio in natural language
    # Check the main YAML files for NL content
    all_nl_text = ''
    for f in REQUIRED_REF_FILES:
        if f.endswith('.yaml'):
            all_nl_text += _read_safe(ref_dir / f) + '\n'
    all_nl_text += _read_safe(ref_dir / '00-portal.md') + '\n'

    ratio = _english_ratio(all_nl_text)
    results['english_ratio']['ratio'] = round(ratio, 3)
    if ratio > 0.6:
        results['english_ratio']['warning'] = True
        results['english_ratio']['status'] = 'warning'

    return results


def compute_exit_code(results):
    """Compute exit code from results."""
    # Any 'fail' status -> exit 2
    for key, val in results.items():
        if val.get('status') == 'fail':
            return 2
    return 0


def print_summary(results):
    """Print human-readable summary."""
    print()
    print('=== Reference Quality Gate ===')
    print()

    # Required files
    rf = results['required_files']
    sym = '+' if rf['status'] == 'pass' else ('!' if rf['status'] == 'warning' else 'x')
    print(f'  [{sym}] required files: {rf["status"]}')
    if rf['missing']:
        print(f'      missing: {rf["missing"]}')
    if rf['empty']:
        print(f'      empty: {rf["empty"]}')

    # Index files
    ix = results['index_files']
    sym = '+' if ix['status'] == 'pass' else ('!' if ix['status'] == 'warning' else 'x')
    print(f'  [{sym}] index files: {ix["status"]}')
    if ix['missing']:
        print(f'      missing: {ix["missing"]}')
    if ix['empty']:
        print(f'      empty: {ix["empty"]}')

    # portal.html
    ph = results['portal_html']
    sym = '+' if ph['status'] == 'pass' else 'x'
    print(f'  [{sym}] portal.html: {"exists" if ph["exists"] else "MISSING"}')

    # YAML readable
    yr = results['yaml_readable']
    sym = '+' if yr['status'] == 'pass' else '!'
    print(f'  [{sym}] yaml readable: {yr["status"]}')
    if yr['failed']:
        print(f'      failed: {yr["failed"]}')

    # Schema version
    sv = results['schema_version']
    sym = '+' if sv['status'] == 'pass' else '!'
    print(f'  [{sym}] schema_version: {sv["status"]}')
    if sv['missing']:
        print(f'      missing in: {sv["missing"]}')

    # English ratio
    er = results['english_ratio']
    sym = '+' if er['status'] == 'pass' else '!'
    print(f'  [{sym}] language check: {er["status"]} (english ratio: {er["ratio"]})')
    if er['warning']:
        print(f'      WARNING: natural language is predominantly English (>60%), expected Chinese')

    print()


def main():
    ap = argparse.ArgumentParser(
        description='Reference Completion Gate — deterministic checks for /reference output'
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
        print('RESULT: FAIL — missing required files, /reference not complete.')
    else:
        has_warning = any(v.get('status') == 'warning' for v in results.values())
        if has_warning:
            print('RESULT: PASS with warnings — see above.')
        else:
            print('RESULT: PASS — all checks satisfied.')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()