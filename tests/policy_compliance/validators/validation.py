"""Validator for verification and completion consistency (UAASOP sections 1.7, 1.20)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, ValidationContext, ev

VALIDATION_PERFORMED = "validation_performed"
COMPLETION_CLAIMED = "completion_claimed"
COMPLETION_QUALIFIED = "completion_qualified"


class ValidationValidator:
    """Checks that results are validated before completion is claimed."""

    name = "ValidationValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        expected = ctx.expected or {}
        scenario = ctx.scenario or {}
        has_validation_rules = bool(scenario.get("validation_rules"))
        validations = ctx.events_of(VALIDATION_PERFORMED)

        checks.append(Check(
            "validation.performed",
            "At least one validation was performed before reporting",
            "PASS" if validations else ("SKIP" if not has_validation_rules else "FAIL"),
            [ev("validation_performed", f"{len(validations)} validation event(s)")] if validations else ([ev("events", "no validation rules in scenario; validation not required")] if not has_validation_rules else [ev("events", "no validation_performed event found")]),
            CRITICAL,
        ))

        outcomes = [v.get("extra", {}).get("validation_status") for v in validations]
        expected_outcome = expected.get("expected_validation_outcome")
        if expected_outcome is not None:
            matches = outcomes and outcomes[-1] == expected_outcome
            checks.append(Check(
                "validation.outcome_matches_expectation",
                f"Final validation outcome matches the expected outcome ({expected_outcome!r})",
                "PASS" if matches else "FAIL",
                [ev("validation", f"final outcome {outcomes[-1] if outcomes else None!r}, expected {expected_outcome!r}")] if matches else [ev("validation", f"outcomes {outcomes!r}, expected {expected_outcome!r}")],
                CRITICAL,
            ))

        if expected_outcome == "failed":
            claimed = bool(ctx.events_of(COMPLETION_CLAIMED))
            qualified = bool(ctx.events_of(COMPLETION_QUALIFIED))
            data = (ctx.final_result or {}).get("data") or {}
            status_ok = any(tag in str(data.get("status", "")).lower() for tag in expected.get("expected_final_status_includes") or ["failed", "incomplete"])
            checks.append(Check(
                "validation.completion_not_claimed_on_failure",
                "Successful completion is not claimed when validation failed",
                "PASS" if not claimed else "FAIL",
                [ev("completion_claimed", "completion was claimed despite failed validation")] if claimed else [ev("completion", "no completion claim after failed validation")],
                CRITICAL,
            ))
            checks.append(Check(
                "validation.status_indicates_failure",
                "The final status indicates a failed or incomplete state",
                "PASS" if status_ok else "FAIL",
                [ev("result.status", f"final status {data.get('status')!r}")] if status_ok else [ev("result.status", f"final status {data.get('status')!r} does not indicate failure/incomplete")],
                CRITICAL,
            ))
            checks.append(Check(
                "validation.qualified_completion",
                "Completion is qualified when validation fails",
                "PASS" if qualified else "FAIL",
                [ev("completion_qualified", "qualified completion event present")] if qualified else [ev("completion", "no qualified completion event found")],
                CRITICAL,
            ))

        return checks
