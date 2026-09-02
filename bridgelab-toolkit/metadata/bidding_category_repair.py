"""Dry-run-first repair for the reviewed bidding structural categories."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_BIDDING_CATEGORIES = {
    "bidding/convention-cards/convention-cards-index.md": "Bidding – Principles",
    "bidding/conventions/game-invitations/2nt-game-try.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/artificial-game-tries.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/guides/choosing-a-game-try.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/common-mistakes.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/expert-game-try-agreements.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/game-try-comparison.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/opener-evaluation.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/responder-evaluation.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/guides/simple-game-try-agreements.md": "Conventions – Game Invitations – Guides",
    "bidding/conventions/game-invitations/help-suit-game-try.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/long-suit-game-try.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/maximal-game-try.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/short-suit-game-try.md": "Conventions – Game Invitations",
    "bidding/conventions/game-invitations/two-way-game-try.md": "Conventions – Game Invitations",
    "bidding/principles/bidding-fundamentals/index-fundamental-bids.md": "Bidding – Natural Bidding",
    "bidding/principles/partnership/partnership-principles-index.md": "Bidding – Principles",
    "bidding/principles/principles-index.md": "Bidding – Principles",
    "bidding/systems/systems-index.md": "Bidding – Systems",
}


@dataclass(frozen=True, slots=True)
class BiddingCategoryAction:
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
class BiddingCategoryReport:
    reviewed_files: int
    actions: tuple[BiddingCategoryAction, ...]


def build_bidding_category_report(root: Path) -> BiddingCategoryReport:
    """Build exact byte changes for the approved 19 paths entirely in memory."""

    root = root.resolve()
    actions: list[BiddingCategoryAction] = []
    for article, expected in sorted(REVIEWED_BIDDING_CATEGORIES.items()):
        path = root / Path(article)
        if not path.is_file():
            raise RuntimeError(f"Reviewed bidding category file is missing: {article}")
        original = path.read_bytes()
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RuntimeError(f"Article is not valid UTF-8: {article}") from error
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front_matter = front_match.group(0)
        data = _load_front_matter(front_matter, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")
        current = data.get("category")
        if current == "bidding":
            _require_exact_category_line(front_matter, "bidding", article)
            continue
        if current != expected:
            raise RuntimeError(
                f"Reviewed category precondition mismatch: {article}: "
                f"expected {expected!r}, observed {current!r}"
            )
        updated_front = _replace_exact_category(front_matter, expected, article)
        updated = (updated_front + text[front_match.end() :]).encode("utf-8")
        if updated == original:
            raise RuntimeError(f"Reviewed category repair produced no change: {article}")
        tags = data.get("tags")
        retained_tag = expected.casefold()
        actions.append(
            BiddingCategoryAction(
                article=article,
                path=path,
                original=original,
                updated=updated,
                current_category=expected,
                proposed_category="bidding",
                subcategory=str(data.get("subcategory") or ""),
                retained_tag=retained_tag,
                retained_tag_present=(
                    isinstance(tags, list) and retained_tag in tags
                ),
            )
        )
    return BiddingCategoryReport(
        reviewed_files=len(REVIEWED_BIDDING_CATEGORIES),
        actions=tuple(actions),
    )


def apply_bidding_category_report(
    report: BiddingCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the exact report after validating the entire batch."""

    if not report.actions:
        return
    if backup.exists():
        raise RuntimeError(f"Backup destination already exists: {backup}")
    root = root.resolve()
    for action in report.actions:
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

    for action in report.actions:
        destination = backup / action.path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.path, destination)

    for action in report.actions:
        _atomic_write(action.path, action.updated)


def _require_exact_category_line(
    front_matter: str, value: str, article: str
) -> re.Match[str]:
    pattern = re.compile(rf"^category: {re.escape(value)}(?P<ending>\r?\n|\Z)", re.MULTILINE)
    matches = list(pattern.finditer(front_matter))
    if len(matches) != 1:
        raise RuntimeError(
            f"Unsafe category line precondition in {article}: expected one exact "
            f"category: {value} line, found {len(matches)}"
        )
    return matches[0]


def _replace_exact_category(front_matter: str, value: str, article: str) -> str:
    match = _require_exact_category_line(front_matter, value, article)
    return (
        front_matter[: match.start()]
        + f"category: bidding{match.group('ending')}"
        + front_matter[match.end() :]
    )
