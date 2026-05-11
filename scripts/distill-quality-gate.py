#!/usr/bin/env python3
"""
distill-quality-gate.py — Distill Completion Gate

Deterministic quality gate that checks whether /prd-distill output
meets minimum completion standards for the AI-friendly pipeline.

Usage:
    python3 scripts/distill-quality-gate.py \
      --distill-dir _prd-tools/distill/<slug> --repo-root .
    python3 .prd-tools/scripts/distill-quality-gate.py \
      --distill-dir _prd-tools/distill/<slug> --repo-root .

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

REQUIRED_DISTILL_FILES = {
    'critical': [
        '_ingest/document.md',
        'spec/ai-friendly-prd.md',
        'report.md',
        'plan.md',
    ],
    'important': [
        'context/prd-quality-report.yaml',
        'context/requirement-ir.yaml',
        'context/layer-impact.yaml',
        'context/contract-delta.yaml',
        'context/graph-context.md',
        'context/readiness-report.yaml',
        'context/final-quality-gate.yaml',
    ],
}

# AI-friendly PRD section headers (13 sections)
AFPRD_SECTIONS = [
    'Overview',
    'Problem Statement',
    'Target Users',
    'Goals & Success Metrics',
    'User Stories',
    'Functional Requirements',
    'Non-Functional Requirements',
    'Technical Considerations',
    'UI/UX Requirements',
    'Out of Scope',
    'Timeline & Milestones',
    'Risks & Mitigations',
    'Open Questions',
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


def _check_required_files(base):
    """Check required distill files exist and non-empty."""
    missing_critical = []
    missing_important = []
    empty = []

    for f in REQUIRED_DISTILL_FILES['critical']:
        p = base / f
        if not p.exists():
            missing_critical.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)

    for f in REQUIRED_DISTILL_FILES['important']:
        p = base / f
        if not p.exists():
            missing_important.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)

    status = 'pass'
    if missing_critical:
        status = 'fail'
    elif missing_important or empty:
        status = 'warning'

    return {
        'status': status,
        'missing_critical': missing_critical,
        'missing_important': missing_important,
        'empty': empty,
    }


def _check_afprd_sections(base):
    """Check ai-friendly-prd.md contains 13 sections."""
    text = _read_safe(base / 'spec' / 'ai-friendly-prd.md')
    if not text.strip():
        return {'status': 'fail', 'found': 0, 'missing': AFPRD_SECTIONS}

    found = []
    missing = []
    for section in AFPRD_SECTIONS:
        # Match section headers like "## 1. Overview" or "## Overview"
        pattern = re.compile(
            rf'^##\s+(?:\d+\.?\s+)?{re.escape(section)}',
            re.I | re.M,
        )
        if pattern.search(text):
            found.append(section)
        else:
            missing.append(section)

    status = 'pass'
    if len(found) < 8:
        status = 'fail'
    elif len(missing) > 3:
        status = 'warning'

    return {
        'status': status,
        'found': len(found),
        'total': len(AFPRD_SECTIONS),
        'missing': missing,
    }


def _check_prd_quality_report(base):
    """Check prd-quality-report.yaml has status and score."""
    text = _read_safe(base / 'context' / 'prd-quality-report.yaml')
    if not text.strip():
        return {'status': 'fail', 'has_status': False, 'has_score': False}

    has_status = bool(re.search(r'^status:\s*', text, re.M))
    has_score = bool(re.search(r'^score:\s*\d+', text, re.M))

    status = 'pass' if (has_status and has_score) else 'fail'
    return {
        'status': status,
        'has_status': has_status,
        'has_score': has_score,
    }


def _check_requirement_ir(base):
    """Check requirement-ir.yaml has ai_prd_req_id and planning eligibility."""
    text = _read_safe(base / 'context' / 'requirement-ir.yaml')
    if not text.strip():
        return {'status': 'fail', 'has_ai_prd_req_id': False, 'has_planning': False}

    has_ai_prd_req_id = bool(re.search(r'ai_prd_req_id:', text))
    has_planning = bool(re.search(r'planning:', text))
    has_eligibility = bool(re.search(r'eligibility:', text))

    status = 'pass' if (has_ai_prd_req_id and has_planning and has_eligibility) else 'fail'
    return {
        'status': status,
        'has_ai_prd_req_id': has_ai_prd_req_id,
        'has_planning': has_planning,
        'has_eligibility': has_eligibility,
    }


def _check_layer_impact(base):
    """Check layer-impact.yaml has code_anchors or fallback."""
    text = _read_safe(base / 'context' / 'layer-impact.yaml')
    if not text.strip():
        return {'status': 'fail', 'has_code_anchors': False, 'has_fallback': False}

    has_code_anchors = bool(re.search(r'code_anchors:', text))
    has_fallback = bool(re.search(r'fallback:', text)) or bool(re.search(r'fallback_reason:', text))

    status = 'pass' if (has_code_anchors or has_fallback) else 'warning'
    return {
        'status': status,
        'has_code_anchors': has_code_anchors,
        'has_fallback': has_fallback,
    }


def _check_index_bridge(base, repo_root):
    """Check if reference/index exists, then query-plan and context-pack must exist."""
    index_dir = Path(repo_root) / '_prd-tools' / 'reference' / 'index'
    index_exists = (index_dir / 'entities.json').exists()

    if not index_exists:
        return {
            'status': 'pass',
            'index_exists': False,
            'note': 'reference/index not found, skipping bridge check',
        }

    qp_exists = _file_exists_nonempty(base / 'context' / 'query-plan.yaml')
    cp_exists = _file_exists_nonempty(base / 'context' / 'context-pack.md')

    status = 'pass' if (qp_exists and cp_exists) else 'fail'
    return {
        'status': status,
        'index_exists': True,
        'query_plan_exists': qp_exists,
        'context_pack_exists': cp_exists,
    }


def _check_final_quality_gate(base):
    """Check final-quality-gate.yaml exists."""
    exists = _file_exists_nonempty(base / 'context' / 'final-quality-gate.yaml')
    return {
        'status': 'pass' if exists else 'fail',
        'exists': exists,
    }


def _check_report_quality(base):
    """Check report.md contains PRD quality summary."""
    text = _read_safe(base / 'report.md')
    if not text.strip():
        return {'status': 'fail', 'has_quality_summary': False}

    # Look for PRD quality section references
    has_quality = bool(re.search(
        r'(?:PRD\s*质量|质量摘要|prd.quality|quality.report|AI-friendly\s*PRD\s*质量)',
        text, re.I,
    ))

    return {
        'status': 'pass' if has_quality else 'warning',
        'has_quality_summary': has_quality,
    }


def _check_plan_missing_confirmation(base):
    """Check plan.md doesn't treat missing_confirmation as confirmed tasks."""
    text = _read_safe(base / 'plan.md')
    if not text.strip():
        return {'status': 'fail', 'suspicious_count': 0}

    # Find checklist items that contain missing_confirmation-like language
    # but are written as confirmed implementation tasks
    suspicious = 0
    # Pattern: checklist item with "missing_confirmation" or "待确认" in context
    # but formatted as a definitive "- [ ]" task without caveats
    checklist_lines = re.findall(r'^-\s+\[[ x]\]\s+.+', text, re.M)
    for line in checklist_lines:
        # If a checklist item explicitly says "missing_confirmation" or "待确认"
        # but doesn't have "假设" or "前提" or "需确认" caveat, it's suspicious
        if re.search(r'missing_confirmation|待确认|needs_confirmation', line, re.I):
            if not re.search(r'假设|前提|需确认|assumption|pending|blocked', line, re.I):
                suspicious += 1

    status = 'pass' if suspicious == 0 else 'warning'
    return {
        'status': status,
        'suspicious_count': suspicious,
    }



