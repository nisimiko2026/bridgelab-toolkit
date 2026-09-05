"""First narrow, source-grounded declarer recommendation engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Strain
from .bidding_rules import KnowledgeSource
from .declarer_play_state import DeclarerHandRole, DeclarerPlayState
from .models import Card, Rank, Suit


UNBLOCK_SOURCE = KnowledgeSource(
    "play/declarer-play/general-techniques/unblock",
    "Example 1 – Simple Unblock",
)


class DeclarerTechnique(str, Enum):
    SIMPLE_UNBLOCK_KING = "simple-unblock-king"


class DeclarerRecommendationStatus(str, Enum):
    RECOMMENDATION = "recommendation"
    NO_DECISION = "no-decision"


class DeclarerRecommendationReason(str, Enum):
    TECHNIQUE_NOT_APPLICABLE = "technique-not-applicable"
    AMBIGUOUS_ACTION = "ambiguous-action"
    ILLEGAL_ACTION = "illegal-action"


@dataclass(frozen=True, slots=True)
class DeclarerRecommendation:
    status: DeclarerRecommendationStatus
    card: Card | None
    explanation: str
    technique: DeclarerTechnique | None = None
    sources: tuple[KnowledgeSource, ...] = ()
    reason: DeclarerRecommendationReason | None = None
    trace: tuple[tuple[str, str], ...] = ()

    @property
    def has_recommendation(self) -> bool:
        return self.status is DeclarerRecommendationStatus.RECOMMENDATION


def evaluate_declarer_play(state: DeclarerPlayState) -> DeclarerRecommendation:
    """Apply only the frozen-source A-J-T-9 opposite K-Q simple unblock."""
    if (
        state.contract.bid.strain is not Strain.NOTRUMP
        or state.acting_role is not DeclarerHandRole.DECLARER_HAND
        or state.current_trick.plays
    ):
        return _not_applicable()

    matches = []
    for suit in Suit:
        declarer_ranks = {card.rank for card in state.declarer_cards if card.suit is suit}
        dummy_ranks = {card.rank for card in state.dummy_cards if card.suit is suit}
        if declarer_ranks == {Rank.KING, Rank.QUEEN} and dummy_ranks == {
            Rank.ACE, Rank.JACK, Rank.TEN, Rank.NINE,
        }:
            matches.append(Card(suit, Rank.KING))
    if not matches:
        return _not_applicable()
    if len(matches) != 1:
        return DeclarerRecommendation(
            DeclarerRecommendationStatus.NO_DECISION, None,
            "Simple Unblock matches more than one suit, so the exact action is ambiguous.",
            reason=DeclarerRecommendationReason.AMBIGUOUS_ACTION,
            trace=(("matching-suits", str(len(matches))),),
        )
    card = matches[0]
    if card not in state.legal_actions:
        return DeclarerRecommendation(
            DeclarerRecommendationStatus.NO_DECISION, None,
            "Simple Unblock identified a card that is not legal in the current trick.",
            reason=DeclarerRecommendationReason.ILLEGAL_ACTION,
            trace=(("candidate", card.serialize()),),
        )
    explanation = (
        f"Simple Unblock matches {card.suit.letter}: dummy holds A-J-T-9 and declarer holds K-Q; "
        f"the frozen source explicitly cashes {card.serialize()} before the queen to clear the suit."
    )
    return DeclarerRecommendation(
        DeclarerRecommendationStatus.RECOMMENDATION, card, explanation,
        DeclarerTechnique.SIMPLE_UNBLOCK_KING, (UNBLOCK_SOURCE,),
        trace=(("technique", DeclarerTechnique.SIMPLE_UNBLOCK_KING.value), ("card", card.serialize())),
    )


def _not_applicable() -> DeclarerRecommendation:
    return DeclarerRecommendation(
        DeclarerRecommendationStatus.NO_DECISION, None,
        "Simple Unblock is not applicable to this declarer position.",
        reason=DeclarerRecommendationReason.TECHNIQUE_NOT_APPLICABLE,
    )
