"""CLI for the reviewed Phase 3A category normalization Batch 3.3t."""

from pathlib import Path
import typer
from metadata.category_normalization_batch3_3t import (
    OBSERVED_CATEGORY,
    PROPOSED_CATEGORY,
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T,
    apply_category_normalization_batch3_3t_report,
    build_category_normalization_batch3_3t_report,
)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_category_normalization_batch3_3t_report(root)
    for action in report.actions:
        subcategory, _ = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T[action.article]
        typer.echo(
            f"SET CATEGORY | {action.article} | {OBSERVED_CATEGORY!r} -> {PROPOSED_CATEGORY!r} | tags frozen | subcategory={subcategory!r} frozen"
        )
    typer.echo()
    typer.echo(f"Files selected      : {report.selected_files}")
    typer.echo(f"Files to update     : {len(report.actions)}")
    typer.echo(f"Category changes    : {len(report.actions)}")
    typer.echo("Tag changes         : 0")
    typer.echo("Subcategory changes : 0")
    typer.echo(f"Files to back up    : {len(report.actions)}")
    if not apply:
        typer.echo("No changes made. Pass --apply and --backup to confirm this repair.")
        return
    if not report.actions:
        typer.echo("Files updated       : 0")
        return
    if backup is None:
        raise typer.BadParameter(
            "--backup is required with --apply", param_hint="--backup"
        )
    apply_category_normalization_batch3_3t_report(report, root, backup)
    typer.echo(f"Files updated       : {len(report.actions)}")
    typer.echo(f"Backup directory    : {backup}")
