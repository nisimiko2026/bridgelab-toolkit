"""
BridgeLab Toolkit
Duplicates Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.duplicates import DuplicateAnalyzer
from analysis.graph import KnowledgeGraph
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
) -> None:
    """
    Display duplicate articles.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    analyzer = DuplicateAnalyzer(graph)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo("Duplicate Articles")
    typer.echo("=" * 60)
    typer.echo()

    typer.echo(
        f"Duplicate groups : {analyzer.count()}"
    )

    typer.echo()

    for line in analyzer.report():
        typer.echo(line)
