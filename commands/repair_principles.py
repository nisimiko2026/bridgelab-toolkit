from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import typer


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


def _load_plan(plan: Path) -> dict:
    return json.loads(plan.read_text(encoding="utf-8"))


def _moves(
    root: Path,
    data: dict,
    include_medium_confidence: bool,
) -> dict[Path, Path]:
    nested = {
        Path(item["old"]).name: Path(item["new"]).name
        for item in data["nested_file_moves"]
        if item["confidence"] == "high" or include_medium_confidence
    }
    moves: dict[Path, Path] = {}

    for item in data["directory_moves"]:
        old = root / Path(item["old"])
        new = root / Path(item["new"])
        if new.exists():
            if old.exists():
                raise RuntimeError(f"Both source and destination directories exist: {old}")
            continue
        if not old.is_dir():
            raise RuntimeError(f"Missing source directory: {old}")
        for source in old.rglob("*.md"):
            name = nested.get(source.name, source.name)
            moves[source] = new / source.relative_to(old).with_name(name)

    # A nested rename may be approved after its surrounding directory move.
    # Resolve the source through the completed move so the plan is resumable.
    for item in data["nested_file_moves"]:
        if item["confidence"] != "high" and not include_medium_confidence:
            continue
        source_identifier = item["old"]
        source = root / Path(source_identifier)
        if not source.exists():
            for directory in data["directory_moves"]:
                if source_identifier.startswith(directory["old"] + "/"):
                    source_identifier = (
                        directory["new"]
                        + source_identifier[len(directory["old"]):]
                    )
                    source = root / Path(source_identifier)
                    break
        destination = root / Path(item["new"])
        if source.is_file() and source != destination and source not in moves:
            moves[source] = destination

    return moves


def run(
    root: Path,
    plan: Path,
    backup: Path,
    apply: bool,
    include_medium_confidence: bool = False,
) -> None:
    data = _load_plan(plan)
    moves = _moves(root, data, include_medium_confidence)
    replacements = [
        (item["old"], item["new"])
        for item in data["directory_moves"]
    ]
    for item in data["nested_file_moves"]:
        if item["confidence"] != "high" and not include_medium_confidence:
            continue
        old_identifier = Path(item["old"]).with_suffix("").as_posix()
        intermediate = old_identifier
        for directory in data["directory_moves"]:
            if old_identifier.startswith(directory["old"] + "/"):
                intermediate = directory["new"] + old_identifier[len(directory["old"]):]
                break
        replacements.append(
            (intermediate, Path(item["new"]).with_suffix("").as_posix())
        )

    collisions = [
        destination.relative_to(root).as_posix()
        for destination in moves.values()
        if destination.exists()
    ]
    if collisions:
        raise RuntimeError(f"Destination collisions: {collisions}")

    changed: dict[Path, str] = {}
    subcategory = re.compile(
        r"^(subcategory:\s*)principals(\s*)$",
        re.IGNORECASE | re.MULTILINE,
    )
    tag = re.compile(
        r"^(\s*-\s*)principals(\s*)$",
        re.IGNORECASE | re.MULTILINE,
    )
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if markdown in moves:
            updated = subcategory.sub(r"\1principles\2", updated)
            updated = tag.sub(r"\1principles\2", updated)
        if updated != text:
            changed[markdown] = updated

    affected = set(moves) | set(changed)
    typer.echo(f"Directory moves       : {len(data['directory_moves'])}")
    typer.echo(f"Source files to move  : {len(moves)}")
    typer.echo(f"Files to rewrite      : {len(changed)}")
    typer.echo(f"Files to back up      : {len(affected)}")
    typer.echo(
        "Partnership index name: "
        + ("included" if include_medium_confidence else "excluded")
    )

    if not apply:
        typer.echo("No changes made. Pass --apply to confirm this migration.")
        return

    backup.mkdir(parents=True, exist_ok=True)
    for source in sorted(affected):
        destination = backup / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for source, destination in sorted(moves.items()):
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)

    for original, updated in changed.items():
        _atomic_write(moves.get(original, original), updated)

    for item in data["directory_moves"]:
        old = root / Path(item["old"])
        if old.exists():
            for directory in sorted(
                (path for path in old.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                directory.rmdir()
            old.rmdir()

    typer.echo(f"Files moved            : {len(moves)}")
    typer.echo(f"Files rewritten        : {len(changed)}")
    typer.echo(f"Backup directory       : {backup}")
