#!/usr/bin/env python3
"""
render-reference-portal.py — Render reference portal.html from fixed template.

Reads reference YAML/MD files, extracts lightweight summaries, and renders
a self-contained portal.html using a fixed HTML template.

Usage:
    python3 scripts/render-reference-portal.py \
      --root . \
      --template .prd-tools/assets/reference-portal-template.html \
      --out _prd-tools/reference/portal.html
"""

import argparse
import html
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────
# Config
# ──────────────────────────────────────────

REF_FILES = [
    ('00-portal.md', '概览'),
    ('project-profile.yaml', '项目概况'),
    ('01-codebase.yaml', '代码库'),
    ('02-coding-rules.yaml', '编码规则'),
    ('03-contracts.yaml', '接口契约'),
    ('04-routing-playbooks.yaml', '路由手册'),
    ('05-domain.yaml', '领域模型'),
]

INDEX_FILES = [
    ('index/entities.json', '实体索引'),
    ('index/edges.json', '关系索引'),
    ('index/inverted-index.json', '倒排索引'),
    ('index/manifest.yaml', '索引元数据'),
]

TABS = [
    ('overview', '概览'),
    ('codebase', '代码库'),
    ('contracts', '接口契约'),
    ('routing', '路由手册'),
    ('domain', '领域模型'),
    ('evidence', 'Evidence Index'),
    ('raw', '原始文件'),
]


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _esc(text):
    return html.escape(text, quote=True)


def _yaml_field(text, field_name):
    """Extract a simple top-level YAML field value (string/number)."""
    m = re.search(rf'^{re.escape(field_name)}:\s*["\']?(.+?)["\']?\s*$', text, re.M)
    return m.group(1).strip() if m else ''


def _yaml_field_int(text, field_name):
    """Extract a YAML integer field."""
    m = re.search(rf'^{re.escape(field_name)}:\s*(\d+)', text, re.M)
    return int(m.group(1)) if m else 0


def _file_size(path):
    try:
        return Path(path).stat().st_size
    except Exception:
        return 0


def _badge(status):
    cls = {'pass': 'badge-pass', 'warning': 'badge-warn', 'fail': 'badge-fail'}.get(status, 'badge-info')
    return f'<span class="value badge {cls}">{_esc(status)}</span>'


# ──────────────────────────────────────────
# Data extraction
# ──────────────────────────────────────────

def extract_profile(ref_dir):
    """Extract project profile summary."""
    text = _read(ref_dir / 'project-profile.yaml')
    return {
        'project': _yaml_field(text, 'project') or _yaml_field(text, 'name') or '-',
        'layer': _yaml_field(text, 'layer') or '-',
        'owner': _yaml_field(text, 'owner') or '-',
        'status': _yaml_field(text, 'status') or '-',
        'schema_version': _yaml_field(text, 'schema_version') or '-',
    }


def extract_index_manifest(ref_dir):
    """Extract index manifest stats."""
    text = _read(ref_dir / 'index' / 'manifest.yaml')
    return {
        'entity_count': _yaml_field_int(text, 'entity_count'),
        'edge_count': _yaml_field_int(text, 'edge_count'),
        'term_count': _yaml_field_int(text, 'term_count'),
        'build_time': _yaml_field(text, 'build_time') or '-',
        'schema_version': _yaml_field(text, 'schema_version') or '-',
    }


def extract_file_summaries(ref_dir):
    """Extract lightweight summaries from each reference file."""
    summaries = {}
    for fname, label in REF_FILES:
        path = ref_dir / fname
        text = _read(path)
        size = _file_size(path)
        sv = _yaml_field(text, 'schema_version') if fname.endswith('.yaml') else '-'
        summaries[fname] = {
            'label': label,
            'exists': bool(text),
            'size': size,
            'schema_version': sv or '-',
        }
    return summaries


# ──────────────────────────────────────────
# HTML builders
# ──────────────────────────────────────────

def build_nav():
    links = []
    for tab_id, label in TABS:
        links.append(f'<a data-tab="sec-{tab_id}" onclick="showTab(\'sec-{tab_id}\')">{_esc(label)}</a>')
    return ' '.join(links)


