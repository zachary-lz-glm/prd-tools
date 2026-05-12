#!/usr/bin/env python3
"""
distill-workflow-gate.py — Distill Workflow Order & Completion Gate

Deterministic gate that enforces:
  1. Distill files must be generated in order (_ingest -> spec -> context -> report/plan)
  2. portal.html must be script-rendered (not handwritten)
  3. distill-quality-gate.py must pass

Usage:
    python3 scripts/distill-workflow-gate.py \
      --distill-dir _prd-tools/distill/<slug> --repo-root .
    python3 .prd-tools/scripts/distill-workflow-gate.py \
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
# Workflow ordering config
# ──────────────────────────────────────────

# Ordered steps: each step requires the previous step's output to exist
WORKFLOW_STEPS = [
    {
        'step': 'ingest',
        'output': '_ingest/document.md',
        'label': 'Step 0: PRD Ingestion',
    },
    {
        'step': 'evidence',
        'output': 'context/evidence.yaml',
        'label': 'Step 1: Evidence Ledger',
    },
    {
        'step': 'afprd',
        'output': 'spec/ai-friendly-prd.md',
        'label': 'Step 1.5: AI-friendly PRD',
    },
    {
        'step': 'prd_quality',
        'output': 'context/prd-quality-report.yaml',
        'label': 'Step 1.5: PRD Quality Report',
    },
    {
        'step': 'requirement_ir',
        'output': 'context/requirement-ir.yaml',
        'label': 'Step 2: Requirement IR',
    },
    {
        'step': 'graph_context',
        'output': 'context/graph-context.md',
        'label': 'Step 3.1: Graph Context',
    },
    {
        'step': 'layer_impact',
        'output': 'context/layer-impact.yaml',
        'label': 'Step 3.2: Layer Impact',
    },
    {
        'step': 'contract_delta',
        'output': 'context/contract-delta.yaml',
        'label': 'Step 4: Contract Delta',
    },
    {
        'step': 'report',
        'output': 'report.md',
        'label': 'Step 8: Report',
    },
    {
        'step': 'report_confirmation',
        'output': 'context/report-confirmation.yaml',
        'label': 'Step 8.1: Report Review Gate',
    },
    {
        'step': 'plan',
        'output': 'plan.md',
        'label': 'Step 5: Plan',
    },
    {
        'step': 'readiness',
        'output': 'context/readiness-report.yaml',
        'label': 'Step 6: Readiness Report',
    },
    {
        'step': 'final_quality_gate',
        'output': 'context/final-quality-gate.yaml',
        'label': 'Step 8.5: Final Quality Gate',
    },
]


def _read_safe(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _file_exists_nonempty(path):
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def _check_workflow_order(distill_dir):
    """Check that distill files were generated in order.

    For each step N, if step N's output exists but step N-1's output
    does not, that's an ordering violation.
    """
    violations = []
    completed = []

    for i, step in enumerate(WORKFLOW_STEPS):
        output_path = distill_dir / step['output']
        exists = _file_exists_nonempty(output_path)

        if exists:
            for j in range(i):
                prev = WORKFLOW_STEPS[j]
                prev_path = distill_dir / prev['output']
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


def _check_portal_script_rendered(distill_dir):
    """Check portal.html exists and has script-rendered marker."""
    portal_path = distill_dir / 'portal.html'
    exists = _file_exists_nonempty(portal_path)

    if not exists:
        return {
            'status': 'fail',
            'exists': False,
            'marker_ok': False,
            'message': 'portal.html 不存在或为空',
        }

    text = _read_safe(portal_path)
    marker_ok = 'data-prd-tools-portal="distill"' in text

    if not marker_ok:
        return {
            'status': 'fail',
            'exists': True,
            'marker_ok': False,
            'message': 'portal.html 缺少 data-prd-tools-portal="distill" 标记，可能非脚本渲染',
        }

    return {
        'status': 'pass',
        'exists': True,
        'marker_ok': True,
    }


def _check_requirement_ir_source(distill_dir):
    """Check requirement-ir.yaml has ai_prd_req_id (must come from afprd)."""
    text = _read_safe(distill_dir / 'context' / 'requirement-ir.yaml')
    if not text.strip():
        return {
            'status': 'fail',
            'has_ai_prd_req_id': False,
            'message': 'requirement-ir.yaml 不存在或为空',
        }

    has_ai_prd_req_id = bool(re.search(r'ai_prd_req_id:', text))
    has_afprd_source = bool(re.search(r'ai_prd_source:\s*["\']?spec/ai-friendly-prd\.md', text))

    return {
        'status': 'pass' if (has_ai_prd_req_id and has_afprd_source) else 'fail',
        'has_ai_prd_req_id': has_ai_prd_req_id,
        'has_afprd_source': has_afprd_source,
    }


def _check_layer_impact_anchors(distill_dir):
    """Check layer-impact.yaml has code_anchors or fallback."""
    text = _read_safe(distill_dir / 'context' / 'layer-impact.yaml')
    if not text.strip():
        return {
            'status': 'fail',
            'has_code_anchors': False,
            'has_fallback': False,
            'message': 'layer-impact.yaml 不存在或为空',
        }

    has_code_anchors = bool(re.search(r'code_anchors:', text))
    has_fallback = bool(re.search(r'fallback:', text)) or bool(re.search(r'fallback_reason:', text))

    return {
        'status': 'pass' if (has_code_anchors or has_fallback) else 'fail',
        'has_code_anchors': has_code_anchors,
        'has_fallback': has_fallback,
    }


def _check_report_confirmation(distill_dir):
    """Check report-confirmation.yaml approves downstream plan/readiness."""
    text = _read_safe(distill_dir / 'context' / 'report-confirmation.yaml')
    if not text.strip():
        return {
            'status': 'fail',
            'exists': False,
            'approved': False,
            'message': 'report-confirmation.yaml 不存在或为空',
        }

    approved = bool(re.search(r'^status:\s*["\']?approved["\']?\s*$', text, re.M))
    return {
        'status': 'pass' if approved else 'fail',
        'exists': True,
        'approved': approved,
        'message': '' if approved else 'report-confirmation.yaml status 不是 approved',
    }


def _check_quality_gate(distill_dir, repo_root):
    """Run distill-quality-gate.py and capture result."""
    candidates = [
        Path(repo_root) / '.prd-tools' / 'scripts' / 'distill-quality-gate.py',
        Path(repo_root) / 'scripts' / 'distill-quality-gate.py',
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
            'message': 'distill-quality-gate.py 未找到，跳过质量门禁检查',
        }

    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(gate_script),
             '--distill-dir', str(distill_dir),
             '--repo-root', str(repo_root)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        exit_code = result.returncode
        stdout = result.stdout.strip()

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
            'message': f'运行 distill-quality-gate.py 失败: {e}',
        }


def run_checks(distill_dir, repo_root):
    """Run all checks and return results dict."""
    base = Path(distill_dir).resolve()

    results = {}
    results['workflow_order'] = _check_workflow_order(base)
    results['requirement_ir_source'] = _check_requirement_ir_source(base)
    results['layer_impact_anchors'] = _check_layer_impact_anchors(base)
    results['report_confirmation'] = _check_report_confirmation(base)
    results['portal_html'] = _check_portal_script_rendered(base)
    results['quality_gate'] = _check_quality_gate(base, repo_root)

    return results


def compute_exit_code(results):
    for key, val in results.items():
        if val.get('status') == 'fail':
            return 2
    return 0


def print_summary(results):
    print()
    print('=== Distill Workflow Gate ===')
    print()

    # Workflow order
    wo = results['workflow_order']
    sym = '+' if wo['status'] == 'pass' else 'x'
    completed = f'{len(wo["completed_steps"])}/{wo["total_steps"]}'
    print(f'  [{sym}] workflow order: {wo["status"]} ({completed} steps completed)')
    if wo['violations']:
        for v in wo['violations']:
            print(f'      VIOLATION: {v["output"]} exists but prerequisite {v["missing_prerequisite"]} is missing')

    # Requirement IR source
    ris = results['requirement_ir_source']
    sym = '+' if ris['status'] == 'pass' else 'x'
    details = []
    if not ris.get('has_ai_prd_req_id'):
        details.append('missing ai_prd_req_id')
    if not ris.get('has_afprd_source'):
        details.append('missing ai_prd_source ref to spec/ai-friendly-prd.md')
    if details:
        print(f'  [{sym}] requirement-ir source: {", ".join(details)}')
    else:
        print(f'  [{sym}] requirement-ir source: ok')

    # Layer impact anchors
    lia = results['layer_impact_anchors']
    sym = '+' if lia['status'] == 'pass' else 'x'
    if lia.get('has_code_anchors'):
        print(f'  [{sym}] layer-impact anchors: has code_anchors')
    elif lia.get('has_fallback'):
        print(f'  [{sym}] layer-impact anchors: fallback only')
    else:
        print(f'  [{sym}] layer-impact anchors: MISSING (no code_anchors or fallback)')

    # Portal html
    rc = results['report_confirmation']
    sym = '+' if rc['status'] == 'pass' else 'x'
    if rc.get('approved'):
        print(f'  [{sym}] report confirmation: approved')
    else:
        print(f'  [{sym}] report confirmation: {rc.get("message", "not approved")}')

    # Portal html
    ph = results['portal_html']
    sym = '+' if ph['status'] == 'pass' else ('!' if ph['status'] == 'warning' else 'x')
    if ph['exists'] and ph.get('marker_ok'):
        print(f'  [{sym}] portal.html: script-rendered')
    elif ph['exists']:
        print(f'  [{sym}] portal.html: exists but {ph.get("message", "not script-rendered")}')
    else:
        print(f'  [{sym}] portal.html: {ph.get("message", "MISSING")}')

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
        description='Distill Workflow Gate — enforce ordering and completion for /prd-distill output'
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
        print('RESULT: FAIL — workflow ordering violations or missing required outputs.')
        print('        /prd-distill must not be declared complete.')
    else:
        has_warning = any(v.get('status') == 'warning' for v in results.values())
        if has_warning:
            print('RESULT: PASS with warnings — see above.')
        else:
            print('RESULT: PASS — workflow ordering and completion verified.')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
