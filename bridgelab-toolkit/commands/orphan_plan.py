from pathlib import Path

import typer

from analysis.orphan_plan import OrphanRepairPlanner
from core.repository import Repository


def run(root: Path, output_directory: Path) -> None:
    """Create parent-index proposals without changing source files."""

    articles = Repository(root).build()
    planner = OrphanRepairPlanner()
    proposals = planner.build(articles)
    json_output = output_directory / "orphan_repair_plan.json"
    markdown_output = output_directory / "orphan_repair_plan.md"
    planner.export(proposals, json_output, markdown_output)

    actionable = sum(item.parent_index is not None for item in proposals)
    typer.echo(f"Articles checked    : {len(articles)}")
    typer.echo(f"Orphan candidates   : {len(proposals)}")
    typer.echo(f"Actionable proposals: {actionable}")
    typer.echo(f"Manual review       : {len(proposals) - actionable}")
    typer.echo(f"JSON plan           : {json_output}")
    typer.echo(f"Markdown plan       : {markdown_output}")
    typer.secho("No source files were modified.", fg=typer.colors.YELLOW)
