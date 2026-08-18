"""Typed, auditable Jira boundary. Reasoning agents receive domain data, not SDK objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.config import Settings, get_settings
from domain.models import AcceptanceCriterion, SourceReference, StoryDetails


class IntegrationError(RuntimeError):
    """Normalised integration failure that workflow retry policy can handle."""


class JiraGateway(Protocol):
    def get_story(self, issue_key: str) -> StoryDetails: ...


@dataclass
class JiraClient:
    settings: Settings | None = None

    def __post_init__(self) -> None:
        self.settings = self.settings or get_settings()
        self._client = None

    def get_story(self, issue_key: str) -> StoryDetails:
        assert self.settings is not None
        self.settings.validate("jira")
        try:
            issue = self._get_client().issue(issue_key)
        except Exception as error:
            raise IntegrationError(f"Unable to retrieve Jira issue '{issue_key}': {error}") from error

        description = _as_text(getattr(issue.fields, "description", ""))
        raw_criteria = getattr(issue.fields, self.settings.jira_acceptance_criteria_field, None)
        criteria = _criteria_from_value(raw_criteria, issue.key)
        source = SourceReference(
            source_type="jira",
            source_id=issue.key,
            location=f"{self.settings.jira_url}/browse/{issue.key}",
            excerpt=str(getattr(issue.fields, "summary", "")),
        )
        return StoryDetails(
            key=issue.key,
            summary=str(getattr(issue.fields, "summary", "")),
            description=description,
            acceptance_criteria=criteria,
            labels=list(getattr(issue.fields, "labels", []) or []),
            source=source,
        )

    def _get_client(self):
        if self._client is None:
            try:
                from jira import JIRA
            except ImportError as error:
                raise IntegrationError("Install the 'jira' package to use the Jira integration.") from error
            assert self.settings is not None
            self._client = JIRA(
                server=self.settings.jira_url,
                basic_auth=(self.settings.jira_user, self.settings.jira_token),
                options={"rest_api_version": "3"},
            )
        return self._client


@dataclass
class InMemoryJiraClient:
    stories: dict[str, StoryDetails]

    def get_story(self, issue_key: str) -> StoryDetails:
        try:
            return self.stories[issue_key]
        except KeyError as error:
            raise IntegrationError(f"No fixture story exists for '{issue_key}'.") from error


def _criteria_from_value(value: object, issue_key: str) -> list[AcceptanceCriterion]:
    if not value:
        return []
    text = _as_text(value)
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    source = SourceReference(source_type="jira", source_id=issue_key, location="acceptance_criteria")
    return [AcceptanceCriterion(criterion_id=f"AC-{index + 1}", text=line, source=source) for index, line in enumerate(lines)]


def _as_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_as_text(item) for item in value)
    if isinstance(value, dict):
        text = value.get("text")
        content = value.get("content", [])
        return "\n".join(part for part in [str(text) if text else "", _as_text(content)] if part)
    return str(value)
""
