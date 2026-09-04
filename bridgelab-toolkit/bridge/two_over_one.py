"""Source-grounded Two-over-One Game Force auction semantics.

Canonical source:
``bidding/systems/2-over-1``

The source explicitly identifies only these automatic game forces:

* 1♥ — 2♣
* 1♥ — 2♦
* 1♠ — 2♣
* 1♠ — 2♦

This module classifies those auctions when the partnership explicitly selects
``two_over_one = game_force``.  It does not decide whether a particular hand
should make the response because the same source allows game values from
12+ HCP *or* excellent distribution *or* a powerful fit and does not provide a
complete deterministic suit-length/quality contract for choosing among the
responses.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Auction, CallType, Strain
from .bidding_rules import KnowledgeSource, SystemContext
from .major_response_options import TwoOverOneTreatment, two_over_one_treatment


ARTICLE = "bidding/systems/2-over-1"
CORE_SOURCE = KnowledgeSource(ARTICLE, "1. Two-over-One Responses are Game Forcing")
GF_SOURCE = KnowledgeSource(ARTICLE, "What Creates a Game Force?")
MISCONCEPTION_SOURCE = KnowledgeSource(ARTICLE, "Every Two-Level Response is Game Forcing")

_AUTOMATIC_GF = {
    (Strain.HEARTS, Strain.CLUBS),
    (Strain.HEARTS, Strain.DIAMONDS),
    (Strain.SPADES, Strain.CLUBS),
    (Strain.SPADES, Strain.DIAMONDS),
}


def is_canonical_two_over_one_pair(opening: Strain, response: Strain) -> bool:
    """Return whether the canonical 2/1 article lists this pair as automatic GF.

    The source heading ``The Four 2/1 Auctions`` explicitly limits the
    automatic game-force domain to four major-to-minor pairs.  In particular,
    ``1♠ — 2♥`` is outside that canonical automatic-GF set.
    """
    if not isinstance(opening, Strain) or not isinstance(response, Strain):
        raise TypeError("opening and response must be Strain")
    return (opening, response) in _AUTOMATIC_GF


@dataclass(frozen=True, slots=True)
class TwoOverOneAssessment:
    """Semantic assessment of an auction under explicit partnership treatment."""

    is_game_force: bool
    explanation: str
    sources: tuple[KnowledgeSource, ...] = ()


def assess_two_over_one_game_force(
    auction: Auction,
    system: SystemContext,
) -> TwoOverOneAssessment:
    """Classify an exact uncontested opening/response sequence.

    A positive result requires explicit ``two_over_one = game_force``.
    Unspecified or natural treatment never silently becomes a game force.
    """
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    treatment = two_over_one_treatment(system)
    if treatment is not TwoOverOneTreatment.GAME_FORCE:
        return TwoOverOneAssessment(
            False,
            "Partnership has not explicitly selected Two-over-One Game Force.",
        )

    entries = auction.entries
    if len(entries) != 3:
        return TwoOverOneAssessment(
            False,
            "Requires exact uncontested opening — Pass — two-level response.",
        )

    opening, rho, response = entries
    if (
        opening.call.kind is not CallType.BID
        or opening.call.bid is None
        or opening.call.bid.level != 1
        or rho.call.kind is not CallType.PASS
        or response.call.kind is not CallType.BID
        or response.call.bid is None
        or response.call.bid.level != 2
        or response.seat is not opening.seat.partner()
    ):
        return TwoOverOneAssessment(False, "Auction is not an uncontested two-over-one response.")

    pair = (opening.call.bid.strain, response.call.bid.strain)
    if not is_canonical_two_over_one_pair(*pair):
        return TwoOverOneAssessment(
            False,
            "Canonical source does not list this sequence as an automatic game force.",
            (MISCONCEPTION_SOURCE,),
        )

    return TwoOverOneAssessment(
        True,
        "Canonical 2/1 source explicitly defines this response as an automatic game force.",
        (CORE_SOURCE, GF_SOURCE, MISCONCEPTION_SOURCE),
    )
