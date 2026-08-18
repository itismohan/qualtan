"""Backward-compatible executive reporting agent backed by typed contracts."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import pretty, reporting_service
from infrastructure.llm_gateway import LLMGateway


@dataclass
class ReportingAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._reporting = reporting_service(self.gateway)

    def generate_executive_summary(self, test_results: str) -> str:
        return pretty(self._reporting.summarize(test_results))
