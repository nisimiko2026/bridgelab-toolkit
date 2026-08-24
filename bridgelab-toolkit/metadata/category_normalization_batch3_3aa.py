"""Safe Phase 3A Batch 3.3aa Hand Evaluation category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AA = {
    "bidding/principles/bidding-fundamentals/offensive-vs-defensive-values.md": [
        "competitive", "double", "hand evaluation", "notrump", "opening",
        "principles", "support", "takeout",
    ],
    "bidding/principles/bidding-fundamentals/playing-tricks.md": [
        "competitive", "double", "hand evaluation", "opening", "principles", "support",
    ],
    "bidding/principles/bidding-fundamentals/quick-tricks.md": [
        "hand evaluation", "opening", "principles", "slam",
    ],
}
OBSERVED_CATEGORY = "Hand Evaluation"
PROPOSED_CATEGORY = "bidding"
REQUIRED_SUBCATEGORY = "principles"


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


def build_category_normalization_batch3_3aa_report(root: Path) -> CategoryNormalizationReport:
    """Build the exact reviewed three-file family entirely in memory."""
    root = root.resolve()
    if root.name != "knowledge":
        raise RuntimeError(
            f"Refusing non-canonical knowledge root (expected directory named 'knowledge'): {root}"
        )
    observed_family = _observed_family(root)
    reviewed_family = set(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AA)
    if observed_family not in (reviewed_family, set()):
        missing = sorted(reviewed_family - observed_family)
        extra = sorted(observed_family - reviewed_family)
        raise RuntimeError(
            f"Reviewed Hand Evaluation family completeness mismatch: missing={missing!r}, extra={extra!r}"
        )

    actions = []
    for article, required_tags in sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AA.items()):
        path = root / article
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
                f"Reviewed frozen-subcategory precondition mismatch: {article}: expected "
                f"{REQUIRED_SUBCATEGORY!r}, observed {data.get('subcategory')!r}"
            )
        tags = data.get("tags")
        if (
            tags != required_tags
            or "hand evaluation" not in required_tags
            or "principles" not in required_tags
            or PROPOSED_CATEGORY in required_tags
        ):
            raise RuntimeError(
                f"Reviewed frozen-tag precondition mismatch: {article}: expected exact retained "
                f"tags {required_tags!r} with semantic tags retained and no broad 'bidding' tag, "
                f"observed {tags!r}"
            )
        current = data.get("category")
        if current == PROPOSED_CATEGORY:
            _require_exact_category_line(front_matter, PROPOSED_CATEGORY, article)
            continue
        if current != OBSERVED_CATEGORY:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: expected "
                f"{OBSERVED_CATEGORY!r}, observed {current!r}"
            )
        updated_front = _replace_exact_category(front_matter, article)
        updated_data = _load_front_matter(updated_front, article)
        if updated_data is None or updated_data.get("tags") != tags:
            raise RuntimeError(f"Reviewed frozen-tag mutation detected: {article}")
        if updated_data.get("subcategory") != REQUIRED_SUBCATEGORY:
            raise RuntimeError(f"Reviewed frozen-subcategory mutation detected: {article}")
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        expected = original.replace(
            f"category: {OBSERVED_CATEGORY}".encode(),
            f"category: {PROPOSED_CATEGORY}".encode(),
            1,
        )
        if updated != expected:
            raise RuntimeError(f"Non-category byte mutation detected: {article}")
        actions.append(CategoryNormalizationAction(article, path, original, updated))
    return CategoryNormalizationReport(len(reviewed_family), tuple(actions))


def apply_category_normalization_batch3_3aa_report(
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


def _require_exact_category_line(
    front_matter: str, value: str, article: str
) -> re.Match[str]:
    pattern = re.compile(rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front_matter))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {article}: expected one exact category: "
            f"{value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str, article: str) -> str:
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY, article)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
