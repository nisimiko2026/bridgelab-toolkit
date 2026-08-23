"""Safe Phase 3A Batch 3.3p core Conventions normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3P = {
    "bidding/conventions/doubles/maximal-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "double",
            "negative",
            "slam",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/negative-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "negative",
            "notrump",
            "opening",
            "overcall",
            "rebid",
            "slam",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/penalty-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "double",
            "forcing",
            "lead",
            "negative",
            "notrump",
            "opening",
            "slam",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/re-opening-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "negative",
            "opening",
            "overcall",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/responsive-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "negative",
            "notrump",
            "opening",
            "overcall",
            "rebid",
            "slam",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/support-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "negative",
            "notrump",
            "opening",
            "rebid",
            "redouble",
            "slam",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/doubles/take-out-double.md": (
        "Competitive Bidding",
        [
            "competitive",
            "competitive bidding",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "negative",
            "notrump",
            "opening",
            "overcall",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/opening-bids/ekren.md": (
        "Opening Conventions",
        [
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "flannery",
            "multi",
            "notrump",
            "opening",
            "opening conventions",
            "preempt",
            "redouble",
            "response",
            "slam",
            "support",
        ],
    ),
    "bidding/conventions/opening-bids/flannery.md": (
        "Opening Conventions",
        [
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "flannery",
            "forcing",
            "negative",
            "notrump",
            "opening",
            "opening conventions",
            "rebid",
            "redouble",
            "response",
            "slam",
            "takeout",
        ],
    ),
    "bidding/conventions/opening-bids/namyats.md": (
        "Opening Conventions",
        [
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "lead",
            "namyats",
            "opening",
            "opening conventions",
            "preempt",
            "redouble",
            "relay",
            "slam",
            "stayman",
            "support",
            "transfer",
        ],
    ),
    "bidding/conventions/opening-bids/two-diamond-multi.md": (
        "Opening Conventions",
        [
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "flannery",
            "multi",
            "opening",
            "opening conventions",
            "redouble",
            "relay",
            "response",
            "slam",
        ],
    ),
    "bidding/conventions/slam-conventions/blackwood.md": (
        "Slam Conventions",
        [
            "blackwood",
            "competitive",
            "conventions",
            "double",
            "forcing",
            "gerber",
            "jacoby",
            "notrump",
            "redouble",
            "response",
            "slam",
            "slam conventions",
        ],
    ),
    "bidding/conventions/slam-conventions/cue-bidding.md": (
        "Slam Conventions",
        [
            "acol",
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "forcing",
            "gerber",
            "lead",
            "opening",
            "precision",
            "sayc",
            "slam",
            "slam conventions",
            "standard american",
        ],
    ),
    "bidding/conventions/slam-conventions/dopi-ropi.md": (
        "Slam Conventions",
        [
            "blackwood",
            "competitive",
            "conventions",
            "double",
            "gerber",
            "redouble",
            "response",
            "slam",
            "slam conventions",
        ],
    ),
    "bidding/conventions/slam-conventions/gerber.md": (
        "Slam Conventions",
        [
            "blackwood",
            "competitive",
            "conventions",
            "double",
            "gerber",
            "jacoby",
            "notrump",
            "opening",
            "redouble",
            "response",
            "slam",
            "slam conventions",
            "stayman",
        ],
    ),
    "bidding/conventions/slam-conventions/roman-key-card-blackwood.md": (
        "Slam Conventions",
        [
            "acol",
            "blackwood",
            "competitive",
            "conventions",
            "double",
            "gerber",
            "jacoby",
            "notrump",
            "precision",
            "redouble",
            "response",
            "sayc",
            "slam",
            "slam conventions",
            "standard american",
        ],
    ),
}
OBSERVED_CATEGORY = "Conventions"
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


def build_category_normalization_batch3_3p_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed sixteen-file batch entirely in memory."""
    root = root.resolve()
    actions: list[CategoryNormalizationAction] = []
    for article, (required_subcategory, required_tags) in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3P.items()
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
        if data.get("subcategory") != required_subcategory:
            raise RuntimeError(
                f"Reviewed frozen-subcategory precondition mismatch: {article}: expected {required_subcategory!r}, observed {data.get('subcategory')!r}"
            )
        tags = data.get("tags")
        structural_tag = required_subcategory.lower()
        if (
            tags != required_tags
            or "conventions" not in required_tags
            or structural_tag not in required_tags
            or PROPOSED_CATEGORY in required_tags
        ):
            raise RuntimeError(
                f"Reviewed frozen-tag precondition mismatch: {article}: expected exact retained tags {required_tags!r} and no broad 'bidding' tag, observed {tags!r}"
            )
        current = data.get("category")
        if current == PROPOSED_CATEGORY:
            _require_exact_category_line(front_matter, PROPOSED_CATEGORY, article)
            continue
        if current != OBSERVED_CATEGORY:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: expected {OBSERVED_CATEGORY!r}, observed {current!r}"
            )
        updated_front = _replace_exact_category(front_matter, article)
        updated_data = _load_front_matter(updated_front, article)
        if updated_data is None or updated_data.get("tags") != tags:
            raise RuntimeError(f"Reviewed frozen-tag mutation detected: {article}")
        if updated_data.get("subcategory") != required_subcategory:
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
        len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3P), tuple(actions)
    )


def apply_category_normalization_batch3_3p_report(
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
            f"Unsafe category line precondition in {article}: expected one exact category: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str, article: str) -> str:
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY, article)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
