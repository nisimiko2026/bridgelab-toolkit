"""Immutable, imperfect-information state for one defensive play decision."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Contract
from .declarer_play_state import Trick, legal_cards
from .models import Card, Seat, Vulnerability
from .probability_engine import ProbabilityContext


class DefensiveStateFailureCode(str, Enum):
    MISSING_CONTRACT = "missing-contract"
    MISSING_DECLARER_SEAT = "missing-declarer-seat"
    MISSING_DEFENDER_HAND = "missing-defender-hand"
    MISSING_DUMMY_HAND = "missing-dummy-hand"
    MISSING_CURRENT_ACTOR = "missing-current-actor"
    MISSING_PLAY_HISTORY = "missing-play-history"
    ACTOR_IS_DECLARER = "actor-is-declarer"
    ACTOR_IS_DUMMY = "actor-is-dummy"
    INVALID_CARD_STATE = "invalid-card-state"
    INCONSISTENT_TRICK_ORDER = "inconsistent-trick-order"


@dataclass(frozen=True, slots=True)
class DefensivePlayInput:
    contract: Contract | None = None
    declarer_seat: Seat | None = None
    defender_cards: frozenset[Card] | None = None
    dummy_cards: frozenset[Card] | None = None
    current_actor: Seat | None = None
    completed_tricks: tuple[Trick, ...] | None = None
    current_trick: Trick | None = None
    vulnerability: Vulnerability | None = None
    opening_leader: Seat | None = None


@dataclass(frozen=True, slots=True)
class DefensivePlayState:
    contract: Contract
    defender_cards: frozenset[Card]
    dummy_cards: frozenset[Card]
    current_actor: Seat
    completed_tricks: tuple[Trick, ...]
    current_trick: Trick
    vulnerability: Vulnerability | None = None
    opening_leader: Seat | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "defender_cards", frozenset(self.defender_cards))
        object.__setattr__(self, "dummy_cards", frozenset(self.dummy_cards))
        object.__setattr__(self, "completed_tricks", tuple(self.completed_tricks))
        if self.current_actor is self.declarer:
            raise ValueError("current defensive actor cannot be declarer")
        if self.current_actor is self.dummy:
            raise ValueError("current defensive actor cannot be dummy")
        if any(not trick.is_complete for trick in self.completed_tricks):
            raise ValueError("completed defensive history may contain only complete tricks")
        expected = self.current_trick.leader
        for _ in self.current_trick.plays:
            expected = expected.next()
        if self.current_actor is not expected:
            raise ValueError("current actor is inconsistent with current trick order")
        visible = self.defender_cards | self.dummy_cards
        if len(visible) != len(self.defender_cards) + len(self.dummy_cards):
            raise ValueError("defender and dummy holdings contain a duplicate card")
        played = tuple(play.card for trick in (*self.completed_tricks, self.current_trick) for play in trick.plays)
        if len(played) != len(set(played)):
            raise ValueError("defensive play history contains a duplicate physical card")
        if visible.intersection(played):
            raise ValueError("played cards cannot remain in defender-known holdings")

    @property
    def declarer(self) -> Seat:
        return self.contract.declarer

    @property
    def dummy(self) -> Seat:
        return self.declarer.partner()

    @property
    def partner(self) -> Seat:
        return self.current_actor.partner()

    @property
    def legal_actions(self) -> tuple[Card, ...]:
        return legal_cards(self.defender_cards, self.current_trick)

    @property
    def trick_number(self) -> int:
        return len(self.completed_tricks) + 1

    @property
    def visible_cards(self) -> frozenset[Card]:
        return self.defender_cards | self.dummy_cards

    @property
    def played_cards(self) -> frozenset[Card]:
        return frozenset(play.card for trick in (*self.completed_tricks, self.current_trick) for play in trick.plays)

    @property
    def unknown_card_count(self) -> int:
        return 52 - len(self.visible_cards | self.played_cards)

    @property
    def follow_suit_required(self) -> bool:
        led = self.current_trick.led_suit
        return led is not None and any(card.suit is led for card in self.defender_cards)

    @property
    def declarer_tricks(self) -> int:
        trump = self.contract.bid.strain.suit
        return sum(trick.winner(trump) in {self.declarer, self.dummy} for trick in self.completed_tricks)

    @property
    def defender_tricks(self) -> int:
        return len(self.completed_tricks) - self.declarer_tricks


@dataclass(frozen=True, slots=True)
class DefensiveStateBuildResult:
    state: DefensivePlayState | None
    failure_code: DefensiveStateFailureCode | None = None
    explanation: str = ""

    @property
    def is_ready(self) -> bool:
        return self.state is not None


def build_defensive_play_state(source: DefensivePlayInput | None) -> DefensiveStateBuildResult:
    if source is None or source.contract is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_CONTRACT, "Defensive contract is missing.")
    if source.declarer_seat is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_DECLARER_SEAT, "Declarer seat is missing.")
    if source.declarer_seat is not source.contract.declarer:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.INVALID_CARD_STATE, "Declarer seat conflicts with contract.")
    if source.defender_cards is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_DEFENDER_HAND, "Acting defender hand is missing.")
    if source.dummy_cards is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_DUMMY_HAND, "Visible dummy hand is missing.")
    if source.current_actor is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_CURRENT_ACTOR, "Current defensive actor is missing.")
    if source.current_actor is source.declarer_seat:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.ACTOR_IS_DECLARER, "Current actor is declarer, not a defender.")
    if source.current_actor is source.declarer_seat.partner():
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.ACTOR_IS_DUMMY, "Current actor is dummy, not a defender.")
    if source.completed_tricks is None or source.current_trick is None:
        return DefensiveStateBuildResult(None, DefensiveStateFailureCode.MISSING_PLAY_HISTORY, "Defensive play history is missing.")
    try:
        state = DefensivePlayState(
            source.contract, source.defender_cards, source.dummy_cards, source.current_actor,
            source.completed_tricks, source.current_trick, source.vulnerability, source.opening_leader,
        )
    except (TypeError, ValueError) as exc:
        code = DefensiveStateFailureCode.INCONSISTENT_TRICK_ORDER if "trick order" in str(exc) else DefensiveStateFailureCode.INVALID_CARD_STATE
        return DefensiveStateBuildResult(None, code, str(exc))
    return DefensiveStateBuildResult(state)


def build_defensive_probability_context(state: DefensivePlayState) -> ProbabilityContext:
    """Expose only cards known to the acting defender and validated history."""
    return ProbabilityContext(state.visible_cards, state.played_cards, state.unknown_card_count)
