"""Safe Phase 4B Batch 9A parenthetical-alias metadata repair."""

from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.document_roles import DocumentRole, classify_document_role
from metadata.sentinel_cleanup import FRONT_MATTER_RE, _atomic_write, _load_front_matter


REVIEWED_ALIASES = {
    "bidding/conventions/competitive/negative-free-bid.md": ("NFB",),
    "bidding/conventions/competitive/unusual-vs-unusual.md": ("UvU",),
    "bidding/conventions/game-invitations/artificial-game-tries.md": ("AGT",),
    "bidding/conventions/game-invitations/two-way-game-try.md": ("TWGT",),
    "bidding/conventions/responses/fourth-suit-forcing.md": ("4SF",),
    "bidding/conventions/responses/new-minor-forcing.md": ("NMF",),
    "bidding/conventions/slam-conventions/ace-asking-bid.md": ("AAB",),
    "bidding/conventions/slam-conventions/control-asking-bid.md": ("CAB",),
    "bidding/conventions/slam-conventions/exclusion-blackwood.md": ("Voidwood",),
    "bidding/conventions/slam-conventions/trump-asking-bid.md": ("TAB",),
    "bidding/principles/bidding-fundamentals/losing-trick-count.md": ("LTC",),
    "bidding/systems/benjamin-acol.md": ("Benjaminised Acol", "Benji Acol"),
    "bidding/systems/ehaa.md": ("Every Hand An Adventure",),
    "bidding/systems/sef.md": ("Système d'Enseignement Français",),
    "play/defence/signaling/standard-signals.md": ("Standard Carding",),
}

REVIEWED_TITLE_H1 = {
    "bidding/conventions/competitive/negative-free-bid.md": (
        "Negative Free Bid",
        "Negative Free Bid (NFB)",
    ),
    "bidding/conventions/competitive/unusual-vs-unusual.md": (
        "Unusual vs. Unusual",
        "Unusual vs. Unusual (UvU)",
    ),
    "bidding/conventions/game-invitations/artificial-game-tries.md": (
        "Artificial Game Tries",
        "Artificial Game Tries (AGT)",
    ),
    "bidding/conventions/game-invitations/two-way-game-try.md": (
        "Two-Way Game Try",
        "Two-Way Game Try (TWGT)",
    ),
    "bidding/conventions/responses/fourth-suit-forcing.md": (
        "Fourth Suit Forcing",
        "Fourth Suit Forcing (4SF)",
    ),
    "bidding/conventions/responses/new-minor-forcing.md": (
        "New Minor Forcing",
        "New Minor Forcing (NMF)",
    ),
    "bidding/conventions/slam-conventions/ace-asking-bid.md": (
        "Ace-Asking Bid",
        "Ace-Asking Bid (AAB)",
    ),
    "bidding/conventions/slam-conventions/control-asking-bid.md": (
        "Control-Asking Bid",
        "Control-Asking Bid (CAB)",
    ),
    "bidding/conventions/slam-conventions/exclusion-blackwood.md": (
        "Exclusion Blackwood",
        "Exclusion Blackwood (Voidwood)",
    ),
    "bidding/conventions/slam-conventions/trump-asking-bid.md": (
        "Trump-Asking Bid",
        "Trump-Asking Bid (TAB)",
    ),
    "bidding/principles/bidding-fundamentals/losing-trick-count.md": (
        "Losing Trick Count",
        "Losing Trick Count (LTC)",
    ),
    "bidding/systems/benjamin-acol.md": (
        "Benjamin Acol",
        "Benjamin Acol (Benjaminised Acol / Benji Acol)",
    ),
    "bidding/systems/ehaa.md": ("EHAA", "EHAA (Every Hand An Adventure)"),
    "bidding/systems/sef.md": ("SEF", "SEF (Système d'Enseignement Français)"),
    "play/defence/signaling/standard-signals.md": (
        "Standard Signals",
        "Standard Signals (Standard Carding)",
    ),
}

