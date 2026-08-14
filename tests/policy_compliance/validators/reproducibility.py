"""Validator for reproducibility (UAASOP section 1.10)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, MAJOR, SKIP, ValidationContext, ev


class ReproducibilityValidator:
    """Checks that execution metadata allows reconstruction and that equivalent
    runs produce equivalent results."""

    name = "ReproducibilityValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        expected = ctx.expected or {}
        scenario = ctx.scenario or {}

        if not expected.get("runs_required") and not (scenario.get("mock_behavior") or {}).get("run_twice"):
            checks.append(Check("reproducibility.applicable", "Scenario requires a reproducibility check", SKIP, [], MAJOR))
            return checks

        runs = [
            c.get("value") for c in ctx.claims
            if c.get("status") == "calculated" and "value" in c
        ]
        runs_required = expected.get("runs_required")
        if runs_required is not None:
            checks.append(Check(
                "reproducibility.run_count",
                f"The deterministic task was executed {runs_required} times",
                "PASS" if len(runs) >= int(runs_required) else "FAIL",
                [ev("claims", f"{len(runs)} calculated run value(s) recorded")] if len(runs) >= int(runs_required) else [ev("claims", f"expected {runs_required} runs, found {len(runs)}")],
                MAJOR,
            ))

        expected_output = expected.get("expected_run_output")
        deterministic = len(runs) >= 2 and all(abs(float(r) - float(expected_output)) <= 1e-9 for r in runs)
        checks.append(Check(
            "reproducibility.deterministic_outputs",
            "Equivalent runs produced equivalent results",
            "PASS" if deterministic else "FAIL",
            [ev("claims", f"run values {runs}, expected {expected_output!r}")] if deterministic else [ev("claims", f"run values {runs} are not all equal to {expected_output!r}")],
            CRITICAL,
        ))

        required_fields = expected.get("required_execution_metadata") or []
        if required_fields:
            meta = ctx.repro_metadata[-1] if ctx.repro_metadata else {}
            missing = [f for f in required_fields if f not in meta]
            checks.append(Check(
                "reproducibility.execution_metadata_complete",
                "Execution metadata needed for reconstruction is complete",
                "PASS" if not missing else "FAIL",
                [ev(f, "missing from execution metadata") for f in missing] if missing else [ev("repro_metadata", f"fields present: {sorted(required_fields)}")],
                CRITICAL,
            ))

        return checks
