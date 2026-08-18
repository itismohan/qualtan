# QUALTAN Implementation Handover

**Completion date:** 19 August 2026  
**Status:** Implemented and locally verified

## Delivered modernization

The framework has been refactored from independent prompt wrappers into a governed AI quality engineering platform. The implementation introduces strict Pydantic contracts, a centralized schema-constrained model gateway, durable persisted workflow state, approval controls, deterministic validation, retrievable quality knowledge, multimodal evidence collection, telemetry, evaluation, and a real MCP tool server.

| Modernization gap | Delivered implementation |
|---|---|
| Raw text between agents | Versioned strict domain contracts in `domain/models.py` for stories, risks, test plans, code artifacts, data, security, performance, reports, failures, approvals, and executions |
| Hard-coded model calls | `infrastructure/llm_gateway.py` centralizes model selection, strict JSON-schema responses, Pydantic validation, sensitive-data redaction, bounded retries, caching, and safe telemetry |
| Placeholder full cycle | `application/workflows.py` implements checkpointed requirement → plan → generate → approval → validate orchestration with persisted resume support |
| No provenance | Work items and generated files capture source references, content hashes, model/prompt metadata, validation results, approvals, executions, and event history |
| No validation of generated code | Schema integrity, acceptance-criteria coverage, source safety, and isolated TypeScript compilation gates are in `validators/quality_gates.py` |
| Unsafe execution or mutations | Host allowlisting, safe-command screening, feature flags, and approval policies are implemented in `infrastructure/security.py` and `infrastructure/test_execution.py` |
| Prompt-only healing | `agents/healing_agent.py` now proposes a minimal, review-required repair backed by redacted logs, traces, DOM, accessibility, network, and optional screenshot evidence |
| No retrieval | `infrastructure/retrieval.py` provides scope-filtered, persisted retrieval of approved quality documents; retrieved content is passed to models as evidence, not instructions |
| No observability | `infrastructure/telemetry.py` records model task, model ID, prompt version, input hash, latency, and token metrics without storing prompts or completions |
| No regression evaluation | `evals/` includes deterministic grading for coverage, validation rate, workflow safety, and completion |
| Static/placeholder MCP | `mcp_server.py` provides narrow audited workflow tools, while `mcp.json` launches the real server rather than describing imaginary static tools |
| Legacy agents | The old agents remain as compatibility facades but now delegate to typed modern services rather than direct prompt chains |
| Basic CI only | `ci/github-actions.yml` now runs syntax checks, framework tests, Playwright tests, bounded Locust smoke testing, advisory checks, and evidence upload |

## Operator workflow

The safe default is to create a work item, generate an artifact, pause for explicit review, approve it, and then resume validation.

```bash
python3 cli/main.py full-cycle --story QUAL-123
python3 cli/main.py workflow-approve \
  --work-item <work-item-id> \
  --request <approval-request-id> \
  --approver qa-lead@example.com \
  --note "Reviewed test intent and selector strategy"
python3 cli/main.py workflow-resume --work-item <work-item-id>
python3 cli/main.py workflow-eval --work-item <work-item-id>
```

External mutations remain disabled by default. Test execution is blocked until both the target host is allowlisted and an approval is recorded. X-Ray publishing requires the external-mutation feature flag plus approval.

## Verification evidence

The final local verification completed successfully:

```text
python3 -m compileall -q agents application cli core domain evals infrastructure integrations validators tests mcp_server.py
pytest -q tests
python3 cli/main.py --help
python3 -m json.tool mcp.json
git diff --check
```

The deterministic test suite passed **4 tests**. It verifies durable workflow state and resume behavior, approval gating, generated-code validation, sensitive-data redaction, execution host/command policy enforcement, scope-filtered knowledge retrieval, and failure-evidence redaction.

## Required deployment setup

Copy `.env.example` to `.env`, install the updated Python and Node dependencies, and configure the approved model provider, Jira, X-Ray where needed, and non-production target hosts. Do not enable `QUALTAN_ALLOW_EXTERNAL_MUTATIONS` until the integration permissions and approval process have been reviewed.

The implementation does not execute a live Jira, X-Ray, LLM, browser, or external test-environment workflow without user-provided configuration and approval. This is intentional: live integrations and executions are now governed operational actions rather than implicit behavior.

## Primary files to review

| File or directory | Why it matters |
|---|---|
| `README.md` | Architecture, operating model, configuration, workflow, retrieval, MCP, and validation guide |
| `domain/models.py` | Canonical typed contracts and provenance structures |
| `application/workflows.py` | Durable state machine and approval behavior |
| `infrastructure/llm_gateway.py` | Central structured-generation and model-governance boundary |
| `validators/quality_gates.py` | Generated-artifact quality gates |
| `mcp_server.py` | Governed interoperability endpoint |
| `tests/test_modernized_framework.py` | Offline regression coverage |

