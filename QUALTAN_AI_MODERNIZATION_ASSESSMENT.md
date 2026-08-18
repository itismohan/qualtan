# QUALTAN AI Modernization Assessment

**Author:** Manus AI  
**Perspective:** Senior AI Engineering  
**Assessment date:** 19 August 2026

## Executive assessment

QUALTAN has a compelling product direction: it connects requirements, test design, browser/API automation, synthetic data, performance, security, defect healing, test management, and reporting into one quality-engineering workflow. The current repository, however, is best described as a **collection of prompt-driven agent wrappers**, not yet a production-grade agent platform.

The most important modernization is not to add more agents or maximize autonomy. It is to make every agent **typed, observable, testable, policy-controlled, and composable**. Today, most agents return unvalidated text, the `full-cycle` command is a placeholder, X-Ray import is not implemented, configuration validation only prints warnings, and the MCP definition contains placeholder paths. These limitations will create brittle automation even if the underlying models improve.

My recommendation is to evolve QUALTAN into a **workflow-native quality engineering platform** with five foundations: a canonical artifact model, schema-constrained generation, durable orchestration, deterministic execution/verification, and continuous AI evaluation. Use autonomy for analysis and proposal; require policy gates for code changes, external system mutations, test execution against real environments, and production-affecting actions.

## Current-state findings

| Area | Current implementation | Engineering consequence | Priority |
|---|---|---|---:|
| Agent outputs | Raw `.content` strings from prompt chains | Downstream agents cannot reliably consume results; malformed JSON and missing fields are likely | P0 |
| Orchestration | Direct CLI instantiation; `full-cycle` is a stub | No durable state, retries, resumability, parallelism, or human approval | P0 |
| Model access | Repeated `ChatOpenAI(model="gpt-4.1-mini")` construction | No centralized routing, fallback, cost budget, latency policy, or provider portability | P1 |
| Validation | Prompt instructions such as “provide structured analysis” | Formatting is requested rather than enforced | P0 |
| Test generation | LLM-generated Playwright code is printed, not compiled or tested | The system can produce syntactically invalid, flaky, insecure, or semantically incorrect tests | P0 |
| Healing | Failure analysis returns a suggested snippet | No evidence-based patching, sandbox replay, diff review, or regression gate | P0 |
| Integrations | Jira/X-Ray are called directly inside agents | Credentials, retries, rate limits, idempotency, and audit trails are mixed with reasoning | P1 |
| MCP | Static configuration with placeholder absolute paths and incomplete tool exposure | Poor portability and unclear tool authorization | P1 |
| Evaluation | No agent trajectory, artifact, or quality regression suite | Prompt/model changes can silently degrade coverage or correctness | P0 |
| CI/CD | Playwright and smoke Locust execution only | No contract tests, generated-code checks, security scan, or AI quality gate | P1 |
| Configuration | Missing environment variables produce warnings | Misconfigured runs can continue and fail unpredictably | P1 |

## Target architecture

The target should be a graph of typed workflow nodes rather than a set of loosely coupled prompts.

```text
Jira / Git / OpenAPI / Playwright artifacts
                    |
             Ingestion + normalization
                    |
          Canonical Quality Work Item
                    |
     Planner graph: analyze -> design -> generate
                    |
      Policy gate + deterministic validators
        |                         |
  Human approval                Execute tests
        |                         |
     Artifact registry <- results, traces, evidence
                    |
       Diagnose -> propose patch -> replay
                    |
          X-Ray / Jira / CI / reports
```

The canonical object should be versioned and persisted. A minimal first version could contain `work_item_id`, requirement source, acceptance criteria, risk classification, assumptions, test intents, test cases, generated files, execution profile, evidence links, and provenance. Every artifact should include the model, prompt version, source references, validator results, and approval status.

For durable orchestration, use a stateful graph runtime such as LangGraph or an equivalent internal workflow engine. LangGraph’s documented capabilities include durable execution, streaming, persistence, and human-in-the-loop control.[4] The design should remain framework-light at the domain boundary so that agents are ordinary Python services and the graph is replaceable.

## Highest-value AI enhancements

### 1. Replace free-form generation with typed artifacts

Define Pydantic models for `StoryAnalysis`, `RiskModel`, `TestPlan`, `GherkinFeature`, `TestCase`, `GeneratedTestFile`, `SyntheticDataset`, `SecurityScenario`, `PerformanceProfile`, `FailureDiagnosis`, and `ExecutiveReport`. Generate against JSON Schema or Pydantic parsing rather than asking the model to “provide structured” text. Structured Outputs are specifically designed to make responses adhere to a supplied JSON Schema and to expose refusals programmatically.[1]

This single change will improve reliability more than another prompt-engineering pass. It also enables schema versioning, deterministic diffing, database persistence, API contracts, and independent validation.

### 2. Introduce a central model gateway and routing policy

