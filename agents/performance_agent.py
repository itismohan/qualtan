"""Backward-compatible performance agent with safe planning boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import performance_service, pretty, reporting_service
from infrastructure.llm_gateway import LLMGateway


@dataclass
class PerformanceAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._performance = performance_service(self.gateway)
        self._reporting = reporting_service(self.gateway)

    def generate_locust_script(self, api_spec: str, load_profile: str = "standard") -> str:
        plan = self._performance.plan(f"Load profile: {load_profile}\n\nAPI specification:\n{api_spec}")
        return plan.locust_script

    def analyze_performance_results(self, stats_csv: str) -> str:
        return pretty(self._reporting.summarize(f"Locust performance statistics:\n{stats_csv}"))
