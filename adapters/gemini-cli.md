# Gemini CLI Adapter

Applies to the [Gemini CLI](https://github.com/google-gemini/gemini-cli) command line agent.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Reference the canonical policy in your project instructions or in the session before scientific work.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Use the shell and file tools under least privilege; grant only the permissions the current step requires.
- Record provenance for consequential outputs per section 3 of the canonical policy.
- Never report tool execution, validation, or success that did not occur.

## Status

Community integration guidance. Not an official Google integration or endorsement. Verify behavior against your installed version.
