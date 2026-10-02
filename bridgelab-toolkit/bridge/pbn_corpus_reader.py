"""Native PBN reader for BridgeLab canonical corpus ingestion.

A5.6.1 — Native PBN Corpus Reader.

PBN-specific syntax is normalized at the corpus boundary.
BridgeLab core objects remain independent of the external file format.

The reader deliberately does not infer bidding systems, conventions,
treatments, or partnership agreements from observed auctions.
"""

from __future__ import annotations

import re
from pathlib import Path

from .auction import Auction, Contract
from .corpus import CanonicalBoardRecord, SourceProvenance
from .deals import Deal
from .models import Hand, Seat, Vulnerability


_TAG_RE = re.compile(
    r'^\[([A-Za-z0-9_]+)\s*"([^"]*)"\]\s*$'
)

_ANNOTATION_REF_RE = re.compile(r"^=\d+=$")


_VULNERABILITY = {
    "NONE": Vulnerability.NONE,
    "-": Vulnerability.NONE,
    "LOVE": Vulnerability.NONE,
    "NS": Vulnerability.NS,
    "EW": Vulnerability.EW,
    "ALL": Vulnerability.BOTH,
    "BOTH": Vulnerability.BOTH,
}


def _seat(value: str) -> Seat:
    """Parse a PBN seat."""

    if not isinstance(value, str):
        raise TypeError(
            "seat must be a string"
        )

    return Seat.parse(
        value.strip().upper()
    )


def _vulnerability(
    value: str,
) -> Vulnerability:
    """Normalize PBN vulnerability notation."""

    if not isinstance(value, str):
        raise TypeError(
            "vulnerability must be a string"
        )

    key = value.strip().upper()

    try:
        return _VULNERABILITY[key]
    except KeyError as exc:
        raise ValueError(
            f"unsupported PBN vulnerability: {value!r}"
        ) from exc


def _parse_deal(
    value: str,
    *,
    seed: int,
) -> Deal:
    """Parse a complete four-hand PBN Deal tag.

    Example:

        W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 ...

    The seat before ':' identifies the first hand.
    The remaining hands proceed clockwise.

    The starting seat in the Deal tag is independent
    of the board dealer.
    """

    if not isinstance(value, str):
        raise TypeError(
            "PBN Deal value must be a string"
        )

    if ":" not in value:
        raise ValueError(
            "PBN Deal tag must contain starting seat"
        )

    seat_text, hands_text = value.split(
        ":",
        1,
    )

    first_seat = _seat(
        seat_text
    )

    hand_tokens = hands_text.split()

    if len(hand_tokens) != 4:
        raise ValueError(
            "PBN Deal tag must contain four hands"
        )

    hands: list[
        tuple[Seat, Hand]
    ] = []

    seat = first_seat

    for token in hand_tokens:
        hands.append(
            (
                seat,
                Hand.parse(token),
            )
        )

        seat = seat.next()

    return Deal(
        seed=seed,
        hands=tuple(hands),
    )



def _strip_pbn_comments(
    text: str,
) -> str:
    """Remove PBN brace comments, including multiline comments.

    PBN comments are annotations, not auction calls.  Replace comment
    characters with spaces while preserving newlines so surrounding
    tokens cannot be accidentally concatenated.
    """

    output: list[str] = []
    depth = 0

    for char in text:
        if char == "{":
            depth += 1
            output.append(" ")
            continue

        if char == "}" and depth:
            depth -= 1
            output.append(" ")
            continue

        if depth:
            output.append(
                "\n" if char == "\n" else " "
            )
        else:
            output.append(char)

    return "".join(output)


def _auction_tokens(
    lines: tuple[str, ...],
) -> tuple[str, ...]:
    """Return individual auction tokens."""

    tokens: list[str] = []

    cleaned_lines = _strip_pbn_comments(
        "\n".join(lines)
    ).splitlines()

    for line in cleaned_lines:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("%"):
            continue

        tokens.extend(
            token
            for token in stripped.split()
            if not _ANNOTATION_REF_RE.fullmatch(token)
        )

    return tuple(tokens)


def _normalize_pbn_call(
    value: str,
) -> str:
    """Normalize one PBN auction call."""

    stripped = value.strip()
    upper = stripped.upper()

    if upper == "PASS":
        return "P"

    if upper == "DOUBLE":
        return "X"

    if upper == "REDOUBLE":
        return "XX"

    # BridgeLab canonical bidding notation already
    # uses NT, so 1NT remains 1NT.
    return upper


