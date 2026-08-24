"""Safe Phase 3A Batch 3.3y Invitational Bidding category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


ARTICLE = "bidding/natural-bids/responses/limit-raise.md"
REQUIRED_TAGS = [
    "acol",
    "forcing",
    "invitational bidding",
    "jacoby",
    "natural-bids",
    "opening",
    "precision",
    "sayc",
    "slam",
    "standard american",
    "support",
]
REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3Y = {ARTICLE: REQUIRED_TAGS}
OBSERVED_CATEGORY = "Invitational Bidding"
PROPOSED_CATEGORY = "bidding"
REQUIRED_SUBCATEGORY = "natural-bids"


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


def build_category_normalization_batch3_3y_report(root: Path) -> CategoryNormalizationReport:
    """Build the exact reviewed one-file family entirely in memory."""
    root = root.resolve()
    if root.name != "knowledge":
        raise RuntimeError(
            f"Refusing non-canonical knowledge root (expected directory named 'knowledge'): {root}"
        )
    observed_family = _observed_family(root)
    reviewed_family = set(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3Y)
    if observed_family not in (reviewed_family, set()):
        missing = sorted(reviewed_family - observed_family)
        extra = sorted(observed_family - reviewed_family)
        raise RuntimeError(
            "Reviewed Invitational Bidding family completeness mismatch: "
            f"missing={missing!r}, extra={extra!r}"
        )

    path = root / ARTICLE
    if not path.is_file():
        raise RuntimeError(f"Reviewed category file is missing: {ARTICLE}")
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {ARTICLE}") from error
    front_match = FRONT_MATTER_RE.match(text)
    if not front_match:
        raise RuntimeError(f"Missing or malformed front matter: {ARTICLE}")
    front_matter = front_match.group(0)
    data = _load_front_matter(front_matter, ARTICLE)
    if data is None:
        raise RuntimeError(f"Empty front matter: {ARTICLE}")
    if data.get("subcategory") != REQUIRED_SUBCATEGORY:
        raise RuntimeError(
            f"Reviewed frozen-subcategory precondition mismatch: {ARTICLE}: "
            f"expected {REQUIRED_SUBCATEGORY!r}, observed {data.get('subcategory')!r}"
        )
    tags = data.get("tags")
    if (
        tags != REQUIRED_TAGS
        or "invitational bidding" not in REQUIRED_TAGS
        or "natural-bids" not in REQUIRED_TAGS
        or PROPOSED_CATEGORY in REQUIRED_TAGS
    ):
        raise RuntimeError(
            f"Reviewed frozen-tag precondition mismatch: {ARTICLE}: expected exact "
            f"retained tags {REQUIRED_TAGS!r} with semantic tags retained and no broad "
            f"'bidding' tag, observed {tags!r}"
        )
    current = data.get("category")
    if current == PROPOSED_CATEGORY:
        _require_exact_category_line(front_matter, PROPOSED_CATEGORY)
        return CategoryNormalizationReport(1, ())
    if current != OBSERVED_CATEGORY:
        raise RuntimeError(
            f"Reviewed category precondition mismatch: {ARTICLE}: expected "
            f"{OBSERVED_CATEGORY!r}, observed {current!r}"
        )
    updated_front = _replace_exact_category(front_matter)
    updated_data = _load_front_matter(updated_front, ARTICLE)
    if updated_data is None or updated_data.get("tags") != tags:
        raise RuntimeError(f"Reviewed frozen-tag mutation detected: {ARTICLE}")
    if updated_data.get("subcategory") != REQUIRED_SUBCATEGORY:
        raise RuntimeError(f"Reviewed frozen-subcategory mutation detected: {ARTICLE}")
    updated = (updated_front + text[front_match.end() :]).encode("utf-8")
    expected = original.replace(
        f"category: {OBSERVED_CATEGORY}".encode(),
        f"category: {PROPOSED_CATEGORY}".encode(),
        1,
    )
    if updated != expected:
        raise RuntimeError(f"Non-category byte mutation detected: {ARTICLE}")
    return CategoryNormalizationReport(
        1, (CategoryNormalizationAction(ARTICLE, path, original, updated),)
    )


def apply_category_normalization_batch3_3y_report(
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
            raise RuntimeError(f"Refusing category repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(f"Reviewed complete-byte precondition mismatch: {action.article}")
    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)
    for action in report.actions:
        _atomic_write(action.path, action.updated)


def _observed_family(root: Path) -> set[str]:
    observed = set()
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


def _require_exact_category_line(front_matter: str, value: str) -> re.Match[str]:
    pattern = re.compile(rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front_matter))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {ARTICLE}: expected one exact "
            f"category: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str) -> str:
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