REVIEWED_SOURCE_SHA256 = {
    "bidding/conventions/competitive/negative-free-bid.md": "a3b5ea4f4ffd2788c2c3fcbc3efe60fed21b6b5c6feb4007e7a417a8633f3469",
    "bidding/conventions/competitive/unusual-vs-unusual.md": "3d78084fa270b8e26a834a22f40759f9a8bbcc2c3c2e8341dd551a62b89cb3e5",
    "bidding/conventions/game-invitations/artificial-game-tries.md": "26c65fdb28f918daed42811a5a58a8a32b2eb57f05203212e1cb0e8848235ca0",
    "bidding/conventions/game-invitations/two-way-game-try.md": "51052821a2a071fdde689dc88817f2d734bec45c83ce2cfb6ca49a2c8c7a0093",
    "bidding/conventions/responses/fourth-suit-forcing.md": "6b929e53dfbc92963ad4e976b78a1824caa032756e0e3a1a3a13f4a8ed975979",
    "bidding/conventions/responses/new-minor-forcing.md": "56875afeb05eb70e1a43c5229db18683e202e7e2733b84d9ba1bdf1aa57e9ecd",
    "bidding/conventions/slam-conventions/ace-asking-bid.md": "27c4788dfd7a2ec45063ed08ae269fa1ed7421938d6ff9e5578417b6f0119f53",
    "bidding/conventions/slam-conventions/control-asking-bid.md": "65da6f197c1488c8f1992683d8e0dd2d67472f2f0ca441adf7f1700517eaae7b",
    "bidding/conventions/slam-conventions/exclusion-blackwood.md": "ef63c53ed856456e82f3c3c412edef53ef6797a572eab869e702b5c8b4d013a4",
    "bidding/conventions/slam-conventions/trump-asking-bid.md": "8262a44cf656bf38da2031279d6bb851beb6b967e9d0e4dfebcd58b74cb9f91f",
    "bidding/principles/bidding-fundamentals/losing-trick-count.md": "a9da2dbf6c6a9612e70cac78601e09f4ccd0a418d14032ae088e5663e0f2be8c",
    "bidding/systems/benjamin-acol.md": "9b9d75277b235653e8172104fcb3967346399047be9fd79a708eda6b90e6e6b1",
    "bidding/systems/ehaa.md": "b9cfacefd32364646990135129e98783e20b8b8ca0815e944cc2a1a9741d2629",
    "bidding/systems/sef.md": "e8e20f4b25ae6d51226b01bb912ed80e11e2ed10656c8ccf5f2c6847b3935941",
    "play/defence/signaling/standard-signals.md": "04901221b34733030e86852e4559dfee9f05358165dc90e5b407011adf769e46",
}

