#!/usr/bin/env python3
"""
build-index.py — Evidence Index MVP

Regex-based code scanner that produces a lightweight evidence index.
Supports TypeScript, JavaScript, and Go.

Usage:
    python3 scripts/build-index.py --repo /path/to/repo --out /path/to/output
    python3 .prd-tools/scripts/build-index.py --repo . --out _prd-tools/reference/index

Output:
    manifest.yaml        — index metadata
    entities.json        — all discovered code entities
    edges.json           — relationships between entities
    inverted-index.json  — term → entity lookup
"""

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path

# ──────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────

SKIP_DIRS = frozenset({
    'node_modules', 'dist', 'build', 'coverage', '.git',
    '.prd-tools', '__pycache__', '.serverless', '.next',
    'backup', 'backups', 'tmp', 'temp', '.tmp',
})

TS_EXTS = frozenset({'.ts', '.tsx', '.js', '.jsx'})
GO_EXTS = frozenset({'.go'})
SRC_EXTS = TS_EXTS | GO_EXTS

REGISTRY_HINTS = frozenset({'Map', 'Registry', 'Config', 'Schema', 'List'})
TEMPLATE_HINT = 'Template'

GENERIC_NAMES = frozenset({
    'data', 'params', 'result', 'error', 'value', 'key', 'item',
    'index', 'count', 'name', 'type', 'options', 'config', 'args',
    'props', 'state', 'context', 'callback', 'handler', 'dispatch',
    'resolve', 'reject', 'request', 'response', 'req', 'res',
})

TYPE_BONUS = frozenset({
    'enum', 'class', 'interface', 'function',
    'template', 'registry', 'switch_case',
})

# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────


def line_at(content, pos):
    """1-based line number for a character position."""
    return content[:pos].count('\n') + 1


def line_text(content, lineno):
    """Full text of a 1-based line."""
    return content.split('\n')[lineno - 1]


def eid(etype, path, name, lineno):
    """Deterministic entity ID."""
    return f"{etype}:{path}:{name}:{lineno}"


def _entity(etype, path, name, lineno, terms, evidence, **meta):
    """Build an entity dict."""
    e = {
        'id': eid(etype, path, name, lineno),
        'type': etype,
        'path': path,
        'name': name,
        'line': lineno,
        'terms': sorted({t for t in terms if t}),
        'evidence': evidence.strip(),
    }
    if meta:
        e['meta'] = meta
    return e


def _edge(from_id, to_id, etype, evidence):
    """Build an edge dict."""
    return {'from': from_id, 'to': to_id, 'type': etype, 'evidence': evidence}


def name_to_terms(name, extra=()):
    """Decompose an identifier into searchable terms."""
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
            if '_' in e:
                for seg in e.split('_'):
                    if len(seg) > 1:
                        terms.add(seg.lower())
    return terms


def enum_members(content, start):
    """Extract member names from an enum starting at *start* position."""
    text = content[start:]
    brace = text.find('{')
    if brace < 0:
        return []
    members = []
    for ln in text[brace + 1:].split('\n'):
        s = ln.strip()
        if s.startswith('}'):
            break
        if not s or s.startswith('//') or s.startswith('/*') or s.startswith('*'):
            continue
        m = re.match(r'(\w+)\s*[=,\n]', s)
        if m:
            members.append(m.group(1))
    return members


