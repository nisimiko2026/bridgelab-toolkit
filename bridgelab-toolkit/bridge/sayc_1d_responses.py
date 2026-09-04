"""Controlled SAYC responses to a 1♦ opening.

Phase 5H implements only the unambiguous responder rules directly supported by
the canonical BridgeLab article
``bidding/natural-bids/responses/response-to-1-diamond``.

Implemented subset for the exact uncontested auction ``1♦ — Pass — ?``:

* Pass with 0–5 HCP.
* 1♥ with 6+ HCP and 4+ hearts.  The source explicitly says that with both
  majors responder bids hearts first.
* 1♠ with 6+ HCP, 4+ spades, and fewer than four hearts.

Diamond raises are deliberately deferred because SAYC permits traditional
raises while Inverted Minors are optional.  Notrump responses are also deferred
because the source includes stopper requirements that are not yet represented
by the Phase 5C hand evaluator.  The natural 2♣ response is described only as
"usually constructive", without a precise strength contract, so it is not
encoded here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit


_SOURCE = "bidding/natural-bids/responses/response-to-1-diamond"

_STRENGTH = KnowledgeSource(_SOURCE, "Strength Categories")
_PRIORITIES = KnowledgeSource(_SOURCE, "Responder's Priorities")
_MAJOR_SECTION = KnowledgeSource(_SOURCE, "Responding with a Major Suit")
_ONE_HEART = KnowledgeSource(_SOURCE, "1♥")
_ONE_SPADE = KnowledgeSource(_SOURCE, "1♠")

_SAYC_NAMES = {"sayc", "standard american yellow card"}


def _is_sayc(context: BiddingContext) -> bool:
    return context.system.system.casefold() in _SAYC_NAMES


def _is_exact_uncontested_one_diamond_response(context: BiddingContext) -> bool:
    entries = context.auction.entries
    if len(entries) != 2:
        return False

    opening, rho = entries
    if opening.call.kind is not CallType.BID or opening.call.bid is None:
        return False
    if opening.call.bid.level != 1 or opening.call.bid.strain is not Strain.DIAMONDS:
        return False
    if rho.call.kind is not CallType.PASS:
        return False

    return opening.seat is context.seat.partner()


def _gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if not _is_sayc(context):
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")
    if not _is_exact_uncontested_one_diamond_response(context):
        return RuleDecision.not_applicable(
            rule_id,
            "Controlled Phase 5H rule applies only to uncontested 1♦ — Pass — ?.",
        )
    return None


@dataclass(frozen=True, slots=True)
class SaycResponseToOneDiamondPassRule:
    rule_id: str = "sayc.response.1d.pass"

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
                "The BridgeLab response-to-1♦ article lists 0–5 HCP as the pass "
                "strength category."
            ),
            sources=(_STRENGTH,),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneDiamondOneHeartRule:
    rule_id: str = "sayc.response.1d.1h"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        hearts = context.evaluation.length(Suit.HEARTS)
        if not (context.evaluation.hcp >= 6 and hearts >= 4):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires 6+ HCP and four or more hearts.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1H"),
            explanation=(
                "After 1♦, the BridgeLab article gives priority to locating a "
                "major-suit fit. 1♥ shows 6+ HCP and 4+ hearts; with both majors "
                "the source explicitly instructs responder to bid hearts first."
            ),
            sources=(_PRIORITIES, _MAJOR_SECTION, _ONE_HEART),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneDiamondOneSpadeRule:
    rule_id: str = "sayc.response.1d.1s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate

        spades = context.evaluation.length(Suit.SPADES)
        hearts = context.evaluation.length(Suit.HEARTS)
        if not (context.evaluation.hcp >= 6 and spades >= 4 and hearts < 4):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Requires 6+ HCP, four or more spades, and fewer than four hearts.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1S"),
            explanation=(
                "After 1♦, 1♠ shows 6+ HCP and 4+ spades. The controlled rule "
                "requires fewer than four hearts because the source explicitly "
                "says to respond hearts first when responder holds both majors."
            ),
            sources=(_PRIORITIES, _MAJOR_SECTION, _ONE_SPADE),
            priority=90,
        )


def sayc_one_diamond_response_rules() -> tuple[
    SaycResponseToOneDiamondPassRule,
    SaycResponseToOneDiamondOneHeartRule,
    SaycResponseToOneDiamondOneSpadeRule,
]:
    """Return the fixed Phase 5H response registry."""
    return (
        SaycResponseToOneDiamondPassRule(),
        SaycResponseToOneDiamondOneHeartRule(),
        SaycResponseToOneDiamondOneSpadeRule(),
    )


def create_sayc_one_diamond_response_engine() -> BiddingEngine:
    """Construct an engine for the Phase 5H controlled 1♦ response subset."""
    return BiddingEngine(sayc_one_diamond_response_rules())
