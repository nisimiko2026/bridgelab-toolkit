"""Safe Phase 4B Batch 3 metadata-title and leading-H1 content repair."""

from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.document_roles import DocumentRole, classify_document_role
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_CONTENT_REPAIRS = {
    "bidding/conventions/responses/preemptive-raise.md": (
        "Preemptive.Raise",
        "Preemptive Raise",
    ),
    "bidding/natural-bids/opening-bids/1-club.md": (
        "1 Club",
        "1♣ Opening Bid",
    ),
}
REVIEWED_SOURCE_SHA256 = {
    "bidding/conventions/responses/preemptive-raise.md": (
        "6f95afd7d4963b92458c43f06fe80324b5656689a5f9b76d730de226b97a3209"
    ),
    "bidding/natural-bids/opening-bids/1-club.md": (
        "fd23cf501aafbfd16d8a8bca340bd4f51ab49108982c6d1c29c1b9d09f25878b"
    ),
}
REVIEWED_POST_SHA256 = {
    "bidding/conventions/responses/preemptive-raise.md": (
        "f9cbcedebf8e5e0cb70593e91d15afd39df6c02d29af5d7b8be67f7b6b5b7a90"
    ),
    "bidding/natural-bids/opening-bids/1-club.md": (
        "1408450ac0373c76e01b36c91f5082b89b0800564f0eb046014ae1f5d082d48f"
    ),
}
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class ContentRepairAction:
    article: str
    path: Path
    original_title: str
    proposed_title: str
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class ContentRepairReport:
    selected_files: int
    actions: tuple[ContentRepairAction, ...]


def build_title_h1_content_repair_batch3_report(root: Path) -> ContentRepairReport:
    """Build the exact reviewed two-file repair plan entirely in memory."""
    root = _validated_root(root)
    reviewed = set(REVIEWED_CONTENT_REPAIRS)
    observed = _missing_document_h1_population(root)
    if observed not in (reviewed, set()):
        raise RuntimeError(
            "Reviewed title/H1 content-repair family census mismatch: "
            f"missing={sorted(reviewed - observed)!r}, extra={sorted(observed - reviewed)!r}"
        )

    actions: list[ContentRepairAction] = []
    for article, (source, target) in REVIEWED_CONTENT_REPAIRS.items():
        path = root / article
        if not path.is_file():
            raise RuntimeError(f"Reviewed content-repair file is missing: {article}")
        original = path.read_bytes()
        text = _decode(original, article)
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front = front_match.group(0)
        data = _load_front_matter(front, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")
        current = data.get("title")
        first_h1 = _first_h1(text, article)
        observed_hash = hashlib.sha256(original).hexdigest()

        if current == target:
            if first_h1 != target or observed_hash != REVIEWED_POST_SHA256[article]:
                raise RuntimeError(f"Reviewed normalized post-image mismatch: {article}")
            _require_exact_title_line(front, target, article)
            continue
        if current != source:
            raise RuntimeError(
                f"Reviewed title precondition mismatch: {article}: "
                f"expected {source!r}, observed {current!r}"
            )
        if first_h1 != "Objectives":
            raise RuntimeError(
                f"Reviewed first-H1 precondition mismatch: {article}: "
                f"expected 'Objectives', observed {first_h1!r}"
            )
        if classify_document_role(article) is not DocumentRole.ARTICLE:
            raise RuntimeError(f"Reviewed document-role precondition mismatch: {article}")
        if observed_hash != REVIEWED_SOURCE_SHA256[article]:
            raise RuntimeError(
                f"Reviewed complete-byte source precondition mismatch: {article}: "
                f"expected {REVIEWED_SOURCE_SHA256[article]}, observed {observed_hash}"
            )

        updated = _build_post_image(original, source, target, article)
        if hashlib.sha256(updated).hexdigest() != REVIEWED_POST_SHA256[article]:
            raise RuntimeError(f"Reviewed post-image construction mismatch: {article}")
        actions.append(ContentRepairAction(article, path, source, target, original, updated))

    if observed == set() and actions:
        raise RuntimeError("Reviewed content-repair census conflicts with normalized targets")
    return ContentRepairReport(len(REVIEWED_CONTENT_REPAIRS), tuple(actions))


def apply_title_h1_content_repair_batch3_report(
    report: ContentRepairReport, root: Path, backup: Path
) -> None:
    """Apply an unchanged report after complete-batch byte preflight."""
    if not report.actions:
        return
    root = _validated_root(root)
    backup = backup.resolve()
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    try:
        backup.relative_to(root)
    except ValueError:
        pass
    else:
        raise RuntimeError(f"Backup destination must be outside canonical knowledge: {backup}")

    for action in report.actions:
        try:
            action.path.resolve().relative_to(root)
        except ValueError as error:
            raise RuntimeError(f"Refusing content repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(f"Reviewed complete-byte precondition mismatch: {action.article}")

    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)

    updated: list[ContentRepairAction] = []
    try:
        for action in report.actions:
            _atomic_write(action.path, action.updated)
            updated.append(action)
    except Exception:
        for action in reversed(updated):
            _atomic_write(action.path, action.original)
        raise


def _build_post_image(original: bytes, source: str, target: str, article: str) -> bytes:
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    source_line = f"title: {source}".encode("utf-8")
    target_line = f"title: {target}".encode("utf-8")
    if original.count(source_line) != 1:
        raise RuntimeError(f"Unsafe title-line precondition: {article}")
    updated = original.replace(source_line, target_line, 1)
    marker = b"# Objectives"
    if updated.count(marker) != 1:
        raise RuntimeError(f"Unsafe Objectives insertion precondition: {article}")
    inserted = f"# {target}".encode("utf-8") + newline + newline + marker
    updated = updated.replace(marker, inserted, 1)
    return updated


def _missing_document_h1_population(root: Path) -> set[str]:
    observed: set[str] = set()
    for path in root.rglob("*.md"):
        article = path.relative_to(root).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            continue
        data = _load_front_matter(front_match.group(0), article)
        title = data.get("title") if data is not None else None
        h1_match = H1_RE.search(text)
        if (
            isinstance(title, str)
            and h1_match
            and title != h1_match.group(1)
            and h1_match.group(1) == "Objectives"
            and classify_document_role(article) is DocumentRole.ARTICLE
        ):
            observed.add(article)
    return observed


def _validated_root(root: Path) -> Path:
    resolved = root.resolve()
    if resolved.name != "knowledge" or any(part.casefold() == "onedrive" for part in resolved.parts):
        raise RuntimeError(
            "Refusing non-canonical knowledge root (expected a directory named "
            f"'knowledge' outside OneDrive): {resolved}"
        )
    return resolved


def _decode(content: bytes, article: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {article}") from error


def _first_h1(text: str, article: str) -> str:
    match = H1_RE.search(text)
    if not match:
        raise RuntimeError(f"Reviewed first-H1 precondition mismatch: {article}: missing H1")
    return match.group(1)


def _require_exact_title_line(front: str, value: str, article: str) -> re.Match[str]:
    pattern = re.compile(rf"^title: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe title line precondition in {article}: expected one exact title: "
            f"{value} line, found {len(matches)}"
        )
    return matches[0]
