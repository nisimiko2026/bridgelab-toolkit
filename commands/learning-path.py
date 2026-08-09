"""
BridgeLab Toolkit
Learning Path Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from analysis.graph import KnowledgeGraph
from analysis.learning_paths import LearningPathAnalyzer
from core.models import Article
from core.repository import Repository


# ============================================================
# Helpers
# ============================================================

def find_article(
    articles: list[Article],
    query: str,
) -> Article | None:
    """
    Find an article by id, title, filename or path.
    """

    query = query.lower().strip()

    # Exact ID
    for article in articles:
        if article.id.lower() == query:
            return article

    # Exact title
    for article in articles:
        if article.metadata.title.lower() == query:
            return article

    # Filename
    for article in articles:
        if article.filename.lower() == query:
            return article

    # Filename without extension
    for article in articles:
        if article.filename.removesuffix(".md").lower() == query:
            return article

    # Relative path
    for article in articles:
        if article.relative_path.as_posix().lower() == query:
            return article

    # Partial title/path match
    for article in articles:
        if (
            query in article.metadata.title.lower()
            or query in article.relative_path.as_posix().lower()
        ):
            return article

    return None


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
    query: str,
) -> None:
    """
    Display a learning path beginning with the specified article.
    """

    typer.echo("Building repository...")

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles loaded : {len(articles)}")

    article = find_article(
        articles,
        query,
    )

    if article is None:

        typer.secho(
            f"Unknown article: {query}",
            fg=typer.colors.RED,
        )

        typer.echo()
        typer.echo("Matching articles:")

        for candidate in sorted(
            articles,
            key=lambda a: a.metadata.title,
        )[:20]:
            typer.echo(f"  {candidate.metadata.title}")

        raise typer.Exit(1)

    graph = KnowledgeGraph(articles)

    analyzer = LearningPathAnalyzer(graph)

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
            f"{index:2}. {node.metadata.title}"
        )
