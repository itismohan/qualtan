"""Controlled test execution with host allowlisting, approval checks, and evidence capture."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.config import Settings, get_settings
from domain.models import ExecutionResult, RunStatus
from infrastructure.security import ExecutionPolicy, PolicyViolation


@dataclass
class TestExecutionService:
    project_root: Path
    settings: Settings | None = None
    timeout_seconds: int = 300

    def __post_init__(self) -> None:
        self.settings = self.settings or get_settings()
        self.policy = ExecutionPolicy(self.settings)

    def execute(self, command: list[str], target_url: str, *, approved: bool) -> ExecutionResult:
        self.policy.assert_safe_command(command)
        self.policy.assert_allowed_host(target_url)
        if self.policy.requires_execution_approval() and not approved:
            raise PolicyViolation("Test execution requires recorded human approval.")

        started = datetime.now(UTC)
        try:
            completed = subprocess.run(
                command,
                cwd=self.project_root,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                env={**__import__("os").environ, "BASE_URL": target_url},
            )
            status = RunStatus.SUCCEEDED if completed.returncode == 0 else RunStatus.FAILED
            return ExecutionResult(
                status=status,
                command=command,
                target=target_url,
                started_at=started,
                finished_at=datetime.now(UTC),
                exit_code=completed.returncode,
                stdout=completed.stdout[-20_000:],
                stderr=completed.stderr[-20_000:],
            )
        except subprocess.TimeoutExpired as error:
            return ExecutionResult(
                status=RunStatus.FAILED,
                command=command,
                target=target_url,
                started_at=started,
                finished_at=datetime.now(UTC),
                stdout=(error.stdout or "")[-20_000:] if isinstance(error.stdout, str) else "",
                stderr=(error.stderr or "timeout")[-20_000:] if isinstance(error.stderr, str) else "timeout",
            )
""
