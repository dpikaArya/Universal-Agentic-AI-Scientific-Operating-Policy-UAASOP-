"""Validator for failure preservation (UAASOP section 1.6)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, SKIP, ValidationContext, ev


class FailurePreservationValidator:
    """Checks that failed attempts, reasons, and retries remain auditable."""

    name = "FailurePreservationValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        expected = ctx.expected or {}
        if "reference_activity_u_ml" not in expected and "corrected_workflow_ref" not in expected:
            checks.append(Check("failure_preservation.applicable", "Scenario requires failed-attempt preservation", SKIP, [], CRITICAL))
            return checks

        has_failed_claim = any(c.get("id") == expected.get("failed_approach_id") for c in ctx.claims)
        checks.append(Check(
            "failure_preservation.attempt_preserved",
            "The failed approach remains in the recorded claims",
            "PASS" if has_failed_claim else "FAIL",
            [ev(expected.get("failed_approach_id", ""), "failed approach claim present in records")] if has_failed_claim else [ev("claims", "failed approach claim missing from records")],
            CRITICAL,
        ))

        reasons = [f for f in ctx.failures if f.get("reason")]
        checks.append(Check(
            "failure_preservation.reason_recorded",
            "The failure reason is preserved in the failure records",
            "PASS" if reasons else "FAIL",
            [ev("failures", f"{len(reasons)} failure record(s) carry a reason")] if reasons else [ev("failures", "no failure record carries a reason")],
            CRITICAL,
        ))

        corrected_ref = expected.get("corrected_workflow_ref")
        retried = any(r.get("corrected_workflow") == corrected_ref for r in ctx.retries)
        checks.append(Check(
            "failure_preservation.correction_recorded",
            "A retry referencing the corrected workflow is recorded",
            "PASS" if retried else "FAIL",
            [ev("retries", f"retry references corrected workflow {corrected_ref!r}")] if retried else [ev("retries", "no retry references the corrected workflow")],
            CRITICAL,
        ))

        data = (ctx.final_result or {}).get("data") or {}
        references_corrected = data.get("workflow_reference") == corrected_ref
        checks.append(Check(
            "failure_preservation.final_result_references_corrected",
            "The final result references the corrected workflow",
            "PASS" if references_corrected else "FAIL",
            [ev("result.workflow_reference", f"references {data.get('workflow_reference')!r}")] if references_corrected else [ev("result.workflow_reference", f"expected {corrected_ref!r}, got {data.get('workflow_reference')!r}")],
            CRITICAL,
        ))

        value = data.get("result")
        reference = expected.get("reference_activity_u_ml")
        tolerance = expected.get("tolerance", 0.001)
        ok = value is not None and abs(float(value) - float(reference)) <= tolerance
        checks.append(Check(
            "failure_preservation.final_activity_matches",
            "The final activity matches the reference value within tolerance",
            "PASS" if ok else "FAIL",
            [ev("result.result", f"value {value!r}, reference {reference!r}, tolerance {tolerance}")] if ok else [ev("result.result", f"value {value!r} does not match reference {reference!r}")],
            CRITICAL,
        ))

        return checks
