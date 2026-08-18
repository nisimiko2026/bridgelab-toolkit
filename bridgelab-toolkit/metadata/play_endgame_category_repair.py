"""Safe category-line repair for the reviewed defence endgame index."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from metadata.bidding_category_repair import _require_exact_category_line
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_ARTICLE = "play/defence/endgame-defence/endgame-defence-index.md"
REVIEWED_COUNTING_ARTICLE = "play/defence/counting/defence-counting-index.md"
REVIEWED_SIGNALING_ARTICLE = "play/defence/signaling/signaling-index.md"
REVIEWED_PROBABILITY_ARTICLE = "play/declarer-play/probability/probability-index.md"
REVIEWED_DEFENCE_PLANNING_ARTICLE = "play/defence/planning/defence-planning-index.md"
REVIEWED_PRINCIPLES_CATEGORIES = {
    "play/principles/play-principles-index.md": "Card Play – Fundamentals",
    "play/principles/preservation-of-entries.md": "techniques/card-play",
}
REVIEWED_TRUMP_PLAY_CATEGORIES = {
    "play/declarer-play/trump-play/cross-ruff.md": "techniques/declarer-techniques",
    "play/declarer-play/trump-play/drawing-trumps.md": "techniques/declarer-techniques",
    "play/declarer-play/trump-play/ruffing-losers.md": "techniques/declarer-techniques",
    "play/declarer-play/trump-play/trump-management.md": "techniques/declarer-techniques",
}
REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES = {
    "play/defence/techniques/defence-techniques-index.md": "Card Play – Defence",
    "play/defence/techniques/trump-promotion.md": "techniques/defensive-techniques",
}
REVIEWED_ENDPLAYS_CATEGORIES = {
    "play/declarer-play/elimination-and-endplays/elimination-index.md": (
        "Card Play – Declarer Play – Techniques"
    ),
    "play/declarer-play/elimination-and-endplays/exit-card.md": "techniques/endplays",
    "play/declarer-play/elimination-and-endplays/strip-and-endplay.md": (
        "techniques/endplays"
    ),
}
REVIEWED_COUPS_CATEGORIES = {
    "play/declarer-play/coups/coups-index.md": "Card Play – Advanced Techniques",
    "play/declarer-play/coups/crocodile-coup.md": "techniques/coups",
    "play/declarer-play/coups/deschapelles-coup.md": "techniques/coups",
    "play/declarer-play/coups/grand-coup.md": "techniques/coups",
}
REVIEWED_FINESSES_CATEGORIES = {
    "play/declarer-play/general-techniques/finesses/backward-finesse.md": "techniques/finessing",
    "play/declarer-play/general-techniques/finesses/delayed-finesse.md": "techniques/finessing",
    "play/declarer-play/general-techniques/finesses/finesses-index.md": "Card Play – Techniques",
    "play/declarer-play/general-techniques/finesses/first-round-finesse.md": "techniques/finessing",
    "play/declarer-play/general-techniques/finesses/marked-finesse.md": "techniques/finessing",
    "play/declarer-play/general-techniques/finesses/repeat-finesse.md": "techniques/finessing",
    "play/declarer-play/general-techniques/finesses/two-way-finesse.md": "techniques/finessing",
}
REVIEWED_GENERAL_TECHNIQUES_CATEGORIES = {
    "play/declarer-play/general-techniques/communication.md": "techniques/card-play",
    "play/declarer-play/general-techniques/overtake.md": "techniques/card-play",
    "play/declarer-play/general-techniques/unblock.md": "techniques/card-play",
}
REVIEWED_DECLARER_DECEPTION_CATEGORIES = {
    "play/declarer-play/deceptive-play/concealment.md": "techniques/deception",
    "play/declarer-play/deceptive-play/deception.md": "techniques/deception",
    "play/declarer-play/deceptive-play/deceptive-signals.md": "techniques/deception",
    "play/declarer-play/deceptive-play/declarer-false-carding.md": "techniques/deception",
    "play/declarer-play/deceptive-play/index-deceptive-play.md": (
        "Card Play – Declarer Play"
    ),
}
REVIEWED_DECLARER_NOTRUMP_CATEGORIES = {
    "play/declarer-play/notrump-play/communication-in-notrump.md": "card-play/notrump-play",
    "play/declarer-play/notrump-play/dangerous-opponent.md": "card-play/notrump-play",
    "play/declarer-play/notrump-play/establishing-long-suits.md": "card-play/notrump-play",
    "play/declarer-play/notrump-play/hold-up-play.md": "techniques/declarer-techniques",
    "play/declarer-play/notrump-play/index-notrump-play.md": "Card Play – Declarer Play",
    "play/declarer-play/notrump-play/keeping-the-lead.md": "card-play/notrump-play",
    "play/declarer-play/notrump-play/notrump-play.md": "card-play/notrump-play",
    "play/declarer-play/notrump-play/timing-in-notrump.md": "card-play/notrump-play",
}
REVIEWED_DECLARER_SQUEEZES_CATEGORIES = {
    "play/declarer-play/squeezes/automatic-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/criss-cross-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/double-progressive-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/positional-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/progressive-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/pseudo-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/squeeze-without-the-count.md": "techniques/squeezes",
    "play/declarer-play/squeezes/squeezes-index.md": "Card Play – Advanced Techniques",
    "play/declarer-play/squeezes/triple-squeeze.md": "techniques/squeezes",
    "play/declarer-play/squeezes/trump-squeeze.md": "techniques/squeezes",
}
REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES = {
    "play/defence/opening-leads/fourth-best.md": "defence/opening-leads",
    "play/defence/opening-leads/honor-leads/index-honor-leads.md": (
        "Card Play – Defence – Opening Leads"
    ),
    "play/defence/opening-leads/lead-partners-suit.md": "defence/opening-leads",
    "play/defence/opening-leads/leading-from-honor-holdings.md": "defence/opening-leads",
    "play/defence/opening-leads/leads-against-slam.md": "defence/opening-leads",
    "play/defence/opening-leads/leads-against-suit.md": "defence/opening-leads",
    "play/defence/opening-leads/opening-leads-index.md": "Card Play – Defence",
    "play/defence/opening-leads/rusinow.md": "defence/opening-leads",
    "play/defence/opening-leads/third-fifth.md": "defence/opening-leads",
    "play/defence/opening-leads/top-of-nothing.md": "defence/opening-leads",
}
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
    canonical_tag_present: bool


@dataclass(frozen=True, slots=True)
class PlayEndgameCategoryReport:
    selected_files: int
    actions: tuple[PlayEndgameCategoryAction, ...]


def build_play_endgame_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the one reviewed category-line change entirely in memory."""

    return _build_play_category_report(
        root, REVIEWED_ARTICLE, EXPECTED_CATEGORY, "defence"
    )


