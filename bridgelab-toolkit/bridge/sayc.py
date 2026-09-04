"""Small, source-grounded SAYC rule set for BridgeLab Phase 5F.

This module is intentionally conservative.  It implements only clear opening
positions explicitly supported by the canonical BridgeLab SAYC/natural-opening
articles.  Ambiguous partnership-agreement cases deliberately return
``not_applicable`` rather than silently inventing a treatment.

Implemented subset:

* 1NT with 15–17 HCP and a canonical balanced shape, excluding five-card-major
  cases because the knowledge base explicitly says partnerships must agree how
  to treat those hands.
* 1♥ / 1♠ with 12–21 HCP, at least five cards, and a strictly longer major.
* 1♣ / 1♦ with 12–21 HCP using clear Better-Minor cases after excluding the
  implemented 1NT and five-card-major cases.

No response, rebid, competitive, preemptive, or strong-opening logic is
implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Call, CallType
from .bidding_engine import BiddingEngine
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Suit


_SAYC_NAMES = {
    "sayc",
    "standard american yellow card",
}

_SAYC_OPENING_REQUIREMENTS = KnowledgeSource(
    "bidding/systems/sayc",
    "Opening Bid Requirements",
)
_SAYC_FIVE_CARD_MAJORS = KnowledgeSource(
    "bidding/systems/sayc",
    "Five-Card Majors",
)
_SAYC_BETTER_MINOR = KnowledgeSource(
    "bidding/systems/sayc",
    "Better Minor",
)
_NOTRUMP_REQUIREMENTS = KnowledgeSource(
    "bidding/natural-bids/opening-bids/1nt-opening",
    "Typical Requirements",
)
_NOTRUMP_BALANCED = KnowledgeSource(
    "bidding/natural-bids/opening-bids/1nt-opening",
    "Balanced Distribution",
)
_HEART_LENGTH = KnowledgeSource(
    "bidding/natural-bids/opening-bids/1-heart",
    "Heart Length",
)
_SPADE_LENGTH = KnowledgeSource(
    "bidding/natural-bids/opening-bids/1-spade",
    "Spade Length",
)


def _is_sayc(context: BiddingContext) -> bool:
    return context.system.system.casefold() in _SAYC_NAMES


def _is_unopened(context: BiddingContext) -> bool:
    """True when no player has yet made a non-pass call."""
    return all(entry.call.kind is CallType.PASS for entry in context.auction.entries)


def _standard_gate(context: BiddingContext, rule_id: str) -> RuleDecision | None:
    if not _is_sayc(context):
        return RuleDecision.not_applicable(rule_id, "Rule is defined only for SAYC.")
    if not _is_unopened(context):
        return RuleDecision.not_applicable(
            rule_id,
            "This Phase 5F rule applies only while the auction is unopened.",
        )
    return None


def _has_five_card_major(context: BiddingContext) -> bool:
    return (
        context.evaluation.length(Suit.HEARTS) >= 5
        or context.evaluation.length(Suit.SPADES) >= 5
    )


def _clear_strong_two_club(context: BiddingContext) -> bool:
    """Objective HCP-only subset of the SAYC strong 2C opening."""
    return context.evaluation.hcp >= 22


def _clear_two_notrump(context: BiddingContext) -> bool:
    return 20 <= context.evaluation.hcp <= 21 and context.evaluation.is_balanced


def _clear_one_notrump(context: BiddingContext) -> bool:
    """Conservative 1NT predicate for the initial controlled subset."""
    evaluation = context.evaluation
    return (
        15 <= evaluation.hcp <= 17
        and evaluation.is_balanced
        and not _has_five_card_major(context)
    )


@dataclass(frozen=True, slots=True)
class SaycOneNotrumpOpeningRule:
    rule_id: str = "sayc.opening.1nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


        if not _clear_one_notrump(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 15–17 HCP, a canonical balanced shape, "
                "and no five-card major.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1NT"),
            explanation=(
                "SAYC defines 1NT as 15–17 HCP with balanced distribution. "
                "This controlled rule excludes five-card-major hands because the "
                "BridgeLab 1NT article identifies their treatment as a partnership "
                "agreement."
            ),
            sources=(
                _SAYC_OPENING_REQUIREMENTS,
                _NOTRUMP_REQUIREMENTS,
                _NOTRUMP_BALANCED,
            ),
            priority=100,
        )


@dataclass(frozen=True, slots=True)
class SaycOneHeartOpeningRule:
    rule_id: str = "sayc.opening.1h"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_two_notrump(context):
            return RuleDecision.not_applicable(self.rule_id, "20–21 balanced is reserved for the SAYC 2NT opening.")
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


        hcp = context.evaluation.hcp
        hearts = context.evaluation.length(Suit.HEARTS)
        spades = context.evaluation.length(Suit.SPADES)

        if not (12 <= hcp <= 21 and hearts >= 5 and hearts > spades):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 12–21 HCP, at least five hearts, "
                "and hearts strictly longer than spades.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1H"),
            explanation=(
                "SAYC uses five-card majors. With opening values and hearts "
                "strictly longer than spades, the controlled subset opens 1♥."
            ),
            sources=(
                _SAYC_OPENING_REQUIREMENTS,
                _SAYC_FIVE_CARD_MAJORS,
                _HEART_LENGTH,
            ),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycOneSpadeOpeningRule:
    rule_id: str = "sayc.opening.1s"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_two_notrump(context):
            return RuleDecision.not_applicable(self.rule_id, "20–21 balanced is reserved for the SAYC 2NT opening.")
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


        hcp = context.evaluation.hcp
        spades = context.evaluation.length(Suit.SPADES)
        hearts = context.evaluation.length(Suit.HEARTS)

        if not (12 <= hcp <= 21 and spades >= 5 and spades > hearts):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires 12–21 HCP, at least five spades, "
                "and spades strictly longer than hearts.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1S"),
            explanation=(
                "SAYC uses five-card majors. With opening values and spades "
                "strictly longer than hearts, the controlled subset opens 1♠."
            ),
            sources=(
                _SAYC_OPENING_REQUIREMENTS,
                _SAYC_FIVE_CARD_MAJORS,
                _SPADE_LENGTH,
            ),
            priority=90,
        )


@dataclass(frozen=True, slots=True)
class SaycOneClubOpeningRule:
    rule_id: str = "sayc.opening.1c"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_two_notrump(context):
            return RuleDecision.not_applicable(self.rule_id, "20–21 balanced is reserved for the SAYC 2NT opening.")
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


        if not 12 <= context.evaluation.hcp <= 21:
            return RuleDecision.not_applicable(self.rule_id, "Requires 12–21 HCP.")
        if _clear_one_notrump(context) or _has_five_card_major(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "A higher-priority implemented SAYC opening family applies.",
            )

        clubs = context.evaluation.length(Suit.CLUBS)
        diamonds = context.evaluation.length(Suit.DIAMONDS)

        clear_club = (
            (clubs > diamonds and clubs >= 3)
            or (clubs == 3 and diamonds == 3)
        )
        if not clear_club:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled Better-Minor subset has no unambiguous 1♣ case.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1C"),
            explanation=(
                "SAYC uses Better Minor. The controlled subset opens the longer "
                "club suit, and with equal 3–3 minors opens 1♣."
            ),
            sources=(
                _SAYC_OPENING_REQUIREMENTS,
                _SAYC_BETTER_MINOR,
            ),
            priority=80,
        )


@dataclass(frozen=True, slots=True)
class SaycOneDiamondOpeningRule:
    rule_id: str = "sayc.opening.1d"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_two_notrump(context):
            return RuleDecision.not_applicable(self.rule_id, "20–21 balanced is reserved for the SAYC 2NT opening.")
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


        if not 12 <= context.evaluation.hcp <= 21:
            return RuleDecision.not_applicable(self.rule_id, "Requires 12–21 HCP.")
        if _clear_one_notrump(context) or _has_five_card_major(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "A higher-priority implemented SAYC opening family applies.",
            )

        clubs = context.evaluation.length(Suit.CLUBS)
        diamonds = context.evaluation.length(Suit.DIAMONDS)

        clear_diamond = (
            (diamonds > clubs and diamonds >= 3)
            or (diamonds == 4 and clubs == 4)
        )
        if not clear_diamond:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled Better-Minor subset has no unambiguous 1♦ case.",
            )

        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("1D"),
            explanation=(
                "SAYC uses Better Minor. The controlled subset opens the longer "
                "diamond suit, and with equal 4–4 minors opens 1♦."
            ),
            sources=(
                _SAYC_OPENING_REQUIREMENTS,
                _SAYC_BETTER_MINOR,
            ),
            priority=80,
        )




_STRONG_TWO_CLUB = KnowledgeSource(
    "bidding/systems/sayc",
    "Strong 2♣ Opening",
)

@dataclass(frozen=True, slots=True)
class SaycStrongTwoClubOpeningRule:
    rule_id: str = "sayc.opening.2c"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "Conservative source-safe subset requires 22+ HCP; the 9+ playing-tricks branch is not evaluated.",
            )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2C"),
            priority=130,
            explanation=(
                "SAYC strong 2♣ is artificial and usually 22+ HCP or 9+ playing tricks. "
                "This conservative rule implements only the objective 22+ HCP branch."
            ),
            sources=(_SAYC_OPENING_REQUIREMENTS, _STRONG_TWO_CLUB),
        )


_SAYC_TWO_NOTRUMP = KnowledgeSource(
    "bidding/systems/sayc",
    "2NT Opening",
)

@dataclass(frozen=True, slots=True)
class SaycTwoNotrumpOpeningRule:
    rule_id: str = "sayc.opening.2nt"

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if not (20 <= context.evaluation.hcp <= 21 and context.evaluation.is_balanced):
            return RuleDecision.not_applicable(
                self.rule_id,
                "SAYC 2NT opening requires 20–21 HCP and balanced distribution.",
            )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse("2NT"),
            priority=120,
            explanation="SAYC 2NT opening: 20–21 HCP, balanced.",
            sources=(_SAYC_TWO_NOTRUMP,),
        )
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )


_WEAK_TWO = KnowledgeSource("bidding/systems/sayc", "Weak Two Openings")

@dataclass(frozen=True, slots=True)
class SaycWeakTwoOpeningRule:
    suit: Suit
    call_text: str
    rule_id: str

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate=_standard_gate(context,self.rule_id)
        if gate is not None:return gate
        if not 6 <= context.evaluation.hcp <= 10:
            return RuleDecision.not_applicable(self.rule_id,"Weak Two source range is 6–10 HCP.")
        if context.evaluation.length(self.suit) != 6:
            return RuleDecision.not_applicable(self.rule_id,"Controlled Weak Two slice requires exactly six cards in the bid suit.")
        qualifying=sum(context.evaluation.length(x)==6 for x in (Suit.DIAMONDS,Suit.HEARTS,Suit.SPADES))
        if qualifying != 1:
            return RuleDecision.not_applicable(self.rule_id,"Frozen source gives no tie-break when multiple Weak Two suits qualify.")
        if any(context.evaluation.length(x) == 7 for x in (Suit.CLUBS,Suit.DIAMONDS,Suit.HEARTS,Suit.SPADES)):
            return RuleDecision.not_applicable(
                self.rule_id,
                "A seven-card suit also fits the controlled three-level preempt shape; frozen source gives no precedence rule.",
            )
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse(self.call_text),priority=110,
          explanation="SAYC Weak Two opening: six-card suit, 6–10 HCP, preemptive; ambiguous multi-suit cases are excluded.",
          sources=(_WEAK_TWO,))
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )



_THREE_LEVEL_PREEMPT = KnowledgeSource(
    "bidding/systems/sayc",
    "Three-Level Openings",
)

@dataclass(frozen=True, slots=True)
class SaycThreeLevelPreemptOpeningRule:
    suit: Suit
    call_text: str
    rule_id: str

    def evaluate(self, context: BiddingContext) -> RuleDecision:
        gate = _standard_gate(context, self.rule_id)
        if gate is not None:
            return gate
        if _clear_strong_two_club(context):
            return RuleDecision.not_applicable(
                self.rule_id,
                "22+ HCP is reserved for the conservative SAYC strong 2C opening.",
            )
        if not 6 <= context.evaluation.hcp <= 10:
            return RuleDecision.not_applicable(
                self.rule_id,
                "The frozen SAYC opening table gives 6–10 HCP for three-level preempts.",
            )
        if context.evaluation.length(self.suit) != 7:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Controlled subset requires exactly seven cards in the preempt suit.",
            )
        qualifying = sum(
            context.evaluation.length(x) == 7
            for x in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES)
        )
        if qualifying != 1:
            return RuleDecision.not_applicable(
                self.rule_id,
                "Frozen source gives no tie-break when multiple seven-card suits qualify.",
            )
        weak_two_overlap = sum(
            context.evaluation.length(x) == 6
            for x in (Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES)
        )
        if weak_two_overlap:
            return RuleDecision.not_applicable(
                self.rule_id,
                "A six-card D/H/S suit also fits the controlled Weak-Two shape; frozen source gives no precedence rule.",
            )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.parse(self.call_text),
            priority=115,
            explanation=(
                "SAYC lists three-level openings as preemptive, 6–10 HCP, and "
                "normally based on a seven-card suit. This conservative rule "
                "implements only the exact seven-card, single-qualifying-suit subset."
            ),
            sources=(_SAYC_OPENING_REQUIREMENTS, _THREE_LEVEL_PREEMPT),
        )

def sayc_opening_rules() -> tuple[
    SaycOneNotrumpOpeningRule,
    SaycStrongTwoClubOpeningRule,
    SaycTwoNotrumpOpeningRule,
    SaycOneHeartOpeningRule,
    SaycOneSpadeOpeningRule,
    SaycOneClubOpeningRule,
    SaycOneDiamondOpeningRule,
    SaycWeakTwoOpeningRule,
    SaycThreeLevelPreemptOpeningRule,
]:
    """Return the fixed Phase 5F controlled SAYC opening registry."""
    return (
        SaycStrongTwoClubOpeningRule(),
        SaycOneNotrumpOpeningRule(),
        SaycTwoNotrumpOpeningRule(),
        SaycOneHeartOpeningRule(),
        SaycOneSpadeOpeningRule(),
        SaycOneClubOpeningRule(),
        SaycOneDiamondOpeningRule(),
        SaycWeakTwoOpeningRule(Suit.SPADES,"2S","sayc.opening.weak2.2s"),
        SaycWeakTwoOpeningRule(Suit.HEARTS,"2H","sayc.opening.weak2.2h"),
        SaycWeakTwoOpeningRule(Suit.DIAMONDS,"2D","sayc.opening.weak2.2d"),
        SaycThreeLevelPreemptOpeningRule(Suit.SPADES,"3S","sayc.opening.preempt3.3s"),
        SaycThreeLevelPreemptOpeningRule(Suit.HEARTS,"3H","sayc.opening.preempt3.3h"),
        SaycThreeLevelPreemptOpeningRule(Suit.DIAMONDS,"3D","sayc.opening.preempt3.3d"),
        SaycThreeLevelPreemptOpeningRule(Suit.CLUBS,"3C","sayc.opening.preempt3.3c"),
    )


def create_sayc_opening_engine() -> BiddingEngine:
    """Construct a bidding engine containing only the Phase 5F SAYC subset."""
    return BiddingEngine(sayc_opening_rules())