def build_summary_cards(profile, manifest, file_summaries):
    ref_count = sum(1 for s in file_summaries.values() if s['exists'])
    total = len(file_summaries)
    idx_ok = manifest['entity_count'] > 0

    cards = []
    cards.append(f'''<div class="card"><div class="label">项目</div><div class="value">{_esc(profile["project"])}</div></div>''')
    cards.append(f'''<div class="card"><div class="label">层级</div><div class="value">{_esc(profile["layer"])}</div></div>''')
    cards.append(f'''<div class="card"><div class="label">Reference 文件</div><div class="value">{ref_count}/{total}</div></div>''')
    cards.append(f'''<div class="card"><div class="label">Evidence Index</div><div class="value">{"{:,}".format(manifest["entity_count"])} 实体</div></div>''')
    cards.append(f'''<div class="card"><div class="label">生成时间</div><div class="value" style="font-size:14px">{_esc(datetime.now().strftime("%Y-%m-%d %H:%M"))}</div></div>''')
    return '\n'.join(cards)


def build_overview_section(profile, file_summaries):
    rows = []
    for fname, info in file_summaries.items():
        status_cls = 'badge-pass' if info['exists'] else 'badge-fail'
        rows.append(f'''<tr>
            <td>{_esc(fname)}</td>
            <td>{_esc(info['label'])}</td>
            <td><span class="tag tag-type">{_esc(info['schema_version'])}</span></td>
            <td><span class="value badge {status_cls}">{"存在" if info["exists"] else "缺失"}</span></td>
            <td>{info["size"]:,} B</td>
        </tr>''')

    return f'''<div class="section active" id="sec-overview">
        <h2>概览</h2>
        <table>
            <tr><th>文件</th><th>说明</th><th>schema_version</th><th>状态</th><th>大小</th></tr>
            {"".join(rows)}
        </table>
    </div>'''


def build_yaml_section(ref_dir, fname, title):
    """Build a section showing a YAML file's key fields and raw viewer."""
    text = _read(ref_dir / fname)
    if not text:
        return f'''<div class="section" id="sec-{title.lower().replace(" ","-")}">
            <h2>{_esc(title)}</h2><p>文件缺失或为空</p></div>'''

    # Extract top-level keys for summary table
    keys = re.findall(r'^(\w[\w_-]*):\s*(.+)$', text, re.M)
    rows = []
    for key, val in keys[:30]:  # limit to 30 fields
        val_display = val.strip()[:80]
        rows.append(f'<tr><td><code>{_esc(key)}</code></td><td>{_esc(val_display)}</td></tr>')

    raw_id = f'raw-{fname.replace("/","-").replace(".","-")}'

    return f'''<div class="section" id="sec-{title.lower().replace(" ","-")}">
        <h2>{_esc(title)}</h2>
        <table><tr><th>字段</th><th>值</th></tr>{"".join(rows)}</table>
        <details id="{raw_id}"><summary>原始内容</summary><pre>{_esc(text)}</pre></details>
    </div>'''


def build_evidence_section(manifest, ref_dir):
    """Build Evidence Index section."""
    idx_path = ref_dir / 'index'
    idx_files_info = []
    for fname, label in INDEX_FILES:
        path = idx_path / fname.split('/')[-1] if '/' in fname else idx_path / fname
        # Fix: index files are directly under index/
        actual_fname = fname.split('/')[-1]
        actual_path = idx_path / actual_fname
        text = _read(actual_path)
        size = _file_size(actual_path)
        idx_files_info.append((actual_fname, label, bool(text), size, text))

    rows = []
    for fname, label, exists, size, _ in idx_files_info:
        status_cls = 'badge-pass' if exists else 'badge-fail'
        rows.append(f'''<tr>
            <td>{_esc(fname)}</td>
            <td>{_esc(label)}</td>
            <td><span class="value badge {status_cls}">{"存在" if exists else "缺失"}</span></td>
            <td>{size:,} B</td>
        </tr>''')

    # Manifest stats
    stats_rows = ''
    if manifest['entity_count'] > 0:
        stats_rows = f'''<table style="margin-bottom:16px">
            <tr><th>实体数</th><th>边数</th><th>Term 数</th><th>构建时间</th></tr>
            <tr><td>{"{:,}".format(manifest["entity_count"])}</td><td>{"{:,}".format(manifest["edge_count"])}</td>
            <td>{"{:,}".format(manifest["term_count"])}</td><td>{_esc(manifest["build_time"])}</td></tr>
        </table>'''

    # Raw viewers for index files
    raw_viewers = ''
    for fname, label, exists, size, text in idx_files_info:
        if exists:
            raw_viewers += f'''<details><summary>{_esc(fname)} ({label})</summary><pre>{_esc(text[:50000])}</pre></details>'''

    return f'''<div class="section" id="sec-evidence">
        <h2>Evidence Index</h2>
        {stats_rows}
        <table><tr><th>文件</th><th>说明</th><th>状态</th><th>大小</th></tr>{"".join(rows)}</table>
        {raw_viewers}
    </div>'''


