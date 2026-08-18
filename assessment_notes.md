# Qualtan assessment notes

## Repository observations

- The framework is a Python CLI with independent LangChain agents for Jira analysis, test design, Playwright/script generation, synthetic data, Xray, performance, security, healing, and reporting.
- `cli/main.py` instantiates agents directly. The `full-cycle` command is only a placeholder; there is no executable end-to-end orchestration.
- Agent outputs are primarily raw `.content` strings from prompt chains. There are no Pydantic/JSON-schema contracts, typed domain models, validation gates, or structured error handling.
- The same model configuration pattern is duplicated across agents; there is no central model router, retry/budget policy, prompt registry, or provider abstraction.
- Xray mapping comments that parsing/import is not implemented. The MCP configuration is a static JSON file with placeholder paths and only a subset of agents exposed.
- CI runs Playwright and a smoke Locust test, but there are no AI-agent regression/evaluation suites, quality gates, trace collection, security scanning, or generated-artifact validation visible in the repository.
- The repository history is small and the working tree contains only an untracked `.DS_Store`.

## External research findings

1. OpenAI Structured Outputs documentation states that schema-constrained responses adhere to a supplied JSON Schema, supporting reliable type-safety and programmatically detectable refusals. It provides Pydantic parsing helpers. Source: https://developers.openai.com/api/docs/guides/structured-outputs
2. OpenAI Responses documentation describes a current response interface with text/image inputs and tools such as file search, web search, and other tool integrations. Source: https://developers.openai.com/api/reference/responses/overview
3. MCP’s latest tools specification says servers expose uniquely named tools with metadata and schemas. It recommends a human in the loop for trust and safety, clear tool visibility, invocation indicators, and confirmation prompts. Source: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
4. LangGraph documentation describes an orchestration runtime centered on durable execution, streaming, human-in-the-loop, and persistence. Source: https://docs.langchain.com/oss/python/langgraph/overview
5. Anthropic’s agent-evaluation guidance distinguishes evaluating final answers from evaluating trajectories/tool use and recommends task-specific graders and repeatable datasets. Source: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
6. Playwright best practices emphasize user-visible behavior, isolated tests, and avoiding testing third-party dependencies. Source: https://playwright.dev/docs/best-practices

## Initial technical judgment

Qualtan’s core idea is strong, but its current implementation is closer to a collection of prompt wrappers than a production-grade agent platform. The highest-leverage modernization is not adding more autonomous agents; it is introducing typed artifacts, a durable workflow graph, tool/API boundaries, deterministic validation, evaluation, security controls, and observability. Autonomy should be constrained to planning and proposal, while test execution, external mutations, and repository changes require policy checks and approvals.
