"""Backward-compatible X-Ray agent using typed mapping and governed mutations."""

from __future__ import annotations

import json
from dataclasses import dataclass

from domain.models import ExecutionResult, RunStatus, TestCase, TestPlan, TestStep, TestType
from integrations.xray import XRayClient, XRayGateway


@dataclass
class XRayAgent:
    client: XRayGateway | None = None

    def __post_init__(self) -> None:
        self.client = self.client or XRayClient()

    def map_test_cases_to_xray(self, generated_test_cases: str) -> str:
        return json.dumps(self.client.map_test_plan(_plan_from_legacy(generated_test_cases)), indent=2)

    def import_test_cases(self, generated_test_cases: str, *, approved: bool = False) -> dict[str, object]:
        return self.client.import_test_plan(_plan_from_legacy(generated_test_cases), approved=approved)

    def sync_results(self, playwright_results: str, *, approved: bool = False) -> dict[str, object]:
        status = RunStatus.FAILED if "fail" in playwright_results.lower() else RunStatus.SUCCEEDED
        result = ExecutionResult(status=status, stdout=playwright_results)
        return self.client.publish_execution(result, approved=approved)


def _plan_from_legacy(content: str) -> TestPlan:
    try:
        return TestPlan.model_validate_json(content)
    except Exception:
        return TestPlan(
            story_key="ADHOC",
            strategy="Legacy test-case import",
            cases=[
                TestCase(
                    case_id="LEGACY-1",
                    title="Imported legacy test case",
                    objective="Preserve legacy test content for review and X-Ray mapping.",
                    test_type=TestType.WEB,
                    steps=[TestStep(action="Review supplied test case", expected_result=content[:2000])],
                )
            ],
        )
