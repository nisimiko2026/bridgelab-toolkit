"""A6.12 simulation provider boundary tests."""

import pytest

from bridge.auction import Bid, Contract, Strain
from bridge.contract_alternative_evaluation import (
    ContractAlternative,
    evaluate_contract_alternatives,
)
from bridge.corpus import Vulnerability
from bridge.deals import generate_deal
from bridge.models import Seat
from bridge.simulation_outcome import summarize_simulation_outcomes
from bridge.simulation_provider import (
    LiveSimulationProvider,
    SimulationSampleRequest,
    SimulationSampleResult,
    SimulationSampleStatus,
)


def _deal():
    return generate_deal(6120)


def _contract(
    level: int = 4,
    strain: Strain = Strain.SPADES,
    declarer: Seat = Seat.NORTH,
) -> Contract:
    return Contract(Bid(level, strain), declarer)


def _request(sample_count: int = 4) -> SimulationSampleRequest:
    return SimulationSampleRequest(
        deal=_deal(),
        contract=_contract(),
        sample_count=sample_count,
    )


def test_request_accepts_valid_context() -> None:
    request = _request(3)
    assert request.sample_count == 3
    assert isinstance(request.contract, Contract)


def test_request_rejects_invalid_deal() -> None:
    with pytest.raises(TypeError, match="deal must be Deal"):
        SimulationSampleRequest(object(), _contract(), 3)


def test_request_rejects_invalid_contract() -> None:
    with pytest.raises(TypeError, match="contract must be Contract"):
        SimulationSampleRequest(_deal(), object(), 3)


@pytest.mark.parametrize("value", (0, -1, 1.5, True))
def test_request_rejects_invalid_sample_count(value) -> None:
    with pytest.raises(ValueError, match="sample_count must be a positive integer"):
        SimulationSampleRequest(_deal(), _contract(), value)


def test_live_provider_success_preserves_raw_samples() -> None:
    provider = LiveSimulationProvider(
        lambda deal, contract, count: (9, 10, 11, 10),
        provider_id="sim-x",
        implementation="monte-carlo-x",
        version="1.2",
    )
    result = provider.sample(_request(4))

    assert isinstance(result, SimulationSampleResult)
    assert result.status is SimulationSampleStatus.SUCCESS
    assert result.declarer_tricks == (9, 10, 11, 10)
    assert result.requested_sample_count == 4
    assert result.provider_id == "sim-x"
    assert result.implementation == "monte-carlo-x"
    assert result.version == "1.2"
    assert result.elapsed_seconds >= 0
    assert result.error is None


def test_provider_receives_exact_context() -> None:
    request = _request(3)
    seen = {}

    def sample(deal, contract, count):
        seen.update(deal=deal, contract=contract, count=count)
        return (8, 9, 10)

    LiveSimulationProvider(sample).sample(request)

    assert seen == {
        "deal": request.deal,
        "contract": request.contract,
        "count": 3,
    }


def test_provider_accepts_generator_output() -> None:
    def sample(deal, contract, count):
        return (9 + (i % 2) for i in range(count))

    result = LiveSimulationProvider(sample).sample(_request(5))
    assert result.status is SimulationSampleStatus.SUCCESS
    assert result.declarer_tricks == (9, 10, 9, 10, 9)


def test_unavailable_provider_returns_no_samples() -> None:
    result = LiveSimulationProvider(None).sample(_request(4))

    assert result.status is SimulationSampleStatus.UNAVAILABLE
    assert result.declarer_tricks == ()
    assert result.elapsed_seconds == 0.0
    assert result.error == "simulation implementation is unavailable"


def test_provider_exception_becomes_failed_without_samples() -> None:
    def explode(deal, contract, count):
        raise RuntimeError("simulation failed")

    result = LiveSimulationProvider(explode).sample(_request(4))

    assert result.status is SimulationSampleStatus.FAILED
    assert result.declarer_tricks == ()
    assert result.elapsed_seconds >= 0
    assert result.error == "RuntimeError: simulation failed"


@pytest.mark.parametrize(
    "samples",
    (
        (9, 10, 11),
        (9, 10, 11, 12, 13),
        (9, 10, 14, 10),
        (9, 10, -1, 10),
        (9, 10, 9.5, 10),
        (9, 10, True, 10),
    ),
)
def test_invalid_provider_samples_become_failed(samples) -> None:
    result = LiveSimulationProvider(
        lambda deal, contract, count: samples
    ).sample(_request(4))

    assert result.status is SimulationSampleStatus.FAILED
    assert result.declarer_tricks == ()
    assert result.error == "simulation implementation returned invalid samples"


