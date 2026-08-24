"""Safe Phase 3A Batch 3.3v defensive-method category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V = {
    "bidding/conventions/defensive-methods/defense-against-multi-2d.md": (
        "Convention Defense",
        [
            "cappelletti",
            "competitive",
            "convention defense",
            "conventions",
            "double",
            "flannery",
            "forcing",
            "lebensohl",
            "multi",
            "opening",
            "precision",
            "response",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/defensive-methods/woolsey-defense-to-multi.md": (
        "Convention Defense",
        [
            "competitive",
            "convention defense",
            "conventions",
            "crash",
            "cue bid",
            "double",
            "forcing",
            "lebensohl",
            "multi",
            "opening",
            "overcall",
            "response",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/defensive-methods/defense-against-precision.md": (
        "Defensive Methods",
        [
            "competitive",
            "conventions",
            "crash",
            "croc",
            "cue bid",
            "defensive methods",
            "double",
            "mathe",
            "multi",
            "negative",
            "opening",
            "precision",
            "relay",
            "standard american",
            "strong club",
            "support",
            "takeout",
            "transfer",
        ],
    ),
    "bidding/conventions/defensive-methods/defense-against-strong-club.md": (
        "Defensive Methods",
        [
            "cappelletti",
            "competitive",
            "conventions",
            "crash",
            "croc",
            "defensive methods",
            "dont",
            "double",
            "mathe",
            "multi",
            "notrump",
            "opening",
            "overcall",
            "precision",
            "relay",
            "strong club",
            "takeout",
            "transfer",
        ],
    ),
}
OBSERVED_CATEGORIES = frozenset({"Convention Defense", "Defensive Methods"})
PROPOSED_CATEGORY = "bidding"
REQUIRED_SUBCATEGORY = "conventions"


@dataclass(frozen=True, slots=True)
class CategoryNormalizationAction:
    article: str
    path: Path
    observed_category: str
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class CategoryNormalizationReport:
    selected_files: int
    actions: tuple[CategoryNormalizationAction, ...]


def build_category_normalization_batch3_3v_report(
    root: Path,
) -> CategoryNormalizationReport:
    """Build the exact reviewed four-file family entirely in memory."""
    root = root.resolve()
    reviewed_by_category = {
        category: {
            article
            for article, (
                observed,
                _,
            ) in REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V.items()
            if observed == category
        }
        for category in OBSERVED_CATEGORIES
    }
    observed_by_category = _observed_families(root)
    for category in OBSERVED_CATEGORIES:
        observed = observed_by_category[category]
        reviewed = reviewed_by_category[category]
        if observed not in (reviewed, set()):
            missing = sorted(reviewed - observed)
            extra = sorted(observed - reviewed)
            raise RuntimeError(
                f"Reviewed {category} family completeness mismatch: missing={missing!r}, extra={extra!r}"
            )

    actions: list[CategoryNormalizationAction] = []
    for article, (observed_category, required_tags) in sorted(
        REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V.items()
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
        semantic_tag = observed_category.casefold()
        tags = data.get("tags")
        if (
            tags != required_tags
            or semantic_tag not in required_tags
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
        if current != observed_category:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: expected {observed_category!r}, observed {current!r}"
            )
        updated_front = _replace_exact_category(
            front_matter, observed_category, article
        )
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
        actions.append(
            CategoryNormalizationAction(
                article, path, observed_category, original, updated
            )
        )
    return CategoryNormalizationReport(
        len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V), tuple(actions)
    )


def apply_category_normalization_batch3_3v_report(
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


def _observed_families(root: Path) -> dict[str, set[str]]:
    observed = {category: set() for category in OBSERVED_CATEGORIES}
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
        if data is not None and data.get("category") in OBSERVED_CATEGORIES:
            observed[data["category"]].add(article)
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


def _replace_exact_category(
    front_matter: str, observed_category: str, article: str
) -> str:
    match = _require_exact_category_line(front_matter, observed_category, article)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
