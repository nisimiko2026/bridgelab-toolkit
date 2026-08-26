"""CLI for Phase 4B Batch 3 minimal title/H1 content repair."""

from pathlib import Path
import sys

import typer

from metadata.title_h1_content_repair_batch3 import (
    apply_title_h1_content_repair_batch3_report,
    build_title_h1_content_repair_batch3_report,
)


def _console_text(value: str) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_title_h1_content_repair_batch3_report(root)
    for action in report.actions:
        typer.echo(_console_text(
            f"SET TITLE + INSERT H1 | {action.article} | "
            f"{action.original_title!r} -> {action.proposed_title!r}"
        ))
    typer.echo()
    typer.echo(f"Files selected     : {report.selected_files}")
    typer.echo(f"Files to update    : {len(report.actions)}")
    typer.echo(f"Title changes      : {len(report.actions)}")
    typer.echo(f"Document H1 inserts: {len(report.actions)}")
    typer.echo(f"Files to back up   : {len(report.actions)}")
    if not apply:
        typer.echo("No changes made. Pass --apply and --backup to confirm this repair.")
        return
    if not report.actions:
        typer.echo("Files updated      : 0")
        return
    if backup is None:
        raise typer.BadParameter("--backup is required with --apply", param_hint="--backup")
    apply_title_h1_content_repair_batch3_report(report, root, backup)
    typer.echo(f"Files updated      : {len(report.actions)}")
    typer.echo(f"Backup directory   : {backup}")
