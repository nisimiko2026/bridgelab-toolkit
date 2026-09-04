"""Deterministic opener acceptance of an already-established Texas Transfer after SAYC 2NT.

Responder-side Texas selection is intentionally not implemented: the frozen
source uses qualitative game-going/no-slam-interest conditions.
"""
from __future__ import annotations
from dataclasses import dataclass

from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision

_SOURCE = "bidding/conventions/transfers/texas-transfers"
_TRANSFER = KnowledgeSource(_SOURCE, "Transfer Structure")
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _calls(context: BiddingContext) -> tuple[str, ...]:
    return tuple(e.call.serialize() for e in context.auction.entries)


@dataclass(frozen=True, slots=True)
class SaycTwoNotrumpTexasAcceptanceRule:
    rule_id: str = "sayc.opener.2nt.texas.accept"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined only for SAYC.")

        calls = _calls(context)
        if calls == ("2NT", "P", "4D", "P"):
            candidate = Call.parse("4H")
            explanation = "After 2NT–4D Texas Transfer, opener completes the transfer to 4H."
        elif calls == ("2NT", "P", "4H", "P"):
            candidate = Call.parse("4S")
            explanation = "After 2NT–4H Texas Transfer, opener completes the transfer to 4S."
        else:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Rule applies only after an established uncontested Texas response to 2NT.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation=explanation,
            sources=(_TRANSFER,),
            priority=100,
        )


def create_sayc_two_notrump_texas_accept_engine() -> BiddingEngine:
    return BiddingEngine((SaycTwoNotrumpTexasAcceptanceRule(),))
