# AGENTS.md

This file tells any agent working in this repository which rules govern its behavior.

## 1. Governing policy

`SCIENTIFIC_AGENT_POLICY.md` is the authoritative universal policy for scientific agentic AI systems. Agents assisting scientific, engineering, data science, computational science, or related development work in this repository must follow it.

## 2. Machine readable configuration

`AGENT_CONFIG.yaml` provides machine readable policy settings. Tools that support configuration loading may read it programmatically. It mirrors the canonical policy.

## 3. Adapters

`adapters/` contains IDE and agent specific integration guidance for OpenCode, Claude Code, Cursor, Cline, Aider, GitHub Copilot, and Gemini CLI. Adapters reference the canonical policy and do not replace it.

## 4. Schemas

`schemas/` contains machine readable contracts for provenance, evidence, claim, and validation records. Use them when the project records such information.

## 5. Project specific instructions

Project specific instructions may extend the policy but must not contradict its scientific safety, provenance, verification, reproducibility, security, or accountability requirements.

## 6. Default workflow

Follow the default agent workflow from the canonical policy when working on scientific tasks:

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
