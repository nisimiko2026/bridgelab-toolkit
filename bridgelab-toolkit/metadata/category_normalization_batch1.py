"""Safe Phase 3A Batch 1 category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH1 = {
    "duplicates/duplicate-scoring.md": ("duplicates", "duplicate"),
    "duplicates/matchpoints-vs-imps.md": ("duplicates", "duplicate"),
    "references/bridge-glossary.md": ("references", "reference"),
    "references/bridge-laws-quick-reference.md": ("references", "reference"),
    "references/bridge-terminology.md": ("references", "reference"),
    "references/common-bridge-abbreviations.md": ("references", "reference"),
}


@dataclass(frozen=True, slots=True)
class CategoryNormalizationAction:
    article: str
    path: Path
    original: bytes
    updated: bytes
    current_category: str
    proposed_category: str
    retained_tag: str


@dataclass(frozen=True, slots=True)
class CategoryNormalizationReport:
    selected_files: int
    actions: tuple[CategoryNormalizationAction, ...]


def build_category_normalization_batch1_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed six-file batch entirely in memory."""

    root = root.resolve()
    actions: list[CategoryNormalizationAction] = []
    for article, (expected, proposed) in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH1.items()
    ):
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
        if current == proposed:
            _require_exact_category_line(front_matter, proposed, article)
            continue
        if current != expected:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: "
                f"expected {expected!r}, observed {current!r}"
            )
        if data.get("subcategory") != "":
            raise RuntimeError(
                f"Reviewed subcategory precondition mismatch: {article}: "
                "expected intentional empty scalar"
            )
        tags = data.get("tags")
        if not isinstance(tags, list) or expected not in tags:
            raise RuntimeError(
                f"Reviewed retained-tag precondition mismatch: {article}: "
                f"expected {expected!r}"
            )
        if proposed in tags:
            raise RuntimeError(
                f"Reviewed canonical-tag precondition mismatch: {article}: "
                f"unexpected {proposed!r} tag"
            )

        updated_front = _replace_exact_category(
            front_matter, expected, proposed, article
        )
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        if updated == original:
            raise RuntimeError(f"Reviewed category repair produced no change: {article}")
        actions.append(
            CategoryNormalizationAction(
                article=article,
                path=path,
                original=original,
                updated=updated,
                current_category=expected,
                proposed_category=proposed,
                retained_tag=expected,
            )
        )

    return CategoryNormalizationReport(
        selected_files=len(REVIEWED_CATEGORY_NORMALIZATION_BATCH1),
        actions=tuple(actions),
    )


def apply_category_normalization_batch1_report(
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


def _replace_exact_category(
    front_matter: str, current: str, proposed: str, article: str
) -> str:
    match = _require_exact_category_line(front_matter, current, article)
    return (
        front_matter[: match.start()]
        + f"category: {proposed}{match.group('ending')}"
        + front_matter[match.end() :]
    )
