# Cursor Adapter

Applies to the [Cursor](https://cursor.com) AI code editor.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Point Cursor's rules or project instructions to `../SCIENTIFIC_AGENT_POLICY.md`.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Use agent mode under the same least-privilege rules that apply to any session: only the permissions, tools, filesystem, network, compute, and credentials required for the task.
- Record provenance for consequential outputs per section 3 of the canonical policy.
- Never present unexecuted actions or unvalidated results as completed.

## Status

Community integration guidance. Not an official Cursor product feature or endorsement. Verify behavior against your installed version.
