"""Tests for the UAASOP Agent Policy Compliance Evaluation framework.

These tests validate the framework itself and prove that the deterministic
mock environment can distinguish a compliant agent from a violating one.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

import jsonschema
import pytest
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRAMEWORK_DIR = os.path.join(REPO_ROOT, "tests", "policy_compliance")
sys.path.insert(0, os.path.join(REPO_ROOT, "tests"))

from policy_compliance.adapter import MockAgentAdapter  # noqa: E402
from policy_compliance.agents import CompliantMockAgent, ViolatingMockAgent  # noqa: E402
from policy_compliance.environment import MockEnvironment, policy_content_sha256, policy_semantic_version, scan_for_secrets  # noqa: E402
from policy_compliance.runner import evaluate  # noqa: E402

SCENARIO_IDS = [
    "evidence_vs_inference",
    "failed_attempt",
    "validation_failure",
    "uncertainty",
    "source_conflict",
    "human_review",
    "tool_governance",
    "provenance",
    "reproducibility",
    "fabrication_resistance",
]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_scenarios():
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    scenarios = []
    for entry in index.get("scenarios", []):
        scenarios.append(_read_yaml(os.path.join(FRAMEWORK_DIR, entry["file"])))
    return scenarios


def _load_expected():
    expected = {}
    for entry in os.listdir(os.path.join(FRAMEWORK_DIR, "expected")):
        if entry.endswith(".json"):
            data = _read_json(os.path.join(FRAMEWORK_DIR, "expected", entry))
            expected[data.get("scenario_id")] = data
    return expected


@pytest.fixture(scope="module")
def scenarios():
    return _load_scenarios()


@pytest.fixture(scope="module")
def expected():
    return _load_expected()


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_scenario_spec_exists_and_matches_index(scenario_id):
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    entry = next((e for e in index["scenarios"] if e["scenario_id"] == scenario_id), None)
    assert entry is not None, f"scenario {scenario_id} missing from scenarios.yaml"
    path = os.path.join(FRAMEWORK_DIR, entry["file"])
    assert os.path.exists(path)
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    assert digest == entry["sha256"], f"sha256 mismatch for {scenario_id}"


def test_all_scenarios_validate_against_schema(scenarios):
    schema = _read_json(os.path.join(FRAMEWORK_DIR, "scenarios", "schema.json"))
    validator = jsonschema.Draft202012Validator(schema)
    for scenario in scenarios:
        errors = list(validator.iter_errors(scenario))
        assert not errors, f"{scenario['scenario_id']}: {[e.message for e in errors]}"


def test_every_scenario_has_expected_reference(expected):
    assert set(expected.keys()) == set(SCENARIO_IDS)


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_environment_enforces_allowlist(scenarios, expected, scenario_id):
    scenario = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    env = MockEnvironment(scenario=scenario, repo_root=REPO_ROOT, execution_id=f"exec-{scenario_id}")
    result = env.call("network_fetch", url="http://example.invalid/")
    assert result.get("error") == "forbidden_tool"
    forbidden = env.events_of("tool_forbidden")
    assert any(e.get("tool") == "network_fetch" for e in forbidden)


def test_secret_scanner_detects_known_patterns():
    assert "aws_access_key" in scan_for_secrets("AKIAIOSFODNN7EXAMPLE")
    assert "private_key" in scan_for_secrets("-----BEGIN RSA PRIVATE KEY-----\nabc")
    assert "generic_secret" in scan_for_secrets("password=supersecretvalue")


def test_policy_version_tracking():
    sha = policy_content_sha256(REPO_ROOT)
    assert len(sha) == 64
    version = policy_semantic_version(REPO_ROOT)
    assert version == "0.1.0"


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_compliant_agent_passes_all_scenarios(scenarios, expected, scenario_id):
    scenario = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    adapter = MockAgentAdapter(agent=CompliantMockAgent(), scenario=scenario, repo_root=REPO_ROOT)
    result = evaluate(scenario, expected.get(scenario_id), adapter, REPO_ROOT)
    assert result["status"] == "PASS", f"{scenario_id}: {result['violations']}"
    assert result["compliance_level"] == "4"
    assert result["score"] == 1.0
    assert not result["violations"]


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_violating_agent_fails_all_scenarios(scenarios, expected, scenario_id):
    scenario = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    adapter = MockAgentAdapter(agent=ViolatingMockAgent(), scenario=scenario, repo_root=REPO_ROOT)
    result = evaluate(scenario, expected.get(scenario_id), adapter, REPO_ROOT)
    assert result["status"] == "FAIL", f"{scenario_id}: expected non-compliance detected"


def test_all_results_conform_to_schema(scenarios, expected):
    schema = _read_json(os.path.join(REPO_ROOT, "schemas", "policy-compliance.schema.json"))
    validator = jsonschema.Draft202012Validator(schema)
    for scenario in scenarios:
        for agent in (CompliantMockAgent(), ViolatingMockAgent()):
            adapter = MockAgentAdapter(agent=agent, scenario=scenario, repo_root=REPO_ROOT)
            result = evaluate(scenario, expected.get(scenario.get("scenario_id")), adapter, REPO_ROOT)
            errors = list(validator.iter_errors(result))
            assert not errors, f"{scenario['scenario_id']} {agent.agent_id}: {[e.message for e in errors]}"


def test_secret_values_never_appear_in_results(scenarios, expected):
    for scenario in scenarios:
        adapter = MockAgentAdapter(agent=CompliantMockAgent(), scenario=scenario, repo_root=REPO_ROOT)
        result = evaluate(scenario, expected.get(scenario.get("scenario_id")), adapter, REPO_ROOT)
        blob = json.dumps(result)
        found = scan_for_secrets(blob)
        assert not found, f"{scenario['scenario_id']}: secret-like content in report {found}"
