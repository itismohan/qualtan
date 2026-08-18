"""Structured local telemetry with no sensitive prompt or completion persistence."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    event_type: str
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class TelemetrySink(Protocol):
    def emit(self, event: TelemetryEvent) -> None: ...


class JsonlTelemetrySink:
    """Append-only structured telemetry; stores hashes and metrics rather than source content."""

    def __init__(self, path: str | Path = "artifacts/telemetry.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def emit(self, event: TelemetryEvent) -> None:
        payload = {"event_type": event.event_type, "created_at": event.created_at.isoformat(), "attributes": event.attributes}
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


class NullTelemetrySink:
    def emit(self, event: TelemetryEvent) -> None:
        return None
