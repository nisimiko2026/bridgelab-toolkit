"""Adapt the existing TrickSolver contract to outcome evaluation.

A6.2 — TrickSolver -> OutcomeEvaluator Adapter.

The adapter preserves the solver's measurement and status. It does not add
heuristics, infer missing tricks, rank outcomes, or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .outcome_evaluation import (
    OutcomeEvaluationMethod,
    OutcomeEvaluationRequest,
    OutcomeEvaluationResult,
    OutcomeEvaluationStatus,
)
from .trick_solver import TrickSolver, TrickSolverResult, TrickSolverStatus


_STATUS_MAP = {
    TrickSolverStatus.SUCCESS: OutcomeEvaluationStatus.SUCCESS,
    TrickSolverStatus.UNAVAILABLE: OutcomeEvaluationStatus.UNAVAILABLE,
    TrickSolverStatus.FAILED: OutcomeEvaluationStatus.FAILED,
}


@dataclass(frozen=True, slots=True)
class TrickSolverOutcomeEvaluator:
    """Expose any existing TrickSolver through the generic outcome contract."""

    solver: TrickSolver
    provider_id: str = "trick-solver"
    method: OutcomeEvaluationMethod = OutcomeEvaluationMethod.DOUBLE_DUMMY

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        if self.method is not OutcomeEvaluationMethod.DOUBLE_DUMMY:
            raise ValueError(
                "TrickSolverOutcomeEvaluator method must be DOUBLE_DUMMY"
            )
        solve = getattr(self.solver, "solve", None)
        if not callable(solve):
            raise TypeError("solver must provide a callable solve method")

    def evaluate(
        self,
        request: OutcomeEvaluationRequest,
    ) -> OutcomeEvaluationResult:
        if not isinstance(request, OutcomeEvaluationRequest):
            raise TypeError("request must be OutcomeEvaluationRequest")

        result = self.solver.solve(
            request.deal,
            request.declarer,
            request.strain,
            opening_lead=request.opening_lead,
        )

        if not isinstance(result, TrickSolverResult):
            raise TypeError("solver must return TrickSolverResult")

        # A solver result must describe the same problem that was requested.
        if result.declarer is not request.declarer:
            raise ValueError("solver result declarer does not match request")
        if result.strain is not request.strain:
            raise ValueError("solver result strain does not match request")
        if result.opening_lead != request.opening_lead:
            raise ValueError("solver result opening_lead does not match request")

        return OutcomeEvaluationResult(
            provider_id=self.provider_id,
            implementation=result.implementation,
            version=result.version,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=_STATUS_MAP[result.status],
            declarer=result.declarer,
            strain=result.strain,
            opening_lead=result.opening_lead,
            declarer_tricks=result.maximum_declarer_tricks,
            sample_count=None,
            elapsed_seconds=result.elapsed_seconds,
            error=result.error,
        )
