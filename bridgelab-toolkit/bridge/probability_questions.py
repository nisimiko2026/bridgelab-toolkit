"""Immutable explicit questions for the probability-engine boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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


class RestrictedChoiceObservationStatus(str, Enum):
    FORCED = "forced"
    OPTIONAL = "optional"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT = "insufficient"


class PublicEvidenceKind(str, Enum):
    PLAYED_CARD = "played-card"
    EXPOSED_CARD = "exposed-card"
    PUBLIC_AUCTION = "public-auction"
    LOGICALLY_ESTABLISHED = "logically-established"


@dataclass(frozen=True, slots=True)
class PublicEvidence:
    kind: PublicEvidenceKind
    observation_index: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PublicEvidenceKind):
            raise TypeError("public evidence kind must be PublicEvidenceKind")
        if self.observation_index is not None and (
            not isinstance(self.observation_index, int)
            or isinstance(self.observation_index, bool)
            or self.observation_index < 0
        ):
            raise ValueError("public evidence observation index must be nonnegative")


@dataclass(frozen=True, slots=True)
class PublicCardOwnership:
    seat: Seat
    card: Card
    evidence: PublicEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.seat, Seat) or not isinstance(self.card, Card):
            raise TypeError("public card ownership requires canonical Seat and Card")
        if not isinstance(self.evidence, PublicEvidence):
            raise TypeError("public card ownership requires typed public evidence")
        if self.evidence.kind is PublicEvidenceKind.PUBLIC_AUCTION:
            raise ValueError("auction evidence cannot establish exact card ownership")


@dataclass(frozen=True, slots=True)
class RestrictedChoiceQuestion(ProbabilityQuestion):
    subject_suit: Suit
    observed_defender: Seat
    observed_play: PlayedCard
    prior_public_plays: tuple[PlayedCard, ...] = ()
    publicly_established_choice_sets: tuple[frozenset[Card], ...] = ()
    choice_basis: tuple[PublicEvidence, ...] = ()
    declarer_seat: Seat | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.subject_suit, Suit):
            raise TypeError("restricted-choice target suit must be Suit")
        if not isinstance(self.observed_defender, Seat):
            raise TypeError("restricted-choice observed defender must be Seat")
        if not isinstance(self.observed_play, PlayedCard):
            raise TypeError("restricted-choice observation must be PlayedCard")
        if self.observed_play.seat is not self.observed_defender:
            raise ValueError("observed play seat must match observed defender")
        if self.observed_play.card.suit is not self.subject_suit:
            raise ValueError("observed card must belong to the target suit")
        if self.declarer_seat is not None:
            if not isinstance(self.declarer_seat, Seat):
                raise TypeError("declarer seat must be Seat when supplied")
            if self.observed_defender in {
                self.declarer_seat,
                self.declarer_seat.partner(),
            }:
                raise ValueError("observed seat must be a defender")
        prior = tuple(self.prior_public_plays)
        if any(not isinstance(play, PlayedCard) for play in prior):
            raise TypeError("prior public play history requires PlayedCard values")
        cards = tuple(play.card for play in prior) + (self.observed_play.card,)
        if len(cards) != len(set(cards)):
            raise ValueError("public observation history contains a duplicate card")
        choice_sets = tuple(frozenset(choices) for choices in self.publicly_established_choice_sets)
        for choices in choice_sets:
            if not choices:
                raise ValueError("an established choice set cannot be empty")
            if any(not isinstance(card, Card) for card in choices):
                raise TypeError("established choices require canonical Card values")
            if any(card.suit is not self.subject_suit for card in choices):
                raise ValueError("established choices must belong to the target suit")
            if self.observed_play.card not in choices:
                raise ValueError("each established choice set must include the observed card")
        basis = tuple(self.choice_basis)
        if any(not isinstance(item, PublicEvidence) for item in basis):
            raise TypeError("choice basis requires typed public evidence")
        if choice_sets and not basis:
            raise ValueError("established choices require a public evidence basis")
        object.__setattr__(self, "prior_public_plays", prior)
        object.__setattr__(self, "publicly_established_choice_sets", choice_sets)
        object.__setattr__(self, "choice_basis", basis)

    @property
    def observation_status(self) -> RestrictedChoiceObservationStatus:
        choices = self.publicly_established_choice_sets
        if not choices:
            return RestrictedChoiceObservationStatus.INSUFFICIENT
        if len(set(choices)) > 1:
            return RestrictedChoiceObservationStatus.AMBIGUOUS
        return (
            RestrictedChoiceObservationStatus.FORCED
            if len(choices[0]) == 1
            else RestrictedChoiceObservationStatus.OPTIONAL
        )


@dataclass(frozen=True, slots=True)
class VacantPlacesQuestion(ProbabilityQuestion):
    subject_suit: Suit
    defenders: tuple[Seat, Seat]
    public_card_ownership: tuple[PublicCardOwnership, ...] = ()
    hand_size_baseline: int = 13
    declarer_seat: Seat | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.subject_suit, Suit):
            raise TypeError("vacant-places target suit must be Suit")
        defenders = tuple(self.defenders)
        if len(defenders) != 2 or any(not isinstance(seat, Seat) for seat in defenders):
            raise TypeError("vacant places requires exactly two canonical defender seats")
        if defenders[0] is defenders[1]:
            raise ValueError("vacant-place defenders must be distinct")
        if self.declarer_seat is not None:
            if not isinstance(self.declarer_seat, Seat):
                raise TypeError("declarer seat must be Seat when supplied")
            if any(
                seat in {self.declarer_seat, self.declarer_seat.partner()}
                for seat in defenders
            ):
                raise ValueError("vacant-place comparison requires two defenders")
        if self.hand_size_baseline != 13:
            raise ValueError("normal bridge hand-size baseline must be 13")
        ownership = tuple(self.public_card_ownership)
        if any(not isinstance(fact, PublicCardOwnership) for fact in ownership):
            raise TypeError("vacant places requires typed public ownership facts")
        if any(fact.seat not in defenders for fact in ownership):
            raise ValueError("ownership fact seat must be a compared defender")
        cards = tuple(fact.card for fact in ownership)
        if len(cards) != len(set(cards)):
            raise ValueError("public ownership facts contain a duplicate physical card")
        for defender in defenders:
            if sum(fact.seat is defender for fact in ownership) > self.hand_size_baseline:
                raise ValueError("public ownership facts exceed legal hand size")
        object.__setattr__(self, "defenders", defenders)
        object.__setattr__(self, "public_card_ownership", ownership)

    @property
    def known_card_counts(self) -> tuple[tuple[Seat, int], ...]:
        return tuple(
            (seat, sum(fact.seat is seat for fact in self.public_card_ownership))
            for seat in self.defenders
        )

    @property
    def remaining_vacant_slots(self) -> tuple[tuple[Seat, int], ...]:
        return tuple(
            (seat, self.hand_size_baseline - count)
            for seat, count in self.known_card_counts
        )

    @property
    def known_target_suit_counts(self) -> tuple[tuple[Seat, int], ...]:
        return tuple(
            (
                seat,
                sum(
                    fact.seat is seat and fact.card.suit is self.subject_suit
                    for fact in self.public_card_ownership
                ),
            )
            for seat in self.defenders
        )


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
