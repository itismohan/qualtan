<p align="center">
  <img src="assets/qualtan.png" alt="QUALTAN logo" width="700"/>
</p>

# QUALTAN: Your Spartan for Quality
## Overview
The **QUALTAN** framework is a cutting-edge, multi-agent test automation solution designed to maximize efficiency and coverage across the entire testing lifecycle. It utilizes a modular, agent-base[...]

## Key Features and Agentic Architecture
**QUALTAN's** power lies in its specialized, cooperative agents:

| Agent | Purpose | CLI Command | Example Usage |
| :--- | :--- | :--- | :--- |
| **JIRA Agent** | Requirement Extraction & Analysis | `jira-agent` | `python cli/main.py jira-agent --story PROJ-123` |
| **Designer Agent** | Test Case & Gherkin Generation | `testcase-agent` | `python cli/main.py testcase-agent --analysis "User can login..."` |
| **ScriptGen Agent** | Playwright Script Generation | `script-agent` | `python cli/main.py script-agent --gherkin "Scenario: Login" --type web` |
| **Data Agent** | Synthetic Test Data Generation | `data-agent` | `python cli/main.py data-agent --schema "User(name, email)" --count 10` |
| **XRay Agent** | Test Management Sync | `xray-agent` | `python cli/main.py xray-agent --cases "Test Case 1..."` |
| **Performance Agent** | Load Test Generation | `perf-agent` | `python cli/main.py perf-agent --spec api_spec.json` |
| **Security Agent** | Security Scenario Generation | `security-agent` | `python cli/main.py security-agent --spec api_spec.json` |
| **Reporting Agent** | Executive Summary | `report-agent` | `python cli/main.py report-agent --results "Pass: 10, Fail: 2"` |
| **Orchestration** | Full E2E Automation Cycle | `full-cycle` | `python cli/main.py full-cycle --story PROJ-123` |

## Technology Stack
*   **Orchestration**: Python 3.11, LangChain, Click (CLI)
*   **Testing**: Playwright, TypeScript
*   **Performance**: Locust
*   **Configuration**: `.env` files for centralized secrets management.
*   **CI/CD**: GitHub Actions (pre-configured)

## Setup and Installation

### Prerequisites
*   Node.js (v18+)
*   Python (v3.11+)
*   **Crucially, set up your environment variables** by creating a `.env` file from the provided `.env.example`.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone <repository-url> saint
    cd saint
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Node.js dependencies (for Playwright):**
    ```bash
    npm install
    npx playwright install --with-deps
    ```

## MCP Configuration for Cursor IDE and Claude Desktop

The `mcp.json` file allows you to integrate SAINT's agents directly into your IDE's AI chat interface.

1.  **Locate the `mcp.json` file** in the root of the `saint` directory.
2.  **Update the paths**: You must replace `/absolute/path/to/saint` within the `mcp.json` file with the actual absolute path of the `saint` directory on your local machine.
3.  **Configure Environment Variables**: Ensure all necessary environment variables (JIRA, X-Ray, OpenAI keys) are set in your IDE's environment or directly within the `mcp.json`'s `env` block.
4.  **Integration**: Follow your IDE's instructions to load the `mcp.json` file. Once loaded, you can call the agents directly from the chat, for example:
    *   **Cursor IDE/Claude Desktop Prompt**: "Use the `jira_agent` tool to analyze story `PROJ-456`."


