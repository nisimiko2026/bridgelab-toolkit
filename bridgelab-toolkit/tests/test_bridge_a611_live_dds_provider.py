"""A6.11 live DDS provider boundary tests."""

import pytest

from bridge.deals import generate_deal
from bridge.live_dds_trick_solver import LiveDDSTrickSolver
from bridge.models import Seat, Suit
from bridge.outcome_evaluation import (
    OutcomeEvaluationMethod,
    OutcomeEvaluationRequest,
    OutcomeEvaluationStatus,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from bridge.trick_solver_outcome_adapter import TrickSolverOutcomeEvaluator


def _deal():
    return generate_deal(6110)


def test_live_dds_solver_success() -> None:
    solver = LiveDDSTrickSolver(
        lambda deal, declarer, strain, opening_lead: 10,
        implementation="dds3",
        version="2.9.0",
    )
    result = solver.solve(_deal(), Seat.NORTH, Suit.SPADES)

    assert isinstance(result, TrickSolverResult)
    assert result.status is TrickSolverStatus.SUCCESS
    assert result.maximum_declarer_tricks == 10
    assert result.implementation == "dds3"
    assert result.version == "2.9.0"
    assert result.declarer is Seat.NORTH
    assert result.strain is Suit.SPADES
    assert result.opening_lead is None
    assert result.elapsed_seconds >= 0
    assert result.error is None


def test_live_dds_solver_supports_notrump() -> None:
    seen = {}

    def solve(deal, declarer, strain, opening_lead):
        seen["strain"] = strain
        return 9

    result = LiveDDSTrickSolver(solve).solve(_deal(), Seat.SOUTH, None)

    assert result.status is TrickSolverStatus.SUCCESS
    assert result.maximum_declarer_tricks == 9
    assert seen["strain"] is None


def test_live_dds_solver_forwards_opening_lead() -> None:
    deal = _deal()
    lead = next(iter(deal.hand(Seat.EAST).cards))
    seen = {}

    def solve(deal_arg, declarer, strain, opening_lead):
        seen["lead"] = opening_lead
        return 8

    result = LiveDDSTrickSolver(solve).solve(
        deal,
        Seat.SOUTH,
        Suit.HEARTS,
        opening_lead=lead,
    )

    assert seen["lead"] == lead
    assert result.opening_lead == lead


def test_unavailable_when_no_live_implementation() -> None:
    result = LiveDDSTrickSolver(None, implementation="dds3").solve(
        _deal(),
        Seat.NORTH,
        Suit.SPADES,
    )

    assert result.status is TrickSolverStatus.UNAVAILABLE
    assert result.maximum_declarer_tricks is None
    assert result.elapsed_seconds == 0.0
    assert result.error == "live DDS implementation is unavailable"


def test_provider_exception_becomes_failed_without_fallback() -> None:
    def explode(deal, declarer, strain, opening_lead):
        raise RuntimeError("dds unavailable")

    result = LiveDDSTrickSolver(explode).solve(
        _deal(),
        Seat.NORTH,
        Suit.SPADES,
    )

    assert result.status is TrickSolverStatus.FAILED
    assert result.maximum_declarer_tricks is None
    assert result.elapsed_seconds >= 0
    assert result.error == "RuntimeError: dds unavailable"


@pytest.mark.parametrize("value", (-1, 14, 7.5, True, "9", None))
def test_invalid_provider_trick_result_becomes_failed(value) -> None:
    solver = LiveDDSTrickSolver(
        lambda deal, declarer, strain, opening_lead: value
    )
    result = solver.solve(_deal(), Seat.NORTH, Suit.SPADES)

    assert result.status is TrickSolverStatus.FAILED
    assert result.maximum_declarer_tricks is None
    assert result.error == "live DDS implementation returned invalid declarer tricks"


def test_callable_receives_exact_request_context() -> None:
    deal = _deal()
    seen = {}

    def solve(deal_arg, declarer, strain, opening_lead):
        seen.update(
            deal=deal_arg,
            declarer=declarer,
            strain=strain,
            opening_lead=opening_lead,
        )
        return 11

    LiveDDSTrickSolver(solve).solve(deal, Seat.WEST, Suit.DIAMONDS)

    assert seen == {
        "deal": deal,
        "declarer": Seat.WEST,
        "strain": Suit.DIAMONDS,
        "opening_lead": None,
    }


def test_end_to_end_through_outcome_evaluator() -> None:
    solver = LiveDDSTrickSolver(
        lambda deal, declarer, strain, opening_lead: 10,
        implementation="dds3",
        version="live-test",
    )
    evaluator = TrickSolverOutcomeEvaluator(
        solver=solver,
        provider_id="dds3",
    )
    request = OutcomeEvaluationRequest(
        deal=_deal(),
        declarer=Seat.NORTH,
        strain=Suit.SPADES,
    )

    result = evaluator.evaluate(request)

    assert result.provider_id == "dds3"
    assert result.implementation == "dds3"
    assert result.version == "live-test"
    assert result.method is OutcomeEvaluationMethod.DOUBLE_DUMMY
    assert result.status is OutcomeEvaluationStatus.SUCCESS
    assert result.declarer_tricks == 10
    assert result.sample_count is None


def test_unavailable_maps_end_to_end_without_invented_tricks() -> None:
    evaluator = TrickSolverOutcomeEvaluator(
        solver=LiveDDSTrickSolver(None, implementation="dds3"),
        provider_id="dds3",
    )
    result = evaluator.evaluate(
        OutcomeEvaluationRequest(
            deal=_deal(),
            declarer=Seat.NORTH,
            strain=Suit.SPADES,
        )
    )

    assert result.status is OutcomeEvaluationStatus.UNAVAILABLE
    assert result.declarer_tricks is None
    assert result.error == "live DDS implementation is unavailable"


def test_failed_maps_end_to_end_without_invented_tricks() -> None:
    def explode(deal, declarer, strain, opening_lead):
        raise ValueError("bad DDS call")

    evaluator = TrickSolverOutcomeEvaluator(
        solver=LiveDDSTrickSolver(explode, implementation="dds3"),
        provider_id="dds3",
    )
    result = evaluator.evaluate(
        OutcomeEvaluationRequest(
            deal=_deal(),
            declarer=Seat.EAST,
            strain=None,
        )
    )

    assert result.status is OutcomeEvaluationStatus.FAILED
    assert result.declarer_tricks is None
    assert result.error == "ValueError: bad DDS call"


def test_rejects_non_callable_provider() -> None:
    with pytest.raises(TypeError, match="solve_callable must be callable or None"):
        LiveDDSTrickSolver(42)


def test_rejects_blank_implementation() -> None:
    with pytest.raises(ValueError, match="implementation must be a non-blank string"):
        LiveDDSTrickSolver(None, implementation="   ")


def test_rejects_blank_version() -> None:
    with pytest.raises(ValueError, match="version must be None or a non-blank string"):
        LiveDDSTrickSolver(None, version=" ")


def test_metadata_is_trimmed() -> None:
    solver = LiveDDSTrickSolver(
        None,
        implementation="  dds3  ",
        version="  2.9.0  ",
    )
    assert solver.implementation == "dds3"
    assert solver.version == "2.9.0"


def test_rejects_invalid_deal() -> None:
    with pytest.raises(TypeError, match="deal must be Deal"):
        LiveDDSTrickSolver(None).solve(object(), Seat.NORTH, Suit.SPADES)


def test_rejects_invalid_declarer() -> None:
    with pytest.raises(TypeError, match="declarer must be Seat"):
        LiveDDSTrickSolver(None).solve(_deal(), "N", Suit.SPADES)


def test_rejects_invalid_strain() -> None:
    with pytest.raises(TypeError, match="strain must be Suit or None for NT"):
        LiveDDSTrickSolver(None).solve(_deal(), Seat.NORTH, "S")


def test_live_dds_boundary_has_no_policy_or_ranking_surface() -> None:
    solver = LiveDDSTrickSolver(None)
    for name in (
        "winner",
        "best",
        "rank",
        "ranking",
        "recommended",
        "recommendation",
        "policy",
    ):
        assert not hasattr(solver, name)
