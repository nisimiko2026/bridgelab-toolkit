"""A6.2 TrickSolver -> OutcomeEvaluator adapter tests."""

from dataclasses import replace

import pytest

from bridge.deals import generate_deal
from bridge.models import Card, Seat, Suit
from bridge.outcome_evaluation import (
    OutcomeEvaluationMethod,
    OutcomeEvaluationRequest,
    OutcomeEvaluationStatus,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from bridge.trick_solver_outcome_adapter import TrickSolverOutcomeEvaluator


class StubTrickSolver:
    def __init__(self, result: TrickSolverResult) -> None:
        self.result = result
        self.calls = []

    def solve(
        self,
        deal,
        declarer,
        strain,
        *,
        opening_lead=None,
    ) -> TrickSolverResult:
        self.calls.append((deal, declarer, strain, opening_lead))
        return self.result


def make_request(
    *,
    declarer: Seat = Seat.NORTH,
    strain: Suit | None = Suit.SPADES,
    opening_lead: Card | None = None,
) -> OutcomeEvaluationRequest:
    return OutcomeEvaluationRequest(
        deal=generate_deal(6201),
        declarer=declarer,
        strain=strain,
        opening_lead=opening_lead,
    )


def make_solver_result(
    *,
    status: TrickSolverStatus = TrickSolverStatus.SUCCESS,
    declarer: Seat = Seat.NORTH,
    strain: Suit | None = Suit.SPADES,
    opening_lead: Card | None = None,
    tricks: int | None = 10,
    error: str | None = None,
) -> TrickSolverResult:
    return TrickSolverResult(
        implementation="stub-dds",
        version="1.2.3",
        deal_id="deal-6201",
        declarer=declarer,
        strain=strain,
        opening_lead=opening_lead,
        status=status,
        maximum_declarer_tricks=tricks,
        elapsed_seconds=0.125,
        error=error,
    )


def test_success_maps_to_double_dummy_outcome() -> None:
    solver = StubTrickSolver(make_solver_result())
    evaluator = TrickSolverOutcomeEvaluator(
        solver=solver,
        provider_id="legacy-dds",
    )
    request = make_request()

    result = evaluator.evaluate(request)

    assert result.provider_id == "legacy-dds"
    assert result.implementation == "stub-dds"
    assert result.version == "1.2.3"
    assert result.method is OutcomeEvaluationMethod.DOUBLE_DUMMY
    assert result.status is OutcomeEvaluationStatus.SUCCESS
    assert result.declarer is Seat.NORTH
    assert result.strain is Suit.SPADES
    assert result.declarer_tricks == 10
    assert result.sample_count is None
    assert result.elapsed_seconds == pytest.approx(0.125)
    assert result.error is None


def test_request_is_forwarded_exactly_to_solver() -> None:
    lead = Card.parse("2S")
    request = make_request(
        declarer=Seat.SOUTH,
        strain=None,
        opening_lead=lead,
    )
    solver = StubTrickSolver(
        make_solver_result(
            declarer=Seat.SOUTH,
            strain=None,
            opening_lead=lead,
            tricks=8,
        )
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    evaluator.evaluate(request)

    assert solver.calls == [
        (request.deal, Seat.SOUTH, None, lead)
    ]


@pytest.mark.parametrize(
    ("solver_status", "outcome_status"),
    (
        (
            TrickSolverStatus.UNAVAILABLE,
            OutcomeEvaluationStatus.UNAVAILABLE,
        ),
        (
            TrickSolverStatus.FAILED,
            OutcomeEvaluationStatus.FAILED,
        ),
    ),
)
def test_non_success_status_is_preserved(
    solver_status,
    outcome_status,
) -> None:
    solver = StubTrickSolver(
        make_solver_result(
            status=solver_status,
            tricks=None,
            error="solver unavailable or failed",
        )
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    result = evaluator.evaluate(make_request())

    assert result.status is outcome_status
    assert result.declarer_tricks is None
    assert result.sample_count is None
    assert result.error == "solver unavailable or failed"


def test_adapter_default_method_is_double_dummy() -> None:
    evaluator = TrickSolverOutcomeEvaluator(
        solver=StubTrickSolver(make_solver_result())
    )

    assert evaluator.method is OutcomeEvaluationMethod.DOUBLE_DUMMY


def test_adapter_rejects_non_double_dummy_method() -> None:
    with pytest.raises(
        ValueError,
        match="method must be DOUBLE_DUMMY",
    ):
        TrickSolverOutcomeEvaluator(
            solver=StubTrickSolver(make_solver_result()),
            method=OutcomeEvaluationMethod.SIMULATION,
        )


def test_adapter_requires_callable_solve() -> None:
    with pytest.raises(
        TypeError,
        match="solver must provide a callable solve method",
    ):
        TrickSolverOutcomeEvaluator(solver=object())  # type: ignore[arg-type]


def test_adapter_requires_nonblank_provider_id() -> None:
    with pytest.raises(
        ValueError,
        match="provider_id must be a non-blank string",
    ):
        TrickSolverOutcomeEvaluator(
            solver=StubTrickSolver(make_solver_result()),
            provider_id=" ",
        )


def test_evaluate_rejects_invalid_request() -> None:
    evaluator = TrickSolverOutcomeEvaluator(
        solver=StubTrickSolver(make_solver_result())
    )

    with pytest.raises(
        TypeError,
        match="request must be OutcomeEvaluationRequest",
    ):
        evaluator.evaluate(object())  # type: ignore[arg-type]


def test_solver_must_return_trick_solver_result() -> None:
    class BadSolver:
        def solve(self, deal, declarer, strain, *, opening_lead=None):
            return object()

    evaluator = TrickSolverOutcomeEvaluator(
        solver=BadSolver()  # type: ignore[arg-type]
    )

    with pytest.raises(
        TypeError,
        match="solver must return TrickSolverResult",
    ):
        evaluator.evaluate(make_request())


def test_mismatched_declarer_is_rejected() -> None:
    solver = StubTrickSolver(
        make_solver_result(declarer=Seat.SOUTH)
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    with pytest.raises(
        ValueError,
        match="solver result declarer does not match request",
    ):
        evaluator.evaluate(make_request())


def test_mismatched_strain_is_rejected() -> None:
    solver = StubTrickSolver(
        make_solver_result(strain=Suit.HEARTS)
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    with pytest.raises(
        ValueError,
        match="solver result strain does not match request",
    ):
        evaluator.evaluate(make_request())


def test_mismatched_opening_lead_is_rejected() -> None:
    solver = StubTrickSolver(
        make_solver_result(opening_lead=Card.parse("2S"))
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    with pytest.raises(
        ValueError,
        match="solver result opening_lead does not match request",
    ):
        evaluator.evaluate(make_request())


def test_solver_measurement_is_not_reinterpreted() -> None:
    solver = StubTrickSolver(
        make_solver_result(tricks=7)
    )
    evaluator = TrickSolverOutcomeEvaluator(solver=solver)

    result = evaluator.evaluate(make_request())

    assert result.declarer_tricks == 7
    assert result.method is OutcomeEvaluationMethod.DOUBLE_DUMMY
    assert result.sample_count is None
