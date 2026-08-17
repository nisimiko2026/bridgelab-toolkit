"""Plan and apply narrowly scoped sentinel metadata cleanup."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from core.models import Article
from metadata.validator import MetadataValidator

FRONT_MATTER_RE = re.compile(
    r"\A(?:\ufeff)?---[ \t]*(?:\r\n|\n).*?(?:\r\n|\n)" r"---[ \t]*(?=\r\n|\n|\Z)",
    re.DOTALL,
)
TOP_LEVEL_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:[^\r\n]*(?:\r?\n|\Z)")
TAGS_KEY_RE = re.compile(r"^tags:[ \t]*(?:\r?\n|\Z)")
NONE_TAG_RE = re.compile(r"^[ \t]*-[ \t]+none[ \t]*(?:\r?\n|\Z)")
DIFFICULTY_NONE_RE = re.compile(
    r"^(?P<prefix>difficulty:[ \t]*)(?:None|'None'|\"None\")"
    r"(?P<suffix>[ \t]*(?:#[^\r\n]*)?(?:\r?\n|\Z))"
)


@dataclass(frozen=True, slots=True)
class CleanupAction:
    article: str
    path: Path
    original: bytes
    updated: bytes
    tag_removals: int
    difficulty_cleared: bool


@dataclass(frozen=True, slots=True)
class CleanupReport:
    actions: tuple[CleanupAction, ...]
    literal_none_subcategories: tuple[str, ...]
    non_exempt_literal_none_difficulties: tuple[str, ...]

    @property
    def tag_removals(self) -> int:
        return sum(action.tag_removals for action in self.actions)

    @property
    def difficulties_cleared(self) -> int:
        return sum(action.difficulty_cleared for action in self.actions)


def build_cleanup_report(root: Path) -> CleanupReport:
    """Build deterministic changes entirely in memory."""

    root = root.resolve()
    actions: list[CleanupAction] = []
    subcategories: list[str] = []
    non_exempt_difficulties: list[str] = []

    for path in sorted(root.rglob("*.md")):
        article = path.relative_to(root).as_posix()
        original = path.read_bytes()
        text = original.decode("utf-8")
        match = FRONT_MATTER_RE.match(text)
        if not match:
            continue

        front_matter = match.group(0)
        data = _load_front_matter(front_matter, article)
        if data is None:
            continue

        tags = data.get("tags")
        expected_tag_removals = (
            sum(item == "none" for item in tags) if isinstance(tags, list) else 0
        )
        literal_none_difficulty = data.get("difficulty") == "None"
        difficulty_exempt = literal_none_difficulty and _difficulty_is_exempt(
            path,
            root,
        )

        if data.get("subcategory") == "None":
            subcategories.append(article)
        if literal_none_difficulty and not difficulty_exempt:
            non_exempt_difficulties.append(article)

        if not expected_tag_removals and not difficulty_exempt:
            continue

        updated_front_matter = _patch_front_matter(
            front_matter,
            expected_tag_removals=expected_tag_removals,
            clear_difficulty=difficulty_exempt,
            article=article,
        )
        updated_text = updated_front_matter + text[match.end() :]
        updated = updated_text.encode("utf-8")
        if updated == original:
            raise RuntimeError(f"Sentinel cleanup produced no change: {article}")
        actions.append(
            CleanupAction(
                article=article,
                path=path,
                original=original,
                updated=updated,
                tag_removals=expected_tag_removals,
                difficulty_cleared=difficulty_exempt,
            )
        )

    return CleanupReport(
        actions=tuple(actions),
        literal_none_subcategories=tuple(sorted(subcategories)),
        non_exempt_literal_none_difficulties=tuple(sorted(non_exempt_difficulties)),
    )


def apply_cleanup(report: CleanupReport, root: Path, backup: Path) -> None:
    """Apply a previously built report after exact byte precondition checks."""

    if not report.actions:
        return
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")

    root = root.resolve()
    for action in report.actions:
        if action.path.read_bytes() != action.original:
            raise RuntimeError(
                f"Sentinel cleanup precondition mismatch: {action.article}"
            )
        try:
            action.path.relative_to(root)
        except ValueError as error:
            raise RuntimeError(
                f"Refusing sentinel cleanup outside repository: {action.path}"
            ) from error

    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)

    for action in report.actions:
        _atomic_write(action.path, action.updated)


def _load_front_matter(front_matter: str, article: str) -> dict | None:
    lines = front_matter.splitlines()
    yaml_text = "\n".join(lines[1:-1])
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as error:
        raise RuntimeError(f"Malformed YAML in {article}: {error}") from error
    if data is None:
        return None
    if not isinstance(data, dict):
        raise RuntimeError(f"Front matter is not a mapping: {article}")
    return data


def _difficulty_is_exempt(path: Path, root: Path) -> bool:
    relative_path = path.relative_to(root)
    article = Article(
        id=relative_path.with_suffix("").as_posix(),
        filename=path.name,
        path=path,
        relative_path=relative_path,
        directory=relative_path.parent.as_posix(),
    )
    return not MetadataValidator._requires_difficulty(article)


def _patch_front_matter(
    front_matter: str,
    *,
    expected_tag_removals: int,
    clear_difficulty: bool,
    article: str,
) -> str:
    lines = front_matter.splitlines(keepends=True)
    tag_removals = 0
    difficulty_clears = 0
    updated: list[str] = []
    in_tags = False

    for line in lines:
        if TAGS_KEY_RE.fullmatch(line):
            in_tags = True
            updated.append(line)
            continue
        if in_tags and TOP_LEVEL_KEY_RE.fullmatch(line):
            in_tags = False
        if in_tags and NONE_TAG_RE.fullmatch(line):
            tag_removals += 1
            continue
        if clear_difficulty:
            match = DIFFICULTY_NONE_RE.fullmatch(line)
            if match:
                difficulty_clears += 1
                updated.append(f"{match.group('prefix')}''{match.group('suffix')}")
                continue
        updated.append(line)

    if tag_removals != expected_tag_removals:
        raise RuntimeError(
            f"Unsafe tags precondition in {article}: expected "
            f"{expected_tag_removals} exact 'none' item(s), found {tag_removals}"
        )
    expected_difficulty_clears = int(clear_difficulty)
    if difficulty_clears != expected_difficulty_clears:
        raise RuntimeError(
            f"Unsafe difficulty precondition in {article}: expected "
            f"{expected_difficulty_clears} literal 'None' line(s), found "
            f"{difficulty_clears}"
        )
    return "".join(updated)


def _atomic_write(path: Path, content: bytes) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
        os.replace(temporary_name, path)
    except OSError:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise
