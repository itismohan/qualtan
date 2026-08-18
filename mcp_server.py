"""QUALTAN MCP server.

It exposes narrowly scoped workflow tools. External mutations and test execution are
not exposed here; they remain policy-gated application actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from application.factory import build_quality_workflow
from application.workflows import RunOptions
from infrastructure.artifact_store import ArtifactStoreError

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as error:  # explicit, actionable error when launched without optional dependency
    raise RuntimeError("Install the 'mcp' dependency with requirements.txt before launching the QUALTAN MCP server.") from error

mcp = FastMCP("QUALTAN")


def _workflow(project_root: str = "."):
    return build_quality_workflow(Path(project_root).resolve())


def _summary(work_item) -> dict[str, Any]:
    return {
        "work_item_id": work_item.work_item_id,
        "story_key": work_item.story.key,
        "status": work_item.status.value,
        "pending_approvals": [
            {"request_id": item.request_id, "action": item.action, "reason": item.reason}
            for item in work_item.approvals
            if item.status.value == "pending"
        ],
        "validation_results": [item.model_dump(mode="json") for item in work_item.validations],
        "last_event": work_item.events[-1].model_dump(mode="json") if work_item.events else None,
    }


@mcp.tool()
def create_quality_work_item(story_key: str, project_root: str = ".") -> dict[str, Any]:
    """Read a Jira story and persist a new QUALTAN work item. Does not generate code or mutate external systems."""
    workflow = _workflow(project_root)
    return _summary(workflow.create_from_jira(story_key))


@mcp.tool()
def run_quality_workflow(work_item_id: str, project_root: str = ".") -> dict[str, Any]:
    """Run or resume a work item. Generated test code stops for recorded human approval before validation."""
    workflow = _workflow(project_root)
    return _summary(workflow.resume(work_item_id, RunOptions(require_generation_approval=True)))


@mcp.tool()
def approve_generated_artifact(work_item_id: str, approval_request_id: str, approver: str, note: str = "", project_root: str = ".") -> dict[str, Any]:
    """Record human approval for a generated artifact. This does not execute tests or change external systems."""
    workflow = _workflow(project_root)
    return _summary(workflow.approve(work_item_id, approval_request_id, approver, note))


@mcp.tool()
def get_quality_work_item(work_item_id: str, project_root: str = ".") -> dict[str, Any]:
    """Read a persisted work item, including its state, approval status, and validation evidence."""
    try:
        return _summary(_workflow(project_root).dependencies.store.load_work_item(work_item_id))
    except ArtifactStoreError as error:
        return {"error": str(error), "work_item_id": work_item_id}


if __name__ == "__main__":
    mcp.run()
