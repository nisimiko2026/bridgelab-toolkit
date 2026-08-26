"""Safe Phase 4B Batch 1 case-only metadata-title normalization."""

from __future__ import annotations

import re
import shutil
import hashlib
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_TITLE_CHANGES = {
    "bidding/conventions/doubles/sos-redouble.md": ("Sos Redouble", "SOS Redouble"),
    "bidding/principles/bidding-fundamentals/rule-of-15.md": ("Rule Of 15", "Rule of 15"),
    "bidding/principles/bidding-fundamentals/rule-of-20.md": ("Rule Of 20", "Rule of 20"),
    "bidding/principles/partnership/ethics-and-unauthorized-information.md": (
        "Ethics And Unauthorized Information",
        "Ethics and Unauthorized Information",
    ),
    "bidding/systems/moscito.md": ("Moscito", "MOSCITO"),
    "play/counting/counting-the-hand.md": ("Counting The Hand", "Counting the Hand"),
    "play/counting/placing-the-card.md": ("Placing The Card", "Placing the Card"),
    "play/declarer-play/planning/planning-the-play.md": (
        "Planning The Play",
        "Planning the Play",
    ),
    "play/declarer-play/squeezes/rectifying-the-count.md": (
        "Rectifying The Count",
        "Rectifying the Count",
    ),
    "play/defence/opening-leads/rule-of-11.md": ("Rule Of 11", "Rule of 11"),
    "play/defence/opening-leads/rule-of-12.md": ("Rule Of 12", "Rule of 12"),
    "play/principles/cover-an-honor-with-an-honor.md": (
        "Cover An Honor With An Honor",
        "Cover an Honor with an Honor",
    ),
}
REVIEWED_SOURCE_SHA256 = {
    "bidding/conventions/doubles/sos-redouble.md": "36efd5a89975148d37fd2f9318eb16c5b2d2311ecd45a0922a9544b7f9f8fa98",
    "bidding/principles/bidding-fundamentals/rule-of-15.md": "266bfaa92e9835646c319c0798429012d9b40094ca4bc596e41af6d88aec3617",
    "bidding/principles/bidding-fundamentals/rule-of-20.md": "f407012f0460e38aed7c8cf4f02913467e2d41692f05d3bfd720cf9ef576790e",
    "bidding/principles/partnership/ethics-and-unauthorized-information.md": "76e42b1c641e1fa486be96e896541a06c746aaf8b81cdca38b5cdd57d5ba1f42",
    "bidding/systems/moscito.md": "1513a9c397c087d1d41b47cf17b562c9b423bc6af8c8284193a579a3a5f6da08",
    "play/counting/counting-the-hand.md": "327c81f588d0fd12c0bd7e24a0d5c6a8cfe4bb06b49dcb4360aab0851ae9e8e7",
    "play/counting/placing-the-card.md": "dd928cbc4cafd63f045b8e94714a763ff55a156b75bdf9619745bb3d96e20cdd",
    "play/declarer-play/planning/planning-the-play.md": "f7bf2bba1a1942afbea3be4d5e69a855b1c10c52de74c5481256edee6d38515f",
    "play/declarer-play/squeezes/rectifying-the-count.md": "51ff037b73a35fd8d66ab662ea4db6bc355dc5059ad27d817a2ccc91e6de56d5",
    "play/defence/opening-leads/rule-of-11.md": "267f6f5a5f876dcf1144e8276eb7c63250fbac43cb325770e7616e870df17cb4",
    "play/defence/opening-leads/rule-of-12.md": "de5c6378eeefcedf7c2b2b83f9d8477096e702888bacce4337415c83be91e119",
    "play/principles/cover-an-honor-with-an-honor.md": "245dd4f0db6124bb413a40c5bf953da33d3cddf5d6d939305aa447450c9c1604",
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


def build_title_h1_case_normalization_batch1_report(root: Path) -> TitleNormalizationReport:
    """Build the exact reviewed 12-file title-line plan entirely in memory."""
    root = _validated_root(root)
    reviewed = set(REVIEWED_TITLE_CHANGES)
    observed = _case_only_mismatch_population(root)
    if observed not in (reviewed, set()):
        raise RuntimeError(
            "Reviewed case-only title/H1 family census mismatch: "
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
        h1 = _first_h1(text, article)
        current = data.get("title")

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
        observed_hash = hashlib.sha256(original).hexdigest()
        if observed_hash != REVIEWED_SOURCE_SHA256[article]:
            raise RuntimeError(
                f"Reviewed complete-byte source precondition mismatch: {article}: "
                f"expected {REVIEWED_SOURCE_SHA256[article]}, observed {observed_hash}"
            )
        if h1 != target:
            raise RuntimeError(
                f"Reviewed H1 precondition mismatch: {article}: expected {target!r}, observed {h1!r}"
            )
        if source.casefold() != target.casefold() or source == target:
            raise RuntimeError(f"Reviewed case-only invariant mismatch: {article}")

        updated_front = _replace_exact_title(front, source, target, article)
        updated = (updated_front + text[match.end() :]).encode("utf-8")
        expected = original.replace(f"title: {source}".encode(), f"title: {target}".encode(), 1)
        if updated != expected:
            raise RuntimeError(f"Non-title byte mutation detected: {article}")
        if _first_h1(updated.decode("utf-8"), article) != h1:
            raise RuntimeError(f"Reviewed frozen-H1 mutation detected: {article}")
        actions.append(
            TitleNormalizationAction(article, path, source, target, original, updated)
        )

    if observed == set() and actions:
        raise RuntimeError("Reviewed case-only title/H1 family census conflicts with normalized targets")
    return TitleNormalizationReport(len(REVIEWED_TITLE_CHANGES), tuple(actions))


def apply_title_h1_case_normalization_batch1_report(
    report: TitleNormalizationReport, root: Path, backup: Path
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
    if resolved.name != "knowledge" or any(
        part.casefold() == "onedrive" for part in resolved.parts
    ):
        raise RuntimeError(
            "Refusing non-canonical knowledge root (expected a directory named "
            f"'knowledge' outside OneDrive): {resolved}"
        )
    return resolved


def _case_only_mismatch_population(root: Path) -> set[str]:
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
        title = data.get("title") if data is not None else None
        h1_match = H1_RE.search(text)
        if (
            isinstance(title, str)
            and h1_match
            and title != h1_match.group(1)
            and title.casefold() == h1_match.group(1).casefold()
        ):
            observed.add(article)
    return observed


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
    return front[: match.start()] + f"title: {target}{match.group('ending')}" + front[match.end() :]
