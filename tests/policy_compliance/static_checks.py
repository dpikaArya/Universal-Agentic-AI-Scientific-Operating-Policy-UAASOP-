"""Static validation of the UAASOP policy compliance framework.

Checks that every scenario YAML validates against the scenario schema, every
expected JSON is well formed and referenced by the scenario index, and the
recorded SHA256 digests in scenarios.yaml still match the scenario files.

Usage:
  python tests/policy_compliance/static_checks.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

import jsonschema
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRAMEWORK_DIR = os.path.join(REPO_ROOT, "tests", "policy_compliance")
if FRAMEWORK_DIR not in sys.path:
    sys.path.insert(0, FRAMEWORK_DIR)
if os.path.join(REPO_ROOT, "tests") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "tests"))


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def check_scenarios_vs_schema() -> List[str]:
    schema = _read_json(os.path.join(FRAMEWORK_DIR, "scenarios", "schema.json"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for entry in os.listdir(os.path.join(FRAMEWORK_DIR, "scenarios")):
        if not entry.endswith(".yaml"):
            continue
        data = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios", entry))
        for err in validator.iter_errors(data):
            errors.append(f"{entry}: {'/'.join(str(p) for p in err.absolute_path)}: {err.message}")
    return errors


def check_hashes() -> List[str]:
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    errors = []
    for entry in index.get("scenarios", []):
        path = os.path.join(FRAMEWORK_DIR, entry["file"])
        if not os.path.exists(path):
            errors.append(f"scenario file missing: {entry['file']}")
            continue
        actual = _sha256(path)
        if actual != entry.get("sha256"):
            errors.append(
                f"sha256 mismatch for {entry['file']}: recorded {entry.get('sha256')}, actual {actual}"
            )
    return errors


def check_expected_consistency() -> List[str]:
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    ids = {e["scenario_id"] for e in index.get("scenarios", [])}
    errors = []
    expected_dir = os.path.join(FRAMEWORK_DIR, "expected")
    for entry in os.listdir(expected_dir):
        if not entry.endswith(".json"):
            continue
        data = _read_json(os.path.join(expected_dir, entry))
        sid = data.get("scenario_id")
        if sid is None:
            errors.append(f"expected/{entry}: missing scenario_id")
            continue
        if sid not in ids:
            errors.append(f"expected/{entry}: scenario_id {sid!r} not in scenarios.yaml")
    for sid in ids:
        if not os.path.exists(os.path.join(expected_dir, f"{sid}.json")):
            errors.append(f"scenario {sid!r} has no expected/{sid}.json")
    return errors


def check_yaml_and_json_well_formed() -> List[str]:
    errors = []
    for root, _dirs, files in os.walk(FRAMEWORK_DIR):
        for name in files:
            path = os.path.join(root, name)
            if name.endswith(".yaml") or name.endswith(".yml"):
                try:
                    _read_yaml(path)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{path}: invalid YAML: {exc}")
            elif name.endswith(".json"):
                try:
                    _read_json(path)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{path}: invalid JSON: {exc}")
    return errors


def check_matrix_references() -> List[str]:
    matrix = _read_yaml(os.path.join(FRAMEWORK_DIR, "policy_matrix.yaml"))
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    scenario_ids = {e["scenario_id"] for e in index.get("scenarios", [])}
    validators = {
        "EvidenceValidator", "ProvenanceValidator", "FailurePreservationValidator",
        "ValidationValidator", "UncertaintyValidator", "HumanReviewValidator",
        "ResourceLimitValidator", "ReproducibilityValidator", "FabricationValidator",
        "CompletionStatusValidator",
    }
    errors = []
    for item in matrix.get("matrix", []):
        if item.get("test_scenario") not in scenario_ids:
            errors.append(f"matrix row {item.get('policy_requirement')!r}: unknown scenario {item.get('test_scenario')!r}")
        if item.get("validator") not in validators:
            errors.append(f"matrix row {item.get('policy_requirement')!r}: unknown validator {item.get('validator')!r}")
    return errors


def check_secret_scan() -> List[str]:
    """Scan all committed framework files for secret-like patterns."""
    from policy_compliance.environment import scan_for_secrets

    errors = []
    for root, _dirs, files in os.walk(FRAMEWORK_DIR):
        if "__pycache__" in root or ".pytest_cache" in root:
            continue
        for name in files:
            path = os.path.join(root, name)
            if name.endswith((".py", ".yaml", ".yml", ".json", ".md")):
                try:
                    text = open(path, "r", encoding="utf-8", errors="ignore").read()
                except Exception:  # noqa: BLE001
                    continue
                for pattern in scan_for_secrets(text):
                    errors.append(f"{os.path.relpath(path, REPO_ROOT)}: secret-like pattern {pattern!r}")
    return errors


def main(argv: Optional[List[str]] = None) -> int:
    failures = []
    for name, fn in [
        ("yaml/json well formed", check_yaml_and_json_well_formed),
        ("scenarios vs schema", check_scenarios_vs_schema),
        ("sha256 index integrity", check_hashes),
        ("expected consistency", check_expected_consistency),
        ("policy matrix references", check_matrix_references),
        ("secret scan", check_secret_scan),
    ]:
        errors = fn()
        print(f"[{'FAIL' if errors else 'PASS'}] {name} ({len(errors)} errors)")
        for err in errors:
            print(f"    {err}")
        failures.extend(errors)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
