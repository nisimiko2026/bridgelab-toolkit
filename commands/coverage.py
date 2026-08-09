"""
BridgeLab Toolkit
Coverage Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.coverage import CoverageAnalyzer
from analysis.graph import KnowledgeGraph
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
) -> None:
    """
    Display repository coverage.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    analyzer = CoverageAnalyzer(graph)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo("Repository Coverage")
    typer.echo("=" * 60)
    typer.echo()

    for line in analyzer.report():
        typer.echo(line)
