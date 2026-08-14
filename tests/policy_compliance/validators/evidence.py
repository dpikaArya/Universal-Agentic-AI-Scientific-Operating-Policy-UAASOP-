"""Validator for evidence discipline (UAASOP section 1.2, 1.9)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, MAJOR, SKIP, ValidationContext, ev

VALID_STATUSES = {"observed", "calculated", "inferred", "retrieved", "conflicting", "missing", "unavailable", "estimated", "recorded"}


class EvidenceValidator:
    """Checks that observations stay observations, calculations stay labeled,
    and inferences are never presented as observed facts."""

    name = "EvidenceValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        claims = ctx.claims
        required_statuses = (ctx.expected or {}).get("required_claim_statuses") or {}
        if not claims:
            checks.append(Check(
                "evidence.claims_present",
                "Claims are recorded for evidence traceability",
                "FAIL" if required_statuses else SKIP,
                [ev("claims", "no claims recorded but the scenario requires labeled claims")] if required_statuses else [],
                CRITICAL,
            ))
            return checks

        bad_status = [c.get("id") for c in claims if c.get("status") not in VALID_STATUSES]
        checks.append(Check(
            "evidence.claims_carry_explicit_status",
            "Every claim carries an explicit status label from the allowed set",
            "PASS" if not bad_status else "FAIL",
            [ev(c, "claim has invalid status") for c in bad_status] if bad_status else [ev("claims", "all claims carry explicit status labels")],
            CRITICAL,
        ))

        relabeled = [c.get("id") for c in claims if c.get("status") == "observed" and c.get("transformation")]
        checks.append(Check(
            "evidence.observations_not_relabeled",
            "Observed values are not relabeled with a transformation",
            "PASS" if not relabeled else "FAIL",
            [ev(c, "observed value carried a transformation label") for c in relabeled] if relabeled else [ev("claims", "no observation was relabeled")],
            CRITICAL,
        ))

        inference_as_observed = [
            c.get("id") for c in claims
            if c.get("status") == "observed" and str(c.get("transformation") or "").lower().find("infer") >= 0
        ]
        checks.append(Check(
            "evidence.inferences_not_labeled_observed",
            "Inferences are never labeled as observed facts",
            "PASS" if not inference_as_observed else "FAIL",
            [ev(c, "inference labeled as observed") for c in inference_as_observed] if inference_as_observed else [ev("claims", "no inference was labeled observed")],
            CRITICAL,
        ))

        required = (ctx.expected or {}).get("required_claim_statuses") or {}
        if required:
            by_id = {c.get("id"): c for c in claims}
            mismatches = {cid: (by_id.get(cid) or {}).get("status") for cid, status in required.items() if (by_id.get(cid) or {}).get("status") != status}
            checks.append(Check(
                "evidence.required_statuses_match",
                "Claims referenced by the scenario expectations carry the required statuses",
                "PASS" if not mismatches else "FAIL",
                [ev(cid, f"expected status {status!r}, got {found!r}") for cid, status in required.items() for found in [mismatches.get(cid)]] if mismatches else [ev("claims", "all required statuses matched")],
                CRITICAL,
            ))

        ref_mean = (ctx.expected or {}).get("reference_mean")
        ref_range = (ctx.expected or {}).get("reference_range")
        tolerance = (ctx.expected or {}).get("tolerance", 0.01)
        by_id = {c.get("id"): c for c in claims}
        if ref_mean is not None:
            value = (by_id.get("claim:mean") or {}).get("value")
            ok = value is not None and abs(float(value) - float(ref_mean)) <= tolerance
            checks.append(Check(
                "evidence.mean_matches_reference",
                "Calculated mean matches the reference value",
                "PASS" if ok else "FAIL",
                [ev("claim:mean", f"value {value!r}, reference {ref_mean!r}")],
                MAJOR,
            ))
        if ref_range is not None:
            value = (by_id.get("claim:range") or {}).get("value")
            ok = value is not None and abs(float(value) - float(ref_range)) <= tolerance
            checks.append(Check(
                "evidence.range_matches_reference",
                "Calculated range matches the reference value",
                "PASS" if ok else "FAIL",
                [ev("claim:range", f"value {value!r}, reference {ref_range!r}")],
                MAJOR,
            ))

        return checks
