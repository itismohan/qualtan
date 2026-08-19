# Security Policy

## Security model

QUALTAN is designed so that probabilistic model output cannot independently authorize execution, external mutation, or policy changes. Models propose artifacts; typed contracts, deterministic validators, execution policies, allowlists, and recorded human approvals determine what can proceed.

The project treats requirements, Jira text, test evidence, API specifications, logs, HTML, DOM snapshots, network data, and retrieved documents as untrusted input. Do not rely on QUALTAN as the sole control for a production environment. Deployers remain responsible for credentials, network segmentation, target authorization, retention settings, and review of generated artifacts.

## Reporting a vulnerability

**Do not disclose suspected vulnerabilities in public GitHub issues, pull requests, discussions, or chat.** When GitHub private vulnerability reporting is enabled, use the repository’s **Report a vulnerability** action in the Security/Advisories area. This is the preferred disclosure route.

Until private reporting is enabled, contact a repository maintainer through the private contact route documented in [`SUPPORT.md`](SUPPORT.md). Include a clear description, affected version or commit, reproducible steps or a proof of concept, impact assessment, and any suggested mitigation. Redact credentials, customer data, internal hosts, and production evidence.

Maintainers will acknowledge a valid report within **five business days**, provide an initial severity and remediation assessment within **ten business days**, and coordinate a fix and disclosure timeline with the reporter. These are project targets, not a service-level agreement.

## Supported versions

| Version | Supported |
|---|---:|
| Latest released minor version | Yes |
| Current `main` branch | Best effort for development findings |
| Older releases | No, unless a maintainer announces an exception |

## In scope

Reports are in scope when they affect QUALTAN source code, packaged artifacts, official CI workflows, project-controlled MCP configurations, release automation, or officially maintained integrations. Particularly valuable reports include policy bypasses, approval bypasses, unsafe execution or mutation paths, secret exposure, authentication or authorization weaknesses, prompt-injection policy escapes, data-redaction failures, dependency compromise, and supply-chain integrity failures.

## Out of scope

The following are normally out of scope: denial of service requiring unreasonably high local resources; vulnerabilities in unmodified third-party services outside an official integration; findings requiring a deployer to deliberately disable documented safeguards; and reports containing only scanner output without a reproducible, QUALTAN-specific impact.

## Safe-harbor expectations

Act in good faith, avoid privacy violations and service disruption, use only accounts and targets you are authorized to test, stop when you identify sensitive data, and provide maintainers a reasonable opportunity to remediate before public disclosure. The project will not pursue action against good-faith researchers who follow these expectations, to the extent permitted by applicable law.

## Deployment requirements

| Control | Required public-release behavior |
|---|---|
| Secrets | Use environment or secret-manager references only; never commit values or include them in MCP templates. |
| Execution | Require an explicit host allowlist and recorded approval before target execution. |
| External mutations | Keep disabled by default; require explicit policy enablement, scoped credentials, and approval evidence. |
| MCP | Keep the tool surface narrow; do not grant arbitrary shell, filesystem, credential, or HTTP access. |
| Evidence | Redact sensitive content, bound capture volume, and set retention appropriate to the deployment. |
| Dependencies | Review advisories, pin compatible ranges, and preserve the enforced dependency-audit CI gate. |

See [`docs/MCP_SECURITY_AUDIT.md`](docs/MCP_SECURITY_AUDIT.md) and the [deployment guide](docs/DEPLOYMENT_AND_SCALING_GUIDE.md) for implementation detail.
