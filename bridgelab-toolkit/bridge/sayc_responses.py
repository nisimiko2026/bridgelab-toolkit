"""Controlled SAYC responses to a 1♣ opening.

Phase 5G deliberately implements only an uncontested ``1♣ — Pass — ?``
responder family that is directly supported by the canonical BridgeLab article
``bidding/natural-bids/responses/response-to-1-club``.

The source describes several treatments as "usually", "typical", or
partnership-dependent.  This module therefore uses conservative predicates and
returns ``not_applicable`` for ambiguous cases instead of filling gaps from
general bridge knowledge.

Implemented subset:

* Pass with 0–5 HCP.
* 1♦ with 6+ HCP, 4+ diamonds, no four-card major, and diamonds longer than
  clubs.
* 1♥ with 6+ HCP and 4+ hearts when spades are shorter; this includes the
  source-defined both-major subset where hearts are strictly longer.
* 1♠ with 6+ HCP and 4+ spades when hearts are shorter; this includes the
  source-defined both-major subset where spades are strictly longer.
* Equal-length holdings with both majors 4+ remain unresolved.
* 1NT with 6–10 HCP, a canonical balanced shape, and no four-card major.
Club raises are intentionally deferred.  Although the
source gives point ranges for those calls, it also gives responder priorities
and alternative club-raise treatments that create precedence questions.  Phase
5G leaves those cases unresolved rather than silently choosing a treatment.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit


_SOURCE = "bidding/natural-bids/responses/response-to-1-club"

_STRENGTH = KnowledgeSource(_SOURCE, "Strength Categories")
_PRIORITIES = KnowledgeSource(_SOURCE, "Responder's Priorities")
_MAJOR_RESPONSES = KnowledgeSource(_SOURCE, "Responses with Major Suits")
_DIAMONDS = KnowledgeSource(_SOURCE, "Responding with Diamonds")
_NOTRUMP = KnowledgeSource(_SOURCE, "Notrump Responses")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _is_sayc(context: BiddingContext) -> bool:
    return context.system.system.casefold() in _SAYC_NAMES


def _is_exact_uncontested_one_club_response(context: BiddingContext) -> bool:
    entries = context.auction.entries
    if len(entries) != 2:
        return False

    opening, rho = entries
    if opening.call.kind is not CallType.BID or opening.call.bid is None:
        return False
    if opening.call.bid.level != 1 or opening.call.bid.strain is not Strain.CLUBS:
        return False
    if rho.call.kind is not CallType.PASS:
        return False

    return opening.seat is context.seat.partner()


def _gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if not _is_sayc(context):
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")
    if not _is_exact_uncontested_one_club_response(context):
        return RuleDecision.not_applicable(
            rule_id,
            "Controlled Phase 5G rule applies only to uncontested 1♣ — Pass — ?.",
        )
    return None


def _has_four_card_major(context: BiddingContext) -> bool:
    return (
        context.evaluation.length(Suit.HEARTS) >= 4
        or context.evaluation.length(Suit.SPADES) >= 4
    )


def _clear_longer_diamond_response(context: BiddingContext) -> bool:
    diamonds = context.evaluation.length(Suit.DIAMONDS)
    clubs = context.evaluation.length(Suit.CLUBS)
    return diamonds >= 4 and diamonds > clubs and not _has_four_card_major(context)



@dataclass(frozen=True, slots=True)
class SaycResponseToOneClubPassRule:
    rule_id: str = "sayc.response.1c.pass"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not 0 <= context.evaluation.hcp <= 5:
            return RuleDecision.not_applicable(self.rule_id, "Requires 0–5 HCP.")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.pass_(),
            explanation=(
                "The BridgeLab 1♣ response article lists 0–5 HCP as the pass "
                "strength category."
            ),
            sources=(_STRENGTH,),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneClubOneHeartRule:
    rule_id: str = "sayc.response.1c.1h"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)
        if not (
            context.evaluation.hcp >= 6
            and hearts >= 4
            and (spades < 4 or hearts > spades)
        ):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 6+ HCP and 4+ hearts; when both majors "
                "are present, hearts must be strictly longer because the source says "
                "to bid the longest major first.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1H"),
            explanation=(
                "After 1♣, the source says responder's first priority is to show "
                "a four-card major; 1♥ shows 6+ HCP and four or more hearts. "
                "When both majors are present, this controlled subset follows the "
                "source instruction to bid the longest major first; equal lengths "
                "remain unresolved."
            ),
            sources=(_PRIORITIES, _MAJOR_RESPONSES),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneClubOneSpadeRule:
    rule_id: str = "sayc.response.1c.1s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        spades = context.evaluation.length(Suit.SPADES)
        hearts = context.evaluation.length(Suit.HEARTS)
        if not (
            context.evaluation.hcp >= 6
            and spades >= 4
            and (hearts < 4 or spades > hearts)
        ):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 6+ HCP and 4+ spades; when both majors "
                "are present, spades must be strictly longer because the source says "
                "to bid the longest major first.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1S"),
            explanation=(
                "After 1♣, the source says responder's first priority is to show "
                "a four-card major; 1♠ shows 6+ HCP and four or more spades. "
                "When both majors are present, this controlled subset follows the "
                "source instruction to bid the longest major first; equal lengths "
                "remain unresolved."
            ),
            sources=(_PRIORITIES, _MAJOR_RESPONSES),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneClubOneDiamondRule:
    rule_id: str = "sayc.response.1c.1d"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        if context.evaluation.hcp < 6 or not _clear_longer_diamond_response(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 6+ HCP, 4+ diamonds, no four-card major, "
                "and diamonds longer than clubs.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1D"),
            explanation=(
                "The BridgeLab response article says 1♦ usually shows 6+ HCP, "
                "four or more diamonds and no four-card major, and separately "
                "describes a natural response when diamonds are longer."
            ),
            sources=(_MAJOR_RESPONSES, _DIAMONDS),
            priority=80,
        )



@dataclass(frozen=True, slots=True)
class SaycResponseToOneClubOneNotrumpRule:
    rule_id: str = "sayc.response.1c.1nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        if not (
            6 <= context.evaluation.hcp <= 10
            and context.evaluation.is_balanced
            and not _has_four_card_major(context)
        ):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 6–10 HCP, a balanced hand, and no four-card major.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1NT"),
            explanation=(
                "After 1♣, the frozen SAYC response source defines 1NT as "
                "6–10 HCP with a balanced hand; major-suit responses have higher "
                "priority, so this controlled rule excludes every four-card major."
            ),
            sources=(_PRIORITIES, _NOTRUMP),
            priority=70,
        )


def sayc_one_club_response_rules() -> tuple[
    SaycResponseToOneClubPassRule,
    SaycResponseToOneClubOneHeartRule,
    SaycResponseToOneClubOneSpadeRule,
    SaycResponseToOneClubOneDiamondRule,
    SaycResponseToOneClubOneNotrumpRule,
]:
    return (
        SaycResponseToOneClubPassRule(),
        SaycResponseToOneClubOneHeartRule(),
        SaycResponseToOneClubOneSpadeRule(),
        SaycResponseToOneClubOneDiamondRule(),
        SaycResponseToOneClubOneNotrumpRule(),
    )


def create_sayc_one_club_response_engine() -> BiddingEngine:
    return BiddingEngine(sayc_one_club_response_rules())
