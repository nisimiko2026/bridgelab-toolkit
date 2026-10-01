"""Double-dummy capability provider adapters.

This module exposes an existing BridgeLab TrickSolver through the generic
capability-provider architecture.  It does not alter solver results, introduce
fallback heuristics, rank providers, or select a preferred double-dummy engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from .capability_providers import Capability, ProviderDescriptor
from .deals import Deal
from .models import Card, Seat, Suit
from .trick_solver import TrickSolver, TrickSolverResult


@dataclass(frozen=True, slots=True)
class TrickSolverDoubleDummyProvider:
    """Adapt one TrickSolver to the DoubleDummyProvider capability contract."""

    solver: TrickSolver
    descriptor: ProviderDescriptor

    def __post_init__(self) -> None:
        if self.descriptor.capability is not Capability.DOUBLE_DUMMY:
            raise ValueError(
                "double-dummy provider descriptor must use "
                "Capability.DOUBLE_DUMMY"
            )

        solve = getattr(self.solver, "solve", None)
        if not callable(solve):
            raise TypeError("solver must provide a callable solve() method")

    def solve(
        self,
        deal: Deal,
        declarer: Seat,
        strain: Suit | None,
        *,
        opening_lead: Card | None = None,
    ) -> TrickSolverResult:
        """Delegate unchanged to the underlying TrickSolver."""
        return self.solver.solve(
            deal,
            declarer,
            strain,
            opening_lead=opening_lead,
        )
