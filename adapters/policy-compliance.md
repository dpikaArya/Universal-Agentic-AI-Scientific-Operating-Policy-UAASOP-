# Policy Compliance Adapter

Evaluates whether an agent actually **behaves** according to the Universal
Agentic AI Scientific Operating Policy (`../SCIENTIFIC_AGENT_POLICY.md`).

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not
replace it.

## What this is

An agent that is told to follow a policy is not the same as an agent that
follows it. The UAASOP Agent Policy Compliance Evaluation
(`../tests/policy_compliance/`) turns observable agent behavior into PASS/FAIL
checks across ten behavioral scenarios: evidence discipline, failure
preservation, verification, uncertainty, conflicting sources, human review, tool
governance, provenance, reproducibility, and fabrication resistance.

It is IDE independent and deterministic. It never inspects private model
reasoning; it only inspects observable artifacts, events, records, and
provenance.

## Integration

Any agent harness can be evaluated by implementing the `AgentAdapter` interface
in `../tests/policy_compliance/adapter.py`:

- `prepare()` - set up the execution environment for one scenario,
- `run()` - execute the scenario and record observable behavior,
- `collect_artifacts()` - return the observable artifacts produced,
- `collect_events()` - return the observable event log,
- `collect_provenance()` - return the provenance records,
- `cleanup()` - release resources.

The `MockAgentAdapter` already provides this for the included deterministic mock
agents, so the suite runs in normal CI without any LLM.

## Running

See `../tests/policy_compliance/README.md`. Static checks, the behavioral suite,
and a pytest suite that proves the framework can tell a compliant agent from a
violating one:

```bash
python tests/policy_compliance/static_checks.py
python tests/policy_compliance/run_compliance.py
python -m pytest tests/test_policy_compliance.py
```

## Status

Community integration guidance. The compliance suite is fully local, uses only
synthetic fixtures, and requires no network, credentials, or HPC resources.
