#!/usr/bin/env python3
"""quality-gate.py — Unified Quality Gate for prd-tools.

Subcommands:
  distill    - Quality + coverage checks for /prd-distill output
  final      - Weighted scoring for distill deliverables (report.md, plan.md)
  reference  - Quality checks for /reference output

Usage:
  python3 scripts/quality-gate.py distill   --distill-dir <path> --repo-root <path> [--mode quality|coverage|all]
  python3 scripts/quality-gate.py final     --distill-dir <path>
  python3 scripts/quality-gate.py reference --root <path>

Exit code: 0 = pass or pass-with-warnings, 2 = fail.
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

import yaml


# ══════════════════════════════════════════════════════════════
# Shared helpers (inlined from _gate_shared.py)
# ══════════════════════════════════════════════════════════════

def read_safe(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def file_exists_nonempty(path):
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def detect_team_mode(repo_root):
    for p in [Path(repo_root) / 'team' / 'project-profile.yaml',
              Path(repo_root) / '_prd-tools' / 'reference' / 'project-profile.yaml']:
        if p.is_file():
            try:
                data = yaml.safe_load(p.read_text(encoding='utf-8')) or {}
            except Exception:
                continue
            if data.get('layer') == 'team-common':
                repos = [r.get('repo', '') for r in data.get('team_repos', []) if r.get('repo')]
                return True, repos
    return False, []


def compute_exit_code(results):
    for val in results.values():
        if isinstance(val, dict) and val.get('status') == 'fail':
            return 2
    return 0


def has_warnings(results):
    return any(isinstance(v, dict) and v.get('status') == 'warning' for v in results.values())


def print_check_line(label, val, indent=2):
    sym = {'pass': '+', 'warning': '!', 'fail': 'x', 'skip': '-'}.get(val.get('status', ''), '?')
    print(f'{" " * indent}[{sym}] {label}: {val["status"]}')
    if val['status'] != 'pass':
        for k, v in val.items():
            if k == 'status':
                continue
            if isinstance(v, bool) and not v:
                print(f'{" " * indent}      {k}: false')
            elif isinstance(v, list) and v:
                print(f'{" " * indent}      {k}: {v}')
            elif isinstance(v, str) and v:
                print(f'{" " * indent}      {k}: {v}')


def _read_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
# DISTILL: Quality + Coverage
# ══════════════════════════════════════════════════════════════

REQUIRED_DISTILL_FILES = {
    'critical': ['_ingest/document.md', 'report.md', 'plan.md'],
    'important': [
        'context/requirement-ir.yaml',
        'context/layer-impact.yaml', 'context/contract-delta.yaml',
        'context/graph-context.md', 'context/report-confirmation.yaml',
        'context/readiness-report.yaml', 'context/final-quality-gate.yaml',
    ],
}

REQUIRED_TEAM_FILES = {
    'critical': ['_ingest/document.md', 'report.md', 'team-plan.md'],
    'important': [
        'context/requirement-ir.yaml',
        'context/layer-impact.yaml', 'context/contract-delta.yaml',
        'context/graph-context.md', 'context/report-confirmation.yaml',
        'context/readiness-report.yaml', 'context/final-quality-gate.yaml',
    ],
}

# ── Distill quality checks ──

def _dq_required_files(base, is_team=False):
    spec = REQUIRED_TEAM_FILES if is_team else REQUIRED_DISTILL_FILES
    missing_critical, missing_important, empty = [], [], []
    for f in spec['critical']:
        p = base / f
        if not p.exists():
            missing_critical.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)
    for f in spec['important']:
        p = base / f
        if not p.exists():
            missing_important.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)
    if is_team:
        plans_dir = base / 'plans'
        if not (plans_dir.is_dir() and list(plans_dir.glob('plan-*.md'))):
            missing_critical.append('plans/plan-*.md (no sub-plans found)')
    status = 'fail' if missing_critical else ('warning' if missing_important or empty else 'pass')
    return {'status': status, 'missing_critical': missing_critical,
            'missing_important': missing_important, 'empty': empty}


def _dq_requirement_ir(base):
    text = read_safe(base / 'context' / 'requirement-ir.yaml')
    if not text.strip():
        return {'status': 'fail', 'has_requirements': False}
    has_reqs = bool(re.search(r'requirements:', text))
    has_evidence = bool(re.search(r'evidence:', text))
    return {'status': 'pass' if (has_reqs and has_evidence) else 'fail',
            'has_requirements': has_reqs, 'has_evidence': has_evidence}


def _dq_layer_impact(base):
    text = read_safe(base / 'context' / 'layer-impact.yaml')
    if not text.strip():
        return {'status': 'fail', 'has_code_anchors': False, 'has_fallback': False}
    has_anchors = bool(re.search(r'code_anchors:', text))
    has_fallback = bool(re.search(r'fallback:', text)) or bool(re.search(r'fallback_reason:', text))
    return {'status': 'pass' if (has_anchors or has_fallback) else 'warning',
            'has_code_anchors': has_anchors, 'has_fallback': has_fallback}


def _dq_index_bridge(base, repo_root):
    index_dir = Path(repo_root) / '_prd-tools' / 'reference' / 'index'
    if not (index_dir / 'entities.json').exists():
        return {'status': 'pass', 'index_exists': False, 'note': 'reference/index not found'}
    qp = file_exists_nonempty(base / 'context' / 'query-plan.yaml')
    cp = file_exists_nonempty(base / 'context' / 'context-pack.md')
    return {'status': 'pass' if (qp and cp) else 'fail', 'index_exists': True,
            'query_plan_exists': qp, 'context_pack_exists': cp}


def _dq_final_quality_gate(base):
    exists = file_exists_nonempty(base / 'context' / 'final-quality-gate.yaml')
    return {'status': 'pass' if exists else 'fail', 'exists': exists}


def _dq_report_quality(base):
    text = read_safe(base / 'report.md')
    if not text.strip():
        return {'status': 'fail', 'has_quality_summary': False}
    has_quality = bool(re.search(r'(?:PRD\s*质量|质量摘要|prd.quality|quality.report|AI-friendly\s*PRD\s*质量)', text, re.I))
    return {'status': 'pass' if has_quality else 'warning', 'has_quality_summary': has_quality}


def _dq_report_confirmation(base):
    text = read_safe(base / 'context' / 'report-confirmation.yaml')
    if not text.strip():
        return {'status': 'fail', 'exists': False, 'approved': False,
                'message': 'report-confirmation.yaml missing or empty'}
    approved = bool(re.search(r'^status:\s*["\']?approved["\']?\s*$', text, re.M))
    return {'status': 'pass' if approved else 'fail', 'exists': True, 'approved': approved,
            'message': '' if approved else 'report-confirmation.yaml status is not approved'}


def _dq_plan_missing_confirmation(base, is_team=False):
    plan_files = [base / 'team-plan.md'] if is_team else [base / 'plan.md']
    if is_team:
        plans_dir = base / 'plans'
        if plans_dir.is_dir():
            plan_files.extend(sorted(plans_dir.glob('plan-*.md')))
    total_suspicious = 0
    for pp in plan_files:
        text = read_safe(pp)
        if not text.strip():
            continue
        for line in re.findall(r'^-\s+\[[ x]\]\s+.+', text, re.M):
            if re.search(r'missing_confirmation|待确认|needs_confirmation', line, re.I):
                if not re.search(r'假设|前提|需确认|assumption|pending|blocked', line, re.I):
                    total_suspicious += 1
    if not is_team and not (base / 'plan.md').exists():
        return {'status': 'fail', 'suspicious_count': 0}
    return {'status': 'pass' if total_suspicious == 0 else 'warning', 'suspicious_count': total_suspicious}


def _dq_team_sub_plans(base, member_repos):
    found, missing = [], []
    for repo in member_repos:
        pf = base / 'plans' / f'plan-{repo}.md'
        (found if file_exists_nonempty(pf) else missing).append(repo)
    return {'status': 'pass' if not missing else 'warning',
            'sub_plans_found': found, 'sub_plans_missing': missing}


def _dq_artifact_contracts(base):
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / 'plugins' / 'prd-distill' / 'skills' / 'prd-distill' / 'references' / 'contracts',
        script_dir.parent.parent / '.claude' / 'skills' / 'prd-distill' / 'references' / 'contracts',
    ]
    contracts_dir = next((c for c in candidates if c.is_dir()), None)
    if not contracts_dir:
        return {'status': 'pass', 'message': 'No contracts directory found'}
    contract_files = sorted(contracts_dir.glob('*.contract.yaml'))
    if not contract_files:
        return {'status': 'pass', 'message': 'No contract files found'}

    import importlib.util
    validator_path = Path(__file__).resolve().parent / 'validate-artifact.py'
    spec = importlib.util.spec_from_file_location("validate_artifact", validator_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    results_list, has_fail, checked, passed = [], False, 0, 0
    for cf in contract_files:
        with open(cf, 'r', encoding='utf-8') as f:
            contract = yaml.safe_load(f)
        if not contract:
            continue
        artifact_path = str(base / contract.get('artifact', ''))
        if not os.path.isfile(artifact_path):
            results_list.append({'contract': cf.name, 'artifact': contract.get('artifact', ''),
                                 'status': 'skip', 'message': 'artifact not found'})
            continue
        checked += 1
        result = mod.validate(artifact_path, contract)
        results_list.append({'contract': cf.name, 'artifact': contract.get('artifact', ''),
                             'status': result['status'], 'findings': result.get('findings', [])})
        if result['status'] == 'fail':
            has_fail = True
        elif result['status'] == 'pass':
            passed += 1

    out_path = base / 'context' / 'artifact-validation.yaml'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        yaml.dump({'schema_version': '1.0', 'status': 'fail' if has_fail else 'pass',
                   'contracts_checked': checked, 'contracts_passed': passed, 'results': results_list},
                  f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if has_fail:
        return {'status': 'fail', 'message': f"Contract violations: {', '.join(r['contract'] for r in results_list if r['status'] == 'fail')}"}
    if checked == 0:
        return {'status': 'pass', 'message': 'No artifacts to validate yet'}
    return {'status': 'pass', 'message': f'{passed}/{checked} contracts passed'}


def _dq_prd_coverage_simple(base):
    coverage_path = base / 'context' / 'coverage-report.yaml'
    if coverage_path.is_file():
        with open(coverage_path, 'r', encoding='utf-8') as f:
            report = yaml.safe_load(f)
        if report and isinstance(report, dict):
            status = report.get('status', 'skip')
            if status in ('fail', 'warning', 'pass'):
                return {'status': status, 'message': f'coverage-report.yaml status: {status}'}
    ds_path = base / '_ingest' / 'document-structure.json'
    if not ds_path.is_file():
        return {'status': 'pass', 'message': 'No document-structure.json (coverage not applicable)'}
    return {'status': 'warning', 'message': 'coverage-report.yaml not found; run --mode coverage'}


def run_distill_quality(base, repo_root):
    is_team, member_repos = detect_team_mode(repo_root)
    results = {
        'required_files': _dq_required_files(base, is_team=is_team),
        'requirement_ir': _dq_requirement_ir(base),
        'layer_impact': _dq_layer_impact(base),
        'index_bridge': _dq_index_bridge(base, repo_root),
        'final_quality_gate': _dq_final_quality_gate(base),
        'report_quality': _dq_report_quality(base),
        'report_confirmation': _dq_report_confirmation(base),
        'plan_missing_confirmation': _dq_plan_missing_confirmation(base, is_team=is_team),
    }
    if is_team:
        results['team_sub_plans'] = _dq_team_sub_plans(base, member_repos)
    results['prd_coverage'] = _dq_prd_coverage_simple(base)
    results['artifact_contracts'] = _dq_artifact_contracts(base)
    return results


def print_distill_quality(results):
    print()
    is_team = 'team_sub_plans' in results
    print(f'=== Distill Quality Gate ({"TEAM" if is_team else "SINGLE-REPO"} MODE) ===')
    print()
    checks = [
        ('required_files', 'Required files'), ('requirement_ir', 'Requirement IR'),
        ('layer_impact', 'Layer impact'), ('index_bridge', 'Index bridge'),
        ('final_quality_gate', 'Final quality gate'), ('report_quality', 'Report quality'),
        ('report_confirmation', 'Report confirmation'),
        ('plan_missing_confirmation', 'Plan missing_confirmation'),
    ]
    if is_team:
        checks.append(('team_sub_plans', 'Team sub-plans'))
    checks += [('prd_coverage', 'PRD coverage (fidelity)'), ('artifact_contracts', 'Artifact contracts')]
    for key, label in checks:
        print_check_line(label, results[key])


# ── Distill coverage checks ──

FATAL_COVERAGE_CHECKS = {'block_coverage', 'media_coverage', 'requirement_trace'}


def _dc_block_coverage(distill_dir):
    ds = _read_json(os.path.join(distill_dir, "_ingest", "document-structure.json"))
    if ds is None:
        return {"status": "skip", "message": "document-structure.json not found"}
    em_path = os.path.join(distill_dir, "_ingest", "evidence-map.yaml")
    if not os.path.isfile(em_path):
        return {"status": "fail", "message": "evidence-map.yaml not found but document-structure.json exists"}
    with open(em_path, "r", encoding="utf-8") as f:
        em = yaml.safe_load(f) or {}
    exclusion_types = set(ds.get("exclusion_types", []))
    em_ids = set()
    for b in em.get("blocks", []):
        bid = b.get("block_id") or b.get("evidence_id", "")
        if bid:
            em_ids.add(bid)
    missing, total = [], 0
    for block in ds.get("blocks", []):
        if block.get("block_type", "") in exclusion_types:
            continue
        total += 1
        bid = block.get("block_id") or block.get("id", "")
        if bid not in em_ids:
            missing.append(bid)
    covered = total - len(missing)
    ratio = covered / total if total > 0 else 1.0
    if missing:
        return {"status": "fail", "covered_blocks": covered, "total_blocks": total,
                "coverage_ratio": round(ratio, 3), "missing": missing[:10],
                "message": f"{len(missing)} blocks not covered in evidence-map"}
    return {"status": "pass", "covered_blocks": covered, "total_blocks": total,
            "coverage_ratio": round(ratio, 3), "missing": [], "message": "All blocks covered"}


def _dc_media_coverage(distill_dir):
    media_dir = os.path.join(distill_dir, "_ingest", "media")
    if not os.path.isdir(media_dir):
        return {"status": "pass", "message": "No media directory"}
    media_files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"):
        media_files.extend(glob.glob(os.path.join(media_dir, ext)))
    if not media_files:
        return {"status": "pass", "message": "No media files found"}
    analysis_path = os.path.join(distill_dir, "_ingest", "media-analysis.yaml")
    if not os.path.isfile(analysis_path):
        return {"status": "fail", "total_media": len(media_files),
                "missing": [os.path.basename(f) for f in media_files[:10]],
                "message": f"media-analysis.yaml not found but {len(media_files)} media files exist"}
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = yaml.safe_load(f)
    analyzed = set()
    items = analysis if isinstance(analysis, list) else (
        analysis.get("media") or analysis.get("items") or analysis.get("images") or []
    ) if isinstance(analysis, dict) else []
    for item in items:
        fname = item.get("file") or item.get("filename") or item.get("media_ref", "")
        if fname:
            analyzed.add(os.path.basename(fname))
    missing = [os.path.basename(f) for f in media_files if os.path.basename(f) not in analyzed]
    if missing:
        return {"status": "fail", "total_media": len(media_files), "analyzed": len(media_files) - len(missing),
                "missing": missing[:10], "message": f"{len(missing)} media files without analysis"}
    return {"status": "pass", "total_media": len(media_files), "analyzed": len(media_files),
            "missing": [], "message": "All media files analyzed"}


def _dc_requirement_trace(distill_dir):
    ir_path = os.path.join(distill_dir, "context", "requirement-ir.yaml")
    if not os.path.isfile(ir_path):
        return {"status": "skip", "message": "requirement-ir.yaml not found"}
    with open(ir_path, "r", encoding="utf-8") as f:
        ir = yaml.safe_load(f) or {}
    requirements = ir.get("requirements", [])
    if not requirements:
        return {"status": "skip", "message": "No requirements in requirement-ir.yaml"}
    missing_trace = []
    for req in requirements:
        evidence = req.get("evidence", {})
        if not isinstance(evidence, dict):
            missing_trace.append(req.get("id", "?"))
        elif not evidence.get("source_blocks") and not evidence.get("source_block_ids"):
            missing_trace.append(req.get("id", "?"))
    if missing_trace:
        return {"status": "fail", "total_requirements": len(requirements),
                "with_trace": len(requirements) - len(missing_trace),
                "missing_trace": missing_trace[:10],
                "message": f"{len(missing_trace)} requirements without source_blocks trace"}
    return {"status": "pass", "total_requirements": len(requirements),
            "with_trace": len(requirements), "missing_trace": [],
            "message": "All requirements have source block trace"}


def _dc_detail_recall(distill_dir):
    ds = _read_json(os.path.join(distill_dir, "_ingest", "document-structure.json"))
    if ds is None:
        return {"status": "skip", "message": "document-structure.json not found"}
    em_path = os.path.join(distill_dir, "_ingest", "evidence-map.yaml")
    if not os.path.isfile(em_path):
        return {"status": "skip", "message": "evidence-map.yaml not found"}
    with open(em_path, "r", encoding="utf-8") as f:
        em = yaml.safe_load(f) or {}
    detail_ids = [b.get("block_id", "") for b in ds.get("blocks", [])
                  if b.get("block_type") in {"table", "code_block"}]
    if not detail_ids:
        return {"status": "pass", "message": "No table/code_block blocks in document"}
    em_map = {b.get("block_id", ""): b.get("requirement_ids", []) for b in em.get("blocks", [])}
    unlinked = [bid for bid in detail_ids if not em_map.get(bid)]
    if unlinked:
        return {"status": "warning", "total_detail_blocks": len(detail_ids), "unlinked": unlinked[:10],
                "message": f"{len(unlinked)} table/code blocks not linked to any requirement"}
    return {"status": "pass", "total_detail_blocks": len(detail_ids), "unlinked": [],
            "message": "All detail blocks linked to requirements"}


def run_distill_coverage(distill_dir):
    return {
        "block_coverage": _dc_block_coverage(distill_dir),
        "media_coverage": _dc_media_coverage(distill_dir),
        "requirement_trace": _dc_requirement_trace(distill_dir),
        "ai_prd_sections": _dc_ai_prd_sections(distill_dir),
        "detail_recall": _dc_detail_recall(distill_dir),
    }


def _coverage_overall_status(results):
    if any(r.get("status") == "fail" and n in FATAL_COVERAGE_CHECKS for n, r in results.items()):
        return "fail"
    if any(r.get("status") == "warning" for r in results.values()):
        return "warning"
    return "pass"


def _write_coverage_report(distill_dir, results):
    report = {"schema_version": "1.0", "gate": "prd-coverage",
              "status": _coverage_overall_status(results), "checks": {}}
    for name, r in results.items():
        report["checks"][name] = {"status": r.get("status", "skip"), "message": r.get("message", "")}
        if "coverage_ratio" in r:
            report["checks"][name]["coverage_ratio"] = r["coverage_ratio"]
        if r.get("missing"):
            report["checks"][name]["missing"] = r["missing"]
    out_path = os.path.join(distill_dir, "context", "coverage-report.yaml")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def print_distill_coverage(results):
    print("\n=== PRD Coverage Gate ===\n")
    for key, label in [("block_coverage", "Block coverage"), ("media_coverage", "Media coverage"),
                        ("requirement_trace", "Requirement trace"), ("ai_prd_sections", "AI-PRD sections"),
                        ("detail_recall", "Detail recall")]:
        r = results.get(key, {})
        sym = {'pass': '+', 'warning': '!', 'fail': 'x'}.get(r.get("status", "skip"), '-')
        extra = f" (ratio: {r['coverage_ratio']})" if "coverage_ratio" in r else ""
        print(f"  [{sym}] {label}: {r.get('message', '')}{extra}")
    print(f"\n  Overall: {_coverage_overall_status(results)}\n")


# ══════════════════════════════════════════════════════════════
# FINAL: Weighted scoring for distill deliverables
# ══════════════════════════════════════════════════════════════

FQ_REQUIRED_FILES = {
    'critical': ['report.md', 'plan.md'],
    'important': ['context/requirement-ir.yaml', 'context/graph-context.md',
                  'context/layer-impact.yaml', 'context/contract-delta.yaml', 'context/readiness-report.yaml'],
}
FQ_OPTIONAL_FILES = ['context/context-pack.md', 'context/query-plan.yaml']

RE_CHECKLIST = re.compile(r'-\s+\[[ x]\]')
RE_FILE_PATH = re.compile(r'(?:src/|lib/)[\w/.-]+\.(?:ts|tsx|js|jsx|go|yaml|yml)')
RE_VERIFY_CMD = re.compile(r'(?:rg\s|grep\s|npm\s+test|pnpm\s+test|go\s+test|curl\s|npx\s+|jest|mocha|vitest)', re.IGNORECASE)
RE_BLOCKER = re.compile(r'(?:BLOCK|阻塞|待确认|Open\s+Question|阻塞项|blocker)', re.IGNORECASE)
RE_BLOCKER_QUALITY = re.compile(r'(?:建议|suggestion|影响|impact|默认策略|default|负责人|owner|mitigation|缓解|风险|risk)', re.IGNORECASE)
RE_ANCHOR_PATH = re.compile(r'`([^`]+\.(?:ts|tsx|js|jsx|go))`')

REPORT_SECTIONS = [
    "1. 需求摘要", "2. PRD 质量摘要", "3. 源码扫描命中摘要", "4. 影响范围",
    "5. 关键结论", "6. 变更明细表", "7. 字段清单", "8. 校验规则",
    "9. 开发 Checklist", "10. 契约对齐与建议", "11. Top Open Questions", "12. 阻塞问题与待确认项",
]
PLAN_SECTIONS = [
    "1. 范围与假设", "2. 整体架构", "3. 实现计划", "4. API 设计",
    "5. 数据存储", "6. 配置与开关", "7. 校验规则汇总", "8. QA 矩阵",
    "9. 契约对齐", "10. 风险与回滚", "11. 工作量估算",
]

CHECK_WEIGHTS = {
    'required_files': 0.20, 'context_pack_consumed': 0.15,
    'code_anchor_coverage': 0.25, 'plan_actionability': 0.25, 'blocker_quality': 0.15,
}


def _fq_load_key_anchors(base):
    rp = base.parent.parent / "reference" / "04-routing-playbooks.yaml"
    if not rp.exists():
        return []
    try:
        text = rp.read_text(encoding='utf-8')
        anchors = []
        for m in re.finditer(r'key_files:\s*\[([^\]]*)\]', text):
            for f in m.group(1).split(','):
                f = f.strip().strip('"').strip("'")
                if f:
                    anchors.append(f)
        return anchors
    except Exception:
        return []


def _fq_extract_paths(text):
    paths = set()
    for m in RE_ANCHOR_PATH.finditer(text):
        paths.add(m.group(1))
    for m in RE_FILE_PATH.finditer(text):
        paths.add(m.group(0))
    return paths


def _fq_extract_symbols(text):
    symbols = set()
    for m in re.finditer(r'\|\s*`(\w+)`\s*\|', text):
        sym = m.group(1)
        if len(sym) > 3:
            symbols.add(sym)
    return symbols


def _fq_required_files(base):
    missing_critical, missing_important, present = [], [], []
    for f in FQ_REQUIRED_FILES['critical']:
        (present if (base / f).exists() else missing_critical).append(f)
    for f in FQ_REQUIRED_FILES['important']:
        (present if (base / f).exists() else missing_important).append(f)
    optional_present = [f for f in FQ_OPTIONAL_FILES if (base / f).exists()]
    total = len(FQ_REQUIRED_FILES['critical']) + len(FQ_REQUIRED_FILES['important'])
    score = int(100 * len(present) / total) if total else 100
    status = 'fail' if missing_critical else ('warning' if missing_important else 'pass')
    return {'status': status, 'score': score, 'present': sorted(present),
            'missing_critical': sorted(missing_critical), 'missing_important': sorted(missing_important),
            'optional_present': sorted(optional_present)}


def _fq_context_pack_consumed(base, report_text, plan_text):
    cp_path = base / 'context/context-pack.md'
    if not cp_path.exists():
        return {'status': 'warning', 'score': 0, 'note': 'context-pack.md not found',
                'anchors_in_pack': 0, 'consumed_by_report': 0, 'consumed_by_plan': 0}
    cp_text = read_safe(cp_path)
    anchor_paths = _fq_extract_paths(cp_text)
    anchor_symbols = _fq_extract_symbols(cp_text)
    if not anchor_paths and not anchor_symbols:
        return {'status': 'pass', 'score': 100, 'note': 'no extractable anchors in context-pack',
                'anchors_in_pack': 0, 'consumed_by_report': 0, 'consumed_by_plan': 0}
    all_anchors = set()
    for p in anchor_paths:
        all_anchors.update([p, Path(p).name, Path(p).stem])
    all_anchors.update(anchor_symbols)
    check_terms = {t for t in all_anchors if len(t) > 3}
    report_hits = sum(1 for t in check_terms if t.lower() in report_text.lower())
    plan_hits = sum(1 for t in check_terms if t.lower() in plan_text.lower())
    total_terms = len(check_terms) if check_terms else 1
    best_ratio = max(report_hits / total_terms, plan_hits / total_terms)
    score = int(100 * min(best_ratio / 0.3, 1.0))
    status = 'pass'
    if best_ratio < 0.1:
        status, score = 'warning', min(score, 30)
    elif best_ratio < 0.3:
        status = 'warning'
    return {'status': status, 'score': score, 'anchors_in_pack': len(check_terms),
            'consumed_by_report': report_hits, 'consumed_by_plan': plan_hits,
            'report_ratio': round(report_hits / total_terms, 2),
            'plan_ratio': round(plan_hits / total_terms, 2)}


def _fq_code_anchor_coverage(base, plan_text):
    anchor_paths = set()
    anchor_paths.update(_fq_extract_paths(read_safe(base / 'context/context-pack.md')))
    anchor_paths.update(_fq_extract_paths(read_safe(base / 'context/graph-context.md')))
    li_text = read_safe(base / 'context/layer-impact.yaml')
    for m in RE_FILE_PATH.finditer(li_text):
        anchor_paths.add(m.group(0))
    if not anchor_paths:
        return {'status': 'pass', 'score': 100, 'note': 'no anchor paths found',
                'total_anchors': 0, 'covered': 0, 'uncovered': []}
    plan_lower = plan_text.lower()
    covered = {p for p in anchor_paths if Path(p).name.lower() in plan_lower or Path(p).stem.lower() in plan_lower}
    uncovered = anchor_paths - covered
    ratio = len(covered) / len(anchor_paths)
    score = int(100 * ratio)
    key_anchors = _fq_load_key_anchors(base)
    key_found = sum(1 for ka in key_anchors if ka.lower() in plan_lower)
    key_ratio = key_found / len(key_anchors) if key_anchors else 1
    key_score = int(100 * key_ratio)
    final_score = int(0.6 * score + 0.4 * key_score)
    status = 'pass'
    if key_ratio < 0.3:
        status, final_score = 'fail', min(final_score, 40)
    elif ratio < 0.5:
        status = 'warning'
    return {'status': status, 'score': final_score, 'total_anchors': len(anchor_paths),
            'covered': len(covered), 'key_anchors_found': key_found,
            'key_anchors_total': len(key_anchors), 'uncovered_samples': sorted(uncovered)[:5]}


def _fq_plan_actionability(plan_text):
    checklists = RE_CHECKLIST.findall(plan_text)
    file_paths = RE_FILE_PATH.findall(plan_text)
    verify_cmds = RE_VERIFY_CMD.findall(plan_text)
    n_cl, n_fp, n_vc = len(checklists), len(set(file_paths)), len(verify_cmds)
    cl_score = min(100, int(100 * n_cl / 5)) if n_cl else 0
    fp_score = min(100, int(100 * n_fp / 3)) if n_fp else 0
    vc_score = 100 if n_vc >= 1 else 0
    score = int(0.3 * cl_score + 0.4 * fp_score + 0.3 * vc_score)
    status = 'pass'
    if n_fp == 0:
        status, score = 'fail', min(score, 20)
    elif n_cl == 0:
        status, score = 'warning', min(score, 70)
    elif n_vc == 0:
        status = 'warning'
    return {'status': status, 'score': score, 'checklist_count': n_cl, 'file_path_count': n_fp,
            'file_paths_sample': sorted(set(file_paths))[:8], 'verify_command_count': n_vc,
            'missing_checklists': n_cl == 0, 'missing_file_paths': n_fp == 0, 'missing_verify_commands': n_vc == 0}


def _fq_blocker_quality(report_text):
    blocker_matches = list(RE_BLOCKER.finditer(report_text))
    if not blocker_matches:
        if re.search(r'无阻[塞塞]|no\s+blocker|无\s*OPEN', report_text, re.IGNORECASE):
            return {'status': 'pass', 'score': 100, 'blocker_count': 0, 'note': 'report states no blockers', 'quality_ratio': 1.0}
        has_section = bool(re.search(r'#{1,4}\s.*(?:阻塞|blocker|open\s+question|待确认)', report_text, re.IGNORECASE))
        if has_section:
            return {'status': 'pass', 'score': 100, 'blocker_count': 0, 'note': 'blockers section present but empty', 'quality_ratio': 1.0}
        return {'status': 'warning', 'score': 70, 'blocker_count': 0, 'note': 'no blocker section found', 'quality_ratio': 0}
    quality_hits = 0
    for m in blocker_matches:
        window = report_text[max(0, m.start() - 50):min(len(report_text), m.end() + 300)]
        if RE_BLOCKER_QUALITY.search(window):
            quality_hits += 1
    ratio = quality_hits / len(blocker_matches)
    score = int(100 * ratio)
    status = 'warning' if ratio < 0.5 else 'pass'
    if ratio < 0.5:
        score = min(score, 50)
    return {'status': status, 'score': score, 'blocker_count': len(blocker_matches),
            'blockers_with_context': quality_hits, 'quality_ratio': round(ratio, 2)}


def _fq_section_structure(base):
    results = {}
    for name, expected in [('report.md', REPORT_SECTIONS), ('plan.md', PLAN_SECTIONS)]:
        p = base / name
        if not p.is_file():
            results[name] = {'status': 'skip', 'reason': 'file missing'}
            continue
        text = read_safe(p)
        got = [g.lstrip('§').strip() for g in re.findall(r'^## (.+)$', text, re.MULTILINE)]
        errors = []
        for i, exp in enumerate(expected):
            if i >= len(got):
                errors.append(f"missing section {i+1}: '{exp}'")
            else:
                if got[i].split('.')[0] != exp.split('.')[0]:
                    errors.append(f"section {i+1} mismatch: expected '{exp}', got '{got[i]}'")
        extra = got[len(expected):]
        if extra:
            errors.append(f"unexpected extra sections: {extra[:3]}")
        results[name] = {'status': 'pass' if not errors else 'fail', 'errors': errors}
    overall = 'pass' if all(r['status'] != 'fail' for r in results.values()) else 'fail'
    return {'status': overall, 'score': 100 if overall == 'pass' else 0,
            'report': results.get('report.md', {}), 'plan': results.get('plan.md', {})}


def fq_compute_overall(checks):
    score = int(round(sum(CHECK_WEIGHTS[k] * checks[k]['score'] for k in CHECK_WEIGHTS)))
    if checks['required_files']['missing_critical']:
        return 'fail', score
    if checks['plan_actionability']['missing_file_paths']:
        return 'fail', score
    if checks['plan_actionability']['missing_checklists']:
        return 'warning', min(score, 84)
    if checks.get('context_pack_consumed', {}).get('status') == 'warning':
        return 'warning', min(score, 84)
    if score >= 85:
        return 'pass', score
    if score >= 60:
        return 'warning', score
    return 'fail', score


def fq_collect_gaps(checks):
    gaps = []
    c = checks
    if c['required_files']['missing_critical']:
        gaps.append(f"missing critical files: {c['required_files']['missing_critical']}")
    if c['required_files']['missing_important']:
        gaps.append(f"missing context files: {c['required_files']['missing_important'][:3]}")
    pa = c['plan_actionability']
    if pa['missing_checklists']:
        gaps.append('plan.md has no checklists (no "- [ ]" items)')
    if pa['missing_file_paths']:
        gaps.append('plan.md has no source file paths')
    if pa['missing_verify_commands']:
        gaps.append('plan.md has no verification commands (rg/grep/test)')
    ca = c['code_anchor_coverage']
    if ca.get('key_anchors_found', 0) < ca.get('key_anchors_total', 0):
        gaps.append(f"plan covers {ca.get('key_anchors_found', 0)}/{ca.get('key_anchors_total', 0)} key anchors")
    bq = c['blocker_quality']
    if bq['blocker_count'] > 0 and bq['quality_ratio'] < 0.5:
        gaps.append(f"blockers lack context ({bq['blockers_with_context']}/{bq['blocker_count']} have owner/suggestion)")
    return gaps[:6]


def fq_format_yaml(checks, overall_status, overall_score, gaps):
    lines = [f'schema_version: "1.0"', f'status: {overall_status}', f'score: {overall_score}', '', 'checks:']
    for check_name in CHECK_WEIGHTS:
        c = checks[check_name]
        lines.append(f'  {check_name}:')
        lines.append(f'    status: {c["status"]}')
        lines.append(f'    score: {c["score"]}')
        for k, v in c.items():
            if k in ('status', 'score'):
                continue
            if isinstance(v, bool):
                lines.append(f'    {k}: {str(v).lower()}')
            elif isinstance(v, str):
                lines.append(f'    {k}: "{v}"')
            elif isinstance(v, float):
                lines.append(f'    {k}: {v}')
            elif isinstance(v, int):
                lines.append(f'    {k}: {v}')
            elif isinstance(v, list):
                if not v:
                    lines.append(f'    {k}: []')
                else:
                    lines.append(f'    {k}:')
                    for item in v:
                        lines.append(f'      - "{item}"')
    lines.append('')
    lines.append('summary:')
    lines.append(f'  top_gaps:')
    for g in (gaps or ['"no significant gaps"']):
        lines.append(f'    - "{g}"')
    lines.append('')
    return '\n'.join(lines)


def run_final(base):
    report_text = read_safe(base / 'report.md')
    plan_text = read_safe(base / 'plan.md')

    checks = {}
    checks['required_files'] = _fq_required_files(base)
    checks['context_pack_consumed'] = _fq_context_pack_consumed(base, report_text, plan_text)
    checks['code_anchor_coverage'] = _fq_code_anchor_coverage(base, plan_text)
    checks['plan_actionability'] = _fq_plan_actionability(plan_text)
    checks['blocker_quality'] = _fq_blocker_quality(report_text)
    checks['section_structure'] = _fq_section_structure(base)

    overall_status, overall_score = fq_compute_overall(checks)
    gaps = fq_collect_gaps(checks)
    yaml_out = fq_format_yaml(checks, overall_status, overall_score, gaps)
    out_path = base / 'context' / 'final-quality-gate.yaml'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml_out, encoding='utf-8')

    print(f'\n  Status: {overall_status.upper()}')
    print(f'  Score:  {overall_score}/100\n')
    for name, c in checks.items():
        sym = {'pass': '+', 'warning': '!', 'fail': 'x'}[c['status']]
        print(f'  [{sym}] {name:30s} score={c["score"]:3d}  ({c["status"]})')
    if gaps:
        print('\n  Top gaps:')
        for g in gaps:
            print(f'    - {g}')
    print(f'\nWritten: {out_path}')


# ══════════════════════════════════════════════════════════════
# REFERENCE: Quality checks
# ══════════════════════════════════════════════════════════════

RQ_REQUIRED_FILES = [
    'project-profile.yaml', '01-codebase.yaml', '02-coding-rules.yaml',
    '03-contracts.yaml', '04-routing-playbooks.yaml', '05-domain.yaml',
]
RQ_REQUIRED_INDEX = ['entities.json', 'edges.json', 'inverted-index.json', 'manifest.yaml']

RQ_VAGUE_STAT = [re.compile(r':\s*[0-9][0-9,]*\+\s*(?:#.*)?$'),
                 re.compile(r':\s*["\'][^"\']*[0-9][0-9,]*\+[^"\']*["\']')]
RQ_PLACEHOLDER_OWNER = [re.compile(r'owner:\s*(growth-team|team|unknown|todo|tbd)\s*$', re.I),
                        re.compile(r'contact:\s*["\']?#(?:[a-z0-9_-]+)["\']?\s*$', re.I)]


def _rq_yaml_readable(path):
    text = read_safe(path)
    return bool(text.strip()) and '\x00' not in text


def _rq_schema_version(path):
    text = read_safe(path)
    return bool(text.strip()) and bool(re.search(r'^schema_version:\s*.+', text, re.M))


def _rq_has_evidence(lines, idx, window=8):
    snippet = '\n'.join(lines[max(0, idx - window):min(len(lines), idx + window + 1)])
    return bool(re.search(r'^\s*(evidence|verified_by|source|locator):\s*\S+', snippet, re.M))


def _rq_evidence_warnings(ref_dir):
    warnings = []
    for f in RQ_REQUIRED_FILES:
        path = ref_dir / f
        if not path.exists():
            continue
        lines = read_safe(path).splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if any(p.search(stripped) for p in RQ_VAGUE_STAT):
                warnings.append({'file': f, 'line': idx + 1, 'reason': 'vague_numeric_claim', 'text': stripped[:140]})
            if any(p.search(stripped) for p in RQ_PLACEHOLDER_OWNER):
                if not _rq_has_evidence(lines, idx):
                    warnings.append({'file': f, 'line': idx + 1, 'reason': 'owner_or_contact_without_evidence', 'text': stripped[:140]})
            if re.search(r'confidence:\s*high\b', stripped, re.I):
                if not _rq_has_evidence(lines, idx):
                    warnings.append({'file': f, 'line': idx + 1, 'reason': 'high_confidence_without_nearby_evidence', 'text': stripped[:140]})
    return warnings


def run_reference_quality(root):
    ref_dir = Path(root) / '_prd-tools' / 'reference'
    index_dir = ref_dir / 'index'

    results = {}
    # required_files
    missing, empty = [], []
    for f in RQ_REQUIRED_FILES:
        p = ref_dir / f
        if not p.exists():
            missing.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)
    results['required_files'] = {'status': 'fail' if missing or empty else 'pass', 'missing': missing, 'empty': empty}

    # index_files
    ix_missing, ix_empty = [], []
    for f in RQ_REQUIRED_INDEX:
        p = index_dir / f
        if not p.exists():
            ix_missing.append(f)
        elif p.stat().st_size == 0:
            ix_empty.append(f)
    results['index_files'] = {'status': 'fail' if ix_missing or ix_empty else 'pass', 'missing': ix_missing, 'empty': ix_empty}

    # yaml_readable
    failed_yaml = [f for f in RQ_REQUIRED_FILES if f.endswith('.yaml')
                   and (ref_dir / f).exists() and not _rq_yaml_readable(ref_dir / f)]
    results['yaml_readable'] = {'status': 'warning' if failed_yaml else 'pass', 'failed': failed_yaml}

    # schema_version
    missing_sv = [f for f in RQ_REQUIRED_FILES if (ref_dir / f).exists() and not _rq_schema_version(ref_dir / f)]
    results['schema_version'] = {'status': 'warning' if missing_sv else 'pass', 'missing': missing_sv}

    # evidence_claims
    warnings = _rq_evidence_warnings(ref_dir)
    results['evidence_claims'] = {'status': 'warning' if warnings else 'pass', 'warnings': warnings}
    return results


def print_reference_quality(results):
    print('\n=== Reference Quality Gate ===\n')
    for key, label in [('required_files', 'required files'), ('index_files', 'index files'),
                        ('yaml_readable', 'yaml readable'), ('schema_version', 'schema_version'),
                        ('evidence_claims', 'evidence claim smells')]:
        r = results[key]
        sym = '+' if r['status'] == 'pass' else ('!' if r['status'] == 'warning' else 'x')
        print(f'  [{sym}] {label}: {r["status"]}')
        for detail_key in ('missing', 'empty', 'failed', 'warnings'):
            if r.get(detail_key):
                items = r[detail_key]
                if isinstance(items, list) and items and isinstance(items[0], dict):
                    for item in items[:12]:
                        print(f'      {item.get("file", "")}:{item.get("line", "")} {item.get("reason", "")}: {item.get("text", "")}')
                    if len(items) > 12:
                        print(f'      ... and {len(items) - 12} more')
                else:
                    print(f'      {detail_key}: {items}')
    print()


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description='Unified Quality Gate for prd-tools')
    sub = ap.add_subparsers(dest='command', required=True)

    # distill
    p_distill = sub.add_parser('distill', help='Quality + coverage checks for /prd-distill output')
    p_distill.add_argument('--distill-dir', '--distill', dest='distill_dir', required=True,
                           help='Path to distill output directory')
    p_distill.add_argument('--repo-root', '--repo', dest='repo_root', required=True,
                           help='Project root directory')
    p_distill.add_argument('--mode', choices=['quality', 'coverage', 'all'], default='quality',
                           help='Gate mode (default: quality)')

    # final
    p_final = sub.add_parser('final', help='Weighted scoring for distill deliverables')
    p_final.add_argument('--distill-dir', '--distill', dest='distill_dir', required=True,
                         help='Path to distill output directory')

    # reference
    p_ref = sub.add_parser('reference', help='Quality checks for /reference output')
    p_ref.add_argument('--root', required=True, help='Project root directory')

    args = ap.parse_args()

    if args.command == 'distill':
        base = Path(args.distill_dir).resolve()
        repo_root = Path(args.repo_root).resolve()
        if not base.is_dir():
            print(f'Error: {base} is not a directory', file=sys.stderr)
            sys.exit(1)
        print(f'Distill dir: {base}')
        print(f'Repo root:   {repo_root}')
        print(f'Mode:        {args.mode}')
        all_results, exit_code = {}, 0
        if args.mode in ('quality', 'all'):
            all_results['quality'] = run_distill_quality(base, repo_root)
            print_distill_quality(all_results['quality'])
        if args.mode in ('coverage', 'all'):
            all_results['coverage'] = run_distill_coverage(str(base))
            print_distill_coverage(all_results['coverage'])
            _write_coverage_report(str(base), all_results['coverage'])
            if any(r.get("status") == "fail" and n in FATAL_COVERAGE_CHECKS for n, r in all_results['coverage'].items()):
                exit_code = 2
        for group in all_results.values():
            exit_code = max(exit_code, compute_exit_code(group))
        if exit_code == 2:
            print('RESULT: FAIL')
        elif has_warnings({k: v for g in all_results.values() for k, v in g.items()}):
            print('RESULT: PASS with warnings')
        else:
            print('RESULT: PASS')
        sys.exit(exit_code)

    elif args.command == 'final':
        base = Path(args.distill_dir).resolve()
        if not base.is_dir():
            print(f'Error: {base} is not a directory', file=sys.stderr)
            sys.exit(1)
        print(f'Distill dir: {base}')
        run_final(base)

    elif args.command == 'reference':
        root = Path(args.root).resolve()
        if not root.is_dir():
            print(f'Error: {root} is not a directory', file=sys.stderr)
            sys.exit(1)
        print(f'Root: {root}')
        results = run_reference_quality(root)
        print_reference_quality(results)
        exit_code = compute_exit_code(results)
        if exit_code == 2:
            print('RESULT: FAIL')
        elif has_warnings(results):
            print('RESULT: PASS with warnings')
        else:
            print('RESULT: PASS')
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
