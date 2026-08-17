"""Dry-run-first command for the reviewed bidding category batch."""

from __future__ import annotations

from pathlib import Path

import typer

from metadata.bidding_category_repair import (
    apply_bidding_category_report,
    build_bidding_category_report,
)


def run(root: Path, backup: Path, apply: bool) -> None:
    report = build_bidding_category_report(root)
    for action in report.actions:
        typer.echo(
            f"SET CATEGORY | {action.article} | {action.current_category!r} -> "
            f"'bidding' | subcategory={action.subcategory!r} | retained-tag="
            f"{action.retained_tag!r} present={action.retained_tag_present} | "
            "tags frozen"
        )

    typer.echo()
    typer.echo(f"Files selected      : {report.reviewed_files}")
    typer.echo(f"Files to update     : {len(report.actions)}")
    typer.echo(f"Category changes    : {len(report.actions)}")
    typer.echo("Tag changes         : 0")
    typer.echo("Subcategory changes : 0")
    typer.echo(f"Files to back up    : {len(report.actions)}")

    if not apply:
        typer.echo("No changes made. Pass --apply to confirm reviewed category repair.")
        return

    apply_bidding_category_report(report, root, backup)
    typer.echo(f"Files updated       : {len(report.actions)}")
    typer.echo(f"Backup directory    : {backup}")
