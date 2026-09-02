"""
BridgeLab Toolkit
Statistics Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.graph import KnowledgeGraph
from analysis.statistics import RepositoryStatistics
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
) -> None:
    """
    Display repository statistics.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    statistics = RepositoryStatistics(graph)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo("Repository Statistics")
    typer.echo("=" * 60)
    typer.echo()

    summary = statistics.summary()

    for name, value in summary.items():

        typer.echo(
            f"{name:20} : {value}"
        )
