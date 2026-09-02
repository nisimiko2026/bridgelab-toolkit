"""Safe Phase 3A Batch 3.3n competitive Conventions normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3N = {
    "bidding/conventions/competitive/balancing-notrump.md": (
        "Balancing",
        [
            "acol",
            "balancing",
            "competitive",
            "conventions",
            "double",
            "gerber",
            "jacoby",
            "lebensohl",
            "negative",
            "notrump",
            "opening",
            "overcall",
            "precision",
            "sayc",
            "standard american",
            "stayman",
            "takeout",
        ],
    ),
    "bidding/conventions/competitive/aspro.md": (
        "Defenses to Notrump",
        [
            "blackwood",
            "cappelletti",
            "competitive",
            "conventions",
            "cue bid",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "preempt",
            "redouble",
            "relay",
            "slam",
        ],
    ),
    "bidding/conventions/competitive/brozel.md": (
        "Defenses to Notrump",
        [
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "redouble",
            "relay",
            "response",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/cappelletti.md": (
        "Defenses to Notrump",
        [
            "acol",
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "precision",
            "preempt",
            "redouble",
            "relay",
            "response",
            "sayc",
            "standard american",
            "strong club",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/dont.md": (
        "Defenses to Notrump",
        [
            "acol",
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "precision",
            "redouble",
            "relay",
            "response",
            "sayc",
            "standard american",
            "stayman",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/hamilton.md": (
        "Defenses to Notrump",
        [
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "notrump",
            "opening",
            "redouble",
            "relay",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/landy.md": (
        "Defenses to Notrump",
        [
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "lead",
            "multi",
            "notrump",
            "opening",
            "overcall",
            "redouble",
            "relay",
            "response",
            "support",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/meckwell.md": (
        "Defenses to Notrump",
        [
            "blackwood",
            "cappelletti",
            "competitive",
            "conventions",
            "cue bid",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "precision",
            "preempt",
            "redouble",
            "relay",
            "slam",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/multi-landy.md": (
        "Defenses to Notrump",
        [
            "cappelletti",
            "competitive",
            "conventions",
            "defenses to notrump",
            "dont",
            "double",
            "multi",
            "notrump",
            "opening",
            "redouble",
            "relay",
            "response",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/ghestem.md": (
        "Overcalls",
        [
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "notrump",
            "opening",
            "overcall",
            "overcalls",
            "precision",
            "redouble",
            "slam",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/competitive/michaels-cue-bid.md": (
        "Overcalls",
        [
            "acol",
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "negative",
            "notrump",
            "opening",
            "overcall",
            "overcalls",
            "precision",
            "response",
            "sayc",
            "slam",
            "standard american",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/competitive/unusual-2nt.md": (
        "Overcalls",
        [
            "acol",
            "blackwood",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "notrump",
            "opening",
            "overcall",
            "overcalls",
            "precision",
            "redouble",
            "sayc",
            "slam",
            "standard american",
            "support",
            "takeout",
        ],
    ),
    "bidding/conventions/competitive/weak-jump-overcall.md": (
        "Overcalls",
        [
            "acol",
            "competitive",
            "conventions",
            "cue bid",
            "double",
            "forcing",
            "lead",
            "notrump",
            "opening",
            "overcall",
            "overcalls",
            "precision",
            "preempt",
            "response",
            "sayc",
            "standard american",
            "support",
            "takeout",
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


def build_category_normalization_batch3_3n_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed thirteen-file batch entirely in memory."""
    root = root.resolve()
    actions: list[CategoryNormalizationAction] = []
    for article, (required_subcategory, required_tags) in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3N.items()
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
        len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3N), tuple(actions)
    )


def apply_category_normalization_batch3_3n_report(
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
