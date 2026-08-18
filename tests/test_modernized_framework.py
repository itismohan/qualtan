from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from application.agents import RequirementAnalysisService, TestCodeGenerationService, TestDesignService
from application.workflows import QualityWorkflow, RunOptions, WorkflowDependencies
from core.config import Settings
from domain.models import (
    AcceptanceCriterion,
    KnowledgeDocument,
    GeneratedFile,
    GeneratedTestDraft,
    RiskItem,
    RiskLevel,
    SourceReference,
    StoryAnalysis,
    StoryDetails,
    TestCase,
    TestPlan,
    TestStep,
    TestType,
)
from infrastructure.artifact_store import ArtifactStore
from infrastructure.llm_gateway import StaticLLMGateway
from infrastructure.evidence import FailureEvidenceCollector
from infrastructure.retrieval import KnowledgeStore
from infrastructure.security import ExecutionPolicy, PolicyViolation, SensitiveDataRedactor
from validators.quality_gates import SchemaIntegrityGate, SourceSafetyGate, TestCoverageGate, ValidationPipeline


def _story() -> StoryDetails:
    source = SourceReference(source_type="jira", source_id="QUAL-1", location="https://jira.example/QUAL-1")
    return StoryDetails(
        key="QUAL-1",
        summary="A user can sign in",
        description="As a user, I can sign in with a registered account.",
        acceptance_criteria=[
            AcceptanceCriterion(criterion_id="AC-1", text="Registered users can sign in.", source=source),
            AcceptanceCriterion(criterion_id="AC-2", text="Invalid credentials show an error.", source=source),
        ],
        source=source,
    )


def _gateway() -> StaticLLMGateway:
    analysis = StoryAnalysis(
        story_key="QUAL-1",
        summary="Sign-in flow with success and error paths.",
        testing_areas=["authentication"],
        risks=[
            RiskItem(
                risk_id="R-1",
                title="Invalid credentials",
                description="The error state may not be visible.",
                level=RiskLevel.HIGH,
                rationale="Authentication feedback is user critical.",
                related_criteria=["AC-2"],
                test_types=[TestType.WEB],
            )
        ],
        data_requirements=["registered and unregistered account"],
    )
    plan = TestPlan(
        story_key="QUAL-1",
        strategy="Verify success and invalid-credential feedback through browser-visible behavior.",
        cases=[
            TestCase(
                case_id="TC-1",
                title="Registered user can sign in",
                objective="Verify a valid user reaches the account area.",
                test_type=TestType.WEB,
                priority=RiskLevel.HIGH,
                steps=[TestStep(action="Submit valid credentials", expected_result="Account heading is visible")],
                covered_criteria=["AC-1"],
                covered_risks=["R-1"],
            ),
            TestCase(
                case_id="TC-2",
                title="Invalid credentials show feedback",
                objective="Verify an invalid user receives an accessible error.",
                test_type=TestType.WEB,
                priority=RiskLevel.HIGH,
                steps=[TestStep(action="Submit invalid credentials", expected_result="Error alert is visible")],
                covered_criteria=["AC-2"],
                covered_risks=["R-1"],
            ),
        ],
    )
    test_source = """import { test, expect } from '@playwright/test';

test('registered user signs in', async ({ page }) => {
  await page.goto('/sign-in');
  await page.getByLabel('Email').fill('registered@example.test');
  await page.getByLabel('Password').fill('not-a-real-secret');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Account' })).toBeVisible();
});
"""
    draft = GeneratedTestDraft(
        files=[GeneratedFile(path="sign-in.spec.ts", language="typescript", content=test_source, source_case_ids=["TC-1", "TC-2"])],
    )
    return StaticLLMGateway({"requirement_analysis": analysis, "test_design": plan, "test_code_generation": draft})


def _workflow(tmp_path: Path) -> QualityWorkflow:
    gateway = _gateway()
    validator = ValidationPipeline([SchemaIntegrityGate(), TestCoverageGate(), SourceSafetyGate()])
    dependencies = WorkflowDependencies(
        requirements=RequirementAnalysisService(gateway),
        design=TestDesignService(gateway),
        code_generation=TestCodeGenerationService(gateway),
        store=ArtifactStore(root=tmp_path / "artifacts"),
        validator=validator,
    )
    return QualityWorkflow(dependencies)


def test_workflow_is_durable_and_validates_generated_code(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    work_item = workflow.create_from_story(_story())

    completed = workflow.run(work_item)

    assert completed.status.value == "succeeded"
    assert completed.analysis is not None
    assert completed.test_plan is not None
    assert completed.artifacts[0].files[0].path == "generated-tests/sign-in.spec.ts"
    assert all(result.passed for result in completed.validations)
    restored = workflow.dependencies.store.load_work_item(completed.work_item_id)
    assert restored.status == completed.status
    assert len(restored.events) >= 7


def test_workflow_requires_explicit_approval_before_validation(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    work_item = workflow.create_from_story(_story())

    blocked = workflow.run(work_item, RunOptions(require_generation_approval=True))

    assert blocked.status.value == "blocked"
    request = blocked.approvals[0]
    approved = workflow.approve(blocked.work_item_id, request.request_id, "qa-lead", "Reviewed generated test intent.")
    completed = workflow.run(approved)
    assert completed.status.value == "succeeded"


def test_redactor_and_execution_policy_protect_sensitive_data_and_targets() -> None:
    result = SensitiveDataRedactor().redact("Authorization: Bearer top-secret-token alice@example.com")
    assert "top-secret-token" not in result.text
    assert "alice@example.com" not in result.text

    settings = replace(Settings.from_env(), allowed_execution_hosts=frozenset({"staging.example.test"}))
    policy = ExecutionPolicy(settings)
    policy.assert_allowed_host("https://staging.example.test/sign-in")
    with pytest.raises(PolicyViolation):
        policy.assert_allowed_host("https://production.example.test/sign-in")
    with pytest.raises(PolicyViolation):
        policy.assert_safe_command(["rm", "-rf", "generated-tests"])


def test_knowledge_retrieval_is_scope_filtered_and_failure_evidence_is_redacted(tmp_path: Path) -> None:
    source = SourceReference(source_type="repository", source_id="POM-1", location="docs/pom.md")
    knowledge = KnowledgeStore(root=tmp_path / "artifacts")
    knowledge.upsert(
        KnowledgeDocument(
            document_id="POM-1",
            title="Stable Playwright locators",
            content="Use getByRole and accessible labels for sign-in forms.",
            source=source,
            allowed_scopes=["default"],
        )
    )
    knowledge.upsert(
        KnowledgeDocument(
            document_id="PRIVATE-1",
            title="Private secret convention",
            content="This document must not be retrieved by the default project.",
            source=source,
            allowed_scopes=["private"],
        )
    )
    results = knowledge.retrieve("sign in accessible role locator", scope="default")
    assert [item.document.document_id for item in results] == ["POM-1"]

    dom_path = tmp_path / "snapshot.html"
    dom_path.write_text("<input value='api_key=super-secret'>", encoding="utf-8")
    collected = FailureEvidenceCollector().collect(
        error_log="Authorization: Bearer secret-token",
        script_content="test('sign in', () => {})",
        dom_snapshot_path=str(dom_path),
    )
    assert "secret-token" not in collected.evidence.error_log
    assert "super-secret" not in (collected.evidence.dom_snapshot_excerpt or "")