def _check_portal_html(base):
    """Check portal.html exists and has script-rendered marker."""
    portal_path = base / 'portal.html'
    exists = _file_exists_nonempty(portal_path)
    marker_ok = False
    message = ''
    if exists:
        text = _read_safe(portal_path)
        if 'data-prd-tools-portal="distill"' in text:
            marker_ok = True
        else:
            message = 'portal.html 缺少 data-prd-tools-portal="distill" 标记，可能非脚本渲染'
    else:
        message = 'portal.html 不存在或为空'
    status = 'pass' if (exists and marker_ok) else ('warning' if exists else 'fail')
    return {
        'status': status,
        'exists': exists,
        'marker_ok': marker_ok,
        'message': message,
    }

def run_checks(distill_dir, repo_root):
    """Run all checks and return results dict."""
    base = Path(distill_dir).resolve()

    results = {}
    results['required_files'] = _check_required_files(base)
    results['afprd_sections'] = _check_afprd_sections(base)
    results['prd_quality_report'] = _check_prd_quality_report(base)
    results['requirement_ir'] = _check_requirement_ir(base)
    results['layer_impact'] = _check_layer_impact(base)
    results['index_bridge'] = _check_index_bridge(base, repo_root)
    results['final_quality_gate'] = _check_final_quality_gate(base)
    results['report_quality'] = _check_report_quality(base)
    results['plan_missing_confirmation'] = _check_plan_missing_confirmation(base)
    results['portal_html'] = _check_portal_html(base)

    return results


