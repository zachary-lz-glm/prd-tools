#!/usr/bin/env python3
"""
context-pack.py — Context Pack MVP

Generates a curated context pack for model consumption from:
  - distill artifacts (requirement-ir.yaml, layer-impact.yaml, evidence.yaml)
  - evidence index (entities.json, edges.json, inverted-index.json)

Outputs:
  - <distill>/context/query-plan.yaml   — query plan with matched entities
  - <out>                               — context-pack.md

Usage:
    python3 scripts/context-pack.py \
      --distill /path/to/distill/output \
      --index /tmp/prd-index \
      --out /tmp/context-pack.md
    python3 .prd-tools/scripts/context-pack.py \
      --distill _prd-tools/distill/<slug> \
      --index _prd-tools/reference/index \
      --out _prd-tools/distill/<slug>/context/context-pack.md
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ──────────────────────────────────────────
# YAML I/O (no third-party deps)
# ──────────────────────────────────────────


def _load_yaml(path):
    """Minimal YAML loader — handles the subset we produce."""
    text = Path(path).read_text(encoding='utf-8')
    # For our structured files we just return raw text; parsing is done
    # with targeted regex below. This avoids a full YAML parser.
    return text


def _save_yaml(path, text):
    Path(path).write_text(text, encoding='utf-8')


# ──────────────────────────────────────────
# Distill artifact readers
# ──────────────────────────────────────────


def parse_requirement_ir(path):
    """Extract structured requirements from requirement-ir.yaml."""
    text = Path(path).read_text(encoding='utf-8')
    reqs = []
    pattern = re.compile(r'^\s*-\s+id:\s+"?([A-Z]+-\d+)"?\s*$(.*?)(?=^\s*-\s+id:|\Z)', re.S | re.M)
    for m in pattern.finditer(text):
        req_id = m.group(1)
        block = m.group(2)

        def _field(name, default=''):
            fm = re.search(rf'^\s*{re.escape(name)}:\s*(.+?)\s*$', block, re.M)
            if not fm:
                return default
            value = fm.group(1).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value

        title = _field('title')
        intent = _field('intent') or _field('business_intent')
        change = _field('change_type')
        prio = _field('priority', 'P1')
        conf = _field('confidence', 'medium')

        def _list_field(name):
            fm = re.search(rf'^\s*{re.escape(name)}:\s*(.*?)(?:^\s*\w+:\s*|\Z)', block, re.S | re.M)
            if not fm:
                return []
            return re.findall(r'^\s*-\s+"?([^"\n]+)"?\s*$', fm.group(1), re.M)

        rules = _list_field('rules')
        biz_entities = _list_field('business_entities')
        open_questions = _list_field('open_questions')
        reqs.append({
            'id': req_id,
            'title': title,
            'intent': intent,
            'change_type': change,
            'priority': prio,
            'confidence': conf,
            'rules': rules[:6],
            'business_entities': biz_entities[:8],
            'open_questions': open_questions[:6],
        })
    return reqs


def parse_layer_impact(path):
    """Extract BFF-layer impacts from layer-impact.yaml."""
    text = Path(path).read_text(encoding='utf-8')
    impacts = []
    for m in re.finditer(
        r'- layer: (\w+)\n'
        r'\s+capability_surface: ([^\n]+)\n'
        r'\s+target: "([^"]+)"\n'
        r'\s+planned_changes: "([^"]+)"\n'
        r'\s+risk: (\w+)',
        text,
    ):
        layer, surface, target, changes, risk = m.groups()
        if layer == 'bff':
            impacts.append({
                'surface': surface.strip(),
                'target': target,
                'changes': changes,
                'risk': risk,
            })
    return impacts


# ──────────────────────────────────────────
# Evidence index helpers
# ──────────────────────────────────────────


def load_index(index_dir):
    """Load evidence index files."""
    p = Path(index_dir)
    entities = json.loads((p / 'entities.json').read_text(encoding='utf-8'))
    edges = json.loads((p / 'edges.json').read_text(encoding='utf-8'))
    inv = json.loads((p / 'inverted-index.json').read_text(encoding='utf-8'))
    # Filter out backup/tmp paths
    _SKIP_PATH = re.compile(r'/(?:backup|backups|tmp|temp|\.tmp)/', re.IGNORECASE)
    entities = [e for e in entities if not _SKIP_PATH.search('/' + e['path'] + '/')]
    edges = [e for e in edges if not _SKIP_PATH.search('/' + e.get('from', '') + '/') and not _SKIP_PATH.search('/' + e.get('to', '') + '/')]
    # Rebuild inverted index without filtered entities
    valid_ids = {e['id'] for e in entities}
    inv = {k: [v for v in vs if v in valid_ids] for k, vs in inv.items()}
    inv = {k: vs for k, vs in inv.items() if vs}
    by_id = {e['id']: e for e in entities}
    return entities, edges, inv, by_id


# ──────────────────────────────────────────
# Domain terminology bridge
# ──────────────────────────────────────────


def _load_domain_terms(ref_dir):
    """Load terms from 05-domain.yaml for vocabulary bridging. Returns [] if unavailable."""
    domain_path = Path(ref_dir) / '05-domain.yaml'
    if not domain_path.exists():
        return []
    try:
        text = domain_path.read_text(encoding='utf-8')
    except Exception:
        return []

    terms = []
    blocks = re.split(r'^\s{2}-\s+term:', text, flags=re.MULTILINE)
    for block in blocks[1:]:
        term_data = {}
        m = re.match(r'\s*"?([^"\n]+)"?\s*$', block, re.MULTILINE)
        if m:
            term_data['term'] = m.group(1).strip().strip('"').strip("'")

        # prd_keywords
        kw_match = re.search(r'prd_keywords:\s*\[([^\]]*)\]', block)
        if kw_match:
            term_data['prd_keywords'] = [
                k.strip().strip('"').strip("'")
                for k in kw_match.group(1).split(',') if k.strip()
            ]
        else:
            kw_section = re.search(r'prd_keywords:\s*\n((?:\s+-\s+.+\n?)*)', block)
            if kw_section:
                term_data['prd_keywords'] = [
                    v.strip().strip('"').strip("'")
                    for v in re.findall(r'^\s+-\s+(.+)$', kw_section.group(1), re.MULTILINE)
                ]
            else:
                term_data['prd_keywords'] = []

        # synonyms
        syn_match = re.search(r'synonyms:\s*\[([^\]]*)\]', block)
        if syn_match:
            term_data['synonyms'] = [
                s.strip().strip('"').strip("'")
                for s in syn_match.group(1).split(',') if s.strip()
            ]
        else:
            syn_section = re.search(r'synonyms:\s*\n((?:\s+-\s+.+\n?)*)', block)
            if syn_section:
                term_data['synonyms'] = [
                    v.strip().strip('"').strip("'")
                    for v in re.findall(r'^\s+-\s+(.+)$', syn_section.group(1), re.MULTILINE)
                ]
            else:
                term_data['synonyms'] = []

        # related_enum
        enum_match = re.search(r'related_enum:\s*"?([^"\n]+)"?', block)
        if enum_match:
            val = enum_match.group(1).strip().strip('"').strip("'")
            term_data['related_enum'] = val if val else ''
        else:
            term_data['related_enum'] = ''

        if term_data.get('term'):
            terms.append(term_data)

    return terms


def _expand_with_domain(query_term, domain_terms):
    """Expand a query term using domain vocabulary. Returns list of code identifiers."""
    q_lower = query_term.lower()
    expansions = []
    for dt in domain_terms:
        all_keywords = [k.lower() for k in dt.get('prd_keywords', [])]
        all_synonyms = [s.lower() for s in dt.get('synonyms', [])]
        term_lower = dt.get('term', '').lower()

        matched = (
            q_lower == term_lower
            or q_lower in all_keywords
            or q_lower in all_synonyms
            or any(q_lower in kw for kw in all_keywords if len(q_lower) >= 2)
        )
        if matched:
            if dt.get('related_enum'):
                expansions.append(dt['related_enum'])
            term_val = dt.get('term', '')
            if term_val and term_val != query_term:
                expansions.append(term_val)
    return expansions


def name_to_terms(name, extra=()):
    """Decompose an identifier into searchable terms (mirrors build-index.py)."""
    terms = {name}
    for part in re.findall(r'[A-Z]{2,}|[A-Z][a-z]+|[a-z]{2,}|\d+', name):
        terms.add(part)
        terms.add(part.lower())
    if '_' in name:
        for seg in name.split('_'):
            if len(seg) > 1:
                terms.add(seg)
                terms.add(seg.lower())
    for e in extra:
        if e:
            terms.add(e)
    return terms


def _path_segments(path):
    segs = set()
    for seg in path.split('/'):
        segs.add(seg.lower())
        if '.' in seg:
            segs.add(seg.rsplit('.', 1)[0].lower())
    return segs


TYPE_BONUS = frozenset({
    'enum', 'class', 'interface', 'function',
    'template', 'registry', 'switch_case',
})


def query_entities(query_str, inv, by_id, max_results=10):
    """Score and rank entities for a query string (mirrors build-index.py scoring)."""
    q_lower = query_str.lower()
    q_terms = {t.lower() for t in name_to_terms(query_str)}

    candidate_ids = set()
    for qt in q_terms:
        candidate_ids.update(inv.get(qt, []))

    results = []
    for cid in candidate_ids:
        ent = by_id.get(cid)
        if not ent:
            continue
        score = 0
        if ent['name'].lower() == q_lower:
            score += 10
        ent_terms_l = {t.lower() for t in ent.get('terms', [])}
        for qt in sorted(q_terms):
            if qt in ent_terms_l:
                score += 3
        path_segs = _path_segments(ent['path'])
        for qt in sorted(q_terms):
            if qt in path_segs:
                score += 2
        if ent['type'] in TYPE_BONUS:
            score += 1
        if score > 0:
            results.append((score, ent))

    results.sort(key=lambda r: (-r[0], r[1]['id']))
    return [(s, e) for s, e in results[:max_results]]


# ──────────────────────────────────────────
# Query plan generation
# ──────────────────────────────────────────

# Map requirement change_type / keywords to expected entity types
_KEYWORD_TYPE_MAP = {
    'CampaignType': ['enum'],
    'Template': ['template', 'function'],
    'getDetailsTemplate': ['template'],
    'getAudienceSegmentationTemplate': ['template'],
    'previewRewardTypeMap': ['registry', 'const'],
    'rewardCondition': ['template', 'function'],
    'Controller': ['class'],
    'Service': ['class'],
    'Model': ['class'],
}

def _extract_query_hints_from_impacts(impacts):
    """Derive query terms from layer-impact targets."""
    hints = []
    for imp in impacts:
        target = imp['target']
        # Extract filename stem as hint
        stem = Path(target.replace(' (NEW)', '')).stem
        if stem and stem not in ('index',):
            hints.append(stem)
        # Extract class/function names from changes text
        for name in re.findall(r'get\w+Template|CampaignType|\w+Controller|\w+Service', imp['changes']):
            hints.append(name)
    return list(set(hints))


_TERM_STOPWORDS = frozenset({
    'add', 'modify', 'delete', 'change', 'type', 'step', 'rules',
    'rule', 'config', 'template', 'condition', 'options', 'default',
    'string', 'number', 'boolean', 'input', 'select', 'checkbox',
    'high', 'medium', 'low', 'bff', 'backend', 'frontend',
})


def _codeish_terms(text):
    """Extract compact code/search terms without exploding context size."""
    terms = set()
    for raw in re.findall(r'[A-Za-z][A-Za-z0-9_]*', text or ''):
        if len(raw) < 3:
            continue
        lower = raw.lower()
        if lower in _TERM_STOPWORDS:
            continue
        has_signal = (
            '_' in raw
            or any(c.isupper() for c in raw[1:])
            or raw.isupper()
            or lower in {
                'campaign', 'campaigntype', 'gasstation', 'gasstationdxgy',
                'courierdxgy', 'previewrewardtypemap', 'rewardcondition',
                'eventrule', 'budget', 'gmv', 'push', 'dlp', 'card',
                'coupon', 'discount', 'message', 'basic',
            }
        )
        if has_signal:
            terms.add(raw)
    return terms


def build_query_plan(requirements, impacts, inv, by_id, domain_terms=None, ref_dir=None):
    """Build query plan from requirements + impacts + index."""
    queries = []
    qid = 0

    # Phase 1: requirement-driven queries
    seen_terms = set()
    req_terms = []
    for req in requirements:
        req_terms.extend(_codeish_terms(req['title']))
        req_terms.extend(_codeish_terms(req['intent']))
        for ent in req.get('business_entities', []):
            req_terms.extend(_codeish_terms(ent))
        for rule in req.get('rules', []):
            req_terms.extend(_codeish_terms(rule))
        for q in req.get('open_questions', []):
            req_terms.extend(_codeish_terms(q))

    # Domain expansion: expand PRD terms to code identifiers
    domain_expanded = set()
    if domain_terms:
        extra_terms = []
        # Check existing code-ish terms against domain vocabulary
        for t in req_terms:
            expansions = _expand_with_domain(t, domain_terms)
            for exp in expansions:
                if exp.lower() not in {rt.lower() for rt in req_terms}:
                    extra_terms.append(exp)
                    domain_expanded.add(exp.lower())
        # Also check raw requirement text for domain prd_keywords (handles Chinese/non-ASCII)
        raw_texts = []
        for req in requirements:
            raw_texts.append(req.get('title', ''))
            raw_texts.append(req.get('intent', ''))
            raw_texts.extend(req.get('business_entities', []))
            raw_texts.extend(req.get('rules', []))
        combined_text = ' '.join(raw_texts)
        for dt in domain_terms:
            for kw in dt.get('prd_keywords', []) + dt.get('synonyms', []):
                if kw and kw in combined_text:
                    if dt.get('related_enum'):
                        exp = dt['related_enum']
                        if exp.lower() not in {rt.lower() for rt in req_terms} and exp.lower() not in domain_expanded:
                            extra_terms.append(exp)
                            domain_expanded.add(exp.lower())
                    term_val = dt.get('term', '')
                    if term_val and term_val.lower() not in {rt.lower() for rt in req_terms} and term_val.lower() not in domain_expanded:
                        extra_terms.append(term_val)
                        domain_expanded.add(term_val.lower())
                    break
        req_terms.extend(extra_terms)

    for t in sorted({term for term in req_terms if len(term) > 2}, key=str.lower):
        if t.lower() in seen_terms:
            continue
        seen_terms.add(t.lower())
        hits = query_entities(t, inv, by_id, max_results=5)
        matched = [e['id'] for _, e in hits]
        if not matched:
            continue
        qid += 1
        expected = _KEYWORD_TYPE_MAP.get(t, [])
        conf = 'high' if any(e['type'] in ('enum', 'template', 'registry', 'class') for _, e in hits) else 'medium'
        # Domain-expanded terms cap at medium confidence
        if t.lower() in domain_expanded and conf == 'high':
            conf = 'medium'
        hint = 'domain-bridge: ' + t if t.lower() in domain_expanded else 'req-term: ' + t
        queries.append({
            'id': f'QP-{qid:03d}',
            'requirement_hint': hint,
            'query_terms': sorted(name_to_terms(t)),
            'expected_anchor_types': expected,
            'matched_entities': matched,
            'confidence': conf,
        })
        if qid >= 30:
            break

    # Phase 2: queries from reference seed symbols
    SEED_QUERIES_DEFAULT = [
        'CampaignType',
        'getDetailsTemplate',
        'getAudienceSegmentationTemplate',
        'previewRewardTypeMap',
        'rewardCondition',
        'courierDxGy',
        'gasStation',
        'build/**/*.d.ts',
        'build/**/*.js',
    ]

    def _load_seed_queries(ref_dir):
        if ref_dir:
            rp = ref_dir / "04-routing-playbooks.yaml"
            if rp.exists():
                try:
                    import yaml as _yaml
                    data = _yaml.safe_load(rp.read_text(encoding='utf-8')) or {}
                    queries = []
                    for route in data.get('prd_routing', []):
                        for f in route.get('key_files', []):
                            stem = Path(f).stem
                            if stem:
                                queries.append(stem)
                    if queries:
                        return queries
                except Exception:
                    pass
        return SEED_QUERIES_DEFAULT

    seed_queries = _load_seed_queries(ref_dir)
    for sq in seed_queries:
        if sq.lower() in seen_terms:
            continue
        seen_terms.add(sq.lower())
        qid += 1
        hits = query_entities(sq, inv, by_id, max_results=5)
        matched = [e['id'] for _, e in hits]
        conf = 'high' if any(e['type'] in ('enum', 'template', 'registry', 'class') for _, e in hits) else 'medium'
        if not matched:
            conf = 'low'
        expected = _KEYWORD_TYPE_MAP.get(sq, [])
        queries.append({
            'id': f'QP-{qid:03d}',
            'requirement_hint': 'anchor: ' + sq,
            'query_terms': sorted(name_to_terms(sq)),
            'expected_anchor_types': expected,
            'matched_entities': matched,
            'confidence': conf,
        })

    # Phase 3: queries from layer-impact targets
    impact_hints = _extract_query_hints_from_impacts(impacts)
    for hint in sorted(set(impact_hints)):
        if hint.lower() in seen_terms:
            continue
        seen_terms.add(hint.lower())
        qid += 1
        hits = query_entities(hint, inv, by_id, max_results=5)
        matched = [e['id'] for _, e in hits]
        conf = 'high' if matched else 'low'
        queries.append({
            'id': f'QP-{qid:03d}',
            'requirement_hint': f'impact: {hint}',
            'query_terms': sorted(name_to_terms(hint)),
            'expected_anchor_types': [],
            'matched_entities': matched,
            'confidence': conf,
        })

    # Phase 4: queries from P0 requirements
    for req in requirements:
        if req['priority'] != 'P0':
            continue
        # Extract candidate query terms from requirement title
        terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+|\b(?:CampaignType|Template|Controller|Service|Reward)\b', req['title'])
        if not terms:
            # Try extracting from rules
            for rule in req['rules']:
                terms.extend(re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', rule))
        for t in set(terms):
            if t.lower() in seen_terms:
                continue
            seen_terms.add(t.lower())
            qid += 1
            hits = query_entities(t, inv, by_id, max_results=3)
            matched = [e['id'] for _, e in hits]
            queries.append({
                'id': f'QP-{qid:03d}',
                'requirement_hint': f'{req["id"]}: {req["title"][:60]}',
                'query_terms': sorted(name_to_terms(t)),
                'expected_anchor_types': [],
                'matched_entities': matched,
                'confidence': 'high' if matched else 'low',
            })

    return queries


def format_query_plan_yaml(queries):
    """Format query plan as YAML string."""
    lines = ['schema_version: "1.0"', 'queries:']
    for q in queries:
        lines.append(f'  - id: {q["id"]}')
        lines.append(f'    requirement_hint: "{q["requirement_hint"]}"')
        qt = json.dumps(q['query_terms'])
        lines.append(f'    query_terms: {qt}')
        et = json.dumps(q['expected_anchor_types'])
        lines.append(f'    expected_anchor_types: {et}')
        me = json.dumps(q['matched_entities'])
        lines.append(f'    matched_entities: {me}')
        lines.append(f'    confidence: {q["confidence"]}')
        lines.append('')
    return '\n'.join(lines)


# ──────────────────────────────────────────
# Context pack generation
# ──────────────────────────────────────────


def _ent_anchor(ent, reason=''):
    """Format a single entity as a code anchor line."""
    line_str = f':{ent["line"]}' if ent.get('line') else ''
    return (
        f'| `{ent["path"]}{line_str}` '
        f'| `{ent["name"]}` '
        f'| {ent["type"]} '
        f'| {reason} |'
    )


def generate_context_pack(slug, requirements, impacts, query_plan, by_id):
    """Generate context-pack.md content."""
    lines = []

    # ── Header ──
    lines.append(f'# Context Pack: {slug}')
    lines.append('')
    lines.append('> Curated context for model consumption. Derived from distill artifacts + evidence index.')
    lines.append('')

    # ── 1. PRD Signals ──
    lines.append('## 1. PRD Signals')
    lines.append('')
    lines.append('| ID | Title | Priority | Change | Confidence |')
    lines.append('|----|-------|----------|--------|------------|')
    for r in requirements:
        lines.append(f'| {r["id"]} | {r["title"][:70]} | {r["priority"]} | {r["change_type"]} | {r["confidence"]} |')
    lines.append('')

    # P0 requirement intent summaries (compact)
    p0_reqs = [r for r in requirements if r['priority'] == 'P0']
    if p0_reqs:
        lines.append('**P0 Requirements:**')
        for r in p0_reqs:
            rules_text = '; '.join(r['rules'][:3])
            lines.append(f'- **{r["id"]}** {r["title"]}: {r["intent"]}')
            if rules_text:
                lines.append(f'  - Rules: {rules_text[:120]}')
        lines.append('')

    # ── 2. Query Plan ──
    lines.append('## 2. Query Plan')
    lines.append('')
    lines.append('| QP | Hint | Terms | Hits | Conf |')
    lines.append('|----|------|-------|------|------|')
    for q in query_plan:
        terms_short = ', '.join(q['query_terms'][:4])
        if len(q['query_terms']) > 4:
            terms_short += ' ...'
        hits = len(q['matched_entities'])
        lines.append(f'| {q["id"]} | {q["requirement_hint"][:50]} | `{terms_short}` | {hits} | {q["confidence"]} |')
    lines.append('')

    # ── 3. Code Anchors ──
    lines.append('## 3. Code Anchors')
    lines.append('')
    lines.append('### 3.1 Type Registry')
    lines.append('')
    lines.append('| Location | Symbol | Type | Reason |')
    lines.append('|----------|--------|------|--------|')

    # Collect anchors by category
    type_anchors = []
    template_anchors = []
    registry_anchors = []
    dispatcher_anchors = []
    similar_anchors = []
    seen_ids = set()

    for q in query_plan:
        for eid in q['matched_entities']:
            if eid in seen_ids:
                continue
            ent = by_id.get(eid)
            if not ent:
                continue
            seen_ids.add(eid)
            cat = _categorize_entity(ent)
            if cat == 'type':
                type_anchors.append((ent, q['requirement_hint']))
            elif cat == 'template':
                template_anchors.append((ent, q['requirement_hint']))
            elif cat == 'registry':
                registry_anchors.append((ent, q['requirement_hint']))
            elif cat == 'dispatcher':
                dispatcher_anchors.append((ent, q['requirement_hint']))
            elif cat == 'similar':
                similar_anchors.append((ent, q['requirement_hint']))

    for ent, hint in type_anchors:
        lines.append(_ent_anchor(ent, hint[:50]))
    lines.append('')

    lines.append('### 3.2 Template Functions')
    lines.append('')
    lines.append('| Location | Symbol | Type | Reason |')
    lines.append('|----------|--------|------|--------|')
    for ent, hint in template_anchors:
        lines.append(_ent_anchor(ent, hint[:50]))
    lines.append('')

    if registry_anchors:
        lines.append('### 3.3 Registries and Maps')
        lines.append('')
        lines.append('| Location | Symbol | Type | Reason |')
        lines.append('|----------|--------|------|--------|')
        for ent, hint in registry_anchors:
            lines.append(_ent_anchor(ent, hint[:50]))
        lines.append('')

    if dispatcher_anchors:
        lines.append('### 3.4 Dispatchers (Switch-Case)')
        lines.append('')
        lines.append('| Location | Symbol | Type | Reason |')
        lines.append('|----------|--------|------|--------|')
        for ent, hint in dispatcher_anchors:
            cases = ent.get('meta', {}).get('cases', [])
            case_str = ', '.join(cases[:4])
            if len(cases) > 4:
                case_str += ' ...'
            lines.append(_ent_anchor(ent, f'{len(cases)} cases: {case_str}'[:70]))
        lines.append('')

    # ── 4. Similar Examples ──
    lines.append('## 4. Similar Examples')
    lines.append('')
    lines.append('Reference implementations for the new campaign type:')
    lines.append('')

    if similar_anchors:
        lines.append('| Location | Symbol | Type | Note |')
        lines.append('|----------|--------|------|------|')
        for ent, hint in similar_anchors:
            lines.append(_ent_anchor(ent, hint[:50]))
        lines.append('')

    # Explicit CourierDxGy/GasStation examples from impacts
    lines.append('**Pattern to follow:**')
    lines.append('```')
    for imp in impacts:
        if '(NEW)' in imp['target']:
            lines.append(f'NEW FILE: {imp["target"]}')
            lines.append(f'  -> {imp["changes"]}')
            lines.append(f'  -> Reference: courierDxGy.ts (same pattern)')
            lines.append('')
    lines.append('```')
    lines.append('')

    # ── 5. Required Plan Tasks ──
    lines.append('## 5. Required Plan Tasks')
    lines.append('')
    lines.append('Derived from query plan hits + layer impacts:')
    lines.append('')

    task_id = 0
    # From impacts with (NEW)
    for imp in impacts:
        if '(NEW)' in imp['target'] and imp['changes'].strip() and '无直接改动' not in imp['changes']:
            task_id += 1
            lines.append(f'### T{task_id:02d}: Create `{Path(imp["target"].replace(" (NEW)", "")).name}`')
            lines.append(f'- Target: `{imp["target"]}`')
            lines.append(f'- Changes: {imp["changes"]}')
            lines.append(f'- Risk: {imp["risk"]}')
            lines.append('')

    # From impacts without (NEW) but low risk
    for imp in impacts:
        if '(NEW)' not in imp['target'] and imp['risk'] in ('low', 'medium') and imp['changes'].strip() and '无直接改动' not in imp['changes']:
            task_id += 1
            lines.append(f'### T{task_id:02d}: Modify `{Path(imp["target"]).name}`')
            lines.append(f'- Target: `{imp["target"]}`')
            lines.append(f'- Changes: {imp["changes"]}')
            lines.append(f'- Risk: {imp["risk"]}')
            lines.append('')

    # ── 6. Missing / Low Confidence ──
    lines.append('## 6. Missing / Low Confidence')
    lines.append('')
    low_conf = [q for q in query_plan if q['confidence'] == 'low']
    if low_conf:
        lines.append('| QP | Hint | Issue |')
        lines.append('|----|------|-------|')
        for q in low_conf:
            lines.append(f'| {q["id"]} | {q["requirement_hint"][:50]} | No entities matched |')
        lines.append('')
    else:
        lines.append('All queries returned results.')
        lines.append('')

    # Needs-confirmation items from requirements
    nc_reqs = [r for r in requirements if r['confidence'] != 'high']
    if nc_reqs:
        lines.append('**Needs confirmation:**')
        for r in nc_reqs:
            lines.append(f'- {r["id"]}: {r["title"]}')
        lines.append('')

    return '\n'.join(lines)


def _categorize_entity(ent):
    """Assign an entity to a display category for the anchors section."""
    t = ent['type']
    name = ent['name']
    path = ent['path']

    # Similar examples: courierDxGy / gasStation files and functions
    for kw in ('courierDxGy', 'gasStation', 'courier', 'GasStation'):
        if kw.lower() in name.lower() or kw.lower() in path.lower():
            if t in ('template', 'function', 'file') and 'index' not in path:
                return 'similar'

    # Type registry: enums, interfaces, classes
    if t in ('enum', 'interface', 'class'):
        return 'type'

    # Dispatchers: switch_case only
    if t == 'switch_case':
        return 'dispatcher'

    # Registries
    if t == 'registry':
        return 'registry'

    # Templates
    if t in ('template', 'function'):
        return 'template'

    return 'template'


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(
        description='Generate Context Pack from distill artifacts + evidence index'
    )
    ap.add_argument('--distill', '--distill-dir', dest='distill', required=True,
                    help='Path to distill output directory')
    ap.add_argument('--index', '--index-dir', dest='index', required=False,
                    help='Path to evidence index directory (default: <distill>/../reference/index)')
    ap.add_argument('--out', required=False,
                    help='Output path for context-pack.md (default: <distill>/context/context-pack.md)')
    args = ap.parse_args()

    distill = Path(args.distill).resolve()
    index_dir = Path(args.index).resolve() if args.index else distill.parent / 'reference' / 'index'
    out_path = Path(args.out).resolve() if args.out else distill / 'context' / 'context-pack.md'

    # Validate inputs
    ctx_dir = distill / 'context'
    req_ir_path = ctx_dir / 'requirement-ir.yaml'
    impact_path = ctx_dir / 'layer-impact.yaml'
    if not req_ir_path.exists():
        print(f'Error: {req_ir_path} not found', file=sys.stderr)
        sys.exit(1)
    if not (index_dir / 'entities.json').exists():
        print(f'Error: {index_dir}/entities.json not found', file=sys.stderr)
        sys.exit(1)

    # Read inputs
    slug = distill.name
    requirements = parse_requirement_ir(req_ir_path)
    impacts = parse_layer_impact(impact_path) if impact_path.exists() else []
    entities, edges, inv, by_id = load_index(index_dir)

    # Load domain terms for vocabulary bridging
    ref_dir = index_dir.parent  # index is at _prd-tools/reference/index/, parent is reference/
    domain_terms = _load_domain_terms(ref_dir)

    print(f'Requirements: {len(requirements)}')
    print(f'BFF impacts:  {len(impacts)}')
    print(f'Index:        {len(entities)} entities, {len(inv)} terms')
    if domain_terms:
        print(f'Domain terms: {len(domain_terms)} loaded')

    # Build query plan
    query_plan = build_query_plan(requirements, impacts, inv, by_id,
                                  domain_terms=domain_terms, ref_dir=ref_dir)
    high_q = sum(1 for q in query_plan if q['confidence'] == 'high')
    low_q = sum(1 for q in query_plan if q['confidence'] == 'low')
    print(f'Query plan:   {len(query_plan)} queries (high={high_q}, low={low_q})')

    # Save query-plan.yaml
    qp_yaml = format_query_plan_yaml(query_plan)
    qp_path = ctx_dir / 'query-plan.yaml'
    _save_yaml(qp_path, qp_yaml)
    print(f'Written: {qp_path}')

    # Generate context-pack.md
    md = generate_context_pack(slug, requirements, impacts, query_plan, by_id)

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding='utf-8')
    line_count = md.count('\n')
    print(f'Written: {out_path} ({line_count} lines)')

    if line_count > 800:
        print(f'WARNING: context-pack exceeds 800 lines ({line_count})', file=sys.stderr)


if __name__ == '__main__':
    main()