def switch_details(content, pos):
    """Return (cases, case->target pairs) from a switch at *pos*."""
    i = pos
    while i < len(content) and content[i] != '{':
        i += 1
    if i >= len(content):
        return [], []
    depth, j = 1, i + 1
    while j < len(content) and depth > 0:
        c = content[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif c in ('"', "'", '`'):
            q, j = c, j + 1
            while j < len(content) and content[j] != q:
                if content[j] == '\\':
                    j += 1
                j += 1
        j += 1
    block = content[i:j]
    cases = re.findall(r'case\s+([\w.]+)\s*:', block)
    targets = re.findall(
        r'case\s+([\w.]+)\s*:\s*\n?\s*(?:return\s+)?(\w+)\s*\(', block
    )
    return cases, targets


# ──────────────────────────────────────────
# Multi-line signature joining
# ──────────────────────────────────────────

_SIG_START_RE = re.compile(
    r'^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?'
    r'(?:async\s+)?(?:const|function|class|interface|type|enum)\s+\w+'
    r'|^func\s+'
    r'|^(?:export\s+)?const\s+\w+\s*=\s*(?:async\s+)?\('
)


def _bracket_balance(line):
    """Count net open brackets in a line, skipping string contents."""
    parens = 0
    angles = 0
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in ('"', "'", '`'):
            q = c
            i += 1
            while i < n and line[i] != q:
                if line[i] == '\\':
                    i += 1
                i += 1
            i += 1
            continue
        if c == '(':
            parens += 1
        elif c == ')':
            parens -= 1
        elif c == '<':
            if i + 1 < n and line[i + 1] not in ('=', ' '):
                angles += 1
        elif c == '>':
            if angles > 0:
                angles -= 1
        i += 1
    return parens + angles


def _join_multiline(content, max_continuation=10):
    """Join multi-line signatures into single lines for regex extraction.

    Returns (new_content, line_map) where line_map[new_lineno] = original_lineno.
    Both are 0-based.
    """
    lines = content.split('\n')
    out_lines = []
    line_map = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if (stripped.startswith('//') or stripped.startswith('/*')
                or stripped.startswith('*')):
            out_lines.append(line)
            line_map.append(i)
            i += 1
            continue

        if _SIG_START_RE.match(stripped):
            balance = _bracket_balance(line)
            if balance > 0:
                joined = line
                orig_i = i
                j = i + 1
                while j < len(lines) and j - i <= max_continuation and balance > 0:
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    joined = joined + ' ' + next_line
                    if len(joined) > 500:
                        joined = line
                        break
                    balance += _bracket_balance(next_line)
                    j += 1
                if joined != line:
                    out_lines.append(joined)
                    line_map.append(orig_i)
                    i = j
                    continue
        out_lines.append(line)
        line_map.append(i)
        i += 1
    return '\n'.join(out_lines), line_map


# ──────────────────────────────────────────
# File discovery
# ──────────────────────────────────────────


def discover(repo):
    """Return sorted list of source file paths under *repo*."""
    root = Path(repo).resolve()
    out = []
    for dirpath, dirs, files in os.walk(str(root)):
        dirs[:] = sorted(
            d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')
        )
        for f in sorted(files):
            if Path(f).suffix in SRC_EXTS:
                out.append(os.path.join(dirpath, f))
    return sorted(out)


# ──────────────────────────────────────────
# TS / JS extraction
# ──────────────────────────────────────────


def extract_ts(rel, content):
    # Pre-process: join multi-line signatures
    joined, line_map = _join_multiline(content)
    original_content = content
    content = joined

    def _orig_line(ln):
        """Map 1-based line in joined content to 1-based line in original."""
        idx = ln - 1
        if line_map and 0 <= idx < len(line_map):
            return line_map[idx] + 1
        return ln

    def _ln(pos):
        """1-based original line number for a character position in joined content."""
        return _orig_line(line_at(content, pos))

    def _ev(ln):
        """Evidence text from original content at a 1-based line number."""
        return line_text(original_content, ln)

    ents, edges, taken = [], [], set()

    # ── enum ──
    for m in re.finditer(r'^export\s+enum\s+(\w+)', content, re.MULTILINE):
        n, ln = m.group(1), _ln(m.start())
        members = enum_members(content, m.start())
        ents.append(
            _entity(
                'enum', rel, n, ln,
                name_to_terms(n, members),
                _ev(ln),
                members=members,
            )
        )
        taken.add(ln)

    # ── interface ──
    for m in re.finditer(
        r'^(export\s+)?interface\s+(\w+)', content, re.MULTILINE
    ):
        n, ln = m.group(2), _ln(m.start())
        if ln in taken:
            continue
        ents.append(
            _entity('interface', rel, n, ln, name_to_terms(n), _ev(ln))
        )
        taken.add(ln)

    # ── class ──
    for m in re.finditer(
        r'^(export\s+(?:default\s+)?(?:abstract\s+)?)?class\s+(\w+)',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), _ln(m.start())
        if ln in taken:
            continue
        meta = {}
        ext = re.search(r'extends\s+(\w+)', content[m.start():m.end() + 120])
        if ext:
            meta['extends'] = ext.group(1)
        ents.append(
            _entity('class', rel, n, ln, name_to_terms(n), _ev(ln), **meta)
        )
        taken.add(ln)

    # ── function (export const arrow) ──
    for m in re.finditer(
        r'^(export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), _ln(m.start())
        if ln in taken:
            continue
        et = 'template' if TEMPLATE_HINT in n else 'function'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), _ev(ln))
        )
        taken.add(ln)

    # ── function (declaration) ──
    for m in re.finditer(
        r'^(export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), _ln(m.start())
        if ln in taken:
            continue
        et = 'template' if TEMPLATE_HINT in n else 'function'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), _ev(ln))
        )
        taken.add(ln)

    # ── class method (indented) ──
    for m in re.finditer(
        r'^\s{2,}(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?(\w+)\s*\(',
        content, re.MULTILINE,
    ):
        n, ln = m.group(1), _ln(m.start())
        if ln in taken:
            continue
        if n in GENERIC_NAMES or n in (
            'if', 'for', 'while', 'switch', 'catch',
            'constructor', 'return', 'throw', 'new',
        ):
            continue
        ents.append(
            _entity('function', rel, n, ln, name_to_terms(n), _ev(ln).strip())
        )
        taken.add(ln)

    # ── const (non-function) ──
    for m in re.finditer(
        r'^(export\s+)?const\s+(\w+)', content, re.MULTILINE
    ):
        n, ln = m.group(2), _ln(m.start())
        if ln in taken:
            continue
        et = 'registry' if any(h in n for h in REGISTRY_HINTS) else 'const'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), _ev(ln))
        )
        taken.add(ln)

    # ── imports (named) ──
    for m in re.finditer(
        r"^import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        content, re.MULTILINE,
    ):
        names_raw, src = m.group(1), m.group(2)
        ln = _ln(m.start())
        for raw in names_raw.split(','):
            nm = raw.strip().split(' as ')[0].strip()
            if not nm:
                continue
            ents.append(
                _entity('import', rel, nm, ln, name_to_terms(nm, [src]),
                        m.group(0).strip(), source=src)
            )
            edges.append(
                _edge(eid('import', rel, nm, ln), src, 'IMPORTS',
                      f"imports {nm} from {src}")
            )
        taken.add(ln)

    # ── imports (default / wildcard) ──
    for m in re.finditer(
        r"^import\s+(?:\*\s+as\s+(\w+)|(\w+))\s+from\s+['\"]([^'\"]+)['\"]",
        content, re.MULTILINE,
    ):
        ln = _ln(m.start())
        if ln in taken:
            continue
        nm = m.group(1) or m.group(2)
        src = m.group(3)
        ents.append(
            _entity('import', rel, nm, ln, name_to_terms(nm, [src]),
                    m.group(0).strip(), source=src)
        )
        edges.append(
            _edge(eid('import', rel, nm, ln), src, 'IMPORTS',
                  f"imports {nm} from {src}")
        )
        taken.add(ln)

    # ── switch-case ──
    _func_lines = sorted(
        [(e['line'], e['name']) for e in ents if e['type'] in ('function', 'template')]
    )

    for m in re.finditer(r'\bswitch\s*\(([^)]+)\)', content):
        disc = m.group(1).strip()
        ln = _ln(m.start())
        if ln in taken:
            continue
        cases, targets = switch_details(content, m.start())
        if len(cases) < 2:
            continue
        sname = f"switch_{disc.replace('.', '_')}"
        terms = name_to_terms(sname, cases)
        enc_func = None
        for fl, fn in reversed(_func_lines):
            if fl <= ln:
                enc_func = fn
                break
        if enc_func:
            terms.update(name_to_terms(enc_func))
        ents.append(
            _entity(
                'switch_case', rel, sname, ln, terms,
                f"switch ({disc}) {{ ... }} // {len(cases)} cases",
                discriminant=disc, cases=cases,
                enclosing_function=enc_func,
            )
        )
        name_map = {e['name']: e['id'] for e in ents}
        for cv, tf in targets:
            tid = name_map.get(tf, tf)
            edges.append(
                _edge(eid('switch_case', rel, sname, ln), tid, 'REGISTERS',
                      f"{cv} -> {tf}()")
            )
        taken.add(ln)

    # ── references (function/template -> same-file entities) ──
    name_map = {e['name']: e['id'] for e in ents if e['type'] not in ('import',)}
    orig_lines = original_content.split('\n')
    for e in ents:
        if e['type'] not in ('function', 'template', 'class'):
            continue
        lo = max(0, e['line'] - 1)
        hi = min(len(orig_lines), e['line'] + 25)
        win = '\n'.join(orig_lines[lo:hi])
        seen = set()
        for other_name, other_id in name_map.items():
            if other_name == e['name'] or len(other_name) < 4:
                continue
            if other_name in GENERIC_NAMES:
                continue
            if other_id == e['id']:
                continue
            if re.search(r'\b' + re.escape(other_name) + r'\b', win):
                key = (e['id'], other_id)
                if key not in seen:
                    edges.append(
                        _edge(e['id'], other_id, 'REFERENCES',
                              f"{e['name']} references {other_name}")
                    )
                    seen.add(key)

    return ents, edges


