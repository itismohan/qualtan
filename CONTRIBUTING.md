# Contributing to QUALTAN

Thank you for helping improve QUALTAN. The project accepts code, documentation, examples, integration adapters, quality rules, and reproducible bug reports. Contributions must strengthen the framework’s core promise: models may propose; **typed contracts, deterministic validation, policy controls, and recorded approvals decide what proceeds**.

## Before opening an issue or pull request

Use GitHub Discussions for design questions, implementation proposals, and requests for help. Use an issue for a reproducible defect or a scoped feature request. Do not put credentials, customer data, production URLs, raw test evidence, or a suspected vulnerability in a public issue. Follow [`SECURITY.md`](SECURITY.md) for private vulnerability reporting.

| Change type | Start here | Required evidence |
|---|---|---|
| Defect | Bug-report issue form | Minimal reproduction, expected and actual behavior, redacted logs |
| Feature or integration | Feature-request issue or design discussion | User problem, proposed public contract, policy and side-effect analysis |
| Public API or policy schema | RFC in `docs/rfcs/` | Compatibility plan, migration plan, security review |
| Documentation or examples | Pull request | Accurate commands, validated links, no secrets or machine-specific paths |
| Security-sensitive behavior | Private disclosure or maintainer discussion | Threat model, least-privilege behavior, deterministic tests |

## Development setup

QUALTAN requires Python 3.11+ and Node.js 22+. Start from a clean local checkout and never commit a populated `.env` file.

```bash
cp .env.example .env
python3 -m pip install -r requirements.txt
npm install
npx playwright install --with-deps chromium

pytest -q tests
CI=1 npm run test:mocks
python3 scripts/validate_framework.py
```

The mock browser tests and performance smoke runner are designed to use local deterministic services. Do not replace them with unapproved production targets or external placeholder hosts.

## Contribution requirements

Keep each pull request focused, explain the user-visible effect, and update documentation and tests with the change. Backward-compatible CLI commands are a public compatibility commitment. Changes to domain models, policy schemas, workflow checkpoints, CLI commands, MCP tools, or integration interfaces must state their compatibility impact explicitly.

All code must pass the project checks before review:

```bash
python3 -m compileall -q agents application cli core domain evals infrastructure integrations validators tests mcp_server.py
pytest -q tests
CI=1 npm run test:mocks
python3 scripts/validate_framework.py
```

| Area | Contribution rule |
|---|---|
| Generated test code | Keep deterministic validation gates and source-safety controls intact. |
| Execution | Preserve host allowlisting and approval requirements. |
| External mutations | Keep disabled by default and require explicit policy enablement plus recorded approval. |
| MCP | Do not add generic shell, filesystem, credential, or arbitrary HTTP tools. |
| Secrets and evidence | Redact sensitive content and use environment or secret-manager references only. |
| Dependencies | Add only maintained, appropriately licensed dependencies with a clear purpose. |

## Developer Certificate of Origin

By contributing, you certify that each contribution is submitted under the [Developer Certificate of Origin 1.1](DCO.txt) and may be distributed under the project’s [Apache-2.0 license](LICENSE). Sign every commit with a DCO sign-off:

```bash
git commit -s -m "Add deterministic adapter validation"
```

The sign-off uses your real name and email in the commit trailer. Contributions without a valid `Signed-off-by:` line may be asked to amend their commits before review.

## Review and merge

Maintainers review correctness, public API compatibility, security, policy behavior, tests, documentation, and operational impact. A maintainer with relevant ownership approval is required for changes to protected areas. The project follows the decision and escalation model in [`GOVERNANCE.md`](GOVERNANCE.md).

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) in all project spaces.
