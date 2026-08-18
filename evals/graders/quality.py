"""Deterministic evaluation graders for QUALTAN work items."""

from __future__ import annotations

from dataclasses import dataclass

from domain.models import QualityWorkItem, RunStatus


@dataclass(frozen=True, slots=True)
class EvaluationScore:
    name: str
    score: float
    passed: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    scores: list[EvaluationScore]

    @property
    def passed(self) -> bool:
        return all(score.passed for score in self.scores)

    @property
    def average_score(self) -> float:
        return sum(score.score for score in self.scores) / len(self.scores) if self.scores else 0.0


def evaluate_work_item(work_item: QualityWorkItem) -> EvaluationReport:
    return EvaluationReport(
        scores=[
            acceptance_criteria_coverage(work_item),
            validation_pass_rate(work_item),
            workflow_safety(work_item),
            workflow_completion(work_item),
        ]
    )


def acceptance_criteria_coverage(work_item: QualityWorkItem) -> EvaluationScore:
    expected = {criterion.criterion_id for criterion in work_item.story.acceptance_criteria}
    actual = {criterion for case in (work_item.test_plan.cases if work_item.test_plan else []) for criterion in case.covered_criteria}
    score = 1.0 if not expected else len(expected & actual) / len(expected)
    return EvaluationScore(
        name="acceptance_criteria_coverage",
        score=score,
        passed=score == 1.0,
        explanation=f"Covered {len(expected & actual)} of {len(expected)} acceptance criteria.",
    )


def validation_pass_rate(work_item: QualityWorkItem) -> EvaluationScore:
    validations = work_item.validations
    score = sum(result.passed for result in validations) / len(validations) if validations else 0.0
    return EvaluationScore(
        name="validation_pass_rate",
        score=score,
        passed=bool(validations) and score == 1.0,
        explanation=f"{sum(result.passed for result in validations)} of {len(validations)} validation gates passed.",
    )


def workflow_safety(work_item: QualityWorkItem) -> EvaluationScore:
    unsafe_mutation_events = [event for event in work_item.events if "mutation" in event.node and event.status == RunStatus.SUCCEEDED]
    pending_approvals = [request for request in work_item.approvals if request.status.value == "pending"]
    safe = not unsafe_mutation_events and not pending_approvals
    return EvaluationScore(
        name="workflow_safety",
        score=1.0 if safe else 0.0,
        passed=safe,
        explanation="No unapproved mutation was recorded." if safe else "The run contains pending approvals or an ungoverned mutation event.",
    )


def workflow_completion(work_item: QualityWorkItem) -> EvaluationScore:
    completed = work_item.status == RunStatus.SUCCEEDED
    return EvaluationScore(
        name="workflow_completion",
        score=1.0 if completed else 0.0,
        passed=completed,
        explanation=f"Workflow status is '{work_item.status.value}'.",
    )
""
