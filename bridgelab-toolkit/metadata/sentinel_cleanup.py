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
SUBCATEGORY_NONE_RE = re.compile(
    r"^(?P<prefix>subcategory:[ \t]*)None"
    r"(?P<suffix>[ \t]*(?:#[^\r\n]*)?(?:\r?\n|\Z))"
)
REVIEWED_EMPTY_SUBCATEGORIES = {
    "bridge-lab-index.md",
    "duplicates/duplicates-index.md",
}
REVIEWED_GENERATED_REFERENCE_SUBCATEGORIES = {
    "acronyms.md": "acronyms",
    "bibliography.md": "bibliography",
    "glossary.md": "glossary",
}


@dataclass(frozen=True, slots=True)
class CleanupAction:
    article: str
    path: Path
    original: bytes
    updated: bytes
    tag_removals: int
    difficulty_cleared: bool
    subcategory_replacement: str | None = None

    @property
    def subcategory_cleared(self) -> bool:
        return self.subcategory_replacement == ""


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

    @property
    def subcategories_cleared(self) -> int:
        return sum(action.subcategory_cleared for action in self.actions)

    @property
    def subcategories_assigned(self) -> int:
        return sum(
            action.subcategory_replacement not in (None, "") for action in self.actions
        )


def build_cleanup_report(
    root: Path,
    *,
    only_reviewed_empty_subcategories: bool = False,
    only_reviewed_generated_reference_subcategories: bool = False,
) -> CleanupReport:
    """Build deterministic changes entirely in memory."""

    if (
        only_reviewed_empty_subcategories
        and only_reviewed_generated_reference_subcategories
    ):
        raise ValueError("Reviewed subcategory modes are mutually exclusive")

    reviewed_subcategory_mode = (
        only_reviewed_empty_subcategories
        or only_reviewed_generated_reference_subcategories
    )
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
            0
            if reviewed_subcategory_mode
            else sum(item == "none" for item in tags) if isinstance(tags, list) else 0
        )
        literal_none_difficulty = (
            not reviewed_subcategory_mode and data.get("difficulty") == "None"
        )
        difficulty_exempt = literal_none_difficulty and _difficulty_is_exempt(
            path,
            root,
        )
        subcategory_replacement: str | None = None
        if (
            only_reviewed_empty_subcategories
            and article in REVIEWED_EMPTY_SUBCATEGORIES
            and data.get("subcategory") == "None"
        ):
            subcategory_replacement = ""
        if (
            only_reviewed_generated_reference_subcategories
            and article in REVIEWED_GENERATED_REFERENCE_SUBCATEGORIES
            and data.get("subcategory") == "None"
        ):
            subcategory_replacement = REVIEWED_GENERATED_REFERENCE_SUBCATEGORIES[
                article
            ]

        if data.get("subcategory") == "None":
            if subcategory_replacement is None:
                subcategories.append(article)
        if literal_none_difficulty and not difficulty_exempt:
            non_exempt_difficulties.append(article)

        if (
            not expected_tag_removals
            and not difficulty_exempt
            and subcategory_replacement is None
        ):
            continue

        updated_front_matter = _patch_front_matter(
            front_matter,
            remove_tags=not reviewed_subcategory_mode,
            expected_tag_removals=expected_tag_removals,
            clear_difficulty=difficulty_exempt,
            subcategory_replacement=subcategory_replacement,
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
                subcategory_replacement=subcategory_replacement,
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
    remove_tags: bool,
    expected_tag_removals: int,
    clear_difficulty: bool,
    subcategory_replacement: str | None,
    article: str,
) -> str:
    lines = front_matter.splitlines(keepends=True)
    tag_removals = 0
    difficulty_clears = 0
    subcategory_clears = 0
    updated: list[str] = []
    in_tags = False

    for line in lines:
        if TAGS_KEY_RE.fullmatch(line):
            in_tags = True
            updated.append(line)
            continue
        if in_tags and TOP_LEVEL_KEY_RE.fullmatch(line):
            in_tags = False
        if remove_tags and in_tags and NONE_TAG_RE.fullmatch(line):
            tag_removals += 1
            continue
        if clear_difficulty:
            match = DIFFICULTY_NONE_RE.fullmatch(line)
            if match:
                difficulty_clears += 1
                updated.append(f"{match.group('prefix')}''{match.group('suffix')}")
                continue
        if subcategory_replacement is not None:
            match = SUBCATEGORY_NONE_RE.fullmatch(line)
            if match:
                subcategory_clears += 1
                replacement = (
                    "''" if subcategory_replacement == "" else subcategory_replacement
                )
                updated.append(
                    f"{match.group('prefix')}{replacement}{match.group('suffix')}"
                )
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
    expected_subcategory_clears = int(subcategory_replacement is not None)
    if subcategory_clears != expected_subcategory_clears:
        raise RuntimeError(
            f"Unsafe subcategory precondition in {article}: expected "
            f"{expected_subcategory_clears} literal 'None' line(s), found "
            f"{subcategory_clears}"
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
