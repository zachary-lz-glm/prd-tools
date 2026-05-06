# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "markitdown[all]",
#     "markitdown-ocr",
#     "openai",
# ]
# ///
#!/usr/bin/env python3
"""Create deterministic PRD ingestion artifacts for prd-distill.

Uses MarkItDown (microsoft/markitdown) as the conversion backend for
docx/pdf/pptx/xlsx/html/image files, with optional LLM Vision for
image content analysis via the markitdown-ocr plugin.

Run with:  uv run ingest_prd.py <prd-file> [--out <dir>]
Deps are auto-installed by uv via PEP 723 inline metadata above.

Produces the same prd-ingest/ output structure expected by prd-distill:
  source-manifest.yaml, document.md, document-structure.json,
  evidence-map.yaml, media-analysis.yaml, tables/, media/,
  extraction-quality.yaml, conversion-warnings.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from markitdown import MarkItDown


# ── Supported formats ────────────────────────────────────────────────

SUPPORTED_TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
SUPPORTED_DOC_SUFFIXES = SUPPORTED_TEXT_SUFFIXES | {
    ".docx", ".pdf", ".pptx", ".ppt", ".xlsx", ".xls", ".html", ".htm",
    ".epub",
}


def markitdown_version() -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "markitdown"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return "unknown"
    match = re.search(r"^Version:\s*(.+)$", result.stdout, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


# ── Helpers ──────────────────────────────────────────────────────────

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


# ── YAML rendering (no external dep) ────────────────────────────────

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


def write_yaml(path: Path, data: Any) -> None:
    path.write_text(render_yaml(data), encoding="utf-8")


# ── MarkItDown conversion ────────────────────────────────────────────

def convert_with_markitdown(source: Path, out_dir: Path) -> dict[str, Any]:
    """Use MarkItDown to convert a document to Markdown.

    Auto-detects LLM credentials for image analysis from environment:
    1. OPENAI_API_KEY + optional OPENAI_BASE_URL → OpenAI client
    2. ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL (ZhiPu) → OpenAI-compatible client
    """
    llm_client = None
    llm_model = None
    ocr_mode = "not_available"
    vision_provider = "none"

    try:
        from openai import OpenAI

        # Strategy 1: Standard OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            base_url = os.environ.get("OPENAI_BASE_URL")
            kwargs: dict[str, Any] = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            llm_client = OpenAI(**kwargs)
            llm_model = os.environ.get("LLM_MODEL", "gpt-4o")
            ocr_mode = "llm_vision"
            vision_provider = "openai_compatible"

        # Strategy 2: ZhiPu (Anthropic-compatible endpoint → OpenAI-compatible)
        if not llm_client:
            zp_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
            zp_base = os.environ.get("ANTHROPIC_BASE_URL", "")
            if zp_token and "bigmodel.cn" in zp_base:
                # Convert https://open.bigmodel.cn/api/anthropic → https://open.bigmodel.cn/api/paas/v4/
                openai_base = "https://open.bigmodel.cn/api/paas/v4/"
                llm_client = OpenAI(api_key=zp_token, base_url=openai_base)
                llm_model = os.environ.get("LLM_MODEL", "glm-4v-flash")
                ocr_mode = "llm_vision"
                vision_provider = "zhipu_openai_compatible"
    except ImportError:
        pass

    md = MarkItDown(enable_plugins=True, llm_client=llm_client, llm_model=llm_model)
    result = md.convert(str(source))

    # Extract images from docx/pptx into media/
    media_items = extract_media_from_source(source, out_dir)

    return {
        "text_content": result.text_content or "",
        "ocr_mode": ocr_mode,
        "vision_provider": vision_provider,
        "vision_model": llm_model or "",
        "media_items": media_items,
    }


def extract_media_from_source(source: Path, out_dir: Path) -> list[dict[str, Any]]:
    """Extract embedded images from docx/pptx into media/ directory."""
    import zipfile

    media_items: list[dict[str, Any]] = []
    suffix = source.suffix.lower()

    if suffix not in {".docx", ".pptx"}:
        return media_items

    try:
        with zipfile.ZipFile(source) as zf:
            media_dir = out_dir / "media"
            counter = 1
            for entry in sorted(zf.namelist()):
                # Match word/media/, ppt/media/, or media/ at root level
                parts = entry.replace("\\", "/").split("/")
                if len(parts) < 2 or parts[-2] != "media":
                    continue
                ext = Path(entry).suffix.lower()
                if ext not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".emf", ".wmf"}:
                    continue
                media_id = f"IMG-{counter:03d}"
                filename = f"{media_id}{ext}"
                output_path = media_dir / filename
                output_path.write_bytes(zf.read(entry))
                media_items.append({
                    "id": media_id,
                    "source_path": entry,
                    "output_path": str(output_path.relative_to(out_dir)),
                    "filename": filename,
                    "mime_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
                    "size_bytes": output_path.stat().st_size,
                    "referenced_by": [],
                })
                counter += 1
    except (zipfile.BadZipFile, KeyError):
        pass

    return media_items


# ── Block splitting ──────────────────────────────────────────────────

def split_into_blocks(markdown: str, source_format: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split markdown into blocks and generate evidence items.

    Identifies headings, paragraphs, tables, and image references,
    assigning deterministic BLK-XXXX and PRD-XXX IDs.
    """
    blocks: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    current_heading = ""
    table_count = 0
    paragraph_count = 0

    # Detect table blocks (consecutive | lines)
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Heading detection
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            current_heading = heading_match.group(2).strip()
            block_id = f"BLK-{len(blocks) + 1:04d}"
            paragraph_count += 1
            blocks.append({
                "id": block_id,
                "type": "heading",
                "locator": f"{source_format}:line:{i + 1}",
                "level": len(heading_match.group(1)),
                "text": current_heading,
            })
            evidence_items.append({
                "id": f"PRD-{len(evidence_items) + 1:03d}",
                "kind": "prd_block",
                "block_id": block_id,
                "locator": f"{source_format}:line:{i + 1}",
                "summary": current_heading[:180],
                "confidence": "high",
            })
            i += 1
            continue

        # Table detection (consecutive | lines with separator)
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if stripped.startswith("|") and re.match(r"^\|[\s\-:|]+\|$", next_stripped):
            table_count += 1
            table_id = f"TBL-{table_count:03d}"
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            table_text = "\n".join(table_lines)
            row_count = len(table_lines)
            has_merged = "<br>" in table_text or "rowspan" in table_text.lower()
            block_id = f"BLK-{len(blocks) + 1:04d}"
            blocks.append({
                "id": block_id,
                "type": "table",
                "locator": f"{source_format}:table:{table_count}",
                "table_id": table_id,
                "rows": row_count,
                "text": table_text[:500],
            })
            evidence_items.append({
                "id": f"PRD-{len(evidence_items) + 1:03d}",
                "kind": "prd_table",
                "block_id": block_id,
                "locator": f"{source_format}:table:{table_count}",
                "summary": f"{row_count} rows table",
                "confidence": "medium" if has_merged else "high",
            })
            continue

        # Image reference detection (standard ![alt](src) or MarkItDown-OCR *[Image OCR]*)
        img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        ocr_match = re.match(r"\*\[Image OCR\](.*)", stripped) if not img_match else None
        if img_match or ocr_match:
            block_id = f"BLK-{len(blocks) + 1:04d}"
            if img_match:
                img_alt = img_match.group(1)
                img_src = img_match.group(2)
                ocr_text = ""
                img_confidence = "low"
            else:
                img_alt = "Image OCR"
                img_src = ""
                ocr_text = ocr_match.group(1).strip() if ocr_match else ""
                img_confidence = "medium"  # LLM Vision analyzed
            blocks.append({
                "id": block_id,
                "type": "image",
                "locator": f"{source_format}:line:{i + 1}",
                "alt": img_alt,
                "src": img_src,
                "text": stripped,
                "ocr_text": ocr_text,
            })
            evidence_items.append({
                "id": f"PRD-{len(evidence_items) + 1:03d}",
                "kind": "prd_image",
                "block_id": block_id,
                "locator": f"{source_format}:line:{i + 1}",
                "summary": f"image: {img_alt or img_src}"[:180],
                "confidence": img_confidence,
            })
            i += 1
            continue

        # Regular paragraph
        paragraph_count += 1
        block_id = f"BLK-{len(blocks) + 1:04d}"
        blocks.append({
            "id": block_id,
            "type": "paragraph",
            "locator": f"{source_format}:line:{i + 1}",
            "heading": current_heading,
            "text": stripped,
        })
        evidence_items.append({
            "id": f"PRD-{len(evidence_items) + 1:03d}",
            "kind": "prd_block",
            "block_id": block_id,
            "locator": f"{source_format}:line:{i + 1}",
            "summary": stripped[:180],
            "confidence": "high",
        })
        i += 1

    return blocks, evidence_items


