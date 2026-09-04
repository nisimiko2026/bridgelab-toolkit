"""Controlled SAYC notrump responses to 1♦.

Canonical source:
bidding/natural-bids/responses/response-to-1-diamond

The source explicitly defines:
* 2NT: usually 10–12 HCP, balanced, invitational.
* 3NT: usually 13–15 HCP, balanced, game values.
It also says balanced hands without a major fit frequently choose notrump and
that responder should investigate a major fit first.

The source's 1NT entry additionally says "stopper(s)" but does not identify
which suit(s) must be stopped.  Therefore 1NT remains deliberately unresolved:
the Phase 5K per-suit policy registry cannot safely infer the missing suit
requirement.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
from .evaluation import ShapeClass


ARTICLE = "bidding/natural-bids/responses/response-to-1-diamond"
PRIORITIES = KnowledgeSource(ARTICLE, "Responder's Priorities")
NOTRUMP = KnowledgeSource(ARTICLE, "Notrump Responses")
TWO_NT = KnowledgeSource(ARTICLE, "2NT")
THREE_NT = KnowledgeSource(ARTICLE, "3NT")
_SAYC = {"sayc", "standard american yellow card"}


def _gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if context.system.system.casefold() not in _SAYC:
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")
    entries = context.auction.entries
    if len(entries) != 2:
        return RuleDecision.not_applicable(rule_id, "Requires exact 1♦ — Pass — ? position.")
    opening, rho = entries
    if (
        opening.seat is not context.seat.partner()
        or opening.call.kind is not CallType.BID
        or opening.call.bid is None
        or opening.call.bid.level != 1
        or opening.call.bid.strain is not Strain.DIAMONDS
        or rho.call.kind is not CallType.PASS
    ):
        return RuleDecision.not_applicable(rule_id, "Requires exact uncontested 1♦ — Pass — ?.")
    return None


def _no_four_card_major(context: BiddingContext) -> bool:
    return (
        context.evaluation.length(Suit.HEARTS) < 4
        and context.evaluation.length(Suit.SPADES) < 4
    )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneDiamondTwoNotrumpRule:
    rule_id: str = "sayc.response.1d.2nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate=_gate(context,self.rule_id)
        if gate is not None: return gate
        if not (10 <= context.evaluation.hcp <= 12):
            return RuleDecision.not_applicable(self.rule_id, "Requires 10–12 HCP.")
        if context.evaluation.shape_class is not ShapeClass.BALANCED:
            return RuleDecision.not_applicable(self.rule_id, "Requires a balanced hand.")
        if not _no_four_card_major(context):
            return RuleDecision.not_applicable(self.rule_id, "Major-suit fit investigation has priority.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2NT"),
            explanation="Source defines 2NT as usually 10–12 HCP, balanced and invitational; major-fit investigation has priority.",
            sources=(PRIORITIES, NOTRUMP, TWO_NT),
            priority=80,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneDiamondThreeNotrumpRule:
    rule_id: str = "sayc.response.1d.3nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate=_gate(context,self.rule_id)
        if gate is not None: return gate
        if not (13 <= context.evaluation.hcp <= 15):
            return RuleDecision.not_applicable(self.rule_id, "Requires 13–15 HCP.")
        if context.evaluation.shape_class is not ShapeClass.BALANCED:
            return RuleDecision.not_applicable(self.rule_id, "Requires a balanced hand.")
        if not _no_four_card_major(context):
            return RuleDecision.not_applicable(self.rule_id, "Major-suit fit investigation has priority.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("3NT"),
            explanation="Source defines 3NT as usually 13–15 HCP, balanced with game values; major-fit investigation has priority.",
            sources=(PRIORITIES, NOTRUMP, THREE_NT),
            priority=80,
        )


def sayc_one_diamond_notrump_rules():
    return (
        SaycResponseToOneDiamondTwoNotrumpRule(),
        SaycResponseToOneDiamondThreeNotrumpRule(),
    )


def create_sayc_one_diamond_notrump_engine() -> BiddingEngine:
    return BiddingEngine(sayc_one_diamond_notrump_rules())
