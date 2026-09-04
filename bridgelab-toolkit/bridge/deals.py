"""Deterministic physical deal generation and replay.

This module contains no bidding knowledge.  It creates complete 52-card deals
from a seed and provides a canonical replay record suitable for offline
simulation experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Mapping

from .models import Card, Hand, Rank, Seat, Suit


def full_deck() -> tuple[Card, ...]:
    """Return the canonical 52-card deck in deterministic suit/rank order."""
    return tuple(Card(suit, rank) for suit in Suit for rank in Rank)


@dataclass(frozen=True, slots=True)
class Deal:
    seed: int
    hands: tuple[tuple[Seat, Hand], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")
        mapping=dict(self.hands)
        if set(mapping) != set(Seat) or len(mapping) != 4:
            raise ValueError("deal must contain exactly N, E, S, W")
        cards=[card for hand in mapping.values() for card in hand.cards]
        if len(cards) != 52 or len(set(cards)) != 52:
            raise ValueError("deal must contain each card exactly once")

    def hand(self, seat: Seat) -> Hand:
        for stored,hand in self.hands:
            if stored is seat:
                return hand
        raise KeyError(seat)

    @property
    def mapping(self) -> dict[Seat, Hand]:
        return dict(self.hands)

    def serialize(self) -> str:
        return "|".join(
            f"{seat.value}:{self.hand(seat).serialize()}"
            for seat in (Seat.NORTH,Seat.EAST,Seat.SOUTH,Seat.WEST)
        )

    @classmethod
    def parse(cls, value: str, *, seed: int = 0) -> "Deal":
        items=[]
        for part in value.strip().split("|"):
            seat_text,sep,hand_text=part.partition(":")
            if not sep:
                raise ValueError("invalid serialized deal")
            items.append((Seat.parse(seat_text),Hand.parse(hand_text)))
        return cls(seed,tuple(items))


def generate_deal(seed: int) -> Deal:
    """Generate one reproducible physical deal using only a local PRNG."""
    if not isinstance(seed,int) or isinstance(seed,bool):
        raise TypeError("seed must be an integer")
    cards=list(full_deck())
    random.Random(seed).shuffle(cards)
    hands=[]
    for index,seat in enumerate((Seat.NORTH,Seat.EAST,Seat.SOUTH,Seat.WEST)):
        hands.append((seat,Hand.from_cards(cards[index*13:(index+1)*13])))
    return Deal(seed,tuple(hands))


def generate_deals(*, start_seed: int, count: int) -> tuple[Deal, ...]:
    if not isinstance(start_seed,int) or isinstance(start_seed,bool):
        raise TypeError("start_seed must be an integer")
    if not isinstance(count,int) or isinstance(count,bool):
        raise TypeError("count must be an integer")
    if count < 0:
        raise ValueError("count must not be negative")
    return tuple(generate_deal(start_seed+i) for i in range(count))
