"""Deterministic opener responses after an established SAYC 1NT Stayman inquiry.

This module deliberately does not select responder's 2C inquiry. The frozen
Stayman source leaves responder minimum strength partnership-dependent.
"""
from __future__ import annotations
from dataclasses import dataclass

from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
from .policy_registry import (
    PolicyRegistry,
    assess_configured_stayman_dual_major_response,
)
from .stayman_dual_major_response_policy import StaymanDualMajorResponse

_SOURCE = "bidding/conventions/responses/stayman"
_RESPONSES = KnowledgeSource(_SOURCE, "Opener's Responses")
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _calls(context: BiddingContext) -> tuple[str, ...]:
    return tuple(e.call.serialize() for e in context.auction.entries)


@dataclass(frozen=True, slots=True)
class SaycOneNotrumpStaymanOpenerResponseRule:
    registry: PolicyRegistry
    rule_id: str = "sayc.opener.1nt.stayman"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined only for SAYC.")
        if _calls(context) != ("1NT", "P", "2C", "P"):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Rule applies only after the exact uncontested 1NT — Pass — 2C — Pass Stayman inquiry.",
            )

        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)
        has_hearts = hearts >= 4
        has_spades = spades >= 4

        policy_explanation = ""
        policy_sources: tuple[KnowledgeSource, ...] = ()
        if has_hearts and has_spades:
            if hearts != 4 or spades != 4:
                return RuleDecision.not_applicable(
                    self.rule_id,
                    "Dual-major policy scope is limited to exactly four hearts and four spades.",
                )
            assessment = assess_configured_stayman_dual_major_response(
                context, self.registry
            )
            if assessment is None:
                return RuleDecision.not_applicable(
                    self.rule_id,
                    "No Stayman dual-major response policy is explicitly configured.",
                )
            if assessment.response is StaymanDualMajorResponse.UNKNOWN:
                return RuleDecision.not_applicable(
                    self.rule_id,
                    "Configured dual-major response policy returned UNKNOWN.",
                )
            if assessment.response is StaymanDualMajorResponse.HEARTS:
                candidate = Call.parse("2H")
                branch = "heart-showing"
            else:
                candidate = Call.parse("2S")
                branch = "spade-showing"
            policy_explanation = (
                f" Explicit partnership policy selects the {branch} branch. "
                f"{assessment.explanation.strip()}"
            )
            policy_sources = assessment.sources
        elif has_hearts:
            candidate = Call.parse("2H")
            explanation = "After 1NT–2C Stayman, 2H shows a four-card heart suit."
        elif has_spades:
            candidate = Call.parse("2S")
            explanation = "After 1NT–2C Stayman, 2S shows a four-card spade suit and normally denies four hearts."
        else:
            candidate = Call.parse("2D")
            explanation = "After 1NT–2C Stayman, 2D denies a four-card major."

        if has_hearts and has_spades:
            explanation = (
                "After 1NT–2C Stayman with exactly four cards in both majors,"
                + policy_explanation
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation=explanation,
            sources=(_RESPONSES,)
            + tuple(source for source in policy_sources if source != _RESPONSES),
            priority=100,
        )


def create_sayc_one_notrump_stayman_opener_response_engine(
    registry: PolicyRegistry | None = None,
) -> BiddingEngine:
    if registry is None:
        registry = PolicyRegistry()
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    return BiddingEngine((SaycOneNotrumpStaymanOpenerResponseRule(registry),))
