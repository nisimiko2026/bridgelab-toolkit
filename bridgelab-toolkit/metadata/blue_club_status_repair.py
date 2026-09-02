"""Safe one-file repair for the reviewed Blue Club status defect."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.audit import DIFFICULTIES
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


ARTICLE = "bidding/systems/blue-club.md"
OBSERVED_STATUS = "Advanced"
PROPOSED_STATUS = "Draft"
REQUIRED_TITLE = "Blue Club"
REQUIRED_CATEGORY = "bidding"
REQUIRED_SUBCATEGORY = "systems"
REQUIRED_DIFFICULTY = "Advanced"


@dataclass(frozen=True, slots=True)
class BlueClubStatusAction:
    article: str
    path: Path
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class BlueClubStatusReport:
    selected_files: int
    actions: tuple[BlueClubStatusAction, ...]


def build_blue_club_status_report(root: Path) -> BlueClubStatusReport:
    """Build the exact reviewed status-line repair entirely in memory."""
    root = _validated_root(root)
    path = root / ARTICLE
    if not path.is_file():
        raise RuntimeError(f"Reviewed status file is missing: {ARTICLE}")

    population = _difficulty_status_population(root)
    if population not in ({ARTICLE}, set()):
        raise RuntimeError(
            "Reviewed difficulty-valued status census mismatch: "
            f"missing={sorted({ARTICLE} - population)!r}, "
            f"extra={sorted(population - {ARTICLE})!r}"
        )

    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {ARTICLE}") from error
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise RuntimeError(f"Missing or malformed front matter: {ARTICLE}")
    front = match.group(0)
    data = _load_front_matter(front, ARTICLE)
    if data is None:
        raise RuntimeError(f"Empty front matter: {ARTICLE}")

    required = {
        "title": REQUIRED_TITLE,
        "category": REQUIRED_CATEGORY,
        "subcategory": REQUIRED_SUBCATEGORY,
        "difficulty": REQUIRED_DIFFICULTY,
    }
    for field, expected in required.items():
        if data.get(field) != expected:
            raise RuntimeError(
                f"Reviewed {field} precondition mismatch: {ARTICLE}: "
                f"expected {expected!r}, observed {data.get(field)!r}"
            )

    status = data.get("status")
    if status == PROPOSED_STATUS:
        if population:
            raise RuntimeError("Reviewed status census conflicts with normalized target")
        _require_exact_status_line(front, PROPOSED_STATUS)
        return BlueClubStatusReport(1, ())
    if status != OBSERVED_STATUS:
        raise RuntimeError(
            f"Reviewed status precondition mismatch: {ARTICLE}: expected "
            f"{OBSERVED_STATUS!r}, observed {status!r}"
        )
    if population != {ARTICLE}:
        raise RuntimeError(
            "Reviewed difficulty-valued status census mismatch: "
            f"missing={[ARTICLE]!r}, extra=[]"
        )

    updated_front = _replace_exact_status(front)
    updated_data = _load_front_matter(updated_front, ARTICLE)
    if updated_data is None:
        raise RuntimeError(f"Empty updated front matter: {ARTICLE}")
    if updated_data.get("difficulty") != REQUIRED_DIFFICULTY:
        raise RuntimeError(f"Reviewed frozen-difficulty mutation detected: {ARTICLE}")
    updated = (updated_front + text[match.end() :]).encode("utf-8")
    expected = original.replace(b"status: Advanced", b"status: Draft", 1)
    if updated != expected:
        raise RuntimeError(f"Non-status byte mutation detected: {ARTICLE}")
    return BlueClubStatusReport(
        1, (BlueClubStatusAction(ARTICLE, path, original, updated),)
    )


def apply_blue_club_status_report(
    report: BlueClubStatusReport, root: Path, backup: Path
) -> None:
    """Apply an unchanged report after complete-byte preflight checks."""
    if not report.actions:
        return
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    root = _validated_root(root)
    for action in report.actions:
        try:
            action.path.resolve().relative_to(root)
        except ValueError as error:
            raise RuntimeError(f"Refusing status repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(
                f"Reviewed complete-byte precondition mismatch: {action.article}"
            )

    action = report.actions[0]
    destination = backup / action.path.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(action.path, destination)
    _atomic_write(action.path, action.updated)


def _validated_root(root: Path) -> Path:
    resolved = root.resolve()
    if resolved.name != "knowledge" or any(
        part.casefold() == "onedrive" for part in resolved.parts
    ):
        raise RuntimeError(
            "Refusing non-canonical knowledge root (expected a directory named "
            f"'knowledge' outside OneDrive): {resolved}"
        )
    return resolved


def _difficulty_status_population(root: Path) -> set[str]:
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
        if data is not None and data.get("status") in DIFFICULTIES:
            observed.add(article)
    return observed


def _require_exact_status_line(front: str, value: str) -> re.Match[str]:
    pattern = re.compile(rf"^status: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe status line precondition in {ARTICLE}: expected one exact "
            f"status: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_status(front: str) -> str:
    match = _require_exact_status_line(front, OBSERVED_STATUS)
    return (
        front[: match.start()]
        + f"status: {PROPOSED_STATUS}{match.group('ending')}"
        + front[match.end() :]
    )