# ── Table extraction ─────────────────────────────────────────────────

def extract_tables_to_files(markdown: str, out_dir: Path) -> list[dict[str, Any]]:
    """Extract markdown tables into separate files under tables/."""
    tables: list[dict[str, Any]] = []
    lines = markdown.splitlines()
    i = 0
    table_idx = 0

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("|") or i + 1 >= len(lines):
            i += 1
            continue

        # Check for separator line (|---|---|)
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if not re.match(r"^\|[\s\-:|]+\|$", next_stripped):
            i += 1
            continue

        table_idx += 1
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i])
            i += 1

        table_id = f"TBL-{table_idx:03d}"
        table_md = "\n".join(table_lines) + "\n"
        table_path = out_dir / "tables" / f"{table_id}.md"
        table_path.write_text(table_md, encoding="utf-8")
        tables.append({
            "table_id": table_id,
            "rows": len(table_lines),
            "path": str(table_path.relative_to(out_dir)),
        })

    return tables


# ── Media analysis ───────────────────────────────────────────────────

def build_media_analysis(
    media_items: list[dict[str, Any]],
    ocr_mode: str,
    text_content: str,
) -> list[dict[str, Any]]:
    """Build media-analysis items with analysis status.

    If LLM Vision was active and MarkItDown generated image descriptions,
    those are captured in the text_content. Media items get
    'llm_vision_analyzed' status; otherwise they stay
    'needs_vision_or_human_review'.
    """
    has_image_descriptions = bool(
        re.search(r"(!\[.*?(?:descri|image|photo|diagram|screenshot|flowchart|figure)|\*\[Image OCR\])", text_content, re.IGNORECASE)
    )

    items = []
    for m in media_items:
        analysis_status = "needs_vision_or_human_review"
        summary = ""
        confidence = "low"

        if ocr_mode == "llm_vision":
            # MarkItDown with LLM client already processed images
            analysis_status = "llm_vision_analyzed"
            summary = "analyzed by markitdown-ocr plugin with LLM Vision"
            confidence = "medium"  # LLM Vision analyzed = medium confidence

        items.append({
            **m,
            "analysis_status": analysis_status,
            "summary": summary,
            "confidence": confidence,
        })

    return items


