"""Run QUALTAN's offline production-readiness validation checks.

This script deliberately avoids live Jira, X-Ray, LLM, browser, and target-environment
operations. Those boundaries require operator configuration and explicit approval.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_PATH = PROJECT_ROOT / "artifacts" / "validation" / "framework-validation.json"


def run_check(name: str, command: list[str], timeout: int = 120) -> dict[str, Any]:
    started = datetime.now(UTC)
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "name": name,
            "passed": result.returncode == 0,
            "command": command,
            "started_at": started.isoformat(),
            "finished_at": datetime.now(UTC).isoformat(),
            "exit_code": result.returncode,
            "stdout": result.stdout[-4_000:],
            "stderr": result.stderr[-4_000:],
        }
    except subprocess.TimeoutExpired as error:
        return {
            "name": name,
            "passed": False,
            "command": command,
            "started_at": started.isoformat(),
            "finished_at": datetime.now(UTC).isoformat(),
            "exit_code": None,
            "stdout": (error.stdout or "")[-4_000:] if isinstance(error.stdout, str) else "",
            "stderr": f"Timed out after {timeout} seconds.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run QUALTAN's offline framework validation suite.")
    parser.add_argument("--report", type=Path, default=VALIDATION_PATH, help="JSON report path.")
    args = parser.parse_args()

    source_paths = [
        "agents",
        "application",
        "cli",
        "core",
        "domain",
        "evals",
        "infrastructure",
        "integrations",
        "validators",
        "tests",
        "performance",
        "mcp_server.py",
    ]
    checks = [
        run_check("python_compilation", [sys.executable, "-m", "compileall", "-q", *source_paths]),
        run_check("regression_and_integration_tests", [sys.executable, "-m", "pytest", "-q", "tests"]),
        run_check("cli_command_discovery", [sys.executable, "cli/main.py", "--help"]),
        run_check("mcp_configuration_json", [sys.executable, "-m", "json.tool", "mcp.json"]),
        run_check("whitespace_integrity", ["git", "diff", "--check"]),
    ]
    report = {
        "framework": "QUALTAN",
        "validation_mode": "offline_no_external_side_effects",
        "created_at": datetime.now(UTC).isoformat(),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "not_executed": [
            "Live Jira retrieval",
            "Live X-Ray mutation",
            "Live model invocation",
            "Browser execution against an external environment",
        ],
        "operator_note": "Run live integrations only after configuring approved credentials, targets, and human approvals.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for item in checks:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"[{status}] {item['name']}")
    print(f"Report: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
