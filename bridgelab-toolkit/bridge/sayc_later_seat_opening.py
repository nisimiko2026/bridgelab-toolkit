"""A9.7.1 adapter from the approved A9 two-suited opening policy to BridgeLab's engine contract.

This module is intentionally narrow:
* SAYC only;
* third/fourth seat after preceding Passes;
* only A9's 5-5 / 6-5 / 6-6 policy scope.

It does not alter the router. A9.7.2 owns route registration.
"""
from __future__ import annotations

from dataclasses import dataclass

from .auction import Call
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .opening_profile_policy import (
    OpeningPolicyStatus,
    OpeningProfile,
    evaluate_two_suited_opening,
)

_SOURCE = KnowledgeSource(
    "bidding/principles/bidding-fundamentals/seat-position",
    "A9 approved later-seat opening policy",
)


def _seat_number(context: BiddingContext) -> int | None:
    calls = context.auction.serialize().upper()
    if calls == "P P":
        return 3
    if calls == "P P P":
        return 4
    return None


@dataclass(frozen=True, slots=True)
class SaycLaterSeatTwoSuitedOpeningRule:
    rule_id: str = "sayc.opening.later-seat.two-suited"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        if context.system.system.casefold() not in {
            "sayc", "standard american yellow card"
        }:
            return RuleDecision.not_applicable(
                self.rule_id, "A9.7.1 adapter is SAYC-only."
            )

        seat_number = _seat_number(context)
        if seat_number is None:
            return RuleDecision.not_applicable(
                self.rule_id,
                "A9.7.1 applies only after exactly P P or P P P.",
            )

        policy = evaluate_two_suited_opening(
            context.hand,
            profile=OpeningProfile.SAYC,
            seat_number=seat_number,
        )

        if policy.status is not OpeningPolicyStatus.OPEN:
            return RuleDecision.not_applicable(
                self.rule_id,
                f"A9 opening policy returned {policy.status.value}: {policy.basis}",
            )

        assert policy.call is not None
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(policy.call),
            explanation=policy.basis,
            sources=(_SOURCE,),
            priority=100,
        )


def create_sayc_later_seat_opening_engine() -> BiddingEngine:
    return BiddingEngine((SaycLaterSeatTwoSuitedOpeningRule(),))
