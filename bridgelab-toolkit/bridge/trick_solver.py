"""System-independent, optional double-dummy trick solver contract.

Solver outcomes are reference measurements. They are not natural or adjusted
Playing Tricks, and failures never acquire a heuristic substitute.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .deals import Deal
from .models import Card, Seat, Suit


class TrickSolverStatus(str, Enum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TrickSolverResult:
    implementation: str
    version: str | None
    deal_id: str
    declarer: Seat
    strain: Suit | None  # None means no trump.
    opening_lead: Card | None
    status: TrickSolverStatus
    maximum_declarer_tricks: int | None
    elapsed_seconds: float
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.declarer, Seat):
            raise TypeError("declarer must be a Seat")
        if self.strain is not None and not isinstance(self.strain, Suit):
            raise TypeError("strain must be a Suit or None for NT")
        if self.status is TrickSolverStatus.SUCCESS:
            if (not isinstance(self.maximum_declarer_tricks, int)
                    or isinstance(self.maximum_declarer_tricks, bool)
                    or not 0 <= self.maximum_declarer_tricks <= 13):
                raise ValueError("successful solver result needs 0..13 declarer tricks")
        elif self.maximum_declarer_tricks is not None:
            raise ValueError("failed/unavailable solver result must not contain tricks")
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed time cannot be negative")


class TrickSolver(Protocol):
    def solve(self, deal: Deal, declarer: Seat, strain: Suit | None,
              *, opening_lead: Card | None = None) -> TrickSolverResult:
        """Return optimal-play declarer tricks, or an explicit unavailable/failure."""
