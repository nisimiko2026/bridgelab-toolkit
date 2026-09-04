"""BridgeLab Bridge Engine — auction representation and legality.

This module models objective auction mechanics only. It deliberately contains
no bidding-system, convention, hand-evaluation, or recommendation knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Iterable, Iterator

from .models import Seat, Suit


class Strain(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    NOTRUMP = 4

    @property
    def symbol(self) -> str:
        return {
            self.CLUBS: "♣",
            self.DIAMONDS: "♦",
            self.HEARTS: "♥",
            self.SPADES: "♠",
            self.NOTRUMP: "NT",
        }[self]

    @property
    def text(self) -> str:
        return {
            self.CLUBS: "C",
            self.DIAMONDS: "D",
            self.HEARTS: "H",
            self.SPADES: "S",
            self.NOTRUMP: "NT",
        }[self]

    @property
    def suit(self) -> Suit | None:
        if self is Strain.NOTRUMP:
            return None
        return Suit(int(self))

    @classmethod
    def parse(cls, value: str) -> "Strain":
        key = value.strip().upper().replace(" ", "")
        aliases = {
            "C": cls.CLUBS,
            "♣": cls.CLUBS,
            "CLUB": cls.CLUBS,
            "CLUBS": cls.CLUBS,
            "D": cls.DIAMONDS,
            "♦": cls.DIAMONDS,
            "DIAMOND": cls.DIAMONDS,
            "DIAMONDS": cls.DIAMONDS,
            "H": cls.HEARTS,
            "♥": cls.HEARTS,
            "HEART": cls.HEARTS,
            "HEARTS": cls.HEARTS,
            "S": cls.SPADES,
            "♠": cls.SPADES,
            "SPADE": cls.SPADES,
            "SPADES": cls.SPADES,
            "N": cls.NOTRUMP,
            "NT": cls.NOTRUMP,
            "NOTRUMP": cls.NOTRUMP,
            "NOTRUMP": cls.NOTRUMP,
            "NO-TRUMP": cls.NOTRUMP,
            "NO_TRUMP": cls.NOTRUMP,
        }
        try:
            return aliases[key]
        except KeyError as exc:
            raise ValueError(f"invalid strain: {value!r}") from exc


@dataclass(frozen=True, slots=True, order=True)
class Bid:
    level: int
    strain: Strain

    def __post_init__(self) -> None:
        if not isinstance(self.level, int) or isinstance(self.level, bool):
            raise TypeError("bid level must be an integer")
        if not 1 <= self.level <= 7:
            raise ValueError("bid level must be between 1 and 7")
        if not isinstance(self.strain, Strain):
            raise TypeError("bid strain must be Strain")

    @property
    def order_value(self) -> int:
        return (self.level - 1) * 5 + int(self.strain)

    def outranks(self, other: "Bid") -> bool:
        return self.order_value > other.order_value

    @classmethod
    def parse(cls, value: str) -> "Bid":
        text = value.strip().upper().replace(" ", "")
        if len(text) < 2 or text[0] not in "1234567":
            raise ValueError(f"invalid bid: {value!r}")
        return cls(level=int(text[0]), strain=Strain.parse(text[1:]))

    def serialize(self) -> str:
        return f"{self.level}{self.strain.text}"

    def __str__(self) -> str:
        return f"{self.level}{self.strain.symbol}"


class CallType(Enum):
    PASS = "P"
    BID = "BID"
    DOUBLE = "X"
    REDOUBLE = "XX"


@dataclass(frozen=True, slots=True)
class Call:
    kind: CallType
    bid: Bid | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, CallType):
            raise TypeError("call kind must be CallType")
        if self.kind is CallType.BID:
            if not isinstance(self.bid, Bid):
                raise ValueError("bid call requires a Bid")
        elif self.bid is not None:
            raise ValueError("non-bid call cannot contain a Bid")

    @classmethod
    def pass_(cls) -> "Call":
        return cls(CallType.PASS)

    @classmethod
    def double(cls) -> "Call":
        return cls(CallType.DOUBLE)

    @classmethod
    def redouble(cls) -> "Call":
        return cls(CallType.REDOUBLE)

    @classmethod
    def from_bid(cls, bid: Bid) -> "Call":
        return cls(CallType.BID, bid)

    @classmethod
    def parse(cls, value: str) -> "Call":
        text = value.strip().upper().replace(" ", "")
        if text in {"P", "PASS", "-"}:
            return cls.pass_()
        if text in {"X", "DBL", "DOUBLE"}:
            return cls.double()
        if text in {"XX", "RDBL", "REDOUBLE"}:
            return cls.redouble()
        return cls.from_bid(Bid.parse(text))

    def serialize(self) -> str:
        if self.kind is CallType.BID:
            assert self.bid is not None
            return self.bid.serialize()
        return self.kind.value

    def __str__(self) -> str:
        if self.kind is CallType.BID:
            assert self.bid is not None
            return str(self.bid)
        return self.kind.value


@dataclass(frozen=True, slots=True)
class AuctionEntry:
    seat: Seat
    call: Call


class Doubling(Enum):
    UNDOUBLED = ""
    DOUBLED = "X"
    REDOUBLED = "XX"


@dataclass(frozen=True, slots=True)
class Contract:
    bid: Bid
    declarer: Seat
    doubling: Doubling = Doubling.UNDOUBLED

    def __post_init__(self) -> None:
        if not isinstance(self.bid, Bid):
            raise TypeError("contract bid must be Bid")
        if not isinstance(self.declarer, Seat):
            raise TypeError("contract declarer must be Seat")
        if not isinstance(self.doubling, Doubling):
            raise TypeError("contract doubling must be Doubling")

    def serialize(self) -> str:
        return f"{self.bid.serialize()}{self.doubling.value} {self.declarer.value}"


class Auction:
    """Mutable auction sequence with deterministic legality checks.

    Seats are assigned from ``dealer`` clockwise. Calls cannot be added after
    the auction has completed.
    """

    def __init__(self, dealer: Seat, calls: Iterable[Call | str] = ()) -> None:
        if not isinstance(dealer, Seat):
            raise TypeError("dealer must be Seat")
        self.dealer = dealer
        self._entries: list[AuctionEntry] = []
        for call in calls:
            self.add(call)

    def __iter__(self) -> Iterator[AuctionEntry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> tuple[AuctionEntry, ...]:
        return tuple(self._entries)

    @property
    def next_seat(self) -> Seat:
        seat = self.dealer
        for _ in self._entries:
            seat = seat.next()
        return seat

    @property
    def calls(self) -> tuple[Call, ...]:
        return tuple(entry.call for entry in self._entries)

    @property
    def is_complete(self) -> bool:
        if len(self._entries) < 4:
            return False
        if not self._has_bid:
            return len(self._entries) == 4 and all(
                entry.call.kind is CallType.PASS for entry in self._entries
            )
        return len(self._entries) >= 4 and all(
            entry.call.kind is CallType.PASS for entry in self._entries[-3:]
        )

    @property
    def is_passed_out(self) -> bool:
        return self.is_complete and not self._has_bid

    @property
    def _has_bid(self) -> bool:
        return any(entry.call.kind is CallType.BID for entry in self._entries)

    @property
    def current_bid(self) -> Bid | None:
        for entry in reversed(self._entries):
            if entry.call.kind is CallType.BID:
                return entry.call.bid
        return None

    @property
    def current_bidder(self) -> Seat | None:
        for entry in reversed(self._entries):
            if entry.call.kind is CallType.BID:
                return entry.seat
        return None

    @property
    def doubling(self) -> Doubling:
        for entry in reversed(self._entries):
            kind = entry.call.kind
            if kind is CallType.BID:
                return Doubling.UNDOUBLED
            if kind is CallType.DOUBLE:
                return Doubling.DOUBLED
            if kind is CallType.REDOUBLE:
                return Doubling.REDOUBLED
        return Doubling.UNDOUBLED

    def legal_calls(self) -> tuple[Call, ...]:
        if self.is_complete:
            return ()

        legal: list[Call] = [Call.pass_()]
        current = self.current_bid

        for level in range(1, 8):
            for strain in Strain:
                bid = Bid(level, strain)
                if current is None or bid.outranks(current):
                    legal.append(Call.from_bid(bid))

        bidder = self.current_bidder
        if bidder is not None:
            next_seat = self.next_seat
            same_side = next_seat is bidder or next_seat.is_partner(bidder)
            if self.doubling is Doubling.UNDOUBLED and not same_side:
                legal.append(Call.double())
            elif self.doubling is Doubling.DOUBLED and same_side:
                legal.append(Call.redouble())

        return tuple(legal)

    def is_legal(self, call: Call | str) -> bool:
        candidate = Call.parse(call) if isinstance(call, str) else call
        if not isinstance(candidate, Call):
            raise TypeError("call must be Call or str")
        return candidate in self.legal_calls()

    def add(self, call: Call | str) -> AuctionEntry:
        if self.is_complete:
            raise ValueError("auction is already complete")
        candidate = Call.parse(call) if isinstance(call, str) else call
        if not isinstance(candidate, Call):
            raise TypeError("call must be Call or str")
        if not self.is_legal(candidate):
            raise ValueError(
                f"illegal call {candidate.serialize()} by {self.next_seat.value}"
            )

        entry = AuctionEntry(self.next_seat, candidate)
        self._entries.append(entry)
        return entry

    @property
    def final_contract(self) -> Contract | None:
        if not self.is_complete or self.is_passed_out:
            return None

        final_bid_entry = next(
            entry
            for entry in reversed(self._entries)
            if entry.call.kind is CallType.BID
        )
        assert final_bid_entry.call.bid is not None
        final_bid = final_bid_entry.call.bid
        declaring_side = final_bid_entry.seat

        declarer = next(
            entry.seat
            for entry in self._entries
            if (
                entry.call.kind is CallType.BID
                and entry.call.bid is not None
                and entry.call.bid.strain is final_bid.strain
                and (
                    entry.seat is declaring_side
                    or entry.seat.is_partner(declaring_side)
                )
            )
        )
        return Contract(final_bid, declarer, self.doubling)

    def serialize(self) -> str:
        return " ".join(entry.call.serialize() for entry in self._entries)
