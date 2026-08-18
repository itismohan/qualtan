"""QUALTAN command-line interface for governed AI quality workflows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import click
try:
    from rich.console import Console
except ImportError:  # allow basic CLI help and diagnostics before optional formatting is installed
    class Console:  # type: ignore[no-redef]
        def print(self, value: object) -> None:
            print(value)

        def print_json(self, *, data: object) -> None:
            print(json.dumps(data, indent=2, default=str))

from agents.data_agent import DataAgent
from agents.designer_agent import DesignerAgent
from agents.jira_agent import JiraAgent
from agents.performance_agent import PerformanceAgent
from agents.reporting_agent import ReportingAgent
from agents.script_gen_agent import ScriptGenAgent
from agents.security_agent import SecurityAgent
from agents.xray_agent import XRayAgent
from application.factory import build_quality_workflow
from application.workflows import RunOptions, WorkflowError
from core.config import ConfigurationError
from domain.models import KnowledgeDocument, SourceReference
from evals.graders.quality import evaluate_work_item
from infrastructure.retrieval import KnowledgeStore

console = Console()


@click.group()
def cli() -> None:
    """QUALTAN: governed, evidence-based AI quality engineering."""


@cli.command(name="jira-agent")
@click.option("--story", required=True, help="Jira story key.")
def jira_cmd(story: str) -> None:
    agent = JiraAgent()
    data = agent.get_story_details(story)
    console.print_json(data=json.loads(agent.analyze_story(data)))


@cli.command(name="testcase-agent")
@click.option("--analysis", required=True, help="Requirement or story analysis text.")
def testcase_cmd(analysis: str) -> None:
    agent = DesignerAgent()
    gherkin = agent.generate_gherkin(analysis)
    cases = agent.generate_test_cases(gherkin)
    console.print(f"[bold green]Generated Gherkin:[/bold green]\n{gherkin}")
    console.print_json(data=json.loads(cases))


@cli.command(name="script-agent")
@click.option("--gherkin", required=True, help="Gherkin scenario or test intent.")
@click.option("--type", "test_type", default="web", show_default=True, help="Test type: web, api, or graphql.")
def script_cmd(gherkin: str, test_type: str) -> None:
    script = ScriptGenAgent().generate_playwright_script(gherkin, test_type)
    console.print(f"[bold green]Generated {test_type} script proposal:[/bold green]\n{script}")


@cli.command(name="data-agent")
@click.option("--schema", required=True, help="Synthetic-data schema or description.")
@click.option("--count", default=5, show_default=True, type=click.IntRange(1, 1000))
def data_cmd(schema: str, count: int) -> None:
    console.print_json(data=json.loads(DataAgent().generate_test_data(schema, count)))


@cli.command(name="xray-agent")
@click.option("--cases", required=True, help="Typed TestPlan JSON or legacy test-case text.")
def xray_cmd(cases: str) -> None:
    console.print_json(data=json.loads(XRayAgent().map_test_cases_to_xray(cases)))


@cli.command(name="perf-agent")
@click.option("--spec", required=True, help="Approved API specification.")
def perf_cmd(spec: str) -> None:
    console.print(PerformanceAgent().generate_locust_script(spec))


@cli.command(name="security-agent")
@click.option("--spec", required=True, help="Approved API specification.")
def security_cmd(spec: str) -> None:
    console.print_json(data=json.loads(SecurityAgent().generate_security_scenarios(spec)))


@cli.command(name="report-agent")
@click.option("--results", required=True, help="Raw, redacted test results.")
def report_cmd(results: str) -> None:
    console.print_json(data=json.loads(ReportingAgent().generate_executive_summary(results)))


@cli.command(name="knowledge-add")
@click.option("--document-id", required=True, help="Stable identifier for the approved knowledge document.")
@click.option("--title", required=True, help="Human-readable knowledge title.")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--scope", default="default", show_default=True, help="Project scope allowed to retrieve this document.")
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def knowledge_add(document_id: str, title: str, file_path: Path, scope: str, project_root: Path) -> None:
    """Add an explicitly approved document to the scope-filtered quality knowledge store."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    document = KnowledgeDocument(
        document_id=document_id,
        title=title,
        content=content,
        source=SourceReference(source_type="operator_file", source_id=document_id, location=str(file_path.resolve())),
        allowed_scopes=[scope],
    )
    KnowledgeStore(root=project_root / "artifacts").upsert(document)
    console.print_json(data={"stored": document_id, "scope": scope, "chars": len(content)})


