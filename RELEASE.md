# Release Process

## Release principles

QUALTAN releases must preserve reproducibility, backward compatibility, and its governed execution model. A release is not ready if it introduces credentials, machine-specific paths, automatic approvals, generic MCP execution access, enabled-by-default external mutations, or an unreviewed dependency or license change.

The project follows semantic versioning for documented public interfaces. Changes to typed contracts, persisted work-item state, policy schemas, approval semantics, CLI commands, MCP tools, plugin protocols, or supported runtimes require explicit compatibility analysis and release notes.

## Maintainer checklist

| Stage | Required action | Evidence |
|---|---|---|
| Scope | Confirm version, release owner, included PRs, migration impact, and release notes | Milestone or release issue |
| Source hygiene | Confirm clean working tree; scan current tree and history for secrets; verify third-party ownership and license posture | Review record |
| Validation | Run Python, browser-mock, performance-smoke, framework, package-build, and dependency checks | CI run and local command output |
| Security | Review advisories, dependency audit, secret scanning, policy changes, MCP template changes, and approval behavior | Security review note |
| Packaging | Build source and wheel artifacts; inspect contents, license, NOTICE, metadata, and entry point | Build artifact checksums |
| Publication | Create signed or verified tag, publish release notes and SBOM, attach checksums | GitHub release record |
| Follow-up | Monitor issues, advisories, installation failures, and downgrade/rollback needs | Release issue closure |

## Pre-release validation

Run these commands from a clean checkout after installing all project dependencies.

```bash
python3 -m compileall -q agents application cli core domain evals infrastructure integrations validators tests mcp_server.py
pytest -q tests
CI=1 npm run test:mocks
python3 scripts/run_performance_smoke.py
python3 scripts/validate_framework.py
python3 -m pip install --upgrade build
python3 -m build
python3 -m pip install --force-reinstall dist/*.whl
qualtan doctor --json
python3 -m pip check
```

The package installation check must run in an isolated environment in CI before a stable release. The build command creates distributable files under `dist/`; these are release artifacts and must not be committed.

## Release artifacts

Each public release should contain the source archive, wheel, `LICENSE`, `NOTICE`, changelog entry, compatibility notes, a machine-readable software bill of materials, checksums, and provenance/attestation once the automated publishing workflow is enabled. Do not publish a package merely because CI passed: release notes must describe functional changes, fixed defects, dependency/security changes, and required migration steps.

## Emergency security release

Security issues may require an expedited patch. Preserve the coordinated disclosure process in [`SECURITY.md`](SECURITY.md), avoid public discussion until the reporter and maintainers agree on disclosure, and document any urgent changes to defaults or policy behavior. Backport only when the supported-version table and maintainer capacity make it realistic; otherwise publish an explicit upgrade notice.

## Owner-only GitHub configuration

The following tasks require repository-owner access and cannot be completed by a source commit:

1. Make the repository public only after the release-readiness audit and owner approval.
2. Enable private vulnerability reporting and configure security-alert notifications.
3. Enable Dependabot alerts, secret scanning, and code scanning if available for the repository plan.
4. Protect `main` with pull-request review, required status checks, and no force pushes.
5. Create and protect a `v*` release-tag policy; require an approved release workflow before publishing artifacts.
6. Enable GitHub Discussions and create categories for support, ideas, Q&A, and announcements.
7. Add repository topics, a short description, a project website if available, and funding information only when appropriate.
8. Configure a package registry or trusted publishing identity before publishing to PyPI.

See [`docs/OPEN_SOURCE_RELEASE.md`](docs/OPEN_SOURCE_RELEASE.md) for the public-launch runbook.