def build_raw_section(ref_dir):
    """Build raw files viewer section."""
    viewers = []
    all_files = list(REF_FILES) + INDEX_FILES
    for fname, label in all_files:
        if '/' in fname:
            path = ref_dir / fname
        else:
            path = ref_dir / fname
        text = _read(path)
        if text:
            viewers.append(f'''<details><summary>{_esc(fname)} — {_esc(label)}</summary><pre>{_esc(text[:100000])}</pre></details>''')
        else:
            viewers.append(f'''<details><summary>{_esc(fname)} — {_esc(label)} (缺失)</summary><pre></pre></details>''')

    return f'''<div class="section" id="sec-raw">
        <h2>原始文件</h2>
        <input type="text" id="rawSearch" class="search-box" placeholder="搜索文件内容..." oninput="searchRaw()">
        <div id="raw-files" style="margin-top:12px">{"".join(viewers)}</div>
    </div>'''


# ──────────────────────────────────────────
# Main render
# ──────────────────────────────────────────

def render(root, template_path, out_path):
    ref_dir = Path(root) / '_prd-tools' / 'reference'
    template = _read(template_path)
    if not template:
        print(f'Error: template not found: {template_path}', file=sys.stderr)
        sys.exit(1)

    profile = extract_profile(ref_dir)
    manifest = extract_index_manifest(ref_dir)
    file_summaries = extract_file_summaries(ref_dir)

    # Build components
    nav = build_nav()
    cards = build_summary_cards(profile, manifest, file_summaries)

    sections = []
    sections.append(build_overview_section(profile, file_summaries))
    sections.append(build_yaml_section(ref_dir, '01-codebase.yaml', '代码库'))
    sections.append(build_yaml_section(ref_dir, '03-contracts.yaml', '接口契约'))
    sections.append(build_yaml_section(ref_dir, '04-routing-playbooks.yaml', '路由手册'))
    sections.append(build_yaml_section(ref_dir, '05-domain.yaml', '领域模型'))
    sections.append(build_evidence_section(manifest, ref_dir))
    sections.append(build_raw_section(ref_dir))

    generated_at = f'由 render-reference-portal.py 生成 — {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    # Replace placeholders
    result = template
    result = result.replace('{{TITLE}}', _esc(f'{profile["project"]} — Reference Portal'))
    result = result.replace('{{NAV}}', nav)
    result = result.replace('{{SUMMARY_CARDS}}', cards)
    result = result.replace('{{SECTIONS}}', '\n'.join(sections))
    result = result.replace('{{GENERATED_AT}}', _esc(generated_at))

    # Write output
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding='utf-8')
    print(f'Rendered: {out_path} ({len(result):,} bytes)')


def main():
    ap = argparse.ArgumentParser(description='Render reference portal.html from fixed template')
    ap.add_argument('--root', required=True, help='Project root directory')
    ap.add_argument('--template', required=True, help='Path to portal template HTML')
    ap.add_argument('--out', required=True, help='Output path for portal.html')
    args = ap.parse_args()

    render(args.root, args.template, args.out)


if __name__ == '__main__':
    main()