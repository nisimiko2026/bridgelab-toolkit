"""Safely apply approved metadata repair proposals."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.repository import Repository
from enrichment.writer import MetadataWriter


@dataclass(frozen=True, slots=True)
class ApplyResult:
    applied: int
    skipped: int
    backed_up: int


def apply_repair_plan(
    root: Path,
    plan_path: Path,
    backup_root: Path,
    allowed_confidence: set[str],
) -> ApplyResult:
    """Apply non-empty proposals only to fields that remain missing."""

    data = json.loads(plan_path.read_text(encoding="utf-8"))
    articles = {
        article.relative_path.as_posix(): article
        for article in Repository(root).build()
    }
    selected: dict[str, dict[str, str]] = {}
    skipped = 0

    for proposal in data.get("proposals", []):
        if (
            proposal.get("confidence") not in allowed_confidence
            or not proposal.get("proposed")
            or proposal.get("field") not in {"description", "difficulty"}
        ):
            skipped += 1
            continue
        selected.setdefault(proposal["article"], {})[proposal["field"]] = proposal[
            "proposed"
        ]

    writer = MetadataWriter()
    applied = 0
    backed_up = 0

    for relative_path, fields in sorted(selected.items()):
        article = articles.get(relative_path)
        if article is None or article.metadata_error:
            skipped += len(fields)
            continue

        pending = {
            field: value
            for field, value in fields.items()
            if not getattr(article.metadata, field)
        }
        skipped += len(fields) - len(pending)
        if not pending:
            continue

        backup = backup_root / article.relative_path
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(article.path, backup)
        backed_up += 1

        for field, value in pending.items():
            setattr(article.metadata, field, value)

        if writer.write(article):
            applied += len(pending)
        else:
            skipped += len(pending)

    return ApplyResult(applied=applied, skipped=skipped, backed_up=backed_up)
