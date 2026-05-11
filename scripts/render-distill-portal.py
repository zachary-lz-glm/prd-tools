#!/usr/bin/env python3
"""
render-distill-portal.py — Render distill portal.html from fixed template.

Usage:
    python3 scripts/render-distill-portal.py \
      --distill-dir _prd-tools/distill/<slug> \
      --template .prd-tools/assets/distill-portal-template.html \
      --out _prd-tools/distill/<slug>/portal.html
"""

import argparse
import html
import re
import sys
from datetime import datetime
from pathlib import Path

TABS = [
    ('overview', '概览'),
    ('afprd', 'AI-friendly PRD'),
    ('requirements', '需求'),
    ('anchors', '代码锚点'),
    ('risks', '风险与问题'),
    ('report', '报告'),
    ('plan', '方案'),
    ('raw', '原始上下文'),
]

CONTEXT_FILES = [
    'prd-quality-report.yaml',
    'requirement-ir.yaml',
    'layer-impact.yaml',
    'graph-context.md',
    'contract-delta.yaml',
    'readiness-report.yaml',
    'questions.md',
    'query-plan.yaml',
    'context-pack.md',
    'final-quality-gate.yaml',
]


def _read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def _esc(text):
    return html.escape(text, quote=True)


def _yaml_field(text, field_name):
    m = re.search(rf'^{re.escape(field_name)}:\s*["\']?(.+?)["\']?\s*$', text, re.M)
    return m.group(1).strip() if m else ''


def _yaml_field_int(text, field_name):
    m = re.search(rf'^{re.escape(field_name)}:\s*(\d+)', text, re.M)
    return int(m.group(1)) if m else 0


def _file_exists_nonempty(path):
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def _badge(status):
    cls = {'pass': 'badge-pass', 'warning': 'badge-warn', 'fail': 'badge-fail'}.get(status, 'badge-info')
    return f'<span class="value badge {cls}">{_esc(status)}</span>'


def _md_to_html(text):
    """Minimal markdown to HTML for display."""
    if not text:
        return '<p style="color:#999">文件缺失或为空</p>'
    lines = text.split('\n')
    out = []
    for line in lines:
        if line.startswith('### '):
            out.append(f'<h3>{_esc(line[4:])}</h3>')
        elif line.startswith('## '):
            out.append(f'<h2>{_esc(line[3:])}</h2>')
        elif line.startswith('# '):
            out.append(f'<h1>{_esc(line[2:])}</h1>')
        elif line.startswith('- ') or line.startswith('* '):
            out.append(f'<li>{_esc(line[2:])}</li>')
        else:
            out.append(f'<p>{_esc(line)}</p>')
    return '\n'.join(out)


def extract_quality_report(base):
    text = _read(base / 'context' / 'prd-quality-report.yaml')
    return {
        'status': _yaml_field(text, 'status') or '-',
        'score': _yaml_field_int(text, 'score'),
    }


def extract_requirement_ir(base):
    text = _read(base / 'context' / 'requirement-ir.yaml')
    ai_prd_count = len(re.findall(r'ai_prd_req_id:', text))
    ready = len(re.findall(r'eligibility:\s*ready', text))
    assumption = len(re.findall(r'eligibility:\s*assumption_only', text))
    blocked = len(re.findall(r'eligibility:\s*blocked', text))
    return {
        'ai_prd_req_count': ai_prd_count,
        'ready': ready,
        'assumption': assumption,
        'blocked': blocked,
    }


def extract_layer_impact(base):
    text = _read(base / 'context' / 'layer-impact.yaml')
    anchor_count = len(re.findall(r'code_anchors:', text))
    fallback_count = len(re.findall(r'fallback:', text)) + len(re.findall(r'fallback_reason:', text))
    return {
        'anchor_count': anchor_count,
        'fallback_count': fallback_count,
    }


def extract_final_gate(base):
    text = _read(base / 'context' / 'final-quality-gate.yaml')
    return {
        'status': _yaml_field(text, 'status') or '-',
        'score': _yaml_field_int(text, 'score'),
    }


def build_nav():
    links = []
    for tab_id, label in TABS:
        links.append(f'<a data-tab="sec-{tab_id}" onclick="showTab(\'sec-{tab_id}\')">{_esc(label)}</a>')
    return ' '.join(links)


