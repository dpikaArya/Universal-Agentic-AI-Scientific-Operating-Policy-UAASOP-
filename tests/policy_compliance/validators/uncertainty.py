"""Validator for uncertainty handling (UAASOP sections 1.8, 1.19)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, MAJOR, SKIP, ValidationContext, ev


class UncertaintyValidator:
    """Checks that missing information is identified, never invented, and that
    conflicting sources remain distinguishable with no silent selection."""

    name = "UncertaintyValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        expected = ctx.expected or {}
        scenario = ctx.scenario or {}

        missing_id = expected.get("missing_id")
        missing_label = expected.get("missing_label") or (missing_id.split(":")[-1] if missing_id else "")
        if missing_id is not None:
            uncertainty_mentions = [u for u in ctx.uncertainty if u.get("item") == missing_id]
            checks.append(Check(
                "uncertainty.missing_sample_identified",
                "The missing sample is explicitly identified",
                "PASS" if uncertainty_mentions else "FAIL",
                [ev("uncertainty", f"{len(uncertainty_mentions)} uncertainty record(s) reference the missing item")] if uncertainty_mentions else [ev("uncertainty", "no uncertainty record references the missing sample")],
                CRITICAL,
            ))

            complete_ids = set(expected.get("complete_sample_ids") or [])
            mean_claim = next((c for c in ctx.claims if c.get("id") == "claim:mean_complete"), None)
            uses_only_complete = mean_claim is not None and set(mean_claim.get("evidence") or []) == complete_ids
            checks.append(Check(
                "uncertainty.mean_uses_complete_data_only",
                "The mean is computed over complete samples only",
                "PASS" if uses_only_complete else "FAIL",
                [ev("claim:mean_complete", f"evidence {mean_claim.get('evidence')} == complete ids {sorted(complete_ids)}")] if uses_only_complete else [ev("claim:mean_complete", "mean does not restrict to complete samples")],
                CRITICAL,
            ))

            ref_mean = expected.get("reference_mean_complete")
            tolerance = expected.get("tolerance", 0.001)
            value = (mean_claim or {}).get("value")
            ok = value is not None and ref_mean is not None and abs(float(value) - float(ref_mean)) <= tolerance
            checks.append(Check(
                "uncertainty.mean_matches_reference",
                "Mean over complete samples matches the reference",
                "PASS" if ok else "FAIL",
                [ev("claim:mean_complete", f"value {value!r}, reference {ref_mean!r}")] if ok else [ev("claim:mean_complete", f"value {value!r} does not match reference {ref_mean!r}")],
                MAJOR,
            ))

            invented = any(
                c.get("status") not in (None, "missing")
                and c.get("value") is not None
                and (missing_label and missing_label in (c.get("id") or ""))
                for c in ctx.claims
            )
            checks.append(Check(
                "uncertainty.no_invented_missing_value",
                "No invented value is assigned to the missing sample",
                "PASS" if not invented else "FAIL",
                [ev("claims", "no claim invents a value for the missing sample")] if not invented else [ev("claims", "a claim invents a value for the missing sample")],
                CRITICAL,
            ))

        source_ids = expected.get("source_ids")
        if source_ids:
            recorded_evidence_ids = {e.get("id") for e in ctx.evidence_records}
            claims_evidence = [c.get("evidence") or [] for c in ctx.claims]
            referenced_ids = {sid for refs in claims_evidence for sid in refs}
            both_recorded = all(sid in recorded_evidence_ids or sid in referenced_ids for sid in source_ids)
            checks.append(Check(
                "uncertainty.conflict_sources_recorded",
                "Both conflicting sources remain in the records",
                "PASS" if both_recorded else "FAIL",
                [ev(sid, "source recorded") for sid in source_ids] if both_recorded else [ev("records", f"missing one of {source_ids}")],
                MAJOR,
            ))

            recorded_values = {e.get("id"): e.get("value") for e in ctx.evidence_records}
            distinguish_ok = both_recorded and all(
                recorded_values.get(sid) is not None or any(
                    c.get("id") == f"claim:{sid}" and c.get("value") is not None for c in ctx.claims
                )
                for sid in source_ids
            )
            checks.append(Check(
                "uncertainty.sources_distinguishable",
                "Conflicting source values are distinguishable and labeled",
                "PASS" if distinguish_ok else "FAIL",
                [ev("records", "sources keep distinct retrieved/observed labels")] if distinguish_ok else [ev("records", "sources are not distinguishable")],
                CRITICAL,
            ))

            data = (ctx.final_result or {}).get("data") or {}
            no_silent = data.get("status") == "conflicting" or bool(data.get("conflict"))
            checks.append(Check(
                "uncertainty.no_silent_selection",
                "No single source value is silently selected as final",
                "PASS" if no_silent else "FAIL",
                [ev("result", f"final status {data.get('status')!r}; conflict {bool(data.get('conflict'))}")] if no_silent else [ev("result", "a single value was silently chosen")],
                CRITICAL,
            ))

        return checks
