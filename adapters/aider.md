# Aider Adapter

Applies to [Aider](https://aider.chat), the terminal based AI pair programming tool.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Reference the canonical policy in your project instructions or in the aider chat before scientific work.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Aider works directly on source files. Verify changes before committing; do not commit unvalidated scientific code as if it were verified.
- Use the default workflow's INSPECT step before modifying existing scientific projects.
- Record provenance for consequential outputs per section 3 of the canonical policy.

## Status

Community integration guidance. Not an official Aider project endorsement. Verify behavior against your installed version.
