"""Explicit partnership options for major-opening response treatments.

Canonical source:
``bidding/natural-bids/responses/response-to-major-opening``

The source says:
* SAYC has a natural structure.
* Forcing 1NT is optional.
* At the two level, new-suit agreements vary.
* Most modern partnerships play Two-over-One Game Force.
* Many partnerships replace the traditional limit raise with Bergen Raises.

This module does not choose among those treatments.  It normalizes only
explicit partnership selections from ``SystemContext`` so bidding rules can
abstain when no agreement has been supplied.
"""

from __future__ import annotations

from enum import Enum

from .bidding_rules import SystemContext


FORCING_ONE_NOTRUMP_OPTION = "forcing_one_notrump"
TWO_OVER_ONE_OPTION = "two_over_one"
MAJOR_RAISE_STYLE_OPTION = "major_raise_style"


class MajorRaiseStyle(Enum):
    TRADITIONAL = "traditional"
    BERGEN = "bergen"
    OTHER = "other"


class ForcingOneNotrumpTreatment(Enum):
    FORCING = "forcing"
    NONFORCING = "nonforcing"
    UNSPECIFIED = "unspecified"


class TwoOverOneTreatment(Enum):
    GAME_FORCE = "game_force"
    NATURAL = "natural"
    UNSPECIFIED = "unspecified"


def major_raise_style(system: SystemContext) -> MajorRaiseStyle:
    """Return the explicitly configured major-raise family.

    Absence preserves the existing BridgeLab controlled-SAYC behavior:
    traditional raises are the conservative default because the canonical SAYC
    section says "Natural structure" and the article presents traditional raises
    before optional replacements.
    """
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    value = system.option(MAJOR_RAISE_STYLE_OPTION)
    if value is None:
        return MajorRaiseStyle.TRADITIONAL

    normalized = str(value).strip().casefold()
    if normalized == "traditional":
        return MajorRaiseStyle.TRADITIONAL
    if normalized == "bergen":
        return MajorRaiseStyle.BERGEN
    return MajorRaiseStyle.OTHER


def forcing_one_notrump_treatment(
    system: SystemContext,
) -> ForcingOneNotrumpTreatment:
    """Return the partnership's explicit 1NT treatment after a major opening.

    No default is inferred because the source explicitly says forcing 1NT is
    optional in SAYC.
    """
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    value = system.option(FORCING_ONE_NOTRUMP_OPTION)
    if value is None:
        return ForcingOneNotrumpTreatment.UNSPECIFIED

    if isinstance(value, bool):
        return (
            ForcingOneNotrumpTreatment.FORCING
            if value
            else ForcingOneNotrumpTreatment.NONFORCING
        )

    normalized = str(value).strip().casefold()
    if normalized in {"forcing", "true", "yes", "1"}:
        return ForcingOneNotrumpTreatment.FORCING
    if normalized in {"nonforcing", "non-forcing", "false", "no", "0"}:
        return ForcingOneNotrumpTreatment.NONFORCING
    return ForcingOneNotrumpTreatment.UNSPECIFIED


def two_over_one_treatment(system: SystemContext) -> TwoOverOneTreatment:
    """Return the explicit two-level new-suit treatment after a major opening.

    No default is inferred because the source says two-level agreements vary.
    """
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    value = system.option(TWO_OVER_ONE_OPTION)
    if value is None:
        return TwoOverOneTreatment.UNSPECIFIED

    if isinstance(value, bool):
        return (
            TwoOverOneTreatment.GAME_FORCE
            if value
            else TwoOverOneTreatment.NATURAL
        )

    normalized = str(value).strip().casefold()
    if normalized in {
        "game_force",
        "game-force",
        "game force",
        "2/1",
        "2/1 game force",
        "two-over-one game force",
        "true",
        "yes",
        "1",
    }:
        return TwoOverOneTreatment.GAME_FORCE
    if normalized in {
        "natural",
        "standard",
        "non-game-force",
        "non game force",
        "false",
        "no",
        "0",
    }:
        return TwoOverOneTreatment.NATURAL
    return TwoOverOneTreatment.UNSPECIFIED
