#!/usr/bin/env python3
"""Benchmark scoring engine for prd-tools output quality evaluation.

Uses only Python stdlib. Parses simple YAML structures via regex.
No external dependencies.

Usage:
  python3 scripts/benchmark_score.py --lint
  python3 scripts/benchmark_score.py --case DIR --output DIR [--baseline DIR] [--write-scores FILE]
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ── Lightweight YAML parser (flat lists only) ────────────────────────────────

def _parse_yaml_list_of_dicts(text: str, list_key: str) -> list[dict]:
    """Parse a simple YAML list like:
    list_key:
      - id: X
        title: Y
        ...
    Returns list of dicts with string values (or lists for must_contain etc).
    """
    result = []
    in_list = False
    current = {}
    current_indent = 0

    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith('#'):
            continue

        # Detect list start
        if stripped.startswith(f'{list_key}:'):
            in_list = True
            continue

        if not in_list:
            continue

        # Detect list item
        item_match = re.match(r'^(\s*)-\s+(\w+):\s*(.*)', stripped)
        if item_match:
            if current:
                result.append(current)
            current_indent = len(item_match.group(1))
            key = item_match.group(2)
            val = item_match.group(3).strip()
            current = {key: val}
            continue

        # Continuation key under current item
        key_match = re.match(r'^\s{0,' + str(current_indent + 6) + r'}(\w+):\s*(.*)', stripped)
        if key_match and current:
            key = key_match.group(1)
            val = key_match.group(2).strip()
            # Handle list values like: must_contain:\n  - foo
            if val == '':
                # Check next lines for list items
                continue
            current[key] = val

    if current:
        result.append(current)

    return result


def _parse_yaml_list_value(text: str, key: str) -> list[str]:
    """Parse a simple key:\n  - val1\n  - val2 structure."""
    result = []
    capture = False
    for line in text.splitlines():
        if line.strip().startswith(f'{key}:'):
            capture = True
            continue
        if capture:
            m = re.match(r'^\s+-\s+(.*)', line)
            if m:
                result.append(m.group(1).strip())
            else:
                capture = False
    return result


def _parse_yaml_string(text: str, key: str) -> str:
    for line in text.splitlines():
        m = re.match(rf'^{key}:\s*(.*)', line.strip())
        if m:
            return m.group(1).strip()
    return ''


def parse_yaml_items(filepath: str) -> list[dict]:
    """Parse expected/*.yaml files. Each file has a top-level key with a list of items.
    Returns list of dicts with string keys and string/list values.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the top-level key
    top_match = re.match(r'(\w+):\s*\n', text)
    if not top_match:
        return []
    top_key = top_match.group(1)

    items = []
    current = None
    current_list_key = None

    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith('#'):
            continue
        if stripped.startswith(f'{top_key}:'):
            continue

        # List item start: "  - id: XXX"
        m = re.match(r'^\s+-\s+(\w+):\s*(.*)', stripped)
        if m:
            if current:
                items.append(current)
            current = {m.group(1): m.group(2).strip()}
            current_list_key = None
            continue

        if current is None:
            continue

        # Sub-list item: "      - foo"
        sm = re.match(r'^\s+-\s+(.*)', stripped)
        if sm and current_list_key:
            current[current_list_key].append(sm.group(1).strip().strip('"').strip("'"))
            continue

        # Key-value pair: "    priority: P0"
        km = re.match(r'^\s+(\w+):\s*(.*)', stripped)
        if km:
            key = km.group(1)
            val = km.group(2).strip()
            if val == '':
                current[key] = []
                current_list_key = key
            else:
                current[key] = val
                current_list_key = None

    if current:
        items.append(current)

    return items


# ── Corpus loading ────────────────────────────────────────────────────────────

def load_corpus(output_dir: str) -> str:
    """Load and concatenate all scoring-relevant files from output."""
    corpus_files = [
        'report.md',
        'plan.md',
        'context/requirement-ir.yaml',
        'context/graph-context.md',
        'context/layer-impact.yaml',
        'context/contract-delta.yaml',
        'context/readiness-report.yaml',
    ]
    parts = []
    for f in corpus_files:
        fp = os.path.join(output_dir, f)
        if os.path.isfile(fp):
            with open(fp, 'r', encoding='utf-8') as fh:
                parts.append(fh.read())
    return '\n\n'.join(parts)


def load_file(output_dir: str, filename: str) -> str:
    fp = os.path.join(output_dir, filename)
    if os.path.isfile(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


# ── Scoring functions ─────────────────────────────────────────────────────────

def score_output_contract(case_dir: str, output_dir: str) -> dict:
    """Check required files and sections exist."""
    expected = parse_yaml_items(os.path.join(case_dir, 'expected', 'output-contract.yaml'))

    # Parse required_files and report/plan sections separately
    with open(os.path.join(case_dir, 'expected', 'output-contract.yaml'), 'r') as f:
        text = f.read()

    required_files = _parse_yaml_list_value(text, 'required_files')
    report_sections = _parse_yaml_list_value(text, 'report_required_sections')
    plan_sections = _parse_yaml_list_value(text, 'plan_required_sections')

    missing_files = []
    for rf in required_files:
        if not os.path.isfile(os.path.join(output_dir, rf)):
            missing_files.append(rf)

    report_text = load_file(output_dir, 'report.md')
    plan_text = load_file(output_dir, 'plan.md')

    missing_report = [s for s in report_sections if s not in report_text]
    missing_plan = [s for s in plan_sections if s not in plan_text]

    total = len(required_files) + len(report_sections) + len(plan_sections)
    hits = total - len(missing_files) - len(missing_report) - len(missing_plan)
    score = int(100 * hits / total) if total > 0 else 100

    return {
        'score': score,
        'missing_files': missing_files,
        'missing_report_sections': missing_report,
        'missing_plan_sections': missing_plan,
    }


def score_requirements(case_dir: str, corpus: str) -> dict:
    """Check requirement recall via must_contain text hits."""
    reqs = parse_yaml_items(os.path.join(case_dir, 'expected', 'requirements.yaml'))

    matched = []
    missing = []

    for req in reqs:
        must = req.get('must_contain', [])
        if isinstance(must, str):
            must = [must]

        if not must:
            continue

        hit = all(kw in corpus for kw in must)

        # Check should_flag_conflict
        conflict_kws = req.get('should_flag_conflict', [])
        if isinstance(conflict_kws, str):
            conflict_kws = [conflict_kws]
        conflict_hit = True
        if conflict_kws:
            # All conflict keywords present AND a conflict signal exists
            all_present = all(kw in corpus for kw in conflict_kws)
            conflict_signals = ['矛盾', '冲突', '待确认', '需确认', '不一致', 'contradict', 'conflict']
            has_signal = any(s in corpus for s in conflict_signals)
            conflict_hit = all_present and has_signal

        if hit and conflict_hit:
            matched.append(req.get('id', '?'))
        else:
            missing.append(req.get('id', '?'))

    total_weight = 0
    hit_weight = 0
    for req in reqs:
        w = 2 if req.get('priority') == 'P0' else 1
        total_weight += w
        rid = req.get('id', '?')
        if rid in matched:
            hit_weight += w

    score = int(100 * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'matched': len(matched),
        'total': len(reqs),
        'missing': missing,
    }


def score_code_anchors(case_dir: str, corpus: str) -> dict:
    """Check code anchor recall: path hit = 60%, symbol hit = 40%."""
    anchors = parse_yaml_items(os.path.join(case_dir, 'expected', 'code-anchors.yaml'))

    matched = []
    missing = []

    for anchor in anchors:
        path = anchor.get('path', '')
        symbols = anchor.get('symbols', [])
        if isinstance(symbols, str):
            symbols = [symbols]

        path_hit = path in corpus if path else True
        symbol_hits = sum(1 for s in symbols if s in corpus)
        symbol_ratio = symbol_hits / len(symbols) if symbols else 1.0

        anchor_score = 0.6 * (1 if path_hit else 0) + 0.4 * symbol_ratio

        if anchor_score >= 0.5:
            matched.append(anchor.get('id', '?'))
        else:
            missing.append(anchor.get('id', '?'))

    total_weight = 0
    hit_weight = 0
    for anchor in anchors:
        w = 2 if anchor.get('priority') == 'P0' else 1
        total_weight += w
        aid = anchor.get('id', '?')
        if aid in matched:
            hit_weight += w

    score = int(100 * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'matched': len(matched),
        'total': len(anchors),
        'missing': missing,
    }


def score_blockers(case_dir: str, corpus: str) -> dict:
    """Check blocker recall via must_contain text hits."""
    blockers = parse_yaml_items(os.path.join(case_dir, 'expected', 'blockers.yaml'))

    matched = []
    missing = []

    for blk in blockers:
        must = blk.get('must_contain', [])
        if isinstance(must, str):
            must = [must]

        if not must:
            continue

        hit = all(kw in corpus for kw in must)
        if hit:
            matched.append(blk.get('id', '?'))
        else:
            missing.append(blk.get('id', '?'))

    total_weight = 0
    hit_weight = 0
    for blk in blockers:
        w = 2 if blk.get('priority') == 'P0' else 1
        total_weight += w
        bid = blk.get('id', '?')
        if bid in matched:
            hit_weight += w

    score = int(100 * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'matched': len(matched),
        'total': len(blockers),
        'missing': missing,
    }


def score_plan_actionability(output_dir: str) -> dict:
    """Evaluate plan.md for actionable content."""
    plan_text = load_file(output_dir, 'plan.md')

    # Checklist count: - [ ] or - [x]
    checklist_count = len(re.findall(r'-\s+\[[ x]\]', plan_text))

    # File path hits: src/... or paths with extensions
    file_paths = set(re.findall(r'(?:src/[\w/.-]+\.(?:ts|tsx|js|go|yaml|yml|json))', plan_text))

    # Verification commands
    verif_patterns = [
        r'npm\s+test', r'pnpm\s+test', r'yarn\s+test',
        r'go\s+test', r'\brg\s+', r'\bgrep\s+', r'\bcurl\s+',
        r'npx\s+', r'tsc\b', r'eslint\b',
    ]
    verif_hits = sum(1 for p in verif_patterns if re.search(p, plan_text))

    # Scoring
    score = 50  # base
    score += min(20, checklist_count * 2)       # up to 20 for checklists
    score += min(20, len(file_paths) * 2)       # up to 20 for file paths
    score += min(10, verif_hits * 5)            # up to 10 for verif commands

    # Penalty: has checklist but no file paths
    weak_signals = []
    if checklist_count > 0 and len(file_paths) == 0:
        score -= 15
        weak_signals.append('有 checklist 但缺少文件路径')
    if verif_hits == 0:
        weak_signals.append('缺少验证命令')

    score = max(0, min(100, score))

    return {
        'score': score,
        'checklist_count': checklist_count,
        'file_path_hits': len(file_paths),
        'verification_command_hits': verif_hits,
        'weak_signals': weak_signals,
    }


# ── Main scoring ──────────────────────────────────────────────────────────────

WEIGHTS = {
    'output_contract': 0.20,
    'requirement_recall': 0.25,
    'code_anchor_recall': 0.25,
    'blocker_recall': 0.20,
    'plan_actionability': 0.10,
}


def run_score(case_dir: str, output_dir: str) -> dict:
    corpus = load_corpus(output_dir)

    scores = {
        'output_contract': score_output_contract(case_dir, output_dir),
        'requirement_recall': score_requirements(case_dir, corpus),
        'code_anchor_recall': score_code_anchors(case_dir, corpus),
        'blocker_recall': score_blockers(case_dir, corpus),
        'plan_actionability': score_plan_actionability(output_dir),
    }

    total = sum(scores[k]['score'] * WEIGHTS[k] for k in WEIGHTS)

    # Load pass thresholds from case.yaml
    case_text = ''
    case_file = os.path.join(case_dir, 'case.yaml')
    if os.path.isfile(case_file):
        with open(case_file, 'r') as f:
            case_text = f.read()
    min_score = int(_parse_yaml_string(case_text, 'min_total_score') or '80')

    return {
        'case_id': os.path.basename(case_dir),
        'output_dir': os.path.abspath(output_dir),
        'total_score': round(total),
        'passed': round(total) >= min_score,
        'scores': scores,
    }


def run_lint():
    """Validate all expected files parse correctly."""
    cases_dir = Path(__file__).parent.parent / 'benchmarks' / 'cases'
    errors = []

    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        case_yaml = case_dir / 'case.yaml'
        if not case_yaml.exists():
            errors.append(f'{case_dir.name}: missing case.yaml')
            continue

        expected_dir = case_dir / 'expected'
        for fname in ['requirements.yaml', 'code-anchors.yaml', 'blockers.yaml', 'output-contract.yaml']:
            fp = expected_dir / fname
            if not fp.exists():
                errors.append(f'{case_dir.name}: missing expected/{fname}')
                continue
            try:
                if fname == 'output-contract.yaml':
                    # output-contract uses flat lists, not list-of-dicts
                    with open(fp, 'r') as f:
                        text = f.read()
                    rf = _parse_yaml_list_value(text, 'required_files')
                    rs = _parse_yaml_list_value(text, 'report_required_sections')
                    ps = _parse_yaml_list_value(text, 'plan_required_sections')
                    if not (rf or rs or ps):
                        errors.append(f'{case_dir.name}: expected/{fname} parsed 0 entries')
                else:
                    items = parse_yaml_items(str(fp))
                    if not items:
                        errors.append(f'{case_dir.name}: expected/{fname} parsed 0 items')
            except Exception as e:
                errors.append(f'{case_dir.name}: expected/{fname} parse error: {e}')

    if errors:
        print('Lint errors:')
        for e in errors:
            print(f'  - {e}')
        sys.exit(1)
    else:
        print('Lint OK: all cases valid')


def run_compare(case_dir: str, baseline_dir: str, output_dir: str) -> dict:
    """Score current output and compare with baseline."""
    current = run_score(case_dir, output_dir)

    baseline_scores_file = os.path.join(baseline_dir, 'scores.yaml')
    if not os.path.isfile(baseline_scores_file):
        print(f'Warning: no baseline scores at {baseline_scores_file}', file=sys.stderr)
        return {'current': current, 'baseline': None, 'diff': None}

    # Parse baseline scores (simple YAML)
    with open(baseline_scores_file, 'r') as f:
        btext = f.read()

    baseline_total = int(_parse_yaml_string(btext, 'total_score') or '0')

    diff = current['total_score'] - baseline_total

    result = {
        'current': current,
        'baseline_total': baseline_total,
        'diff': diff,
        'regression': diff < -5,
    }

    # Per-dimension diff
    dim_diffs = {}
    for dim in WEIGHTS:
        cur = current['scores'][dim]['score']
        # Parse baseline dimension score
        # baseline scores.yaml has nested structure, search for dimension
        bl_match = re.search(rf'{dim}:\s*\n\s+score:\s*(\d+)', btext)
        bl = int(bl_match.group(1)) if bl_match else 0
        dim_diffs[dim] = cur - bl

    result['dimension_diffs'] = dim_diffs

    return result


def write_scores(result: dict, filepath: str):
    """Write scores.yaml (simple YAML, no library)."""
    lines = [
        f'case_id: {result["case_id"]}',
        f'output_dir: {result["output_dir"]}',
        f'total_score: {result["total_score"]}',
        f'passed: {"true" if result["passed"] else "false"}',
        '',
        'scores:',
    ]

    for dim, data in result['scores'].items():
        lines.append(f'  {dim}:')
        for k, v in data.items():
            if isinstance(v, list):
                if not v:
                    lines.append(f'    {k}: []')
                else:
                    lines.append(f'    {k}:')
                    for item in v:
                        lines.append(f'      - {item}')
            else:
                lines.append(f'    {k}: {v}')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def print_score_report(result: dict):
    """Pretty-print scoring result."""
    print(f'\n{"=" * 60}')
    print(f'  Benchmark: {result["case_id"]}')
    print(f'  Output:    {result["output_dir"]}')
    print(f'  Total:     {result["total_score"]}/100  {"PASS" if result["passed"] else "FAIL"}')
    print(f'{"=" * 60}')

    for dim, data in result['scores'].items():
        pct = WEIGHTS[dim]
        weighted = round(data['score'] * pct)
        print(f'\n  [{dim}] {data["score"]}/100 (weight {int(pct*100)}%, contributes {weighted})')
        for k, v in data.items():
            if k == 'score':
                continue
            if isinstance(v, list) and v:
                print(f'    {k}: {v}')
            elif not isinstance(v, list):
                print(f'    {k}: {v}')

    print()


def print_compare_report(result: dict):
    """Pretty-print comparison result."""
    bl = result.get('baseline_total')
    if bl is None:
        print_score_report(result['current'])
        return

    cur = result['current']
    diff = result['diff']

    arrow = '='
    if diff > 0:
        arrow = '+'
    elif diff < 0:
        arrow = '-'

    print(f'\n{"=" * 60}')
    print(f'  Compare: {cur["case_id"]}')
    print(f'  Baseline: {bl}  Current: {cur["total_score"]}  ({arrow}{abs(diff)})')
    if result['regression']:
        print(f'  *** REGRESSION DETECTED ***')
    print(f'{"=" * 60}')

    for dim, d in result.get('dimension_diffs', {}).items():
        symbol = '+' if d > 0 else ('-' if d < 0 else '=')
        print(f'  {dim}: {symbol}{d}')

    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

# ── Oracle scoring ────────────────────────────────────────────────────────────

PRIORITY_WEIGHT = {'P0': 2.0, 'P1': 1.0, 'P2': 0.5}

ORACLE_WEIGHTS = {
    'requirement_recall':    35,
    'code_anchor_accuracy':  30,
    'blocker_quality':       20,
    'plan_actionability':    15,
}

FORBIDDEN_PENALTY_MAX = 10


def _parse_oracle(filepath):
    """Parse oracle.yaml into structured sections."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Parse each section using the existing parse_yaml_items
    # but oracle has different keys, so we parse manually
    sections = {
        'requirements': [],
        'code_anchors': [],
        'blockers': [],
        'forbidden_claims': [],
    }

    current_section = None
    current = None
    current_list_key = None

    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith('#'):
            continue

        # Section headers
        for sec in sections:
            if stripped.startswith(f'{sec}:'):
                current_section = sec
                current = None
                current_list_key = None
                break
        else:
            if current_section is None:
                continue

            # List item start
            m = re.match(r'^\s+-\s+(\w+):\s*(.*)', stripped)
            if m:
                if current:
                    sections[current_section].append(current)
                current = {m.group(1): m.group(2).strip().strip('"').strip("'")}
                current_list_key = None
                continue

            if current is None:
                continue

            # Sub-list item
            sm = re.match(r'^\s+-\s+(.*)', stripped)
            if sm and current_list_key:
                val = sm.group(1).strip().strip('"').strip("'")
                if isinstance(current.get(current_list_key), list):
                    current[current_list_key].append(val)
                continue

            # Key-value
            km = re.match(r'^\s+(\w+):\s*(.*)', stripped)
            if km:
                key = km.group(1)
                val = km.group(2).strip().strip('"').strip("'")
                if val == '':
                    current[key] = []
                    current_list_key = key
                else:
                    current[key] = val
                    current_list_key = None

    if current and current_section:
        sections[current_section].append(current)

    return sections


def _load_deliverable(output_dir, name):
    """Load a specific deliverable file, return its text."""
    mapping = {
        'report': 'report.md',
        'plan': 'plan.md',
        'requirement-ir': 'context/requirement-ir.yaml',
        'graph-context': 'context/graph-context.md',
        'layer-impact': 'context/layer-impact.yaml',
        'contract-delta': 'context/contract-delta.yaml',
        'readiness-report': 'context/readiness-report.yaml',
        'context-pack': 'context/context-pack.md',
        'query-plan': 'context/query-plan.yaml',
    }
    fp = os.path.join(output_dir, mapping.get(name, name))
    if os.path.isfile(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def _weight_of(priority):
    return PRIORITY_WEIGHT.get(priority, 1.0)


def _grade(score):
    if score >= 90: return 'A'
    if score >= 80: return 'B'
    if score >= 70: return 'C'
    if score >= 60: return 'D'
    return 'F'


def oracle_score_requirements(req_items, output_dir):
    """Score requirement recall against oracle."""
    matched = []
    missed = []
    total_weight = 0.0
    hit_weight = 0.0

    for req in req_items:
        rid = req.get('id', '?')
        prio = req.get('priority', 'P1')
        w = _weight_of(prio)
        total_weight += w

        terms = req.get('acceptable_terms', [])
        if isinstance(terms, str):
            terms = [terms]

        targets = req.get('must_appear_in', [])
        if isinstance(targets, str):
            targets = [targets]

        # Check each target deliverable
        all_hit = True
        for target in targets:
            text = _load_deliverable(output_dir, target)
            if not text:
                all_hit = False
                break
            # All acceptable terms must appear in at least one target
            for term in terms:
                if term not in text:
                    all_hit = False
                    break
            if not all_hit:
                break

        # Check conflict flagging if required
        if all_hit and req.get('must_flag_conflict') == 'true':
            conflict_sigs = req.get('conflict_signals', [])
            if isinstance(conflict_sigs, str):
                conflict_sigs = [conflict_sigs]
            if conflict_sigs:
                report_text = _load_deliverable(output_dir, 'report')
                has_signal = any(s in report_text for s in conflict_sigs)
                if not has_signal:
                    all_hit = False

        if all_hit:
            matched.append(rid)
            hit_weight += w
        else:
            missed.append(rid)

    max_score = ORACLE_WEIGHTS['requirement_recall']
    score = int(max_score * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'max': max_score,
        'matched': matched,
        'missed': missed,
    }


def oracle_score_code_anchors(anchor_items, output_dir):
    """Score code anchor accuracy against oracle."""
    matched = []
    missed = []
    total_weight = 0.0
    hit_weight = 0.0

    for anchor in anchor_items:
        aid = anchor.get('id', '?')
        prio = anchor.get('priority', 'P1')
        w = _weight_of(prio)
        total_weight += w

        path = anchor.get('path', '')
        symbol = anchor.get('symbol', '')
        targets = anchor.get('must_appear_in', [])
        if isinstance(targets, str):
            targets = [targets]

        hit = False
        for target in targets:
            text = _load_deliverable(output_dir, target)
            if not text:
                continue
            # Path hit (basename or full)
            path_hit = (path in text or
                        os.path.basename(path) in text or
                        Path(path).stem in text) if path else True
            # Symbol hit
            sym_hit = symbol in text if symbol else True
            if path_hit and sym_hit:
                hit = True
                break

        if hit:
            matched.append(aid)
            hit_weight += w
        else:
            missed.append(aid)

    max_score = ORACLE_WEIGHTS['code_anchor_accuracy']
    score = int(max_score * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'max': max_score,
        'matched': matched,
        'missed': missed,
    }


def oracle_score_blockers(blocker_items, output_dir):
    """Score blocker quality against oracle."""
    matched = []
    missed = []
    total_weight = 0.0
    hit_weight = 0.0

    for blk in blocker_items:
        bid = blk.get('id', '?')
        prio = blk.get('priority', 'P1')
        w = _weight_of(prio)
        total_weight += w

        terms = blk.get('acceptable_terms', [])
        if isinstance(terms, str):
            terms = [terms]

        targets = blk.get('must_appear_in', [])
        if isinstance(targets, str):
            targets = [targets]

        hit = False
        for target in targets:
            text = _load_deliverable(output_dir, target)
            if not text:
                continue
            if all(t in text for t in terms):
                hit = True
                break

        if hit:
            matched.append(bid)
            hit_weight += w
        else:
            missed.append(bid)

    max_score = ORACLE_WEIGHTS['blocker_quality']
    score = int(max_score * hit_weight / total_weight) if total_weight > 0 else 0

    return {
        'score': score,
        'max': max_score,
        'matched': matched,
        'missed': missed,
    }


def oracle_score_plan_actionability(output_dir):
    """Score plan actionability (reuse existing logic)."""
    plan_text = load_file(output_dir, 'plan.md')
    max_score = ORACLE_WEIGHTS['plan_actionability']

    checklist_count = len(re.findall(r'-\s+\[[ x]\]', plan_text))
    file_paths = set(re.findall(r'(?:src/[\w/.-]+\.(?:ts|tsx|js|go|yaml|yml|json))', plan_text))
    verif_patterns = [
        r'npm\s+test', r'pnpm\s+test', r'yarn\s+test',
        r'go\s+test', r'\brg\s+', r'\bgrep\s+', r'\bcurl\s+',
        r'npx\s+', r'tsc\b', r'eslint\b',
    ]
    verif_hits = sum(1 for p in verif_patterns if re.search(p, plan_text))

    # Score components (out of 15 max)
    raw = 5  # base
    raw += min(4, checklist_count)
    raw += min(4, len(file_paths))
    raw += min(2, verif_hits)

    issues = []
    if checklist_count == 0:
        issues.append('plan has no checklists')
    if len(file_paths) == 0:
        issues.append('plan has no file paths')
    if verif_hits == 0:
        issues.append('plan has no verification commands')

    score = min(max_score, raw)

    return {
        'score': score,
        'max': max_score,
        'issues': issues if issues else ['none'],
    }


def oracle_check_forbidden(forbidden_items, output_dir):
    """Check for forbidden claims across all deliverables."""
    corpus = load_corpus(output_dir)
    # Also load context files not in default corpus
    for extra in ['context/context-pack.md', 'context/query-plan.yaml']:
        corpus += '\n' + load_file(output_dir, extra)

    hits = []
    for fc in forbidden_items:
        fid = fc.get('id', '?')
        terms = fc.get('forbidden_terms', [])
        if isinstance(terms, str):
            terms = [terms]
        for term in terms:
            if term in corpus:
                hits.append({'id': fid, 'term': term, 'meaning': fc.get('meaning', '')})

    penalty = min(FORBIDDEN_PENALTY_MAX, len(hits) * 3)

    return {
        'penalty': penalty,
        'hits': [f'{h["id"]}: "{h["term"]}" ({h["meaning"]})' for h in hits],
    }


def run_oracle(oracle_path, output_dir):
    """Run full oracle scoring."""
    sections = _parse_oracle(oracle_path)

    req_result = oracle_score_requirements(sections['requirements'], output_dir)
    anchor_result = oracle_score_code_anchors(sections['code_anchors'], output_dir)
    blocker_result = oracle_score_blockers(sections['blockers'], output_dir)
    plan_result = oracle_score_plan_actionability(output_dir)
    forbidden_result = oracle_check_forbidden(sections['forbidden_claims'], output_dir)

    gross = (req_result['score'] + anchor_result['score'] +
             blocker_result['score'] + plan_result['score'])
    quality_score = max(0, gross - forbidden_result['penalty'])

    # P0 requirement miss → hard fail
    p0_missed = []
    for req in sections['requirements']:
        if req.get('priority') == 'P0' and req.get('id', '?') in req_result['missed']:
            p0_missed.append(req['id'])

    passed = quality_score >= 60 and len(p0_missed) == 0

    return {
        'type': 'oracle',
        'quality_score': quality_score,
        'grade': _grade(quality_score),
        'passed': passed,
        'p0_requirement_misses': p0_missed,
        'scores': {
            'requirement_recall': req_result,
            'code_anchor_accuracy': anchor_result,
            'blocker_quality': blocker_result,
            'plan_actionability': plan_result,
            'false_positive_penalty': forbidden_result,
        },
    }


def print_oracle_report(result):
    """Pretty-print oracle scoring result."""
    print(f'\n{"=" * 60}')
    print(f'  Oracle Quality Score (ground-truth based)')
    print(f'  Grade:  {result["grade"]}  Score: {result["quality_score"]}/100')
    print(f'  Passed: {"YES" if result["passed"] else "NO"}')
    print(f'{"=" * 60}')

    for dim in ['requirement_recall', 'code_anchor_accuracy', 'blocker_quality', 'plan_actionability']:
        d = result['scores'][dim]
        sym = '+' if d['score'] >= d['max'] * 0.8 else ('!' if d['score'] >= d['max'] * 0.5 else 'x')
        print(f'\n  [{sym}] {dim}  {d["score"]}/{d["max"]}')
        if d.get('missed'):
            print(f'      missed: {d["missed"]}')
        if d.get('issues') and d['issues'] != ['none']:
            print(f'      issues: {d["issues"]}')

    fp = result['scores']['false_positive_penalty']
    if fp['penalty'] > 0:
        print(f'\n  [!] false_positive_penalty  -{fp["penalty"]}')
        for h in fp['hits']:
            print(f'      HIT: {h}')
    else:
        print(f'\n  [+] false_positive_penalty  0 (no forbidden claims found)')

    if result.get('p0_requirement_misses'):
        print(f'\n  *** P0 REQUIREMENT MISSES (hard fail): {result["p0_requirement_misses"]} ***')

    print()


def write_oracle_scores(result, filepath):
    """Write oracle scores to YAML file."""
    lines = [
        f'type: oracle',
        f'quality_score: {result["quality_score"]}',
        f'grade: {result["grade"]}',
        f'passed: {"true" if result["passed"] else "false"}',
        '',
        'scores:',
    ]

    for dim in ['requirement_recall', 'code_anchor_accuracy', 'blocker_quality', 'plan_actionability', 'false_positive_penalty']:
        d = result['scores'][dim]
        lines.append(f'  {dim}:')
        for k, v in d.items():
            if isinstance(v, list):
                if not v:
                    lines.append(f'    {k}: []')
                else:
                    lines.append(f'    {k}:')
                    for item in v:
                        lines.append(f'      - "{item}"')
            else:
                lines.append(f'    {k}: {v}')

    lines.append('')
    lines.append('p0_requirement_misses:')
    for m in result.get('p0_requirement_misses', []):
        lines.append(f'  - "{m}"')
    if not result.get('p0_requirement_misses'):
        lines.append('  []')

    lines.append('')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Benchmark scoring engine')
    parser.add_argument('--lint', action='store_true', help='Validate expected files')
    parser.add_argument('--case', type=str, help='Case directory')
    parser.add_argument('--output', type=str, help='Output directory to score')
    parser.add_argument('--baseline', type=str, help='Baseline directory for comparison')
    parser.add_argument('--write-scores', type=str, help='Write scores.yaml to this path')
    parser.add_argument('--oracle', type=str, help='Path to oracle.yaml for ground-truth scoring')
    parser.add_argument('--write-oracle-scores', type=str, help='Write oracle scores.yaml to this path')

    args = parser.parse_args()

    if args.lint:
        run_lint()
        return

    if args.oracle:
        if not args.output:
            print('Error: --output required with --oracle', file=sys.stderr)
            sys.exit(1)
        result = run_oracle(args.oracle, args.output)
        print_oracle_report(result)
        if args.write_oracle_scores:
            write_oracle_scores(result, args.write_oracle_scores)
            print(f'Oracle scores written to {args.write_oracle_scores}')
        return

    if not args.case or not args.output:
        print('Error: --case and --output required (unless --lint or --oracle)', file=sys.stderr)
        sys.exit(1)

    if args.baseline:
        result = run_compare(args.case, args.baseline, args.output)
        print_compare_report(result)
    else:
        result = run_score(args.case, args.output)
        print_score_report(result)

    if args.write_scores:
        # run_compare returns nested structure; extract current scores
        if 'current' in result:
            write_scores(result['current'], args.write_scores)
        else:
            write_scores(result, args.write_scores)
        print(f'Scores written to {args.write_scores}')


if __name__ == '__main__':
    main()
