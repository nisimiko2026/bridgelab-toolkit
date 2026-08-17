"""Safe category-line repair for the reviewed defence endgame index."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.bidding_category_repair import _require_exact_category_line
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_ARTICLE = "play/defence/endgame-defence/endgame-defence-index.md"
EXPECTED_CATEGORY = "Card Play – Defence"
PROPOSED_CATEGORY = "play"


@dataclass(frozen=True, slots=True)
class PlayEndgameCategoryAction:
    article: str
    path: Path
    original: bytes
    updated: bytes
    current_category: str
    proposed_category: str
    subcategory: str
    retained_tag: str
    retained_tag_present: bool


@dataclass(frozen=True, slots=True)
class PlayEndgameCategoryReport:
    selected_files: int
    actions: tuple[PlayEndgameCategoryAction, ...]


def build_play_endgame_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the one reviewed category-line change entirely in memory."""

    root = root.resolve()
    path = root / Path(REVIEWED_ARTICLE)
    if not path.is_file():
        raise RuntimeError(f"Reviewed play category file is missing: {REVIEWED_ARTICLE}")
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {REVIEWED_ARTICLE}") from error
    front_match = FRONT_MATTER_RE.match(text)
    if not front_match:
        raise RuntimeError(f"Missing or malformed front matter: {REVIEWED_ARTICLE}")
    front_matter = front_match.group(0)
    data = _load_front_matter(front_matter, REVIEWED_ARTICLE)
    if data is None:
        raise RuntimeError(f"Empty front matter: {REVIEWED_ARTICLE}")
    current = data.get("category")
    if current == PROPOSED_CATEGORY:
        _require_exact_category_line(front_matter, PROPOSED_CATEGORY, REVIEWED_ARTICLE)
        return PlayEndgameCategoryReport(selected_files=1, actions=())
    if current != EXPECTED_CATEGORY:
        raise RuntimeError(
            f"Reviewed category precondition mismatch: {REVIEWED_ARTICLE}: "
            f"expected {EXPECTED_CATEGORY!r}, observed {current!r}"
        )
    match = _require_exact_category_line(
        front_matter, EXPECTED_CATEGORY, REVIEWED_ARTICLE
    )
    updated_front = (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
    updated = (updated_front + text[front_match.end() :]).encode("utf-8")
    tags = data.get("tags")
    retained_tag = EXPECTED_CATEGORY.casefold()
    action = PlayEndgameCategoryAction(
        article=REVIEWED_ARTICLE,
        path=path,
        original=original,
        updated=updated,
        current_category=EXPECTED_CATEGORY,
        proposed_category=PROPOSED_CATEGORY,
        subcategory=str(data.get("subcategory") or ""),
        retained_tag=retained_tag,
        retained_tag_present=isinstance(tags, list) and retained_tag in tags,
    )
    return PlayEndgameCategoryReport(selected_files=1, actions=(action,))


def apply_play_endgame_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed action after all source preconditions pass."""

    if not report.actions:
        return
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    root = root.resolve()
    action = report.actions[0]
    try:
        action.path.resolve().relative_to(root)
    except ValueError as error:
        raise RuntimeError(
            f"Refusing category repair outside repository: {action.path}"
        ) from error
    if action.path.read_bytes() != action.original:
        raise RuntimeError(
            f"Reviewed category precondition mismatch: {action.article}"
        )

    destination = backup / action.path.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(action.path, destination)
    _atomic_write(action.path, action.updated)
