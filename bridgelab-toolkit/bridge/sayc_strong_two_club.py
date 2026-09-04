"""Conservative SAYC response to an established strong 2C opening."""
from __future__ import annotations
from dataclasses import dataclass
from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision

_SOURCE = KnowledgeSource("bidding/systems/sayc", "Responses")
_BALANCED_REBID_SOURCE = KnowledgeSource(
    "bidding/natural-bids/responses/response-to-2-clubs", "Opener's Rebids"
)
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


@dataclass(frozen=True, slots=True)
class SaycStrongTwoClubBalancedRebidRule:
    """Source-gated balanced 22–24 HCP rebid after the 2D waiting response."""

    rule_id: str = "sayc.opener.2c.2d.2nt.balanced-22-24"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is SAYC only.")
        if context.auction.serialize() != "2C P 2D P":
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires the exact uncontested 2C-P-2D-P opener-rebid position.",
            )
        evaluation = context.evaluation
        if not evaluation.is_balanced or not 22 <= evaluation.hcp <= 24:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Frozen source supports only a balanced 22–24 HCP opener rebidding 2NT.",
            )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2NT"),
            priority=100,
            explanation=(
                "After the 2D waiting response, the frozen source maps a balanced "
                "22–24 HCP strong-2C opener to 2NT."
            ),
            sources=(_BALANCED_REBID_SOURCE,),
        )


def create_sayc_strong_two_club_balanced_rebid_engine() -> BiddingEngine:
    return BiddingEngine((SaycStrongTwoClubBalancedRebidRule(),))
