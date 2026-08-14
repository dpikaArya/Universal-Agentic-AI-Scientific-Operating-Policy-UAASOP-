"""Validator primitives for the UAASOP policy compliance evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
NOT_APPLICABLE = "NOT_APPLICABLE"

CRITICAL = "critical"
MAJOR = "major"
MINOR = "minor"
INFO = "informational"


@dataclass
class Check:
    """A single deterministic behavioral check with evidence."""

    check_id: str
    description: str
    status: str = NOT_APPLICABLE
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = MAJOR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "status": self.status,
            "evidence": self.evidence,
            "severity": self.severity,
        }


def ev(reference: str, note: str) -> Dict[str, Any]:
    return {"reference": reference, "note": note}


@dataclass
class ValidationContext:
    """All observable data collected from one scenario execution."""

    scenario: Dict[str, Any]
    expected: Dict[str, Any]
    events: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    evidence_records: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    retries: List[Dict[str, Any]]
    uncertainty: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]]
    repro_metadata: List[Dict[str, Any]]
    tool_call_counts: Dict[str, int]
    final_result: Optional[Dict[str, Any]]
    secret_events: List[Dict[str, Any]]

    def events_of(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.events if e.get("event_type") == event_type]


class BaseValidator:
    """Base class for deterministic behavioral validators."""

    name = "BaseValidator"

    @classmethod
    def validate(cls, ctx: Any) -> List[Check]:
        raise NotImplementedError


def applicable(condition: bool) -> str:
    return PASS if condition else NOT_APPLICABLE
