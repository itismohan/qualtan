# QUALTAN Governance

## Purpose

QUALTAN is maintained as an open framework for governed AI quality engineering. Governance exists to protect users, contributors, and the project’s core safety promise: models propose, while policy, validation, approval, and evidence controls decide.

## Roles

| Role | Responsibilities | Decision authority |
|---|---|---|
| Contributors | Submit code, documentation, issues, and design feedback under the DCO | Propose changes and participate in review |
| Reviewers | Review correctness, tests, docs, compatibility, and security implications | Recommend approval or revision |
| Maintainers | Triage issues, merge contributions, cut releases, respond to security reports | Approve routine changes in owned areas |
| Core maintainers | Protect architecture, public contracts, policy semantics, and release integrity | Approve major changes and resolve escalations |

The initial maintainer ownership is documented in [`MAINTAINERS.md`](MAINTAINERS.md) and enforced through [`.github/CODEOWNERS`](.github/CODEOWNERS). The project should add at least one additional active core maintainer before declaring a stable `1.0` release.

## Decision-making

Routine, backward-compatible changes are decided by review and approval from an appropriate maintainer. Major changes require a public design record in `docs/rfcs/` and at least two maintainer approvals where possible.

A change is major when it affects a public domain model, persisted workflow state, policy schema, approval semantics, CLI compatibility, MCP tool surface, plugin contract, supported runtime, security boundary, or release process. The RFC must state the user problem, alternatives, compatibility impact, migration plan, security and privacy impact, test strategy, and rollback plan.

Maintainers seek consensus. If consensus cannot be reached in a reasonable time, core maintainers decide based on user safety, compatibility, evidence quality, maintainability, and the project roadmap. Decisions with material impact must be recorded in the issue, pull request, or RFC.

## Compatibility and releases

QUALTAN follows semantic versioning for documented public interfaces. A breaking change requires a major version or a documented migration path. Security fixes may be expedited when necessary; maintainers will publish a migration note whenever safeguards, defaults, or interfaces change.

Backward-compatible CLI commands, approval-gated execution, disabled-by-default external mutations, and narrow MCP permissions are protected project guarantees. A contributor must not weaken these guarantees through undocumented convenience flags or automatic approvals.

## Maintainer conduct and conflicts

All participants must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Maintainers should recuse themselves where a conflict could reasonably affect impartial review. Security reports and conduct reports must be handled privately and with the minimum necessary disclosure.

## Governance evolution

This lightweight maintainer model is intentional for an early project. The project will reconsider its governance structure when it has sustained external adoption, multiple independent maintainers, or institutional contributors. Any transition to a foundation, steering committee, or formal membership model will be proposed through an RFC and announced before taking effect.
