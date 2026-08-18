"""Backward-compatible test designer backed by structured planning services."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import adhoc_story, design_service, gherkin_from_plan, pretty, requirement_service
from infrastructure.llm_gateway import LLMGateway


@dataclass
class DesignerAgent:
    gateway: LLMGateway | None = None

    def __post_init__(self) -> None:
        self._requirements = requirement_service(self.gateway)
        self._design = design_service(self.gateway)

    def generate_gherkin(self, story_analysis: str) -> str:
        story = adhoc_story(story_analysis)
        analysis = self._requirements.analyze(story)
        return gherkin_from_plan(self._design.design(story, analysis))

    def generate_test_cases(self, gherkin_content: str) -> str:
        story = adhoc_story(gherkin_content)
        analysis = self._requirements.analyze(story)
        return pretty(self._design.design(story, analysis))
