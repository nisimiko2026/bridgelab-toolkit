"""Controlled policy-aware Two-over-One response selection.

Canonical sources:

* ``bidding/systems/2-over-1``
* ``bidding/natural-bids/responses/response-to-major-opening``

This is deliberately a *restricted executable slice*.  A recommendation is
made only when all source requirements used by the rule are deterministic:

* explicit partnership treatment ``two_over_one = game_force``;
* exact uncontested one-major opening;
* 12+ HCP (the source's objective game-value branch);
* no three-card support for opener's major;
* after 1♥, no four-card spade suit because the higher major has priority;
* selected minor has at least five cards;
* selected minor is strictly longer than the other minor;
* an explicitly configured SuitQualityPolicy returns QUALIFIES.

The source also allows excellent distribution or a powerful fit, but those
qualitative branches are not inferred here. Equal-length candidate minors are
also left unresolved rather than inventing a tie-break.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .major_response_options import TwoOverOneTreatment, two_over_one_treatment
from .models import Suit
from .policy_registry import PolicyRegistry, assess_configured_suit_quality
from .suit_quality_policy import SuitQualityStatus


SYSTEM_ARTICLE = "bidding/systems/2-over-1"
MAJOR_RESPONSE_ARTICLE = "bidding/natural-bids/responses/response-to-major-opening"

GF_SOURCE = KnowledgeSource(SYSTEM_ARTICLE, "What Creates a Game Force?")
VALUES_SOURCE = KnowledgeSource(SYSTEM_ARTICLE, "Hands Suitable for a 2/1 Response")
PRIORITIES_SOURCE = KnowledgeSource(MAJOR_RESPONSE_ARTICLE, "Responder's Priorities")
WITHOUT_SUPPORT_SOURCE = KnowledgeSource(MAJOR_RESPONSE_ARTICLE, "Responding Without Support")
NEW_SUIT_SOURCE = KnowledgeSource(MAJOR_RESPONSE_ARTICLE, "New Suit Responses")
TWO_OVER_ONE_SOURCE = KnowledgeSource(MAJOR_RESPONSE_ARTICLE, "Two-over-One Game Force")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _exact_major_response(context: BiddingContext, opening: Strain) -> bool:
    entries = context.auction.entries
    if len(entries) != 2:
        return False
    opener, rho = entries
    return (
        opener.seat is context.seat.partner()
        and opener.call.kind is CallType.BID
        and opener.call.bid is not None
        and opener.call.bid.level == 1
        and opener.call.bid.strain is opening
        and rho.call.kind is CallType.PASS
    )


@dataclass(frozen=True, slots=True)
class _TwoOverOneMinorResponseRule:
    registry: PolicyRegistry
    opening: Strain
    response_suit: Suit
    rule_id: str

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined for configured SAYC partnerships.")

        if two_over_one_treatment(context.system) is not TwoOverOneTreatment.GAME_FORCE:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Partnership has not explicitly selected Two-over-One Game Force.",
            )

        if not _exact_major_response(context, self.opening):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires exact uncontested one-major — Pass — ?.",
            )

        if context.evaluation.hcp < 12:
            return RuleDecision.not_applicable(
                self.rule_id,
                "This controlled slice implements only the source's objective 12+ HCP branch.",
            )

        opener_suit = (
            Suit.HEARTS if self.opening is Strain.HEARTS else Suit.SPADES
        )
        if context.evaluation.length(opener_suit) >= 3:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Responder has major support; the source gives support priority.",
            )

        if self.opening is Strain.HEARTS and context.evaluation.length(Suit.SPADES) >= 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "After 1♥, a four-card spade suit has priority over a minor response.",
            )

        other_minor = Suit.DIAMONDS if self.response_suit is Suit.CLUBS else Suit.CLUBS
        selected_length = context.evaluation.length(self.response_suit)
        if selected_length < 5:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Two-over-One source requires a good five-card suit for this controlled response.",
            )
        if selected_length <= context.evaluation.length(other_minor):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Selected minor is not strictly longer than the other minor; tie/longer-suit choice is unresolved.",
            )

        quality = assess_configured_suit_quality(context, self.registry, self.response_suit)
        if quality is None:
            return RuleDecision.not_applicable(
                self.rule_id,
                "No configured/resolvable suit-quality policy.",
            )
        if quality.status is SuitQualityStatus.UNKNOWN:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Configured suit-quality policy returned UNKNOWN.",
            )
        if quality.status is SuitQualityStatus.DOES_NOT_QUALIFY:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Configured suit-quality policy does not qualify the selected suit.",
            )

        strain = Strain.CLUBS if self.response_suit is Suit.CLUBS else Strain.DIAMONDS
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2C" if strain is Strain.CLUBS else "2D"),
            explanation=(
                "Explicit 2/1 Game Force partnership treatment; responder has 12+ HCP, "
                "no priority major support/response, the selected minor is a strictly "
                "longer five-card-or-longer suit, and the configured suit-quality policy "
                f"'{quality.policy_id}' qualifies it. Policy explanation: {quality.explanation}"
            ),
            sources=(
                GF_SOURCE,
                VALUES_SOURCE,
                PRIORITIES_SOURCE,
                WITHOUT_SUPPORT_SOURCE,
                NEW_SUIT_SOURCE,
                TWO_OVER_ONE_SOURCE,
                *quality.sources,
            ),
            priority=75,
        )


def sayc_two_over_one_response_rules(registry: PolicyRegistry):
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    return (
        _TwoOverOneMinorResponseRule(registry, Strain.HEARTS, Suit.CLUBS, "sayc.response.1h.2c.2over1"),
        _TwoOverOneMinorResponseRule(registry, Strain.HEARTS, Suit.DIAMONDS, "sayc.response.1h.2d.2over1"),
        _TwoOverOneMinorResponseRule(registry, Strain.SPADES, Suit.CLUBS, "sayc.response.1s.2c.2over1"),
        _TwoOverOneMinorResponseRule(registry, Strain.SPADES, Suit.DIAMONDS, "sayc.response.1s.2d.2over1"),
    )


def create_sayc_two_over_one_response_engine(registry: PolicyRegistry) -> BiddingEngine:
    return BiddingEngine(sayc_two_over_one_response_rules(registry))
