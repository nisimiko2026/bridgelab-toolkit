"""
BridgeLab Toolkit
Debug Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from core.repository import Repository

from enrichment.alias_repository import AliasRepository
from enrichment.system_repository import SystemRepository


# ============================================================
# Command
# ============================================================

def run(
    root: Path,
) -> None:
    """
    Debug the repository.
    """

    typer.echo("=" * 60)
    typer.echo("BridgeLab Debug")
    typer.echo("=" * 60)
    typer.echo()

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    typer.echo(f"Repository : {root}")
    typer.echo(f"Exists     : {root.exists()}")
    typer.echo()

    repository = Repository(root)

    articles = repository.build()

    typer.echo(f"Articles   : {len(articles)}")
    typer.echo()

    # --------------------------------------------------------
    # Systems
    # --------------------------------------------------------

    systems = SystemRepository().systems

    typer.echo(f"Systems    : {len(systems)}")

    if systems:
        typer.echo(f"First      : {systems[0]}")

    typer.echo()

    # --------------------------------------------------------
    # Aliases
    # --------------------------------------------------------

    aliases = AliasRepository().aliases

    typer.echo(f"Aliases    : {len(aliases)}")

    typer.echo()

    # --------------------------------------------------------
    # Sample Articles
    # --------------------------------------------------------

    typer.echo("First Articles")
    typer.echo("-" * 60)

    for article in articles[:10]:

        typer.echo(
            f"{article.id:30} "
            f"{article.metadata.title}"
        )

    typer.echo()

    # --------------------------------------------------------
    # References
    # --------------------------------------------------------

    total = sum(
        len(article.metadata.references)
        for article in articles
    )

    typer.echo(f"References : {total}")

    if total == 0:

        typer.secho(
            "WARNING: No references detected.",
            fg=typer.colors.YELLOW,
        )

    typer.echo()

    # --------------------------------------------------------
    # Tags
    # --------------------------------------------------------

    total = sum(
        len(article.metadata.tags)
        for article in articles
    )

    typer.echo(f"Tags       : {total}")

    typer.echo()

    # --------------------------------------------------------
    # Systems Assigned
    # --------------------------------------------------------

    assigned = sum(
        1
        for article in articles
        if article.metadata.systems
    )

    typer.echo(f"Articles with systems : {assigned}")

    typer.echo()

    typer.secho(
        "Debug completed.",
        fg=typer.colors.GREEN,
    )
