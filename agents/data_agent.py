"""Backward-compatible synthetic-data agent using a privacy-aware contract."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import data_service, pretty
from infrastructure.llm_gateway import LLMGateway


@dataclass
class DataAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._data = data_service(self.gateway)

    def generate_test_data(self, schema: str, count: int = 5) -> str:
        return pretty(self._data.generate(schema, count))