Create `core/llm_gateway.py` with a stable interface such as `complete(task, input, output_schema, policy)`. The gateway should support model selection by task, fallback providers, timeouts, retries with jitter, token and cost budgets, caching for deterministic analysis, redaction, and request correlation IDs.

Use smaller/cheaper models for extraction, classification, selector ranking, and report formatting; use stronger reasoning/coding models for test-plan synthesis, ambiguous requirements, security analysis, and healing proposals. Do not hard-code model names inside each agent. Model choice should be configuration and policy, not application logic.

### 3. Turn the “full cycle” into a resumable workflow

Implement a graph with explicit nodes: `fetch_story`, `normalize_requirement`, `analyze_risk`, `generate_test_plan`, `generate_tests`, `validate_artifacts`, `approve_mutations`, `execute`, `diagnose_failures`, `propose_healing`, `replay`, `publish_results`, and `report`.

Each node must be idempotent. Persist state after every material step, record inputs/outputs, and support resume from the last successful node. Parallelize independent work such as functional, security, and performance planning, but join them through typed results. Add bounded retries and dead-letter handling for integration failures.

### 4. Add retrieval and evidence grounding

Build a quality knowledge base from approved test patterns, page-object conventions, API schemas, historical failures, security policies, flaky-test history, and prior accepted healing patches. Retrieve only relevant, permission-filtered material for each task.

Every generated test should carry evidence references: requirement clause, endpoint/schema, page/role/text source, and the repository convention used. For a Jira story, the system should distinguish facts from assumptions and flag missing acceptance criteria instead of inventing them.

### 5. Make generated code execute like software

Generated Playwright, Locust, and security artifacts must pass deterministic gates:

| Gate | Example check |
|---|---|
| Schema | Pydantic validation of the generated artifact |
| Syntax | TypeScript/Python parse and compile check |
| Static quality | ESLint, Ruff, formatting, dependency and secret scans |
| Contract | Playwright test discovery, API schema validation, Gherkin consistency |
| Safety | Allowed-host check, no destructive commands, credential redaction |
| Runtime | Isolated smoke replay with trace/video/screenshot capture |
| Review | Human approval for repository writes or external mutations |

The generator should write to a temporary branch/worktree, run the gates, and produce a patch. It should never silently overwrite a user’s test suite.

### 6. Upgrade self-healing into evidence-based repair

The existing healing agent should not directly “correct” code based only on a log and optional HTML. A safer loop is: classify failure; collect trace, screenshot, DOM/accessibility snapshot, network log, source revision, and recent history; generate ranked hypotheses; propose a minimal diff; apply it in a sandbox; replay the failed test and a regression subset; then request approval before merge.

Prefer stable Playwright locators—role, label, text, and test IDs—over inferred CSS or XPath. Playwright’s guidance emphasizes user-visible behavior, test isolation, and avoiding dependence on third-party systems.[6] Healing should therefore optimize for semantic locator quality and maintainability, not merely “make this run pass once.”

### 7. Add agent evaluations as first-class CI assets

Create a versioned `evals/` suite containing representative Jira stories, API schemas, failure traces, and expected artifact properties. Evaluate both the final artifact and the trajectory: tool selection, source grounding, policy compliance, execution outcome, and unnecessary actions. Agent evaluation guidance treats the path/tool use as a separate object of evaluation from the final answer.[5]

Recommended metrics include requirement coverage, acceptance-criteria coverage, schema validity, compile pass rate, first-run execution pass rate, flaky-test rate, mutation safety, healing replay success, false-positive rate, latency, and cost per work item. Use deterministic graders wherever possible and an LLM judge only for clearly defined semantic dimensions with calibration examples.

### 8. Treat MCP as a governed tool plane

Expose Jira, X-Ray, repository, Playwright, artifact storage, and test execution as narrow tools with explicit schemas and least-privilege credentials. MCP’s current tools specification describes uniquely named tools with metadata and schemas, and recommends that users be able to see and deny tool invocations.[3]

Separate read tools from mutation tools. For example, `jira.get_issue` can be automatic, while `xray.import_tests`, `git.apply_patch`, and `test.run_against_environment` require an approval policy. Log tool arguments, result hashes, actor, approval, and side effects. Do not expose a generic shell tool to the model.

### 9. Add multimodal failure understanding selectively

Use screenshots, Playwright traces, accessibility trees, DOM snapshots, and network logs as structured evidence. A vision-capable model can help classify visual regressions, layout shifts, and screenshot mismatches, but visual judgments should be paired with deterministic pixel/region thresholds and accessibility assertions. The model should explain evidence and rank hypotheses; it should not be the sole pass/fail oracle.

### 10. Add security and privacy by design

Introduce input classification and redaction before model calls. Jira descriptions, logs, DOM snapshots, and API payloads may contain credentials, tokens, personal data, or prompt-injection text. Treat all external text as untrusted data. Add tenant/project authorization to retrieval, allowlisted hosts for execution, secret scanning, retention limits, encrypted artifact storage, and audit logs.

