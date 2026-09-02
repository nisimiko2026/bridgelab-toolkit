"""Dry-run-first command for exact metadata sentinel cleanup."""

from __future__ import annotations

from pathlib import Path

import typer

from metadata.sentinel_cleanup import apply_cleanup, build_cleanup_report


def run(
    root: Path,
    backup: Path,
    apply: bool,
    only_reviewed_empty_subcategories: bool = False,
    only_reviewed_generated_reference_subcategories: bool = False,
) -> None:
    report = build_cleanup_report(
        root,
        only_reviewed_empty_subcategories=only_reviewed_empty_subcategories,
        only_reviewed_generated_reference_subcategories=(
            only_reviewed_generated_reference_subcategories
        ),
    )

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
        if action.subcategory_cleared:
            typer.echo(
                f"CLEAR SUBCATEGORY | {action.article} | literal 'None' | "
                "reviewed intentional empty"
            )
        elif action.subcategory_replacement is not None:
            typer.echo(
                f"SET SUBCATEGORY | {action.article} | literal 'None' -> "
                f"{action.subcategory_replacement!r} | reviewed generated reference"
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
    typer.echo(f"Reviewed subcategories clear : {report.subcategories_cleared}")
    typer.echo(f"Reviewed subcategories assign: {report.subcategories_assigned}")
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
