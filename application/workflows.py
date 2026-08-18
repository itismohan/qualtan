"""Durable QUALTAN workflow orchestration.

The orchestrator is intentionally deterministic. Model services may reason, but all
state transitions, side effects, approvals, retries, and persistence are explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from application.agents import RequirementAnalysisService, TestCodeGenerationService, TestDesignService
from domain.models import ApprovalRequest, ApprovalStatus, QualityWorkItem, RunStatus, StoryDetails, ValidationResult
from infrastructure.artifact_store import ArtifactStore
from integrations.jira import JiraGateway


class ArtifactValidator(Protocol):
    def validate(self, work_item: QualityWorkItem) -> list[ValidationResult]: ...


class WorkflowError(RuntimeError):
    """Raised when a durable workflow node cannot finish safely."""


@dataclass(frozen=True, slots=True)
class WorkflowDependencies:
    requirements: RequirementAnalysisService
    design: TestDesignService
    code_generation: TestCodeGenerationService
    store: ArtifactStore
    validator: ArtifactValidator | None = None
    jira: JiraGateway | None = None


@dataclass(frozen=True, slots=True)
class RunOptions:
    generate_code: bool = True
    validate: bool = True
    require_generation_approval: bool = False


class QualityWorkflow:
    """Checkpointed work-item state machine for requirement-to-test generation."""

    def __init__(self, dependencies: WorkflowDependencies):
        self.dependencies = dependencies

    def create_from_story(self, story: StoryDetails) -> QualityWorkItem:
        work_item = QualityWorkItem(story=story)
        work_item.record_event("create", RunStatus.PENDING, "Created quality work item.")
        self._save(work_item)
        return work_item

    def create_from_jira(self, issue_key: str) -> QualityWorkItem:
        if not self.dependencies.jira:
            raise WorkflowError("Jira gateway is not configured for create_from_jira.")
        story = self.dependencies.jira.get_story(issue_key)
        return self.create_from_story(story)

    def resume(self, work_item_id: str, options: RunOptions | None = None) -> QualityWorkItem:
        return self.run(self.dependencies.store.load_work_item(work_item_id), options)

    def run(self, work_item: QualityWorkItem, options: RunOptions | None = None) -> QualityWorkItem:
        options = options or RunOptions()
        if work_item.status == RunStatus.SUCCEEDED:
            return work_item
        if any(request.status == ApprovalStatus.REJECTED for request in work_item.approvals):
            work_item.record_event("workflow", RunStatus.CANCELLED, "Workflow remains cancelled because an approval was rejected.")
            self._save(work_item)
            return work_item
        if work_item.requires_approval:
            work_item.record_event("workflow", RunStatus.BLOCKED, "Workflow is waiting for approval.")
            self._save(work_item)
            return work_item

        try:
            self._run_analysis(work_item)
            self._run_design(work_item)
            if options.generate_code:
                self._run_generation(work_item, options)
            if work_item.requires_approval:
                work_item.record_event("workflow", RunStatus.BLOCKED, "Generated artifact awaits approval.")
                self._save(work_item)
                return work_item
            if options.validate and self.dependencies.validator:
                self._run_validation(work_item)
            if any(not result.passed for result in work_item.validations):
                work_item.record_event("workflow", RunStatus.FAILED, "One or more artifact validation gates failed.")
            else:
                work_item.record_event("workflow", RunStatus.SUCCEEDED, "Quality workflow completed successfully.")
            self._save(work_item)
            return work_item
        except Exception as error:
            work_item.record_event("workflow", RunStatus.FAILED, f"Workflow failed safely: {error}")
            self._save(work_item)
            raise WorkflowError(f"Work item '{work_item.work_item_id}' failed: {error}") from error

    def approve(self, work_item_id: str, request_id: str, approver: str, note: str = "") -> QualityWorkItem:
        work_item = self.dependencies.store.load_work_item(work_item_id)
        request = next((item for item in work_item.approvals if item.request_id == request_id), None)
        if request is None:
            raise WorkflowError(f"No approval request '{request_id}' in work item '{work_item_id}'.")
        if request.status != ApprovalStatus.PENDING:
            raise WorkflowError(f"Approval request '{request_id}' has already been decided.")
        index = work_item.approvals.index(request)
        work_item.approvals[index] = request.model_copy(
            update={"status": ApprovalStatus.APPROVED, "approved_by": approver, "decision_note": note}
        )
        work_item.record_event("approval", RunStatus.RUNNING, f"Approved '{request.action}'.", approver=approver)
        self._save(work_item)
        return work_item

    def reject(self, work_item_id: str, request_id: str, approver: str, note: str) -> QualityWorkItem:
        work_item = self.dependencies.store.load_work_item(work_item_id)
        request = next((item for item in work_item.approvals if item.request_id == request_id), None)
        if request is None:
            raise WorkflowError(f"No approval request '{request_id}' in work item '{work_item_id}'.")
        index = work_item.approvals.index(request)
        work_item.approvals[index] = request.model_copy(
            update={"status": ApprovalStatus.REJECTED, "approved_by": approver, "decision_note": note}
        )
        work_item.record_event("approval", RunStatus.CANCELLED, f"Rejected '{request.action}'.", approver=approver)
        self._save(work_item)
        return work_item

    def _run_analysis(self, work_item: QualityWorkItem) -> None:
        if work_item.analysis is not None:
            return
        work_item.record_event("analyze_requirement", RunStatus.RUNNING, "Analyzing requirement and risks.")
        self._save(work_item)
        work_item.analysis = self.dependencies.requirements.analyze(work_item.story)
        work_item.record_event("analyze_requirement", RunStatus.RUNNING, "Requirement analysis completed.")
        self._save(work_item)

    def _run_design(self, work_item: QualityWorkItem) -> None:
        if work_item.test_plan is not None:
            return
        if work_item.analysis is None:
            raise WorkflowError("Cannot design tests without requirement analysis.")
        work_item.record_event("design_tests", RunStatus.RUNNING, "Designing test plan.")
        self._save(work_item)
        work_item.test_plan = self.dependencies.design.design(work_item.story, work_item.analysis)
        work_item.record_event("design_tests", RunStatus.RUNNING, "Test plan completed.")
        self._save(work_item)

    def _run_generation(self, work_item: QualityWorkItem, options: RunOptions) -> None:
        if work_item.artifacts:
            return
        if work_item.test_plan is None:
            raise WorkflowError("Cannot generate test code without a test plan.")
        work_item.record_event("generate_code", RunStatus.RUNNING, "Generating Playwright test artifact.")
        self._save(work_item)
        artifact = self.dependencies.code_generation.generate(work_item.story, work_item.test_plan)
        work_item.artifacts.append(artifact)
        work_item.record_event("generate_code", RunStatus.RUNNING, "Generated test artifact.", artifact_id=artifact.artifact_id)
        if options.require_generation_approval:
            work_item.approvals.append(
                ApprovalRequest(
                    action="generated_artifact.approve",
                    reason="A human must approve generated test code before validation or repository write.",
                    requested_by="quality_workflow",
                )
            )
        self._save(work_item)

    def _run_validation(self, work_item: QualityWorkItem) -> None:
        if work_item.validations:
            return
        assert self.dependencies.validator is not None
        work_item.record_event("validate_artifact", RunStatus.RUNNING, "Running deterministic validation gates.")
        self._save(work_item)
        work_item.validations.extend(self.dependencies.validator.validate(work_item))
        work_item.record_event("validate_artifact", RunStatus.RUNNING, "Validation gates completed.")
        self._save(work_item)

    def _save(self, work_item: QualityWorkItem) -> None:
        self.dependencies.store.save_work_item(work_item)
""
