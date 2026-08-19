# QUALTAN Offline Demo

This demonstration verifies QUALTAN’s governed workflow foundations without a Jira account, model-provider key, cloud target, browser service, or production data. It is the recommended first experience for contributors and evaluators.

> **What this demonstrates:** Requirement analysis, test planning, generated-artifact validation, durable approval state, evidence redaction, and execution policy are tested through deterministic fixtures. No model call or external mutation is performed.

## Prerequisites

Install the project and test dependencies from the repository root:

```bash
python3 -m pip install ".[test]"
```

Node.js and Playwright are optional for the Python-only workflow demonstration. Install them only when running the browser mock tests.

## Step 1: inspect local readiness

```bash
qualtan doctor --json
```

The output intentionally reports only readiness booleans and policy posture. It does not print secret values, target URLs, or host allowlist entries. A missing model, Jira, or X-Ray credential is expected for this offline demonstration.

## Step 2: exercise the governed workflow

```bash
pytest -q tests/test_modernized_framework.py
```

The test suite creates a typed requirement, generates deterministic test artifacts through a static gateway, persists a work item, validates the artifacts, and verifies that the workflow blocks until a human approval is recorded when approval is required.

## Step 3: verify repository controls

```bash
python3 scripts/validate_framework.py
```

This confirms the documented architecture and validation assets are present and that the repository remains structurally ready for local development.

## Optional: run deterministic REST and GraphQL browser mocks

```bash
npm install
npx playwright install --with-deps chromium
CI=1 npm run test:mocks
```

The mock suite stubs network routes inside the browser test process. It does not contact `api.example.com`, a live GraphQL endpoint, or any external placeholder service.

## Next step: connect an approved integration

After completing the offline demonstration, configure a non-production model provider and Jira connection in `.env`. Start with `full-cycle` only after reviewing the [policy configuration](../../README.md#policy-configuration). External execution remains host-allowlisted and approval-gated; external mutations remain disabled until explicitly enabled and approved.
