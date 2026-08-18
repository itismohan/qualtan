"""Backward-compatible script generator backed by typed test-code generation."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import adhoc_story, code_service, design_service, requirement_service
from domain.models import TestType
from infrastructure.llm_gateway import LLMGateway


@dataclass
class ScriptGenAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._requirements = requirement_service(self.gateway)
        self._design = design_service(self.gateway)
        self._code = code_service(self.gateway)

    def generate_playwright_script(self, gherkin_scenario: str, test_type: str = "web") -> str:
        story = adhoc_story(gherkin_scenario)
        analysis = self._requirements.analyze(story)
        plan = self._design.design(story, analysis)
        selected_type = TestType(test_type) if test_type in {item.value for item in TestType} else TestType.WEB
        plan = plan.model_copy(update={"cases": [case.model_copy(update={"test_type": selected_type}) for case in plan.cases]})
        artifact = self._code.generate(story, plan)
        return "\n\n".join(file.content for file in artifact.files)

    def generate_api_client(self, swagger_or_schema: str) -> str:
        return self.generate_playwright_script(swagger_or_schema, test_type="api")
