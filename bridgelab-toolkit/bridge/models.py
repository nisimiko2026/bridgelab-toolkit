"""BridgeLab Bridge Engine — immutable core bridge domain models.

This module deliberately contains no bidding-system knowledge.  It models
only objective bridge facts needed by later auction and reasoning layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Iterable, Iterator


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def symbol(self) -> str:
        return {self.CLUBS: "♣", self.DIAMONDS: "♦", self.HEARTS: "♥", self.SPADES: "♠"}[self]

    @property
    def letter(self) -> str:
        return {self.CLUBS: "C", self.DIAMONDS: "D", self.HEARTS: "H", self.SPADES: "S"}[self]

    @classmethod
    def parse(cls, value: str) -> "Suit":
        key = value.strip().upper()
        aliases = {
            "C": cls.CLUBS, "♣": cls.CLUBS, "CLUB": cls.CLUBS, "CLUBS": cls.CLUBS,
            "D": cls.DIAMONDS, "♦": cls.DIAMONDS, "DIAMOND": cls.DIAMONDS, "DIAMONDS": cls.DIAMONDS,
            "H": cls.HEARTS, "♥": cls.HEARTS, "HEART": cls.HEARTS, "HEARTS": cls.HEARTS,
            "S": cls.SPADES, "♠": cls.SPADES, "SPADE": cls.SPADES, "SPADES": cls.SPADES,
        }
        try:
            return aliases[key]
        except KeyError as exc:
            raise ValueError(f"invalid suit: {value!r}") from exc


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        return {10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}.get(int(self), str(int(self)))

    @classmethod
    def parse(cls, value: str) -> "Rank":
        key = value.strip().upper()
        aliases = {str(n): cls(n) for n in range(2, 10)}
        aliases.update({"T": cls.TEN, "10": cls.TEN, "J": cls.JACK, "Q": cls.QUEEN, "K": cls.KING, "A": cls.ACE})
        try:
            return aliases[key]
        except KeyError as exc:
            raise ValueError(f"invalid rank: {value!r}") from exc


@dataclass(frozen=True, slots=True, order=True)
class Card:
    suit: Suit
    rank: Rank

    def __post_init__(self) -> None:
        if not isinstance(self.suit, Suit):
            raise TypeError("suit must be Suit")
        if not isinstance(self.rank, Rank):
            raise TypeError("rank must be Rank")

    @classmethod
    def parse(cls, value: str) -> "Card":
        text = value.strip()
        if len(text) < 2:
            raise ValueError(f"invalid card: {value!r}")
        if text[0] in "♣♦♥♠":
            suit, rank = Suit.parse(text[0]), Rank.parse(text[1:])
        else:
            suit, rank = Suit.parse(text[-1]), Rank.parse(text[:-1])
        return cls(suit=suit, rank=rank)

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.symbol}"

    def serialize(self) -> str:
        """ASCII canonical card representation, e.g. AS or TD."""
        return f"{self.rank.symbol}{self.suit.letter}"


class Seat(Enum):
    NORTH = "N"
    EAST = "E"
    SOUTH = "S"
    WEST = "W"

    @classmethod
    def parse(cls, value: str) -> "Seat":
        key = value.strip().upper()
        aliases = {"N": cls.NORTH, "NORTH": cls.NORTH, "E": cls.EAST, "EAST": cls.EAST,
                   "S": cls.SOUTH, "SOUTH": cls.SOUTH, "W": cls.WEST, "WEST": cls.WEST}
        try:
            return aliases[key]
        except KeyError as exc:
            raise ValueError(f"invalid seat: {value!r}") from exc

    def next(self) -> "Seat":
        order = (Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST)
        return order[(order.index(self) + 1) % 4]

    def partner(self) -> "Seat":
        return self.next().next()

    def is_partner(self, other: "Seat") -> bool:
        return self.partner() is other


class Vulnerability(Enum):
    NONE = "None"
    NS = "NS"
    EW = "EW"
    BOTH = "Both"

    def is_vulnerable(self, seat: Seat) -> bool:
        if self is Vulnerability.BOTH:
            return True
        if self is Vulnerability.NONE:
            return False
        if self is Vulnerability.NS:
            return seat in (Seat.NORTH, Seat.SOUTH)
        return seat in (Seat.EAST, Seat.WEST)


@dataclass(frozen=True, slots=True)
class Hand:
    """Exactly thirteen unique cards.

    Canonical text uses PBN-style suit order S.H.D.C, with '-' for a void.
    Example: ``AKQ.JT9.876.5432``.
    """

    cards: frozenset[Card]

    def __post_init__(self) -> None:
        if not isinstance(self.cards, frozenset):
            object.__setattr__(self, "cards", frozenset(self.cards))
        if len(self.cards) != 13:
            raise ValueError(f"a bridge hand must contain exactly 13 unique cards; got {len(self.cards)}")

    @classmethod
    def from_cards(cls, cards: Iterable[Card]) -> "Hand":
        materialized = tuple(cards)
        unique = frozenset(materialized)
        if len(unique) != len(materialized):
            raise ValueError("hand contains duplicate cards")
        return cls(unique)

    @classmethod
    def parse(cls, value: str) -> "Hand":
        groups = value.strip().upper().split(".")
        if len(groups) != 4:
            raise ValueError("hand must contain four dot-separated suits in S.H.D.C order")

        cards: list[Card] = []
        for suit, ranks in zip((Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS), groups):
            ranks = ranks.strip()
            if ranks in ("", "-"):
                continue
            i = 0
            while i < len(ranks):
                token = "10" if ranks[i:i+2] == "10" else ranks[i]
                cards.append(Card(suit=suit, rank=Rank.parse(token)))
                i += len(token)
        return cls.from_cards(cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(sorted(self.cards, key=lambda c: (int(c.suit), int(c.rank)), reverse=True))

    def cards_in(self, suit: Suit) -> tuple[Card, ...]:
        return tuple(sorted((c for c in self.cards if c.suit is suit), key=lambda c: int(c.rank), reverse=True))

    def length(self, suit: Suit) -> int:
        return sum(card.suit is suit for card in self.cards)

    @property
    def shape(self) -> tuple[int, int, int, int]:
        """Suit lengths in canonical S.H.D.C order."""
        return tuple(self.length(s) for s in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS))

    def serialize(self) -> str:
        groups = []
        for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS):
            ranks = "".join(card.rank.symbol for card in self.cards_in(suit))
            groups.append(ranks or "-")
        return ".".join(groups)

    def __str__(self) -> str:
        return self.serialize()
