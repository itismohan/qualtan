# AI IDE MCP and Deterministic Network Testing

QUALTAN now provides two complementary developer-experience capabilities. The Playwright suite intercepts REST and GraphQL traffic locally, so API contract checks do not depend on an internet connection, a placeholder hostname, or a shared staging environment. The repository also provides project-scoped MCP configuration for **Cursor**, **Claude Code**, **Codex**, and **Kiro**, allowing each client to use the same governed QUALTAN MCP server.

> **Safety principle:** The IDE configuration starts a local stdio server with no embedded credentials. The server retains QUALTAN’s approval and policy boundaries; IDE support does not grant tools broader authority.

## Deterministic REST and GraphQL testing

The Playwright suite in [`playwright/tests/api-network-stubs.spec.ts`](../playwright/tests/api-network-stubs.spec.ts) uses `page.route()` to intercept requests from a local synthetic origin. It validates the request method, authorization header, GraphQL operation name, variables, and query shape before returning a deterministic response. It also covers a GraphQL `errors` response, so UI or client error handling can be tested without a live service.

| Test capability | Mocked behavior | External dependency |
|---|---|---|
| REST contract | `GET /api/v1/resource` validates a Bearer token and returns a controlled resource | None |
| GraphQL success | `POST /graphql` validates operation, variables, and query then returns products | None |
| GraphQL failure | `POST /graphql` returns a controlled GraphQL error envelope | None |
| Browser execution | Playwright uses a route-served `https://qualtan.mock` page | None |

Run the focused mocked suite with:

```bash
npm install --no-package-lock --no-audit --no-fund
npx playwright install chromium
CI=1 npm run test:mocks
```

Run the entire repository Playwright suite with:

```bash
CI=1 npm test
```

The GitHub Actions workflow discovers the committed `*.spec.ts` file, installs Chromium, and executes this mock suite. It also runs the committed Locust scenario through `scripts/run_performance_smoke.py`, which starts an ephemeral loopback REST/GraphQL mock server and tears it down after the smoke test. No CI job resolves or contacts a placeholder, staging, or production API host.

## AI IDE MCP support

All supported clients use QUALTAN’s local stdio server, [`mcp_server.py`](../mcp_server.py). The configuration files are committed as project templates, so a developer can clone the repository and open it directly in their IDE. Each template assumes that `python` resolves to a Python environment with the project dependencies installed.

| Client | Project template | Setup and verification |
|---|---|---|
| Cursor | [`.cursor/mcp.json`](../.cursor/mcp.json) | Open the project, then review the `qualtan` server in **Customize**. Cursor supports project-level `.cursor/mcp.json` for local stdio servers.[1] |
| Claude Code | [`.mcp.json`](../.mcp.json) | Run `claude` in the repository, accept workspace trust, then use `/mcp` or `claude mcp list` to review the pending project server. Claude Code does not let a cloned repository auto-approve its own MCP server.[2] |
| Codex | [`.codex/config.toml`](../.codex/config.toml) | Open the trusted repository in Codex CLI, IDE extension, or ChatGPT desktop. The project configuration uses `[mcp_servers.qualtan]` with prompt-based tool approval.[3] |
| Kiro | [`.kiro/settings/mcp.json`](../.kiro/settings/mcp.json) | Enable MCP support and open **Kiro: Open workspace MCP config (JSON)**. Saving reconnects the workspace server automatically; review the server in the Kiro MCP panel.[4] |

### Shared prerequisites

Install the Python runtime and dependencies before starting a local MCP server:

```bash
python3 -m pip install -r requirements.txt
python mcp_server.py
```

The final command is only a diagnostic; the client normally starts the server itself. If `python` is unavailable on a developer’s operating system, change the client template locally to the appropriate interpreter command, such as `python3` or an absolute virtual-environment path. Do not commit user-specific absolute paths or credentials back to these shared templates.

### Supported tools and approvals

The server exposes only QUALTAN’s narrow workflow operations: create a work item, run the quality workflow, record an approval, and retrieve work-item state. It intentionally does not expose unrestricted shell access, arbitrary code execution, or automatic external mutations. Codex is configured to prompt for tool approval; Kiro leaves `autoApprove` empty; Cursor and Claude Code require the user’s respective MCP/workspace review flows.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| MCP server fails to start | Run `python mcp_server.py` in the repository root. Confirm `python` points to the environment where `requirements.txt` was installed. |
| Cursor cannot find the script | Open the repository root as the workspace; the configuration uses `${workspaceFolder}`. |
| Claude Code shows pending approval | Start Claude Code in the project and accept workspace trust; this is an intentional protection against repository-controlled auto-enablement.[2] |
| Codex does not load the template | Trust the project and inspect `.codex/config.toml`; Codex project-scoped configuration is enabled only for trusted projects.[3] |
| Kiro ignores a configuration value | Open the workspace MCP configuration from the Kiro command palette and verify that the project scope is active. Workspace settings override Kiro global settings.[4] |
| CI reports a Locust failure | Run `python scripts/run_performance_smoke.py` locally and inspect the local mock API response contract. The CI test must not use a placeholder, staging, or production host. |

## References

[1]: https://cursor.com/docs/mcp "Cursor — Model Context Protocol"

[2]: https://code.claude.com/docs/en/mcp "Claude Code — Connect Claude Code to tools via MCP"

[3]: https://developers.openai.com/codex/mcp "OpenAI — Codex Model Context Protocol"

[4]: https://kiro.dev/docs/mcp/configuration/ "Kiro — MCP Configuration"
