"""Controlled SAYC natural one-level overcall selection.

Frozen SAYC source requirements for a simple overcall are 8–17 HCP, a good
five-card suit, and suitable playing strength. BridgeLab keeps the two
qualitative requirements behind explicit configured policies: SuitQualityPolicy
and PlayingStrengthPolicy. No default interpretation is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .bidding_engine import BiddingEngine
from .models import Suit
from .policy_registry import PolicyRegistry, assess_configured_suit_quality, assess_configured_playing_strength
from .suit_quality_policy import SuitQualityStatus
from .playing_strength_policy import PlayingStrengthStatus

_SOURCE = KnowledgeSource("bidding/systems/sayc", "Natural Overcalls")
_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _direct_one_level_opening(context: BiddingContext) -> Strain | None:
    entries = context.auction.entries
    if len(entries) != 1:
        return None
    opening = entries[0]
    if opening.call.kind is not CallType.BID or opening.call.bid is None:
        return None
    bid = opening.call.bid
    if bid.level != 1 or bid.strain is Strain.NOTRUMP:
        return None
    return bid.strain


def legal_one_level_overcall_suits(opening: Strain) -> tuple[Suit, ...]:
    """Return only suits that can legally overcall the opening at level one."""
    if opening is Strain.NOTRUMP:
        return ()
    return tuple(Suit(value) for value in range(int(opening) + 1, int(Strain.NOTRUMP)))


@dataclass(frozen=True, slots=True)
class SaycNaturalOneLevelOvercallRule:
    registry: PolicyRegistry
    rule_id: str = "sayc.overcall.one_level.natural"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in _SAYC_NAMES:
            return RuleDecision.not_applicable(self.rule_id, "Rule is defined for configured SAYC partnerships.")

        opening = _direct_one_level_opening(context)
        if opening is None:
            return RuleDecision.not_applicable(self.rule_id, "Requires a direct seat after one natural one-level suit opening.")

        if not 8 <= context.evaluation.hcp <= 17:
            return RuleDecision.not_applicable(self.rule_id, "Frozen SAYC source gives 8–17 HCP for a simple overcall.")

        eligible = [s for s in legal_one_level_overcall_suits(opening) if context.evaluation.length(s) >= 5]
        if not eligible:
            return RuleDecision.not_applicable(self.rule_id, "No legally available one-level suit has five or more cards.")

        qualified = []
        unresolved = []
        for suit in eligible:
            assessment = assess_configured_suit_quality(context, self.registry, suit)
            if assessment is None or assessment.status is SuitQualityStatus.UNKNOWN:
                unresolved.append(suit)
            elif assessment.status is SuitQualityStatus.QUALIFIES:
                qualified.append((suit, assessment))

        if unresolved:
            return RuleDecision.not_applicable(
                self.rule_id,
                "At least one five-card legal candidate has no known configured suit-quality verdict; selection is unresolved.",
            )
        if not qualified:
            return RuleDecision.not_applicable(self.rule_id, "Configured suit-quality policy qualifies no legal five-card candidate.")
        if len(qualified) != 1:
            return RuleDecision.not_applicable(self.rule_id, "More than one legal five-card suit qualifies; source gives no selector here.")

        strength = assess_configured_playing_strength(context, self.registry)
        if strength is None or strength.status is PlayingStrengthStatus.UNKNOWN:
            return RuleDecision.not_applicable(
                self.rule_id,
                "The frozen source also requires suitable playing strength; no known configured playing-strength verdict is available.",
            )
        if strength.status is not PlayingStrengthStatus.QUALIFIES:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Configured playing-strength policy does not qualify this hand for the source requirement.",
            )

        suit, quality = qualified[0]
        strain = Strain(int(suit))
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(f"1{strain.symbol}"),
            explanation=(
                "Frozen SAYC source gives 8–17 HCP, a good five-card suit, and "
                "suitable playing strength for a simple overcall. This hand has "
                "one legal 5+ one-level candidate, and both explicitly configured "
                "policies qualify the source's qualitative requirements."
            ),
            sources=tuple(dict.fromkeys((_SOURCE,) + quality.sources + strength.sources)),
            priority=100,
        )


def sayc_natural_one_level_overcall_rules(registry: PolicyRegistry):
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    return (SaycNaturalOneLevelOvercallRule(registry),)


def create_sayc_natural_one_level_overcall_engine(
    registry: PolicyRegistry,
) -> BiddingEngine:
    return BiddingEngine(sayc_natural_one_level_overcall_rules(registry))
