"""Controlled opener rebids after an established Two-over-One game force.

Canonical source:
``bidding/systems/2-over-1`` — ``Opener's Rebids``.

The source gives this priority order:

1. Describe shape / show a second suit.
2. Support responder.
3. Rebid opener's own suit.
4. Make a balanced rebid.

Phase 5W implemented the clearest source-explicit second-suit examples:

* 1♠ — 2♣ — 2♦: natural, four or more diamonds, normally preferred to 2♠.
* 1♥ — 2♦ — 2♠: four or more spades with five or more hearts.

Phase 5X added the first source-explicit support rebid:

* 1♠ — 2♣ — 3♣: club support, usually four cards.

Phase 5Y adds the objective shape branch of the next priority:

* 1♠ — 2♣ — 2♠: the source says this is usually six spades or a poor hand
  unsuitable for another rebid.

Only the deterministic six-spade branch is executable.  ``Minimum`` and
``poor hand unsuitable for another rebid`` remain qualitative and are not
converted into invented strength thresholds.

BridgeLab's Auction includes opponents' passes, so the executable positions are
``1S-P-2C-P-?`` and ``1H-P-2D-P-?``.

No general second-suit ordering rule is invented.  The 1♠/2♣ rule therefore
abstains when opener also has four hearts, because the canonical excerpt does
not specify precedence between two available second suits.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .major_response_options import TwoOverOneTreatment, two_over_one_treatment
from .models import Suit


ARTICLE = "bidding/systems/2-over-1"
OPENER_REBIDS_SOURCE = KnowledgeSource(ARTICLE, "Opener's Rebids")
SECOND_SUIT_SOURCE = KnowledgeSource(ARTICLE, "Priority 1 — Show a Second Suit")
SUPPORT_SOURCE = KnowledgeSource(ARTICLE, "Priority 2 — Support Responder")
OWN_SUIT_SOURCE = KnowledgeSource(ARTICLE, "Priority 3 — Rebid Own Suit")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _exact_established_two_over_one(
    context: BiddingContext,
    opening: Strain,
    response: Strain,
) -> bool:
    entries = context.auction.entries
    if len(entries) != 4:
        return False

    opener, rho, responder, lho = entries
    return (
        opener.seat is context.seat
        and opener.call.kind is CallType.BID
        and opener.call.bid is not None
        and opener.call.bid.level == 1
        and opener.call.bid.strain is opening
        and rho.call.kind is CallType.PASS
        and responder.seat is context.seat.partner()
        and responder.call.kind is CallType.BID
        and responder.call.bid is not None
        and responder.call.bid.level == 2
        and responder.call.bid.strain is response
        and lho.call.kind is CallType.PASS
    )


@dataclass(frozen=True, slots=True)
class SaycTwoOverOneOneSpadeTwoClubTwoDiamondRule:
    """Recommend 2♦ after exact 1♠-P-2♣-P when the source-explicit shape is clear."""

    rule_id: str = "sayc.2over1.opener.1s.2c.2d"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is scoped to configured SAYC partnerships.")

        if two_over_one_treatment(context.system) is not TwoOverOneTreatment.GAME_FORCE:
            return RuleDecision.not_applicable(self.rule_id, "Partnership has not explicitly selected Two-over-One Game Force.")

        if not _exact_established_two_over_one(context, Strain.SPADES, Strain.CLUBS):
            return RuleDecision.not_applicable(self.rule_id, "Requires exact 1♠ — Pass — 2♣ — Pass — ?.")

        if context.evaluation.length(Suit.DIAMONDS) < 4:
            return RuleDecision.not_applicable(self.rule_id, "Canonical 2♦ rebid requires four or more diamonds.")

        if context.evaluation.length(Suit.HEARTS) >= 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Opener also has four hearts; source does not define precedence between multiple second suits.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2D"),
            explanation=(
                "After the established 1♠ — 2♣ game force, canonical opener-rebid "
                "priority is to describe shape and show a second suit. The source "
                "explicitly gives 2♦ as natural with four or more diamonds and "
                "usually preferred to rebidding 2♠."
            ),
            sources=(OPENER_REBIDS_SOURCE, SECOND_SUIT_SOURCE),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycTwoOverOneOneHeartTwoDiamondTwoSpadeRule:
    """Recommend 2♠ after exact 1♥-P-2♦-P with 5+ hearts and 4+ spades."""

    rule_id: str = "sayc.2over1.opener.1h.2d.2s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is scoped to configured SAYC partnerships.")

        if two_over_one_treatment(context.system) is not TwoOverOneTreatment.GAME_FORCE:
            return RuleDecision.not_applicable(self.rule_id, "Partnership has not explicitly selected Two-over-One Game Force.")

        if not _exact_established_two_over_one(context, Strain.HEARTS, Strain.DIAMONDS):
            return RuleDecision.not_applicable(self.rule_id, "Requires exact 1♥ — Pass — 2♦ — Pass — ?.")

        if context.evaluation.length(Suit.HEARTS) < 5:
            return RuleDecision.not_applicable(self.rule_id, "Canonical example describes five or more hearts.")

        if context.evaluation.length(Suit.SPADES) < 4:
            return RuleDecision.not_applicable(self.rule_id, "Canonical 2♠ rebid requires four or more spades.")

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2S"),
            explanation=(
                "After the established 1♥ — 2♦ game force, canonical opener-rebid "
                "priority is to describe shape and show a second suit. The source "
                "explicitly describes 2♠ as showing four or more spades with five "
                "or more hearts."
            ),
            sources=(OPENER_REBIDS_SOURCE, SECOND_SUIT_SOURCE),
            priority=90,
        )



@dataclass(frozen=True, slots=True)
class SaycTwoOverOneOneSpadeTwoClubThreeClubRule:
    """Recommend 3♣ after exact 1♠-P-2♣-P with the source-explicit support shape."""

    rule_id: str = "sayc.2over1.opener.1s.2c.3c"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Rule is scoped to configured SAYC partnerships.",
            )

        if two_over_one_treatment(context.system) is not TwoOverOneTreatment.GAME_FORCE:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Partnership has not explicitly selected Two-over-One Game Force.",
            )

        if not _exact_established_two_over_one(context, Strain.SPADES, Strain.CLUBS):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires exact 1♠ — Pass — 2♣ — Pass — ?.",
            )

        if context.evaluation.length(Suit.CLUBS) < 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Canonical support example says the 3♣ rebid usually shows four clubs.",
            )

        if (
            context.evaluation.length(Suit.HEARTS) >= 4
            or context.evaluation.length(Suit.DIAMONDS) >= 4
        ):
            return RuleDecision.not_applicable(
                self.rule_id,
                "A four-card second suit is present; canonical opener priorities put showing a second suit before supporting responder.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("3C"),
            explanation=(
                "After the established 1♠ — 2♣ game force, and with no four-card "
                "second suit taking Priority 1, the canonical Priority 2 example "
                "supports responder with 3♣. The source says this club support "
                "usually shows four cards."
            ),
            sources=(OPENER_REBIDS_SOURCE, SECOND_SUIT_SOURCE, SUPPORT_SOURCE),
            priority=80,
        )


@dataclass(frozen=True, slots=True)
class SaycTwoOverOneOneSpadeTwoClubTwoSpadeRule:
    """Recommend the objective six-spade branch of 1♠-P-2♣-P-2♠."""

    rule_id: str = "sayc.2over1.opener.1s.2c.2s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Rule is scoped to configured SAYC partnerships.",
            )

        if two_over_one_treatment(context.system) is not TwoOverOneTreatment.GAME_FORCE:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Partnership has not explicitly selected Two-over-One Game Force.",
            )

        if not _exact_established_two_over_one(context, Strain.SPADES, Strain.CLUBS):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires exact 1♠ — Pass — 2♣ — Pass — ?.",
            )

        if context.evaluation.length(Suit.SPADES) < 6:
            return RuleDecision.not_applicable(
                self.rule_id,
                "This controlled branch implements only the source's objective six-spade case.",
            )

        if (
            context.evaluation.length(Suit.HEARTS) >= 4
            or context.evaluation.length(Suit.DIAMONDS) >= 4
        ):
            return RuleDecision.not_applicable(
                self.rule_id,
                "A four-card second suit is present; canonical Priority 1 is to show a second suit.",
            )

        if context.evaluation.length(Suit.CLUBS) >= 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Four-card club support is present; canonical Priority 2 supports responder before Priority 3 rebids opener's suit.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2S"),
            explanation=(
                "After the established 1♠ — 2♣ game force, no source-explicit "
                "Priority 1 second suit or Priority 2 four-card club support applies. "
                "The canonical Priority 3 example says 2♠ is usually based on six "
                "spades or on a qualitatively poor hand. This controlled rule uses "
                "only the objective six-spade branch and makes no minimum-strength "
                "or poor-hand classification."
            ),
            sources=(
                OPENER_REBIDS_SOURCE,
                SECOND_SUIT_SOURCE,
                SUPPORT_SOURCE,
                OWN_SUIT_SOURCE,
            ),
            priority=70,
        )

def sayc_two_over_one_opener_rebid_rules():
    return (
        SaycTwoOverOneOneSpadeTwoClubTwoDiamondRule(),
        SaycTwoOverOneOneHeartTwoDiamondTwoSpadeRule(),
        SaycTwoOverOneOneSpadeTwoClubThreeClubRule(),
        SaycTwoOverOneOneSpadeTwoClubTwoSpadeRule(),
    )


def create_sayc_two_over_one_opener_rebid_engine() -> BiddingEngine:
    return BiddingEngine(sayc_two_over_one_opener_rebid_rules())
