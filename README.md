# Universal Agentic AI Scientific Operating Policy

An IDE independent operating policy for trustworthy, verifiable, provenance aware scientific agentic AI systems.

Universal Agentic AI Scientific Operating Policy provides a portable governance and configuration layer for AI agents working on scientific and research projects. It defines practical rules for evidence, provenance, verification, reproducibility, human accountability, security, and responsible execution across different AI development environments.

---

## What UAASOP is

UAASOP is a compact, practical, reusable operating policy for agentic AI systems that assist scientific research, engineering, data science, computational science, and related development. It is a single canonical policy that works across OpenCode, Claude Code, Cursor, Cline, Aider, GitHub Copilot, Gemini CLI, and other agentic AI development environments.

This repository is the reference implementation. OpenCode may be the tool used to build and maintain it, but the policy itself is IDE independent.

## Why it exists

Agentic AI systems now write analysis scripts, run computations, interpret data, and draft scientific text. These systems are powerful but not intrinsically reliable. Without explicit rules, an agent may silently convert inference into fact, hide failed approaches, fabricate citations, or present unverified output as validated results.

UAASOP exists to make scientific agentic AI behavior explicit, consistent, and auditable.

## What problem it solves

- **Unverified results presented as fact.** The policy requires explicit evidence discipline and uncertainty labeling.
- **Untraceable outputs.** Consequential outputs must be traceable back through decisions, computations, tools, inputs, evidence, and sources.
- **Lost failures.** Failed approaches and rejected hypotheses are preserved as scientific data.
- **No human accountability.** Consequential decisions require recorded human review.
- **Uncontrolled execution.** Compute discipline, least privilege, and HPC safety rules constrain what agents may do.
- **Vendor lock-in.** Portability rules keep the policy and projects independent of any single AI environment.

## Why scientific agentic AI needs provenance and verification

Science depends on trust: the trust that a result means what it appears to mean, that it can be traced to its evidence, and that it can be reproduced. An agent that produces a number is not enough; the scientific community needs to know which number came from a measurement, which came from a calculation, and which came from an assumption.

Provenance answers "where did this come from and what built upon what?" Verification answers "is it actually right?" Accountability answers "who is responsible?" UAASOP requires all three.

## How the pieces work together

| Piece | Role |
| --- | --- |
| `SCIENTIFIC_AGENT_POLICY.md` | The authoritative canonical policy. All other files reference it. |
| `AGENT_CONFIG.yaml` | Machine readable policy settings that tools can load programmatically. |
| `adapters/` | IDE and agent specific integration guidance, referencing the canonical policy rather than duplicating it. |
| `schemas/` | Machine readable contracts for provenance, evidence, claim, and validation records. |
| `AGENTS.md` | Entry point telling any agent which files govern behavior in this repository. |
| `examples/` | Reference projects showing how a scientific repository consumes UAASOP. |

Project specific instructions may extend the policy but must not contradict its scientific safety, provenance, verification, reproducibility, security, or accountability requirements.

## Architecture

```
                     ┌─────────────────────────────┐
                     │  SCIENTIFIC_AGENT_POLICY.md  │  canonical policy
                     └──────────────┬──────────────┘
                                    │ referenced by
        ┌───────────────┬───────────┼───────────┬───────────────┐
        │               │           │           │               │
   ┌────▼─────┐   ┌─────▼────┐ ┌────▼────┐ ┌────▼─────┐   ┌─────▼──────┐
   │ AGENT    │   │ adapters/│ │ schemas/│ │AGENTS.md│   │ examples/  │
   │CONFIG    │   │ per IDE  │ │ JSON    │ │ entry   │   │ reference  │
   │.yaml     │   │ guidance │ │ contracts│ │ point   │   │ projects   │
   └──────────┘   └──────────┘ └─────────┘ └──────────┘   └────────────┘
                                    │
                              ┌─────▼─────┐
                              │ agent runs │  UNDERSTAND → PLAN → INSPECT
                              │ scientific │  → EXECUTE → VALIDATE → TRACE
                              │ workflow   │  → REVIEW → REPORT
                              └───────────┘
```

## Adopting UAASOP in a new project

1. Copy `AGENTS.md` into your project root, or reference the canonical policy from your project's instruction file.
2. Point the agent at `SCIENTIFIC_AGENT_POLICY.md` as the governing policy.
3. Load `AGENT_CONFIG.yaml` where your tool supports machine readable configuration.
4. Apply the relevant schema from `schemas/` when your project records provenance, evidence, claims, or validation.
5. Add your own project specific instructions. They may extend the policy, not contradict it.
6. Record provenance for consequential outputs, label uncertainty, and require human review for consequential decisions.

## Minimal usage example

A researcher asks an agent to analyze a dataset:

1. **UNDERSTAND** — The agent restates the scientific question: "What is the effect of treatment X on metric Y in dataset Z?"
2. **PLAN** — It plans the analysis: load data, describe, run the specified statistical test, validate.
3. **INSPECT** — It reads the project `AGENTS.md`, existing tests, and data contracts before touching anything.
4. **EXECUTE** — It runs the analysis with least privilege, recording the command, code version, and inputs.
5. **VALIDATE** — It checks the computation against a deterministic reference and a statistical sanity check.
6. **TRACE** — It confirms the result can be traced: result → test → R script → dataset → source.
7. **REVIEW** — It flags the result as `calculated`, notes the confidence, and requests human review before it is treated as a conclusion.
8. **REPORT** — It reports the result labeled `calculated`, with explicit uncertainty and the validation record.

## Default agent workflow

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

## What the policy does not guarantee

UAASOP does **not** guarantee scientific correctness.

It does not perform verification itself, does not validate your data, does not review your results, and does not replace human scientific expertise. An agent that follows this policy can still be wrong.

What UAASOP establishes are behavioral, provenance, verification, reproducibility, security, and accountability requirements. It increases the probability that errors are found, that results are traceable, and that responsibility is clear. Correctness remains the responsibility of the scientists who use the policy.

## Repository structure

```
├── README.md
├── LICENSE
├── AGENTS.md
├── SCIENTIFIC_AGENT_POLICY.md
├── AGENT_CONFIG.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .gitignore
├── adapters/
│   ├── opencode.md
│   ├── claude-code.md
│   ├── cursor.md
│   ├── cline.md
│   ├── aider.md
│   ├── copilot.md
│   └── gemini-cli.md
├── schemas/
│   ├── provenance.schema.json
│   ├── evidence.schema.json
│   ├── claim.schema.json
│   └── validation.schema.json
└── examples/
    └── minimal-project/
        ├── AGENTS.md
        └── README.md
```

## License

MIT. See [LICENSE](LICENSE).