def _parse_auction(
    *,
    dealer: Seat,
    lines: tuple[str, ...],
) -> tuple[Auction, bool]:
    """Parse a PBN auction.

    AP means "all pass from this point" and is expanded
    until BridgeLab reports the auction complete.

    Legacy source files can contain stray auction tokens after a legally
    completed auction.  Those tokens are ignored at the PBN boundary rather
    than being passed into BridgeLab core legality.  The returned boolean
    records whether meaningful trailing tokens were ignored.
    """

    auction = Auction(
        dealer
    )

    tokens = _auction_tokens(
        lines
    )

    ignored_trailing_tokens = False

    for index, token in enumerate(tokens):
        normalized = token.strip()

        if not normalized:
            continue

        if normalized == "*":
            break

        # Once BridgeLab reports a complete auction, any later PBN calls are
        # source-level trailing data.  Preserve that fact in provenance but
        # do not weaken or bypass core auction legality.
        if auction.is_complete:
            ignored_trailing_tokens = any(
                remaining.strip()
                and remaining.strip() != "*"
                for remaining in tokens[index:]
            )
            break

        upper = normalized.upper()

        if upper == "AP":
            while not auction.is_complete:
                auction.add("P")

            if any(
                remaining.strip()
                and remaining.strip() != "*"
                for remaining in tokens[index + 1:]
            ):
                ignored_trailing_tokens = True
            break

        auction.add(
            _normalize_pbn_call(
                normalized
            )
        )

    return auction, ignored_trailing_tokens


def _parse_optional_int(
    value: str | None,
) -> int | None:
    """Parse an optional integer PBN tag."""

    if value is None:
        return None

    stripped = value.strip()

    if not stripped:
        return None

    if stripped == "#":
        return None

    return int(
        stripped
    )


def _parse_optional_contract(
    value: str | None,
    *,
    declarer: str | None = None,
) -> Contract | None:
    """Convert PBN contract tags to BridgeLab canonical form.

    PBN stores contract and declarer separately:

        [Contract "3NT"]
        [Declarer "N"]

    BridgeLab Contract.parse expects:

        "3NT N"

    No NT -> N conversion is performed because BridgeLab's
    canonical bid notation itself uses NT.
    """

    if value is None:
        return None

    stripped = value.strip()

    if not stripped:
        return None

    if stripped == "#":
        return None

    if stripped.upper() in {
        "PASS",
        "PASSEDOUT",
    }:
        return None

    if declarer is None:
        raise ValueError(
            "PBN contract requires Declarer"
        )

    declarer_text = (
        declarer.strip().upper()
    )

    if (
        not declarer_text
        or declarer_text == "#"
    ):
        raise ValueError(
            "PBN contract requires Declarer"
        )

    normalized_contract = (
        stripped.upper()
    )

    return Contract.parse(
        f"{normalized_contract} "
        f"{declarer_text}"
    )


def _record_from_block(
    *,
    tags: dict[str, str],
    auction_lines: tuple[str, ...],
    provider: str,
    source: str,
    provider_version: str | None,
    record_index: int,
    transformations: tuple[str, ...] = (),
) -> CanonicalBoardRecord | None:
    """Convert one PBN board block to a canonical record."""

    required = (
        "Dealer",
        "Vulnerable",
        "Deal",
    )

    if not all(
        name in tags
        for name in required
    ):
        return None

    dealer = _seat(
        tags["Dealer"]
    )

    vulnerability = _vulnerability(
        tags["Vulnerable"]
    )

    board_number = _parse_optional_int(
        tags.get("Board")
    )

    if board_number is not None:
        record_id = str(
            board_number
        )
        seed = board_number
    else:
        record_id = (
            f"record-{record_index}"
        )
        seed = record_index

    deal = _parse_deal(
        tags["Deal"],
        seed=seed,
    )

    auction: Auction | None = None

    if "Auction" in tags:
        auction_dealer = _seat(
            tags["Auction"]
        )

        if auction_dealer is not dealer:
            raise ValueError(
                "PBN Auction seat conflicts "
                "with Dealer"
            )

        try:
            auction, ignored_trailing_tokens = _parse_auction(
                dealer=dealer,
                lines=auction_lines,
            )
            if ignored_trailing_tokens:
                transformations = (
                    *transformations,
                    "ignored-trailing-pbn-auction-tokens",
                )
        except (TypeError, ValueError) as exc:
            board_text = tags.get("Board", f"record-{record_index}")
            room_text = tags.get("Room", "?")
            auction_text = " ".join(_auction_tokens(auction_lines))
            raise type(exc)(
                "PBN auction parse failed "
                f"(board={board_text!r}, room={room_text!r}, "
                f"dealer={dealer.value!r}, auction={auction_text!r}): "
                f"{exc}"
            ) from exc

    contract = _parse_optional_contract(
        tags.get("Contract"),
        declarer=tags.get(
            "Declarer"
        ),
    )

    tricks = _parse_optional_int(
        tags.get("Result")
    )

    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider=provider,
            source=source,
            record_id=record_id,
            language=None,
            notation="PBN",
            provider_version=(
                provider_version
            ),
            transformations=(
                "parsed-native-pbn",
                *transformations,
            ),
        ),
        dealer=dealer,
        vulnerability=vulnerability,
        deal=deal,
        auction=auction,
        contract=contract,
        opening_lead=None,
        tricks=tricks,
        board_number=board_number,

        # System information must remain unknown
        # unless explicitly supplied by a trusted
        # source.  Never infer it from the auction.
        ns_system=None,
        ew_system=None,
    )


