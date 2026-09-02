"""Safe Phase 4B Batch 7 metadata-title capitalization repair."""

from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.document_roles import DocumentRole, classify_document_role
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_TITLE_CHANGES = {
    "bidding/conventions/slam-conventions/serious-3nt.md": (
        "Serious 3Nt",
        "Serious 3NT",
        "Serious 3NT Convention",
    ),
    "bidding/systems/ehaa.md": (
        "Ehaa",
        "EHAA",
        "EHAA (Every Hand An Adventure)",
    ),
    "bidding/systems/sef.md": (
        "Sef",
        "SEF",
        "SEF (Système d'Enseignement Français)",
    ),
    "play/declarer-play/coups/coup-en-passant.md": (
        "Coup En Passant",
        "Coup en Passant",
        "Coup en Passant Technique",
    ),
}

REVIEWED_SOURCE_SHA256 = {
    "bidding/conventions/slam-conventions/serious-3nt.md": (
        "0822c3aff00834735d863369a1e761633dcd82f4f225f0dd1ef0c68f0b5df97c"
    ),
    "bidding/systems/ehaa.md": (
        "5e9803b7686e05b7f55fc64eef9bbe13d5a787daf7cd0f88be60cf501c051e5a"
    ),
    "bidding/systems/sef.md": (
        "0dedcd4c1533e3b82e2776524e5536d97d19b78604d8b16a50026e321da90fca"
    ),
    "play/declarer-play/coups/coup-en-passant.md": (
        "743b3fd5d2678bbe6016555d2b5199fbd427dd2b805657064c4aa9971fd5d92c"
    ),
}

REVIEWED_POST_SHA256 = {
    "bidding/conventions/slam-conventions/serious-3nt.md": (
        "4647e21449f9bc80a703a912d7273329798cd4eeadd6f68417abcf9057527d8c"
    ),
    "bidding/systems/ehaa.md": (
        "b9cfacefd32364646990135129e98783e20b8b8ca0815e944cc2a1a9741d2629"
    ),
    "bidding/systems/sef.md": (
        "e8e20f4b25ae6d51226b01bb912ed80e11e2ed10656c8ccf5f2c6847b3935941"
    ),
    "play/declarer-play/coups/coup-en-passant.md": (
        "48c9b8b57ed028f13d65cbd7cd0846fea490350bfc7bfd1eed63eadda27888f6"
    ),
}

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
PRESENTATION_RE = re.compile(
    r"^(?P<base>.+?)(?:\s+\([^\r\n()]*\)|\s+(?:Technique|System|Convention))$"
)


@dataclass(frozen=True, slots=True)
class MetadataCaseRepairAction:
    article: str
    path: Path
    original_title: str
    proposed_title: str
    expected_h1: str
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class MetadataCaseRepairReport:
    selected_files: int
    actions: tuple[MetadataCaseRepairAction, ...]


def build_title_h1_metadata_case_repair_batch7_report(
    root: Path,
) -> MetadataCaseRepairReport:
    """Build the exact reviewed four-file repair plan entirely in memory."""
    root = _validated_root(root)
    reviewed = set(REVIEWED_TITLE_CHANGES)
    observed = _capitalization_defect_population(root)
    if observed not in (reviewed, set()):
        raise RuntimeError(
            "Reviewed metadata capitalization census mismatch: "
            f"missing={sorted(reviewed - observed)!r}, extra={sorted(observed - reviewed)!r}"
        )

    actions: list[MetadataCaseRepairAction] = []
    for article, (source, target, expected_h1) in REVIEWED_TITLE_CHANGES.items():
        path = root / article
        if not path.is_file():
            raise RuntimeError(f"Reviewed metadata-case file is missing: {article}")
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
            if first_h1 != expected_h1 or observed_hash != REVIEWED_POST_SHA256[article]:
                raise RuntimeError(f"Reviewed normalized post-image mismatch: {article}")
            _require_exact_title_line(front, target, article)
            continue
        if current != source:
            raise RuntimeError(
                f"Reviewed title precondition mismatch: {article}: "
                f"expected {source!r}, observed {current!r}"
            )
        if first_h1 != expected_h1:
            raise RuntimeError(
                f"Reviewed first-H1 precondition mismatch: {article}: "
                f"expected {expected_h1!r}, observed {first_h1!r}"
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
        actions.append(
            MetadataCaseRepairAction(
                article, path, source, target, expected_h1, original, updated
            )
        )

    if observed == set() and actions:
        raise RuntimeError("Reviewed metadata-case census conflicts with normalized targets")
    return MetadataCaseRepairReport(len(REVIEWED_TITLE_CHANGES), tuple(actions))


def apply_title_h1_metadata_case_repair_batch7_report(
    report: MetadataCaseRepairReport, root: Path, backup: Path
) -> None:
    """Apply an unchanged report after complete-batch and backup preflight."""
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
            raise RuntimeError(f"Refusing metadata repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(f"Reviewed complete-byte precondition mismatch: {action.article}")

    try:
        for action in report.actions:
            destination = backup / action.path.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(action.path, destination)
            if destination.read_bytes() != action.original:
                raise RuntimeError(f"Backup byte verification failed: {action.article}")
    except Exception:
        if backup.exists():
            shutil.rmtree(backup)
        raise

    updated: list[MetadataCaseRepairAction] = []
    try:
        for action in report.actions:
            _atomic_write(action.path, action.updated)
            updated.append(action)
    except Exception:
        for action in reversed(updated):
            _atomic_write(action.path, action.original)
        raise


def _build_post_image(original: bytes, source: str, target: str, article: str) -> bytes:
    source_line = f"title: {source}".encode("utf-8")
    target_line = f"title: {target}".encode("utf-8")
    if original.count(source_line) != 1:
        raise RuntimeError(f"Unsafe title-line precondition: {article}")
    updated = original.replace(source_line, target_line, 1)
    if len(updated) != len(original):
        raise RuntimeError(f"Reviewed title replacement changed byte length: {article}")
    return updated


def _capitalization_defect_population(root: Path) -> set[str]:
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
        if not isinstance(title, str) or not h1_match:
            continue
        presentation = PRESENTATION_RE.fullmatch(h1_match.group(1))
        if not presentation:
            continue
        base = presentation.group("base")
        if title != base and title.casefold() == base.casefold():
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
