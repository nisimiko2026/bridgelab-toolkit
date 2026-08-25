"""Safe atomic Phase 3A Batch 3.3af Index-to-bidding normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REQUIRED_TAGS = {
    "bidding/natural-bids/opening-bids/natural-opening-bids-index.md": [
        "index", "natural-bids", "opening", "preempt", "response",
    ],
    "bidding/natural-bids/rebids/natural-rebids-index.md": [
        "index", "natural-bids", "notrump", "opening", "rebid", "response", "slam", "support",
    ],
    "bidding/natural-bids/responses/natural-responses-index.md": [
        "index", "natural-bids", "notrump", "opening", "preempt", "response", "support",
    ],
}
ARTICLES = tuple(REQUIRED_TAGS)
OBSERVED_CATEGORY = "Index"
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


def build_category_normalization_batch3_3af_report(root: Path) -> CategoryNormalizationReport:
    """Build the exact reviewed three-file family entirely in memory."""
    root = root.resolve()
    if root.name != "knowledge":
        raise RuntimeError(
            f"Refusing non-canonical knowledge root (expected directory named 'knowledge'): {root}"
        )
    for article in ARTICLES:
        if _canonical_category_from_path(article) != PROPOSED_CATEGORY:
            raise RuntimeError(f"Reviewed path-derived category mismatch: {article}")
        if not (root / article).is_file():
            raise RuntimeError(f"Reviewed category file is missing: {article}")
    observed = _bidding_index_family(root)
    reviewed = set(ARTICLES)
    extra = observed - reviewed
    if extra:
        raise RuntimeError(
            "Reviewed bidding Index family completeness mismatch: "
            f"missing={sorted(reviewed - observed)!r}, extra={sorted(extra)!r}"
        )
    actions = []
    normalized = 0
    for article in ARTICLES:
        path = root / article
        original = path.read_bytes()
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RuntimeError(f"Article is not valid UTF-8: {article}") from error
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front = front_match.group(0)
        data = _load_front_matter(front, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")
        if data.get("subcategory") != REQUIRED_SUBCATEGORY:
            raise RuntimeError(
                f"Reviewed frozen-subcategory precondition mismatch: {article}: "
                f"observed {data.get('subcategory')!r}"
            )
        tags = data.get("tags")
        required = REQUIRED_TAGS[article]
        if tags != required or "index" not in required or "natural-bids" not in required or "bidding" in required:
            raise RuntimeError(
                f"Reviewed frozen-tag precondition mismatch: {article}: "
                f"expected {required!r}, observed {tags!r}"
            )
        current = data.get("category")
        if current == PROPOSED_CATEGORY:
            _require_exact_category_line(front, PROPOSED_CATEGORY, article)
            normalized += 1
            continue
        if current != OBSERVED_CATEGORY:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: observed {current!r}"
            )
        updated_front = _replace_exact_category(front, article)
        updated_data = _load_front_matter(updated_front, article)
        if updated_data is None or updated_data.get("tags") != tags:
            raise RuntimeError(f"Reviewed frozen-tag mutation detected: {article}")
        if updated_data.get("subcategory") != REQUIRED_SUBCATEGORY:
            raise RuntimeError(f"Reviewed frozen-subcategory mutation detected: {article}")
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        expected = original.replace(b"category: Index", b"category: bidding", 1)
        if updated != expected:
            raise RuntimeError(f"Non-category byte mutation detected: {article}")
        actions.append(CategoryNormalizationAction(article, path, original, updated))
    if normalized and actions:
        raise RuntimeError("Refusing partially normalized indivisible three-file family")
    return CategoryNormalizationReport(3, tuple(actions))


def apply_category_normalization_batch3_3af_report(
    report: CategoryNormalizationReport, root: Path, backup: Path
) -> None:
    """Apply atomically at family level, rolling back replacements on failure."""
    if not report.actions:
        return
    if len(report.actions) != 3:
        raise RuntimeError("Refusing partial three-file family apply")
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
    replaced = []
    try:
        for action in report.actions:
            _atomic_write(action.path, action.updated)
            replaced.append(action)
    except OSError:
        for action in reversed(replaced):
            _atomic_write(action.path, action.original)
        raise


def _canonical_category_from_path(article: str) -> str:
    parts = Path(article).parts
    if not parts or parts[0] != "bidding":
        raise RuntimeError(f"Unrecognized canonical domain for reviewed article: {article}")
    return "bidding"


def _bidding_index_family(root: Path) -> set[str]:
    observed = set()
    bidding = root / "bidding"
    for path in bidding.rglob("*.md") if bidding.is_dir() else ():
        article = path.relative_to(root).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        match = FRONT_MATTER_RE.match(text)
        if match:
            data = _load_front_matter(match.group(0), article)
            if data is not None and data.get("category") == OBSERVED_CATEGORY:
                observed.add(article)
    return observed


def _require_exact_category_line(front: str, value: str, article: str) -> re.Match[str]:
    pattern = re.compile(rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {article}: expected one exact line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front: str, article: str) -> str:
    match = _require_exact_category_line(front, OBSERVED_CATEGORY, article)
    return front[: match.start()] + f"category: {PROPOSED_CATEGORY}{match.group('ending')}" + front[match.end() :]