def read_pbn_text(
    text: str,
    *,
    source: str,
    provider: str = "pbn-native",
    provider_version: str | None = None,
) -> tuple[
    CanonicalBoardRecord,
    ...
]:
    """Read canonical records from PBN text."""

    if not isinstance(
        text,
        str,
    ):
        raise TypeError(
            "text must be a string"
        )

    if (
        not isinstance(
            source,
            str,
        )
        or not source.strip()
    ):
        raise ValueError(
            "source must be a non-blank string"
        )

    if (
        not isinstance(
            provider,
            str,
        )
        or not provider.strip()
    ):
        raise ValueError(
            "provider must be a non-blank string"
        )

    if (
        provider_version is not None
        and (
            not isinstance(
                provider_version,
                str,
            )
            or not provider_version.strip()
        )
    ):
        raise ValueError(
            "provider_version must be None "
            "or a non-blank string"
        )

    normalized_source = (
        source.strip()
    )

    normalized_provider = (
        provider.strip()
    )

    normalized_provider_version = (
        provider_version.strip()
        if provider_version is not None
        else None
    )

    tags: dict[
        str,
        str,
    ] = {}

    auction_lines: list[
        str
    ] = []

    records: list[
        CanonicalBoardRecord
    ] = []

    section: str | None = None

    record_index = 0

    # Some legacy PBN exports use [Deal "#"] for the second
    # room of a board.  Preserve concrete Deal values by board
    # number so the inherited value can be resolved without
    # guessing a starting seat or hand order.
    concrete_deals_by_board: dict[str, str] = {}

    def flush() -> None:
        nonlocal tags
        nonlocal auction_lines
        nonlocal section
        nonlocal record_index

        if not tags:
            return

        record_index += 1

        record_tags = dict(
            tags
        )

        record_transformations: list[
            str
        ] = []

        deal_value = record_tags.get(
            "Deal"
        )

        board_key = record_tags.get(
            "Board"
        )

        if (
            deal_value is not None
            and deal_value.strip() == "#"
        ):
            if (
                board_key is None
                or board_key not in concrete_deals_by_board
            ):
                raise ValueError(
                    "PBN inherited Deal has no prior "
                    "concrete Deal for the same board"
                )

            record_tags["Deal"] = (
                concrete_deals_by_board[
                    board_key
                ]
            )

            record_transformations.append(
                "resolved-pbn-inherited-deal"
            )

        elif (
            deal_value is not None
            and deal_value.strip()
            and deal_value.strip() != "#"
            and board_key is not None
        ):
            concrete_deals_by_board[
                board_key
            ] = deal_value

        record = _record_from_block(
            tags=record_tags,
            auction_lines=tuple(
                auction_lines
            ),
            provider=(
                normalized_provider
            ),
            source=(
                normalized_source
            ),
            provider_version=(
                normalized_provider_version
            ),
            record_index=(
                record_index
            ),
            transformations=tuple(
                record_transformations
            ),
        )

        if record is not None:
            records.append(
                record
            )

        tags = {}
        auction_lines = []
        section = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if line.startswith("%"):
            continue

        match = _TAG_RE.match(
            line
        )

        if match:
            tag_name = (
                match.group(1)
            )

            tag_value = (
                match.group(2)
            )

            # A repeated Board tag starts a new PBN record.
            # This is essential for team/match files where Open
            # and Closed rooms are separate records for the same
            # board number and Event is not repeated between them.
            #
            # Event remains a secondary boundary for conventional
            # PBN files once the current block contains a Deal.
            if (
                tag_name == "Board"
                and "Board" in tags
            ):
                flush()
            elif (
                tag_name == "Event"
                and tags
                and "Deal" in tags
            ):
                flush()

            tags[tag_name] = (
                tag_value
            )

            if tag_name == "Auction":
                section = "auction"
            else:
                # A new tag terminates the
                # previous free-text section.
                # This prevents [Play] data
                # from becoming auction calls.
                section = None

            continue

        if section == "auction":
            if not line:
                continue

            auction_lines.append(
                line
            )

    flush()

    return tuple(
        records
    )


def read_pbn_file(
    path: str | Path,
    *,
    provider: str = "pbn-native",
    provider_version: str | None = None,
    encoding: str = "utf-8",
) -> tuple[
    CanonicalBoardRecord,
    ...
]:
    """Read canonical records directly from a PBN file.

    UTF-8 remains the primary/default encoding.

    When the default UTF-8 decoding fails, legacy PBN files
    are retried using Windows-1252. An explicitly requested
    non-UTF-8 encoding is used exactly as supplied and is not
    silently replaced by another encoding.
    """

    file_path = Path(
        path
    )

    try:
        text = file_path.read_text(
            encoding=encoding,
        )

    except UnicodeDecodeError:
        normalized_encoding = (
            encoding
            .strip()
            .lower()
            .replace("_", "-")
        )

        if normalized_encoding not in {
            "utf-8",
            "utf8",
        }:
            raise

        text = file_path.read_text(
            encoding="cp1252",
        )

    return read_pbn_text(
        text,
        source=str(
            file_path
        ),
        provider=provider,
        provider_version=(
            provider_version
        ),
    )
