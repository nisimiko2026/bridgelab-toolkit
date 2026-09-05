"""Immutable, strategy-free state for one declarer-play decision."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .auction import Contract
from .models import Card, Seat, Suit, Vulnerability


class DeclarerHandRole(str, Enum):
    DECLARER_HAND = "declarer-hand"
    DUMMY_HAND = "dummy-hand"


class DeclarerStateFailureCode(str, Enum):
    MISSING_CONTRACT = "missing-contract"
    MISSING_DECLARER_SEAT = "missing-declarer-seat"
    MISSING_DECLARER_HAND = "missing-declarer-hand"
    MISSING_DUMMY_HAND = "missing-dummy-hand"
    MISSING_CURRENT_ACTOR = "missing-current-actor"
    MISSING_PLAY_HISTORY = "missing-play-history"
    INVALID_CARD_STATE = "invalid-card-state"


@dataclass(frozen=True, slots=True)
class PlayedCard:
    seat: Seat
    card: Card

    def __post_init__(self) -> None:
        if not isinstance(self.seat, Seat) or not isinstance(self.card, Card):
            raise TypeError("played card requires canonical Seat and Card values")


@dataclass(frozen=True, slots=True)
class Trick:
    leader: Seat
    plays: tuple[PlayedCard, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "plays", tuple(self.plays))
        if not isinstance(self.leader, Seat):
            raise TypeError("trick leader must be Seat")
        if len(self.plays) > 4:
            raise ValueError("a trick cannot contain more than four cards")
        expected = self.leader
        for play in self.plays:
            if play.seat is not expected:
                raise ValueError("trick play order must rotate clockwise from its leader")
            expected = expected.next()
        if len({play.card for play in self.plays}) != len(self.plays):
            raise ValueError("a physical card cannot appear twice in one trick")

    @property
    def led_suit(self) -> Suit | None:
        return None if not self.plays else self.plays[0].card.suit

    @property
    def is_complete(self) -> bool:
        return len(self.plays) == 4

    def winner(self, trump: Suit | None) -> Seat | None:
        if not self.is_complete:
            return None
        led = self.led_suit
        assert led is not None
        eligible_suit = trump if trump is not None and any(p.card.suit is trump for p in self.plays) else led
        return max(
            (play for play in self.plays if play.card.suit is eligible_suit),
            key=lambda play: int(play.card.rank),
        ).seat


def legal_cards(acting_cards: Iterable[Card], current_trick: Trick) -> tuple[Card, ...]:
    """Return every legal card, deterministically, without selecting among them."""
    cards = tuple(sorted(set(acting_cards), reverse=True))
    led = current_trick.led_suit
    following = tuple(card for card in cards if card.suit is led)
    return following if following else cards


@dataclass(frozen=True, slots=True)
class DeclarerPlayInput:
    contract: Contract | None = None
    declarer_seat: Seat | None = None
    declarer_cards: frozenset[Card] | None = None
    dummy_cards: frozenset[Card] | None = None
    current_actor: Seat | None = None
    completed_tricks: tuple[Trick, ...] | None = None
    current_trick: Trick | None = None
    vulnerability: Vulnerability | None = None
    opening_leader: Seat | None = None


@dataclass(frozen=True, slots=True)
class DeclarerPlayState:
    contract: Contract
    declarer_cards: frozenset[Card]
    dummy_cards: frozenset[Card]
    current_actor: Seat
    completed_tricks: tuple[Trick, ...]
    current_trick: Trick
    vulnerability: Vulnerability | None = None
    opening_leader: Seat | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "declarer_cards", frozenset(self.declarer_cards))
        object.__setattr__(self, "dummy_cards", frozenset(self.dummy_cards))
        object.__setattr__(self, "completed_tricks", tuple(self.completed_tricks))
        if self.current_actor not in {self.declarer, self.dummy}:
            raise ValueError("current actor must be declarer or dummy")
        if any(not trick.is_complete for trick in self.completed_tricks):
            raise ValueError("completed play history may contain only complete tricks")
        if self.current_trick.plays:
            expected = self.current_trick.leader
            for _ in self.current_trick.plays:
                expected = expected.next()
            if self.current_actor is not expected:
                raise ValueError("current actor is inconsistent with current trick order")
        elif self.current_actor is not self.current_trick.leader:
            raise ValueError("current actor must lead an empty current trick")
        visible = self.declarer_cards | self.dummy_cards
        if len(visible) != len(self.declarer_cards) + len(self.dummy_cards):
            raise ValueError("declarer and dummy holdings contain a duplicate card")
        played = tuple(play.card for trick in (*self.completed_tricks, self.current_trick) for play in trick.plays)
        if len(played) != len(set(played)):
            raise ValueError("play history contains a duplicate physical card")
        if visible.intersection(played):
            raise ValueError("played cards cannot remain in visible holdings")

    @property
    def declarer(self) -> Seat:
        return self.contract.declarer

    @property
    def dummy(self) -> Seat:
        return self.declarer.partner()

    @property
    def acting_role(self) -> DeclarerHandRole:
        return DeclarerHandRole.DECLARER_HAND if self.current_actor is self.declarer else DeclarerHandRole.DUMMY_HAND

    @property
    def acting_cards(self) -> frozenset[Card]:
        return self.declarer_cards if self.acting_role is DeclarerHandRole.DECLARER_HAND else self.dummy_cards

    @property
    def legal_actions(self) -> tuple[Card, ...]:
        return legal_cards(self.acting_cards, self.current_trick)

    @property
    def trick_number(self) -> int:
        return len(self.completed_tricks) + 1

    @property
    def visible_cards(self) -> frozenset[Card]:
        return self.declarer_cards | self.dummy_cards

    @property
    def played_cards(self) -> frozenset[Card]:
        return frozenset(play.card for trick in (*self.completed_tricks, self.current_trick) for play in trick.plays)

    @property
    def unknown_card_count(self) -> int:
        return 52 - len(self.visible_cards | self.played_cards)

    @property
    def follow_suit_required(self) -> bool:
        led = self.current_trick.led_suit
        return led is not None and any(card.suit is led for card in self.acting_cards)

    @property
    def declarer_tricks(self) -> int:
        trump = self.contract.bid.strain.suit
        return sum(trick.winner(trump) in {self.declarer, self.dummy} for trick in self.completed_tricks)

    @property
    def defender_tricks(self) -> int:
        return len(self.completed_tricks) - self.declarer_tricks


@dataclass(frozen=True, slots=True)
class DeclarerStateBuildResult:
    state: DeclarerPlayState | None
    failure_code: DeclarerStateFailureCode | None = None
    explanation: str = ""

    @property
    def is_ready(self) -> bool:
        return self.state is not None


def build_declarer_play_state(source: DeclarerPlayInput | None) -> DeclarerStateBuildResult:
    if source is None or source.contract is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_CONTRACT, "Declarer contract is missing.")
    if source.declarer_seat is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_DECLARER_SEAT, "Declarer seat is missing.")
    if source.declarer_seat is not source.contract.declarer:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.INVALID_CARD_STATE, "Declarer seat conflicts with contract.")
    if source.declarer_cards is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_DECLARER_HAND, "Declarer hand is missing.")
    if source.dummy_cards is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_DUMMY_HAND, "Dummy hand is missing.")
    if source.current_actor is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_CURRENT_ACTOR, "Current actor is missing.")
    if source.completed_tricks is None or source.current_trick is None:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.MISSING_PLAY_HISTORY, "Play history is missing.")
    try:
        state = DeclarerPlayState(
            source.contract, source.declarer_cards, source.dummy_cards, source.current_actor,
            source.completed_tricks, source.current_trick, source.vulnerability, source.opening_leader,
        )
    except (TypeError, ValueError) as exc:
        return DeclarerStateBuildResult(None, DeclarerStateFailureCode.INVALID_CARD_STATE, str(exc))
    return DeclarerStateBuildResult(state)
