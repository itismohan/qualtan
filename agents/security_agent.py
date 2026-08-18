"""Backward-compatible agent for safe, authorized security test planning."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import pretty, security_service
from infrastructure.llm_gateway import LLMGateway


@dataclass
class SecurityAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._security = security_service(self.gateway)

    def generate_security_scenarios(self, api_spec: str) -> str:
        return pretty(self._security.assess(api_spec))
