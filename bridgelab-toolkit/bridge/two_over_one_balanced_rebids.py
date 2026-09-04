"""Source-grounded audit helpers for balanced opener rebids after 2/1 GF.

The canonical 2/1 article describes ``1♥ — 2♦ — 2NT`` as:

* balanced minimum;
* no better description.

It does not assign an HCP range to ``minimum`` in this 2/1 sequence.

The general SAYC article does contain a generic ``2NT = 18-19 balanced``
notrump-rebid statement, but it is not scoped to an already game-forcing
Two-over-One auction.  BridgeLab therefore does not silently transfer that
range into the 2/1 module.

This module records the executable evidence and the unresolved strength
contract without producing a bidding recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import CallType, Strain
from .bidding_rules import BiddingContext, KnowledgeSource
from .evaluation import ShapeClass
from .major_response_options import TwoOverOneTreatment, two_over_one_treatment


ARTICLE = "bidding/systems/2-over-1"
FIRST_RESPONSIBILITY_SOURCE = KnowledgeSource(ARTICLE, "Opener's First Responsibility")
BALANCED_REBID_SOURCE = KnowledgeSource(ARTICLE, "Priority 4 — Balanced Rebids")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


@dataclass(frozen=True, slots=True)
class TwoOverOneBalancedRebidEvidence:
    """Objective evidence for the canonical 1♥-2♦-2NT shape branch."""

    exact_auction: bool
    game_force_configured: bool
    balanced: bool
    strength_contract_known: bool
    explanation: str
    sources: tuple[KnowledgeSource, ...]

    @property
    def executable(self) -> bool:
        """Whether the source currently supports a complete production rule."""
        return (
            self.exact_auction
            and self.game_force_configured
            and self.balanced
            and self.strength_contract_known
        )


def _exact_one_heart_two_diamond_rebid(context: BiddingContext) -> bool:
    entries = context.auction.entries
    if len(entries) != 4:
        return False
    opener, rho, responder, lho = entries
    return (
        opener.seat is context.seat
        and opener.call.kind is CallType.BID
        and opener.call.bid is not None
        and opener.call.bid.level == 1
        and opener.call.bid.strain is Strain.HEARTS
        and rho.call.kind is CallType.PASS
        and responder.seat is context.seat.partner()
        and responder.call.kind is CallType.BID
        and responder.call.bid is not None
        and responder.call.bid.level == 2
        and responder.call.bid.strain is Strain.DIAMONDS
        and lho.call.kind is CallType.PASS
    )


def assess_one_heart_two_diamond_balanced_rebid(
    context: BiddingContext,
) -> TwoOverOneBalancedRebidEvidence:
    """Assess only what the canonical 2/1 source makes deterministic.

    ``strength_contract_known`` is intentionally False: the article says
    "balanced minimum" but supplies no numeric minimum range for this auction.
    """
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")

    exact = (
        context.system.system.casefold() in _SAYC_NAMES
        and _exact_one_heart_two_diamond_rebid(context)
    )
    gf = two_over_one_treatment(context.system) is TwoOverOneTreatment.GAME_FORCE
    balanced = context.evaluation.shape_class is ShapeClass.BALANCED

    return TwoOverOneBalancedRebidEvidence(
        exact_auction=exact,
        game_force_configured=gf,
        balanced=balanced,
        strength_contract_known=False,
        explanation=(
            "Canonical 2/1 material describes 1♥ — 2♦ — 2NT as a balanced "
            "minimum with no better description, but does not define a numeric "
            "strength range for 'minimum' in this game-forcing auction. The "
            "general SAYC 2NT rebid range is not imported because its scope is "
            "not established as this 2/1 sequence."
        ),
        sources=(FIRST_RESPONSIBILITY_SOURCE, BALANCED_REBID_SOURCE),
    )
