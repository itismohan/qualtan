# MCP and Environment-Secret Security Audit

**Scope:** Project-scoped MCP templates, `mcp_server.py`, GitHub Actions secret handling, tracked-file exposure controls, and the deterministic mock-network test path.

> **Audit limitation:** The latest GitHub Actions logs could not be retrieved in this session because the repository’s GitHub connector is disabled and its enablement request was not approved. The runtime outcomes of the CI mock-network and Locust steps are therefore **not confirmed from GitHub logs** in this report.

## Executive result

The committed MCP templates do not contain credentials, private-key material, user-specific absolute paths, automatic tool approval, or remote MCP URLs. The QUALTAN MCP server exposes a narrow tool surface and does not expose arbitrary shell execution, direct test execution, or external mutation tools. The CI workflow passes the Kubernetes deployment credential only through the protected GitHub Environment secret `KUBE_CONFIG_DATA` and gives repository contents read-only permissions.

During the audit, the repository was found to have no `.gitignore`; consequently, local `.env` and private-key files could have been accidentally staged in a future change. This was remediated with a root `.gitignore`. The Codex MCP template was also tightened to avoid forwarding ambient environment variables unnecessarily.

## Evidence summary

| Area | Result | Evidence |
|---|---|---|
| Tracked credential files | Pass | No tracked `.env`, certificate, key, or keystore files were found. |
| Literal credential scan | Pass | The audit found no common private-key, cloud-access-key, GitHub-token, Slack-token, or OpenAI-key patterns in tracked implementation/configuration files. |
| IDE MCP templates | Pass | Cursor, Claude Code, Codex, and Kiro templates use local `stdio` commands and contain no tokens, headers, remote URLs, or user-specific paths. |
| Codex ambient environment forwarding | Remediated | Removed the unnecessary `env_vars` entry from `.codex/config.toml`. |
| Tool approval | Pass | Codex uses `default_tools_approval_mode = "prompt"`; Kiro has an empty `autoApprove` list. Cursor and Claude Code retain client-native review/trust controls. |
| MCP tool surface | Pass | `mcp_server.py` exports only create, run/resume, approve, and read-state workflow tools. Direct execution and external mutation methods are absent. |
| CI permissions | Pass | The workflow has read-only repository content permission; deployment is manual and bound to a GitHub Environment. |
| Deployment credential use | Review required | `KUBE_CONFIG_DATA` is referenced only as a GitHub Environment secret and decoded into a temporary runner file. Long-term, prefer cloud OIDC federation over a static kubeconfig. |
| Local secret-file protection | Remediated | Added ignore rules for `.env`, `.env.*`, private keys, certificates, keystores, browser reports, and generated validation output while preserving `.env.example`. |
| Python dependency audit | Remediated and verified | Raised `pytest` to `>=9.0.3,<10`, the reported fixed release range. A fresh `pip-audit -r requirements.txt` found no known vulnerabilities. |
| GitHub Actions runtime logs | Not confirmed | The supplied private run remains inaccessible to the available browser session; re-run the audit with an authenticated GitHub session to verify exact job-step outcomes. |

## CI mock-network verification status

The committed GitHub Actions workflow executes the following deterministic checks after Python dependencies are installed:

| CI step | Expected behavior | Log verification status |
|---|---|---|
| `Run committed Playwright tests when present` | Installs Chromium and executes the route-stub suite. The suite intercepts REST and GraphQL calls at a local synthetic origin. | Not confirmed from GitHub logs. |
| `Run Locust smoke test against isolated local mock API` | Starts an ephemeral loopback REST/GraphQL mock server and runs Locust against it. No placeholder, staging, or production host is configured. | Not confirmed from GitHub logs. |

Local evidence collected before this audit recorded **19 passing Python tests** and **3 passing Playwright route-stub tests**. The full local Locust runner requires the declared `locust` dependency; it was not installed on the connected desktop at audit time. GitHub Actions installs the declared dependencies before the runner step, but this should be confirmed from a successful run log.

## Required follow-up

The first priority is to inspect the latest `QUALTAN CI/CD` run in GitHub Actions and confirm that the Playwright and Locust steps are green. If the run is red, download the workflow artifact and inspect only the relevant test output. Do not add real API URLs or tokens to CI merely to make the smoke test pass.

For deployment, keep `KUBE_CONFIG_DATA` restricted to the `staging` and `production` GitHub Environments, rotate it on a defined schedule, and migrate to cloud workload identity/OIDC when the target platform supports it. Secrets must remain outside tracked configuration files; inject them only through protected environment secrets at runtime.
