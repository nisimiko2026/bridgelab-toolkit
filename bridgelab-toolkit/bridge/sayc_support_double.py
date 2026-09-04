"""Narrow source-grounded SAYC Support Double.

Phase 9R activates only frozen-source example auction shapes. It deliberately
does not generalize to every possible Support Double sequence. Eligibility
items left qualitative/partnership-dependent by the source are delegated to an
explicit SupportDoubleEligibilityPolicy with no default.
"""
from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit
from .policy_registry import PolicyRegistry, assess_configured_support_double_eligibility
from .support_double_eligibility_policy import SupportDoubleEligibilityStatus

_SAYC_SOURCE = KnowledgeSource("bidding/systems/sayc", "Support Double")
_DETAIL_SOURCE = KnowledgeSource("bidding/conventions/doubles/support-double", "When to Use")

# Frozen-source examples only. These are intentionally not a generic convention
# grammar. Support Redouble is excluded and remains a separate future branch.
_EXAMPLE_AUCTIONS = {
    ("1D", "P", "1H", "1S"): Suit.HEARTS,
    ("1C", "P", "1H", "1S"): Suit.HEARTS,
    ("1D", "P", "1S", "2C"): Suit.SPADES,
    ("1H", "P", "1S", "2D"): Suit.SPADES,
}


def _supported_responder_suit(context: BiddingContext) -> Suit | None:
    calls = tuple(call.serialize() for call in context.auction.calls)
    return _EXAMPLE_AUCTIONS.get(calls)


@dataclass(frozen=True, slots=True)
class SaycSupportDoubleExampleRule:
    registry: PolicyRegistry
    rule_id: str = "sayc.double.support.example_slice"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.strip().casefold() not in {
            "sayc", "standard american yellow card"
        }:
            return RuleDecision.not_applicable(self.rule_id, "Rule is SAYC-only.")

        responder_suit = _supported_responder_suit(context)
        if responder_suit is None:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Phase 9R is restricted to frozen-source Support Double example auctions.",
            )

        if context.hand.length(responder_suit) != 3:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Frozen Support Double source requires exactly three-card support for responder's suit.",
            )

        assessment = assess_configured_support_double_eligibility(context, self.registry)
        if assessment is None or assessment.status is SupportDoubleEligibilityStatus.UNKNOWN:
            return RuleDecision.not_applicable(
                self.rule_id,
                "No known configured Support Double eligibility verdict is available.",
            )
        if assessment.status is not SupportDoubleEligibilityStatus.QUALIFIES:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Configured Support Double eligibility policy does not qualify this hand/auction.",
            )

        candidate = Call.double()
        if not context.auction.is_legal(candidate):
            return RuleDecision.not_applicable(
                self.rule_id, "Double is not legal in the current auction."
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation=(
                "Source-grounded Support Double example slice: opener has exactly "
                "three-card support for responder's major and the explicitly configured "
                "eligibility policy qualifies the unresolved partnership conditions."
            ),
            sources=tuple(dict.fromkeys((_SAYC_SOURCE, _DETAIL_SOURCE) + assessment.sources)),
            priority=100,
        )


def create_sayc_support_double_example_engine(registry: PolicyRegistry) -> BiddingEngine:
    return BiddingEngine((SaycSupportDoubleExampleRule(registry),))