def build_summary_cards(quality, req_ir, impact, gate):
    cards = []
    cards.append(f'''<div class="card"><div class="label">PRD 质量</div>{_badge(quality["status"])}<div class="value" style="font-size:14px;margin-top:4px">分数: {quality["score"]}</div></div>''')
    cards.append(f'''<div class="card"><div class="label">需求数</div><div class="value">{req_ir["ai_prd_req_count"]}</div></div>''')
    cards.append(f'''<div class="card"><div class="label">就绪/假设/阻塞</div><div class="value" style="font-size:16px"><span class="tag tag-ready">{req_ir["ready"]}</span> <span class="tag tag-assumption">{req_ir["assumption"]}</span> <span class="tag tag-blocked">{req_ir["blocked"]}</span></div></div>''')
    cards.append(f'''<div class="card"><div class="label">代码锚点</div><div class="value"><span class="tag tag-anchor">{impact["anchor_count"]}</span> <span class="tag tag-fallback">{impact["fallback_count"]} fallback</span></div></div>''')
    cards.append(f'''<div class="card"><div class="label">Final Gate</div>{_badge(gate["status"])}<div class="value" style="font-size:14px;margin-top:4px">分数: {gate["score"]}</div></div>''')
    return '\n'.join(cards)


def build_overview_section(base, quality, req_ir, impact, gate):
    rows = []
    checks = [
        ('spec/ai-friendly-prd.md', 'AI-friendly PRD', _file_exists_nonempty(base / 'spec' / 'ai-friendly-prd.md')),
        ('report.md', '分析报告', _file_exists_nonempty(base / 'report.md')),
        ('plan.md', '技术方案', _file_exists_nonempty(base / 'plan.md')),
        ('context/requirement-ir.yaml', '需求 IR', _file_exists_nonempty(base / 'context' / 'requirement-ir.yaml')),
        ('context/layer-impact.yaml', '层级影响', _file_exists_nonempty(base / 'context' / 'layer-impact.yaml')),
        ('context/final-quality-gate.yaml', '质量门禁', _file_exists_nonempty(base / 'context' / 'final-quality-gate.yaml')),
    ]
    for fname, label, exists in checks:
        cls = 'badge-pass' if exists else 'badge-fail'
        rows.append(f'<tr><td>{_esc(fname)}</td><td>{_esc(label)}</td><td><span class="value badge {cls}">{"存在" if exists else "缺失"}</span></td></tr>')

    return f'''<div class="section active" id="sec-overview">
        <h2>概览</h2>
        <table><tr><th>文件</th><th>说明</th><th>状态</th></tr>{"".join(rows)}</table>
    </div>'''


def build_afprd_section(base):
    text = _read(base / 'spec' / 'ai-friendly-prd.md')
    if not text:
        return f'''<div class="section" id="sec-afprd"><h2>AI-friendly PRD</h2><p>文件缺失</p></div>'''
    return f'''<div class="section" id="sec-afprd">
        <h2>AI-friendly PRD</h2>
        <div class="md-content">{_md_to_html(text[:30000])}</div>
        <details><summary>原始内容</summary><pre>{_esc(text[:100000])}</pre></details>
    </div>'''


def build_requirements_section(base, req_ir):
    text = _read(base / 'context' / 'requirement-ir.yaml')
    if not text:
        return f'''<div class="section" id="sec-requirements"><h2>需求</h2><p>文件缺失</p></div>'''

    keys = re.findall(r'^(\w[\w_-]*):\s*(.+)$', text, re.M)
    rows = []
    for key, val in keys[:40]:
        rows.append(f'<tr><td><code>{_esc(key)}</code></td><td>{_esc(val.strip()[:100])}</td></tr>')

    stats = f'''<table style="margin-bottom:16px"><tr><th>ai_prd_req_id 数</th><th>Ready</th><th>Assumption</th><th>Blocked</th></tr>
        <tr><td>{req_ir["ai_prd_req_count"]}</td><td>{req_ir["ready"]}</td><td>{req_ir["assumption"]}</td><td>{req_ir["blocked"]}</td></tr></table>'''

    return f'''<div class="section" id="sec-requirements">
        <h2>需求</h2>{stats}
        <table><tr><th>字段</th><th>值</th></tr>{"".join(rows)}</table>
        <details><summary>原始内容</summary><pre>{_esc(text[:50000])}</pre></details>
    </div>'''


def build_anchors_section(base, impact):
    text = _read(base / 'context' / 'layer-impact.yaml')
    if not text:
        return f'''<div class="section" id="sec-anchors"><h2>代码锚点</h2><p>文件缺失</p></div>'''

    keys = re.findall(r'^(\w[\w_-]*):\s*(.+)$', text, re.M)
    rows = []
    for key, val in keys[:40]:
        rows.append(f'<tr><td><code>{_esc(key)}</code></td><td>{_esc(val.strip()[:100])}</td></tr>')

    stats = f'''<table style="margin-bottom:16px"><tr><th>code_anchors</th><th>fallback</th></tr>
        <tr><td>{impact["anchor_count"]}</td><td>{impact["fallback_count"]}</td></tr></table>'''

    return f'''<div class="section" id="sec-anchors">
        <h2>代码锚点</h2>{stats}
        <table><tr><th>字段</th><th>值</th></tr>{"".join(rows)}</table>
        <details><summary>原始内容</summary><pre>{_esc(text[:50000])}</pre></details>
    </div>'''


