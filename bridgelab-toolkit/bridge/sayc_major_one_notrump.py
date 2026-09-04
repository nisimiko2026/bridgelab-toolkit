"""Controlled SAYC 1NT responses after one-major openings.

Canonical source:
``bidding/natural-bids/responses/response-to-major-opening``

The source states that 1NT is usually:
* 6–9 HCP,
* balanced,
* no support,
* no better natural response.

It also states:
* after 1♥, 1♠ shows 4+ spades and at least 6 HCP;
* support has priority;
* forcing 1NT is optional in SAYC.

Therefore these rules require an explicit ``forcing_one_notrump`` partnership
setting.  The selected treatment changes the explanation/trace, not the call.

The source does not provide a precise executable definition of every possible
two-level "better natural response", so this controlled slice only excludes
better responses that are already explicit in the same source: a major raise
and, after 1♥, the 1♠ response.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .evaluation import ShapeClass
from .major_response_options import (
    ForcingOneNotrumpTreatment,
    forcing_one_notrump_treatment,
)
from .models import Suit


ARTICLE = "bidding/natural-bids/responses/response-to-major-opening"
PRIORITIES = KnowledgeSource(ARTICLE, "Responder's Priorities")
ONE_NT = KnowledgeSource(ARTICLE, "1NT")
OTHER_MAJOR = KnowledgeSource(ARTICLE, "Responding with Another Major")
SAYC = KnowledgeSource(ARTICLE, "SAYC")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _gate(
    context: BiddingContext,
    rule_id: str,
    opening_strain: Strain,
) -> RuleDecision | None:
    if context.system.system.casefold() not in _SAYC_NAMES:
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")

    entries = context.auction.entries
    if len(entries) != 2:
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested one-major — Pass — ?."
        )

    opening, rho = entries
    if (
        opening.seat is not context.seat.partner()
        or opening.call.kind is not CallType.BID
        or opening.call.bid is None
        or opening.call.bid.level != 1
        or opening.call.bid.strain is not opening_strain
        or rho.call.kind is not CallType.PASS
    ):
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested one-major — Pass — ?."
        )
    return None


def _treatment(context: BiddingContext) -> ForcingOneNotrumpTreatment:
    return forcing_one_notrump_treatment(context.system)


def _treatment_explanation(treatment: ForcingOneNotrumpTreatment) -> str:
    if treatment is ForcingOneNotrumpTreatment.FORCING:
        return "Partnership configuration explicitly plays the 1NT response as forcing."
    if treatment is ForcingOneNotrumpTreatment.NONFORCING:
        return "Partnership configuration explicitly plays the 1NT response as nonforcing."
    raise ValueError("1NT treatment must be explicitly configured")


def _common_requirements(
    context: BiddingContext,
    rule_id: str,
    trump: Suit,
) -> RuleDecision | None:
    treatment = _treatment(context)
    if treatment is ForcingOneNotrumpTreatment.UNSPECIFIED:
        return RuleDecision.not_applicable(
            rule_id,
            "Forcing/nonforcing 1NT treatment is not configured.",
        )
    if not 6 <= context.evaluation.hcp <= 9:
        return RuleDecision.not_applicable(rule_id, "Requires 6–9 HCP.")
    if context.evaluation.shape_class is not ShapeClass.BALANCED:
        return RuleDecision.not_applicable(rule_id, "Requires a balanced hand.")
    if context.evaluation.length(trump) >= 3:
        return RuleDecision.not_applicable(
            rule_id,
            "Responder has support; source gives raising partner's major priority.",
        )
    return None


@dataclass(frozen=True, slots=True)
class SaycResponseToOneHeartOneNotrumpRule:
    rule_id: str = "sayc.response.1h.1nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id, Strain.HEARTS)
        if gate is not None:
            return gate

        common = _common_requirements(context, self.rule_id, Suit.HEARTS)
        if common is not None:
            return common

        if context.evaluation.length(Suit.SPADES) >= 4:
            return RuleDecision.not_applicable(
                self.rule_id,
                "A 1♠ response is a better explicit natural response after 1♥.",
            )

        treatment = _treatment(context)
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1NT"),
            explanation=(
                "The source defines 1NT as usually 6–9 HCP, balanced, without "
                "support and without a better natural response. "
                + _treatment_explanation(treatment)
            ),
            sources=(PRIORITIES, ONE_NT, OTHER_MAJOR, SAYC),
            priority=70,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneSpadeOneNotrumpRule:
    rule_id: str = "sayc.response.1s.1nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id, Strain.SPADES)
        if gate is not None:
            return gate

        common = _common_requirements(context, self.rule_id, Suit.SPADES)
        if common is not None:
            return common

        treatment = _treatment(context)
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1NT"),
            explanation=(
                "The source defines 1NT as usually 6–9 HCP, balanced, without "
                "support and without a better natural response. After 1♠ the "
                "source states there is no higher-ranking major response. "
                + _treatment_explanation(treatment)
            ),
            sources=(PRIORITIES, ONE_NT, OTHER_MAJOR, SAYC),
            priority=70,
        )


def sayc_major_one_notrump_response_rules():
    return (
        SaycResponseToOneHeartOneNotrumpRule(),
        SaycResponseToOneSpadeOneNotrumpRule(),
    )


def create_sayc_major_one_notrump_response_engine() -> BiddingEngine:
    return BiddingEngine(sayc_major_one_notrump_response_rules())
