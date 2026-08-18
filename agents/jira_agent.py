"""Backward-compatible Jira agent built on typed QUALTAN services."""

from __future__ import annotations

from dataclasses import dataclass

from agents._compat import pretty, requirement_service, story_from_legacy
from infrastructure.llm_gateway import LLMGateway
from integrations.jira import JiraClient, JiraGateway


@dataclass
class JiraAgent:
    gateway: LLMGateway | None = None
    client: JiraGateway | None = None

    def __post_init__(self) -> None:
        self.client = self.client or JiraClient()
        self._requirements = requirement_service(self.gateway)

    def get_story_details(self, issue_key: str) -> dict[str, object]:
        story = self.client.get_story(issue_key)
        return {
            "key": story.key,
            "summary": story.summary,
            "description": story.description,
            "acceptance_criteria": [criterion.text for criterion in story.acceptance_criteria],
            "labels": story.labels,
        }

    def analyze_story(self, story_data: dict[str, object]) -> str:
        return pretty(self._requirements.analyze(story_from_legacy(story_data)))
