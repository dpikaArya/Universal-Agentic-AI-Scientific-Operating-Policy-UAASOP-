"""Command line entry point for the UAASOP Agent Policy Compliance Evaluation.

Usage:
  python tests/policy_compliance/run_compliance.py                     # both mock agents, all scenarios
  python tests/policy_compliance/run_compliance.py --agent compliant   # only the compliant mock agent
  python tests/policy_compliance/run_compliance.py --scenario provenance
  python tests/policy_compliance/run_compliance.py --json --report-dir reports/
  python tests/policy_compliance/run_compliance.py --demonstrate       # CI: exit 0 (expected FAILs allowed)

Exit codes:
  0  all results PASS (or --demonstrate, where expected mock-agent FAILs are tolerated)
  1  any result FAILed or a result failed schema validation
  2  usage/argument error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import jsonschema
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRAMEWORK_DIR = os.path.join(REPO_ROOT, "tests", "policy_compliance")
TESTS_DIR = os.path.join(REPO_ROOT, "tests")
sys.path.insert(0, TESTS_DIR)
sys.path.insert(0, REPO_ROOT)


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_scenarios() -> List[Dict[str, Any]]:
    index = _read_yaml(os.path.join(FRAMEWORK_DIR, "scenarios.yaml"))
    scenarios = []
    for entry in index.get("scenarios", []):
        path = os.path.join(FRAMEWORK_DIR, entry["file"])
        scenario = _read_yaml(path)
        scenario["scenario_file"] = entry["file"]
        scenarios.append(scenario)
    return scenarios


def load_expected() -> Dict[str, Dict[str, Any]]:
    expected = {}
    for entry in os.listdir(os.path.join(FRAMEWORK_DIR, "expected")):
        if entry.endswith(".json"):
            data = _read_json(os.path.join(FRAMEWORK_DIR, "expected", entry))
            expected[data.get("scenario_id")] = data
    return expected


def load_result_schema() -> Dict[str, Any]:
    return _read_json(os.path.join(REPO_ROOT, "schemas", "policy-compliance.schema.json"))


def validate_result(result: Dict[str, Any]) -> List[str]:
    schema = load_result_schema()
    validator = jsonschema.Draft202012Validator(schema)
    return sorted(e.message for e in validator.iter_errors(result))


def markdown_report(results: List[Dict[str, Any]]) -> str:
    lines = [
        "# UAASOP Agent Policy Compliance Evaluation",
        "",
        "Deterministic behavioral evaluation. Only observable behavior was inspected.",
        "",
        "| Scenario | Agent | Status | Level | Score | Violations |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['scenario_id']} | {r['agent_id']} | {r['status']} | "
            f"{r['compliance_level']} | {r['score']} | {len(r['violations'])} |"
        )
    lines.append("")
    for r in results:
        if r.get("violations"):
            lines.append(f"## {r['scenario_id']} - {r['agent_id']}")
            lines.append("")
            for v in r["violations"]:
                lines.append(f"- **{v['type']}** ({v['check_id']}): {v['description']}")
            lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the UAASOP behavioral compliance evaluation")
    parser.add_argument("--scenario", help="run only this scenario_id")
    parser.add_argument("--agent", choices=["compliant", "violating"], help="run only this mock agent")
    parser.add_argument("--json", action="store_true", help="emit raw JSON results to stdout")
    parser.add_argument("--report-dir", help="write JSON and Markdown reports to this directory")
    parser.add_argument(
        "--demonstrate",
        action="store_true",
        help="run the full mock-agent demonstration and exit 0 even when an agent FAILs "
        "(intended for CI: the violating mock agent is expected to FAIL; schema errors and "
        "exceptions still fail).",
    )
    args = parser.parse_args(argv)

    from policy_compliance.adapter import MockAgentAdapter
    from policy_compliance.agents import CompliantMockAgent, ViolatingMockAgent
    from policy_compliance.runner import evaluate

    scenarios = load_scenarios()
    if args.scenario:
        scenarios = [s for s in scenarios if s.get("scenario_id") == args.scenario]
        if not scenarios:
            print(f"error: unknown scenario {args.scenario!r}", file=sys.stderr)
            return 2
    expected = load_expected()

    agents = []
    if args.agent in (None, "compliant"):
        agents.append(("compliant", CompliantMockAgent()))
    if args.agent in (None, "violating"):
        agents.append(("violating", ViolatingMockAgent()))

    all_results: List[Dict[str, Any]] = []
    exit_code = 0
    for name, agent in agents:
        for scenario in scenarios:
            adapter = MockAgentAdapter(agent=agent, scenario=scenario, repo_root=REPO_ROOT)
            result = evaluate(scenario, expected.get(scenario.get("scenario_id"), {}), adapter, REPO_ROOT)
            all_results.append(result)
            schema_errors = validate_result(result)
            marker = "PASS" if result["status"] == "PASS" and not schema_errors else "FAIL"
            if schema_errors:
                exit_code = 1
            elif result["status"] != "PASS" and not args.demonstrate:
                exit_code = 1
            print(
                f"[{marker}] {result['agent_id']:22s} {result['scenario_id']:24s} "
                f"status={result['status']} level={result['compliance_level']} "
                f"score={result['score']} violations={len(result['violations'])}"
            )
            if schema_errors:
                for err in schema_errors:
                    print(f"  schema error: {err}")

    if args.json:
        print(json.dumps(all_results, indent=2))

    if args.report_dir:
        os.makedirs(args.report_dir, exist_ok=True)
        stamp = "compliance"
        with open(os.path.join(args.report_dir, f"{stamp}.json"), "w", encoding="utf-8") as handle:
            json.dump(all_results, handle, indent=2)
        with open(os.path.join(args.report_dir, f"{stamp}.md"), "w", encoding="utf-8") as handle:
            handle.write(markdown_report(all_results))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
