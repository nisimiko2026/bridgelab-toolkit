"""Safe Phase 3A Batch 3.3a category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_ARTICLE = "bidding/conventions/opening-bids/gambling-3nt.md"
OBSERVED_CATEGORY = "Convention"
PROPOSED_CATEGORY = "bidding"


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


def build_category_normalization_batch3_3a_report(root: Path) -> CategoryNormalizationReport:
    """Build the exact reviewed single-file batch entirely in memory."""

    root = root.resolve()
    path = root / Path(REVIEWED_ARTICLE)
    if not path.is_file():
        raise RuntimeError(f"Reviewed category file is missing: {REVIEWED_ARTICLE}")
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {REVIEWED_ARTICLE}") from error
    front_match = FRONT_MATTER_RE.match(text)
    if not front_match:
        raise RuntimeError(f"Missing or malformed front matter: {REVIEWED_ARTICLE}")
    front_matter = front_match.group(0)
    data = _load_front_matter(front_matter, REVIEWED_ARTICLE)
    if data is None:
        raise RuntimeError(f"Empty front matter: {REVIEWED_ARTICLE}")

    current = data.get("category")
    if current == PROPOSED_CATEGORY:
        _require_exact_category_line(front_matter, PROPOSED_CATEGORY)
        return CategoryNormalizationReport(selected_files=1, actions=())
    if current != OBSERVED_CATEGORY:
        raise RuntimeError(
            f"Reviewed category precondition mismatch: {REVIEWED_ARTICLE}: "
            f"expected {OBSERVED_CATEGORY!r}, observed {current!r}"
        )
    tags = data.get("tags")
    if not isinstance(tags, list) or "convention" not in tags or "bidding" in tags:
        raise RuntimeError(
            f"Reviewed frozen-tag precondition mismatch: {REVIEWED_ARTICLE}: "
            "expected existing 'convention' tag and no 'bidding' tag"
        )

    updated_front = _replace_exact_category(front_matter)
    updated = (updated_front + text[front_match.end() :]).encode("utf-8")
    if updated == original:
        raise RuntimeError(
            f"Reviewed category repair produced no change: {REVIEWED_ARTICLE}"
        )
    action = CategoryNormalizationAction(REVIEWED_ARTICLE, path, original, updated)
    return CategoryNormalizationReport(selected_files=1, actions=(action,))


def apply_category_normalization_batch3_3a_report(
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


def _require_exact_category_line(front_matter: str, value: str) -> re.Match[str]:
    pattern = re.compile(
        rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE
    )
    matches = list(pattern.finditer(front_matter))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {REVIEWED_ARTICLE}: expected one "
            f"exact category: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str) -> str:
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
