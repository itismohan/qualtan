"""Data-safety utilities and execution policy enforcement."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from core.config import Settings


class PolicyViolation(PermissionError):
    """Raised when a workflow action conflicts with configured safety policy."""


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    redacted_categories: tuple[str, ...]


class SensitiveDataRedactor:
    """Conservative redaction before logs, persistence, or model requests."""

    _PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("authorization", re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|basic)\s+)[^\s,;]+")),
        ("api_key", re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+")),
        ("secret", re.compile(r"(?i)(client_secret|secret|password)\s*[:=]\s*[^\s,;]+")),
        ("jwt", re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+\b")),
        ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    )

    def redact(self, text: str) -> RedactionResult:
        categories: list[str] = []
        redacted = text
        for category, pattern in self._PATTERNS:
            if pattern.search(redacted):
                categories.append(category)
                if category in {"authorization", "api_key"}:
                    redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
                elif category == "secret":
                    redacted = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)
                else:
                    redacted = pattern.sub(f"[{category.upper()}_REDACTED]", redacted)
        return RedactionResult(text=redacted, redacted_categories=tuple(categories))


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ExecutionPolicy:
    """Central policy for commands, hosts, and side-effecting operations."""

    _DENIED_COMMAND_TOKENS = frozenset({"rm", "sudo", "curl", "wget", "nc", "netcat", "ssh", "scp", "chmod", "chown"})

    def __init__(self, settings: Settings):
        self.settings = settings

    def assert_allowed_host(self, target_url: str) -> None:
        host = urlparse(target_url).hostname
        if not host:
            raise PolicyViolation(f"Execution target is not a valid URL: {target_url}")
        if host.lower() not in self.settings.allowed_execution_hosts:
            allowed = ", ".join(sorted(self.settings.allowed_execution_hosts)) or "<none>"
            raise PolicyViolation(f"Host '{host}' is not allowlisted. Allowed hosts: {allowed}")

    def assert_safe_command(self, command: Iterable[str]) -> None:
        values = list(command)
        if not values:
            raise PolicyViolation("Execution command must not be empty.")
        forbidden = [value for value in values if value.lower() in self._DENIED_COMMAND_TOKENS]
        if forbidden:
            raise PolicyViolation(f"Command contains forbidden token(s): {', '.join(forbidden)}")

    def assert_mutation_allowed(self, action: str, approved: bool) -> None:
        if not self.settings.allow_external_mutations:
            raise PolicyViolation(
                f"'{action}' is disabled. Set QUALTAN_ALLOW_EXTERNAL_MUTATIONS=true after a security review."
            )
        if self.settings.require_approval_for_mutations and not approved:
            raise PolicyViolation(f"'{action}' requires recorded human approval.")

    def requires_execution_approval(self) -> bool:
        return self.settings.require_approval_for_execution
""