def test_non_iterable_provider_output_becomes_failed() -> None:
    result = LiveSimulationProvider(
        lambda deal, contract, count: 10
    ).sample(_request(4))

    assert result.status is SimulationSampleStatus.FAILED
    assert result.declarer_tricks == ()
    assert result.error.startswith("TypeError:")


def test_raw_samples_feed_a65_without_scoring_average_tricks() -> None:
    provider_result = LiveSimulationProvider(
        lambda deal, contract, count: (9, 10, 11, 10)
    ).sample(_request(4))

    summary = summarize_simulation_outcomes(
        contract=provider_result.contract,
        vulnerability=Vulnerability.NONE,
        declarer_tricks=provider_result.declarer_tricks,
    )

    assert summary.sample_count == 4
    assert len(summary.outcomes) == 4
    assert tuple(
        outcome.declarer_tricks for outcome in summary.outcomes
    ) == (9, 10, 11, 10)


def test_two_provider_results_feed_a69_pipeline() -> None:
    deal = _deal()
    alternatives = (
        ContractAlternative("3NT", _contract(3, Strain.NOTRUMP)),
        ContractAlternative("4S", _contract(4, Strain.SPADES)),
    )
    provider = LiveSimulationProvider(
        lambda deal_arg, contract, count: (
            (8, 9, 9, 10)
            if contract.bid.strain is Strain.NOTRUMP
            else (9, 10, 10, 11)
        )
    )

    samples = {}
    for alternative in alternatives:
        result = provider.sample(
            SimulationSampleRequest(
                deal=deal,
                contract=alternative.contract,
                sample_count=4,
            )
        )
        assert result.status is SimulationSampleStatus.SUCCESS
        samples[alternative.alternative_id] = result.declarer_tricks

    pipeline = evaluate_contract_alternatives(
        deal=deal,
        vulnerability=Vulnerability.NONE,
        alternatives=alternatives,
        declarer_tricks=samples,
    )

    assert tuple(
        item.alternative_id for item in pipeline.evaluations
    ) == ("3NT", "4S")
    assert pipeline.evaluation("3NT").summary.sample_count == 4
    assert pipeline.evaluation("4S").summary.sample_count == 4


def test_result_rejects_samples_for_unavailable_status() -> None:
    with pytest.raises(
        ValueError,
        match="failed/unavailable simulation result must not contain samples",
    ):
        SimulationSampleResult(
            provider_id="x",
            implementation="x",
            version=None,
            status=SimulationSampleStatus.UNAVAILABLE,
            contract=_contract(),
            requested_sample_count=1,
            declarer_tricks=(9,),
            elapsed_seconds=0.0,
        )


def test_result_rejects_wrong_success_sample_count() -> None:
    with pytest.raises(
        ValueError,
        match="successful simulation must return exactly requested_sample_count samples",
    ):
        SimulationSampleResult(
            provider_id="x",
            implementation="x",
            version=None,
            status=SimulationSampleStatus.SUCCESS,
            contract=_contract(),
            requested_sample_count=2,
            declarer_tricks=(9,),
            elapsed_seconds=0.0,
        )


def test_rejects_non_callable_provider() -> None:
    with pytest.raises(TypeError, match="sample_callable must be callable or None"):
        LiveSimulationProvider(42)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"provider_id": " "}, "provider_id must be a non-blank string"),
        ({"implementation": " "}, "implementation must be a non-blank string"),
        ({"version": " "}, "version must be None or a non-blank string"),
    ),
)
def test_provider_rejects_invalid_metadata(kwargs, message) -> None:
    with pytest.raises(ValueError, match=message):
        LiveSimulationProvider(None, **kwargs)


def test_provider_metadata_is_trimmed() -> None:
    provider = LiveSimulationProvider(
        None,
        provider_id="  sim  ",
        implementation="  mc  ",
        version="  1.0  ",
    )
    assert provider.provider_id == "sim"
    assert provider.implementation == "mc"
    assert provider.version == "1.0"


def test_sample_rejects_wrong_request_type() -> None:
    with pytest.raises(TypeError, match="request must be SimulationSampleRequest"):
        LiveSimulationProvider(None).sample(object())


def test_boundary_has_no_scoring_ranking_or_policy_surface() -> None:
    provider = LiveSimulationProvider(None)
    for name in (
        "score",
        "winner",
        "best",
        "rank",
        "ranking",
        "recommended",
        "recommendation",
        "policy",
    ):
        assert not hasattr(provider, name)
