"""CLI for Phase 4B Batch 1 case-only metadata-title normalization."""

from pathlib import Path

import typer

from metadata.title_h1_case_normalization_batch1 import (
    apply_title_h1_case_normalization_batch1_report,
    build_title_h1_case_normalization_batch1_report,
)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_title_h1_case_normalization_batch1_report(root)
    for action in report.actions:
        typer.echo(
            f"SET TITLE | {action.article} | {action.original_title!r} -> "
            f"{action.proposed_title!r} | H1 frozen"
        )
    typer.echo()
    typer.echo(f"Files selected   : {report.selected_files}")
    typer.echo(f"Files to update  : {len(report.actions)}")
    typer.echo(f"Title changes    : {len(report.actions)}")
    typer.echo("H1 changes       : 0")
    typer.echo(f"Files to back up : {len(report.actions)}")
    if not apply:
        typer.echo("No changes made. Pass --apply and --backup to confirm this repair.")
        return
    if not report.actions:
        typer.echo("Files updated    : 0")
        return
    if backup is None:
        raise typer.BadParameter("--backup is required with --apply", param_hint="--backup")
    apply_title_h1_case_normalization_batch1_report(report, root, backup)
    typer.echo(f"Files updated    : {len(report.actions)}")
    typer.echo(f"Backup directory : {backup}")
