"""Atomic local artifact registry for durable, resumable QUALTAN runs."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from core.config import Settings, get_settings
from domain.models import QualityWorkItem
from infrastructure.security import content_hash


class ArtifactStoreError(RuntimeError):
    """Raised when persisted workflow state cannot be safely read or written."""


class ArtifactStore:
    """File-backed registry; replaceable with object storage or a database in deployment."""

    _SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.-]+$")

    def __init__(self, root: str | Path | None = None, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.root = Path(root or self.settings.artifact_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save_work_item(self, work_item: QualityWorkItem) -> Path:
        path = self._work_item_path(work_item.work_item_id)
        payload = work_item.model_dump(mode="json")
        payload["integrity_hash"] = content_hash(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        self._atomic_write_json(path, payload)
        return path

    def load_work_item(self, work_item_id: str) -> QualityWorkItem:
        path = self._work_item_path(work_item_id)
        if not path.exists():
            raise ArtifactStoreError(f"No persisted work item exists for '{work_item_id}'.")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ArtifactStoreError(f"Cannot read persisted work item '{work_item_id}': {error}") from error
        integrity_hash = payload.pop("integrity_hash", None)
        calculated_hash = content_hash(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        if integrity_hash != calculated_hash:
            raise ArtifactStoreError(f"Integrity check failed for persisted work item '{work_item_id}'.")
        return QualityWorkItem.model_validate(payload)

    def save_text_evidence(self, work_item_id: str, name: str, content: str) -> Path:
        directory = self._work_item_path(work_item_id).parent / "evidence"
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = self._safe_identifier(name)
        path = directory / safe_name
        self._atomic_write_text(path, content)
        return path

    def list_work_items(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))

    def _work_item_path(self, work_item_id: str) -> Path:
        return self.root / f"{self._safe_identifier(work_item_id)}.json"

    def _safe_identifier(self, value: str) -> str:
        if not self._SAFE_IDENTIFIER.match(value):
            raise ArtifactStoreError(f"Unsafe artifact identifier: {value!r}")
        return value

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict) -> None:
        ArtifactStore._atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, path)
        except OSError as error:
            raise ArtifactStoreError(f"Cannot atomically write artifact '{path}': {error}") from error
""
