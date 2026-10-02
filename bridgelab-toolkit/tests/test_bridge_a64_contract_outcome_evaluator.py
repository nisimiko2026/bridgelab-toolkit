"""A6.4 contract outcome evaluator tests."""

import pytest

from bridge.auction import Contract
from bridge.contract_outcome_evaluator import evaluate_contract_outcome
from bridge.corpus import Vulnerability
from bridge.deals import generate_deal
from bridge.models import Seat, Suit
from bridge.outcome_evaluation import (
    OutcomeEvaluationMethod,
    OutcomeEvaluationResult,
    OutcomeEvaluationStatus,
)


class StubOutcomeEvaluator:
    def __init__(self, result: OutcomeEvaluationResult) -> None:
        self.result = result
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        return self.result


def make_result(
    *,
    status=OutcomeEvaluationStatus.SUCCESS,
    declarer=Seat.NORTH,
    strain=Suit.HEARTS,
    tricks=10,
    method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
    sample_count=None,
    error=None,
):
    return OutcomeEvaluationResult(
        provider_id="stub-outcome",
        implementation="stub-engine",
        version="1",
        method=method,
        status=status,
        declarer=declarer,
        strain=strain,
        opening_lead=None,
        declarer_tricks=tricks,
        sample_count=sample_count,
        elapsed_seconds=0.01,
        error=error,
    )


def test_successful_measurement_is_scored() -> None:
    evaluator = StubOutcomeEvaluator(make_result())
    result = evaluate_contract_outcome(
        evaluator=evaluator,
        deal=generate_deal(6401),
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
    )

    assert result.status is OutcomeEvaluationStatus.SUCCESS
    assert result.outcome is not None
    assert result.declarer_score == 420
    assert result.ns_score == 420
    assert result.outcome.declarer_tricks == 10


def test_contract_fields_are_mapped_to_measurement_request() -> None:
    deal = generate_deal(6402)
    evaluator = StubOutcomeEvaluator(
        make_result(declarer=Seat.SOUTH, strain=None, tricks=9)
    )
    contract = Contract.parse("3NT S")

    evaluate_contract_outcome(
        evaluator=evaluator,
        deal=deal,
        contract=contract,
        vulnerability=Vulnerability.NS,
    )

    assert len(evaluator.requests) == 1
    request = evaluator.requests[0]
    assert request.deal is deal
    assert request.declarer is Seat.SOUTH
    assert request.strain is None
    assert request.opening_lead is None


def test_contract_doubling_is_used_by_scoring() -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(declarer=Seat.EAST, strain=Suit.SPADES, tricks=10)
    )
    result = evaluate_contract_outcome(
        evaluator=evaluator,
        deal=generate_deal(6403),
        contract=Contract.parse("4SX E"),
        vulnerability=Vulnerability.NONE,
    )

    assert result.declarer_score == 590
    assert result.ns_score == -590


@pytest.mark.parametrize(
    "status",
    (
        OutcomeEvaluationStatus.UNAVAILABLE,
        OutcomeEvaluationStatus.FAILED,
    ),
)
def test_non_success_has_no_scored_outcome(status) -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(
            status=status,
            tricks=None,
            error="not available",
        )
    )
    result = evaluate_contract_outcome(
        evaluator=evaluator,
        deal=generate_deal(6404),
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
    )

    assert result.status is status
    assert result.outcome is None
    assert result.declarer_score is None
    assert result.ns_score is None
    assert result.measurement.error == "not available"


def test_fractional_simulation_tricks_are_not_scored_as_a_contract() -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(
            tricks=9.5,
            method=OutcomeEvaluationMethod.SIMULATION,
            sample_count=1000,
        )
    )

    with pytest.raises(
        ValueError,
        match="integer declarer-trick measurement",
    ):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=generate_deal(6405),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_integer_valued_float_measurement_can_be_scored() -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(
            tricks=10.0,
            method=OutcomeEvaluationMethod.SIMULATION,
            sample_count=1000,
        )
    )
    result = evaluate_contract_outcome(
        evaluator=evaluator,
        deal=generate_deal(6406),
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
    )

    assert result.declarer_score == 420


def test_measurement_declarer_must_match_contract() -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(declarer=Seat.SOUTH)
    )

    with pytest.raises(
        ValueError,
        match="measurement declarer does not match contract",
    ):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=generate_deal(6407),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_measurement_strain_must_match_contract() -> None:
    evaluator = StubOutcomeEvaluator(
        make_result(strain=Suit.SPADES)
    )

    with pytest.raises(
        ValueError,
        match="measurement strain does not match contract",
    ):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=generate_deal(6408),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_evaluator_must_return_outcome_result() -> None:
    class BadEvaluator:
        def evaluate(self, request):
            return object()

    with pytest.raises(
        TypeError,
        match="evaluator must return OutcomeEvaluationResult",
    ):
        evaluate_contract_outcome(
            evaluator=BadEvaluator(),
            deal=generate_deal(6409),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_evaluator_requires_callable_evaluate() -> None:
    with pytest.raises(
        TypeError,
        match="evaluator must provide a callable evaluate method",
    ):
        evaluate_contract_outcome(
            evaluator=object(),
            deal=generate_deal(6410),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_invalid_deal_is_rejected() -> None:
    evaluator = StubOutcomeEvaluator(make_result())
    with pytest.raises(TypeError, match="deal must be Deal"):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=object(),
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
        )


def test_invalid_contract_is_rejected() -> None:
    evaluator = StubOutcomeEvaluator(make_result())
    with pytest.raises(TypeError, match="contract must be Contract"):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=generate_deal(6411),
            contract=object(),
            vulnerability=Vulnerability.NONE,
        )


def test_invalid_vulnerability_is_rejected() -> None:
    evaluator = StubOutcomeEvaluator(make_result())
    with pytest.raises(TypeError, match="vulnerability must be Vulnerability"):
        evaluate_contract_outcome(
            evaluator=evaluator,
            deal=generate_deal(6412),
            contract=Contract.parse("4H N"),
            vulnerability="NONE",
        )
