"""Composition root for production and CLI QUALTAN workflows."""

from __future__ import annotations

from pathlib import Path

from application.agents import RequirementAnalysisService, TestCodeGenerationService, TestDesignService
from application.workflows import QualityWorkflow, WorkflowDependencies
from infrastructure.artifact_store import ArtifactStore
from infrastructure.llm_gateway import OpenAIModelGateway
from infrastructure.retrieval import KnowledgeStore
from infrastructure.telemetry import JsonlTelemetrySink
from integrations.jira import JiraClient
from validators.quality_gates import default_validation_pipeline


def build_quality_workflow(project_root: str | Path = ".") -> QualityWorkflow:
    root = Path(project_root).resolve()
    gateway = OpenAIModelGateway(telemetry=JsonlTelemetrySink(root / "artifacts" / "telemetry.jsonl"))
    return QualityWorkflow(
        WorkflowDependencies(
            requirements=RequirementAnalysisService(gateway),
            design=TestDesignService(gateway, knowledge=KnowledgeStore(root=root / "artifacts")),
            code_generation=TestCodeGenerationService(gateway),
            store=ArtifactStore(root=root / "artifacts"),
            validator=default_validation_pipeline(root),
            jira=JiraClient(),
        )
    )
