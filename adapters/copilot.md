# GitHub Copilot Adapter

Applies to [GitHub Copilot](https://github.com/features/copilot) and its agentic coding features.

## Policy reference

The governing policy is `../SCIENTIFIC_AGENT_POLICY.md`. This adapter does not replace it.

## Integration

- Reference the canonical policy in your repository instruction file so Copilot chat and agent sessions honor it.
- Load `../AGENT_CONFIG.yaml` for machine readable policy settings where your environment supports it.
- Follow the default workflow: UNDERSTAND, PLAN, INSPECT, EXECUTE, VALIDATE, TRACE, REVIEW, REPORT.

## Specific guidance

- Treat Copilot suggestions as unverified drafts. Apply evidence discipline before accepting any scientific claim, calculation, or citation into the record.
- Never accept a suggestion that fabricates citations, sources, experiments, or measurements.
- Record provenance for consequential outputs per section 3 of the canonical policy.

## Status

Community integration guidance. Not an official GitHub feature or endorsement. Verify behavior against your installed version.
