"""Policy-gated GAME_GOING responder continuations after 1NT Stayman."""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
from .policy_registry import (
    PolicyRegistry,
    assess_configured_stayman_continuation_strength,
)
from .stayman_continuation_strength_policy import StaymanContinuationStrength


_SOURCE = KnowledgeSource(
    "bidding/conventions/responses/stayman", "Responder's Continuations"
)
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _calls(context: BiddingContext) -> tuple[str, ...]:
    return tuple(entry.call.serialize() for entry in context.auction.entries)


@dataclass(frozen=True, slots=True)
class SaycOneNotrumpStaymanMajorFitGameContinuationRule:
    registry: PolicyRegistry
    rule_id: str = "sayc.responder.1nt.stayman.major_fit.game"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "SAYC only.")

        auction = _calls(context)
        if auction == ("1NT", "P", "2C", "P", "2H", "P"):
            shown_suit, game_call = Suit.HEARTS, "4H"
        elif auction == ("1NT", "P", "2C", "P", "2S", "P"):
            shown_suit, game_call = Suit.SPADES, "4S"
        else:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires an exact uncontested 1NT Stayman major response.",
            )

        assessment = assess_configured_stayman_continuation_strength(
            context, self.registry
        )
        if assessment is None:
            return RuleDecision.not_applicable(
                self.rule_id,
                "No Stayman continuation strength policy is explicitly configured.",
            )
        if assessment.classification is not StaymanContinuationStrength.GAME_GOING:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Configured policy did not classify this continuation as GAME_GOING.",
            )
        if context.evaluation.length(shown_suit) < 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Responder lacks four-card support for opener's shown major.",
            )

        sources = (_SOURCE,) + tuple(
            source for source in assessment.sources if source != _SOURCE
        )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(game_call),
            explanation=(
                f"Explicit GAME_GOING classification and an established major fit: "
                f"bid {game_call}. {assessment.explanation.strip()}"
            ),
            sources=sources,
            priority=100,
        )


def create_sayc_one_notrump_stayman_major_fit_game_continuation_engine(
    registry: PolicyRegistry,
) -> BiddingEngine:
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    return BiddingEngine(
        (SaycOneNotrumpStaymanMajorFitGameContinuationRule(registry),)
    )

