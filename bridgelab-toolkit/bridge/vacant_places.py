"""Exact, oriented vacant-place probabilities for two defenders.

This is an offline general calculator over the existing typed probability
question. It does not register a new production probability route.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb

from .models import Seat, Suit
from .probability_questions import VacantPlacesQuestion
from .probability_values import ProbabilityValue


@dataclass(frozen=True, slots=True)
class OrientedTrumpBreak:
    first_defender: Seat
    first_trumps: int
    second_defender: Seat
    second_trumps: int
    probability: ProbabilityValue


def oriented_trump_break(
    question: VacantPlacesQuestion,
    outstanding_trumps: int,
    *,
    side_suit: Suit | None = None,
    side_length_mixture: tuple[tuple[int, int, ProbabilityValue], ...] | None = None,
) -> tuple[OrientedTrumpBreak, ...]:
    """Condition on exact or probabilistic oriented side-suit lengths.

    Mixture entries are (first-defender length, second-defender length, weight).
    A statement such as 5+ must be represented by a distribution across all
    plausible lengths; it is never coerced to an exact length of five.
    """
    if not isinstance(question, VacantPlacesQuestion):
        raise TypeError("typed vacant-places question required")
    if not isinstance(outstanding_trumps, int) or isinstance(outstanding_trumps, bool) or not 0 <= outstanding_trumps <= 13:
        raise ValueError("outstanding trumps must be in 0..13")
    if (side_suit is None) != (side_length_mixture is None):
        raise ValueError("side suit and length mixture must be supplied together")
    if side_suit is not None and (not isinstance(side_suit, Suit) or side_suit is question.subject_suit):
        raise ValueError("conditioning side suit must differ from trump")
    first, second = question.defenders
    known_target = dict(question.known_target_suit_counts)
    known_all = dict(question.known_card_counts)
    unknown_trumps = outstanding_trumps - known_target[first] - known_target[second]
    if unknown_trumps < 0:
        raise ValueError("known defender trumps exceed outstanding count")
    if side_length_mixture is None:
        components: tuple[tuple[int | None, int | None, ProbabilityValue], ...] = (
            (None, None, ProbabilityValue(1, 1)),)
    else:
        if not side_length_mixture:
            raise ValueError("mixture needs at least one component")
        components = side_length_mixture
        if sum((weight.as_fraction() for _, _, weight in components), Fraction()) != 1:
            raise ValueError("mixture weights must sum to one")
    probabilities = [Fraction() for _ in range(outstanding_trumps + 1)]
    for length_first, length_second, weight in components:
        slots = []
        for defender, length in ((first, length_first), (second, length_second)):
            extra_known = 0
            if length is not None:
                if not isinstance(length, int) or isinstance(length, bool) or not 0 <= length <= 13:
                    raise ValueError("side-suit length must be in 0..13")
                already_known = sum(fact.seat is defender and fact.card.suit is side_suit
                                    for fact in question.public_card_ownership)
                if length < already_known:
                    raise ValueError("side length contradicts public ownership")
                extra_known = length - already_known
            vacant = 13 - known_all[defender] - extra_known
            if vacant < 0:
                raise ValueError("known cards exceed defender capacity")
            slots.append(vacant)
        total_vacant = sum(slots)
        if unknown_trumps > total_vacant:
            raise ValueError("insufficient vacant places for outstanding trumps")
        denominator = comb(total_vacant, unknown_trumps)
        for unknown_first in range(unknown_trumps + 1):
            unknown_second = unknown_trumps - unknown_first
            if unknown_first > slots[0] or unknown_second > slots[1]:
                continue
            total_first = known_target[first] + unknown_first
            probabilities[total_first] += weight.as_fraction() * Fraction(
                comb(slots[0], unknown_first) * comb(slots[1], unknown_second), denominator)
    return tuple(OrientedTrumpBreak(first, first_count, second,
                                     outstanding_trumps - first_count,
                                     ProbabilityValue(value.numerator, value.denominator))
                 for first_count, value in enumerate(probabilities))
