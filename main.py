"""
BridgeLab Toolkit
Main Application
"""

from __future__ import annotations

from pathlib import Path

import typer

from config import REPOSITORY, REPORTS

from commands.scan import run as scan_command
from commands.debug import run as debug_command
from commands.enrich import run as enrich_command
from commands.validate import run as validate_command
from commands.repair_plan import run as repair_plan_command
from commands.repair_apply import run as repair_apply_command
from commands.repair_filenames import run as repair_filenames_command

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


@app.command()
def validate(
    root: Path = repository_option(),
) -> None:
    """Validate repository health."""
    validate_command(root)


@app.command("repair-plan")
def repair_plan(
    root: Path = repository_option(),
    output_directory: Path = typer.Option(
        REPORTS,
        "--output-directory",
        file_okay=False,
        resolve_path=True,
        help="Directory for JSON and Markdown repair plans.",
    ),
) -> None:
    """Generate read-only metadata repair proposals."""
    repair_plan_command(root, output_directory)


@app.command("repair-apply")
def repair_apply(
    root: Path = repository_option(),
    plan: Path = typer.Option(
        REPORTS / "metadata_repair_plan.json",
        "--plan",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "metadata-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
    include_low_confidence: bool = typer.Option(
        False,
        "--include-low-confidence",
        help="Apply low-confidence proposals after explicit editorial review.",
    ),
) -> None:
    """Apply medium/high-confidence repairs after backing up source files."""
    repair_apply_command(
        root,
        plan,
        backup,
        apply,
        include_low_confidence=include_low_confidence,
    )


@app.command("repair-filenames")
def repair_filenames(
    root: Path = repository_option(),
    backup: Path = typer.Option(
        REPORTS.parent / "backups" / "filename-repair",
        "--backup",
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """Rename known invalid files and update exact inbound references."""
    repair_filenames_command(root, backup, apply)


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
