"""Safe Phase 3A Batch 3.3m response-family Convention normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3M = {
    "bidding/conventions/responses/2nt-inquiry-after-multi-two-diamond.md": [
        "acol",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "multi",
        "opening",
        "precision",
        "rebid",
        "relay",
        "response",
        "slam",
    ],
    "bidding/conventions/responses/2nt-inquiry-over-weak-2.md": [
        "acol",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "notrump",
        "opening",
        "precision",
        "rebid",
        "response",
        "sayc",
        "slam",
        "standard american",
    ],
    "bidding/conventions/responses/inverted-minors.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "cue bid",
        "double",
        "forcing",
        "jacoby",
        "notrump",
        "opening",
        "precision",
        "rebid",
        "relay",
        "response",
        "sayc",
        "slam",
        "standard american",
        "stayman",
        "strong club",
        "support",
    ],
    "bidding/conventions/responses/lebensohl-after-1nt-overcall.md": [
        "cappelletti",
        "competitive",
        "convention",
        "conventions",
        "cue bid",
        "forcing",
        "lebensohl",
        "notrump",
        "opening",
        "overcall",
        "precision",
        "relay",
        "sayc",
        "slam",
        "standard american",
        "transfer",
    ],
    "bidding/conventions/responses/mixed-raise.md": [
        "competitive",
        "convention",
        "conventions",
        "cue bid",
        "double",
        "forcing",
        "jacoby",
        "negative",
        "opening",
        "precision",
        "response",
        "sayc",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/passed-hand-bergen.md": [
        "acol",
        "competitive",
        "convention",
        "conventions",
        "drury",
        "forcing",
        "jacoby",
        "opening",
        "precision",
        "rebid",
        "response",
        "sayc",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/passed-hand-jacoby.md": [
        "acol",
        "convention",
        "conventions",
        "drury",
        "forcing",
        "jacoby",
        "opening",
        "precision",
        "rebid",
        "sayc",
        "slam",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/passed-hand-splinter.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "cue bid",
        "drury",
        "forcing",
        "jacoby",
        "opening",
        "precision",
        "response",
        "sayc",
        "slam",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/response-to-gambling-3nt.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "lead",
        "notrump",
        "opening",
        "precision",
        "relay",
        "response",
        "sayc",
        "slam",
        "standard american",
        "support",
        "transfer",
    ],
    "bidding/conventions/responses/reverse-drury.md": [
        "acol",
        "competitive",
        "convention",
        "conventions",
        "cue bid",
        "drury",
        "jacoby",
        "opening",
        "precision",
        "response",
        "sayc",
        "slam",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/soloway.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "jacoby",
        "opening",
        "precision",
        "rebid",
        "response",
        "sayc",
        "slam",
        "standard american",
        "support",
    ],
    "bidding/conventions/responses/two-way-checkback.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "notrump",
        "opening",
        "precision",
        "rebid",
        "relay",
        "response",
        "sayc",
        "slam",
        "standard american",
        "stayman",
        "support",
    ],
    "bidding/conventions/responses/two-way-new-minor-forcing.md": [
        "acol",
        "blackwood",
        "competitive",
        "convention",
        "conventions",
        "forcing",
        "notrump",
        "opening",
        "precision",
        "relay",
        "response",
        "sayc",
        "slam",
        "standard american",
        "stayman",
        "support",
    ],
}
OBSERVED_CATEGORY = "Convention"
PROPOSED_CATEGORY = "bidding"
REQUIRED_SUBCATEGORY = "conventions"


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


def build_category_normalization_batch3_3m_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed thirteen-file batch entirely in memory."""

    root = root.resolve()
    actions: list[CategoryNormalizationAction] = []
    for article, required_tags in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3M.items()
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
        if data.get("subcategory") != REQUIRED_SUBCATEGORY:
            raise RuntimeError(
                f"Reviewed frozen-subcategory precondition mismatch: {article}: "
                f"expected {REQUIRED_SUBCATEGORY!r}, observed {data.get('subcategory')!r}"
            )
        tags = data.get("tags")
        if (
            tags != required_tags
            or "convention" not in required_tags
            or "conventions" not in required_tags
            or PROPOSED_CATEGORY in required_tags
        ):
            raise RuntimeError(
                f"Reviewed frozen-tag precondition mismatch: {article}: expected "
                f"exact retained tags {required_tags!r} and no broad 'bidding' tag, "
                f"observed {tags!r}"
            )
        current = data.get("category")
        if current == PROPOSED_CATEGORY:
            _require_exact_category_line(front_matter, PROPOSED_CATEGORY, article)
            continue
        if current != OBSERVED_CATEGORY:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: "
                f"expected {OBSERVED_CATEGORY!r}, observed {current!r}"
            )
        updated_front = _replace_exact_category(front_matter, article)
        updated_data = _load_front_matter(updated_front, article)
        if updated_data is None or updated_data.get("tags") != tags:
            raise RuntimeError(f"Reviewed frozen-tag mutation detected: {article}")
        if updated_data.get("subcategory") != REQUIRED_SUBCATEGORY:
            raise RuntimeError(
                f"Reviewed frozen-subcategory mutation detected: {article}"
            )
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        if updated == original:
            raise RuntimeError(
                f"Reviewed category repair produced no change: {article}"
            )
        actions.append(CategoryNormalizationAction(article, path, original, updated))
    return CategoryNormalizationReport(
        selected_files=len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3M),
        actions=tuple(actions),
    )


def apply_category_normalization_batch3_3m_report(
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
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY, article)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
