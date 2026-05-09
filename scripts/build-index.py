#!/usr/bin/env python3
"""
build-index.py — Evidence Index MVP

Regex-based code scanner that produces a lightweight evidence index.
Supports TypeScript, JavaScript, and Go.

Usage:
    python3 scripts/build-index.py --repo /path/to/repo --out /path/to/output

Output:
    manifest.yaml        — index metadata
    entities.json        — all discovered code entities
    edges.json           — relationships between entities
    inverted-index.json  — term → entity lookup
"""

import argparse
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
    ents, edges, taken = [], [], set()

    # ── enum ──
    for m in re.finditer(r'^export\s+enum\s+(\w+)', content, re.MULTILINE):
        n, ln = m.group(1), line_at(content, m.start())
        members = enum_members(content, m.start())
        ents.append(
            _entity(
                'enum', rel, n, ln,
                name_to_terms(n, members),
                line_text(content, ln),
                members=members,
            )
        )
        taken.add(ln)

    # ── interface ──
    for m in re.finditer(
        r'^(export\s+)?interface\s+(\w+)', content, re.MULTILINE
    ):
        n, ln = m.group(2), line_at(content, m.start())
        if ln in taken:
            continue
        ents.append(
            _entity('interface', rel, n, ln, name_to_terms(n),
                    line_text(content, ln))
        )
        taken.add(ln)

    # ── class ──
    for m in re.finditer(
        r'^(export\s+(?:default\s+)?(?:abstract\s+)?)?class\s+(\w+)',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), line_at(content, m.start())
        if ln in taken:
            continue
        meta = {}
        ext = re.search(r'extends\s+(\w+)', content[m.start():m.end() + 120])
        if ext:
            meta['extends'] = ext.group(1)
        ents.append(
            _entity('class', rel, n, ln, name_to_terms(n),
                    line_text(content, ln), **meta)
        )
        taken.add(ln)

    # ── function (export const arrow) ──
    for m in re.finditer(
        r'^(export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), line_at(content, m.start())
        if ln in taken:
            continue
        et = 'template' if TEMPLATE_HINT in n else 'function'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), line_text(content, ln))
        )
        taken.add(ln)

    # ── function (declaration) ──
    for m in re.finditer(
        r'^(export\s+(?:default\s+)?)?function\s+(\w+)',
        content, re.MULTILINE,
    ):
        n, ln = m.group(2), line_at(content, m.start())
        if ln in taken:
            continue
        et = 'template' if TEMPLATE_HINT in n else 'function'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), line_text(content, ln))
        )
        taken.add(ln)

    # ── class method (indented) ──
    for m in re.finditer(
        r'^\s{2,}(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?(\w+)\s*\(',
        content, re.MULTILINE,
    ):
        n, ln = m.group(1), line_at(content, m.start())
        if ln in taken:
            continue
        if n in GENERIC_NAMES or n in (
            'if', 'for', 'while', 'switch', 'catch',
            'constructor', 'return', 'throw', 'new',
        ):
            continue
        ents.append(
            _entity('function', rel, n, ln, name_to_terms(n),
                    line_text(content, ln).strip())
        )
        taken.add(ln)

    # ── const (non-function) ──
    for m in re.finditer(
        r'^(export\s+)?const\s+(\w+)', content, re.MULTILINE
    ):
        n, ln = m.group(2), line_at(content, m.start())
        if ln in taken:
            continue
        et = 'registry' if any(h in n for h in REGISTRY_HINTS) else 'const'
        ents.append(
            _entity(et, rel, n, ln, name_to_terms(n), line_text(content, ln))
        )
        taken.add(ln)

    # ── imports (named) ──
    for m in re.finditer(
        r"^import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        content, re.MULTILINE,
    ):
        names_raw, src = m.group(1), m.group(2)
        ln = line_at(content, m.start())
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
        ln = line_at(content, m.start())
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
    # Detect enclosing function for each switch to link dispatcher to caller
    _func_lines = sorted(
        [(e['line'], e['name']) for e in ents if e['type'] in ('function', 'template')]
    )

    for m in re.finditer(r'\bswitch\s*\(([^)]+)\)', content):
        disc = m.group(1).strip()
        ln = line_at(content, m.start())
        if ln in taken:
            continue
        cases, targets = switch_details(content, m.start())
        if len(cases) < 2:
            continue
        sname = f"switch_{disc.replace('.', '_')}"
        terms = name_to_terms(sname, cases)
        # Find the enclosing function name and add it to terms
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
        # resolve target function names to entity IDs where possible
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
    lines = content.split('\n')
    for e in ents:
        if e['type'] not in ('function', 'template', 'class'):
            continue
        lo = max(0, e['line'] - 1)
        hi = min(len(lines), e['line'] + 25)
        win = '\n'.join(lines[lo:hi])
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
    ents, edges, taken = [], [], set()

    # functions
    for m in re.finditer(
        r'^func\s+(?:\([^)]+\)\s*)?(\w+)\s*\(', content, re.MULTILINE
    ):
        n, ln = m.group(1), line_at(content, m.start())
        ents.append(
            _entity('function', rel, n, ln, name_to_terms(n),
                    line_text(content, ln))
        )
        taken.add(ln)

    # struct -> class
    for m in re.finditer(r'^type\s+(\w+)\s+struct\b', content, re.MULTILINE):
        n, ln = m.group(1), line_at(content, m.start())
        ents.append(
            _entity('class', rel, n, ln, name_to_terms(n),
                    line_text(content, ln))
        )

    # interface
    for m in re.finditer(r'^type\s+(\w+)\s+interface\b', content, re.MULTILINE):
        n, ln = m.group(1), line_at(content, m.start())
        ents.append(
            _entity('interface', rel, n, ln, name_to_terms(n),
                    line_text(content, ln))
        )

    # const blocks
    for m in re.finditer(
        r'^const\s*\(([^)]+)\)', content, re.MULTILINE | re.DOTALL
    ):
        ln = line_at(content, m.start())
        for cm in re.finditer(r'(\w+)\s*=', m.group(1)):
            ents.append(
                _entity('const', rel, cm.group(1), ln,
                        name_to_terms(cm.group(1)),
                        f"const {cm.group(1)} = ...")
            )
        taken.add(ln)

    # single const
    for m in re.finditer(r'^const\s+(\w+)\s*=', content, re.MULTILINE):
        ln = line_at(content, m.start())
        if ln in taken:
            continue
        ents.append(
            _entity('const', rel, m.group(1), ln,
                    name_to_terms(m.group(1)), line_text(content, ln))
        )

    # import blocks
    for m in re.finditer(
        r'^import\s*\(([^)]+)\)', content, re.MULTILINE | re.DOTALL
    ):
        ln = line_at(content, m.start())
        for cm in re.finditer(r'"([^"]+)"', m.group(1)):
            imp = cm.group(1)
            nm = imp.split('/')[-1]
            ents.append(
                _entity('import', rel, nm, ln, {nm, imp},
                        f'import "{imp}"', source=imp)
            )

    # single imports
    for m in re.finditer(r'^import\s+"([^"]+)"', content, re.MULTILINE):
        ln = line_at(content, m.start())
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
# Output
# ──────────────────────────────────────────


