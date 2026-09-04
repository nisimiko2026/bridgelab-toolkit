"""Controlled SAYC responses to a 1♥ opening.

Canonical source:
``bidding/natural-bids/responses/response-to-major-opening``

Phase 5M encodes only responses whose strength, fit, and priority conditions are
explicit enough to execute without inventing partnership agreements:

* Pass: 0–5 HCP.
* 2♥ simple raise: approximately 6–9 HCP with 3+ heart support.
* 3♥ traditional limit raise: approximately 10–12 HCP with 4+ heart support.
* 1♠: 6+ HCP with 4+ spades when responder does not have the 3-card heart
  support needed for the source-defined simple raise.

The source says SAYC has a natural structure and that forcing 1NT is optional.
Accordingly 1NT is not implemented here.  The source also says many
partnerships replace the traditional 3♥ limit raise with Bergen Raises; this
controlled rule is therefore enabled only when the explicit system option
``major_raise_style`` is absent or equals ``traditional``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType, Strain
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit


ARTICLE = "bidding/natural-bids/responses/response-to-major-opening"
STRENGTH = KnowledgeSource(ARTICLE, "Strength Categories")
PRIORITIES = KnowledgeSource(ARTICLE, "Responder's Priorities")
SIMPLE_RAISE = KnowledgeSource(ARTICLE, "Simple Raise")
LIMIT_RAISE = KnowledgeSource(ARTICLE, "Limit Raise")
OTHER_MAJOR = KnowledgeSource(ARTICLE, "Responding with Another Major")
SAYC = KnowledgeSource(ARTICLE, "SAYC")

_SAYC_NAMES = {"sayc", "standard american yellow card"}
_MAJOR_RAISE_STYLE_OPTION = "major_raise_style"


def _gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if context.system.system.casefold() not in _SAYC_NAMES:
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")

    entries = context.auction.entries
    if len(entries) != 2:
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested 1♥ — Pass — ?."
        )

    opening, rho = entries
    if (
        opening.seat is not context.seat.partner()
        or opening.call.kind is not CallType.BID
        or opening.call.bid is None
        or opening.call.bid.level != 1
        or opening.call.bid.strain is not Strain.HEARTS
        or rho.call.kind is not CallType.PASS
    ):
        return RuleDecision.not_applicable(
            rule_id, "Requires exact uncontested 1♥ — Pass — ?."
        )
    return None


def _traditional_major_raises(context: BiddingContext) -> bool:
    style = context.system.option(_MAJOR_RAISE_STYLE_OPTION)
    if style is None:
        return True
    return str(style).strip().casefold() == "traditional"


@dataclass(frozen=True, slots=True)
class SaycResponseToOneHeartPassRule:
    rule_id: str = "sayc.response.1h.pass"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not 0 <= context.evaluation.hcp <= 5:
            return RuleDecision.not_applicable(self.rule_id, "Requires 0–5 HCP.")

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.pass_(),
            explanation="The source lists 0–5 HCP as the pass strength category.",
            sources=(STRENGTH,),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneHeartSimpleRaiseRule:
    rule_id: str = "sayc.response.1h.2h"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not _traditional_major_raises(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Traditional major raises are not configured.",
            )
        if not 6 <= context.evaluation.hcp <= 9:
            return RuleDecision.not_applicable(self.rule_id, "Requires 6–9 HCP.")
        if context.evaluation.length(Suit.HEARTS) < 3:
            return RuleDecision.not_applicable(
                self.rule_id, "Requires three or more hearts of support."
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2H"),
            explanation=(
                "Supporting opener is the highest priority. The source defines "
                "a simple raise as approximately 6–9 HCP with three- or "
                "four-card support."
            ),
            sources=(PRIORITIES, SIMPLE_RAISE, SAYC),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneHeartLimitRaiseRule:
    rule_id: str = "sayc.response.1h.3h"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not _traditional_major_raises(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Traditional major raises are not configured.",
            )
        if not 10 <= context.evaluation.hcp <= 12:
            return RuleDecision.not_applicable(self.rule_id, "Requires 10–12 HCP.")
        if context.evaluation.length(Suit.HEARTS) < 4:
            return RuleDecision.not_applicable(
                self.rule_id, "Requires four or more hearts of support."
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("3H"),
            explanation=(
                "The source defines the traditional limit raise as "
                "approximately 10–12 HCP, four-card support, invitational."
            ),
            sources=(PRIORITIES, LIMIT_RAISE, SAYC),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycResponseToOneHeartOneSpadeRule:
    rule_id: str = "sayc.response.1h.1s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _gate(context, self.rule_id)
        if gate is not None:
            return gate
        if context.evaluation.hcp < 6:
            return RuleDecision.not_applicable(self.rule_id, "Requires at least 6 HCP.")
        if context.evaluation.length(Suit.SPADES) < 4:
            return RuleDecision.not_applicable(
                self.rule_id, "Requires four or more spades."
            )
        if context.evaluation.length(Suit.HEARTS) >= 3:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Source gives support priority; controlled 1♠ is limited to hands "
                "without the three-card heart support used by the simple raise.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1S"),
            explanation=(
                "After 1♥ the source explicitly allows 1♠ with four or more "
                "spades and at least 6 HCP. This controlled rule also enforces "
                "the source's support-first priority."
            ),
            sources=(PRIORITIES, OTHER_MAJOR, SAYC),
            priority=80,
        )


def sayc_one_heart_response_rules():
    return (
        SaycResponseToOneHeartPassRule(),
        SaycResponseToOneHeartSimpleRaiseRule(),
        SaycResponseToOneHeartLimitRaiseRule(),
        SaycResponseToOneHeartOneSpadeRule(),
    )


def create_sayc_one_heart_response_engine() -> BiddingEngine:
    return BiddingEngine(sayc_one_heart_response_rules())
