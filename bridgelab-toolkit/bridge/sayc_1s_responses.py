"""Controlled SAYC responses to a 1♠ opening.

Canonical source:
``bidding/natural-bids/responses/response-to-major-opening``

Implemented only where the source provides executable conditions without
requiring an unstated partnership agreement:

* Pass: 0–5 HCP.
* 2♠ simple raise: approximately 6–9 HCP with 3+ spade support.
* 3♠ traditional limit raise: approximately 10–12 HCP with 4+ spade support.

The source explicitly states that after 1♠ there is no higher-ranking major to
bid.  It also states that forcing 1NT is optional in SAYC, so 1NT is deliberately
not implemented here.

Traditional raises are enabled only when ``major_raise_style`` is absent or
equals ``traditional``.  Other treatments such as Bergen are not inferred.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit


ARTICLE = "bidding/natural-bids/responses/response-to-major-opening"
STRENGTH = KnowledgeSource(ARTICLE, "Strength Categories")
PRIORITIES = KnowledgeSource(ARTICLE, "Responder's Priorities")
SIMPLE_RAISE = KnowledgeSource(ARTICLE, "Simple Raise")
LIMIT_RAISE = KnowledgeSource(ARTICLE, "Limit Raise")
OTHER_MAJOR = KnowledgeSource(ARTICLE, "Responding with Another Major")
SAYC = KnowledgeSource(ARTICLE, "SAYC")

_SAYC_NAMES = {"sayc", "standard american yellow card"}
_MAJOR_RAISE_STYLE_OPTION = "major_raise_style"


def _gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if context.system.system.casefold() not in _SAYC_NAMES:
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")

    entries = context.auction.entries
    if len(entries) != 2:
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested 1♠ — Pass — ?."
        )

    opening, rho = entries
    if (
        opening.seat is not context.seat.partner()
        or opening.call.kind is not CallType.BID
        or opening.call.bid is None
        or opening.call.bid.level != 1
        or opening.call.bid.strain is not Strain.SPADES
        or rho.call.kind is not CallType.PASS
    ):
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested 1♠ — Pass — ?."
        )
    return None


def _traditional_major_raises(context: BiddingContext) -> bool:
    style = context.system.option(_MAJOR_RAISE_STYLE_OPTION)
    if style is None:
        return True
    return str(style).strip().casefold() == "traditional"


@dataclass(frozen=True, slots=True)
class SaycResponseToOneSpadePassRule:
    rule_id: str = "sayc.response.1s.pass"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not 0 <= context.evaluation.hcp <= 5:
            return RuleDecision.not_applicable(self.rule_id, "Requires 0–5 HCP.")

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.pass_(),
            explanation="The source lists 0–5 HCP as the pass strength category.",
            sources=(STRENGTH,),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneSpadeSimpleRaiseRule:
    rule_id: str = "sayc.response.1s.2s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not _traditional_major_raises(context):
            return RuleDecision.not_applicable(
                self.rule_id, "Traditional major raises are not configured."
            )
        if not 6 <= context.evaluation.hcp <= 9:
            return RuleDecision.not_applicable(self.rule_id, "Requires 6–9 HCP.")
        if context.evaluation.length(Suit.SPADES) < 3:
            return RuleDecision.not_applicable(
                self.rule_id, "Requires three or more spades of support."
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2S"),
            explanation=(
                "Supporting opener is the highest priority. The source defines "
                "a simple raise as approximately 6–9 HCP with three- or "
                "four-card support."
            ),
            sources=(PRIORITIES, SIMPLE_RAISE, SAYC),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneSpadeLimitRaiseRule:
    rule_id: str = "sayc.response.1s.3s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not _traditional_major_raises(context):
            return RuleDecision.not_applicable(
                self.rule_id, "Traditional major raises are not configured."
            )
        if not 10 <= context.evaluation.hcp <= 12:
            return RuleDecision.not_applicable(self.rule_id, "Requires 10–12 HCP.")
        if context.evaluation.length(Suit.SPADES) < 4:
            return RuleDecision.not_applicable(
                self.rule_id, "Requires four or more spades of support."
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("3S"),
            explanation=(
                "The source defines the traditional limit raise as "
                "approximately 10–12 HCP, four-card support, invitational."
            ),
            sources=(PRIORITIES, LIMIT_RAISE, SAYC),
            priority=90,
        )


def sayc_one_spade_response_rules():
    return (
        SaycResponseToOneSpadePassRule(),
        SaycResponseToOneSpadeSimpleRaiseRule(),
        SaycResponseToOneSpadeLimitRaiseRule(),
    )


def create_sayc_one_spade_response_engine() -> BiddingEngine:
    return BiddingEngine(sayc_one_spade_response_rules())
