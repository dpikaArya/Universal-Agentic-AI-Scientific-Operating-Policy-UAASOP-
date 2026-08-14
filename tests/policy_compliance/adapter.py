"""Agent adapter interface for the UAASOP policy compliance evaluation.

An AgentAdapter is the only bridge between the compliance framework and an
agentic AI system. It makes an agent's observable behavior available as
artifacts, events, and provenance records without ever requiring access to
private model reasoning.

The MockAgentAdapter runs a deterministic mock agent entirely locally, which
allows the compliance framework itself to be tested without a real LLM. A real
agent harness (for example OpenCode, Claude Code, Cursor, Cline, Aider, Gemini
CLI, or GitHub Copilot) can implement the same interface by translating its own
execution log into these structures.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .environment import MockEnvironment


class AgentAdapter(ABC):
    """Conceptual interface for executing an agent against a scenario.

    Operations equivalent to prepare / run / collect_artifacts /
    collect_events / collect_provenance / cleanup. Implementations must not
    depend on a specific IDE. They only need to expose observable behavior.
    """

    agent_id: str = "AgentAdapter"

    @abstractmethod
    def prepare(self) -> None:
        """Set up the execution environment for one scenario."""

    @abstractmethod
    def run(self) -> None:
        """Execute the scenario and record observable behavior."""

    @abstractmethod
    def collect_artifacts(self) -> List[Dict[str, Any]]:
        """Return the observable artifacts the agent produced."""

    @abstractmethod
    def collect_events(self) -> List[Dict[str, Any]]:
        """Return the observable event log (tool calls, records, decisions)."""

    @abstractmethod
    def collect_provenance(self) -> List[Dict[str, Any]]:
        """Return the provenance records the agent recorded."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources; must be safe to call after run or prepare."""


class MockAgentAdapter(AgentAdapter):
    """Adapter that runs a deterministic mock agent against the mock environment.

    No LLM, no network, no credentials. Used to test the compliance framework
    and to run the behavioral suite in normal CI.
    """

    def __init__(
        self,
        agent: Any,
        scenario: Optional[Dict[str, Any]] = None,
        env: Optional[MockEnvironment] = None,
        repo_root: Optional[str] = None,
        seed: int = 42,
    ):
        self.agent = agent
        self.agent_id = getattr(agent, "agent_id", "MockAgent")
        self.scenario = scenario
        self.env = env
        self.repo_root = repo_root
        self.seed = seed
        self.execution_id = "exec-" + uuid.uuid4().hex[:12]

    def prepare(self) -> None:
        if self.scenario is None:
            raise RuntimeError("MockAgentAdapter.prepare requires a scenario")
        if self.env is None:
            self.env = MockEnvironment(
                scenario=self.scenario,
                repo_root=self.repo_root,
                execution_id=self.execution_id,
                agent_id=self.agent_id,
                seed=self.seed,
            )

    def run(self) -> None:
        if self.env is None:
            self.prepare()
        self.agent.run(self.scenario, self.env)

    def collect_artifacts(self) -> List[Dict[str, Any]]:
        return self.env.artifacts_all() if self.env else []

    def collect_events(self) -> List[Dict[str, Any]]:
        return self.env.events() if self.env else []

    def collect_provenance(self) -> List[Dict[str, Any]]:
        return self.env.provenance_all() if self.env else []

    def cleanup(self) -> None:
        self.env = None
