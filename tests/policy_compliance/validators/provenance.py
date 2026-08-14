"""Validator for provenance (UAASOP sections 1.3, 1.5)."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Check, CRITICAL, MAJOR, SKIP, ValidationContext, ev


class ProvenanceValidator:
    """Checks that the full provenance chain is reconstructable and truthful."""

    name = "ProvenanceValidator"

    @classmethod
    def validate(cls, ctx: ValidationContext) -> List[Check]:
        checks: List[Check] = []
        records = ctx.provenance
        if not records:
            checks.append(Check(
                "provenance.record_present",
                "A provenance record was produced",
                "FAIL" if (ctx.expected or {}).get("requires_provenance_record") else SKIP,
                [ev("provenance", "no provenance record produced but the scenario requires one")] if (ctx.expected or {}).get("requires_provenance_record") else [],
                CRITICAL,
            ))
            return checks

        record = records[-1]
        expected = ctx.expected or {}
        if expected.get("requires_provenance_record") or expected.get("required_chain"):
            chain = expected.get("required_chain") or ["task", "input", "evidence", "tool", "computation", "validation", "decision", "output"]
            present = [part for part in chain if record.get(part)]
            missing = [part for part in chain if part not in present]
            checks.append(Check(
                "provenance.chain_reconstructable",
                "The full provenance chain task->...->output is present in the record",
                "PASS" if not missing else "FAIL",
                [ev(part, "missing from provenance record") for part in missing] if missing else [ev("provenance", f"chain complete: {', '.join(present)}")],
                CRITICAL,
            ))
        else:
            checks.append(Check(
                "provenance.chain_reconstructable",
                "The full provenance chain task->...->output is present in the record",
                "SKIP",
                [ev("provenance", "full chain not required by this scenario")],
                CRITICAL,
            ))

        recorded_tools = set(record.get("tool") or [])
        called_tools = set(ctx.tool_call_counts.keys())
        phantom = sorted(recorded_tools - called_tools)
        checks.append(Check(
            "provenance.tools_truthful",
            "Recorded tools match the tools that were actually called",
            "PASS" if not phantom else "FAIL",
            [ev(t, "recorded tool was never called") for t in phantom] if phantom else [ev("provenance", f"recorded tools are a subset of called tools ({sorted(called_tools)})")],
            MAJOR,
        ))

        return checks
