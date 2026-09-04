"""Theory-neutral aggregation of auction simulation outcomes."""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from typing import Iterable
from .auction_simulation import AuctionSimulationResult, SimulationStopReason


@dataclass(frozen=True, slots=True)
class SimulationStatistics:
    runs: int
    completed: int
    abstained: int
    max_steps: int
    total_calls_added: int
    max_calls_added: int
    stop_reason_counts: tuple[tuple[str,int], ...]
    stopped_seat_counts: tuple[tuple[str,int], ...]

    @property
    def average_calls_added(self) -> float:
        return 0.0 if self.runs == 0 else self.total_calls_added / self.runs


def summarize_simulations(results: Iterable[AuctionSimulationResult]) -> SimulationStatistics:
    rows=tuple(results)
    reasons=Counter(r.stop_reason.value for r in rows)
    seats=Counter(r.stopped_seat.value for r in rows if r.stopped_seat is not None)
    lengths=[len(r.steps) for r in rows]
    return SimulationStatistics(
        runs=len(rows),
        completed=reasons[SimulationStopReason.AUCTION_COMPLETE.value],
        abstained=reasons[SimulationStopReason.NO_RECOMMENDATION.value],
        max_steps=reasons[SimulationStopReason.MAX_STEPS.value],
        total_calls_added=sum(lengths),
        max_calls_added=max(lengths,default=0),
        stop_reason_counts=tuple(sorted(reasons.items())),
        stopped_seat_counts=tuple(sorted(seats.items())),
    )
