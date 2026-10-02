"""A6.1 system-independent outcome evaluation contract tests."""

import pytest

from bridge.deals import Deal, generate_deal
from bridge.models import Card, Seat, Suit
from bridge.outcome_evaluation import (
    OutcomeEvaluationMethod,
    OutcomeEvaluationRequest,
    OutcomeEvaluationResult,
    OutcomeEvaluationStatus,
)


def make_deal() -> Deal:
    # Use BridgeLab's canonical deterministic deal generator so the fixture
    # is guaranteed to contain all 52 cards exactly once.
    return generate_deal(6101)


def test_request_accepts_suit_contract() -> None:
    deal = make_deal()

    request = OutcomeEvaluationRequest(
        deal=deal,
        declarer=Seat.NORTH,
        strain=Suit.SPADES,
    )

    assert request.deal is deal
    assert request.declarer is Seat.NORTH
    assert request.strain is Suit.SPADES
    assert request.opening_lead is None


def test_request_accepts_notrump_and_opening_lead() -> None:
    request = OutcomeEvaluationRequest(
        deal=make_deal(),
        declarer=Seat.SOUTH,
        strain=None,
        opening_lead=Card.parse("2S"),
    )

    assert request.strain is None
    assert request.opening_lead == Card.parse("2S")


def test_request_rejects_invalid_declarer() -> None:
    with pytest.raises(TypeError, match="declarer must be a Seat"):
        OutcomeEvaluationRequest(
            deal=make_deal(),
            declarer="N",  # type: ignore[arg-type]
            strain=Suit.HEARTS,
        )


def test_successful_double_dummy_result_accepts_integer_tricks() -> None:
    result = OutcomeEvaluationResult(
        provider_id="legacy-trick-solver",
        implementation="test-dds",
        version="1",
        method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
        status=OutcomeEvaluationStatus.SUCCESS,
        declarer=Seat.NORTH,
        strain=Suit.SPADES,
        opening_lead=None,
        declarer_tricks=10,
        sample_count=None,
        elapsed_seconds=0.01,
    )

    assert result.declarer_tricks == 10
    assert result.sample_count is None


def test_double_dummy_rejects_fractional_tricks() -> None:
    with pytest.raises(
        ValueError,
        match="double-dummy declarer tricks must be an integer",
    ):
        OutcomeEvaluationResult(
            provider_id="dds",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=OutcomeEvaluationStatus.SUCCESS,
            declarer=Seat.NORTH,
            strain=Suit.HEARTS,
            opening_lead=None,
            declarer_tricks=9.5,
            sample_count=None,
            elapsed_seconds=0.0,
        )


def test_double_dummy_rejects_sample_count() -> None:
    with pytest.raises(
        ValueError,
        match="double-dummy outcome result must not contain sample_count",
    ):
        OutcomeEvaluationResult(
            provider_id="dds",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=OutcomeEvaluationStatus.SUCCESS,
            declarer=Seat.NORTH,
            strain=Suit.HEARTS,
            opening_lead=None,
            declarer_tricks=9,
            sample_count=100,
            elapsed_seconds=0.0,
        )


def test_successful_simulation_accepts_expected_fractional_tricks() -> None:
    result = OutcomeEvaluationResult(
        provider_id="simulation",
        implementation="monte-carlo",
        version="1",
        method=OutcomeEvaluationMethod.SIMULATION,
        status=OutcomeEvaluationStatus.SUCCESS,
        declarer=Seat.SOUTH,
        strain=None,
        opening_lead=None,
        declarer_tricks=8.37,
        sample_count=10000,
        elapsed_seconds=1.25,
    )

    assert result.declarer_tricks == pytest.approx(8.37)
    assert result.sample_count == 10000


