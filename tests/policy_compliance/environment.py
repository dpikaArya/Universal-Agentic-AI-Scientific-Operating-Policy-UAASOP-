"""Deterministic mock environment for the UAASOP policy compliance evaluation.

The mock environment is the observable world in which an agent runs a scenario.
Every tool call, record, validation, approval, and produced artifact is captured
as an event so that behavior can be validated without access to private model
reasoning.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---- observable event types ----------------------------------------------
POLICY_ACCESS = "policy_access"
CONFIG_ACCESS = "config_access"
INSTRUCTIONS_ACCESS = "instructions_access"
DECISION_RECORDED = "decision_recorded"
EVIDENCE_RETRIEVED = "evidence_retrieved"
EVIDENCE_RECORDED = "evidence_recorded"
CALCULATION_PERFORMED = "calculation_performed"
CLAIM_RECORDED = "claim_recorded"
UNCERTAINTY_RECORDED = "uncertainty_recorded"
FAILURE_RECORDED = "failure_recorded"
RETRY_RECORDED = "retry_recorded"
VALIDATION_PERFORMED = "validation_performed"
APPROVAL_REQUESTED = "approval_requested"
APPROVAL_RECEIVED = "approval_received"
APPROVAL_DENIED = "approval_denied"
APPROVAL_BYPASSED = "approval_bypassed"
PROVENANCE_RECORDED = "provenance_recorded"
ARTIFACT_PRODUCED = "artifact_produced"
COMPLETION_CLAIMED = "completion_claimed"
COMPLETION_QUALIFIED = "completion_qualified"
TOOL_CALL = "tool_call"
TOOL_FORBIDDEN = "tool_forbidden"
TOOL_FAILURE = "tool_failure"
REPRO_METADATA_RECORDED = "repro_metadata_recorded"
CITATION_LOOKUP = "citation_lookup"
TRACE_VERIFIED = "trace_verified"
SECRET_LEAKED = "secret_leaked"

EVENT_TYPES = {
    POLICY_ACCESS,
    CONFIG_ACCESS,
    INSTRUCTIONS_ACCESS,
    DECISION_RECORDED,
    EVIDENCE_RETRIEVED,
    EVIDENCE_RECORDED,
    CALCULATION_PERFORMED,
    CLAIM_RECORDED,
    UNCERTAINTY_RECORDED,
    FAILURE_RECORDED,
    RETRY_RECORDED,
    VALIDATION_PERFORMED,
    APPROVAL_REQUESTED,
    APPROVAL_RECEIVED,
    APPROVAL_DENIED,
    APPROVAL_BYPASSED,
    PROVENANCE_RECORDED,
    ARTIFACT_PRODUCED,
    COMPLETION_CLAIMED,
    COMPLETION_QUALIFIED,
    TOOL_CALL,
    TOOL_FORBIDDEN,
    TOOL_FAILURE,
    REPRO_METADATA_RECORDED,
    CITATION_LOOKUP,
    TRACE_VERIFIED,
    SECRET_LEAKED,
}

# Secret patterns used by the secret scanner. All fixtures are synthetic; no
# real credentials ever enter this framework.
SECRET_PATTERNS: List[tuple] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic_secret", re.compile(r"(?i)(secret|password|api[_-]?key|token)[^0-9A-Za-z]{0,6}[:=][^\s]{8,}")),
]


def scan_for_secrets(texts: Any) -> List[str]:
    """Return the names of secret patterns found in the given text or records."""
    if not isinstance(texts, (list, tuple)):
        texts = [texts]
    found: List[str] = []
    for text in texts:
        if not isinstance(text, str):
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text) and name not in found:
                found.append(name)
    return found


class ToolFailure(Exception):
    """Deterministic tool failure raised by the mock environment."""

    def __init__(self, message: str, failure_type: str = "tool_failure"):
        super().__init__(message)
        self.message = message
        self.failure_type = failure_type


class EventLog:
    """Append-only machine readable event log for one scenario execution."""

    def __init__(self, execution_id: str, agent_id: str):
        self.execution_id = execution_id
        self.agent_id = agent_id
        self._events: List[Dict[str, Any]] = []

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def record(
        self,
        event_type: str,
        tool: Optional[str] = None,
        input_reference: Optional[str] = None,
        output_reference: Optional[str] = None,
        decision: Optional[str] = None,
        failure_status: Optional[str] = None,
        failure_type: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event type: {event_type}")
        payload = dict(extra or {})
        event = {
            "event_id": "evt-" + uuid.uuid4().hex[:12],
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
            "timestamp": self._now(),
            "event_type": event_type,
            "tool": tool,
            "input_reference": input_reference,
            "output_reference": output_reference,
            "decision": decision,
            "failure_status": failure_status,
            "failure_type": failure_type,
        }
        event["extra"] = payload
        self._events.append(event)
        if event_type != SECRET_LEAKED:
            text = " ".join([str(decision or ""), json.dumps(payload)])
            for name in scan_for_secrets(text):
                self._events.append({
                    "event_id": "evt-" + uuid.uuid4().hex[:12],
                    "execution_id": self.execution_id,
                    "agent_id": self.agent_id,
                    "timestamp": self._now(),
                    "event_type": SECRET_LEAKED,
                    "tool": tool,
                    "input_reference": input_reference,
                    "decision": f"secret-like pattern detected: {name}",
                    "extra": {"pattern": name},
                })
        return event

    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    def events_of(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self._events if e["event_type"] == event_type]

    def count(self, event_type: str) -> int:
        return len(self.events_of(event_type))


class ArtifactStore:
    """Stores observable artifacts produced by an agent."""

    def __init__(self) -> None:
        self._artifacts: List[Dict[str, Any]] = []

    def produce(self, artifact_type: str, data: Dict[str, Any], reference: Optional[str] = None) -> str:
        ref = reference or f"artifact:{artifact_type}:{len(self._artifacts) + 1}"
        self._artifacts.append({"reference": ref, "type": artifact_type, "data": data})
        return ref

    def all(self) -> List[Dict[str, Any]]:
        return list(self._artifacts)

    def last_of_type(self, artifact_type: str) -> Optional[Dict[str, Any]]:
        for artifact in reversed(self._artifacts):
            if artifact["type"] == artifact_type:
                return artifact
        return None


class ProvenanceStore:
    """Append-only store of provenance records."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        rec = dict(record)
        rec.setdefault("id", "prov-" + uuid.uuid4().hex[:12])
        rec.setdefault("created_at", datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
        self._records.append(rec)
        return rec

    def all(self) -> List[Dict[str, Any]]:
        return list(self._records)


def _coerce_scalar(value: Any) -> Any:
    return value


class MockEnvironment:
    """Deterministic environment exposing the mock tool surface.

    The environment enforces the scenario allowlist and resource limits, so any
    forbidden or excessive tool use is observable in the event log.
    """

    def __init__(
        self,
        scenario: Dict[str, Any],
        repo_root: Optional[str] = None,
        execution_id: Optional[str] = None,
        agent_id: str = "mock-agent",
        seed: int = 42,
    ):
        self.scenario = scenario
        self.repo_root = repo_root or os.getcwd()
        self.execution_id = execution_id or ("exec-" + uuid.uuid4().hex[:12])
        self.seed = seed
        self.event_log = EventLog(self.execution_id, agent_id)
        self.artifacts = ArtifactStore()
        self.provenance = ProvenanceStore()

        self._mock = scenario.get("mock_behavior", {}) or {}
        self._evidence = self._mock.get("evidence", []) or []
        self._calculations = self._mock.get("calculations", []) or []
        self._approval_rules = self._mock.get("approvals", []) or []
        self._tool_failures = self._mock.get("failures", []) or []
        self._query_data = self._mock.get("query_data", []) or []
        self._allowed_tools = set(scenario.get("allowed_tools") or [])
        self._limits = scenario.get("resource_limits", {}) or {}

        self._tool_call_count: Dict[str, int] = {}
        self._validation_calls: Dict[str, int] = {}
        self._approval_state: Dict[str, str] = {}

        self._evidence_records: List[Dict[str, Any]] = []
        self._claims: List[Dict[str, Any]] = []
        self._failures: List[Dict[str, Any]] = []
        self._retries: List[Dict[str, Any]] = []
        self._uncertainty: List[Dict[str, Any]] = []
        self._approvals: List[Dict[str, Any]] = []
        self._repro_metadata: List[Dict[str, Any]] = []

        self._citation_cache: Optional[List[Dict[str, Any]]] = None
        self._tools = self._build_tools()

    # ---- registry --------------------------------------------------------
    def _build_tools(self) -> Dict[str, Any]:
        tools: Dict[str, Any] = {
            "read_policy": self._read_policy,
            "read_config": self._read_config,
            "read_instructions": self._read_instructions,
            "discover_data": self._discover_data,
            "retrieve_evidence": self._retrieve_evidence,
            "calculate": self._calculate,
            "validate": self._validate,
            "record_claim": self._record_claim,
            "record_evidence": self._record_evidence,
            "record_failure": self._record_failure,
            "record_retry": self._record_retry,
            "record_uncertainty": self._record_uncertainty,
            "record_decision": self._record_decision,
            "request_approval": self._request_approval,
            "get_approval_status": self._get_approval_status,
            "record_approval": self._record_approval,
            "produce_result": self._produce_result,
            "record_provenance": self._record_provenance,
            "record_repro_metadata": self._record_repro_metadata,
            "record_trace": self._record_trace,
            "lookup_citation": self._lookup_citation,
            "query_database": self._query_database,
            "summarize": self._summarize,
            "network_fetch": self._network_fetch,
        }
        return tools

    def tools(self) -> List[str]:
        return sorted(self._tools)

    # ---- public call surface --------------------------------------------
    def call(self, tool: str, **kwargs: Any) -> Any:
        call_no = self._tool_call_count.get(tool, 0) + 1
        self._tool_call_count[tool] = call_no
        input_reference = kwargs.get("_input") or kwargs.get("input_reference")
        decision = kwargs.pop("_decision", None) or f"invoked {tool!r}"

        if tool not in self._tools:
            self.event_log.record(
                TOOL_CALL, tool=tool, input_reference=input_reference,
                failure_status="unknown_tool", decision=f"called unknown tool {tool!r}",
                extra={"call_number": call_no},
            )
            return {"error": f"unknown tool {tool!r}"}

        if tool not in self._allowed_tools:
            self.event_log.record(
                TOOL_CALL, tool=tool, input_reference=input_reference,
                failure_status="forbidden_tool", decision=f"attempted forbidden tool {tool!r}",
                extra={"call_number": call_no},
            )
            self.event_log.record(
                TOOL_FORBIDDEN, tool=tool, input_reference=input_reference,
                decision=f"tool {tool!r} is not permitted in this scenario",
                extra={"call_number": call_no},
            )
            return {"error": "forbidden_tool", "tool": tool}

        max_calls = self._limits.get(tool, {}).get("max_calls")
        if max_calls is not None and call_no > max_calls:
            self.event_log.record(
                TOOL_CALL, tool=tool, input_reference=input_reference,
                failure_status="resource_limit", decision=f"resource limit exceeded for {tool!r}",
                extra={"call_number": call_no, "limit": max_calls},
            )
            self.event_log.record(
                TOOL_FAILURE, tool=tool, input_reference=input_reference,
                failure_status=f"resource limit of {max_calls} exceeded",
                failure_type="resource_limit", decision=f"{tool!r} exceeded its limit",
                extra={"call_number": call_no, "limit": max_calls},
            )
            raise ToolFailure(f"resource limit of {max_calls} exceeded", failure_type="resource_limit")

        for failure in self._tool_failures:
            if failure.get("tool") != tool:
                continue
            if call_no <= failure.get("times_fail", 1):
                self.event_log.record(
                    TOOL_CALL, tool=tool, input_reference=input_reference,
                    failure_status=failure.get("error", "failed"),
                    decision=f"tool {tool!r} failed as scripted",
                    extra={"call_number": call_no},
                )
                self.event_log.record(
                    TOOL_FAILURE, tool=tool, input_reference=input_reference,
                    failure_status=failure.get("error", "failed"),
                    failure_type=failure.get("type", "tool_failure"),
                    decision=f"tool {tool!r} failed as scripted",
                    extra={"call_number": call_no},
                )
                raise ToolFailure(failure.get("error", "tool failed"), failure_type=failure.get("type", "tool_failure"))

        self.event_log.record(
            TOOL_CALL, tool=tool, input_reference=input_reference, decision=decision,
            extra={"call_number": call_no},
        )
        handler = self._tools[tool]
        return handler(**kwargs)

    # ---- shared tool handlers -------------------------------------------
    def _read_policy(self, **_kwargs: Any) -> Dict[str, Any]:
        self.event_log.record(
            POLICY_ACCESS, tool="read_policy", input_reference="SCIENTIFIC_AGENT_POLICY.md",
            decision="accessed canonical policy",
            extra={"policy_file": "SCIENTIFIC_AGENT_POLICY.md"},
        )
        return {"policy": "SCIENTIFIC_AGENT_POLICY.md", "version": "0.1.0"}

    def _read_config(self, **_kwargs: Any) -> Dict[str, Any]:
        self.event_log.record(
            CONFIG_ACCESS, tool="read_config", input_reference="AGENT_CONFIG.yaml",
            decision="accessed machine readable policy configuration",
        )
        return {"config": "AGENT_CONFIG.yaml"}

    def _read_instructions(self, **_kwargs: Any) -> Dict[str, Any]:
        self.event_log.record(
            INSTRUCTIONS_ACCESS, tool="read_instructions", input_reference="AGENTS.md",
            decision="accessed repository agent instructions",
        )
        return {"instructions": "AGENTS.md"}

    def _discover_data(self, **_kwargs: Any) -> Dict[str, Any]:
        ids = [item.get("id") for item in self._evidence]
        return {"evidence_ids": ids}

    def _retrieve_evidence(self, evidence_id: str = None, **_kwargs: Any) -> Dict[str, Any]:
        target = evidence_id
        if target is None:
            raise ToolFailure("evidence_id is required")
        for item in self._evidence:
            if item.get("id") == target:
                self.event_log.record(
                    EVIDENCE_RETRIEVED, tool="retrieve_evidence", input_reference=target,
                    decision=f"retrieved evidence {target!r}", extra={"status": item.get("status")},
                )
                return dict(item)
        raise ToolFailure(f"evidence {target!r} not available", failure_type="evidence_missing")

    def _calculate(self, calc_id: str = None, **_kwargs: Any) -> Dict[str, Any]:
        target = calc_id
        if target is None:
            raise ToolFailure("calc_id is required")
        for item in self._calculations:
            if item.get("id") == target:
                self.event_log.record(
                    CALCULATION_PERFORMED, tool="calculate", input_reference=target,
                    decision=f"performed calculation {target!r}", extra={"output": item.get("output")},
                )
                return {"id": target, "output": item.get("output"), "status": "calculated"}
        raise ToolFailure(f"calculation {target!r} not available", failure_type="calculation_missing")

    def _validate(self, target: str = None, **_kwargs: Any) -> Dict[str, Any]:
        if target is None:
            raise ToolFailure("target is required")
        call_no = self._validation_calls.get(target, 0) + 1
        self._validation_calls[target] = call_no
        rule = next((r for r in (self.scenario.get("validation_rules") or []) if r.get("target") == target), None)
        outcome = rule.get("expected_outcome", "passed") if rule else "passed"
        reason = rule.get("reason", "") if rule else ""
        if rule:
            cumulative = 0
            for failure in rule.get("scripted_failures", []) or []:
                cumulative += failure.get("times", 1)
                if call_no <= cumulative:
                    outcome = failure.get("outcome", "failed")
                    reason = failure.get("reason", "")
                    break
        self.event_log.record(
            VALIDATION_PERFORMED, tool="validate", input_reference=target,
            decision=f"validated {target!r}: {outcome}",
            extra={"validation_status": outcome, "reason": reason, "call_number": call_no},
        )
        return {"target": target, "outcome": outcome, "reason": reason}

    def _record_claim(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._claims.append(rec)
        self.event_log.record(
            CLAIM_RECORDED, tool="record_claim", output_reference=rec.get("id"),
            decision=rec.get("claim"), extra={"status": rec.get("status"), "evidence": rec.get("evidence", [])},
        )
        return {"recorded": True, "id": rec.get("id")}

    def _record_evidence(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._evidence_records.append(rec)
        self.event_log.record(
            EVIDENCE_RECORDED, tool="record_evidence", output_reference=rec.get("id"),
            decision=f"recorded evidence {rec.get('id')}", extra={"status": rec.get("status"), "value": rec.get("value")},
        )
        return {"recorded": True, "id": rec.get("id")}

    def _record_failure(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._failures.append(rec)
        self.event_log.record(
            FAILURE_RECORDED, tool="record_failure", output_reference=rec.get("id"),
            decision=f"recorded failure {rec.get('id')}", extra={"reason": rec.get("reason"), "tool": rec.get("tool")},
        )
        return {"recorded": True, "id": rec.get("id")}

    def _record_retry(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._retries.append(rec)
        self.event_log.record(
            RETRY_RECORDED, tool="record_retry", output_reference=rec.get("id"),
            decision=f"recorded retry {rec.get('id')}", extra={"corrected_workflow": rec.get("corrected_workflow")},
        )
        return {"recorded": True, "id": rec.get("id")}

    def _record_uncertainty(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._uncertainty.append(rec)
        self.event_log.record(
            UNCERTAINTY_RECORDED, tool="record_uncertainty", input_reference=rec.get("item"),
            decision=rec.get("note") or "recorded uncertainty", extra={"status": rec.get("status")},
        )
        return {"recorded": True}

    def _record_decision(self, description: str = None, **kwargs: Any) -> Dict[str, Any]:
        self.event_log.record(
            DECISION_RECORDED, tool="record_decision", decision=description or "decision",
            extra=kwargs,
        )
        return {"recorded": True}

    def _request_approval(self, action: str = None, reason: str = None, **kwargs: Any) -> Dict[str, Any]:
        if action is None:
            raise ToolFailure("action is required")
        rule = next((a for a in self._approval_rules if a.get("action") == action), None)
        required = bool(rule.get("required", True)) if rule else True
        if not required:
            return {"action": action, "status": "not_required", "required": False}
        self.event_log.record(
            APPROVAL_REQUESTED, tool="request_approval", input_reference=action,
            decision=f"requested human approval for {action!r}", extra={"reason": reason},
        )
        initial = "approved" if (rule and rule.get("auto_approve")) else "pending"
        self._approval_state[action] = initial
        return {"action": action, "status": initial, "required": True}

    def _get_approval_status(self, action: str = None, **kwargs: Any) -> Dict[str, Any]:
        if action is None:
            raise ToolFailure("action is required")
        status = self._approval_state.get(action, "not_requested")
        if status == "pending":
            rule = next((a for a in self._approval_rules if a.get("action") == action), None)
            status = "approved" if (rule and rule.get("auto_approve")) else "denied"
            self._approval_state[action] = status
        if status == "approved":
            self.event_log.record(
                APPROVAL_RECEIVED, tool="get_approval_status", input_reference=action,
                decision=f"human approval received for {action!r}",
            )
        elif status == "denied":
            self.event_log.record(
                APPROVAL_DENIED, tool="get_approval_status", input_reference=action,
                decision=f"human approval denied for {action!r}",
            )
        return {"action": action, "status": status}

    def _record_approval(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._approvals.append(rec)
        self.event_log.record(
            DECISION_RECORDED, tool="record_approval", input_reference=rec.get("action"),
            decision=f"recorded human decision {rec.get('status')} for {rec.get('action')}",
            extra={"by": rec.get("by")},
        )
        return {"recorded": True}

    def _produce_result(self, artifact_type: str = "final_result", data: Dict[str, Any] = None, reference: str = None, **kwargs: Any) -> str:
        data = data or {}
        ref = self.artifacts.produce(artifact_type, data, reference)
        self.event_log.record(
            ARTIFACT_PRODUCED, tool="produce_result", output_reference=ref,
            decision=f"produced artifact {ref!r}", extra={"artifact_type": artifact_type},
        )
        return ref

    def _record_provenance(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self.provenance.record(rec)
        self.event_log.record(
            PROVENANCE_RECORDED, tool="record_provenance", output_reference=rec.get("id"),
            decision="recorded provenance",
            extra={"chain": rec.get("chain", []), "tools": rec.get("tool", [])},
        )
        return {"recorded": True, "id": rec.get("id")}

    def _record_repro_metadata(self, record: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        rec = record or kwargs.get("_record") or {}
        self._repro_metadata.append(rec)
        self.event_log.record(
            REPRO_METADATA_RECORDED, tool="record_repro_metadata",
            decision="recorded reproducibility metadata", extra={"fields": sorted(rec)},
        )
        return {"recorded": True}

    def _record_trace(self, note: str = None, **kwargs: Any) -> Dict[str, Any]:
        self.event_log.record(
            TRACE_VERIFIED, tool="record_trace",
            decision=note or "confirmed provenance chain from output to evidence",
        )
        return {"traceable": True}

    def _lookup_citation(self, key: str = None, **kwargs: Any) -> Dict[str, Any]:
        if key is None:
            raise ToolFailure("citation key is required")
        if self._citation_cache is None:
            path = os.path.join(self.repo_root, "tests", "policy_compliance", "fixtures", "reference_catalog.json")
            entries: List[Dict[str, Any]] = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as handle:
                    entries = json.load(handle).get("entries", [])
            self._citation_cache = entries
        entry = next((e for e in self._citation_cache if e.get("key") == key), None)
        found = entry is not None
        self.event_log.record(
            CITATION_LOOKUP, tool="lookup_citation", input_reference=key,
            decision=f"looked up citation {key!r}: {'found' if found else 'not found'}",
            extra={"found": found},
        )
        return {"key": key, "found": found, "entry": entry}

    def _query_database(self, query: str = None, **kwargs: Any) -> Dict[str, Any]:
        row = next((r for r in self._query_data if r.get("key") == query), None)
        self.event_log.record(
            TOOL_CALL, tool="query_database", input_reference=query,
            decision=f"queried metrics database for {query!r}",
            extra={"key": query},
        )
        if row is None:
            return {"key": query, "found": False}
        return dict(row)

    def _summarize(self, rows: Any = None, **kwargs: Any) -> Dict[str, Any]:
        rows = rows or []
        summary = "synthetic metrics summary"
        self.event_log.record(
            TOOL_CALL, tool="summarize", decision="summarized retrieved metrics",
            extra={"rows": len(rows)},
        )
        return {"summary": summary, "rows": rows}

    def _network_fetch(self, url: str = None, **kwargs: Any) -> Dict[str, Any]:
        # Handler exists but the environment blocks the call unless permitted.
        return {"error": "forbidden"}

    # ---- observable state accessors --------------------------------------
    def events(self) -> List[Dict[str, Any]]:
        return self.event_log.events()

    def events_of(self, event_type: str) -> List[Dict[str, Any]]:
        return self.event_log.events_of(event_type)

    def tool_call_counts(self) -> Dict[str, int]:
        return dict(self._tool_call_count)

    def artifacts_all(self) -> List[Dict[str, Any]]:
        return self.artifacts.all()

    def final_result(self) -> Optional[Dict[str, Any]]:
        return self.artifacts.last_of_type("final_result")

    def provenance_all(self) -> List[Dict[str, Any]]:
        return self.provenance.all()

    def recorded_claims(self) -> List[Dict[str, Any]]:
        return list(self._claims)

    def recorded_evidence(self) -> List[Dict[str, Any]]:
        return list(self._evidence_records)

    def recorded_failures(self) -> List[Dict[str, Any]]:
        return list(self._failures)

    def recorded_retries(self) -> List[Dict[str, Any]]:
        return list(self._retries)

    def recorded_uncertainty(self) -> List[Dict[str, Any]]:
        return list(self._uncertainty)

    def recorded_approvals(self) -> List[Dict[str, Any]]:
        return list(self._approvals)

    def repro_metadata(self) -> List[Dict[str, Any]]:
        return list(self._repro_metadata)

    def approval_state(self) -> Dict[str, str]:
        return dict(self._approval_state)


def policy_content_sha256(repo_root: str) -> str:
    """Content hash of the canonical policy for policy version tracking."""
    path = os.path.join(repo_root, "SCIENTIFIC_AGENT_POLICY.md")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def policy_semantic_version(repo_root: str) -> str:
    path = os.path.join(repo_root, "SCIENTIFIC_AGENT_POLICY.md")
    if not os.path.exists(path):
        return "unknown"
    with open(path, "r", encoding="utf-8") as handle:
        match = re.search(r"Version\s*:\s*\*+\s*([\w.\-]+)", handle.read(4000), re.IGNORECASE)
    return match.group(1) if match else "unknown"
