"""Optional live DDS boundary for BridgeLab.

A6.11 — Live DDS Provider Boundary.

This module adapts an optional external DDS callable to BridgeLab's existing
TrickSolver contract. DDS remains an external measurement provider: importing
this module does not import or require a DDS package, and unavailable/failure
states never receive heuristic substitutes.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from .deals import Deal
from .models import Card, Seat, Suit
from .trick_solver import TrickSolverResult, TrickSolverStatus


LiveDDSCallable = Callable[[Deal, Seat, Suit | None, Card | None], int]


@dataclass(frozen=True, slots=True)
class LiveDDSTrickSolver:
    """Expose an injected live DDS implementation through ``TrickSolver``."""

    solve_callable: LiveDDSCallable | None
    implementation: str = "live-dds"
    version: str | None = None

    def __post_init__(self) -> None:
        if self.solve_callable is not None and not callable(self.solve_callable):
            raise TypeError("solve_callable must be callable or None")
        if not isinstance(self.implementation, str) or not self.implementation.strip():
            raise ValueError("implementation must be a non-blank string")
        object.__setattr__(self, "implementation", self.implementation.strip())
        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise ValueError("version must be None or a non-blank string")
            object.__setattr__(self, "version", self.version.strip())

    def solve(
        self,
        deal: Deal,
        declarer: Seat,
        strain: Suit | None,
        *,
        opening_lead: Card | None = None,
    ) -> TrickSolverResult:
        if not isinstance(deal, Deal):
            raise TypeError("deal must be Deal")
        if not isinstance(declarer, Seat):
            raise TypeError("declarer must be Seat")
        if strain is not None and not isinstance(strain, Suit):
            raise TypeError("strain must be Suit or None for NT")
        if opening_lead is not None and not isinstance(opening_lead, Card):
            raise TypeError("opening_lead must be Card or None")

        deal_id = deal.serialize()

        if self.solve_callable is None:
            return TrickSolverResult(
                implementation=self.implementation,
                version=self.version,
                deal_id=deal_id,
                declarer=declarer,
                strain=strain,
                opening_lead=opening_lead,
                status=TrickSolverStatus.UNAVAILABLE,
                maximum_declarer_tricks=None,
                elapsed_seconds=0.0,
                error="live DDS implementation is unavailable",
            )

        started = perf_counter()
        try:
            tricks = self.solve_callable(deal, declarer, strain, opening_lead)
        except Exception as exc:
            elapsed = perf_counter() - started
            return TrickSolverResult(
                implementation=self.implementation,
                version=self.version,
                deal_id=deal_id,
                declarer=declarer,
                strain=strain,
                opening_lead=opening_lead,
                status=TrickSolverStatus.FAILED,
                maximum_declarer_tricks=None,
                elapsed_seconds=elapsed,
                error=f"{type(exc).__name__}: {exc}",
            )

        elapsed = perf_counter() - started
        if not isinstance(tricks, int) or isinstance(tricks, bool) or not 0 <= tricks <= 13:
            return TrickSolverResult(
                implementation=self.implementation,
                version=self.version,
                deal_id=deal_id,
                declarer=declarer,
                strain=strain,
                opening_lead=opening_lead,
                status=TrickSolverStatus.FAILED,
                maximum_declarer_tricks=None,
                elapsed_seconds=elapsed,
                error="live DDS implementation returned invalid declarer tricks",
            )

        return TrickSolverResult(
            implementation=self.implementation,
            version=self.version,
            deal_id=deal_id,
            declarer=declarer,
            strain=strain,
            opening_lead=opening_lead,
            status=TrickSolverStatus.SUCCESS,
            maximum_declarer_tricks=tricks,
            elapsed_seconds=elapsed,
            error=None,
        )