def test_simulation_rejects_nonpositive_sample_count() -> None:
    with pytest.raises(ValueError, match="sample_count must be a positive integer"):
        OutcomeEvaluationResult(
            provider_id="simulation",
            implementation="monte-carlo",
            version=None,
            method=OutcomeEvaluationMethod.SIMULATION,
            status=OutcomeEvaluationStatus.SUCCESS,
            declarer=Seat.SOUTH,
            strain=None,
            opening_lead=None,
            declarer_tricks=8.0,
            sample_count=0,
            elapsed_seconds=0.0,
        )


@pytest.mark.parametrize(
    "status",
    (
        OutcomeEvaluationStatus.UNAVAILABLE,
        OutcomeEvaluationStatus.FAILED,
    ),
)
def test_non_success_result_must_not_contain_tricks(status) -> None:
    with pytest.raises(
        ValueError,
        match="failed/unavailable outcome result must not contain tricks",
    ):
        OutcomeEvaluationResult(
            provider_id="dds",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=status,
            declarer=Seat.NORTH,
            strain=Suit.CLUBS,
            opening_lead=None,
            declarer_tricks=7,
            sample_count=None,
            elapsed_seconds=0.0,
        )


def test_unavailable_result_is_explicit() -> None:
    result = OutcomeEvaluationResult(
        provider_id="dds",
        implementation="test-dds",
        version=None,
        method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
        status=OutcomeEvaluationStatus.UNAVAILABLE,
        declarer=Seat.NORTH,
        strain=Suit.CLUBS,
        opening_lead=None,
        declarer_tricks=None,
        sample_count=None,
        elapsed_seconds=0.0,
        error="DDS library is not installed",
    )

    assert result.status is OutcomeEvaluationStatus.UNAVAILABLE
    assert result.declarer_tricks is None
    assert result.error == "DDS library is not installed"


def test_failed_result_is_explicit() -> None:
    result = OutcomeEvaluationResult(
        provider_id="simulation",
        implementation="monte-carlo",
        version="1",
        method=OutcomeEvaluationMethod.SIMULATION,
        status=OutcomeEvaluationStatus.FAILED,
        declarer=Seat.EAST,
        strain=Suit.DIAMONDS,
        opening_lead=None,
        declarer_tricks=None,
        sample_count=None,
        elapsed_seconds=0.2,
        error="evaluation failed",
    )

    assert result.status is OutcomeEvaluationStatus.FAILED
    assert result.error == "evaluation failed"


def test_successful_result_rejects_tricks_outside_bridge_range() -> None:
    with pytest.raises(
        ValueError,
        match="successful outcome result needs 0..13 declarer tricks",
    ):
        OutcomeEvaluationResult(
            provider_id="dds",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=OutcomeEvaluationStatus.SUCCESS,
            declarer=Seat.NORTH,
            strain=Suit.SPADES,
            opening_lead=None,
            declarer_tricks=14,
            sample_count=None,
            elapsed_seconds=0.0,
        )


def test_result_rejects_negative_elapsed_time() -> None:
    with pytest.raises(ValueError, match="elapsed_seconds must be non-negative"):
        OutcomeEvaluationResult(
            provider_id="dds",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=OutcomeEvaluationStatus.UNAVAILABLE,
            declarer=Seat.NORTH,
            strain=Suit.SPADES,
            opening_lead=None,
            declarer_tricks=None,
            sample_count=None,
            elapsed_seconds=-0.1,
        )


def test_result_requires_nonblank_provider_id() -> None:
    with pytest.raises(ValueError, match="provider_id must be a non-blank string"):
        OutcomeEvaluationResult(
            provider_id=" ",
            implementation="test-dds",
            version=None,
            method=OutcomeEvaluationMethod.DOUBLE_DUMMY,
            status=OutcomeEvaluationStatus.UNAVAILABLE,
            declarer=Seat.NORTH,
            strain=Suit.SPADES,
            opening_lead=None,
            declarer_tricks=None,
            sample_count=None,
            elapsed_seconds=0.0,
        )
