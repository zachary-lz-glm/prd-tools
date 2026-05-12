#!/usr/bin/env python3
"""Artifact Contract Validator — 通用产物契约检查器

读取 .contract.yaml 定义的规则，检查实际产物是否符合。
支持 YAML 产物和 Markdown 产物。

退出码: 0 = pass/warning, 2 = fail
"""

import argparse
import os
import re
import sys
from typing import Any, Dict, List, Optional

import yaml


def _read_yaml(path: str) -> Optional[Dict]:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_path(data: Any, path: str) -> Any:
    """Resolve a dot-separated path in nested dict. Returns None if not found."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _resolve_wildcard_each(data: Any, path: str) -> List[Any]:
    """Resolve paths like 'layers.*.impacts' — collect all matching arrays."""
    parts = path.split(".")
    results = [data]
    for part in parts:
        next_results = []
        for item in results:
            if part == "*":
                if isinstance(item, dict):
                    next_results.extend(item.values())
            elif isinstance(item, dict):
                val = item.get(part)
                if val is not None:
                    if isinstance(val, list):
                        next_results.extend(val)
                    else:
                        next_results.append(val)
            elif isinstance(item, list):
                for elem in item:
                    if isinstance(elem, dict):
                        val = elem.get(part)
                        if val is not None:
                            next_results.append(val)
        results = next_results
    return results


# ──────────────────────────────────────────
# Rule evaluators
# ──────────────────────────────────────────

def _eval_path_rule(data: Dict, rule: Dict) -> Dict:
    """Evaluate a path-based rule (equals or exists)."""
    rule_id = rule["id"]
    path = rule["path"]
    value = _resolve_path(data, path)

    if "equals" in rule:
        expected = rule["equals"]
        if value == expected:
            return {"rule_id": rule_id, "status": "pass"}
        return {
            "rule_id": rule_id,
            "status": "fail",
            "message": f"{path} is {value!r}, expected {expected!r}",
        }

    if rule.get("exists"):
        if value is not None:
            return {"rule_id": rule_id, "status": "pass"}
        return {
            "rule_id": rule_id,
            "status": "fail",
            "message": f"{path} does not exist",
        }

    return {"rule_id": rule_id, "status": "pass"}


def _eval_each_rule(data: Dict, rule: Dict) -> Dict:
    """Evaluate an each-based rule (required fields, require expression, when/forbid)."""
    rule_id = rule["id"]
    each_path = rule["each"]

    if "*" in each_path:
        items = _resolve_wildcard_each(data, each_path)
    else:
        items = _resolve_path(data, each_path)

    if not items or not isinstance(items, list):
        return {"rule_id": rule_id, "status": "pass", "message": "no items to check"}

    findings = []

    if "required" in rule:
        required_fields = rule["required"]
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for field in required_fields:
                if field not in item or item[field] is None:
                    item_id = item.get("id", f"[{i}]")
                    findings.append(f"{item_id} missing field '{field}'")

    if "require" in rule:
        expr = rule["require"]
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            if not _eval_expression(item, expr):
                item_id = item.get("id", f"[{i}]")
                findings.append(f"{item_id} fails: {expr}")

    if "when" in rule and "forbid" in rule:
        when = rule["when"]
        forbid = rule["forbid"]
        when_field = when["field"]
        when_value = when["equals"]
        forbid_field = forbid["field"]
        forbid_value = forbid["equals"]

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            actual_when = _resolve_path(item, when_field)
            if actual_when == when_value:
                actual_forbid = _resolve_path(item, forbid_field)
                if actual_forbid == forbid_value:
                    item_id = item.get("id", f"[{i}]")
                    findings.append(
                        f"{item_id}: {forbid_field}={forbid_value!r} forbidden when {when_field}={when_value!r}"
                    )

    if findings:
        return {"rule_id": rule_id, "status": "fail", "findings": findings}
    return {"rule_id": rule_id, "status": "pass"}


def _eval_expression(item: Dict, expr: str) -> bool:
    """Evaluate a simple expression like 'len(evidence.source_blocks) > 0 or len(evidence.source_block_ids) > 0'."""
    if " or " in expr:
        parts = expr.split(" or ")
        return any(_eval_expression(item, p.strip()) for p in parts)

    if " and " in expr:
        parts = expr.split(" and ")
        return all(_eval_expression(item, p.strip()) for p in parts)

    # len(field) > 0
    m = re.match(r"len\(([^)]+)\)\s*>\s*(\d+)", expr)
    if m:
        field_path = m.group(1)
        threshold = int(m.group(2))
        val = _resolve_path(item, field_path)
        if isinstance(val, (list, str, dict)):
            return len(val) > threshold
        return False

    # field exists
    m = re.match(r"(\S+)\s+exists", expr)
    if m:
        field_path = m.group(1)
        return _resolve_path(item, field_path) is not None

    return True


# ──────────────────────────────────────────
# Markdown rules
# ──────────────────────────────────────────

def _eval_markdown_rule(content: str, rule: Dict) -> Dict:
    """Evaluate a markdown-specific rule."""
    rule_id = rule["id"]
    rule_type = rule.get("type", "")

    if rule_type == "heading_count":
        min_h2 = rule.get("min_h2", 0)
        h2_count = len(re.findall(r"^## ", content, re.MULTILINE))
        if h2_count >= min_h2:
            return {"rule_id": rule_id, "status": "pass"}
        return {
            "rule_id": rule_id,
            "status": "fail",
            "message": f"Found {h2_count} H2 headings, need >= {min_h2}",
        }

    if rule_type == "pattern_present":
        pattern = rule.get("pattern", "")
        if re.search(pattern, content):
            return {"rule_id": rule_id, "status": "pass"}
        return {
            "rule_id": rule_id,
            "status": "fail",
            "message": f"Pattern {pattern!r} not found in file",
        }

    return {"rule_id": rule_id, "status": "pass"}


# ──────────────────────────────────────────
# Main validation logic
# ──────────────────────────────────────────

def validate(artifact_path: str, contract: Dict) -> Dict:
    """Validate an artifact against a contract. Returns validation result dict."""
    artifact_type = contract.get("type", "yaml")
    rules = contract.get("rules", contract.get("required_rules", []))
    required_top_level = contract.get("required_top_level", [])

    if not os.path.isfile(artifact_path):
        return {
            "status": "skip",
            "message": f"Artifact not found: {artifact_path}",
            "findings": [],
        }

    if artifact_type == "markdown":
        with open(artifact_path, "r", encoding="utf-8") as f:
            content = f.read()
        results = []
        for rule in rules:
            results.append(_eval_markdown_rule(content, rule))
    else:
        data = _read_yaml(artifact_path)
        if data is None:
            return {"status": "fail", "message": "Failed to parse YAML", "findings": []}

        results = []

        for key in required_top_level:
            if key not in data:
                results.append({
                    "rule_id": f"required_top_level_{key}",
                    "status": "fail",
                    "message": f"Missing top-level key: {key}",
                })

        for rule in rules:
            if "path" in rule:
                results.append(_eval_path_rule(data, rule))
            elif "each" in rule:
                results.append(_eval_each_rule(data, rule))

    has_fail = any(r.get("status") == "fail" for r in results)
    has_warning = any(r.get("status") == "warning" for r in results)

    findings = []
    for r in results:
        if r.get("status") != "pass":
            entry = {"rule_id": r["rule_id"], "status": r["status"]}
            if "message" in r:
                entry["message"] = r["message"]
            if "findings" in r:
                entry["details"] = r["findings"]
            findings.append(entry)

    status = "fail" if has_fail else ("warning" if has_warning else "pass")
    return {"status": status, "findings": findings}


def main():
    parser = argparse.ArgumentParser(description="Artifact Contract Validator")
    parser.add_argument("--artifact", required=True, help="Path to artifact file")
    parser.add_argument("--contract", required=True, help="Path to contract YAML")
    args = parser.parse_args()

    contract = _read_yaml(args.contract)
    if not contract:
        print(f"ERROR: Cannot read contract: {args.contract}", file=sys.stderr)
        sys.exit(1)

    result = validate(args.artifact, contract)

    print(f"\n=== Artifact Contract: {os.path.basename(args.contract)} ===")
    print(f"  Artifact: {args.artifact}")
    print(f"  Status: {result['status']}")
    if result.get("findings"):
        for f in result["findings"]:
            sym = "x" if f["status"] == "fail" else "!"
            print(f"  [{sym}] {f['rule_id']}: {f.get('message', '')}")
            if "details" in f:
                for d in f["details"][:5]:
                    print(f"      - {d}")
    else:
        print("  [+] All rules passed")

    sys.exit(2 if result["status"] == "fail" else 0)


if __name__ == "__main__":
    main()
