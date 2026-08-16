"""Apply reviewed metadata repair proposals."""

from __future__ import annotations

from pathlib import Path

import typer

from metadata.repair_apply import apply_repair_plan


def run(
    root: Path,
    plan: Path,
    backup: Path,
    apply: bool,
    include_low_confidence: bool = False,
) -> None:
    if not apply:
        typer.echo("No changes made. Pass --apply to confirm the repair batch.")
        raise typer.Exit(code=2)

    allowed_confidence = {"high", "medium"}
    if include_low_confidence:
        allowed_confidence.add("low")

    result = apply_repair_plan(
        root=root,
        plan_path=plan,
        backup_root=backup,
        allowed_confidence=allowed_confidence,
    )
    typer.echo(f"Proposals applied : {result.applied}")
    typer.echo(f"Proposals skipped : {result.skipped}")
    typer.echo(f"Files backed up    : {result.backed_up}")
    typer.echo(f"Backup directory  : {backup}")
