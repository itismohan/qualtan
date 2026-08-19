## Summary

Explain the user-visible change and link the related issue or RFC.

## Safety and compatibility impact

State the effect on typed contracts, persisted workflow state, CLI compatibility, MCP tools, policy controls, approvals, execution, external mutations, secrets, and evidence handling. Write `None` only after considering each area.

## Validation evidence

Describe the checks you ran and their results. Include focused tests for changed behavior and update documentation or examples when needed.

- [ ] `python3 -m compileall -q agents application cli core domain evals infrastructure integrations validators tests mcp_server.py`
- [ ] `pytest -q tests`
- [ ] `CI=1 npm run test:mocks` when browser/API/GraphQL behavior changes
- [ ] `python3 scripts/validate_framework.py`
- [ ] Relevant generated artifacts, logs, and fixtures are redacted and bounded

## Contribution checklist

- [ ] My commits include a DCO `Signed-off-by:` trailer.
- [ ] I have not added credentials, private data, machine-specific paths, or automatic approval behavior.
- [ ] I have preserved approval-gated execution and disabled-by-default external mutations.
- [ ] I updated public documentation, configuration references, and compatibility notes as needed.
- [ ] I have considered the release-note impact.
