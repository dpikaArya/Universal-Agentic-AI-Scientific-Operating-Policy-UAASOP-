"""Registry of behavioral validators for the UAASOP compliance evaluation."""

from __future__ import annotations

from typing import Dict, List, Type

from .base import BaseValidator, ValidationContext
from .completion_status import CompletionStatusValidator
from .evidence import EvidenceValidator
from .fabrication import FabricationValidator
from .failure_preservation import FailurePreservationValidator
from .human_review import HumanReviewValidator
from .provenance import ProvenanceValidator
from .reproducibility import ReproducibilityValidator
from .resource_limit import ResourceLimitValidator
from .uncertainty import UncertaintyValidator
from .validation import ValidationValidator

ALL_VALIDATORS: List[Type[BaseValidator]] = [
    EvidenceValidator,
    ProvenanceValidator,
    FailurePreservationValidator,
    ValidationValidator,
    UncertaintyValidator,
    HumanReviewValidator,
    ResourceLimitValidator,
    ReproducibilityValidator,
    FabricationValidator,
    CompletionStatusValidator,
]

VALIDATOR_REGISTRY: Dict[str, Type[BaseValidator]] = {v.name: v for v in ALL_VALIDATORS}


def run_all_validators(ctx: ValidationContext) -> List[Dict[str, object]]:
    """Run every validator against a scenario execution and return check dicts."""
    checks = []
    for validator in ALL_VALIDATORS:
        for check in validator.validate(ctx):
            checks.append(check.to_dict())
    return checks


__all__ = ["ALL_VALIDATORS", "VALIDATOR_REGISTRY", "run_all_validators"]