# ──────────────────────────────────────────
# Go extraction
# ──────────────────────────────────────────


def extract_go(rel, content):
    joined, line_map = _join_multiline(content)
    original_content = content
    content = joined

    def _ln(pos):
        idx = line_at(content, pos) - 1
        if line_map and 0 <= idx < len(line_map):
            return line_map[idx] + 1
        return idx + 1

    def _ev(ln):
        return line_text(original_content, ln)

    ents, edges, taken = [], [], set()

    # functions
    for m in re.finditer(
        r'^func\s+(?:\([^)]+\)\s*)?(\w+)\s*\(', content, re.MULTILINE
    ):
        n, ln = m.group(1), _ln(m.start())
        ents.append(
            _entity('function', rel, n, ln, name_to_terms(n), _ev(ln))
        )
        taken.add(ln)

    # struct -> class
    for m in re.finditer(r'^type\s+(\w+)\s+struct\b', content, re.MULTILINE):
        n, ln = m.group(1), _ln(m.start())
        ents.append(
            _entity('class', rel, n, ln, name_to_terms(n), _ev(ln))
        )

    # interface
    for m in re.finditer(r'^type\s+(\w+)\s+interface\b', content, re.MULTILINE):
        n, ln = m.group(1), _ln(m.start())
        ents.append(
            _entity('interface', rel, n, ln, name_to_terms(n), _ev(ln))
        )

    # const blocks
    for m in re.finditer(
        r'^const\s*\(([^)]+)\)', content, re.MULTILINE | re.DOTALL
    ):
        ln = _ln(m.start())
        for cm in re.finditer(r'(\w+)\s*=', m.group(1)):
            ents.append(
                _entity('const', rel, cm.group(1), ln,
                        name_to_terms(cm.group(1)),
                        f"const {cm.group(1)} = ...")
            )
        taken.add(ln)

    # single const
    for m in re.finditer(r'^const\s+(\w+)\s*=', content, re.MULTILINE):
        ln = _ln(m.start())
        if ln in taken:
            continue
        ents.append(
            _entity('const', rel, m.group(1), ln,
                    name_to_terms(m.group(1)), _ev(ln))
        )

    # import blocks
    for m in re.finditer(
        r'^import\s*\(([^)]+)\)', content, re.MULTILINE | re.DOTALL
    ):
        ln = _ln(m.start())
        for cm in re.finditer(r'"([^"]+)"', m.group(1)):
            imp = cm.group(1)
            nm = imp.split('/')[-1]
            ents.append(
                _entity('import', rel, nm, ln, {nm, imp},
                        f'import "{imp}"', source=imp)
            )

    # single imports
    for m in re.finditer(r'^import\s+"([^"]+)"', content, re.MULTILINE):
        ln = _ln(m.start())
        if ln in taken:
            continue
        imp = m.group(1)
        nm = imp.split('/')[-1]
        ents.append(
            _entity('import', rel, nm, ln, {nm, imp},
                    f'import "{imp}"', source=imp)
        )

    return ents, edges


