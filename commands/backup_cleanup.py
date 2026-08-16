"""Safely enforce retention for dated repair backup directories."""

from __future__ import annotations

import re
import shutil
from datetime import date, timedelta
from pathlib import Path

import typer


DATED_BACKUP = re.compile(r"^.+-(?P<date>\d{8})-(?P<sequence>\d{2})$")


def expired_backups(root: Path, retention_days: int, today: date | None = None) -> list[Path]:
    """Return dated child directories older than the retention window."""
    root = root.resolve()
    cutoff = (today or date.today()) - timedelta(days=retention_days)
    expired: list[Path] = []
    for candidate in root.iterdir():
        if not candidate.is_dir() or candidate.is_symlink():
            continue
        match = DATED_BACKUP.fullmatch(candidate.name)
        if not match:
            continue
        backup_date = date.fromisoformat(
            f"{match['date'][:4]}-{match['date'][4:6]}-{match['date'][6:]}"
        )
        if backup_date < cutoff:
            expired.append(candidate.resolve())
    return sorted(expired)


def run(root: Path, retention_days: int, apply: bool, today: date | None = None) -> None:
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"Backup root is not a directory: {root}")
    expired = expired_backups(root, retention_days, today=today)
    typer.echo(f"Retention period : {retention_days} days")
    typer.echo(f"Expired backups  : {len(expired)}")
    for path in expired:
        typer.echo(f"  {path.name}")
    if not apply:
        typer.echo("No backups removed. Pass --apply to remove expired dated backups.")
        return
    for path in expired:
        if path.parent != root:
            raise RuntimeError(f"Refusing cleanup outside backup root: {path}")
        shutil.rmtree(path)
    typer.echo(f"Backups removed  : {len(expired)}")
