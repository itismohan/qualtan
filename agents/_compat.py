"""Compatibility helpers for legacy agent method signatures."""

from __future__ import annotations

import json

from application.agents import (
    FailureDiagnosisService,
    PerformancePlanningService,
    ReportingService,
    RequirementAnalysisService,
    SecurityAssessmentService,
    SyntheticDataService,
    TestCodeGenerationService,
    TestDesignService,
)
from domain.models import AcceptanceCriterion, FailureEvidence, StoryDetails, TestPlan
from infrastructure.llm_gateway import LLMGateway, OpenAIModelGateway


def gateway_or_default(gateway: LLMGateway | None) -> LLMGateway:
    return gateway or OpenAIModelGateway()


def story_from_legacy(data: dict[str, object]) -> StoryDetails:
    raw_criteria = data.get("acceptance_criteria", [])
    if isinstance(raw_criteria, str):
        raw_criteria = [line.strip(" -") for line in raw_criteria.splitlines() if line.strip()]
    criteria = [
        AcceptanceCriterion(criterion_id=f"AC-{index + 1}", text=str(value))
        for index, value in enumerate(raw_criteria if isinstance(raw_criteria, list) else [])
    ]
    return StoryDetails(
        key=str(data.get("key", "ADHOC")),
        summary=str(data.get("summary", "Ad hoc requirement")),
        description=str(data.get("description", "")),
        acceptance_criteria=criteria,
    )


def adhoc_story(analysis: str) -> StoryDetails:
    return StoryDetails(key="ADHOC", summary="Ad hoc test design", description=analysis)


def gherkin_from_plan(plan: TestPlan) -> str:
    lines = [f"Feature: {plan.strategy}"]
    for case in plan.cases:
        lines.extend(["", f"  Scenario: {case.title}"])
        for precondition in case.preconditions:
            lines.append(f"    Given {precondition}")
        for index, step in enumerate(case.steps):
            keyword = "When" if index == 0 else "And"
            lines.append(f"    {keyword} {step.action}")
            lines.append(f"    Then {step.expected_result}")
    return "\n".join(lines)


def pretty(value: object) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, indent=2, default=str)


def requirement_service(gateway: LLMGateway | None = None) -> RequirementAnalysisService:
    return RequirementAnalysisService(gateway_or_default(gateway))


def design_service(gateway: LLMGateway | None = None) -> TestDesignService:
    return TestDesignService(gateway_or_default(gateway))


def code_service(gateway: LLMGateway | None = None) -> TestCodeGenerationService:
    return TestCodeGenerationService(gateway_or_default(gateway))


def data_service(gateway: LLMGateway | None = None) -> SyntheticDataService:
    return SyntheticDataService(gateway_or_default(gateway))


def security_service(gateway: LLMGateway | None = None) -> SecurityAssessmentService:
    return SecurityAssessmentService(gateway_or_default(gateway))


def performance_service(gateway: LLMGateway | None = None) -> PerformancePlanningService:
    return PerformancePlanningService(gateway_or_default(gateway))


def diagnosis_service(gateway: LLMGateway | None = None) -> FailureDiagnosisService:
    return FailureDiagnosisService(gateway_or_default(gateway))


def reporting_service(gateway: LLMGateway | None = None) -> ReportingService:
    return ReportingService(gateway_or_default(gateway))


def failure_evidence(error_log: str, script_content: str, html_snapshot: str | None) -> FailureEvidence:
    return FailureEvidence(error_log=error_log, test_path="legacy-inline.spec.ts", dom_snapshot_path=html_snapshot, source_revision=script_content)
