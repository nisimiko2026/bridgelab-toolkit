"""Observed bidding decisions extracted from canonical corpus records.

A CorpusBiddingDecision represents one actual call observed in a corpus,
together with the information available immediately before that call.

Observed calls are evidence. They are not BridgeLab recommendations and do
not imply that the observed partnership used any particular bidding system.
"""

from __future__ import annotations

from dataclasses import dataclass

from .auction import Auction, Call
from .corpus import CanonicalBoardRecord, SourceProvenance
from .models import Hand, Seat, Vulnerability


@dataclass(frozen=True, slots=True)
class CorpusBiddingDecision:
    """One observed corpus bidding decision."""

    provenance: SourceProvenance
    call_index: int
    seat: Seat
    hand: Hand
    auction: Auction
    observed_call: Call
    vulnerability: Vulnerability
    system_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, SourceProvenance):
            raise TypeError(
                "provenance must be SourceProvenance"
            )

        if (
            not isinstance(self.call_index, int)
            or isinstance(self.call_index, bool)
            or self.call_index < 0
        ):
            raise ValueError(
                "call_index must be a non-negative integer"
            )

        if not isinstance(self.seat, Seat):
            raise TypeError("seat must be Seat")

        if not isinstance(self.hand, Hand):
            raise TypeError("hand must be Hand")

        if not isinstance(self.auction, Auction):
            raise TypeError("auction must be Auction")

        if not isinstance(self.observed_call, Call):
            raise TypeError("observed_call must be Call")

        if not isinstance(
            self.vulnerability,
            Vulnerability,
        ):
            raise TypeError(
                "vulnerability must be Vulnerability"
            )

        if self.auction.next_seat is not self.seat:
            raise ValueError(
                "auction next seat conflicts with decision seat"
            )

        if not self.auction.is_legal(self.observed_call):
            raise ValueError(
                "observed call is illegal for auction prefix"
            )

        if self.system_id is not None:
            if (
                not isinstance(self.system_id, str)
                or not self.system_id.strip()
            ):
                raise ValueError(
                    "system_id must be None or a non-blank string"
                )

            object.__setattr__(
                self,
                "system_id",
                self.system_id.strip(),
            )


def _system_for_seat(
    record: CanonicalBoardRecord,
    seat: Seat,
) -> str | None:
    if seat in (Seat.NORTH, Seat.SOUTH):
        return record.ns_system
    return record.ew_system


def extract_corpus_bidding_decisions(
    record: CanonicalBoardRecord,
) -> tuple[CorpusBiddingDecision, ...]:
    """Extract every observed bidding decision from one canonical board.

    The auction stored on each decision is the prefix immediately before
    the observed call.
    """

    if not isinstance(record, CanonicalBoardRecord):
        raise TypeError(
            "record must be CanonicalBoardRecord"
        )

    if record.deal is None:
        raise ValueError(
            "record must contain a deal"
        )

    if record.auction is None:
        raise ValueError(
            "record must contain an auction"
        )

    prefix = Auction(record.dealer)
    decisions: list[CorpusBiddingDecision] = []

    for index, entry in enumerate(record.auction.entries):
        seat = prefix.next_seat

        if seat is not entry.seat:
            raise ValueError(
                "auction entry seat conflicts with auction prefix"
            )

        decisions.append(
            CorpusBiddingDecision(
                provenance=record.provenance,
                call_index=index,
                seat=seat,
                hand=record.deal.hand(seat),
                auction=Auction(
                    record.dealer,
                    prefix.calls,
                ),
                observed_call=entry.call,
                vulnerability=record.vulnerability,
                system_id=_system_for_seat(
                    record,
                    seat,
                ),
            )
        )

        prefix.add(entry.call)

    return tuple(decisions)
