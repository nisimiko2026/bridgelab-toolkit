from __future__ import annotations

import json
import os
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


def _selected(plan: Path, include_medium_confidence: bool) -> list[dict]:
    allowed = {"high"}
    if include_medium_confidence:
        allowed.add("medium")
    data = json.loads(plan.read_text(encoding="utf-8"))
    return [
        item for item in data.get("direct_repairs", [])
        if item.get("confidence") in allowed
    ]


def _file_moves(root: Path, proposals: list[dict]) -> dict[Path, Path]:
    moves: dict[Path, Path] = {}
    for proposal in proposals:
        old = root / Path(proposal["old"])
        new = root / Path(proposal["new"])
        if proposal["kind"] == "directory_and_nested_index":
            nested = proposal["additional_rename"]
            for source in old.rglob("*.md"):
                name = nested["new"] if source.name == nested["old"] else source.name
                moves[source] = new / source.relative_to(old).with_name(name)
        elif proposal["kind"] == "directory":
            for source in old.rglob("*.md"):
                moves[source] = new / source.relative_to(old)
        else:
            moves[old] = new
    return moves


def run(
    root: Path,
    plan: Path,
    backup: Path,
    apply: bool,
    include_medium_confidence: bool = False,
) -> None:
    proposals = _selected(plan, include_medium_confidence)
    moves = _file_moves(root, proposals)
    replacements: list[tuple[str, str]] = []
    for proposal in proposals:
        replacements.append((proposal["old"].removesuffix(".md"), proposal["new"].removesuffix(".md")))
        nested = proposal.get("additional_rename")
        if nested:
            new_directory = proposal["new"]
            replacements.append(
                (
                    f"{new_directory}/{nested['old'].removesuffix('.md')}",
                    f"{new_directory}/{nested['new'].removesuffix('.md')}",
                )
            )
    replacements.append(("Kaplan Rubens Hand Hvaluation", "Kaplan Rubens Hand Evaluation"))

    missing = [str(path.relative_to(root)) for path in moves if not path.is_file()]
    collisions = [
        str(path.relative_to(root))
        for path in moves.values()
        if path.exists() and path not in moves
    ]
    if missing or collisions:
        raise RuntimeError(
            f"Unsafe spelling repair state; missing={missing}, collisions={collisions}"
        )

    changed: dict[Path, str] = {}
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            changed[markdown] = updated

    affected = set(moves) | set(changed)
    typer.echo(f"Repair groups selected: {len(proposals)}")
    typer.echo(f"Source files to move : {len(moves)}")
    typer.echo(f"Files to rewrite     : {len(changed)}")
    typer.echo(f"Files to back up     : {len(affected)}")

    if not apply:
        typer.echo("No changes made. Pass --apply to confirm this spelling batch.")
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
        target = moves.get(original, original)
        _atomic_write(target, updated)

    old_directories = sorted(
        {
            root / Path(item["old"])
            for item in proposals
            if item["kind"].startswith("directory")
        },
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in old_directories:
        directory.rmdir()

    typer.echo(f"Files moved          : {len(moves)}")
    typer.echo(f"Files rewritten      : {len(changed)}")
    typer.echo(f"Backup directory     : {backup}")
