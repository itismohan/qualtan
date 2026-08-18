"""Bounded evidence collection for safe, multimodal failure diagnosis."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path

from domain.models import FailureEvidence
from infrastructure.security import SensitiveDataRedactor


@dataclass(frozen=True, slots=True)
class CollectedFailureEvidence:
    evidence: FailureEvidence
    image_data_urls: tuple[str, ...] = ()


class FailureEvidenceCollector:
    """Reads only approved local evidence paths and redacts textual evidence."""

    def __init__(self, redactor: SensitiveDataRedactor | None = None, max_text_chars: int = 16_000, max_image_bytes: int = 4_000_000):
        self.redactor = redactor or SensitiveDataRedactor()
        self.max_text_chars = max_text_chars
        self.max_image_bytes = max_image_bytes

    def collect(
        self,
        *,
        error_log: str,
        script_content: str,
        trace_path: str | None = None,
        screenshot_path: str | None = None,
        dom_snapshot_path: str | None = None,
        accessibility_snapshot_path: str | None = None,
        network_log_path: str | None = None,
    ) -> CollectedFailureEvidence:
        evidence = FailureEvidence(
            error_log=self._redact(error_log),
            test_path="legacy-inline.spec.ts",
            trace_path=trace_path,
            screenshot_path=screenshot_path,
            dom_snapshot_path=dom_snapshot_path,
            accessibility_snapshot_path=accessibility_snapshot_path,
            network_log_path=network_log_path,
            source_revision=self._redact(script_content),
            trace_excerpt=self._read_text(trace_path),
            dom_snapshot_excerpt=self._read_text(dom_snapshot_path),
            accessibility_snapshot_excerpt=self._read_text(accessibility_snapshot_path),
            network_log_excerpt=self._read_text(network_log_path),
        )
        image = self._read_image(screenshot_path)
        return CollectedFailureEvidence(evidence=evidence, image_data_urls=(image,) if image else ())

    def _read_text(self, value: str | None) -> str | None:
        if not value:
            return None
        path = Path(value)
        if not path.is_file():
            return None
        try:
            return self._redact(path.read_text(encoding="utf-8", errors="replace")[: self.max_text_chars])
        except OSError:
            return None

    def _read_image(self, value: str | None) -> str | None:
        if not value:
            return None
        path = Path(value)
        if not path.is_file() or path.stat().st_size > self.max_image_bytes:
            return None
        mime_type, _ = mimetypes.guess_type(path.name)
        if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
            return None
        try:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError:
            return None
        return f"data:{mime_type};base64,{encoded}"

    def _redact(self, value: str) -> str:
        return self.redactor.redact(value).text