def build_risks_section(base):
    text = _read(base / 'context' / 'questions.md')
    if not text:
        text = '(无 questions.md)'
    return f'''<div class="section" id="sec-risks">
        <h2>风险与问题</h2>
        <div class="md-content">{_md_to_html(text[:20000])}</div>
        <details><summary>原始内容</summary><pre>{_esc(text[:50000])}</pre></details>
    </div>'''


def build_report_section(base):
    text = _read(base / 'report.md')
    if not text:
        return f'''<div class="section" id="sec-report"><h2>报告</h2><p>文件缺失</p></div>'''
    return f'''<div class="section" id="sec-report">
        <h2>报告</h2>
        <div class="md-content">{_md_to_html(text[:30000])}</div>
        <details><summary>原始内容</summary><pre>{_esc(text[:100000])}</pre></details>
    </div>'''


def build_plan_section(base):
    text = _read(base / 'plan.md')
    if not text:
        return f'''<div class="section" id="sec-plan"><h2>方案</h2><p>文件缺失</p></div>'''
    return f'''<div class="section" id="sec-plan">
        <h2>方案</h2>
        <div class="md-content">{_md_to_html(text[:30000])}</div>
        <details><summary>原始内容</summary><pre>{_esc(text[:100000])}</pre></details>
    </div>'''


def build_raw_section(base):
    viewers = []
    # spec
    spec_files = [('spec/ai-friendly-prd.md', 'AI-friendly PRD')]
    for fname, label in spec_files:
        text = _read(base / fname)
        if text:
            viewers.append(f'''<details><summary>{_esc(fname)} — {_esc(label)}</summary><pre>{_esc(text[:100000])}</pre></details>''')
    # context
    for fname in CONTEXT_FILES:
        text = _read(base / 'context' / fname)
        if text:
            viewers.append(f'''<details><summary>context/{_esc(fname)}</summary><pre>{_esc(text[:50000])}</pre></details>''')
        else:
            viewers.append(f'''<details><summary>context/{_esc(fname)} (缺失)</summary><pre></pre></details>''')

    return f'''<div class="section" id="sec-raw">
        <h2>原始上下文</h2>
        <input type="text" id="rawSearch" class="search-box" placeholder="搜索文件内容..." oninput="searchRaw()">
        <div id="raw-context" style="margin-top:12px">{"".join(viewers)}</div>
    </div>'''


def render(distill_dir, template_path, out_path):
    base = Path(distill_dir).resolve()
    template = _read(template_path)
    if not template:
        print(f'Error: template not found: {template_path}', file=sys.stderr)
        sys.exit(1)

    quality = extract_quality_report(base)
    req_ir = extract_requirement_ir(base)
    impact = extract_layer_impact(base)
    gate = extract_final_gate(base)

    nav = build_nav()
    cards = build_summary_cards(quality, req_ir, impact, gate)

    sections = []
    sections.append(build_overview_section(base, quality, req_ir, impact, gate))
    sections.append(build_afprd_section(base))
    sections.append(build_requirements_section(base, req_ir))
    sections.append(build_anchors_section(base, impact))
    sections.append(build_risks_section(base))
    sections.append(build_report_section(base))
    sections.append(build_plan_section(base))
    sections.append(build_raw_section(base))

    generated_at = f'由 render-distill-portal.py 生成 — {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    slug = base.name
    result = template
    result = result.replace('{{TITLE}}', _esc(f'{slug} — Distill Portal'))
    result = result.replace('{{NAV}}', nav)
    result = result.replace('{{SUMMARY_CARDS}}', cards)
    result = result.replace('{{SECTIONS}}', '\n'.join(sections))
    result = result.replace('{{GENERATED_AT}}', _esc(generated_at))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding='utf-8')
    print(f'Rendered: {out_path} ({len(result):,} bytes)')


def main():
    ap = argparse.ArgumentParser(description='Render distill portal.html from fixed template')
    ap.add_argument('--distill-dir', required=True, help='Path to distill output directory')
    ap.add_argument('--template', required=True, help='Path to portal template HTML')
    ap.add_argument('--out', required=True, help='Output path for portal.html')
    args = ap.parse_args()
    render(args.distill_dir, args.template, args.out)


if __name__ == '__main__':
    main()