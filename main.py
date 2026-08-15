"""
BridgeLab Toolkit
Main Application
"""

from __future__ import annotations

from pathlib import Path

import typer

from config import REPOSITORY

from commands.scan import run as scan_command
from commands.debug import run as debug_command
from commands.enrich import run as enrich_command

from commands.statistics import run as statistics_command
from commands.coverage import run as coverage_command
from commands.orphans import run as orphans_command
from commands.duplicates import run as duplicates_command
from commands.related import run as related_command
from commands.learning_path import run as learning_path_command


# ============================================================
# Application
# ============================================================

app = typer.Typer(
    help="BridgeLab Knowledge Toolkit",
    add_completion=False,
)


# ============================================================
# Common Root Option
# ============================================================

def repository_option() -> Path:
    return typer.Option(
        REPOSITORY,
        "--root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Knowledge repository.",
    )


# ============================================================
# Repository Commands
# ============================================================

@app.command()
def scan(
    root: Path = repository_option(),
) -> None:
    """
    Scan the repository.
    """
    scan_command(root)


@app.command()
def debug(
    root: Path = repository_option(),
) -> None:
    """
    Debug the repository.
    """
    debug_command(root)


@app.command()
def enrich(
    root: Path = repository_option(),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Write enriched metadata to source articles.",
    ),
) -> None:
    """
    Enrich repository metadata.
    """
    enrich_command(root, apply=apply)


# ============================================================
# Analysis Commands
# ============================================================

@app.command()
def statistics(
    root: Path = repository_option(),
) -> None:
    """
    Display repository statistics.
    """
    statistics_command(root)


@app.command()
def coverage(
    root: Path = repository_option(),
) -> None:
    """
    Display repository coverage.
    """
    coverage_command(root)


@app.command()
def orphans(
    root: Path = repository_option(),
) -> None:
    """
    Display orphan articles.
    """
    orphans_command(root)


@app.command()
def duplicates(
    root: Path = repository_option(),
) -> None:
    """
    Display duplicate articles.
    """
    duplicates_command(root)


@app.command()
def related(
    article: str = typer.Argument(
        ...,
        help="Article ID or path.",
    ),
    root: Path = repository_option(),
) -> None:
    """
    Display related articles.
    """
    related_command(root, article)


@app.command("learning-path")
def learning_path(
    article: str = typer.Argument(
        ...,
        help="Article ID or path.",
    ),
    root: Path = repository_option(),
) -> None:
    """
    Display a learning path.
    """
    learning_path_command(root, article)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    app()
