"""Configuration and runtime policy for QUALTAN.

Configuration is intentionally explicit: integrations are optional until a workflow
requires them, while security and model defaults are always available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(RuntimeError):
    """Raised when a requested capability lacks mandatory configuration."""


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    artifact_dir: str
    openai_api_key: str | None
    openai_base_url: str | None
    default_model: str
    reasoning_model: str
    model_timeout_seconds: float
    model_max_retries: int
    max_model_cost_usd: float
    jira_url: str | None
    jira_user: str | None
    jira_token: str | None
    jira_acceptance_criteria_field: str
    xray_client_id: str | None
    xray_client_secret: str | None
    xray_base_url: str
    base_url: str
    api_base_url: str
    graphql_endpoint: str | None
    allowed_execution_hosts: frozenset[str] = field(default_factory=frozenset)
    allow_external_mutations: bool = False
    require_approval_for_execution: bool = True
    require_approval_for_mutations: bool = True
    redact_sensitive_data: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.getenv("BASE_URL", "http://localhost:3000")
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:3000/api")
        configured_hosts = _csv("QUALTAN_ALLOWED_EXECUTION_HOSTS")
        default_hosts = {
            host
            for host in (_host(base_url), _host(api_base_url), _host(os.getenv("GRAPHQL_ENDPOINT")))
            if host
        }
        return cls(
            environment=os.getenv("QUALTAN_ENV", "development"),
            artifact_dir=os.getenv("QUALTAN_ARTIFACT_DIR", "artifacts"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE"),
            default_model=os.getenv("QUALTAN_DEFAULT_MODEL", "gpt-5-mini"),
            reasoning_model=os.getenv("QUALTAN_REASONING_MODEL", "gpt-5"),
            model_timeout_seconds=float(os.getenv("QUALTAN_MODEL_TIMEOUT_SECONDS", "60")),
            model_max_retries=int(os.getenv("QUALTAN_MODEL_MAX_RETRIES", "2")),
            max_model_cost_usd=float(os.getenv("QUALTAN_MAX_MODEL_COST_USD", "2.00")),
            jira_url=os.getenv("JIRA_URL"),
            jira_user=os.getenv("JIRA_USER"),
            jira_token=os.getenv("JIRA_TOKEN"),
            jira_acceptance_criteria_field=os.getenv("JIRA_ACCEPTANCE_CRITERIA_FIELD", "customfield_10100"),
            xray_client_id=os.getenv("XRAY_CLIENT_ID"),
            xray_client_secret=os.getenv("XRAY_CLIENT_SECRET"),
            xray_base_url=os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app/api/v2"),
            base_url=base_url,
            api_base_url=api_base_url,
            graphql_endpoint=os.getenv("GRAPHQL_ENDPOINT"),
            allowed_execution_hosts=frozenset(configured_hosts or default_hosts),
            allow_external_mutations=_bool("QUALTAN_ALLOW_EXTERNAL_MUTATIONS", False),
            require_approval_for_execution=_bool("QUALTAN_REQUIRE_APPROVAL_FOR_EXECUTION", True),
            require_approval_for_mutations=_bool("QUALTAN_REQUIRE_APPROVAL_FOR_MUTATIONS", True),
            redact_sensitive_data=_bool("QUALTAN_REDACT_SENSITIVE_DATA", True),
        )

    def validate(self, capability: str = "core") -> None:
        required: dict[str, tuple[tuple[str, str | None], ...]] = {
            "llm": (("OPENAI_API_KEY", self.openai_api_key),),
            "jira": (("JIRA_URL", self.jira_url), ("JIRA_USER", self.jira_user), ("JIRA_TOKEN", self.jira_token)),
            "xray": (("XRAY_CLIENT_ID", self.xray_client_id), ("XRAY_CLIENT_SECRET", self.xray_client_secret)),
            "execution": (("QUALTAN_ALLOWED_EXECUTION_HOSTS or a configured target URL", ",".join(self.allowed_execution_hosts)),),
            "core": (),
        }
        if capability not in required:
            raise ConfigurationError(f"Unknown configuration capability: {capability}")
        missing = [name for name, value in required[capability] if not value]
        if missing:
            raise ConfigurationError(
                f"Cannot use '{capability}' capability. Missing: {', '.join(missing)}. "
                "Set the variables in .env; do not hard-code secrets."
            )


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str) -> set[str]:
    return {item.strip().lower() for item in os.getenv(name, "").split(",") if item.strip()}


def _host(url: str | None) -> str | None:
    if not url:
        return None
    return urlparse(url).hostname


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reset_settings_cache() -> None:
    """Support deterministic tests that change environment variables."""

    get_settings.cache_clear()


class Config:
    """Compatibility facade for legacy callers while avoiding import-time validation."""

    @classmethod
    def validate(cls, capability: str = "core") -> None:
        get_settings().validate(capability)

    @classmethod
    def settings(cls) -> Settings:
        return get_settings()
""
