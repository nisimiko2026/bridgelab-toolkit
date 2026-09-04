"""BridgeLab Bridge Engine — objective hand-evaluation facts.

This module intentionally stops short of bidding decisions.  It derives
repeatable facts from a :class:`bridge.models.Hand`: HCP, controls, suit
lengths, distribution, shortage counts, source-defined balanced-shape
classification, and raw honor evidence by suit.

Source conventions reflected here come from the canonical BridgeLab corpus:

* High-card points: A=4, K=3, Q=2, J=1.
* Controls: A=2, K=1.
* Balanced shapes: 4-3-3-3, 4-4-3-2, 5-3-3-2.
* Semi-balanced shapes: 5-4-2-2, 6-3-2-2.

No opening thresholds, system ranges, fit-dependent adjustments, or bid
recommendations belong in this layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import Hand, Rank, Suit


SUIT_ORDER: tuple[Suit, ...] = (
    Suit.SPADES,
    Suit.HEARTS,
    Suit.DIAMONDS,
    Suit.CLUBS,
)

_HCP_BY_RANK = {
    Rank.ACE: 4,
    Rank.KING: 3,
    Rank.QUEEN: 2,
    Rank.JACK: 1,
}

_CONTROLS_BY_RANK = {
    Rank.ACE: 2,
    Rank.KING: 1,
}

_BALANCED_DISTRIBUTIONS = {
    (4, 3, 3, 3),
    (4, 4, 3, 2),
    (5, 3, 3, 2),
}

_SEMI_BALANCED_DISTRIBUTIONS = {
    (5, 4, 2, 2),
    (6, 3, 2, 2),
}


class ShapeClass(Enum):
    BALANCED = "balanced"
    SEMI_BALANCED = "semi-balanced"
    UNBALANCED = "unbalanced"


@dataclass(frozen=True, slots=True)
class SuitHonorEvidence:
    """Objective honor/length facts for one suit.

    This intentionally does **not** classify a holding as a "stopper".
    The canonical BridgeLab knowledge says stopper quality matters, including
    partial and double stoppers, but does not define a universal card-pattern
    rule.  Keeping the evidence raw prevents the hand evaluator from silently
    importing a bidding convention.
    """

    suit: Suit
    length: int
    honors: tuple[Rank, ...]

    @property
    def has_ace(self) -> bool:
        return Rank.ACE in self.honors

    @property
    def has_king(self) -> bool:
        return Rank.KING in self.honors

    @property
    def has_queen(self) -> bool:
        return Rank.QUEEN in self.honors

    @property
    def has_jack(self) -> bool:
        return Rank.JACK in self.honors

    @property
    def has_ten(self) -> bool:
        return Rank.TEN in self.honors

    @property
    def honor_count(self) -> int:
        return len(self.honors)



@dataclass(frozen=True, slots=True)
class SuitQualityEvidence:
    """Objective rank-pattern evidence for one suit.

    This is deliberately **not** a quality verdict.  It records only facts that
    later system/convention policies may interpret: suit length, all ranks,
    T/J/Q/K/A honors, the highest card, and consecutive rank runs.

    A sequence run is a maximal descending run of consecutive ranks of length
    at least two, for example ``A-K-Q`` or ``J-T-9``.
    """

    suit: Suit
    length: int
    ranks: tuple[Rank, ...]
    honors: tuple[Rank, ...]
    sequences: tuple[tuple[Rank, ...], ...]

    @property
    def honor_count(self) -> int:
        return len(self.honors)

    @property
    def top_honor_count(self) -> int:
        return sum(rank >= Rank.QUEEN for rank in self.honors)

    @property
    def top_rank(self) -> Rank | None:
        return self.ranks[0] if self.ranks else None

    @property
    def longest_sequence_length(self) -> int:
        return max((len(sequence) for sequence in self.sequences), default=0)


@dataclass(frozen=True, slots=True)
class HandEvaluation:
    """Immutable, system-neutral facts derived from one bridge hand."""

    hcp: int
    controls: int
    suit_lengths: tuple[int, int, int, int]
    distribution: tuple[int, int, int, int]
    shape_class: ShapeClass
    voids: int
    singletons: int
    doubletons: int
    longest_length: int
    longest_suits: tuple[Suit, ...]
    suit_honor_evidence: tuple[SuitHonorEvidence, ...]
    suit_quality_evidence: tuple[SuitQualityEvidence, ...]

    def length(self, suit: Suit) -> int:
        """Return the stored suit length for ``suit``."""
        if not isinstance(suit, Suit):
            raise TypeError("suit must be Suit")
        return self.suit_lengths[SUIT_ORDER.index(suit)]

    def honor_evidence(self, suit: Suit) -> SuitHonorEvidence:
        """Return objective length/honor evidence for ``suit``."""
        if not isinstance(suit, Suit):
            raise TypeError("suit must be Suit")
        return self.suit_honor_evidence[SUIT_ORDER.index(suit)]

    def quality_evidence(self, suit: Suit) -> SuitQualityEvidence:
        """Return raw rank-pattern evidence for ``suit``."""
        if not isinstance(suit, Suit):
            raise TypeError("suit must be Suit")
        return self.suit_quality_evidence[SUIT_ORDER.index(suit)]

    @property
    def is_balanced(self) -> bool:
        return self.shape_class is ShapeClass.BALANCED

    @property
    def is_semi_balanced(self) -> bool:
        return self.shape_class is ShapeClass.SEMI_BALANCED

    @property
    def is_unbalanced(self) -> bool:
        return self.shape_class is ShapeClass.UNBALANCED

    @property
    def has_void(self) -> bool:
        return self.voids > 0

    @property
    def has_singleton(self) -> bool:
        return self.singletons > 0


def high_card_points(hand: Hand) -> int:
    """Count standard Milton Work high-card points: A=4, K=3, Q=2, J=1."""
    _require_hand(hand)
    return sum(_HCP_BY_RANK.get(card.rank, 0) for card in hand.cards)


def controls(hand: Hand) -> int:
    """Count ace/king controls: ace=2, king=1."""
    _require_hand(hand)
    return sum(_CONTROLS_BY_RANK.get(card.rank, 0) for card in hand.cards)


def suit_lengths(hand: Hand) -> tuple[int, int, int, int]:
    """Return suit lengths in canonical S.H.D.C order."""
    _require_hand(hand)
    return tuple(hand.length(suit) for suit in SUIT_ORDER)


def distribution(hand: Hand) -> tuple[int, int, int, int]:
    """Return suit lengths sorted from longest to shortest."""
    return tuple(sorted(suit_lengths(hand), reverse=True))


def suit_honor_evidence(hand: Hand, suit: Suit) -> SuitHonorEvidence:
    """Return raw T/J/Q/K/A evidence for one suit.

    No stopper interpretation is made here.
    """
    _require_hand(hand)
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    honors = tuple(
        sorted(
            (
                card.rank
                for card in hand.cards
                if card.suit is suit and card.rank >= Rank.TEN
            ),
            reverse=True,
        )
    )
    return SuitHonorEvidence(
        suit=suit,
        length=hand.length(suit),
        honors=honors,
    )


def all_suit_honor_evidence(hand: Hand) -> tuple[SuitHonorEvidence, ...]:
    """Return raw honor evidence in canonical S.H.D.C order."""
    _require_hand(hand)
    return tuple(suit_honor_evidence(hand, suit) for suit in SUIT_ORDER)



def suit_quality_evidence(hand: Hand, suit: Suit) -> SuitQualityEvidence:
    """Return raw rank-pattern evidence for one suit.

    No label such as "good", "strong", "solid", or "biddable" is assigned.
    """
    _require_hand(hand)
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    ranks = tuple(
        sorted(
            (card.rank for card in hand.cards if card.suit is suit),
            reverse=True,
        )
    )
    honors = tuple(rank for rank in ranks if rank >= Rank.TEN)

    sequences: list[tuple[Rank, ...]] = []
    if ranks:
        run = [ranks[0]]
        for rank in ranks[1:]:
            if int(run[-1]) - int(rank) == 1:
                run.append(rank)
            else:
                if len(run) >= 2:
                    sequences.append(tuple(run))
                run = [rank]
        if len(run) >= 2:
            sequences.append(tuple(run))

    return SuitQualityEvidence(
        suit=suit,
        length=len(ranks),
        ranks=ranks,
        honors=honors,
        sequences=tuple(sequences),
    )


def all_suit_quality_evidence(hand: Hand) -> tuple[SuitQualityEvidence, ...]:
    """Return rank-pattern evidence in canonical S.H.D.C order."""
    _require_hand(hand)
    return tuple(suit_quality_evidence(hand, suit) for suit in SUIT_ORDER)


def classify_shape(hand: Hand) -> ShapeClass:
    """Classify the hand using the BridgeLab corpus shape vocabulary."""
    shape = distribution(hand)
    if shape in _BALANCED_DISTRIBUTIONS:
        return ShapeClass.BALANCED
    if shape in _SEMI_BALANCED_DISTRIBUTIONS:
        return ShapeClass.SEMI_BALANCED
    return ShapeClass.UNBALANCED


def evaluate_hand(hand: Hand) -> HandEvaluation:
    """Derive all current system-neutral evaluation facts in one pass."""
    _require_hand(hand)
    lengths = suit_lengths(hand)
    dist = tuple(sorted(lengths, reverse=True))
    longest = max(lengths)
    longest_suits = tuple(
        suit for suit, length in zip(SUIT_ORDER, lengths) if length == longest
    )

    return HandEvaluation(
        hcp=high_card_points(hand),
        controls=controls(hand),
        suit_lengths=lengths,
        distribution=dist,
        shape_class=(
            ShapeClass.BALANCED
            if dist in _BALANCED_DISTRIBUTIONS
            else ShapeClass.SEMI_BALANCED
            if dist in _SEMI_BALANCED_DISTRIBUTIONS
            else ShapeClass.UNBALANCED
        ),
        voids=sum(length == 0 for length in lengths),
        singletons=sum(length == 1 for length in lengths),
        doubletons=sum(length == 2 for length in lengths),
        longest_length=longest,
        longest_suits=longest_suits,
        suit_honor_evidence=all_suit_honor_evidence(hand),
        suit_quality_evidence=all_suit_quality_evidence(hand),
    )


def _require_hand(hand: Hand) -> None:
    if not isinstance(hand, Hand):
        raise TypeError("hand must be Hand")