Implement prompt-injection defenses at the tool boundary: the model may summarize untrusted content, but instructions found in that content must not override system policy. Require explicit approval for any action that changes Jira/X-Ray, files, environments, or test data.

## Recommended repository evolution

```text
qualtan/
  domain/
    models.py              # versioned Pydantic artifacts
    policies.py             # permissions, approvals, execution policy
  application/
    workflows.py           # durable workflow definitions
    commands.py             # use cases, not agent internals
  agents/
    requirement.py
    test_design.py
    code_generation.py
    diagnosis.py
    reporting.py
  integrations/
    jira.py
    xray.py
    playwright.py
    git.py
  infrastructure/
    llm_gateway.py
    retrieval.py
    persistence.py
    tracing.py
    redaction.py
  validators/
    schemas.py
    code.py
    runtime.py
    security.py
  evals/
    datasets/
    graders/
    run_evals.py
  cli/
    main.py
```

Keep the current agent names as compatibility wrappers initially, but move their logic behind typed application services. This allows incremental migration without breaking the CLI or MCP consumers.

## Phased roadmap

| Phase | Timeline | Deliverables | Exit criteria |
|---|---:|---|---|
| Foundation | 0–2 weeks | Central config, model gateway, typed models, structured logging, strict startup validation, secret redaction | Every command emits a typed result or a typed error; no agent hard-codes credentials/model policy |
| Reliable generation | 2–5 weeks | Schema-constrained agents, artifact registry, TypeScript/Python validators, generated-code sandbox, real X-Ray mapping | Generated artifacts validate, compile, and are persisted with provenance |
| Durable workflow | 5–8 weeks | Implemented full-cycle graph, persistence, retries, resumability, approval gates, parallel branches | A failed run can resume; external mutations are idempotent and auditable |
| Evidence and evaluation | 8–12 weeks | Retrieval index, eval datasets, trajectory graders, CI quality gates, cost/latency dashboard | Model/prompt changes cannot merge when key quality metrics regress |
| Advanced intelligence | 12+ weeks | Trace-based healing, multimodal diagnosis, risk-based test selection, flaky-test prediction, adaptive coverage planning | AI features demonstrate measurable improvement against the baseline, not only qualitative appeal |

## Metrics that should govern investment

Do not measure success by the number of agents or generated lines of code. Track the following baseline and target metrics:

| Dimension | Metric |
|---|---|
| Correctness | Percentage of generated artifacts passing schema, compile, and runtime gates |
| Coverage | Acceptance-criteria and risk coverage per work item |
| Stability | First-run pass rate and seven-day flaky-test rate |
| Healing | Percentage of proposed fixes that pass replay plus regression checks |
| Safety | Unauthorized mutation count, secret leakage incidents, and blocked unsafe actions |
| Efficiency | Median cycle time, model latency, and cost per accepted test |
| Adoption | Percentage of generated artifacts accepted with no manual rewrite |
| Operations | Resumable-run success rate and integration failure recovery rate |

## What I would build first

The first vertical slice should be deliberately narrow: **Jira story to one approved Playwright test**. It should fetch and normalize the story, produce a typed risk/test plan, generate one test file, validate and compile it, run it in an isolated environment, attach evidence, and require approval before writing to the repository or X-Ray. This slice exercises the entire architecture and exposes the highest-risk boundaries.

I would not begin with autonomous multi-agent debate, a generic “AI test engineer” chat UI, or additional model providers. Those features can be added later, but they will amplify today’s lack of contracts and observability. Reliability, evidence, and safe execution are the differentiators that will make QUALTAN credible in enterprise QA environments.

## Final recommendation

QUALTAN should position itself as an **AI quality engineering control plane**, not merely an LLM test generator. The winning design combines deterministic testing infrastructure with probabilistic reasoning: models propose and prioritize; schemas, compilers, policy engines, test runners, and human approvals decide what is allowed to ship.

If the team completes only three upgrades in the next quarter, make them: **(1) typed structured artifacts, (2) a real durable full-cycle workflow with approval gates, and (3) an evaluation/validation harness that executes every generated artifact**. Those three changes will create the platform required for all later enhancements—retrieval, multimodal diagnosis, model routing, self-healing, and agent interoperability.

## References

[1]: https://developers.openai.com/api/docs/guides/structured-outputs "OpenAI — Structured model outputs"

[2]: https://developers.openai.com/api/reference/responses/overview "OpenAI — Responses API overview"

[3]: https://modelcontextprotocol.io/specification/2026-07-28/server/tools "Model Context Protocol — Tools specification"

[4]: https://docs.langchain.com/oss/python/langgraph/overview "LangChain — LangGraph overview"

[5]: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents "Anthropic — Demystifying evals for AI agents"

[6]: https://playwright.dev/docs/best-practices "Playwright — Best practices"
