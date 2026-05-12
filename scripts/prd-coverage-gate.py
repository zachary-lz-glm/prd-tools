#!/usr/bin/env python3
"""PRD Coverage Gate — 保真度门禁脚本

检查原始 PRD 信息是否被完整覆盖到下游产物中。
消费 document-structure.json 和 evidence-map.yaml，输出 coverage-report.yaml。

退出码: 0 = 通过(或 warning), 2 = 保真度不足
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import yaml


def _read_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_yaml(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _check_block_coverage(distill_dir):
    """document-structure.json 中所有非 excluded block 必须出现在 evidence-map.yaml 中。"""
    ds_path = os.path.join(distill_dir, "_ingest", "document-structure.json")
    em_path = os.path.join(distill_dir, "_ingest", "evidence-map.yaml")

    ds = _read_json(ds_path)
    if ds is None:
        return {"status": "skip", "message": "document-structure.json not found"}

    em = _read_yaml(em_path)
    if em is None:
        return {"status": "fail", "message": "evidence-map.yaml not found but document-structure.json exists"}

    ds_blocks = ds.get("blocks", [])
    exclusion_types = set(ds.get("exclusion_types", []))

    em_blocks = em.get("blocks", [])
    em_block_ids = set()
    for b in em_blocks:
        bid = b.get("block_id") or b.get("evidence_id", "")
        if bid:
            em_block_ids.add(bid)

    missing = []
    total = 0
    for block in ds_blocks:
        block_id = block.get("block_id") or block.get("id", "")
        block_type = block.get("block_type", "")
        if block_type in exclusion_types:
            continue
        total += 1
        if block_id not in em_block_ids:
            missing.append(block_id)

    covered = total - len(missing)
    ratio = covered / total if total > 0 else 1.0

    if missing:
        return {
            "status": "fail",
            "covered_blocks": covered,
            "total_blocks": total,
            "coverage_ratio": round(ratio, 3),
            "missing": missing[:10],
            "message": f"{len(missing)} blocks not covered in evidence-map",
        }

    return {
        "status": "pass",
        "covered_blocks": covered,
        "total_blocks": total,
        "coverage_ratio": round(ratio, 3),
        "missing": [],
        "message": "All blocks covered",
    }


def _check_media_coverage(distill_dir):
    """_ingest/media/ 下所有图片必须在 media-analysis.yaml 有条目。"""
    media_dir = os.path.join(distill_dir, "_ingest", "media")
    analysis_path = os.path.join(distill_dir, "_ingest", "media-analysis.yaml")

    if not os.path.isdir(media_dir):
        return {"status": "pass", "message": "No media directory"}

    media_files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"):
        media_files.extend(glob.glob(os.path.join(media_dir, ext)))

    if not media_files:
        return {"status": "pass", "message": "No media files found"}

    analysis = _read_yaml(analysis_path)
    if analysis is None:
        return {
            "status": "fail",
            "total_media": len(media_files),
            "missing": [os.path.basename(f) for f in media_files[:10]],
            "message": f"media-analysis.yaml not found but {len(media_files)} media files exist",
        }

    analyzed_files = set()
    if isinstance(analysis, list):
        for item in analysis:
            fname = item.get("file") or item.get("filename") or item.get("media_ref", "")
            if fname:
                analyzed_files.add(os.path.basename(fname))
    elif isinstance(analysis, dict):
        for item in analysis.get("media") or analysis.get("items") or analysis.get("images") or []:
            fname = item.get("file") or item.get("filename") or item.get("media_ref", "")
            if fname:
                analyzed_files.add(os.path.basename(fname))

    missing = []
    for f in media_files:
        basename = os.path.basename(f)
        if basename not in analyzed_files:
            missing.append(basename)

    if missing:
        return {
            "status": "fail",
            "total_media": len(media_files),
            "analyzed": len(media_files) - len(missing),
            "missing": missing[:10],
            "message": f"{len(missing)} media files without analysis",
        }

    return {
        "status": "pass",
        "total_media": len(media_files),
        "analyzed": len(media_files),
        "missing": [],
        "message": "All media files analyzed",
    }


def _check_requirement_trace(distill_dir):
    """requirement-ir.yaml 每条 requirement 的 source_blocks 或 source_block_ids 非空。"""
    ir_path = os.path.join(distill_dir, "context", "requirement-ir.yaml")
    ir = _read_yaml(ir_path)

    if ir is None:
        return {"status": "skip", "message": "requirement-ir.yaml not found"}

    requirements = ir.get("requirements", [])
    if not requirements:
        return {"status": "skip", "message": "No requirements in requirement-ir.yaml"}

    missing_trace = []
    for req in requirements:
        req_id = req.get("id", "?")
        evidence = req.get("evidence", {})
        if not isinstance(evidence, dict):
            missing_trace.append(req_id)
            continue
        source_blocks = evidence.get("source_blocks", [])
        source_block_ids = evidence.get("source_block_ids", [])
        if not source_blocks and not source_block_ids:
            missing_trace.append(req_id)

    if missing_trace:
        return {
            "status": "fail",
            "total_requirements": len(requirements),
            "with_trace": len(requirements) - len(missing_trace),
            "missing_trace": missing_trace[:10],
            "message": f"{len(missing_trace)} requirements without source_blocks trace",
        }

    return {
        "status": "pass",
        "total_requirements": len(requirements),
        "with_trace": len(requirements),
        "missing_trace": [],
        "message": "All requirements have source block trace",
    }


def _check_ai_prd_sections(distill_dir):
    """ai-friendly-prd.md 章节覆盖 document-structure.json 中所有 level-1 heading。"""
    ds_path = os.path.join(distill_dir, "_ingest", "document-structure.json")
    afprd_path = os.path.join(distill_dir, "spec", "ai-friendly-prd.md")

    ds = _read_json(ds_path)
    if ds is None:
        return {"status": "skip", "message": "document-structure.json not found"}

    if not os.path.isfile(afprd_path):
        return {"status": "skip", "message": "ai-friendly-prd.md not found"}

    headings = []
    for block in ds.get("blocks", []):
        if block.get("block_type") == "heading" and block.get("level", 0) <= 2:
            text = block.get("heading") or block.get("text_excerpt", "")
            if text:
                headings.append(text.strip().lower())

    if not headings:
        return {"status": "pass", "message": "No level-1/2 headings in document-structure"}

    with open(afprd_path, "r", encoding="utf-8") as f:
        afprd_content = f.read().lower()

    uncovered = []
    for h in headings:
        keywords = [w for w in h.split() if len(w) > 2]
        if keywords and not any(kw in afprd_content for kw in keywords[:3]):
            uncovered.append(h)

    if uncovered:
        return {
            "status": "warning",
            "total_headings": len(headings),
            "uncovered": uncovered[:10],
            "message": f"{len(uncovered)} PRD headings may not be covered in ai-friendly-prd",
        }

    return {
        "status": "pass",
        "total_headings": len(headings),
        "uncovered": [],
        "message": "All PRD headings appear covered",
    }


def _check_detail_recall(distill_dir):
    """table/code_block 类型 block 必须在 evidence-map 中有 requirement_ids 非空。"""
    ds_path = os.path.join(distill_dir, "_ingest", "document-structure.json")
    em_path = os.path.join(distill_dir, "_ingest", "evidence-map.yaml")

    ds = _read_json(ds_path)
    if ds is None:
        return {"status": "skip", "message": "document-structure.json not found"}

    em = _read_yaml(em_path)
    if em is None:
        return {"status": "skip", "message": "evidence-map.yaml not found"}

    detail_types = {"table", "code_block"}
    detail_blocks = []
    for block in ds.get("blocks", []):
        if block.get("block_type") in detail_types:
            detail_blocks.append(block.get("block_id", ""))

    if not detail_blocks:
        return {"status": "pass", "message": "No table/code_block blocks in document"}

    em_map = {}
    for b in em.get("blocks", []):
        bid = b.get("block_id", "")
        req_ids = b.get("requirement_ids", [])
        em_map[bid] = req_ids

    unlinked = []
    for bid in detail_blocks:
        if bid not in em_map or not em_map[bid]:
            unlinked.append(bid)

    if unlinked:
        return {
            "status": "warning",
            "total_detail_blocks": len(detail_blocks),
            "unlinked": unlinked[:10],
            "message": f"{len(unlinked)} table/code blocks not linked to any requirement",
        }

    return {
        "status": "pass",
        "total_detail_blocks": len(detail_blocks),
        "unlinked": [],
        "message": "All detail blocks linked to requirements",
    }


# ──────────────────────────────────────────
# Orchestration
# ──────────────────────────────────────────

def run_checks(distill_dir):
    results = {}
    results["block_coverage"] = _check_block_coverage(distill_dir)
    results["media_coverage"] = _check_media_coverage(distill_dir)
    results["requirement_trace"] = _check_requirement_trace(distill_dir)
    results["ai_prd_sections"] = _check_ai_prd_sections(distill_dir)
    results["detail_recall"] = _check_detail_recall(distill_dir)
    return results


FATAL_CHECKS = {"block_coverage", "media_coverage", "requirement_trace"}


def compute_exit_code(results):
    for name, r in results.items():
        if name in FATAL_CHECKS and r.get("status") == "fail":
            return 2
    return 0


def compute_overall_status(results):
    has_fail = any(
        r.get("status") == "fail" and name in FATAL_CHECKS
        for name, r in results.items()
    )
    if has_fail:
        return "fail"
    has_warning = any(r.get("status") == "warning" for r in results.values())
    if has_warning:
        return "warning"
    return "pass"


def write_coverage_report(distill_dir, results):
    report = {
        "schema_version": "1.0",
        "gate": "prd-coverage",
        "status": compute_overall_status(results),
        "checks": {},
    }
    for name, r in results.items():
        report["checks"][name] = {
            "status": r.get("status", "skip"),
            "message": r.get("message", ""),
        }
        if "coverage_ratio" in r:
            report["checks"][name]["coverage_ratio"] = r["coverage_ratio"]
        if "missing" in r and r["missing"]:
            report["checks"][name]["missing"] = r["missing"]

    out_path = os.path.join(distill_dir, "context", "coverage-report.yaml")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return out_path


def print_summary(results):
    print("\n=== PRD Coverage Gate ===\n")
    checks_order = [
        ("block_coverage", "Block coverage"),
        ("media_coverage", "Media coverage"),
        ("requirement_trace", "Requirement trace"),
        ("ai_prd_sections", "AI-PRD sections"),
        ("detail_recall", "Detail recall"),
    ]
    for key, label in checks_order:
        r = results.get(key, {})
        status = r.get("status", "skip")
        if status == "pass":
            sym = "+"
        elif status == "warning":
            sym = "!"
        elif status == "fail":
            sym = "x"
        else:
            sym = "-"
        msg = r.get("message", "")
        extra = ""
        if "coverage_ratio" in r:
            extra = f" (ratio: {r['coverage_ratio']})"
        print(f"  [{sym}] {label}: {msg}{extra}")

    overall = compute_overall_status(results)
    print(f"\n  Overall: {overall}\n")


def main():
    parser = argparse.ArgumentParser(description="PRD Coverage Gate")
    parser.add_argument("--distill-dir", required=True, help="Path to distill directory")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    distill_dir = args.distill_dir
    if not os.path.isdir(distill_dir):
        print(f"ERROR: distill directory not found: {distill_dir}", file=sys.stderr)
        sys.exit(1)

    results = run_checks(distill_dir)
    print_summary(results)
    write_coverage_report(distill_dir, results)
    sys.exit(compute_exit_code(results))


if __name__ == "__main__":
    main()
