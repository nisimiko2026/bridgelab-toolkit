from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.repository import Repository
from enrichment.writer import MetadataWriter

from .graph import KnowledgeGraph


@dataclass(frozen=True, slots=True)
class OrphanApplyResult:
    applied: int
    skipped: int
    backed_up: int
    parent_indexes: int


def selected_proposals(
    plan_path: Path,
    allowed_confidence: set[str],
) -> list[dict[str, object]]:
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    return [
        item for item in data.get("proposals", [])
        if item.get("confidence") in allowed_confidence
        and item.get("parent_index")
        and item.get("target")
    ]


def apply_orphan_plan(
    root: Path,
    plan_path: Path,
    backup_root: Path,
    allowed_confidence: set[str],
) -> OrphanApplyResult:
    """Add approved orphan targets to their proposed parent indexes."""

    articles = Repository(root).build()
    by_id = {article.id.casefold(): article for article in articles}
    graph = KnowledgeGraph(articles)
    grouped: dict[str, list[str]] = {}
    skipped = 0

    for proposal in selected_proposals(plan_path, allowed_confidence):
        parent_id = str(proposal["parent_index"]).casefold()
        target_id = str(proposal["target"]).casefold()
        parent = by_id.get(parent_id)
        target = by_id.get(target_id)

        if (
            parent is None
            or target is None
            or parent.metadata_error
            or target_id == parent_id
            or graph.incoming(target)
        ):
            skipped += 1
            continue
        grouped.setdefault(parent_id, []).append(target.id)

    writer = MetadataWriter()
    applied = 0
    backed_up = 0
    changed_parents = 0

    for parent_id, targets in sorted(grouped.items()):
        parent = by_id[parent_id]
        existing = {item.casefold() for item in parent.metadata.references}
        additions = sorted(
            {target for target in targets if target.casefold() not in existing}
        )
        skipped += len(targets) - len(additions)
        if not additions:
            continue

        backup = backup_root / parent.relative_path
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(parent.path, backup)
        backed_up += 1

        parent.metadata.references.extend(additions)
        if writer.write(parent):
            applied += len(additions)
            changed_parents += 1
        else:
            skipped += len(additions)

    return OrphanApplyResult(
        applied=applied,
        skipped=skipped,
        backed_up=backed_up,
        parent_indexes=changed_parents,
    )
