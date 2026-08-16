from pathlib import Path

import typer

from analysis.orphan_apply import apply_orphan_plan, selected_proposals


def run(
    root: Path,
    plan: Path,
    backup: Path,
    apply: bool,
    include_medium_confidence: bool = False,
) -> None:
    allowed_confidence = {"high"}
    if include_medium_confidence:
        allowed_confidence.add("medium")

    selected = selected_proposals(plan, allowed_confidence)
    parent_indexes = {str(item["parent_index"]) for item in selected}

    if not apply:
        typer.echo(f"Proposals selected: {len(selected)}")
        typer.echo(f"Parent indexes    : {len(parent_indexes)}")
        typer.echo("No changes made. Pass --apply to confirm this repair batch.")
        return

    result = apply_orphan_plan(
        root=root,
        plan_path=plan,
        backup_root=backup,
        allowed_confidence=allowed_confidence,
    )
    typer.echo(f"Proposals applied: {result.applied}")
    typer.echo(f"Proposals skipped: {result.skipped}")
    typer.echo(f"Parent indexes   : {result.parent_indexes}")
    typer.echo(f"Files backed up  : {result.backed_up}")
    typer.echo(f"Backup directory : {backup}")