# ── Quality gates ────────────────────────────────────────────────────

def quality_status(
    warnings: list[str],
    media_items: list[dict[str, Any]],
    block_count: int,
) -> tuple[str, list[str]]:
    gates: list[str] = []
    status = "pass"

    if block_count == 0:
        status = "block"
        gates.append("no readable text blocks extracted")

    unanalyzed = [m for m in media_items if m.get("analysis_status") == "needs_vision_or_human_review"]
    if unanalyzed:
        status = "warn" if status == "pass" else status
        gates.append(f"{len(unanalyzed)} images require vision or human review")

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


# ── Source manifest ──────────────────────────────────────────────────

def source_manifest(
    source: Path,
    source_format: str,
    backend: str,
    ocr_mode: str,
    vision_provider: str,
    vision_model: str,
) -> dict[str, Any]:
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
            "backend": backend,
            "backend_version": markitdown_version() if backend == "markitdown" else "not_applicable",
            "ocr": ocr_mode,
            "vision_provider": vision_provider,
            "vision_model": vision_model,
            "notes": [
                "markdown/text inputs are read directly to preserve line fidelity",
                "binary document inputs are converted through MarkItDown",
                "image-derived requirements require llm_vision or human confirmation",
            ],
        },
    }


# ── Main conversion pipeline ────────────────────────────────────────