REVIEWED_POST_SHA256 = {
    "bidding/conventions/competitive/negative-free-bid.md": "ef69bff890b3dc1e2d5c60fe9b6b42ed9e541b52a1382ec27a1fc8f7538f50e2",
    "bidding/conventions/competitive/unusual-vs-unusual.md": "c959d4ff20be6bd20bc7753a06a9b41c5f6efc77b6c97e8aee99b8088181e55c",
    "bidding/conventions/game-invitations/artificial-game-tries.md": "65aecdfc745374aa0f14808649671937cc93a01c599308e4b2a83c8f2f140c75",
    "bidding/conventions/game-invitations/two-way-game-try.md": "295f333a0bda498a3e1ab897381165400b55be25124c64ac660ce175558f8039",
    "bidding/conventions/responses/fourth-suit-forcing.md": "505903520f988b729c430651bdf7f17aeaf29ed4c1ac24a149c6c29aff1b3de2",
    "bidding/conventions/responses/new-minor-forcing.md": "9ab79509e1626e61ed1e6a3fa0be671134ff9d01ce9b3295e0133f1afecf3a43",
    "bidding/conventions/slam-conventions/ace-asking-bid.md": "d2faa25e003583eeffe63228ec57c6ef7107b737e7b38e9b3f7378609c5f07ec",
    "bidding/conventions/slam-conventions/control-asking-bid.md": "769a284c82b3250dada1d00f414440a424b1e3eb88cbb684653289c679d132a2",
    "bidding/conventions/slam-conventions/exclusion-blackwood.md": "7c26935e3191ff22c46f17b5e40ebf0fa9d29879165c9d07b93cb43f1a0b5b3c",
    "bidding/conventions/slam-conventions/trump-asking-bid.md": "9c0bf4ea892eaa4d1f71e4406a9352ba5104fe8023b98593c30398a303a90c71",
    "bidding/principles/bidding-fundamentals/losing-trick-count.md": "b86df7e9ae99a23cdfcf1d095d30cce70f94cb868f9d7f1e396f6addeb0be451",
    "bidding/systems/benjamin-acol.md": "9c24a9b8f5060f5809d1dc339e87159dda71aef34bc8fac685d4063eec769522",
    "bidding/systems/ehaa.md": "90b1b12cf91a40a7d565ab4964e5357a4fd1db77576d2678f716b85c460ad352",
    "bidding/systems/sef.md": "037d3c7098ec3f8d9007434d1b98f6e7ae379f4b67122578feba3a42f0c18d03",
    "play/defence/signaling/standard-signals.md": "9510b17d58674b97fe3c5b247c88bd0bcaa89de7c3555784ddca6ed614b7ddd9",
}

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
PARENTHETICAL_RE = re.compile(r"^(?P<title>.+) \((?P<alternate>[^\r\n()]*)\)$")


@dataclass(frozen=True, slots=True)
class ParentheticalAliasesRepairAction:
    article: str
    path: Path
    aliases: tuple[str, ...]
    original: bytes
    updated: bytes


@dataclass(frozen=True, slots=True)
class ParentheticalAliasesRepairReport:
    selected_files: int
    actions: tuple[ParentheticalAliasesRepairAction, ...]


def build_title_h1_parenthetical_aliases_batch9_report(
    root: Path,
) -> ParentheticalAliasesRepairReport:
    """Build the exact reviewed 15-file alias plan entirely in memory."""
    root = _validated_root(root)
    reviewed = set(REVIEWED_ALIASES)
    observed = _parenthetical_article_population(root)
    if observed != reviewed:
        raise RuntimeError(
            "Reviewed parenthetical ARTICLE census mismatch: "
            f"missing={sorted(reviewed - observed)!r}, extra={sorted(observed - reviewed)!r}"
        )

    actions: list[ParentheticalAliasesRepairAction] = []
    for article, aliases in REVIEWED_ALIASES.items():
        path = root / article
        if not path.is_file():
            raise RuntimeError(f"Reviewed parenthetical-alias file is missing: {article}")
        original = path.read_bytes()
        text = _decode(original, article)
        front_match = FRONT_MATTER_RE.match(text)
        if not front_match:
            raise RuntimeError(f"Missing or malformed front matter: {article}")
        front = front_match.group(0)
        data = _load_front_matter(front, article)
        if data is None:
            raise RuntimeError(f"Empty front matter: {article}")

        expected_title, expected_h1 = REVIEWED_TITLE_H1[article]
        if data.get("title") != expected_title:
            raise RuntimeError(f"Reviewed title precondition mismatch: {article}")
        if _first_h1(text, article) != expected_h1:
            raise RuntimeError(f"Reviewed first-H1 precondition mismatch: {article}")
        if classify_document_role(article) is not DocumentRole.ARTICLE:
            raise RuntimeError(f"Reviewed document-role precondition mismatch: {article}")
        if data.get("acronyms") != []:
            raise RuntimeError(f"Reviewed acronyms precondition mismatch: {article}")

        current_aliases = data.get("aliases")
        observed_hash = hashlib.sha256(original).hexdigest()
        if current_aliases == list(aliases):
            if observed_hash != REVIEWED_POST_SHA256[article]:
                raise RuntimeError(f"Reviewed normalized post-image mismatch: {article}")
            _require_exact_alias_block(front, aliases, article)
            continue
        if current_aliases != []:
            raise RuntimeError(f"Reviewed aliases precondition mismatch: {article}")
        _require_exact_empty_alias_line(front, article)
        if observed_hash != REVIEWED_SOURCE_SHA256[article]:
            raise RuntimeError(
                f"Reviewed complete-byte source precondition mismatch: {article}: "
                f"expected {REVIEWED_SOURCE_SHA256[article]}, observed {observed_hash}"
            )

        updated = _build_post_image(original, aliases, article)
        if hashlib.sha256(updated).hexdigest() != REVIEWED_POST_SHA256[article]:
            raise RuntimeError(f"Reviewed post-image construction mismatch: {article}")
        actions.append(ParentheticalAliasesRepairAction(article, path, aliases, original, updated))

    return ParentheticalAliasesRepairReport(len(REVIEWED_ALIASES), tuple(actions))


