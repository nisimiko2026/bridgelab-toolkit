"""Safe Phase 3A Batch 3.3ad Bridge Formats category normalization."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


ARTICLE = "duplicates/duplicates-index.md"
REQUIRED_TAGS = ["bridge formats", "competitive"]
REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AD = {ARTICLE: REQUIRED_TAGS}
OBSERVED_CATEGORY = "Bridge Formats"
PROPOSED_CATEGORY = "duplicate"
REQUIRED_SUBCATEGORY = ""
DOMAIN_CATEGORY_BY_COMPONENT = {"duplicates": "duplicate"}


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


def build_category_normalization_batch3_3ad_report(root: Path) -> CategoryNormalizationReport:
    """Build the exact reviewed one-file domain-index repair in memory."""
    root = root.resolve()
    if root.name != "knowledge":
        raise RuntimeError(
            f"Refusing non-canonical knowledge root (expected directory named 'knowledge'): {root}"
        )
    if _canonical_category_from_path(ARTICLE) != PROPOSED_CATEGORY:
        raise RuntimeError(
            f"Reviewed path-derived category mismatch: {ARTICLE}: expected {PROPOSED_CATEGORY!r}"
        )
    observed_family = _observed_family(root)
    reviewed_family = set(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AD)
    if observed_family not in (reviewed_family, set()):
        missing = sorted(reviewed_family - observed_family)
        extra = sorted(observed_family - reviewed_family)
        raise RuntimeError(
            f"Reviewed Bridge Formats family completeness mismatch: missing={missing!r}, extra={extra!r}"
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
            f"Reviewed frozen-subcategory precondition mismatch: {ARTICLE}: expected empty, "
            f"observed {data.get('subcategory')!r}"
        )
    tags = data.get("tags")
    if (
        tags != REQUIRED_TAGS
        or "bridge formats" not in REQUIRED_TAGS
        or PROPOSED_CATEGORY in REQUIRED_TAGS
    ):
        raise RuntimeError(
            f"Reviewed frozen-tag precondition mismatch: {ARTICLE}: expected exact retained "
            f"tags {REQUIRED_TAGS!r} with 'bridge formats' retained and no broad "
            f"'duplicate' tag, observed {tags!r}"
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


def apply_category_normalization_batch3_3ad_report(
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


def _canonical_category_from_path(article: str) -> str:
    first_component = Path(article).parts[0]
    try:
        return DOMAIN_CATEGORY_BY_COMPONENT[first_component]
    except KeyError as error:
        raise RuntimeError(
            f"Unrecognized canonical domain component for reviewed article: {article}"
        ) from error


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
            f"Unsafe category line precondition in {ARTICLE}: expected one exact category: "
            f"{value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str) -> str:
    match = _require_exact_category_line(front_matter, OBSERVED_CATEGORY)
    return (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