@cli.command(name="knowledge-list")
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def knowledge_list(project_root: Path) -> None:
    """List approved knowledge documents available to the workflow."""
    documents = KnowledgeStore(root=project_root / "artifacts").list_documents()
    console.print_json(data={"documents": [item.model_dump(mode="json", exclude={"content"}) for item in documents]})


@cli.command(name="full-cycle")
@click.option("--story", required=True, help="Jira story key.")
@click.option("--approve-generated", is_flag=True, help="Record explicit approval to validate generated artifacts in this run.")
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def full_cycle(story: str, approve_generated: bool, project_root: Path) -> None:
    """Run the persisted requirement-to-validated-artifact workflow."""
    try:
        workflow = build_quality_workflow(project_root)
        work_item = workflow.create_from_jira(story)
        result = workflow.run(work_item, RunOptions(require_generation_approval=not approve_generated))
    except (ConfigurationError, WorkflowError) as error:
        raise click.ClickException(str(error)) from error
    _print_work_item(result)


@cli.command(name="workflow-resume")
@click.option("--work-item", "work_item_id", required=True, help="Persisted work-item ID.")
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def workflow_resume(work_item_id: str, project_root: Path) -> None:
    """Resume a persisted workflow after resolving its approval state."""
    try:
        result = build_quality_workflow(project_root).resume(work_item_id)
    except (ConfigurationError, WorkflowError) as error:
        raise click.ClickException(str(error)) from error
    _print_work_item(result)


@cli.command(name="workflow-approve")
@click.option("--work-item", "work_item_id", required=True)
@click.option("--request", "request_id", required=True, help="Approval request ID from workflow output.")
@click.option("--approver", required=True, help="Human approver identity.")
@click.option("--note", default="", help="Approval evidence or review note.")
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def workflow_approve(work_item_id: str, request_id: str, approver: str, note: str, project_root: Path) -> None:
    """Record a human approval; this command does not execute or mutate external systems."""
    try:
        result = build_quality_workflow(project_root).approve(work_item_id, request_id, approver, note)
    except (ConfigurationError, WorkflowError) as error:
        raise click.ClickException(str(error)) from error
    _print_work_item(result)


@cli.command(name="workflow-eval")
@click.option("--work-item", "work_item_id", required=True)
@click.option("--project-root", default=".", type=click.Path(path_type=Path), show_default=True)
def workflow_eval(work_item_id: str, project_root: Path) -> None:
    """Evaluate a persisted work item using deterministic quality graders."""
    work_item = build_quality_workflow(project_root).dependencies.store.load_work_item(work_item_id)
    report = evaluate_work_item(work_item)
    console.print_json(data={"passed": report.passed, "average_score": report.average_score, "scores": [score.__dict__ if hasattr(score, "__dict__") else {"name": score.name, "score": score.score, "passed": score.passed, "explanation": score.explanation} for score in report.scores]})


def _print_work_item(work_item) -> None:
    console.print_json(
        data={
            "work_item_id": work_item.work_item_id,
            "status": work_item.status.value,
            "approval_requests": [request.model_dump(mode="json") for request in work_item.approvals],
            "validation_results": [result.model_dump(mode="json") for result in work_item.validations],
            "events": [event.model_dump(mode="json") for event in work_item.events[-8:]],
        }
    )


if __name__ == "__main__":
    cli()
