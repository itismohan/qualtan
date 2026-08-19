# QUALTAN Requests for Comments

An RFC is required for a material change to a public domain model, persisted work-item state, policy schema, approval semantic, CLI command, MCP tool, plugin interface, supported runtime, or security boundary. The goal is not bureaucracy: it is to let users and contributors understand the safety, compatibility, and migration consequences before implementation begins.

## RFC lifecycle

| State | Meaning | Maintainer action |
|---|---|---|
| Draft | Proposal is open for technical and community feedback | Confirm scope and identify affected owners |
| Accepted | Project has agreed to pursue the design | Link implementation issue and compatibility plan |
| Implemented | Code, tests, docs, and migration guidance are released | Link release note and close implementation work |
| Rejected | The project will not pursue the proposal | Record rationale and viable alternatives |
| Superseded | A newer proposal replaces the design | Link successor RFC |

## Required content

Each RFC must explain the user problem, goals and non-goals, proposed design, alternatives, security and privacy impact, policy and side effects, compatibility impact, migration and rollback plan, test strategy, documentation changes, and open questions. Do not include credentials, private customer evidence, or vulnerability details.

Core maintainers decide RFCs under [`GOVERNANCE.md`](../../GOVERNANCE.md). Security-sensitive designs may require private review before a public RFC can be opened.
