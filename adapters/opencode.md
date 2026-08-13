# OpenCode Adapter

Applies to the [OpenCode](https://opencode.ai) agentic development environment.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Read `AGENTS.md` at the repository root; it is the agent entry point.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings.
- When working on scientific tasks, follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- OpenCode exposes a shell tool for terminal operations and file tools for reading, editing, and writing files. Use them under least privilege.
- Before modifying an existing project, inspect its instructions, architecture, tests, schemas, data contracts, provenance mechanisms, and workflows.
- Record provenance for consequential outputs using the fields in `../SCIENTIFIC_AGENT_POLICY.md` section 3.
- Never claim tool execution, validation, or success that did not occur.

## Status

Community integration guidance. Not an official OpenCode product or endorsement. Verify behavior against your installed version.
