from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from click.testing import CliRunner

from application.workflows import RunOptions, WorkflowError
from core.config import Settings
from cli.main import cli
from domain.models import (
    ExecutionResult,
    GeneratedArtifact,
    GeneratedFile,
    QualityWorkItem,
    RunStatus,
    TestCase,
    TestPlan,
    TestStep,
    TestType,
)
from evals.graders.quality import evaluate_work_item
from infrastructure.artifact_store import ArtifactStore, ArtifactStoreError
from infrastructure.security import ExecutionPolicy, PolicyViolation
from infrastructure.telemetry import JsonlTelemetrySink, TelemetryEvent
from infrastructure.test_execution import TestExecutionService
from integrations.xray import InMemoryXRayClient
from tests.test_modernized_framework import _story, _workflow
from validators.quality_gates import SourceSafetyGate, TestCoverageGate


def _valid_plan() -> TestPlan:
    return TestPlan(
        story_key="QUAL-1",
        strategy="Valid test plan for integration mapping.",
        cases=[
            TestCase(
                case_id="TC-1",
                title="Sign-in succeeds",
                objective="Verify the user-visible account state.",
                test_type=TestType.WEB,
                steps=[TestStep(action="Submit valid credentials", expected_result="Account is visible")],
                covered_criteria=["AC-1"],
            ),
            TestCase(
                case_id="TC-2",
                title="Sign-in failure is visible",
                objective="Verify accessible failure feedback.",
                test_type=TestType.WEB,
                steps=[TestStep(action="Submit invalid credentials", expected_result="Error is visible")],
                covered_criteria=["AC-2"],
            ),
        ],
    )


def test_artifact_store_detects_tampering(tmp_path: Path) -> None:
    store = ArtifactStore(root=tmp_path / "artifacts")
    work_item = QualityWorkItem(story=_story())
    stored_path = store.save_work_item(work_item)

    payload = json.loads(stored_path.read_text(encoding="utf-8"))
    payload["story"]["summary"] = "Tampered after persistence"
    stored_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ArtifactStoreError, match="Integrity check failed"):
        store.load_work_item(work_item.work_item_id)


def test_rejected_approval_cancels_resume_and_preserves_generated_artifact(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    blocked = workflow.run(workflow.create_from_story(_story()), RunOptions(require_generation_approval=True))
    request = blocked.approvals[0]

    rejected = workflow.reject(blocked.work_item_id, request.request_id, "qa-lead", "Selectors need review.")
    resumed = workflow.run(rejected)

    assert resumed.status == RunStatus.CANCELLED
    assert len(resumed.artifacts) == 1
    assert not resumed.validations
    assert "rejected" in resumed.events[-1].message.lower()


def test_duplicate_approval_decision_is_rejected(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    blocked = workflow.run(workflow.create_from_story(_story()), RunOptions(require_generation_approval=True))
    request = blocked.approvals[0]
    workflow.approve(blocked.work_item_id, request.request_id, "qa-lead")

    with pytest.raises(WorkflowError, match="already been decided"):
        workflow.approve(blocked.work_item_id, request.request_id, "qa-lead")


def test_validation_gates_reject_unsafe_source_and_coverage_gap() -> None:
    unsafe = GeneratedArtifact(
        artifact_type="playwright_test_suite",
        generated_by="test",
        files=[
            GeneratedFile(
                path="generated-tests/unsafe.spec.ts",
                language="typescript",
                content="import { test } from '@playwright/test'; test('bad', async ({ page }) => { await page.waitForTimeout(500); });",
            )
        ],
    )
    work_item = QualityWorkItem(story=_story(), test_plan=_valid_plan(), artifacts=[unsafe])

    source_result = SourceSafetyGate().validate(work_item)
    assert not source_result.passed
    assert any("fixed sleep" in detail for detail in source_result.details)
    assert any("explicit assertion" in detail for detail in source_result.details)

    incomplete_plan = _valid_plan().model_copy(update={"cases": [_valid_plan().cases[0]]})
    incomplete = QualityWorkItem(story=_story(), test_plan=incomplete_plan)
    coverage_result = TestCoverageGate().validate(incomplete)
    assert not coverage_result.passed
    assert any("AC-2" in detail for detail in coverage_result.details)


def test_xray_mapping_requires_approval_for_mutation_and_maps_approved_plan() -> None:
    client = InMemoryXRayClient()
    plan = _valid_plan()

    with pytest.raises(Exception, match="requires approval"):
        client.import_test_plan(plan, approved=False)

    result = client.import_test_plan(plan, approved=True)
    assert result == {"imported": 2, "mode": "in_memory"}
    assert client.imported_plans[0]["tests"][0]["summary"] == "Sign-in succeeds"


def test_execution_policy_blocks_unapproved_execution_even_on_allowlisted_host(tmp_path: Path) -> None:
    base_settings = Settings.from_env()
    settings = replace(
        base_settings,
        allowed_execution_hosts=frozenset({"staging.example.test"}),
        require_approval_for_execution=True,
    )
    policy = ExecutionPolicy(settings)
    runner = TestExecutionService(project_root=tmp_path, settings=settings)

    with pytest.raises(PolicyViolation, match="requires recorded human approval"):
        runner.execute(["npm", "test"], "https://staging.example.test/health", approved=False)

    policy.assert_allowed_host("https://staging.example.test/health")
    policy.assert_safe_command(["npm", "test"])


def test_jsonl_telemetry_is_structured_and_does_not_require_prompt_storage(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.jsonl"
    sink = JsonlTelemetrySink(path)
    sink.emit(TelemetryEvent(event_type="llm.generation", attributes={"task": "test_design", "latency_ms": 42}))

    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "llm.generation"
    assert payload["attributes"] == {"task": "test_design", "latency_ms": 42}
    assert "prompt" not in payload
    assert "completion" not in payload


def test_cli_knowledge_add_and_list_are_persisted_by_project_scope(tmp_path: Path) -> None:
    knowledge_file = tmp_path / "locator-standard.md"
    knowledge_file.write_text("Use getByRole and labels for user-visible behavior.", encoding="utf-8")
    runner = CliRunner()

    add = runner.invoke(
        cli,
        [
            "knowledge-add",
            "--document-id",
            "locator-standard",
            "--title",
            "Locator standard",
            "--file",
            str(knowledge_file),
            "--scope",
            "default",
            "--project-root",
            str(tmp_path),
        ],
    )
    listing = runner.invoke(cli, ["knowledge-list", "--project-root", str(tmp_path)])

    assert add.exit_code == 0, add.output
    assert listing.exit_code == 0, listing.output
    assert "locator-standard" in listing.output


def test_evaluation_reports_failure_for_incomplete_unsuccessful_work_item() -> None:
    work_item = QualityWorkItem(story=_story(), status=RunStatus.FAILED, test_plan=_valid_plan())

    report = evaluate_work_item(work_item)
    scores = {score.name: score for score in report.scores}
    assert scores["acceptance_criteria_coverage"].passed
    assert not scores["validation_pass_rate"].passed
    assert not scores["workflow_completion"].passed
    assert not report.passed
