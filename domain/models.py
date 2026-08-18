"""Versioned, typed domain contracts shared across QUALTAN workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DomainModel(BaseModel):
    """Strict base model: unrecognised model output must not leak downstream."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestType(str, Enum):
    WEB = "web"
    API = "api"
    GRAPHQL = "graphql"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class SourceReference(DomainModel):
    source_type: str = Field(description="System that supplied this evidence, e.g. jira or openapi.")
    source_id: str
    location: str | None = Field(default=None, description="URL, file path, or source location.")
    excerpt: str | None = None
    content_hash: str | None = None


class KnowledgeDocument(DomainModel):
    document_id: str
    title: str
    content: str = Field(min_length=1)
    source: SourceReference
    tags: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] = Field(default_factory=lambda: ["default"])
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RetrievedDocument(DomainModel):
    document: KnowledgeDocument
    score: float = Field(ge=0.0)
    matched_terms: list[str] = Field(default_factory=list)


class AcceptanceCriterion(DomainModel):
    criterion_id: str
    text: str = Field(min_length=1)
    source: SourceReference | None = None


class StoryDetails(DomainModel):
    key: str
    summary: str
    description: str = ""
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    source: SourceReference | None = None


class Assumption(DomainModel):
    statement: str
    impact: RiskLevel = RiskLevel.MEDIUM
    requires_confirmation: bool = True


class RiskItem(DomainModel):
    risk_id: str
    title: str
    description: str
    level: RiskLevel
    rationale: str
    related_criteria: list[str] = Field(default_factory=list)
    test_types: list[TestType] = Field(default_factory=list)


class StoryAnalysis(DomainModel):
    story_key: str
    summary: str
    testing_areas: list[str] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    data_requirements: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)


class TestDataEntry(DomainModel):
    key: str
    value: str | int | float | bool | None = None


class TestStep(DomainModel):
    action: str
    expected_result: str
    test_data: list[TestDataEntry] = Field(default_factory=list)


class TestCase(DomainModel):
    case_id: str
    title: str
    objective: str
    test_type: TestType
    priority: RiskLevel = RiskLevel.MEDIUM
    preconditions: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(default_factory=list)
    gherkin: str | None = None
    covered_criteria: list[str] = Field(default_factory=list)
    covered_risks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TestPlan(DomainModel):
    story_key: str
    strategy: str
    cases: list[TestCase] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)


class SyntheticRecord(DomainModel):
    record_id: str
    values: list[TestDataEntry] = Field(default_factory=list)


class SyntheticDataset(DomainModel):
    schema_description: str
    records: list[SyntheticRecord] = Field(default_factory=list)
    edge_cases_covered: list[str] = Field(default_factory=list)
    privacy_notes: list[str] = Field(default_factory=list)


class SecurityScenario(DomainModel):
    scenario_id: str
    title: str
    threat_category: str
    severity: RiskLevel
    steps: list[str] = Field(default_factory=list)
    expected_security_control: str


class SecurityAssessment(DomainModel):
    target_description: str
    scenarios: list[SecurityScenario] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    safe_execution_notes: list[str] = Field(default_factory=list)


class PerformancePlan(DomainModel):
    target_description: str
    locust_script: str
    user_count: int = Field(ge=1)
    spawn_rate: int = Field(ge=1)
    duration: str
    success_criteria: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)


class ExecutiveReport(DomainModel):
    headline: str
    summary: str
    quality_status: str
    key_metrics: list[TestDataEntry] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class GeneratedFile(DomainModel):
    path: str
    language: str
    content: str
    source_case_ids: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    content_hash: str | None = None


class GeneratedTestDraft(DomainModel):
    files: list[GeneratedFile] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)


class GeneratedArtifact(DomainModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    artifact_type: str
    version: str = "1.0"
    files: list[GeneratedFile] = Field(default_factory=list)
    generated_by: str
    model: str | None = None
    prompt_version: str | None = None
    provenance: list[SourceReference] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationResult(DomainModel):
    validator: str
    passed: bool
    summary: str
    details: list[str] = Field(default_factory=list)
    evidence_paths: list[str] = Field(default_factory=list)
    duration_ms: int | None = None


class ExecutionResult(DomainModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: RunStatus
    command: list[str] = Field(default_factory=list)
    target: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    evidence_paths: list[str] = Field(default_factory=list)


class FailureEvidence(DomainModel):
    error_log: str
    test_path: str | None = None
    trace_path: str | None = None
    screenshot_path: str | None = None
    dom_snapshot_path: str | None = None
    accessibility_snapshot_path: str | None = None
    network_log_path: str | None = None
    source_revision: str | None = None
    trace_excerpt: str | None = None
    dom_snapshot_excerpt: str | None = None
    accessibility_snapshot_excerpt: str | None = None
    network_log_excerpt: str | None = None


class PatchProposal(DomainModel):
    path: str
    unified_diff: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    risks: list[str] = Field(default_factory=list)


class FailureDiagnosis(DomainModel):
    category: str
    root_cause_hypotheses: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommended_patch: PatchProposal | None = None
    requires_human_review: bool = True


class ApprovalRequest(DomainModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    action: str
    reason: str
    requested_by: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    payload_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    approved_by: str | None = None
    decision_note: str | None = None


class GenerationMetadata(DomainModel):
    task: str
    model: str
    prompt_version: str
    input_hash: str
    cached: bool = False
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class WorkflowEvent(DomainModel):
    sequence: int
    node: str
    status: RunStatus
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityWorkItem(DomainModel):
    """Persisted source of truth for a QUALTAN workflow execution."""

    work_item_id: str = Field(default_factory=lambda: str(uuid4()))
    story: StoryDetails
    status: RunStatus = RunStatus.PENDING
    analysis: StoryAnalysis | None = None
    test_plan: TestPlan | None = None
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    validations: list[ValidationResult] = Field(default_factory=list)
    executions: list[ExecutionResult] = Field(default_factory=list)
    approvals: list[ApprovalRequest] = Field(default_factory=list)
    events: list[WorkflowEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def record_event(
        self,
        node: str,
        status: RunStatus,
        message: str,
        **metadata: Any,
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            sequence=len(self.events) + 1,
            node=node,
            status=status,
            message=message,
            metadata=metadata,
        )
        self.events.append(event)
        self.updated_at = datetime.now(UTC)
        self.status = status
        return event

    @property
    def requires_approval(self) -> bool:
        return any(request.status == ApprovalStatus.PENDING for request in self.approvals)
""