def convert_source(source: Path, out_dir: Path) -> dict[str, Any]:
    """Convert a PRD file using MarkItDown and produce prd-ingest artifacts."""
    suffix = source.suffix.lower()
    warnings: list[str] = []

    if suffix in SUPPORTED_TEXT_SUFFIXES:
        # Plain text/markdown: read directly, no MarkItDown needed
        text_content = source.read_text(encoding="utf-8", errors="replace")
        source_format = "markdown" if suffix in {".md", ".markdown"} else "text"
        backend = "direct_text"
        ocr_mode = "not_applicable"
        vision_provider = "not_applicable"
        vision_model = ""
        media_items_raw: list[dict[str, Any]] = []
    else:
        # All binary formats go through MarkItDown
        result = convert_with_markitdown(source, out_dir)
        text_content = result["text_content"]
        ocr_mode = result["ocr_mode"]
        vision_provider = result["vision_provider"]
        vision_model = result["vision_model"]
        media_items_raw = result["media_items"]
        source_format = suffix.lstrip(".")
        backend = "markitdown"

        if not text_content.strip():
            raise RuntimeError(f"MarkItDown returned empty content for {source.name}")

    # Split into blocks
    blocks, evidence_items = split_into_blocks(text_content, source_format)

    # Extract tables to separate files
    extracted_tables = extract_tables_to_files(text_content, out_dir)
    # Attach table file paths to matching blocks
    for block in blocks:
        if block["type"] == "table":
            for tbl in extracted_tables:
                if tbl["table_id"] == block.get("table_id"):
                    block["path"] = tbl["path"]
                    break

    # Build media analysis
    media_analysis = build_media_analysis(media_items_raw, ocr_mode, text_content)

    # Detect image references in markdown for media tracking
    img_refs = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text_content)
    ocr_blocks = re.findall(r"\*\[Image OCR\](.*?)\*\[End OCR\]\*", text_content, re.DOTALL)
    if (img_refs or ocr_blocks) and not media_items_raw:
        for idx, (alt, src) in enumerate(img_refs, start=1):
            media_items_raw.append({
                "id": f"IMG-{idx:03d}",
                "source_path": src,
                "output_path": "",
                "filename": "",
                "mime_type": mimetypes.guess_type(src)[0] or "application/octet-stream",
                "size_bytes": None,
                "referenced_by": [],
            })
        for idx, ocr_text in enumerate(ocr_blocks, start=len(img_refs) + 1):
            media_items_raw.append({
                "id": f"IMG-{idx:03d}",
                "source_path": "llm_vision_inline",
                "output_path": "",
                "filename": "",
                "mime_type": "image/llm-vision",
                "size_bytes": None,
                "referenced_by": [],
            })
        media_analysis = build_media_analysis(media_items_raw, ocr_mode, text_content)

    # Add warnings for unanalyzed media
    unanalyzed = [m for m in media_analysis if m.get("analysis_status") == "needs_vision_or_human_review"]
    if unanalyzed:
        warnings.append(f"{len(unanalyzed)} images extracted but require vision or human review for content understanding")

    paragraph_count = len([b for b in blocks if b["type"] in {"paragraph", "heading"}])
    table_count = len([b for b in blocks if b["type"] == "table"])
    media_count = len(media_items_raw)

    return {
        "format": source_format,
        "document_markdown": text_content if text_content.endswith("\n") else text_content + "\n",
        "structure": {
            "schema_version": "1.0",
            "source_type": source_format,
            "blocks": blocks,
            "stats": {
                "paragraphs": paragraph_count,
                "tables": table_count,
                "media": media_count,
            },
        },
        "evidence_items": evidence_items,
        "media_items": media_analysis,
        "warnings": sorted(set(warnings)),
        "backend": backend,
        "ocr_mode": ocr_mode,
        "vision_provider": vision_provider,
        "vision_model": vision_model,
    }


def run(source: Path, out_dir: Path) -> int:
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_DOC_SUFFIXES:
        raise ValueError(
            f"unsupported PRD format: {suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_DOC_SUFFIXES))}"
        )

    ensure_dirs(out_dir)
    parsed = convert_source(source, out_dir)

    blocks = parsed["structure"]["blocks"]
    warnings = list(parsed["warnings"])
    media_items = list(parsed["media_items"])
    status, gates = quality_status(warnings, media_items, len(blocks))

    # Write all prd-ingest artifacts
    (out_dir / "document.md").write_text(parsed["document_markdown"], encoding="utf-8")
    (out_dir / "document-structure.json").write_text(
        json.dumps(parsed["structure"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_yaml(
        out_dir / "source-manifest.yaml",
        source_manifest(
            source,
            parsed["format"],
            parsed["backend"],
            parsed["ocr_mode"],
            parsed["vision_provider"],
            parsed["vision_model"],
        ),
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
                    "id": item["id"],
                    "analysis_status": item.get("analysis_status", "needs_vision_or_human_review"),
                    "summary": item.get("summary", ""),
                    "confidence": item.get("confidence", "low"),
                    "source_path": item.get("source_path", ""),
                    "output_path": item.get("output_path", ""),
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
    (out_dir / "INGESTION_STATUS.md").write_text(
        "\n".join([
            "# PRD Ingestion Status",
            "",
            f"- Source: `{source}`",
            f"- Backend: `{parsed['backend']}`",
            f"- OCR / Vision: `{parsed['ocr_mode']}`",
            f"- Vision provider: `{parsed['vision_provider']}`",
            f"- Vision model: `{parsed['vision_model'] or 'not_applicable'}`",
            f"- Quality: `{status}`",
            f"- Blocks: `{len(blocks)}`",
            f"- Tables: `{parsed['structure']['stats']['tables']}`",
            f"- Media: `{parsed['structure']['stats']['media']}`",
            "",
            "Next checks:",
            "- Read `extraction-quality.yaml` before trusting downstream conclusions.",
            "- Read `media-analysis.yaml` when the PRD includes screenshots, flowcharts, or diagrams.",
            "- Ensure unresolved warnings are copied into `report.md` section 10.",
            "",
        ]),
        encoding="utf-8",
    )

    print(str(out_dir))
    return 0 if status != "block" else 2


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Ingest a PRD document into stable artifacts.")
    parser.add_argument("source", help="Path to PRD file (docx/md/txt/pdf/pptx/xlsx/html)")
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
                    "MarkItDown conversion failed. Check the file format and try again.",
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
