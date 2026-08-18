"""Local, permission-filtered retrieval for approved quality knowledge.

This implementation intentionally uses deterministic lexical retrieval so it is easy
to audit and can be replaced by a vector index without changing domain services.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from domain.models import KnowledgeDocument, RetrievedDocument
from infrastructure.artifact_store import ArtifactStore


class KnowledgeStore:
    """Persist approved patterns, schemas, policies, and historical evidence by scope."""

    def __init__(self, root: str | Path = "artifacts"):
        self.store = ArtifactStore(root=root)
        self.path = self.store.root / "quality_knowledge.json"

    def upsert(self, document: KnowledgeDocument) -> None:
        documents = {item.document_id: item for item in self.list_documents()}
        documents[document.document_id] = document
        payload = [item.model_dump(mode="json") for item in documents.values()]
        self.store._atomic_write_json(self.path, {"documents": payload})

    def list_documents(self) -> list[KnowledgeDocument]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [KnowledgeDocument.model_validate(item) for item in raw.get("documents", [])]

    def retrieve(self, query: str, scope: str = "default", limit: int = 5) -> list[RetrievedDocument]:
        query_terms = _terms(query)
        if not query_terms:
            return []
        results: list[RetrievedDocument] = []
        for document in self.list_documents():
            if scope not in document.allowed_scopes:
                continue
            content_terms = _terms(f"{document.title}\n{document.content}\n{' '.join(document.tags)}")
            overlap = sorted(query_terms & content_terms)
            if not overlap:
                continue
            score = len(overlap) / len(query_terms)
            results.append(RetrievedDocument(document=document, score=score, matched_terms=overlap))
        return sorted(results, key=lambda item: (-item.score, item.document.updated_at), reverse=False)[:limit]

    @staticmethod
    def context(documents: list[RetrievedDocument], max_chars: int = 12_000) -> str:
        """Create bounded evidence context; documents remain data, never instructions."""

        chunks: list[str] = []
        remaining = max_chars
        for item in documents:
            content = item.document.content[:remaining]
            chunks.append(
                f"[Evidence: {item.document.document_id} | {item.document.source.source_type}:{item.document.source.source_id}]\n"
                f"{content}"
            )
            remaining -= len(content)
            if remaining <= 0:
                break
        return "\n\n".join(chunks)


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9_]{2,}", value.lower()) if term not in {"the", "and", "for", "with", "from"}}
