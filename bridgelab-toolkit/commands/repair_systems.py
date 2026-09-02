"""Apply the reviewed systems metadata removal plan safely."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import typer


SYSTEMS_BLOCK = re.compile(
    r"^systems:[ \t]*(?:\[[ \t]*\])?[ \t]*\r?\n"
    r"(?P<items>(?:[ \t]*-[ \t]+[^\r\n]+\r?\n)*)",
    re.MULTILINE,
)


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


def _values(items: str) -> list[str]:
    values: list[str] = []
    for line in items.splitlines():
        value = line.split("-", 1)[1].strip()
        values.append(value.strip("'\""))
    return values


def _updated_text(text: str, current: list[str], proposed: list[str]) -> str:
    matches = list(SYSTEMS_BLOCK.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one systems block, found {len(matches)}")
    match = matches[0]
    actual = _values(match.group("items"))
    if actual != current:
        raise RuntimeError(
            f"Systems metadata drift: expected {current!r}, found {actual!r}"
        )
    replacement = "systems: []\n"
    if proposed:
        replacement = "systems:\n" + "".join(
            f"  - {value}\n" for value in proposed
        )
    return text[: match.start()] + replacement + text[match.end() :]


def run(root: Path, plan: Path, backup: Path, apply: bool) -> None:
    data = json.loads(plan.read_text(encoding="utf-8"))
    proposals = data["proposals"]
    changed: dict[Path, str] = {}
    removal_count = 0

    for proposal in proposals:
        path = root / Path(proposal["path"])
        if not path.is_file():
            raise RuntimeError(f"Missing planned source: {path}")
        current = proposal["current_systems"]
        proposed = proposal["proposed_systems"]
        removal_count += len(proposal["remove"])
        text = path.read_text(encoding="utf-8")
        updated = _updated_text(text, current, proposed)
        if updated == text:
            raise RuntimeError(f"Plan produced no change: {path}")
        changed[path] = updated

    typer.echo(f"Files to update       : {len(changed)}")
    typer.echo(f"Assignments to remove: {removal_count}")
    typer.echo(f"Files to back up      : {len(changed)}")

    if not apply:
        typer.echo("No changes made. Pass --apply to confirm systems repair.")
        return

    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    for source in sorted(changed):
        destination = backup / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for path, updated in changed.items():
        _atomic_write(path, updated)

    typer.echo(f"Files updated         : {len(changed)}")
    typer.echo(f"Assignments removed   : {removal_count}")
    typer.echo(f"Backup directory      : {backup}")
