"""Safe Phase 3A Batch 3.3u Convention Card normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3U = {
    "bidding/conventions/competitive/good-bad-2nt.md": [
        "competitive",
        "convention card",
        "conventions",
        "double",
        "forcing",
        "lebensohl",
        "notrump",
        "relay",
        "response",
        "support",
        "takeout",
        "wolff signoff",
    ],
    "bidding/conventions/competitive/jordan-2nt.md": [
        "competitive",
        "convention card",
        "conventions",
        "double",
        "forcing",
        "jacoby",
        "negative",
        "opening",
        "redouble",
        "response",
        "slam",
        "support",
        "takeout",
    ],
    "bidding/conventions/competitive/lionel.md": [
        "cappelletti",
        "competitive",
        "convention card",
        "conventions",
        "dont",
        "double",
        "notrump",
        "opening",
        "relay",
    ],
    "bidding/conventions/competitive/scrambling-2nt.md": [
        "competitive",
        "convention card",
        "conventions",
        "double",
        "lebensohl",
        "notrump",
        "relay",
        "support",
        "takeout",
    ],
    "bidding/conventions/doubles/rosenkranz-double.md": [
        "competitive",
        "convention card",
        "conventions",
        "double",
        "lead",
        "negative",
        "opening",
        "overcall",
        "rebid",
        "redouble",
        "signal",
        "support",
        "takeout",
    ],
    "bidding/conventions/doubles/rosenkranz-redouble.md": [
        "competitive",
        "convention card",
        "conventions",
        "double",
        "lead",
        "negative",
        "opening",
        "overcall",
        "redouble",
        "support",
    ],
    "bidding/conventions/responses/transfer-walsh.md": [
        "convention card",
        "conventions",
        "jacoby",
        "notrump",
        "opening",
        "response",
        "slam",
        "stayman",
        "transfer",
        "walsh",
    ],
    "bidding/conventions/responses/walsh.md": [
        "convention card",
        "conventions",
        "forcing",
        "opening",
        "precision",
        "rebid",
        "response",
        "standard american",
        "support",
        "two over one",
        "walsh",
    ],
    "bidding/conventions/responses/wolff-signoff.md": [
        "competitive",
        "convention card",
        "conventions",
        "forcing",
        "lebensohl",
        "rebid",
        "relay",
        "response",
        "slam",
        "two over one",
        "wolff signoff",
    ],
    "bidding/conventions/responses/xyz.md": [
        "convention card",
        "conventions",
        "forcing",
        "notrump",
        "rebid",
        "relay",
        "stayman",
        "two over one",
        "walsh",
    ],
    "bidding/conventions/slam-conventions/ace-asking-bid.md": [
        "blackwood",
        "convention card",
        "conventions",
        "gerber",
        "notrump",
        "response",
        "slam",
    ],
    "bidding/conventions/slam-conventions/control-asking-bid.md": [
        "blackwood",
        "convention card",
        "conventions",
        "precision",
        "relay",
        "response",
        "slam",
        "strong club",
    ],
    "bidding/conventions/slam-conventions/minorwood.md": [
        "blackwood",
        "convention card",
        "conventions",
        "response",
        "slam",
    ],
    "bidding/conventions/slam-conventions/specific-king-ask.md": [
        "blackwood",
        "convention card",
        "conventions",
        "precision",
        "relay",
        "response",
        "slam",
    ],
    "bidding/conventions/slam-conventions/spiral-scan.md": [
        "blackwood",
        "convention card",
        "conventions",
        "response",
        "slam",
    ],
    "bidding/conventions/slam-conventions/trump-asking-bid.md": [
        "blackwood",
        "convention card",
        "conventions",
        "precision",
        "relay",
        "response",
        "slam",
        "strong club",
        "support",
    ],
    "bidding/conventions/transfers/transfer-lebensohl.md": [
        "cappelletti",
        "competitive",
        "convention card",
        "conventions",
        "dont",
        "double",
        "forcing",
        "lebensohl",
        "multi",
        "negative",
        "response",
        "stayman",
        "transfer",
    ],
}
OBSERVED_CATEGORY = "Convention Card"
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


def build_category_normalization_batch3_3u_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed seventeen-file family entirely in memory."""
    root = root.resolve()
    observed_family = _observed_family(root)
    reviewed_family = set(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3U)
    if observed_family not in (reviewed_family, set()):
        missing = sorted(reviewed_family - observed_family)
        extra = sorted(observed_family - reviewed_family)
        raise RuntimeError(
            f"Reviewed Convention Card family completeness mismatch: missing={missing!r}, extra={extra!r}"
        )
    actions: list[CategoryNormalizationAction] = []
    for article, required_tags in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3U.items()
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
                f"Reviewed frozen-subcategory precondition mismatch: {article}: expected {REQUIRED_SUBCATEGORY!r}, observed {data.get('subcategory')!r}"
            )
        tags = data.get("tags")
        if (
            tags != required_tags
            or "convention card" not in required_tags
            or "conventions" not in required_tags
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
        len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3U), tuple(actions)
    )


def apply_category_normalization_batch3_3u_report(
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


def _observed_family(root: Path) -> set[str]:
    observed: set[str] = set()
    for path in root.rglob("*.md"):
        article = path.relative_to(root).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        match = FRONT_MATTER_RE.match(text)
        if not match:
            continue
        data = _load_front_matter(match.group(0), article)
        if data is not None and data.get("category") == OBSERVED_CATEGORY:
            observed.add(article)
    return observed


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
