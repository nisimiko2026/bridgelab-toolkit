"""Deterministic opener responses after an established SAYC 2NT Stayman inquiry.

This module deliberately does not select responder's 3C inquiry. The frozen
Stayman source leaves responder minimum strength partnership-dependent.
"""
from __future__ import annotations
from dataclasses import dataclass

from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit

_SOURCE = "bidding/conventions/responses/stayman"
_RESPONSES = KnowledgeSource(_SOURCE, "2NT Auctions")
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _calls(context: BiddingContext) -> tuple[str, ...]:
    return tuple(e.call.serialize() for e in context.auction.entries)


@dataclass(frozen=True, slots=True)
class SaycTwoNotrumpStaymanOpenerResponseRule:
    rule_id: str = "sayc.opener.2nt.stayman"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined only for SAYC.")
        if _calls(context) != ("2NT", "P", "3C", "P"):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Rule applies only after the exact uncontested 2NT — Pass — 3C — Pass Stayman inquiry.",
            )

        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)
        has_hearts = hearts >= 4
        has_spades = spades >= 4

        if has_hearts and has_spades:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Frozen Stayman source leaves the response with both four-card majors partnership-dependent.",
            )
        if has_hearts:
            candidate = Call.parse("3H")
            explanation = "After 2NT–3C Stayman, 3H shows a four-card heart suit."
        elif has_spades:
            candidate = Call.parse("3S")
            explanation = "After 2NT–3C Stayman, 3S shows a four-card spade suit."
        else:
            candidate = Call.parse("3D")
            explanation = "After 2NT–3C Stayman, 3D denies a four-card major."

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation=explanation,
            sources=(_RESPONSES,),
            priority=100,
        )


def create_sayc_two_notrump_stayman_opener_response_engine() -> BiddingEngine:
    return BiddingEngine((SaycTwoNotrumpStaymanOpenerResponseRule(),))
