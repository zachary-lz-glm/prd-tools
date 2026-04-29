#!/usr/bin/env python3
"""Create deterministic PRD ingestion artifacts for prd-distill.

This script intentionally uses only the Python standard library. It is not a
full OCR/layout engine; it provides a stable local baseline and makes any
unread image/layout risk explicit for the downstream AI workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
SUPPORTED_TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
SUPPORTED_DOC_SUFFIXES = SUPPORTED_TEXT_SUFFIXES | {".docx", ".pdf"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = Path(value).stem.lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    return value or "prd"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_dirs(out_dir: Path) -> None:
    for name in ["tables", "media"]:
        (out_dir / name).mkdir(parents=True, exist_ok=True)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def attr(element: ET.Element, namespace: str, name: str) -> Optional[str]:
    return element.attrib.get(f"{{{namespace}}}{name}")


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_yaml(path: Path, data: Any) -> None:
    path.write_text(render_yaml(data), encoding="utf-8")


def render_yaml(data: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(render_yaml(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{prefix}[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.append(render_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.append(render_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{yaml_scalar(data)}"


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        name = local_name(node.tag)
        if name == "t":
            parts.append(node.text or "")
        elif name == "tab":
            parts.append("\t")
        elif name in {"br", "cr"}:
            parts.append("\n")
    text = "".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraph_style(paragraph: ET.Element) -> Optional[str]:
    style = paragraph.find("./w:pPr/w:pStyle", NS)
    if style is None:
        return None
    return attr(style, NS["w"], "val")


def heading_prefix(style: Optional[str]) -> str:
    if not style:
        return ""
    normalized = style.lower()
    match = re.search(r"(?:heading|title|标题)\s*([1-6])", normalized)
    if match:
        return "#" * int(match.group(1)) + " "
    if normalized in {"title", "标题"}:
        return "# "
    return ""


def paragraph_image_rids(paragraph: ET.Element) -> list[str]:
    rids: list[str] = []
    for blip in paragraph.findall(".//a:blip", NS):
        rid = attr(blip, NS["r"], "embed") or attr(blip, NS["r"], "link")
        if rid:
            rids.append(rid)
    return rids


def cell_text(cell: ET.Element) -> str:
    texts: list[str] = []
    for paragraph in cell.findall(".//w:p", NS):
        text = paragraph_text(paragraph)
        if text:
            texts.append(text)
    return "<br>".join(texts).strip()


def table_to_rows(table: ET.Element) -> tuple[list[list[str]], list[str]]:
    rows: list[list[str]] = []
    warnings: list[str] = []
    for row in table.findall("./w:tr", NS):
        cells: list[str] = []
        for cell in row.findall("./w:tc", NS):
            if cell.find(".//w:gridSpan", NS) is not None:
                warnings.append("merged horizontal cells detected")
            if cell.find(".//w:vMerge", NS) is not None:
                warnings.append("merged vertical cells detected")
            cells.append(cell_text(cell))
        if cells:
            rows.append(cells)
    return rows, sorted(set(warnings))


def escape_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def rows_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    lines = [
        "| " + " | ".join(escape_md_cell(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    for row in padded[1:]:
        lines.append("| " + " | ".join(escape_md_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def read_relationships(docx: zipfile.ZipFile) -> dict[str, str]:
    rel_path = "word/_rels/document.xml.rels"
    if rel_path not in docx.namelist():
        return {}
    root = ET.fromstring(docx.read(rel_path))
    rels: dict[str, str] = {}
    for rel in root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        rel_type = rel.attrib.get("Type")
        target = rel.attrib.get("Target")
        if rel_id and rel_type == IMAGE_REL and target:
            rels[rel_id] = target
    return rels


def normalize_docx_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("word", target))


def extract_media(docx: zipfile.ZipFile, out_dir: Path, rels: dict[str, str]) -> dict[str, dict[str, Any]]:
    media_dir = out_dir / "media"
    media_by_zip: dict[str, dict[str, Any]] = {}
    rel_to_zip = {rid: normalize_docx_target(target) for rid, target in rels.items()}
    candidate_paths = sorted(
        set(path for path in docx.namelist() if path.startswith("word/media/"))
        | set(rel_to_zip.values())
    )

    counter = 1
    for zip_path in candidate_paths:
        if zip_path not in docx.namelist():
            continue
        suffix = Path(zip_path).suffix.lower() or ".bin"
        media_id = f"IMG-{counter:03d}"
        filename = f"{media_id}{suffix}"
        output_path = media_dir / filename
        output_path.write_bytes(docx.read(zip_path))
        media_by_zip[zip_path] = {
            "id": media_id,
            "source_path": zip_path,
            "output_path": str(output_path.relative_to(out_dir)),
            "filename": filename,
            "mime_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
            "size_bytes": output_path.stat().st_size,
            "referenced_by": [],
        }
        counter += 1

    for rid, zip_path in rel_to_zip.items():
        if zip_path in media_by_zip:
            media_by_zip[zip_path]["relationship_id"] = rid
    return media_by_zip


def parse_docx(source: Path, out_dir: Path) -> dict[str, Any]:
    warnings: list[str] = []
    with zipfile.ZipFile(source) as docx:
        if "word/document.xml" not in docx.namelist():
            raise ValueError("word/document.xml not found in docx")
        rels = read_relationships(docx)
        media_by_zip = extract_media(docx, out_dir, rels)
        rel_to_media = {
            rid: media_by_zip[normalize_docx_target(target)]
            for rid, target in rels.items()
            if normalize_docx_target(target) in media_by_zip
        }
        root = ET.fromstring(docx.read("word/document.xml"))

    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("w:body not found in docx")

    blocks: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    md_lines: list[str] = []
    table_count = 0
    paragraph_count = 0

    for child in body:
        name = local_name(child.tag)
        if name == "p":
            text = paragraph_text(child)
            rids = paragraph_image_rids(child)
            media_ids: list[str] = []
            for rid in rids:
                media = rel_to_media.get(rid)
                if media:
                    media_ids.append(media["id"])
            if not text and not media_ids:
                continue
            paragraph_count += 1
            block_id = f"BLK-{len(blocks) + 1:04d}"
            style = paragraph_style(child)
            locator = f"docx:paragraph:{paragraph_count}"
            markdown = f"{heading_prefix(style)}{text}" if text else ""
            if markdown:
                md_lines.append(f"<!-- {block_id} -->")
                md_lines.append(markdown)
                md_lines.append("")
            for media_id in media_ids:
                md_lines.append(f"<!-- {block_id}:{media_id} -->")
                md_lines.append(f"![{media_id}](media/{media_id}{Path(next(m['filename'] for m in media_by_zip.values() if m['id'] == media_id)).suffix})")
                md_lines.append("")
                for media in media_by_zip.values():
                    if media["id"] == media_id:
                        media["referenced_by"].append(block_id)
                        break
            blocks.append(
                {
                    "id": block_id,
                    "type": "paragraph",
                    "locator": locator,
                    "style": style,
                    "text": text,
                    "media_ids": media_ids,
                }
            )
            evidence_items.append(
                {
                    "id": f"PRD-{len(evidence_items) + 1:03d}",
                    "kind": "prd_block",
                    "block_id": block_id,
                    "locator": locator,
                    "summary": text[:180],
                    "confidence": "high" if text else "low",
                }
            )
        elif name == "tbl":
            table_count += 1
            rows, table_warnings = table_to_rows(child)
            warnings.extend(f"table {table_count}: {item}" for item in table_warnings)
            table_id = f"TBL-{table_count:03d}"
            block_id = f"BLK-{len(blocks) + 1:04d}"
            locator = f"docx:table:{table_count}"
            markdown = rows_to_markdown(rows)
            table_path = out_dir / "tables" / f"{table_id}.md"
            table_path.write_text(markdown + "\n", encoding="utf-8")
            md_lines.append(f"<!-- {block_id}:{table_id} -->")
            md_lines.append(markdown)
            md_lines.append("")
            blocks.append(
                {
                    "id": block_id,
                    "type": "table",
                    "locator": locator,
                    "table_id": table_id,
                    "rows": len(rows),
                    "columns": max((len(row) for row in rows), default=0),
                    "path": str(table_path.relative_to(out_dir)),
                    "warnings": table_warnings,
                }
            )
            evidence_items.append(
                {
                    "id": f"PRD-{len(evidence_items) + 1:03d}",
                    "kind": "prd_table",
                    "block_id": block_id,
                    "locator": locator,
                    "summary": f"{len(rows)} rows table",
                    "confidence": "medium" if table_warnings else "high",
                }
            )

    media_items = sorted(media_by_zip.values(), key=lambda item: item["id"])
    if media_items:
        warnings.append("images extracted but image text/diagram semantics require vision or human review")

    return {
        "format": "docx",
        "document_markdown": "\n".join(md_lines).strip() + "\n",
        "structure": {
            "schema_version": "1.0",
            "source_type": "docx",
            "blocks": blocks,
            "stats": {
                "paragraphs": paragraph_count,
                "tables": table_count,
                "media": len(media_items),
            },
        },
        "evidence_items": evidence_items,
        "media_items": media_items,
        "warnings": sorted(set(warnings)),
    }


def parse_text_document(source: Path, out_dir: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8", errors="replace")
    blocks: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    current_heading = ""
    table_count = 0
    image_refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip()
        block_id = f"BLK-{len(blocks) + 1:04d}"
        block_type = "table_row" if stripped.startswith("|") and stripped.endswith("|") else "paragraph"
        if block_type == "table_row":
            table_count += 1
        blocks.append(
            {
                "id": block_id,
                "type": block_type,
                "locator": f"line:{idx}",
                "heading": current_heading,
                "text": stripped,
            }
        )
        evidence_items.append(
            {
                "id": f"PRD-{len(evidence_items) + 1:03d}",
                "kind": "prd_block",
                "block_id": block_id,
                "locator": f"line:{idx}",
                "summary": stripped[:180],
                "confidence": "high",
            }
        )

    warnings = []
    media_items = []
    for idx, ref in enumerate(image_refs, start=1):
        media_items.append(
            {
                "id": f"IMG-{idx:03d}",
                "source_path": ref,
                "output_path": "",
                "mime_type": "",
                "size_bytes": None,
                "referenced_by": [],
            }
        )
    if media_items:
        warnings.append("markdown image references detected but image semantics require vision or human review")

    return {
        "format": "markdown" if source.suffix.lower() in {".md", ".markdown"} else "text",
        "document_markdown": text if text.endswith("\n") else text + "\n",
        "structure": {
            "schema_version": "1.0",
            "source_type": source.suffix.lower().lstrip(".") or "text",
            "blocks": blocks,
            "stats": {
                "paragraphs": len([b for b in blocks if b["type"] == "paragraph"]),
                "tables": table_count,
                "media": len(media_items),
            },
        },
        "evidence_items": evidence_items,
        "media_items": media_items,
        "warnings": warnings,
    }


def parse_pdf(source: Path, out_dir: Path) -> dict[str, Any]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("PDF ingestion requires pdftotext or a dedicated layout/OCR service")
    result = subprocess.run(
        [pdftotext, "-layout", str(source), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    temp = out_dir / ".pdf-extracted.txt"
    temp.write_text(result.stdout, encoding="utf-8")
    parsed = parse_text_document(temp, out_dir)
    parsed["format"] = "pdf_text"
    parsed["warnings"].append("pdf converted by pdftotext; tables/images/reading order require review")
    temp.unlink(missing_ok=True)
    return parsed


def quality_status(warnings: list[str], media_items: list[dict[str, Any]], block_count: int) -> tuple[str, list[str]]:
    gates: list[str] = []
    status = "pass"
    if block_count == 0:
        status = "block"
        gates.append("no readable text blocks extracted")
    if media_items:
        status = "warn" if status == "pass" else status
        gates.append("images require vision or human review before using image-only requirements")
    if warnings:
        status = "warn" if status == "pass" else status
    return status, gates


def conversion_warnings_text(warnings: list[str], gates: list[str]) -> str:
    if not warnings and not gates:
        return "# Conversion Warnings\n\nNo conversion warnings.\n"
    lines = ["# Conversion Warnings", ""]
    for item in warnings:
        lines.append(f"- {item}")
    for item in gates:
        lines.append(f"- quality gate: {item}")
    lines.append("")
    return "\n".join(lines)


def source_manifest(source: Path, source_format: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "source": {
            "path": str(source),
            "filename": source.name,
            "format": source_format,
            "size_bytes": source.stat().st_size,
            "sha256": sha256_file(source),
        },
        "ingestion": {
            "tool": "prd-distill/scripts/ingest_prd.py",
            "mode": "local_baseline",
            "ocr": "not_available",
        },
    }


def run(source: Path, out_dir: Path) -> int:
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_DOC_SUFFIXES:
        raise ValueError(f"unsupported PRD format: {suffix}")

    ensure_dirs(out_dir)
    if suffix == ".docx":
        parsed = parse_docx(source, out_dir)
    elif suffix == ".pdf":
        parsed = parse_pdf(source, out_dir)
    else:
        parsed = parse_text_document(source, out_dir)

    blocks = parsed["structure"]["blocks"]
    warnings = list(parsed["warnings"])
    media_items = list(parsed["media_items"])
    status, gates = quality_status(warnings, media_items, len(blocks))

    (out_dir / "document.md").write_text(parsed["document_markdown"], encoding="utf-8")
    (out_dir / "document-structure.json").write_text(
        json.dumps(parsed["structure"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_yaml(
        out_dir / "source-manifest.yaml",
        source_manifest(source, parsed["format"]),
    )
    write_yaml(
        out_dir / "evidence-map.yaml",
        {
            "schema_version": "1.0",
            "items": parsed["evidence_items"],
        },
    )
    write_yaml(
        out_dir / "media-analysis.yaml",
        {
            "schema_version": "1.0",
            "items": [
                {
                    **item,
                    "analysis_status": "needs_vision_or_human_review",
                    "summary": "",
                    "confidence": "low",
                }
                for item in media_items
            ],
        },
    )
    write_yaml(
        out_dir / "extraction-quality.yaml",
        {
            "schema_version": "1.0",
            "status": status,
            "stats": parsed["structure"]["stats"],
            "quality_gates": gates,
            "warnings": warnings,
            "rules": [
                "Do not infer requirements from images unless media-analysis has human or vision evidence.",
                "Do not use table content with merged-cell warnings as high confidence without review.",
                "Every downstream requirement must cite evidence-map item ids or stronger evidence.",
            ],
        },
    )
    (out_dir / "conversion-warnings.md").write_text(
        conversion_warnings_text(warnings, gates),
        encoding="utf-8",
    )

    print(str(out_dir))
    return 0 if status != "block" else 2


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Ingest a PRD document into stable artifacts.")
    parser.add_argument("source", help="Path to PRD docx/md/txt/pdf")
    parser.add_argument(
        "--out",
        help="Output directory. Default: _output/prd-distill/<slug>/prd-ingest",
    )
    args = parser.parse_args(argv)

    source = Path(args.source)
    out_dir = Path(args.out) if args.out else Path("_output") / "prd-distill" / slugify(source.name) / "prd-ingest"
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        return run(source, out_dir)
    except Exception as exc:
        ensure_dirs(out_dir)
        write_yaml(
            out_dir / "extraction-quality.yaml",
            {
                "schema_version": "1.0",
                "status": "block",
                "error": str(exc),
                "rules": [
                    "Ask the user for a markdown/text export or use a dedicated layout/OCR service.",
                ],
            },
        )
        (out_dir / "conversion-warnings.md").write_text(
            f"# Conversion Warnings\n\n- ingestion failed: {exc}\n",
            encoding="utf-8",
        )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
