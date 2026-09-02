"""CLI for the reviewed five-file declarer-deception category batch."""

from __future__ import annotations

from pathlib import Path

import typer

from metadata.play_endgame_category_repair import (
    apply_play_declarer_deception_category_report,
    build_play_declarer_deception_category_report,
)


def run(root: Path, backup: Path | None, apply: bool) -> None:
    report = build_play_declarer_deception_category_report(root)
    for action in report.actions:
        typer.echo(
            f"SET CATEGORY | {action.article} | {action.current_category!r} -> "
            f"{action.proposed_category!r} | subcategory={action.subcategory!r} | "
            f"retained-tag={action.retained_tag!r} present={action.retained_tag_present} | "
            f"broad-tag-present={action.canonical_tag_present} | tags frozen"
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
        raise typer.BadParameter("--backup is required with --apply", param_hint="--backup")
    apply_play_declarer_deception_category_report(report, root, backup)
    typer.echo(f"Files updated       : {len(report.actions)}")
    typer.echo(f"Backup directory    : {backup}")
