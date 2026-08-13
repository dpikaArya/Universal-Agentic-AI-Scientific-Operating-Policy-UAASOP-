# Claude Code Adapter

Applies to the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) agentic coding environment.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Reference the canonical policy from your project instructions or add a CLAUDE.md pointer to `../SCIENTIFIC_AGENT_POLICY.md`.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Do not exceed the permissions granted to the session. Least privilege applies.
- Record consequential decisions and human approvals as provenance per section 3 of the canonical policy.
- Do not fabricate file changes, tool results, or successful runs.

## Status

Community integration guidance. Not an official Anthropic integration or endorsement. Verify behavior against your installed version.
