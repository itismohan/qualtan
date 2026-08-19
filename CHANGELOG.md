# Changelog

All notable changes to QUALTAN are documented in this file. The project follows [Semantic Versioning](https://semver.org/) for documented public interfaces.

## [Unreleased]

### Added

- Apache-2.0 licensing, contributor DCO, governance, conduct, support, security, and release-process assets for the public framework baseline.
- Package metadata and the `qualtan` command entry point.
- `qualtan doctor`, a secret-safe readiness diagnostic that reports policy posture without printing credentials, endpoints, or allowlisted hosts.
- An offline onboarding demonstration, structured issue forms, CODEOWNERS, release runbook, and public community documentation.

### Security

- Community contribution and release rules now explicitly protect approval-gated execution, disabled-by-default external mutations, narrow MCP permissions, and secret-safe templates.

## [0.1.0] - 2026-08-19

### Added

- Typed Pydantic domain contracts for requirements, risk, plans, generated tests, approvals, validation, execution evidence, and reporting.
- Durable requirement-to-test orchestration with checkpointed work-item state and recorded approvals.
- Central model gateway with schema-constrained output, redaction, bounded retry, safe caching, and telemetry.
- Deterministic validation gates for schema integrity, acceptance-criteria coverage, generated-source safety, and TypeScript compilation.
- Governed Jira and X-Ray integration boundaries, policy-controlled execution, and a narrow MCP server for supported AI IDEs.
- Deterministic REST/GraphQL Playwright route stubs and local Locust smoke infrastructure.
- CI/CD validation with an enforced Python dependency audit and secret-safe MCP configuration templates.

[Unreleased]: https://github.com/itismohan/qualtan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/itismohan/qualtan/releases/tag/v0.1.0
