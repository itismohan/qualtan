"""Backward-compatible healing agent that proposes, but never applies, repairs."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import diagnosis_service, failure_evidence, pretty
from infrastructure.evidence import FailureEvidenceCollector
from infrastructure.llm_gateway import LLMGateway


@dataclass
class HealingAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._diagnosis = diagnosis_service(self.gateway)

    def analyze_failure(self, error_log: str, script_content: str, html_snapshot: str | None = None) -> str:
        evidence = failure_evidence(error_log, script_content, html_snapshot)
        return pretty(self._diagnosis.diagnose(evidence))

    def analyze_failure_with_evidence(
        self,
        error_log: str,
        script_content: str,
        *,
        trace_path: str | None = None,
        screenshot_path: str | None = None,
        dom_snapshot_path: str | None = None,
        accessibility_snapshot_path: str | None = None,
        network_log_path: str | None = None,
    ) -> str:
        """Propose a review-required repair using bounded, redacted execution evidence."""
        collected = FailureEvidenceCollector().collect(
            error_log=error_log,
            script_content=script_content,
            trace_path=trace_path,
            screenshot_path=screenshot_path,
            dom_snapshot_path=dom_snapshot_path,
            accessibility_snapshot_path=accessibility_snapshot_path,
            network_log_path=network_log_path,
        )
        return pretty(self._diagnosis.diagnose(collected.evidence, collected.image_data_urls))
