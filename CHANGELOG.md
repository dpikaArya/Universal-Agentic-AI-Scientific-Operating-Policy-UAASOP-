# Changelog

All notable changes to the Universal Agentic AI Scientific Operating Policy are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Agent Policy Compliance Evaluation: a deterministic, IDE independent behavioral test suite that checks whether an agent actually follows the policy, not whether it claims to.
- Ten behavioral compliance scenarios (evidence vs inference, failed attempt preservation, validation failure, uncertainty, conflicting sources, human review, tool governance, provenance, reproducibility, fabrication resistance) with machine readable specs, expected references, synthetic fixtures, and a SHA256 verified scenario index.
- Ten deterministic behavioral validators and a compliance runner producing results that conform to `schemas/policy-compliance.schema.json`, with critical-violation detection and compliance levels 0-4.
- `CompliantMockAgent` (passes every scenario) and `ViolatingMockAgent` (fails every scenario) plus a pytest suite proving the framework can distinguish them.
- CLI (`run_compliance.py`), static checks (`static_checks.py`), and `adapters/policy-compliance.md` describing how any agent harness can implement the `AgentAdapter` interface.

## [0.1.0] - 2026-08-13

### Added

- Initial Universal Agentic AI Scientific Operating Policy.
- Canonical policy `SCIENTIFIC_AGENT_POLICY.md` with 20 universal principles, default agent workflow, provenance record guidance, and confidence/uncertainty language.
- Machine readable configuration `AGENT_CONFIG.yaml`.
- Repository entry point `AGENTS.md`.
- Adapters for OpenCode, Claude Code, Cursor, Cline, Aider, GitHub Copilot, and Gemini CLI.
- JSON Schemas for provenance, evidence, claim, and validation records.
- Minimal example project demonstrating how a scientific repository consumes UAASOP.
- Documentation: README, CONTRIBUTING, LICENSE (MIT), CHANGELOG, .gitignore.