def write_manifest(d, repo, nfiles, nents, nedges):
    import datetime

    (d / 'manifest.yaml').write_text(
        f"# Evidence Index Manifest\n"
        f"repo: {repo}\n"
        f"generated_at: '{datetime.datetime.now().isoformat()}'\n"
        f"files_scanned: {nfiles}\n"
        f"entities: {nents}\n"
        f"edges: {nedges}\n"
        f"generator: build-index.py v1.0.0\n",
        encoding='utf-8',
    )


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


def build_index(repo_str, out_str):
    """Build evidence index from a repository."""
    repo = Path(repo_str).resolve()
    out = Path(out_str).resolve()
    out.mkdir(parents=True, exist_ok=True)

    files = discover(repo)
    print(f"Scanning {len(files)} source files ...")

    all_ents, all_edges = [], []

    for fp in files:
        rel = os.path.relpath(fp, str(repo))
        try:
            src = Path(fp).read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if not src.strip():
            continue

        # file entity
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

        # DEFINES edges: file -> each entity it contains
        for e in ents:
            all_edges.append(
                _edge(f_ent['id'], e['id'], 'DEFINES',
                      f"{Path(rel).name} defines {e['name']}")
            )
        all_ents.extend(ents)
        all_edges.extend(edges)

    inv = inverted_index(all_ents)

    write_manifest(out, str(repo), len(files), len(all_ents), len(all_edges))
    write_json(out / 'entities.json', all_ents)
    write_json(out / 'edges.json', all_edges)
    write_json(out / 'inverted-index.json', inv)

    print(f"Done -> {out}/")
    print(f"  entities.json       ({len(all_ents)} entities)")
    print(f"  edges.json          ({len(all_edges)} edges)")
    print(f"  inverted-index.json ({len(inv)} terms)")


def main():
    ap = argparse.ArgumentParser(
        description='Evidence Index: build (--repo/--out) or query (--query/--index)'
    )
    ap.add_argument('--repo', help='Repository root path (build mode)')
    ap.add_argument('--out', help='Output directory (build mode)')
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
        build_index(args.repo, args.out)
    else:
        ap.error('Provide --repo/--out (build) or --query/--index (query)')


if __name__ == '__main__':
    main()
