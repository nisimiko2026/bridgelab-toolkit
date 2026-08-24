"""CLI for the reviewed Phase 3A category normalization Batch 3.3v."""

from pathlib import Path

import typer

from metadata.category_normalization_batch3_3v import (
    PROPOSED_CATEGORY,
    REQUIRED_SUBCATEGORY,
    apply_category_normalization_batch3_3v_report,
    build_category_normalization_batch3_3v_report,
)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_category_normalization_batch3_3v_report(root)
    for action in report.actions:
        typer.echo(
            f"SET CATEGORY | {action.article} | {action.observed_category!r} -> {PROPOSED_CATEGORY!r} | tags frozen | subcategory={REQUIRED_SUBCATEGORY!r} frozen"
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
    apply_category_normalization_batch3_3v_report(report, root, backup)
    typer.echo(f"Files updated       : {len(report.actions)}")
    typer.echo(f"Backup directory    : {backup}")
