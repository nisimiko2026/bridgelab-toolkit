"""
BridgeLab Toolkit
Learning Path Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.graph import KnowledgeGraph
from analysis.learning_paths import LearningPathAnalyzer
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
    article_id: str,
) -> None:
    """
    Display a learning path beginning with the specified article.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    analyzer = LearningPathAnalyzer(graph)

    article = graph.article(article_id)

    if article is None:

        typer.secho(
            f"Unknown article: {article_id}",
            fg=typer.colors.RED,
        )

        raise typer.Exit(1)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo(f"Learning Path: {article.metadata.title}")
    typer.echo("=" * 60)
    typer.echo()

    for index, node in enumerate(
        analyzer.path(article),
        start=1,
    ):

        typer.echo(
            f"{index:2}. {node.relative_path.as_posix()}"
        )
