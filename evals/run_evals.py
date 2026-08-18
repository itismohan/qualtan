"""Run deterministic quality evaluations against a persisted QUALTAN work item."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import click

from evals.graders.quality import evaluate_work_item
from infrastructure.artifact_store import ArtifactStore


@click.command()
@click.option("--work-item", "work_item_id", required=True, help="Persisted QUALTAN work-item ID.")
@click.option("--artifact-dir", default="artifacts", show_default=True, type=click.Path(path_type=Path))
def main(work_item_id: str, artifact_dir: Path) -> None:
    work_item = ArtifactStore(root=artifact_dir).load_work_item(work_item_id)
    report = evaluate_work_item(work_item)
    click.echo(
        json.dumps(
            {
                "passed": report.passed,
                "average_score": report.average_score,
                "scores": [asdict(score) for score in report.scores],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
