"""CLI for the reviewed one-file Blue Club status repair."""

from pathlib import Path

import typer

from metadata.blue_club_status_repair import (
    OBSERVED_STATUS,
    PROPOSED_STATUS,
    REQUIRED_DIFFICULTY,
    apply_blue_club_status_report,
    build_blue_club_status_report,
)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_blue_club_status_report(root)
    for action in report.actions:
        typer.echo(
            f"SET STATUS | {action.article} | {OBSERVED_STATUS!r} -> "
            f"{PROPOSED_STATUS!r} | difficulty={REQUIRED_DIFFICULTY!r} frozen"
        )
    typer.echo()
    typer.echo(f"Files selected     : {report.selected_files}")
    typer.echo(f"Files to update    : {len(report.actions)}")
    typer.echo(f"Status changes     : {len(report.actions)}")
    typer.echo("Difficulty changes : 0")
    typer.echo(f"Files to back up   : {len(report.actions)}")
    if not apply:
        typer.echo("No changes made. Pass --apply and --backup to confirm this repair.")
        return
    if not report.actions:
        typer.echo("Files updated     : 0")
        return
    if backup is None:
        raise typer.BadParameter("--backup is required with --apply", param_hint="--backup")
    apply_blue_club_status_report(report, root, backup)
    typer.echo(f"Files updated     : {len(report.actions)}")
    typer.echo(f"Backup directory  : {backup}")
