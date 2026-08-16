"""Safely repair known invalid repository filenames and references."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import typer


RENAMES = {
    "bidding/conventions/competitive/good–bad-2nt.md":
        "bidding/conventions/competitive/good-bad-2nt.md",
    "bidding/conventions/defensive-methods/Woolsey Defense to Multi.md":
        "bidding/conventions/defensive-methods/woolsey-defense-to-multi.md",
    "bidding/conventions/doubles/action.double.md":
        "bidding/conventions/doubles/action-double.md",
    "bidding/conventions/responses/Jacoby-notrump.md":
        "bidding/conventions/responses/jacoby-notrump.md",
    "bidding/conventions/responses/preemptive.raise.md":
        "bidding/conventions/responses/preemptive-raise.md",
    "play/declarer-play/probabilty/Inference.md":
        "play/declarer-play/probabilty/probability-inference.md",
}


def _atomic_write(path: Path, content: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
        os.replace(temporary_name, path)
    except OSError:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def run(root: Path, backup: Path, apply: bool) -> None:
    if not apply:
        typer.echo("No changes made. Pass --apply to confirm filename repairs.")
        raise typer.Exit(code=2)

    sources = {old: root / Path(old) for old in RENAMES}
    missing = [old for old, path in sources.items() if not path.is_file()]
    collisions = [new for new in RENAMES.values() if (root / Path(new)).exists()]

    # A case-only rename resolves to the same Windows file and is not a collision.
    collisions = [
        new
        for new in collisions
        if str(root / Path(new)).casefold()
        not in {str(path).casefold() for path in sources.values()}
    ]
    if missing or collisions:
        raise RuntimeError(f"Unsafe rename state; missing={missing}, collisions={collisions}")

    replacements: list[tuple[str, str]] = []
    for old, new in RENAMES.items():
        replacements.extend(
            [
                (old, new),
                (old.removesuffix(".md"), new.removesuffix(".md")),
            ]
        )

    changed_references: dict[Path, str] = {}
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            changed_references[markdown] = updated

    backup.mkdir(parents=True, exist_ok=True)
    affected = set(sources.values()) | set(changed_references)
    for path in sorted(affected):
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    for old, new in RENAMES.items():
        source = root / Path(old)
        destination = root / Path(new)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if str(source).casefold() == str(destination).casefold():
            intermediate = source.with_name(source.name + ".rename-temp")
            os.replace(source, intermediate)
            os.replace(intermediate, destination)
        else:
            os.replace(source, destination)

    for original, updated in changed_references.items():
        target = root / Path(RENAMES.get(original.relative_to(root).as_posix(), original.relative_to(root)))
        _atomic_write(target, updated)

    typer.echo(f"Files renamed     : {len(RENAMES)}")
    typer.echo(f"References updated: {len(changed_references)}")
    typer.echo(f"Files backed up   : {len(affected)}")
    typer.echo(f"Backup directory : {backup}")
