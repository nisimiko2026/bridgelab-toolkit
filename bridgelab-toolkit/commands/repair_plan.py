"""Metadata repair-plan command."""

from __future__ import annotations

from pathlib import Path

import typer

from core.repository import Repository
from metadata.repair_plan import MetadataRepairPlanner


def run(root: Path, output_directory: Path) -> None:
    """Create review artifacts without changing repository source files."""

    articles = Repository(root).build()
    planner = MetadataRepairPlanner()
    proposals = planner.build(articles)
    json_output = output_directory / "metadata_repair_plan.json"
    markdown_output = output_directory / "metadata_repair_plan.md"
    planner.export(proposals, json_output, markdown_output)

    descriptions = sum(item.field == "description" for item in proposals)
    difficulties = sum(item.field == "difficulty" for item in proposals)

    typer.echo(f"Articles checked     : {len(articles)}")
    typer.echo(f"Description proposals: {descriptions}")
    typer.echo(f"Difficulty proposals : {difficulties}")
    typer.echo(f"Total proposals      : {len(proposals)}")
    typer.echo(f"JSON plan            : {json_output}")
    typer.echo(f"Markdown plan        : {markdown_output}")
    typer.secho("No source files were modified.", fg=typer.colors.YELLOW)
