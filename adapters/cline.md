# Cline Adapter

Applies to [Cline](https://cline.bot), the open source AI coding assistant.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Add a `.clinerules` file (or equivalent project instructions) referencing `../SCIENTIFIC_AGENT_POLICY.md`.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Approve or reject tool calls with least privilege in mind; grant only what the current step requires.
- Record provenance for consequential outputs per section 3 of the canonical policy.
- Do not fabricate terminal output, file edits, or validation results.

## Status

Community integration guidance. Not an official Cline project endorsement. Verify behavior against your installed version.