def apply_title_h1_parenthetical_aliases_batch9_report(
    report: ParentheticalAliasesRepairReport,
    root: Path,
    backup: Path,
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
            raise RuntimeError(f"Refusing alias repair outside repository: {action.path}") from error
        if action.path.read_bytes() != action.original:
            raise RuntimeError(f"Reviewed complete-byte precondition mismatch: {action.article}")

    try:
        for action in report.actions:
            destination = backup / action.article
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(action.path, destination)
            if destination.read_bytes() != action.original:
                raise RuntimeError(f"Backup byte verification failed: {action.article}")
    except Exception:
        if backup.exists():
            shutil.rmtree(backup)
        raise

    try:
        for action in report.actions:
            _atomic_write(action.path, action.updated)
    except Exception as error:
        rollback_errors: list[str] = []
        for action in reversed(report.actions):
            try:
                if action.path.read_bytes() != action.original:
                    _atomic_write(action.path, action.original)
            except Exception as rollback_error:  # pragma: no cover - catastrophic I/O
                rollback_errors.append(f"{action.article}: {rollback_error}")
        if rollback_errors:
            raise RuntimeError(
                "Alias repair failed and rollback was incomplete: " + "; ".join(rollback_errors)
            ) from error
        raise


def _build_post_image(original: bytes, aliases: tuple[str, ...], article: str) -> bytes:
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    source = b"aliases: []"
    if original.count(source) != 1:
        raise RuntimeError(f"Unsafe aliases-line precondition: {article}")
    replacement = b"aliases:" + newline + newline.join(
        b"  - " + alias.encode("utf-8") for alias in aliases
    )
    return original.replace(source, replacement, 1)


def _parenthetical_article_population(root: Path) -> set[str]:
    observed: set[str] = set()
    for path in sorted(root.rglob("*.md")):
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
        parenthetical = PARENTHETICAL_RE.fullmatch(h1_match.group(1))
        if (
            parenthetical
            and parenthetical.group("title") == title
            and classify_document_role(article) is DocumentRole.ARTICLE
        ):
            observed.add(article)
    return observed


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


def _require_exact_alias_block(
    front: str,
    aliases: tuple[str, ...],
    article: str,
) -> None:
    newline = "\r\n" if "\r\n" in front else "\n"
    expected = "aliases:" + newline + newline.join(f"  - {alias}" for alias in aliases)
    if front.count(expected) != 1:
        raise RuntimeError(f"Unsafe normalized aliases-block precondition: {article}")


def _require_exact_empty_alias_line(front: str, article: str) -> None:
    pattern = re.compile(r"^aliases: \[\](?:\r?\n|\Z)", re.MULTILINE)
    if len(pattern.findall(front)) != 1:
        raise RuntimeError(f"Unsafe aliases-line precondition: {article}")
