"""Profile-specific two-suited opening policy approved during A9 review.

Scope is deliberately narrow: hands whose two longest suits are 5-5, 6-5, or
6-6.  This module does not replace NT/strong/preempt families outside that
scope and does not silently activate Nisim–Nily as a bidding system.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import Hand, Suit


class OpeningProfile(str, Enum):
    SAYC = "SAYC"
    NISIM_NILY = "nisim-nily"


class OpeningPolicyStatus(str, Enum):
    OPEN = "open"
    PASS = "pass"
    OUT_OF_SCOPE = "out-of-scope"


@dataclass(frozen=True, slots=True)
class TwoSuitedOpeningDecision:
    profile: OpeningProfile
    status: OpeningPolicyStatus
    call: str | None
    hcp: int
    rule20_score: int
    shape: tuple[int, int, int, int]
    seat_number: int
    basis: str


_SUITS = (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)
_CALL = {
    Suit.SPADES: "1S",
    Suit.HEARTS: "1H",
    Suit.DIAMONDS: "1D",
    Suit.CLUBS: "1C",
}
_HCP = {"A": 4, "K": 3, "Q": 2, "J": 1}


def _hcp(hand: Hand) -> int:
    """Objective Milton Work HCP from the core Hand model."""
    return sum(_HCP.get(card.rank.symbol, 0) for card in hand)


def _two_longest(hand: Hand) -> tuple[tuple[Suit, int], tuple[Suit, int]]:
    # _SUITS is high-to-low; stable sorting therefore resolves equal length
    # toward the higher-ranking suit.
    ranked = sorted(
        ((suit, hand.length(suit)) for suit in _SUITS),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0], ranked[1]


def _in_review_scope(hand: Hand) -> bool:
    lengths = sorted(hand.shape, reverse=True)[:2]
    return tuple(lengths) in ((5, 5), (6, 5), (6, 6))


def _major_hcp(hand: Hand) -> int:
    return sum(
        _HCP.get(card.rank.symbol, 0)
        for suit in (Suit.SPADES, Suit.HEARTS)
        for card in hand.cards_in(suit)
    )


def _one_level_longer_or_higher(hand: Hand) -> str:
    (suit, _length), _second = _two_longest(hand)
    return _CALL[suit]


def _rule20(hand: Hand) -> tuple[int, bool]:
    hcp = _hcp(hand)
    lengths = sorted(hand.shape, reverse=True)
    score = hcp + lengths[0] + lengths[1]
    return score, score >= 20


def _late_equal_major_exception(hand: Hand, seat_number: int) -> bool:
    return (
        seat_number in (3, 4)
        and hand.length(Suit.SPADES) == 5
        and hand.length(Suit.HEARTS) == 5
        and _hcp(hand) >= 8
        and _major_hcp(hand) >= 8
    )


def evaluate_two_suited_opening(
    hand: Hand,
    *,
    profile: OpeningProfile,
    seat_number: int,
) -> TwoSuitedOpeningDecision:
    """Apply the approved A9 two-suited opening rules.

    seat_number is 1..4 and represents the opening seat after preceding Passes.
    """
    if seat_number not in (1, 2, 3, 4):
        raise ValueError("seat_number must be 1, 2, 3, or 4")

    hcp = _hcp(hand)
    score, qualifies20 = _rule20(hand)

    if not _in_review_scope(hand):
        return TwoSuitedOpeningDecision(
            profile, OpeningPolicyStatus.OUT_OF_SCOPE, None, hcp, score,
            hand.shape, seat_number,
            "A9 policy is limited to 5-5, 6-5, and 6-6 review hands.",
        )

    if _late_equal_major_exception(hand, seat_number):
        return TwoSuitedOpeningDecision(
            profile, OpeningPolicyStatus.OPEN, "1S", hcp, score,
            hand.shape, seat_number,
            "Third/fourth seat after prior Passes: exactly 5S-5H, at least 8 HCP "
            "total and at least 8 HCP concentrated in the two majors.",
        )

    if profile is OpeningProfile.SAYC:
        if hcp > 10 or qualifies20:
            return TwoSuitedOpeningDecision(
                profile, OpeningPolicyStatus.OPEN, _one_level_longer_or_higher(hand),
                hcp, score, hand.shape, seat_number,
                "SAYC A9 agreement: HCP > 10 opens; otherwise Rule of 20 qualifies. "
                "Open the longer suit, or the higher-ranking suit when equal.",
            )
        return TwoSuitedOpeningDecision(
            profile, OpeningPolicyStatus.PASS, None, hcp, score,
            hand.shape, seat_number,
            "SAYC A9 agreement: no Rule-of-20 qualification and no approved "
            "later-seat 5S-5H exception.",
        )

    # Nisim–Nily
    if hcp > 10:
        return TwoSuitedOpeningDecision(
            profile, OpeningPolicyStatus.OPEN, _one_level_longer_or_higher(hand),
            hcp, score, hand.shape, seat_number,
            "Nisim–Nily: above 10 HCP opens without Rule of 20.",
        )

    if hcp == 10 and qualifies20:
        return TwoSuitedOpeningDecision(
            profile, OpeningPolicyStatus.OPEN, _one_level_longer_or_higher(hand),
            hcp, score, hand.shape, seat_number,
            "Nisim–Nily: 10 HCP plus Rule of 20 opens at the one level.",
        )

    if hcp < 10:
        s = hand.length(Suit.SPADES)
        h = hand.length(Suit.HEARTS)
        d = hand.length(Suit.DIAMONDS)
        c = hand.length(Suit.CLUBS)

        if s >= 5 and max(d, c) >= 5:
            return TwoSuitedOpeningDecision(
                profile, OpeningPolicyStatus.OPEN, "2S", hcp, score,
                hand.shape, seat_number,
                "Existing Nisim–Nily weak two-suited treatment: spades plus a minor.",
            )
        if h >= 5 and max(d, c) >= 5:
            return TwoSuitedOpeningDecision(
                profile, OpeningPolicyStatus.OPEN, "2H", hcp, score,
                hand.shape, seat_number,
                "Existing Nisim–Nily weak two-suited treatment: hearts plus a minor.",
            )
        if d >= 5 and c >= 5:
            return TwoSuitedOpeningDecision(
                profile, OpeningPolicyStatus.OPEN, "2NT", hcp, score,
                hand.shape, seat_number,
                "Existing Nisim–Nily weak two-suited treatment: both minors.",
            )

    return TwoSuitedOpeningDecision(
        profile, OpeningPolicyStatus.PASS, None, hcp, score,
        hand.shape, seat_number,
        "No approved Nisim–Nily opening in this A9 two-suited policy scope.",
    )
