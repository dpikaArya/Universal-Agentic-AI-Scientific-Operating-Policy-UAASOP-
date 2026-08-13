# Contributing

Thank you for considering contributing to the Universal Agentic AI Scientific Operating Policy.

## What you can contribute

- **Policy changes** — improvements to `SCIENTIFIC_AGENT_POLICY.md`.
- **Schema changes** — changes to the machine readable contracts in `schemas/`.
- **Adapter changes** — integration guidance for a supported IDE or a new IDE.
- **Example changes** — reference projects in `examples/` and documentation fixes.

## Ground rules for policy changes

Policy changes must preserve:

- **human accountability** — humans remain responsible for consequential scientific decisions,
- **provenance** — outputs remain traceable to evidence and process,
- **verification** — verification requirements are not weakened,
- **reproducibility** — recorded state must support reproduction,
- **security** — least privilege and data protection are not weakened,
- **portability** — the policy stays independent of any single AI vendor or IDE.

## How to propose changes

1. Fork the repository.
2. Create a feature branch.
3. Make your change. Keep the policy concise and operational. Avoid duplicating rules across files; reference the canonical policy instead.
4. If you change `SCIENTIFIC_AGENT_POLICY.md`, update `AGENT_CONFIG.yaml` and `AGENTS.md` for consistency.
5. Update `CHANGELOG.md` under an Unreleased section.
6. Validate any JSON or YAML you touch (see below).
7. Open a pull request describing the motivation and the scientific or operational rationale.

## Validation

- JSON and JSON Schema files must be valid JSON and valid JSON Schema Draft 2020-12 (or later).
- YAML files must parse as valid YAML.
- Relative links in Markdown must resolve.
- The policy must remain IDE independent; no adapter may duplicate the full canonical policy.

## Code of conduct

Be respectful and constructive. Focus on technical and scientific merit. Scientific disagreement belongs in the repository, preserved and resolved with recorded reasoning.