def build_play_counting_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the reviewed defence-counting category change in memory."""

    return _build_play_category_report(
        root, REVIEWED_COUNTING_ARTICLE, EXPECTED_CATEGORY, "defence"
    )


def build_play_signaling_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the reviewed defence-signaling category change in memory."""

    return _build_play_category_report(
        root, REVIEWED_SIGNALING_ARTICLE, EXPECTED_CATEGORY, "defence"
    )


def build_play_probability_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the reviewed declarer-probability category change in memory."""

    return _build_play_category_report(
        root,
        REVIEWED_PROBABILITY_ARTICLE,
        "Card Play – Principles",
        "declarer-play",
        require_canonical_tag_absent=True,
    )


def build_play_defence_planning_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the reviewed defence-planning index category change in memory."""

    return _build_play_category_report(
        root,
        REVIEWED_DEFENCE_PLANNING_ARTICLE,
        "Card Play – Defence",
        "defence",
        require_canonical_tag_absent=True,
    )


def build_play_principles_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the exact reviewed two-file principles batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_PRINCIPLES_CATEGORIES.items():
        report = _build_play_category_report(
            root, article, expected_category, "principles"
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_PRINCIPLES_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_trump_play_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the exact reviewed four-file trump-play batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_TRUMP_PLAY_CATEGORIES.items():
        report = _build_play_category_report(
            root, article, expected_category, "declarer-play"
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_TRUMP_PLAY_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_defence_techniques_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed two-file defence-techniques batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "defence",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_endplays_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the exact reviewed three-file declarer-endplays batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_ENDPLAYS_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_ENDPLAYS_CATEGORIES), actions=tuple(actions)
    )


def build_play_coups_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the exact reviewed four-file declarer-coups batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_COUPS_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_COUPS_CATEGORIES), actions=tuple(actions)
    )


