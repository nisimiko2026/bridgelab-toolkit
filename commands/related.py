"""
BridgeLab Toolkit
Related Articles Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.graph import KnowledgeGraph
from analysis.related import RelatedAnalyzer
from core.repository import Repository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
    article_id: str,
) -> None:
    """
    Display articles related to the specified article.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    graph = KnowledgeGraph(articles)

    analyzer = RelatedAnalyzer(graph)

    article = graph.find_article(article_id)

    if article is None:

        typer.secho(
            f"Unknown article: {article_id}",
            fg=typer.colors.RED,
        )

        raise typer.Exit(1)

    typer.echo()
    typer.echo("=" * 60)
    typer.echo(f"Related Articles: {article.metadata.title}")
    typer.echo("=" * 60)
    typer.echo()

    for related, score in analyzer.related(article):

        typer.echo(
            f"{score:3}  {related.relative_path.as_posix()}"
        )
