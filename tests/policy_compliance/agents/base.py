"""Deterministic compliant mock agent.

Implements the UAASOP default workflow (UNDERSTAND -> PLAN -> INSPECT ->
EXECUTE -> VALIDATE -> TRACE -> REVIEW -> REPORT) against the mock
environment. It is intended to pass every applicable compliance scenario:
evidence stays labeled, failures are preserved, validation is enforced,
uncertainty is recorded, human review is requested, provenance is complete,
reproducibility metadata is kept, and nothing is fabricated.
"""

from __future__ import annotations

import platform
from typing import Any, Dict, List, Optional

from ..environment import COMPLETION_CLAIMED, COMPLETION_QUALIFIED, ToolFailure

DEFAULT_PROFILE: Dict[str, Any] = {
    "policy_discovery": True,
    "record_decisions": True,
    "record_evidence": True,
    "record_claims": True,
    "record_failures": True,
    "record_retries": True,
    "preserve_failed_attempts": True,
    "request_approval": True,
    "record_approvals": True,
    "record_uncertainty": True,
    "record_provenance": True,
    "record_repro_metadata": True,
    "validate_output": True,
    "retry_after_failure": True,
    "run_twice": True,
}


class CompliantMockAgent:
    """Deterministic scripted agent that follows UAASOP behavior."""

    agent_id = "CompliantMockAgent"
    model_id = "deterministic-mock"
    model_version = "mock-1.0.0"

    def __init__(self, profile: Optional[Dict[str, Any]] = None, seed: int = 42):
        self.profile = dict(DEFAULT_PROFILE)
        if profile:
            self.profile.update(profile)
        self.seed = seed
        self.scenario: Dict[str, Any] = {}
        self.env: Any = None
        self._evidence_seen: List[Dict[str, Any]] = []
        self._validation_results: List[Dict[str, Any]] = []
        self._unavailable_citations: List[str] = []
        self._citations_found: List[str] = []
        self._missing_ids: List[str] = []
        self._workflow_reference: Optional[str] = None
        self._result_value: Any = None
        self._query_rows: List[Dict[str, Any]] = []
        self._final_result_ref: Optional[str] = None
        self._has_conflict = False
        self._has_inference = False
        self._completion_claimed = False
        self._completion_qualified = False

    def _p(self, key: str, default: Any = False) -> Any:
        return self.profile.get(key, default)

    # ---- public API ------------------------------------------------------
    def run(self, scenario: Dict[str, Any], env: Any) -> "CompliantMockAgent":
        self.scenario = scenario
        self.env = env
        self._evidence_seen = []
        self._validation_results = []
        self._unavailable_citations = []
        self._citations_found = []
        self._missing_ids = []
        self._workflow_reference = None
        self._result_value = None
        self._query_rows = []
        self._final_result_ref = None
        self._has_conflict = False
        self._has_inference = False
        self._completion_claimed = False
        self._completion_qualified = False

        self._preflight()
        self._understand()
        self._execute()
        self._validate()
        self._uncertainty()
        self._review()
        self._trace()
        self._report()
        self._provenance()
        self._repro()
        return self

    # ---- workflow phases -------------------------------------------------
    def _preflight(self) -> None:
        if self._p("policy_discovery"):
            self.env.call("read_policy")
            self.env.call("read_config")
            self.env.call("read_instructions")

    def _understand(self) -> None:
        if self._p("record_decisions"):
            task = self.scenario.get("scientific_task", "")
            self.env.call(
                "record_decision",
                description=f"UNDERSTAND: restated scientific question for {self.scenario.get('scenario_id')}: {task[:120]}",
            )

    def _execute(self) -> None:
        self._handle_citations()
        self._retrieve_evidence_records()
        self._run_queries()
        self._run_steps()

    def _handle_citations(self) -> None:
        for citation in self.scenario.get("mock_behavior", {}).get("requested_citations", []) or []:
            key = citation.get("key")
            result = self.env.call("lookup_citation", key=key)
            if result.get("found"):
                self._citations_found.append(key)
                if self._p("record_claims"):
                    entry = result.get("entry") or {}
                    self.env.call(
                        "record_claim",
                        record={
                            "id": f"claim:citation:{key}",
                            "claim": entry.get("title", key),
                            "status": "retrieved",
                            "evidence": [],
                            "transformation": f"verified against reference catalog: {entry.get('journal', '')}",
                        },
                    )
            else:
                self._unavailable_citations.append(key)

    def _retrieve_evidence_records(self) -> None:
        available = self.env.call("discover_data")
        for evidence_id in available.get("evidence_ids", []):
            try:
                evidence = self.env.call("retrieve_evidence", evidence_id=evidence_id)
            except ToolFailure:
                continue
            self._evidence_seen.append(evidence)
            if evidence.get("status") == "missing":
                self._missing_ids.append(evidence_id)
            if self._p("record_evidence"):
                self._record_evidence_record(evidence)

    def _record_evidence_record(self, evidence: Dict[str, Any]) -> None:
        record = {
            "id": evidence.get("id"),
            "content": evidence.get("content"),
            "status": evidence.get("status"),
            "value": evidence.get("value"),
            "source": evidence.get("source"),
            "source_type": evidence.get("source_type"),
        }
        self.env.call("record_evidence", record=record)

    def _run_queries(self) -> None:
        for query in self.scenario.get("mock_behavior", {}).get("queries", []) or []:
            row = self.env.call("query_database", query=query)
            if row.get("found", True):
                self._query_rows.append(row)

    def _run_steps(self) -> None:
        steps = self.scenario.get("mock_behavior", {}).get("analysis_steps", []) or []
        run_twice = bool((self.scenario.get("mock_behavior", {}) or {}).get("run_twice")) and self._p("run_twice")
        for step in steps:
            if step.get("phase") == "corrected":
                continue
            self._execute_step(step)
            if run_twice and step.get("calculate"):
                repeat = dict(step)
                repeat["target"] = step.get("target") + "_run2"
                self._execute_step(repeat)

    def _execute_step(self, step: Dict[str, Any]) -> None:
        step_type = step.get("type")
        if step_type == "record":
            self._record_claim(step)
            return
        if step_type == "conflict":
            self._has_conflict = True
            self._record_claim(step)
            return
        if step_type in ("inference", "decision"):
            self._has_inference = True
            self._record_claim(step)
            return
        if step_type == "consequential":
            self._record_claim(step)
            return
        if step_type == "summarize":
            self.env.call("summarize", rows=self._query_rows)
            self._result_value = self._query_rows
            return
        calc_id = step.get("calculate")
        if not calc_id:
            return
        try:
            result = self.env.call("calculate", calc_id=calc_id)
        except ToolFailure as exc:
            self._handle_scripted_failure(step, exc)
            return
        value = result.get("output")
        if step.get("phase") == "corrected" or self._workflow_reference is None:
            self._workflow_reference = calc_id
        self._result_value = value
        self._record_claim(step, value=value)

    def _handle_scripted_failure(self, step: Dict[str, Any], exc: ToolFailure) -> None:
        calc_id = step.get("calculate")
        if self._p("record_failures") and self._p("preserve_failed_attempts"):
            self.env.call(
                "record_failure",
                record={"id": f"failure:tool:{calc_id}", "tool": "calculate", "reason": exc.message, "phase": "attempt"},
            )
        if self._p("record_retries"):
            self.env.call("record_retry", record={"id": f"retry:{calc_id}", "tool": "calculate", "outcome": "retried"})
        result = self.env.call("calculate", calc_id=calc_id)
        value = result.get("output")
        self._result_value = value
        self._record_claim(step, value=value)

    def _record_claim(self, step: Dict[str, Any], value: Any = None) -> None:
        status = step.get("status", "calculated")
        claim_record: Dict[str, Any] = {
            "id": step.get("target"),
            "claim": step.get("transformation", "derived " + str(step.get("target"))),
            "status": status,
            "evidence": step.get("evidence") or [],
            "transformation": step.get("transformation"),
        }
        if value is not None:
            claim_record["value"] = value
        if self._p("record_claims"):
            self.env.call("record_claim", record=claim_record)

    def _corrective_step(self) -> Optional[Dict[str, Any]]:
        steps = self.scenario.get("mock_behavior", {}).get("analysis_steps", []) or []
        for step in steps:
            if step.get("phase") == "corrected":
                return step
        return None

    def _validate(self) -> None:
        if not self._p("validate_output"):
            return
        for rule in self.scenario.get("validation_rules", []) or []:
            target = rule.get("target")
            for attempt in range(1, 4):
                result = self.env.call("validate", target=target)
                self._validation_results = [r for r in self._validation_results if r.get("target") != target]
                self._validation_results.append(result)
                if result.get("outcome") == "passed":
                    break
                if self._p("record_failures"):
                    self.env.call(
                        "record_failure",
                        record={
                            "id": f"failure:validation:{target}:{attempt}",
                            "tool": "validate",
                            "reason": result.get("reason"),
                            "target": target,
                            "phase": "validation",
                        },
                    )
                if attempt == 1:
                    corrective = self._corrective_step()
                    if corrective:
                        if self._p("record_retries"):
                            self.env.call(
                                "record_retry",
                                record={
                                    "id": f"retry:{target}:{attempt}",
                                    "tool": "calculate",
                                    "corrected_workflow": corrective.get("calculate"),
                                    "phase": "corrected",
                                },
                            )
                        self._execute_step(corrective)
                        continue
                if self._p("record_retries"):
                    self.env.call(
                        "record_retry",
                        record={"id": f"retry:{target}:{attempt}", "tool": "validate", "phase": "revalidation"},
                    )

    def _uncertainty(self) -> None:
        if not self._p("record_uncertainty"):
            return
        for evidence_id in self._missing_ids:
            self.env.call(
                "record_uncertainty",
                record={"item": evidence_id, "status": "missing", "note": "value is missing, not fabricated"},
            )
        if self._has_inference:
            self.env.call(
                "record_uncertainty",
                record={"item": self.scenario.get("scenario_id"), "status": "inferred", "note": "inference carries epistemic uncertainty"},
            )
        if self._has_conflict:
            self.env.call(
                "record_uncertainty",
                record={"item": "conflict:mp", "status": "conflicting", "note": "sources disagree; conflict preserved"},
            )
        for key in self._unavailable_citations:
            self.env.call(
                "record_uncertainty",
                record={"item": f"citation:{key}", "status": "unavailable", "note": "citation not found in catalog; information unavailable"},
            )
        if any(r.get("outcome") != "passed" for r in self._validation_results):
            self.env.call(
                "record_uncertainty",
                record={"item": self.scenario.get("scenario_id"), "status": "validation_failed", "note": "validation did not pass; result is not final"},
            )

    def _review(self) -> None:
        for approval in self.scenario.get("mock_behavior", {}).get("approvals", []) or []:
            if not approval.get("required", True):
                continue
            if not self._p("request_approval"):
                continue
            requested = self.env.call("request_approval", action=approval.get("action"), reason=approval.get("reason"))
            status = self.env.call("get_approval_status", action=approval.get("action")).get("status")
            if self._p("record_approvals"):
                self.env.call(
                    "record_approval",
                    record={"action": approval.get("action"), "status": status, "by": "human", "decision": "recorded human decision"},
                )
            self._approval_outcome = status

    def _trace(self) -> None:
        self.env.call("record_trace", note="verified provenance chain from output to evidence")

    def _report(self) -> None:
        validation_failed = any(r.get("outcome") != "passed" for r in self._validation_results)
        data: Dict[str, Any] = {}
        if validation_failed:
            data = {
                "result": self._result_value,
                "status": "incomplete",
                "validation": "failed",
                "completion": "execution completed; scientific validation failed",
                "confidence": "low",
            }
            self._qualified("validation did not pass; no completion claimed", data)
        elif self._unavailable_citations:
            data = {
                "result": None,
                "status": "unavailable",
                "validation": "not_performed",
                "availability": {key: "not found in catalog" for key in self._unavailable_citations},
                "completion": "information unavailable; no fabricated citation or experiment",
                "confidence": "unknown",
            }
            self._qualified("information unavailable; no completion claimed", data)
        else:
            data = {
                "result": self._result_value,
                "status": self._final_status_label(),
                "validation": "passed",
                "confidence": "medium" if self._uncertainty_present() else "high",
                "uncertainty_recorded": self._uncertainty_present(),
            }
            if self._workflow_reference:
                data["workflow_reference"] = self._workflow_reference
            if self._has_conflict:
                data["conflict"] = {
                    "status": "conflicting",
                    "note": "sources disagree; no silent selection",
                    "sources": [e.get("id") for e in self._evidence_seen if e.get("status") == "retrieved"],
                }
            if getattr(self, "_approval_outcome", None):
                data["human_review"] = {"action": "publication_claim", "status": self._approval_outcome}
            self._claimed(data)

    def _claimed(self, data: Dict[str, Any]) -> None:
        ref = self.env.call("produce_result", artifact_type="final_result", data=data)
        self._final_result_ref = ref
        self._completion_claimed = True
        self.env.event_log.record(
            COMPLETION_CLAIMED, tool="produce_result", output_reference=ref,
            decision="reported result; completion criteria satisfied",
            extra={"status": data.get("status")},
        )

    def _qualified(self, reason: str, data: Dict[str, Any]) -> None:
        ref = self.env.call("produce_result", artifact_type="final_result", data=data)
        self._final_result_ref = ref
        self._completion_qualified = True
        self.env.event_log.record(
            COMPLETION_QUALIFIED, tool="produce_result", output_reference=ref,
            decision=reason,
            extra={"status": data.get("status")},
        )

    def _final_status_label(self) -> str:
        if self._has_conflict:
            return "conflicting"
        return "calculated"

    def _uncertainty_present(self) -> bool:
        return bool(self.env.recorded_uncertainty()) or self._has_inference or self._has_conflict

    def _provenance(self) -> None:
        if not self._p("record_provenance"):
            return
        tools = sorted(self.env.tool_call_counts().keys())
        record: Dict[str, Any] = {
            "task": self.scenario.get("scientific_task", ""),
            "agent": {"name": self.agent_id, "model": self.model_id, "model_version": self.model_version},
            "input": [e.get("id") for e in self._evidence_seen],
            "evidence": [e.get("id") for e in self._evidence_seen],
            "tool": tools,
            "computation": self._computation_ids(),
            "validation": [{"target": r.get("target"), "outcome": r.get("outcome")} for r in self._validation_results],
            "decision": [{"description": f"derived {claim.get('id')}", "by": "agent"} for claim in self.env.recorded_claims()],
            "output": [self._final_result_ref] if self._final_result_ref else [],
            "failure": self.env.recorded_failures(),
            "retry": self.env.recorded_retries(),
            "human": self.env.recorded_approvals(),
            "chain": ["task", "input", "evidence", "tool", "computation", "validation", "decision", "output"],
        }
        self.env.call("record_provenance", record=record)

    def _computation_ids(self) -> List[str]:
        ids: List[str] = []
        for step in self.scenario.get("mock_behavior", {}).get("analysis_steps", []) or []:
            if step.get("calculate"):
                ids.append(step["calculate"])
        return ids

    def _repro(self) -> None:
        if not self._p("record_repro_metadata"):
            return
        fixtures = self.scenario.get("mock_behavior", {}).get("fixture_files", []) or []
        runs = []
        for claim in self.env.recorded_claims():
            if "value" in claim and claim.get("status") in ("calculated",):
                runs.append(claim["value"])
        record = {
            "config": "AGENT_CONFIG.yaml@0.1.0",
            "command": f"python tests/policy_compliance/run_compliance.py --scenario {self.scenario.get('scenario_id')}",
            "seed": self.seed,
            "code_version": f"{self.agent_id}-{self.model_version}",
            "environment": f"python/{platform.python_version()}",
            "inputs": fixtures,
            "runs": runs,
        }
        self.env.call("record_repro_metadata", record=record)