def build_play_finesses_category_report(root: Path) -> PlayEndgameCategoryReport:
    """Build the exact reviewed seven-file declarer-finesses batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_FINESSES_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_FINESSES_CATEGORIES), actions=tuple(actions)
    )


def build_play_general_techniques_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed three-file general-techniques batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_GENERAL_TECHNIQUES_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_GENERAL_TECHNIQUES_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_declarer_deception_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed five-file declarer-deception batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_DECLARER_DECEPTION_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_DECLARER_DECEPTION_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_declarer_notrump_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed eight-file declarer-notrump batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_DECLARER_NOTRUMP_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_DECLARER_NOTRUMP_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_declarer_squeezes_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed ten-file declarer-squeezes batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_DECLARER_SQUEEZES_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "declarer-play",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_DECLARER_SQUEEZES_CATEGORIES),
        actions=tuple(actions),
    )


def build_play_defence_opening_leads_category_report(
    root: Path,
) -> PlayEndgameCategoryReport:
    """Build the exact reviewed ten-file defence opening-leads batch in memory."""

    actions = []
    for article, expected_category in REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES.items():
        report = _build_play_category_report(
            root,
            article,
            expected_category,
            "defence",
            require_canonical_tag_absent=True,
        )
        actions.extend(report.actions)
    return PlayEndgameCategoryReport(
        selected_files=len(REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES),
        actions=tuple(actions),
    )


def _build_play_category_report(
    root: Path,
    reviewed_article: str,
    expected_category: str,
    expected_subcategory: str,
    *,
    require_canonical_tag_absent: bool = False,
) -> PlayEndgameCategoryReport:
    """Build one explicitly allowlisted play category-line action."""

    root = root.resolve()
    path = root / Path(reviewed_article)
    if not path.is_file():
        raise RuntimeError(f"Reviewed play category file is missing: {reviewed_article}")
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Article is not valid UTF-8: {reviewed_article}") from error
    front_match = FRONT_MATTER_RE.match(text)
    if not front_match:
        raise RuntimeError(f"Missing or malformed front matter: {reviewed_article}")
    front_matter = front_match.group(0)
    data = _load_front_matter(front_matter, reviewed_article)
    if data is None:
        raise RuntimeError(f"Empty front matter: {reviewed_article}")
    subcategory = data.get("subcategory")
    if subcategory != expected_subcategory:
        raise RuntimeError(
            f"Reviewed subcategory precondition mismatch: {reviewed_article}: "
            f"expected {expected_subcategory!r}, observed {subcategory!r}"
        )
    retained_tag = expected_category.casefold()
    tags = data.get("tags")
    if not isinstance(tags, list) or retained_tag not in tags:
        raise RuntimeError(
            f"Reviewed retained-tag precondition mismatch: {reviewed_article}: "
            f"expected {retained_tag!r}"
        )
    if require_canonical_tag_absent and PROPOSED_CATEGORY in tags:
        raise RuntimeError(
            f"Reviewed broad-tag precondition mismatch: {reviewed_article}: "
            f"unexpected {PROPOSED_CATEGORY!r} tag"
        )
    current = data.get("category")
    if current == PROPOSED_CATEGORY:
        _require_exact_category_line(front_matter, PROPOSED_CATEGORY, reviewed_article)
        return PlayEndgameCategoryReport(selected_files=1, actions=())
    if current != expected_category:
        raise RuntimeError(
            f"Reviewed category precondition mismatch: {reviewed_article}: "
            f"expected {expected_category!r}, observed {current!r}"
        )
    match = _require_exact_category_line(
        front_matter, expected_category, reviewed_article
    )
    updated_front = (
        front_matter[: match.start()]
        + f"category: {PROPOSED_CATEGORY}{match.group('ending')}"
        + front_matter[match.end() :]
    )
    updated = (updated_front + text[front_match.end() :]).encode("utf-8")
    action = PlayEndgameCategoryAction(
        article=reviewed_article,
        path=path,
        original=original,
        updated=updated,
        current_category=expected_category,
        proposed_category=PROPOSED_CATEGORY,
        subcategory=expected_subcategory,
        retained_tag=retained_tag,
        retained_tag_present=isinstance(tags, list) and retained_tag in tags,
        canonical_tag_present=isinstance(tags, list) and PROPOSED_CATEGORY in tags,
    )
    return PlayEndgameCategoryReport(selected_files=1, actions=(action,))


def apply_play_endgame_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed action after all source preconditions pass."""

    _apply_play_category_report(report, root, backup)


def apply_play_counting_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed counting action using the same safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_signaling_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed signaling action using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_probability_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed probability action using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_defence_planning_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the defence-planning index action using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_principles_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed principles batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_trump_play_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the reviewed trump-play batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_defence_techniques_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the defence-techniques batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_endplays_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-endplays batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_coups_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-coups batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_finesses_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-finesses batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_general_techniques_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the general-techniques batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_declarer_deception_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-deception batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_declarer_notrump_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-notrump batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_declarer_squeezes_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the declarer-squeezes batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def apply_play_defence_opening_leads_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Apply the defence opening-leads batch using the shared safety contract."""

    _apply_play_category_report(report, root, backup)


def _apply_play_category_report(
    report: PlayEndgameCategoryReport, root: Path, backup: Path
) -> None:
    """Preflight all reviewed actions, back up all, then replace sequentially."""

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