# ──────────────────────────────────────────
# Inverted index
# ──────────────────────────────────────────


def inverted_index(entities):
    idx = defaultdict(list)
    for e in entities:
        for t in e.get('terms', []):
            idx[t.lower()].append(e['id'])
    return {k: sorted(set(v)) for k, v in sorted(idx.items())}


# ──────────────────────────────────────────
# Cross-file edge resolution
# ──────────────────────────────────────────


def _build_module_map(entities):
    """Build module_key → [entity_ids] mapping for import resolution."""
    module_map = defaultdict(list)
    for ent in entities:
        if ent['type'] in ('file', 'import'):
            continue
        path = ent['path']
        module_key = path.rsplit('.', 1)[0]
        module_map[module_key].append(ent['id'])
        if module_key.startswith('src/'):
            module_map[module_key[4:]].append(ent['id'])
    return dict(module_map)


def _resolve_import_path(source, importer_path):
    """Resolve a relative import path to an absolute module key."""
    if source.startswith('.'):
        importer_dir = os.path.dirname(importer_path)
        resolved = os.path.normpath(os.path.join(importer_dir, source))
        return resolved.replace('\\', '/')
    if source.startswith('@/'):
        return 'src/' + source[2:]
    return None


def _resolve_edges(entities, edges):
    """Resolve IMPORTS edges to concrete entity IDs. Returns new RESOLVED_IMPORT edges."""
    module_map = _build_module_map(entities)
    by_id = {e['id']: e for e in entities}

    entity_by_module_name = {}
    for ent in entities:
        if ent['type'] in ('file', 'import'):
            continue
        key = ent['path'].rsplit('.', 1)[0]
        entity_by_module_name[(key, ent['name'])] = ent['id']
        if key.startswith('src/'):
            entity_by_module_name[(key[4:], ent['name'])] = ent['id']

    resolved_edges = []
    for edge in edges:
        if edge['type'] != 'IMPORTS':
            continue
        from_id = edge['from']
        import_source = edge['to']

        importer = by_id.get(from_id)
        if not importer or importer['type'] != 'import':
            continue
        importer_path = importer['path']
        imported_name = importer['name']

        resolved_key = _resolve_import_path(import_source, importer_path)
        if not resolved_key:
            continue

        target_id = entity_by_module_name.get((resolved_key, imported_name))

        if not target_id:
            # Try index.ts barrel file
            index_key = resolved_key + '/index'
            target_id = entity_by_module_name.get((index_key, imported_name))

        if not target_id:
            # Try matching by name in the module's entities
            candidates = module_map.get(resolved_key, [])
            for cid in candidates:
                cand = by_id.get(cid)
                if cand and cand['name'] == imported_name:
                    target_id = cid
                    break

        if not target_id:
            # Barrel: check index file for re-exports
            index_key = resolved_key + '/index'
            index_ents = [
                by_id[eid_] for eid_ in module_map.get(index_key, [])
                if by_id.get(eid_, {}).get('type') == 'import'
                and by_id.get(eid_, {}).get('name') == imported_name
            ]
            for ie in index_ents:
                sub_source = ie.get('meta', {}).get('source', '')
                if sub_source:
                    sub_key = _resolve_import_path(sub_source, index_key + '.ts')
                    if sub_key:
                        target_id = entity_by_module_name.get((sub_key, imported_name))
                        if target_id:
                            break

        if target_id and target_id != from_id:
            resolved_edges.append(_edge(
                from_id, target_id, 'RESOLVED_IMPORT',
                f"{imported_name}: {import_source} -> {target_id}"
            ))

    return resolved_edges


