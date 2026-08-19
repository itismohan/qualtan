# Open-Source Release Runbook

## Purpose

This runbook turns QUALTAN from a private modernized repository into a trustworthy public framework. It complements [`RELEASE.md`](../RELEASE.md) by separating work that can be versioned in source control from the owner-only configuration required on GitHub and package registries.

> **Release standard:** A public release must make the safe path the easy path. It must demonstrate deterministic local validation before external integration, keep execution approval-gated, keep mutations disabled by default, and never use secrets or machine-specific paths in source-controlled templates.

## Go/no-go gate

| Gate | Source-controlled evidence | Owner-only evidence |
|---|---|---|
| Legal and attribution | `LICENSE`, `NOTICE`, dependency inventory, reviewed ownership | Approval from the copyright owner and legal reviewer where required |
| Community | Contribution, conduct, governance, support, and maintainer documents; forms and PR template | Issue labels and Discussions enabled |
| Security | `SECURITY.md`, audit report, enforced dependency audit, secret-safe templates | Private vulnerability reporting and security notifications enabled |
| Developer experience | Package metadata, `qualtan doctor`, offline demo, tested CLI | A clean-machine or clean-environment install test |
| Release engineering | Release process, changelog, CI release workflow, artifact ignore rules | Protected `main`, protected tags, publishing identity |
| Product boundary | Open core and managed-service position documented | Public repository description and roadmap approved |

All gates must be green before changing repository visibility. A red gate should result in a delayed launch, not a weaker security default.

## Public launch sequence

### 1. Perform a clean-room audit

Review the full Git history for credentials, private keys, customer data, proprietary documentation, employee-specific paths, and unlicensed copied code or assets. Remove or rewrite sensitive history before making the repository public; adding a `.gitignore` after the fact does not remove historical content. Verify that every image, architecture diagram, dependency, and example is safe to redistribute.

### 2. Validate the public developer journey

From a clean environment, clone the repository and complete the [offline demo](../examples/offline-demo/README.md). The developer must be able to install the package, run `qualtan doctor`, execute deterministic regression tests, and understand why no external target or mutation occurs. Treat a missing CLI entry point, unclear credentials workflow, or a surprise model call as a launch blocker.

### 3. Configure repository controls

Enable branch protection for `main`, require the Python tests and browser mock suite, forbid force pushes, and require code-owner review where GitHub plan capabilities allow. Enable private vulnerability reporting and subscribe security maintainers to alerts. Turn on GitHub Discussions and apply labels referenced by the issue templates.

### 4. Publish a transparent beta

Create `v0.1.0` only after the release checklist completes. Write release notes that say what is production-ready, what remains beta, which integrations require credentials, which settings are dangerous, and how a user can run the offline demo. Do not imply that generated tests are automatically correct or that the framework independently authorizes execution.

### 5. Operate the community

Triaging early issues is part of the product. Label reproducible defects, security reports, documentation gaps, good first issues, and design/RFC requests. Publish a three-month roadmap that prioritizes reliable onboarding, compatibility, secure adapters, and external contributor enablement over a large collection of ungoverned autonomous agents.

## First release scope

The `0.1.0` community release should include the following public components: typed domain contracts; durable workflow orchestration; central model gateway and redaction; deterministic quality gates; approval and execution policy; governed Jira/X-Ray adapters; the local MCP server; CLI compatibility commands; deterministic REST/GraphQL Playwright mocks; local Locust smoke infrastructure; architecture, deployment, IDE, security, contribution, and release documentation.

A managed service, if later created, may offer central policy management, long-term immutable audit retention, enterprise identity, fleet operations, and support. It must not put the locally usable policy engine, validators, approval semantics, or reference integrations behind a proprietary boundary.

## Initial operating metrics

| Metric | First-quarter target | Why it matters |
|---|---:|---|
| Time to complete offline demo | Under 10 minutes | Measures onboarding quality without vendor dependency |
| First response to a valid issue or pull request | Within 7 days | Sets a credible community expectation |
| Private vulnerability-report acknowledgement | Within 5 business days | Supports coordinated disclosure |
| Public release builds with SBOM and checksums | 100% | Makes supply-chain review possible |
| Unapproved external-mutation regressions | 0 | Preserves QUALTAN’s core trust boundary |

## References

GitHub provides community health files for contribution, conduct, governance, security, support, and templates; repository licenses must remain in the repository itself.[1] GitHub private vulnerability reporting gives researchers a structured non-public disclosure path.[2] The OpenSSF Best Practices Badge is a useful voluntary maturity target after the initial release baseline is stable.[3]

[1]: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file "GitHub Docs — Creating a default community health file"
[2]: https://docs.github.com/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository "GitHub Docs — Configuring private vulnerability reporting for a repository"
[3]: https://openssf.org/projects/best-practices-badge/ "OpenSSF — Best Practices Badge"
