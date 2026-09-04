"""Conservative SAYC Jacoby Transfers after a 2NT opening.

Frozen BridgeLab sources support Jacoby Transfers after 2NT: responder with a
five-card-or-longer major transfers via 3D to hearts or 3H to spades, and
opener normally completes the transfer.  The source does not define precedence
when responder holds both majors, so that case deliberately abstains.
"""
from __future__ import annotations
from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit

_SOURCE = "bidding/conventions/transfers/jacoby-transfers"
_TRANSFER = KnowledgeSource(_SOURCE, "Jacoby Transfer After 2NT")
_REQUIREMENTS = KnowledgeSource(_SOURCE, "Requirements")
_ACCEPT = KnowledgeSource(_SOURCE, "Opener's Responsibilities")
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _is_sayc(context: BiddingContext) -> bool:
    return context.system.system.casefold() in _SAYC_NAMES


def _calls(context: BiddingContext) -> tuple[str, ...]:
    return tuple(e.call.serialize() for e in context.auction.entries)


def _response_gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if not _is_sayc(context):
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")
    if _calls(context) != ("2NT", "P"):
        return RuleDecision.not_applicable(rule_id, "Rule applies only to uncontested 2NT — Pass — ?.")
    return None


@dataclass(frozen=True, slots=True)
class SaycTwoNotrumpJacobyResponseRule:
    target: Suit
    rule_id: str

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _response_gate(context, self.rule_id)
        if gate is not None:
            return gate
        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)
        if hearts >= 5 and spades >= 5:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Frozen Jacoby source gives no precedence when both majors are five cards or longer.",
            )
        length = hearts if self.target is Suit.HEARTS else spades
        if length < 5:
            return RuleDecision.not_applicable(self.rule_id, "Jacoby Transfer requires a five-card or longer target major.")
        candidate = Call.parse("3D" if self.target is Suit.HEARTS else "3H")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation=(
                "After a 2NT opening, the frozen Jacoby source uses 3D to transfer to hearts "
                "and 3H to transfer to spades; responder may transfer with any strength and 5+ cards."
            ),
            sources=(_TRANSFER, _REQUIREMENTS),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycTwoNotrumpJacobyAcceptRule:
    transfer_call: str
    completion_call: str
    rule_id: str

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if not _is_sayc(context):
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined only for SAYC.")
        expected = ("2NT", "P", self.transfer_call, "P")
        if _calls(context) != expected:
            return RuleDecision.not_applicable(self.rule_id, "Rule applies only to the exact uncontested Jacoby-transfer auction.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(self.completion_call),
            explanation="The frozen Jacoby source says opener normally accepts the transfer after 2NT.",
            sources=(_TRANSFER, _ACCEPT),
            priority=100,
        )


def create_sayc_two_notrump_jacoby_response_engine() -> BiddingEngine:
    return BiddingEngine((
        SaycTwoNotrumpJacobyResponseRule(Suit.HEARTS, "sayc.response.2nt.jacoby.hearts"),
        SaycTwoNotrumpJacobyResponseRule(Suit.SPADES, "sayc.response.2nt.jacoby.spades"),
    ))


def create_sayc_two_notrump_jacoby_accept_engine() -> BiddingEngine:
    return BiddingEngine((
        SaycTwoNotrumpJacobyAcceptRule("3D", "3H", "sayc.opener.2nt.jacoby.accept.hearts"),
        SaycTwoNotrumpJacobyAcceptRule("3H", "3S", "sayc.opener.2nt.jacoby.accept.spades"),
    ))
