#!/usr/bin/env python3
"""Ingest a docx PRD file into _ingest/ with document.md, media/, structure.json, manifests.

Usage:
    python3 scripts/ingest-docx.py --input path/to/prd.docx --output _prd-tools/distill/<slug>
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
}


def _extract_paragraphs(xml_path):
    """Extract paragraphs and tables from document.xml, return markdown text."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    lines = []
    for body in root.findall('.//w:body', NS):
        for child in body:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'p':
                texts = []
                for t in child.findall('.//w:t', NS):
                    if t.text:
                        texts.append(t.text)
                line = ''.join(texts).strip()
                if line:
                    # Detect heading style
                    pPr = child.find('w:pPr', NS)
                    if pPr is not None:
                        pStyle = pPr.find('w:pStyle', NS)
                        if pStyle is not None:
                            val = pStyle.get(f"{{{NS['w']}}}val", "")
                            if 'Heading1' in val or 'heading 1' in val.lower():
                                line = f"# {line}"
                            elif 'Heading2' in val or 'heading 2' in val.lower():
                                line = f"## {line}"
                            elif 'Heading3' in val or 'heading 3' in val.lower():
                                line = f"### {line}"
                    lines.append(line)
            elif tag == 'tbl':
                rows = child.findall('.//w:tr', NS)
                table_lines = []
                for i, row in enumerate(rows):
                    cells = []
                    for cell in row.findall('.//w:tc', NS):
                        cell_texts = []
                        for t in cell.findall('.//w:t', NS):
                            if t.text:
                                cell_texts.append(t.text)
                        cells.append(''.join(cell_texts).strip())
                    table_lines.append('| ' + ' | '.join(cells) + ' |')
                    if i == 0:
                        table_lines.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
                if table_lines:
                    lines.append('')
                    lines.extend(table_lines)
                    lines.append('')
    return '\n'.join(lines)


def _extract_image_rels(rels_path):
    """Extract image relationship mappings from document.xml.rels."""
    if not os.path.isfile(rels_path):
        return {}
    tree = ET.parse(rels_path)
    root = tree.getroot()
    mapping = {}
    for rel in root:
        rid = rel.get('Id', '')
        target = rel.get('Target', '')
        rel_type = rel.get('Type', '')
        if 'image' in target.lower() or 'image' in rel_type.lower():
            mapping[rid] = target
    return mapping


def _copy_media(docx_tmp, media_out):
    """Copy media files from extracted docx to output media directory."""
    media_out.mkdir(parents=True, exist_ok=True)
    count = 0
    # Try word/media/ first, then top-level media/
    for prefix in ['word/media/', 'media/']:
        src_dir = docx_tmp / prefix
        if src_dir.is_dir():
            for f in src_dir.iterdir():
                if f.is_file():
                    dest = media_out / f.name
                    shutil.copy2(f, dest)
                    count += 1
    return count


def _compute_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def main():
    ap = argparse.ArgumentParser(description='Ingest docx PRD into _ingest/')
    ap.add_argument('--input', required=True, help='Path to .docx file')
    ap.add_argument('--output', '--distill-dir', dest='output', required=True,
                    help='Distill directory (writes to <output>/_ingest/)')
    args = ap.parse_args()

    src = Path(args.input).resolve()
    out_base = Path(args.output).resolve()
    ingest_dir = out_base / '_ingest'
    media_dir = ingest_dir / 'media'

    if not src.is_file():
        print(f'Error: {src} not found', file=sys.stderr)
        sys.exit(1)

    ingest_dir.mkdir(parents=True, exist_ok=True)

    # Extract docx (zip)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        docx_tmp = Path(tmp)
        with zipfile.ZipFile(src) as z:
            z.extractall(docx_tmp)

        # Fix permissions
        for f in docx_tmp.rglob('*'):
            try:
                os.chmod(f, 0o644)
            except OSError:
                pass

        # Extract text
        doc_xml = docx_tmp / 'word' / 'document.xml'
        if doc_xml.is_file():
            markdown = _extract_paragraphs(str(doc_xml))
        else:
            markdown = f"# Error: word/document.xml not found in {src.name}"

        # Copy media
        media_count = _copy_media(docx_tmp, media_dir)

        # Extract image rels
        rels_path = docx_tmp / 'word' / '_rels' / 'document.xml.rels'
        image_rels = _extract_image_rels(str(rels_path))

    # Write outputs
    (ingest_dir / 'document.md').write_text(markdown, encoding='utf-8')

    # document-structure.json
    structure = {
        'media_files': sorted(str(f.name) for f in media_dir.iterdir() if f.is_file()),
        'image_relationships': image_rels,
        'paragraph_count': markdown.count('\n') + 1,
    }
    (ingest_dir / 'document-structure.json').write_text(
        json.dumps(structure, indent=2, ensure_ascii=False), encoding='utf-8')

    # source-manifest.yaml
    manifest = f"""file_hash: "{_compute_hash(src)}"
file_name: "{src.name}"
file_size: {src.stat().st_size}
media_count: {media_count}
extraction_method: "zipfile"
"""
    (ingest_dir / 'source-manifest.yaml').write_text(manifest, encoding='utf-8')

    # extraction-quality.yaml
    quality = f"""status: {'pass' if markdown.strip() else 'warn'}
text_completeness: {'high' if len(markdown) > 200 else 'low'}
image_extraction_status: {'pass' if media_count > 0 else 'no_images'}
media_count: {media_count}
"""
    (ingest_dir / 'extraction-quality.yaml').write_text(quality, encoding='utf-8')

    print(f'Ingested: {src.name}')
    print(f'  document.md: {len(markdown)} chars')
    print(f'  media/: {media_count} files')
    print(f'  output: {ingest_dir}')


if __name__ == '__main__':
    main()
