"""
BridgeLab Toolkit
Orphans Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.graph import KnowledgeGraph
from analysis.orphans import OrphanAnalyzer
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
) -> None:
    """
    Display orphan articles.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    analyzer = OrphanAnalyzer(graph)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo("Orphan Articles")
    typer.echo("=" * 60)
    typer.echo()

    typer.echo(
        f"Total orphans : {analyzer.count()}"
    )

    typer.echo()

    for category, count in analyzer.summary().items():

        typer.echo(
            f"{category:25} {count}"
        )

    typer.echo()

    for line in analyzer.report():

        typer.echo(line)
