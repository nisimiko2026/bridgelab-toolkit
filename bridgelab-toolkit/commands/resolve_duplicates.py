"""Resolve the reviewed duplicate-filename set safely."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import typer


RENAMES = {
    "play/declarer-play/deceptive-play/false-carding.md":
        "play/declarer-play/deceptive-play/declarer-false-carding.md",
    "play/declarer-play/general-techniques/preserving-entries.md":
        "play/declarer-play/general-techniques/entry-management-technique.md",
}
CONSOLIDATIONS = {
    "play/defence/counting/rule-of-11.md":
        "play/defence/opening-leads/rule-of-11.md",
}


def _atomic_write(path: Path, content: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
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
        typer.echo("No changes made. Pass --apply to confirm duplicate resolution.")
        raise typer.Exit(code=2)

    actions = {**RENAMES, **CONSOLIDATIONS}
    for old, new in actions.items():
        if not (root / Path(old)).is_file() or not (
            (root / Path(new)).is_file() if old in CONSOLIDATIONS else True
        ):
            raise RuntimeError(f"Unsafe duplicate-resolution state: {old} -> {new}")
        if old in RENAMES and (root / Path(new)).exists():
            raise RuntimeError(f"Rename target already exists: {new}")

    replacements: list[tuple[str, str]] = []
    for old, new in actions.items():
        replacements.extend(
            [(old, new), (old.removesuffix(".md"), new.removesuffix(".md"))]
        )

    changed: dict[Path, str] = {}
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            changed[markdown] = updated

    sources = {root / Path(path) for path in actions}
    affected = sources | set(changed)
    backup.mkdir(parents=True, exist_ok=True)
    for path in sorted(affected):
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    for old, new in RENAMES.items():
        os.replace(root / Path(old), root / Path(new))

    for old in CONSOLIDATIONS:
        (root / Path(old)).unlink()

    for original, updated in changed.items():
        relative = original.relative_to(root).as_posix()
        target = root / Path(RENAMES.get(relative, relative))
        if target.exists():
            _atomic_write(target, updated)

    typer.echo(f"Files renamed       : {len(RENAMES)}")
    typer.echo(f"Duplicates removed  : {len(CONSOLIDATIONS)}")
    typer.echo(f"References updated  : {len(changed)}")
    typer.echo(f"Files backed up     : {len(affected)}")
    typer.echo(f"Backup directory   : {backup}")
