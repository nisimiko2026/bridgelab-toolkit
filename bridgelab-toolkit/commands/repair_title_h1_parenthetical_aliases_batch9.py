"""CLI for Phase 4B Batch 9A parenthetical-alias metadata repair."""

from pathlib import Path
import sys

import typer

from metadata.title_h1_parenthetical_aliases_batch9 import (
    apply_title_h1_parenthetical_aliases_batch9_report,
    build_title_h1_parenthetical_aliases_batch9_report,
)


def _console_text(value: str) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_title_h1_parenthetical_aliases_batch9_report(root)
    for action in report.actions:
        typer.echo(
            _console_text(
                f"SET ALIASES | {action.article} | [] -> {list(action.aliases)!r}"
            )
        )
    typer.echo()
    typer.echo(f"Files selected  : {report.selected_files}")
    typer.echo(f"Files to update : {len(report.actions)}")
    typer.echo(f"Alias fields    : {len(report.actions)}")
    typer.echo(f"Alias values    : {sum(len(action.aliases) for action in report.actions)}")
    typer.echo("Acronym changes : 0")
    typer.echo("Title changes   : 0")
    typer.echo("H1 changes      : 0")
    typer.echo(f"Files to back up: {len(report.actions)}")
    if not apply:
        typer.echo("No changes made. Pass --apply and --backup to confirm this repair.")
        return
    if not report.actions:
        typer.echo("Files updated   : 0")
        return
    if backup is None:
        raise typer.BadParameter("--backup is required with --apply", param_hint="--backup")
    apply_title_h1_parenthetical_aliases_batch9_report(report, root, backup)
    typer.echo(f"Files updated   : {len(report.actions)}")
    typer.echo(f"Backup directory: {backup}")
