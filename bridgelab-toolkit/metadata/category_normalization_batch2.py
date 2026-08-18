"""Safe Phase 3A Batch 2 category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH2 = {
    "play/declarer-play/general-techniques/general-techniques-index.md",
    "play/declarer-play/planning/preserving-entries.md",
    "play/declarer-play/planning/transportation.md",
    "play/defence/signaling/revolving-discards.md",
}


@dataclass(frozen=True, slots=True)
class CategoryNormalizationAction:
    article: str
    path: Path
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class CategoryNormalizationReport:
    selected_files: int
    actions: tuple[CategoryNormalizationAction, ...]


def build_category_normalization_batch2_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed four-file batch entirely in memory."""

    root = root.resolve()
    actions: list[CategoryNormalizationAction] = []
    for article in sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH2):
        path = root / Path(article)
        if not path.is_file():
            raise RuntimeError(f"Reviewed category file is missing: {article}")
        original = path.read_bytes()
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RuntimeError(f"Article is not valid UTF-8: {article}") from error
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front_matter = front_match.group(0)
        data = _load_front_matter(front_matter, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")

        current = data.get("category")
        if current == "play":
            _require_exact_category_line(front_matter, "play", article)
            continue
        if current != "Play":
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: "
                f"expected 'Play', observed {current!r}"
            )
        tags = data.get("tags")
        if not isinstance(tags, list) or "play" not in tags:
            raise RuntimeError(
                f"Reviewed canonical-tag precondition mismatch: {article}: "
                "expected existing 'play' tag"
            )

        updated_front = _replace_exact_category(front_matter, article)
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        if updated == original:
            raise RuntimeError(f"Reviewed category repair produced no change: {article}")
        actions.append(CategoryNormalizationAction(article, path, original, updated))

    return CategoryNormalizationReport(
        selected_files=len(REVIEWED_CATEGORY_NORMALIZATION_BATCH2),
        actions=tuple(actions),
    )


def apply_category_normalization_batch2_report(
    report: CategoryNormalizationReport, root: Path, backup: Path
) -> None:
    """Apply an unchanged report after preflighting the complete batch."""

    if not report.actions:
        return
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    root = root.resolve()
    for action in report.actions:
        try:
            action.path.resolve().relative_to(root)
        except ValueError as error:
            raise RuntimeError(
                f"Refusing category repair outside repository: {action.path}"
            ) from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {action.article}"
            )

    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)
    for action in report.actions:
        _atomic_write(action.path, action.updated)


def _require_exact_category_line(
    front_matter: str, value: str, article: str
) -> re.Match[str]:
    pattern = re.compile(
        rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE
    )
    matches = list(pattern.finditer(front_matter))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {article}: expected one exact "
            f"category: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str, article: str) -> str:
    match = _require_exact_category_line(front_matter, "Play", article)
    return (
        front_matter[: match.start()]
        + f"category: play{match.group('ending')}"
        + front_matter[match.end() :]
    )