# ──────────────────────────────────────────
# Output
# ──────────────────────────────────────────


def write_json(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


# ──────────────────────────────────────────
# Query
# ──────────────────────────────────────────


def _path_segments(path):
    """Extract lowercased path segments (dirs + stem)."""
    segs = set()
    for seg in path.split('/'):
        segs.add(seg.lower())
        if '.' in seg:
            segs.add(seg.rsplit('.', 1)[0].lower())
    return segs


def query_index(index_dir, query_str):
    """Query the evidence index and print top 10 scored results.

    Scoring (deterministic, explainable):
        exact name match  = +10
        term match        = +3  (per matched query term)
        path segment match = +2 (per matched query term)
        entity type bonus = +1  (enum/class/interface/function/template/registry/switch_case)
    """
    idx_path = Path(index_dir).resolve()
    entities = json.loads(
        (idx_path / 'entities.json').read_text(encoding='utf-8')
    )
    inv_idx = json.loads(
        (idx_path / 'inverted-index.json').read_text(encoding='utf-8')
    )
    by_id = {e['id']: e for e in entities}

    q_lower = query_str.lower()
    q_terms = {t.lower() for t in name_to_terms(query_str)}

    # Collect candidates from inverted index
    candidate_ids = set()
    for qt in q_terms:
        candidate_ids.update(inv_idx.get(qt, []))

    # Score candidates
    results = []
    for cid in candidate_ids:
        ent = by_id.get(cid)
        if not ent:
            continue
        score = 0
        matched = []

        # Exact name match: +10
        if ent['name'].lower() == q_lower:
            score += 10
            matched.append(f"exact:{ent['name']}")

        # Term matches: +3 each
        ent_terms_l = {t.lower() for t in ent.get('terms', [])}
        for qt in sorted(q_terms):
            if qt in ent_terms_l:
                score += 3
                matched.append(f"term:{qt}")

        # Path segment matches: +2 each
        path_segs = _path_segments(ent['path'])
        for qt in sorted(q_terms):
            if qt in path_segs:
                score += 2
                matched.append(f"path:{qt}")

        # Entity type bonus: +1
        if ent['type'] in TYPE_BONUS:
            score += 1

        if score > 0:
            results.append({
                'score': score,
                'id': ent['id'],
                'type': ent['type'],
                'name': ent['name'],
                'path': ent['path'],
                'line': ent.get('line', 0),
                'matched_terms': sorted(set(matched)),
            })

    results.sort(key=lambda r: (-r['score'], r['id']))
    top = results[:10]

    # Print
    print(
        f"\nQuery: {query_str} | "
        f"{len(candidate_ids)} candidates, {len(results)} scored, top {len(top)}\n"
    )
    for i, r in enumerate(top, 1):
        loc = f"{r['path']}:{r['line']}" if r['line'] else r['path']
        print(f"  #{i:<2} score={r['score']:<3} "
              f"type={r['type']:<12} "
              f"symbol={r['name']}")
        print(f"       path: {loc}")
        print(f"       matched: {', '.join(r['matched_terms'][:8])}")
    if not top:
        print("  (no results)")
    print()


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────


def build_index(repo_str, out_str, full=False):
    """Build evidence index from a repository."""
    repo = Path(repo_str).resolve()
    out = Path(out_str).resolve()
    out.mkdir(parents=True, exist_ok=True)

    files = discover(repo)
    print(f"Scanning {len(files)} source files ...")

    mode = 'full'
    all_ents, all_edges, file_hashes = None, None, None

    # Attempt incremental build
    if not full:
        existing = _load_existing_index(out)
        if existing:
            old_ents, old_edges, old_hashes = existing
            if old_hashes:
                try:
                    all_ents, all_edges, file_hashes = _incremental_build(
                        repo, files, old_ents, old_edges, old_hashes
                    )
                    mode = 'incremental'
                except Exception as e:
                    print(f"  Incremental failed ({e}), falling back to full rebuild")
                    all_ents, all_edges, file_hashes = None, None, None

    if all_ents is None:
        all_ents, all_edges, file_hashes = _full_build(repo, files)
        mode = 'full'

    # Cross-file edge resolution
    resolved = _resolve_edges(all_ents, all_edges)
    all_edges.extend(resolved)
    if resolved:
        print(f"  Resolved {len(resolved)} cross-file import edges")

    # Deterministic output ordering
    all_ents.sort(key=lambda e: e['id'])
    all_edges.sort(key=lambda e: (e['from'], e['to'], e['type']))

    inv = inverted_index(all_ents)

    _write_manifest(out, str(repo), len(files), len(all_ents), len(all_edges),
                    file_hashes, mode)
    write_json(out / 'entities.json', all_ents)
    write_json(out / 'edges.json', all_edges)
    write_json(out / 'inverted-index.json', inv)

    print(f"Done ({mode}) -> {out}/")
    print(f"  entities.json       ({len(all_ents)} entities)")
    print(f"  edges.json          ({len(all_edges)} edges)")
    print(f"  inverted-index.json ({len(inv)} terms)")


def _full_build(repo, files):
    """Full extraction of all files."""
    all_ents, all_edges = [], []
    file_hashes = {}

    for fp in files:
        rel = os.path.relpath(fp, str(repo))
        file_hashes[rel] = _compute_file_hash(fp)
        try:
            src = Path(fp).read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if not src.strip():
            continue

        stem = Path(rel).stem
        f_ent = _entity(
            'file', rel, Path(rel).name, 0,
            name_to_terms(stem, [str(Path(rel).parent)]), rel,
        )
        all_ents.append(f_ent)

        ext = Path(fp).suffix
        if ext in TS_EXTS:
            ents, edges = extract_ts(rel, src)
        elif ext in GO_EXTS:
            ents, edges = extract_go(rel, src)
        else:
            continue

        for e in ents:
            all_edges.append(
                _edge(f_ent['id'], e['id'], 'DEFINES',
                      f"{Path(rel).name} defines {e['name']}")
            )
        all_ents.extend(ents)
        all_edges.extend(edges)

    return all_ents, all_edges, file_hashes


def _incremental_build(repo, files, existing_ents, existing_edges, old_hashes):
    """Incremental build: only re-extract changed/new files."""
    new_hashes = {}
    changed_files = []

    for fp in files:
        rel = os.path.relpath(fp, str(repo))
        h = _compute_file_hash(fp)
        new_hashes[rel] = h
        if old_hashes.get(rel) != h:
            changed_files.append(fp)

    current_rels = {os.path.relpath(fp, str(repo)) for fp in files}
    deleted_rels = set(old_hashes.keys()) - current_rels

    if not changed_files and not deleted_rels:
        print("  No changes detected. Index is up to date.")
        # Strip old RESOLVED_IMPORT edges (will be regenerated)
        clean_edges = [e for e in existing_edges if e['type'] != 'RESOLVED_IMPORT']
        return existing_ents, clean_edges, new_hashes

    print(f"  Changed/new: {len(changed_files)}, deleted: {len(deleted_rels)}")

    # Remove entities/edges from changed and deleted files
    remove_paths = {os.path.relpath(fp, str(repo)) for fp in changed_files} | deleted_rels
    retained_ents = [e for e in existing_ents if e['path'] not in remove_paths]
    retained_ent_ids = {e['id'] for e in retained_ents}
    retained_edges = [
        e for e in existing_edges
        if e['type'] != 'RESOLVED_IMPORT' and e['from'] in retained_ent_ids
    ]

    # Re-extract changed files
    new_ents, new_edges = [], []
    for fp in changed_files:
        rel = os.path.relpath(fp, str(repo))
        try:
            src = Path(fp).read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if not src.strip():
            continue

        stem = Path(rel).stem
        f_ent = _entity(
            'file', rel, Path(rel).name, 0,
            name_to_terms(stem, [str(Path(rel).parent)]), rel,
        )
        new_ents.append(f_ent)

        ext = Path(fp).suffix
        if ext in TS_EXTS:
            ents, edges = extract_ts(rel, src)
        elif ext in GO_EXTS:
            ents, edges = extract_go(rel, src)
        else:
            continue

        for e in ents:
            new_edges.append(
                _edge(f_ent['id'], e['id'], 'DEFINES',
                      f"{Path(rel).name} defines {e['name']}")
            )
        new_ents.extend(ents)
        new_edges.extend(edges)

    all_ents = retained_ents + new_ents
    all_edges = retained_edges + new_edges
    return all_ents, all_edges, new_hashes


def _compute_file_hash(filepath):
    """SHA-256 hash of file content."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_existing_index(out_dir):
    """Load existing index. Returns (entities, edges, file_hashes) or None."""
    try:
        ents_path = out_dir / 'entities.json'
        edges_path = out_dir / 'edges.json'
        manifest_path = out_dir / 'manifest.yaml'
        if not ents_path.exists() or not manifest_path.exists():
            return None
        ents = json.loads(ents_path.read_text(encoding='utf-8'))
        edges = json.loads(edges_path.read_text(encoding='utf-8')) if edges_path.exists() else []
        manifest_text = manifest_path.read_text(encoding='utf-8')
        file_hashes = {}
        in_hashes = False
        for line in manifest_text.split('\n'):
            if line.strip() == 'file_hashes:':
                in_hashes = True
                continue
            if in_hashes:
                if line.startswith('  '):
                    parts = line.strip().split(': ', 1)
                    if len(parts) == 2:
                        file_hashes[parts[0]] = parts[1]
                else:
                    in_hashes = False
        return ents, edges, file_hashes
    except Exception:
        return None


def _write_manifest(d, repo, nfiles, nents, nedges, file_hashes, mode='full'):
    import datetime
    lines = [
        "# Evidence Index Manifest",
        f"repo: {repo}",
        f"generated_at: '{datetime.datetime.now().isoformat()}'",
        f"files_scanned: {nfiles}",
        f"entities: {nents}",
        f"edges: {nedges}",
        f"generator: build-index.py v2.0.0",
        f"build_mode: {mode}",
        "file_hashes:",
    ]
    for path in sorted(file_hashes.keys()):
        lines.append(f"  {path}: {file_hashes[path]}")
    (d / 'manifest.yaml').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(
        description='Evidence Index: build (--repo/--out) or query (--query/--index)'
    )
    ap.add_argument('--repo', help='Repository root path (build mode)')
    ap.add_argument('--out', help='Output directory (build mode)')
    ap.add_argument('--full', action='store_true',
                    help='Force full rebuild (skip incremental)')
    ap.add_argument('--query', help='Query string (query mode)')
    ap.add_argument('--index', help='Index directory (query mode)')
    args = ap.parse_args()

    if args.query:
        if not args.index:
            ap.error('--index is required with --query')
        query_index(args.index, args.query)
    elif args.repo:
        if not args.out:
            ap.error('--out is required with --repo')
        build_index(args.repo, args.out, full=args.full)
    else:
        ap.error('Provide --repo/--out (build) or --query/--index (query)')


if __name__ == '__main__':
    main()
