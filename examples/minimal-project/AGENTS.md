# Project AGENTS.md

This example project demonstrates how a scientific repository consumes UAASOP. It is intentionally domain independent; substitute your own discipline, data, and tools.

## Governing policy

- `../../SCIENTIFIC_AGENT_POLICY.md` is the authoritative universal policy. Follow it for all scientific work in this project.
- `../../AGENT_CONFIG.yaml` provides machine readable policy settings.
- Project specific instructions below extend the policy. They do not contradict its scientific safety, provenance, verification, reproducibility, security, or accountability requirements.

## Project instructions

1. All analysis scripts must record the command, script version, input references, and random seed used, so results can be reproduced.
2. Before reporting any result as a conclusion, label its epistemic status (`verified`, `calculated`, `estimated`, `inferred`, `predicted`, etc.) and record supporting validation.
3. Consequential decisions and conflicting evidence require recorded human review before the project treats them as final.
4. Raw inputs and generated outputs live in directories ignored by git; references and descriptions are recorded in the provenance file.
5. Do not commit credentials, tokens, private keys, or restricted datasets. Use environment variables referenced by name, never by value.

## Provenance records

Record consequential outputs in `provenance.json` conforming to `../../schemas/provenance.schema.json`. Link each output through its computation, tool, input, and evidence chain.

## Validation

Run project checks before reporting results. Record each check in `validations.json` conforming to `../../schemas/validation.schema.json`, with type, result, and method.

## Workflow

Follow the default agent workflow from the canonical policy:

```
UNDERSTAND
→ PLAN
→ INSPECT
→ EXECUTE
→ VALIDATE
→ TRACE
→ REVIEW
→ REPORT
```
