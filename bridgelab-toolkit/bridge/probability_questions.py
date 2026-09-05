"""Immutable explicit questions for the probability-engine boundary."""

from __future__ import annotations

from dataclasses import dataclass

from .declarer_play_state import PlayedCard
from .models import Card, Seat, Suit


@dataclass(frozen=True, slots=True)
class ProbabilityQuestion:
    subject: str

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("probability question subject must not be blank")


@dataclass(frozen=True, slots=True)
class KnownCardCountQuestion(ProbabilityQuestion):
    subject: str = "declarer-visible card accounting"


@dataclass(frozen=True, slots=True)
class RestrictedChoiceQuestion(ProbabilityQuestion):
    subject_suit: Suit
    observed_play: tuple[PlayedCard, ...] = ()
    known_cards: frozenset[Card] = frozenset()


@dataclass(frozen=True, slots=True)
class VacantPlacesQuestion(ProbabilityQuestion):
    subject_suit: Suit
    known_seat_constraints: tuple[tuple[Seat, int], ...] = ()


@dataclass(frozen=True, slots=True)
class SuitDistributionQuestion(ProbabilityQuestion):
    subject_suit: Suit
    cards_outstanding: int
    candidate_distributions: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class TrumpBreakQuestion(ProbabilityQuestion):
    subject_suit: Suit
    cards_outstanding: int
    candidate_distributions: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class MonteCarloQuestion(ProbabilityQuestion):
    seed: int | None = None
    trials: int | None = None
