#!/usr/bin/env python3
"""
final-quality-gate.py — Final Quality Gate MVP

Deterministic quality gate that checks whether distill deliverables
(report.md, plan.md) are ready for developer consumption.

Checks (no LLM, pure text analysis):
  1. required_files       — are all expected files present?
  2. context_pack_consumed — did report/plan use context-pack anchors?
  3. code_anchor_coverage  — did plan.md reference key file paths?
  4. plan_actionability    — checklists, file paths, verify commands
  5. blocker_quality       — blockers have owner/suggestion/mitigation

Usage:
    python3 scripts/final-quality-gate.py \
      --distill /path/to/distill/output
    python3 .prd-tools/scripts/final-quality-gate.py \
      --distill _prd-tools/distill/<slug>

Output:
    <distill>/context/final-quality-gate.yaml
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ──────────────────────────────────────────
# Required files config
# ──────────────────────────────────────────

REQUIRED_FILES = {
    'critical': [
        'report.md',
        'plan.md',
    ],
    'important': [
        'context/requirement-ir.yaml',
        'context/graph-context.md',
        'context/layer-impact.yaml',
        'context/contract-delta.yaml',
        'context/readiness-report.yaml',
    ],
}

OPTIONAL_FILES = [
    'context/context-pack.md',
    'context/query-plan.yaml',
]

# ──────────────────────────────────────────
# Regex patterns
# ──────────────────────────────────────────

RE_CHECKLIST = re.compile(r'-\s+\[[ x]\]')
RE_FILE_PATH = re.compile(r'(?:src/|lib/)[\w/.-]+\.(?:ts|tsx|js|jsx|go|yaml|yml)')
RE_VERIFY_CMD = re.compile(
    r'(?:rg\s|grep\s|npm\s+test|pnpm\s+test|go\s+test|curl\s|npx\s+|jest|mocha|vitest)',
    re.IGNORECASE,
)
RE_BLOCKER = re.compile(
    r'(?:BLOCK|阻塞|待确认|Open\s+Question|阻塞项|blocker)',
    re.IGNORECASE,
)
RE_BLOCKER_QUALITY = re.compile(
    r'(?:建议|suggestion|影响|impact|默认策略|default|负责人|owner|mitigation|缓解|风险|risk)',
    re.IGNORECASE,
)
RE_ANCHOR_PATH = re.compile(r'`([^`]+\.(?:ts|tsx|js|jsx|go))`')

# Key anchors that should appear in a well-contextualized deliverable
KEY_ANCHOR_FILES_DEFAULT = [
    'campaignType.ts',
    'previewRewardType.ts',
    'details/index.ts',
    'audienceSegmentation/index.ts',
    'rewardCondition.ts',
    'basic.ts',
    'message.ts',
]


def load_key_anchors(base):
    """Load key anchor files from routing-playbooks, fall back to hardcoded."""
    rp = base.parent.parent / "reference" / "04-routing-playbooks.yaml"
    if rp.exists():
        try:
            import yaml as _yaml
            data = _yaml.safe_load(rp.read_text(encoding='utf-8')) or {}
            anchors = []
            for route in data.get('prd_routing', []):
                for f in route.get('key_files', []):
                    anchors.append(f)
            if anchors:
                return anchors
        except Exception:
            pass
    return list(KEY_ANCHOR_FILES_DEFAULT)

# ──────────────────────────────────────────
# Check helpers
# ──────────────────────────────────────────


def _read_safe(path):
    """Read file, return text or empty string."""
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _extract_paths_from_context_pack(text):
    """Extract code anchor file paths from context-pack.md tables."""
    paths = set()
    for m in RE_ANCHOR_PATH.finditer(text):
        paths.add(m.group(1))
    # Also match `src/...` without backticks
    for m in RE_FILE_PATH.finditer(text):
        paths.add(m.group(0))
    return paths


def _extract_paths_from_graph_context(text):
    """Extract key file paths from graph-context.md."""
    paths = set()
    for m in RE_ANCHOR_PATH.finditer(text):
        paths.add(m.group(1))
    for m in RE_FILE_PATH.finditer(text):
        paths.add(m.group(0))
    return paths


def _extract_symbols_from_context(text):
    """Extract `symbol` names from context-pack/code-anchor tables."""
    symbols = set()
    # Match symbol column in markdown tables: | `symbol_name` |
    for m in re.finditer(r'\|\s*`(\w+)`\s*\|', text):
        sym = m.group(1)
        if len(sym) > 3:
            symbols.add(sym)
    return symbols


# ──────────────────────────────────────────
# Check 1: Required files
# ──────────────────────────────────────────


def check_required_files(base):
    """Verify all expected files exist."""
    missing_critical = []
    missing_important = []
    present = []

    for f in REQUIRED_FILES['critical']:
        p = base / f
        if p.exists():
            present.append(f)
        else:
            missing_critical.append(f)

    for f in REQUIRED_FILES['important']:
        p = base / f
        if p.exists():
            present.append(f)
        else:
            missing_important.append(f)

    optional_present = []
    for f in OPTIONAL_FILES:
        if (base / f).exists():
            optional_present.append(f)

    # Score
    total = len(REQUIRED_FILES['critical']) + len(REQUIRED_FILES['important'])
    found = len(present)
    score = int(100 * found / total) if total else 100

    status = 'pass'
    if missing_critical:
        status = 'fail'
    elif missing_important:
        status = 'warning'

    return {
        'status': status,
        'score': score,
        'present': sorted(present),
        'missing_critical': sorted(missing_critical),
        'missing_important': sorted(missing_important),
        'optional_present': sorted(optional_present),
    }


# ──────────────────────────────────────────
# Check 2: Context pack consumed
# ──────────────────────────────────────────


def check_context_pack_consumed(base, report_text, plan_text):
    """Check if report/plan consumed context-pack anchors."""
    cp_path = base / 'context/context-pack.md'
    if not cp_path.exists():
        return {
            'status': 'warning',
            'score': 0,
            'note': 'context-pack.md not found, skipping',
            'anchors_in_pack': 0,
            'consumed_by_report': 0,
            'consumed_by_plan': 0,
        }

    cp_text = _read_safe(cp_path)
    anchor_paths = _extract_paths_from_context_pack(cp_text)
    anchor_symbols = _extract_symbols_from_context(cp_text)

    if not anchor_paths and not anchor_symbols:
        return {
            'status': 'pass',
            'score': 100,
            'note': 'no extractable anchors in context-pack',
            'anchors_in_pack': 0,
            'consumed_by_report': 0,
            'consumed_by_plan': 0,
        }

    # Check consumption — use basenames and key terms
    all_anchors = set()
    for p in anchor_paths:
        all_anchors.add(p)
        all_anchors.add(Path(p).name)
        all_anchors.add(Path(p).stem)
    all_anchors.update(anchor_symbols)

    # Filter to short meaningful names only
    check_terms = {t for t in all_anchors if len(t) > 3}

    report_hits = sum(1 for t in check_terms if t.lower() in report_text.lower())
    plan_hits = sum(1 for t in check_terms if t.lower() in plan_text.lower())

    total_terms = len(check_terms) if check_terms else 1
    report_ratio = report_hits / total_terms
    plan_ratio = plan_hits / total_terms

    # Good if either report or plan consumes >30% of anchors
    best_ratio = max(report_ratio, plan_ratio)
    score = int(100 * min(best_ratio / 0.3, 1.0))

    status = 'pass'
    if best_ratio < 0.1:
        status = 'warning'
        score = min(score, 30)
    elif best_ratio < 0.3:
        status = 'warning'

    return {
        'status': status,
        'score': score,
        'anchors_in_pack': len(check_terms),
        'consumed_by_report': report_hits,
        'consumed_by_plan': plan_hits,
        'report_ratio': round(report_ratio, 2),
        'plan_ratio': round(plan_ratio, 2),
    }


# ──────────────────────────────────────────
# Check 3: Code anchor coverage
# ──────────────────────────────────────────


def check_code_anchor_coverage(base, plan_text):
    """Check if plan.md references key code anchor paths."""
    # Collect anchor paths from all context sources
    anchor_paths = set()

    # From context-pack.md
    cp_text = _read_safe(base / 'context/context-pack.md')
    anchor_paths.update(_extract_paths_from_context_pack(cp_text))

    # From graph-context.md
    gc_text = _read_safe(base / 'context/graph-context.md')
    anchor_paths.update(_extract_paths_from_graph_context(gc_text))

    # From layer-impact.yaml
    li_text = _read_safe(base / 'context/layer-impact.yaml')
    for m in RE_FILE_PATH.finditer(li_text):
        anchor_paths.add(m.group(0))

    if not anchor_paths:
        return {
            'status': 'pass',
            'score': 100,
            'note': 'no anchor paths found in context files',
            'total_anchors': 0,
            'covered': 0,
            'uncovered': [],
        }

    # Check plan coverage using basenames
    plan_lower = plan_text.lower()
    covered = set()
    uncovered = set()

    for p in anchor_paths:
        basename = Path(p).name.lower()
        stem = Path(p).stem.lower()
        if basename in plan_lower or stem in plan_lower:
            covered.add(p)
        else:
            uncovered.add(p)

    ratio = len(covered) / len(anchor_paths)
    score = int(100 * ratio)

    # Also check against key anchor basenames
    key_anchors = load_key_anchors(base)
    key_found = 0
    for ka in key_anchors:
        if ka.lower() in plan_lower:
            key_found += 1
    key_ratio = key_found / len(key_anchors) if key_anchors else 1
    key_score = int(100 * key_ratio)

    # Combined score (60% coverage, 40% key anchors)
    final_score = int(0.6 * score + 0.4 * key_score)

    status = 'pass'
    if key_ratio < 0.3:
        status = 'fail'
        final_score = min(final_score, 40)
    elif ratio < 0.5:
        status = 'warning'

    return {
        'status': status,
        'score': final_score,
        'total_anchors': len(anchor_paths),
        'covered': len(covered),
        'key_anchors_found': key_found,
        'key_anchors_total': len(key_anchors),
        'uncovered_samples': sorted(uncovered)[:5],
    }


# ──────────────────────────────────────────
# Check 4: Plan actionability
# ──────────────────────────────────────────


def check_plan_actionability(plan_text):
    """Check plan.md for checklists, file paths, and verify commands."""
    checklists = RE_CHECKLIST.findall(plan_text)
    n_checklists = len(checklists)

    file_paths = RE_FILE_PATH.findall(plan_text)
    n_file_paths = len(set(file_paths))

    verify_cmds = RE_VERIFY_CMD.findall(plan_text)
    n_verify_cmds = len(verify_cmds)

    # Score components
    # Checklists: target >= 5
    cl_score = min(100, int(100 * n_checklists / 5)) if n_checklists else 0
    # File paths: target >= 3
    fp_score = min(100, int(100 * n_file_paths / 3)) if n_file_paths else 0
    # Verify commands: target >= 1
    vc_score = 100 if n_verify_cmds >= 1 else 0

    # Weighted: 30% checklists, 40% file paths, 30% verify commands
    score = int(0.3 * cl_score + 0.4 * fp_score + 0.3 * vc_score)

    status = 'pass'
    if n_file_paths == 0:
        status = 'fail'
        score = min(score, 20)
    elif n_checklists == 0:
        status = 'warning'
        score = min(score, 70)
    elif n_verify_cmds == 0:
        status = 'warning'

    return {
        'status': status,
        'score': score,
        'checklist_count': n_checklists,
        'file_path_count': n_file_paths,
        'file_paths_sample': sorted(set(file_paths))[:8],
        'verify_command_count': n_verify_cmds,
        'missing_checklists': n_checklists == 0,
        'missing_file_paths': n_file_paths == 0,
        'missing_verify_commands': n_verify_cmds == 0,
    }


# ──────────────────────────────────────────
# Check 5: Blocker quality
# ──────────────────────────────────────────


def check_blocker_quality(report_text):
    """Check if blockers in report.md have quality attributes."""
    # Find blocker sections
    blocker_matches = list(RE_BLOCKER.finditer(report_text))

    if not blocker_matches:
        # No blockers found — could be good (none exist) or bad (not documented)
        # If report mentions "无阻塞" or similar, it's fine
        if re.search(r'无阻[塞塞]|no\s+blocker|无\s*OPEN', report_text, re.IGNORECASE):
            return {
                'status': 'pass',
                'score': 100,
                'blocker_count': 0,
                'note': 'report explicitly states no blockers',
                'quality_ratio': 1.0,
            }
        # Check if report has a blockers section at all
        has_section = bool(re.search(
            r'#{1,4}\s.*(?:阻塞|blocker|open\s+question|待确认)',
            report_text, re.IGNORECASE
        ))
        if has_section:
            return {
                'status': 'pass',
                'score': 100,
                'blocker_count': 0,
                'note': 'blockers section present but empty',
                'quality_ratio': 1.0,
            }
        return {
            'status': 'warning',
            'score': 70,
            'blocker_count': 0,
            'note': 'no blocker section found in report',
            'quality_ratio': 0,
        }

    blocker_count = len(blocker_matches)

    # For each blocker, check surrounding context for quality attributes
    quality_hits = 0
    for m in blocker_matches:
        # Extract a window around the blocker mention
        start = max(0, m.start() - 50)
        end = min(len(report_text), m.end() + 300)
        window = report_text[start:end]
        if RE_BLOCKER_QUALITY.search(window):
            quality_hits += 1

    quality_ratio = quality_hits / blocker_count if blocker_count else 1.0
    score = int(100 * quality_ratio)

    status = 'pass'
    if quality_ratio < 0.5:
        status = 'warning'
        score = min(score, 50)

    return {
        'status': status,
        'score': score,
        'blocker_count': blocker_count,
        'blockers_with_context': quality_hits,
        'quality_ratio': round(quality_ratio, 2),
    }


# ──────────────────────────────────────────
# Scoring and output
# ──────────────────────────────────────────

CHECK_WEIGHTS = {
    'required_files': 0.20,
    'context_pack_consumed': 0.15,
    'code_anchor_coverage': 0.25,
    'plan_actionability': 0.25,
    'blocker_quality': 0.15,
}


def compute_overall(checks):
    """Compute weighted overall score and status."""
    score = sum(
        CHECK_WEIGHTS[k] * checks[k]['score']
        for k in CHECK_WEIGHTS
    )
    score = int(round(score))

    # Status rules
    if checks['required_files']['missing_critical']:
        return 'fail', score
    if checks['plan_actionability']['missing_file_paths']:
        return 'fail', score
    if checks['plan_actionability']['missing_checklists']:
        return 'warning', min(score, 84)
    if checks.get('context_pack_consumed', {}).get('status') == 'warning':
        return 'warning', min(score, 84)

    if score >= 85:
        return 'pass', score
    elif score >= 60:
        return 'warning', score
    else:
        return 'fail', score


def collect_gaps(checks):
    """Collect top gaps for summary."""
    gaps = []
    c = checks

    if c['required_files']['missing_critical']:
        gaps.append(f"missing critical files: {c['required_files']['missing_critical']}")

    if c['required_files']['missing_important']:
        gaps.append(f"missing context files: {c['required_files']['missing_important'][:3]}")

    pa = c['plan_actionability']
    if pa['missing_checklists']:
        gaps.append('plan.md has no checklists (no "- [ ]" items)')
    if pa['missing_file_paths']:
        gaps.append('plan.md has no source file paths')
    if pa['missing_verify_commands']:
        gaps.append('plan.md has no verification commands (rg/grep/test)')

    ca = c['code_anchor_coverage']
    if ca.get('key_anchors_found', 0) < ca.get('key_anchors_total', 0):
        gaps.append(
            f"plan covers {ca.get('key_anchors_found', 0)}/{ca.get('key_anchors_total', 0)} key anchors"
        )

    bq = c['blocker_quality']
    if bq['blocker_count'] > 0 and bq['quality_ratio'] < 0.5:
        gaps.append(
            f"blockers lack context ({bq['blockers_with_context']}/{bq['blocker_count']} have owner/suggestion)"
        )

    return gaps[:6]


def format_output_yaml(checks, overall_status, overall_score, gaps):
    """Format the quality gate result as YAML."""
    lines = [
        'schema_version: "1.0"',
        f'status: {overall_status}',
        f'score: {overall_score}',
        '',
        'checks:',
    ]

    for check_name in CHECK_WEIGHTS:
        c = checks[check_name]
        lines.append(f'  {check_name}:')
        lines.append(f'    status: {c["status"]}')
        lines.append(f'    score: {c["score"]}')
        # Add relevant detail fields
        for k, v in c.items():
            if k in ('status', 'score'):
                continue
            if isinstance(v, bool):
                lines.append(f'    {k}: {str(v).lower()}')
            elif isinstance(v, str):
                lines.append(f'    {k}: "{v}"')
            elif isinstance(v, float):
                lines.append(f'    {k}: {v}')
            elif isinstance(v, int):
                lines.append(f'    {k}: {v}')
            elif isinstance(v, list):
                if not v:
                    lines.append(f'    {k}: []')
                else:
                    lines.append(f'    {k}:')
                    for item in v:
                        lines.append(f'      - "{item}"')

    lines.append('')
    lines.append('summary:')
    lines.append(f'  top_gaps:')
    if gaps:
        for g in gaps:
            lines.append(f'    - "{g}"')
    else:
        lines.append(f'    - "no significant gaps"')

    lines.append('')
    return '\n'.join(lines)


REPORT_SECTIONS = [
    "1. 需求摘要",
    "2. PRD 质量摘要",
    "3. 源码扫描命中摘要",
    "4. 影响范围",
    "5. 关键结论",
    "6. 变更明细表",
    "7. 字段清单",
    "8. 校验规则",
    "9. 开发 Checklist",
    "10. 契约对齐与建议",
    "11. Top Open Questions",
    "12. 阻塞问题与待确认项",
]

PLAN_SECTIONS = [
    "1. 范围与假设",
    "2. 整体架构",
    "3. 实现计划",
    "4. API 设计",
    "5. 数据存储",
    "6. 配置与开关",
    "7. 校验规则汇总",
    "8. QA 矩阵",
    "9. 契约对齐",
    "10. 风险与回滚",
    "11. 工作量估算",
]


def check_section_structure(base):
    """Check report.md and plan.md H2 headings match schema-defined sections."""
    results = {}
    for name, expected in [('report.md', REPORT_SECTIONS), ('plan.md', PLAN_SECTIONS)]:
        p = base / name
        if not p.is_file():
            results[name] = {'status': 'skip', 'reason': 'file missing'}
            continue
        text = _read_safe(p)
        got = re.findall(r'^## (.+)$', text, re.MULTILINE)
        got = [g.lstrip('§').strip() for g in got]
        errors = []
        for i, exp in enumerate(expected):
            if i >= len(got):
                errors.append(f"missing section {i+1}: '{exp}'")
            else:
                exp_num = exp.split('.')[0]
                got_num = got[i].split('.')[0] if '.' in got[i] else ''
                if got_num != exp_num:
                    errors.append(f"section {i+1} mismatch: expected '{exp}', got '{got[i]}'")
        extra = got[len(expected):]
        if extra:
            errors.append(f"unexpected extra sections: {extra[:3]}")
        status = 'pass' if not errors else 'fail'
        results[name] = {'status': status, 'errors': errors}
    overall = 'pass' if all(r['status'] != 'fail' for r in results.values()) else 'fail'
    return {
        'status': overall,
        'score': 100 if overall == 'pass' else 0,
        'report': results.get('report.md', {}),
        'plan': results.get('plan.md', {}),
    }


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(
        description='Final Quality Gate — deterministic checks for distill deliverables'
    )
    ap.add_argument('--distill', '--distill-dir', dest='distill', required=True,
                    help='Path to distill output directory')
    args = ap.parse_args()

    base = Path(args.distill).resolve()
    if not base.is_dir():
        print(f'Error: {base} is not a directory', file=sys.stderr)
        sys.exit(1)

    # Read main deliverables
    report_text = _read_safe(base / 'report.md')
    plan_text = _read_safe(base / 'plan.md')

    print(f'Distill dir: {base}')
    print(f'report.md:   {len(report_text)} chars')
    print(f'plan.md:     {len(plan_text)} chars')
    print()

    # Run checks
    checks = {}
    print('Running checks...')

    print('  1/5 required_files')
    checks['required_files'] = check_required_files(base)

    print('  2/5 context_pack_consumed')
    checks['context_pack_consumed'] = check_context_pack_consumed(base, report_text, plan_text)

    print('  3/5 code_anchor_coverage')
    checks['code_anchor_coverage'] = check_code_anchor_coverage(base, plan_text)

    print('  4/5 plan_actionability')
    checks['plan_actionability'] = check_plan_actionability(plan_text)

    print('  5/6 blocker_quality')
    checks['blocker_quality'] = check_blocker_quality(report_text)

    print('  6/6 section_structure')
    checks['section_structure'] = check_section_structure(base)

    # Compute overall
    overall_status, overall_score = compute_overall(checks)
    gaps = collect_gaps(checks)

    # Output
    yaml_out = format_output_yaml(checks, overall_status, overall_score, gaps)
    out_path = base / 'context' / 'final-quality-gate.yaml'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml_out, encoding='utf-8')

    # Print summary
    print()
    print(f'  Status: {overall_status.upper()}')
    print(f'  Score:  {overall_score}/100')
    print()
    for name, c in checks.items():
        sym = {'pass': '+', 'warning': '!', 'fail': 'x'}[c['status']]
        print(f'  [{sym}] {name:30s} score={c["score"]:3d}  ({c["status"]})')
    if gaps:
        print()
        print('  Top gaps:')
        for g in gaps:
            print(f'    - {g}')
    print()
    print(f'Written: {out_path}')


if __name__ == '__main__':
    main()
