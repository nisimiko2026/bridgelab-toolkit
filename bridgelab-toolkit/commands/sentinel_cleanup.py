"""Dry-run-first command for exact metadata sentinel cleanup."""

from __future__ import annotations

from pathlib import Path

import typer

from metadata.sentinel_cleanup import apply_cleanup, build_cleanup_report


def run(root: Path, backup: Path, apply: bool) -> None:
    report = build_cleanup_report(root)

    for action in report.actions:
        if action.tag_removals:
            typer.echo(
                f"REMOVE TAG | {action.article} | exact 'none' items: "
                f"{action.tag_removals}"
            )
        if action.difficulty_cleared:
            typer.echo(
                f"CLEAR DIFFICULTY | {action.article} | literal 'None' | "
                "difficulty-exempt"
            )
    for article in report.literal_none_subcategories:
        typer.echo(f"REPORT ONLY | {article} | subcategory | literal 'None'")
    for article in report.non_exempt_literal_none_difficulties:
        typer.echo(
            f"REPORT ONLY | {article} | difficulty | literal 'None' | " "not exempt"
        )

    typer.echo()
    typer.echo(f"Files to update              : {len(report.actions)}")
    typer.echo(f"Exact 'none' tags to remove  : {report.tag_removals}")
    typer.echo(f"Exempt difficulties to clear : {report.difficulties_cleared}")
    typer.echo(
        "Literal subcategories reported: " f"{len(report.literal_none_subcategories)}"
    )
    typer.echo(
        "Non-exempt difficulties       : "
        f"{len(report.non_exempt_literal_none_difficulties)}"
    )
    typer.echo(f"Files to back up             : {len(report.actions)}")

    if not apply:
        typer.echo("No changes made. Pass --apply to confirm sentinel cleanup.")
        return

    apply_cleanup(report, root, backup)
    typer.echo(f"Files updated                : {len(report.actions)}")
    typer.echo(f"Backup directory             : {backup}")