def compute_exit_code(results):
    """Compute exit code from results."""
    for key, val in results.items():
        if val.get('status') == 'fail':
            return 2
    return 0


def print_summary(results):
    """Print human-readable summary."""
    print()
    print('=== Distill Quality Gate ===')
    print()

    checks = [
        ('required_files', 'Required files'),
        ('afprd_sections', 'AI-friendly PRD sections'),
        ('prd_quality_report', 'PRD quality report'),
        ('requirement_ir', 'Requirement IR'),
        ('layer_impact', 'Layer impact'),
        ('index_bridge', 'Index bridge'),
        ('final_quality_gate', 'Final quality gate'),
        ('report_quality', 'Report quality'),
        ('plan_missing_confirmation', 'Plan missing_confirmation'),
        ('portal_html', 'Portal HTML'),
    ]

    for key, label in checks:
        val = results[key]
        sym = {'pass': '+', 'warning': '!', 'fail': 'x'}[val['status']]
        print(f'  [{sym}] {label:30s} {val["status"]}')
        # Print relevant details for non-pass
        if val['status'] != 'pass':
            for k, v in val.items():
                if k == 'status':
                    continue
                if isinstance(v, bool):
                    if not v:
                        print(f'      {k}: false')
                elif isinstance(v, list) and v:
                    print(f'      {k}: {v}')
                elif isinstance(v, int) and v > 0:
                    print(f'      {k}: {v}')
                elif isinstance(v, str) and v:
                    print(f'      {k}: {v}')

    print()


def main():
    ap = argparse.ArgumentParser(
        description='Distill Completion Gate — deterministic checks for /prd-distill output'
    )
    ap.add_argument('--distill-dir', required=True,
                    help='Path to distill output directory (_prd-tools/distill/<slug>)')
    ap.add_argument('--repo-root', required=True,
                    help='Project root directory (containing _prd-tools/reference/)')
    args = ap.parse_args()

    distill_dir = Path(args.distill_dir).resolve()
    repo_root = Path(args.repo_root).resolve()

    if not distill_dir.is_dir():
        print(f'Error: {distill_dir} is not a directory', file=sys.stderr)
        sys.exit(1)

    print(f'Distill dir: {distill_dir}')
    print(f'Repo root:   {repo_root}')

    results = run_checks(distill_dir, repo_root)
    print_summary(results)

    exit_code = compute_exit_code(results)
    if exit_code == 2:
        print('RESULT: FAIL — missing critical files or checks, /prd-distill not complete.')
    else:
        has_warning = any(v.get('status') == 'warning' for v in results.values())
        if has_warning:
            print('RESULT: PASS with warnings — see above.')
        else:
            print('RESULT: PASS — all checks satisfied.')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()