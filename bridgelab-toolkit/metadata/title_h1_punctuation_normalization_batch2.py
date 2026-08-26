"""Safe Phase 4B Batch 2 punctuation-only metadata-title normalization."""

from __future__ import annotations

import hashlib
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_TITLE_CHANGES = {
    "bidding/conventions/doubles/lead-directing-double.md": (
        "Lead Directing Double", "Lead-Directing Double",
    ),
    "bidding/conventions/responses/five-card-stayman.md": (
        "Five Card Stayman", "Five-Card Stayman",
    ),
    "bidding/conventions/responses/two-way-stayman.md": (
        "Two Way Stayman", "Two-Way Stayman",
    ),
    "duplicates/matchpoints-vs-imps.md": ("Matchpoints Vs Imps", "Matchpoints vs. IMPs"),
    "play/defence/planning/active-vs-passive-defense.md": (
        "Active Vs Passive Defense", "Active vs. Passive Defense",
    ),
}
REVIEWED_SOURCE_SHA256 = {
    "bidding/conventions/doubles/lead-directing-double.md": "fe93a723fb7c5e4944c7b0d161d3ffecb55fea4294bd697f36f04802d99bdc26",
    "bidding/conventions/responses/five-card-stayman.md": "2739a254654e86430ebe08cbde9460bd7ba7d5ee9818cbe7d3ad253699efe42b",
    "bidding/conventions/responses/two-way-stayman.md": "174fd05aeb97ba100e4fa11267d611d09089c7287e9b3284a825c82c22ce4374",
    "duplicates/matchpoints-vs-imps.md": "ecc9a11292b2a04121192c87c52111dcd4450eed58a8ec496838d4078001992e",
    "play/defence/planning/active-vs-passive-defense.md": "44dc0f9cbec82858b0b903697bfc3f2854fe42774652dfee6d323fadbc9fe283",
}
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class TitleNormalizationAction:
    article: str
    path: Path
    original_title: str
    proposed_title: str
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class TitleNormalizationReport:
    selected_files: int
    actions: tuple[TitleNormalizationAction, ...]


def build_title_h1_punctuation_normalization_batch2_report(
    root: Path,
) -> TitleNormalizationReport:
    """Build the exact reviewed five-file title-line plan entirely in memory."""
    root = _validated_root(root)
    reviewed = set(REVIEWED_TITLE_CHANGES)
    observed = _punctuation_only_mismatch_population(root)
    if observed not in (reviewed, set()):
        raise RuntimeError(
            "Reviewed punctuation-only title/H1 family census mismatch: "
            f"missing={sorted(reviewed - observed)!r}, extra={sorted(observed - reviewed)!r}"
        )

    actions: list[TitleNormalizationAction] = []
    for article, (source, target) in REVIEWED_TITLE_CHANGES.items():
        path = root / article
        if not path.is_file():
            raise RuntimeError(f"Reviewed title file is missing: {article}")
        original = path.read_bytes()
        text = _decode(original, article)
        match = FRONT_MATTER_RE.match(text)
        if not match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front = match.group(0)
        data = _load_front_matter(front, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")
        current = data.get("title")
        h1 = _first_h1(text, article)
        if current == target:
            if h1 != target:
                raise RuntimeError(
                    f"Reviewed H1 precondition mismatch: {article}: expected {target!r}, observed {h1!r}"
                )
            _require_exact_title_line(front, target, article)
            continue
        if current != source:
            raise RuntimeError(
                f"Reviewed title precondition mismatch: {article}: expected {source!r}, observed {current!r}"
            )
        if h1 != target:
            raise RuntimeError(
                f"Reviewed H1 precondition mismatch: {article}: expected {target!r}, observed {h1!r}"
            )
        if source.casefold() == target.casefold() or _alphanumeric(source) != _alphanumeric(target):
            raise RuntimeError(f"Reviewed punctuation-only invariant mismatch: {article}")
        observed_hash = hashlib.sha256(original).hexdigest()
        if observed_hash != REVIEWED_SOURCE_SHA256[article]:
            raise RuntimeError(
                f"Reviewed complete-byte source precondition mismatch: {article}: "
                f"expected {REVIEWED_SOURCE_SHA256[article]}, observed {observed_hash}"
            )
        updated_front = _replace_exact_title(front, source, target, article)
        updated = (updated_front + text[match.end():]).encode("utf-8")
        expected = original.replace(f"title: {source}".encode(), f"title: {target}".encode(), 1)
        if updated != expected:
            raise RuntimeError(f"Non-title byte mutation detected: {article}")
        if _first_h1(updated.decode("utf-8"), article) != h1:
            raise RuntimeError(f"Reviewed frozen-H1 mutation detected: {article}")
        actions.append(TitleNormalizationAction(article, path, source, target, original, updated))

    if observed == set() and actions:
        raise RuntimeError("Reviewed punctuation-only family census conflicts with normalized targets")
    return TitleNormalizationReport(len(REVIEWED_TITLE_CHANGES), tuple(actions))


def apply_title_h1_punctuation_normalization_batch2_report(
    report: TitleNormalizationReport, root: Path, backup: Path,
) -> None:
    """Apply an unchanged report after a complete-batch byte preflight."""
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
            raise RuntimeError(f"Refusing title repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(f"Reviewed complete-byte precondition mismatch: {action.article}")
    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)
    updated: list[TitleNormalizationAction] = []
    try:
        for action in report.actions:
            _atomic_write(action.path, action.updated)
            updated.append(action)
    except Exception:
        for action in reversed(updated):
            _atomic_write(action.path, action.original)
        raise


def _validated_root(root: Path) -> Path:
    resolved = root.resolve()
    if resolved.name != "knowledge" or any(part.casefold() == "onedrive" for part in resolved.parts):
        raise RuntimeError(
            "Refusing non-canonical knowledge root (expected a directory named "
            f"'knowledge' outside OneDrive): {resolved}"
        )
    return resolved


def _punctuation_only_mismatch_population(root: Path) -> set[str]:
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
        title = data.get("title") if data is not None else None
        h1_match = H1_RE.search(text)
        if (
            isinstance(title, str) and h1_match and title != h1_match.group(1)
            and title.casefold() != h1_match.group(1).casefold()
            and _alphanumeric(title) == _alphanumeric(h1_match.group(1))
        ):
            observed.add(article)
    return observed


def _alphanumeric(value: str) -> str:
    return "".join(
        character.casefold()
        for character in unicodedata.normalize("NFKD", value)
        if character.isalnum()
    )


def _decode(content: bytes, article: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {article}") from error


def _first_h1(text: str, article: str) -> str:
    match = H1_RE.search(text)
    if not match:
        raise RuntimeError(f"Reviewed H1 precondition mismatch: {article}: missing H1")
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


def _replace_exact_title(front: str, source: str, target: str, article: str) -> str:
    match = _require_exact_title_line(front, source, article)
    return front[:match.start()] + f"title: {target}{match.group('ending')}" + front[match.end():]
