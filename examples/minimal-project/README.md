# Minimal Project Example

A minimal, domain independent example of a scientific repository that consumes the Universal Agentic AI Scientific Operating Policy (UAASOP).

## What this example shows

- How a project entry point (`AGENTS.md`) references the canonical policy and machine readable configuration.
- How to layer project specific rules on top of the canonical policy without contradicting it.
- How to record provenance and validation using the schemas in `../schemas/`.

## Files

| File | Role |
| --- | --- |
| `AGENTS.md` | Project entry point binding this project to the UAASOP policy. |
| `README.md` | This file. |

## Expected additions in a real project

- Analysis or experiment scripts with recorded commands and seeds.
- A `provenance.json` conforming to `../schemas/provenance.schema.json`.
- A `validations.json` conforming to `../schemas/validation.schema.json`.
- Raw data and generated outputs stored outside git, referenced by path or checksum in the provenance records.

## How to adapt this example

1. Copy `AGENTS.md` into your own project.
2. Adjust the project specific instructions to your discipline, but keep them consistent with the canonical policy.
3. Add the schemas from `../schemas/` and validate your records against them.
4. Use the default workflow from `../../SCIENTIFIC_AGENT_POLICY.md` for every scientific task.

## Reference

- Canonical policy: `../../SCIENTIFIC_AGENT_POLICY.md`
- Machine readable configuration: `../../AGENT_CONFIG.yaml`
- Schemas: `../schemas/`
