"""Conservative SAYC response to an established strong 2C opening."""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision

_SOURCE = KnowledgeSource("bidding/systems/sayc", "Responses")
_NAMES={"sayc","standard american yellow card"}

@dataclass(frozen=True, slots=True)
class SaycStrongTwoClubWaitingResponseRule:
    rule_id: str = "sayc.response.2c.2d.waiting"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _NAMES:
            return RuleDecision.not_applicable(self.rule_id,"Rule is SAYC only.")
        if context.auction.serialize() != "2C P":
            return RuleDecision.not_applicable(self.rule_id,"Requires exact uncontested 2C-P response position.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2D"),
            priority=100,
            explanation=(
                "The frozen SAYC source defines 2♦ as the waiting/default response "
                "to the strong artificial 2♣ opening; positive responses vary by partnership."
            ),
            sources=(_SOURCE,),
        )

def create_sayc_strong_two_club_response_engine() -> BiddingEngine:
    return BiddingEngine((SaycStrongTwoClubWaitingResponseRule(),))
