"""A6.14 end-to-end outcome pipeline integration tests."""

import pytest

from bridge.auction import Bid, Contract, Strain
from bridge.contract_alternative_evaluation import ContractAlternative
from bridge.corpus import Vulnerability
from bridge.deals import generate_deal
from bridge.end_to_end_outcome_pipeline import (
    AlternativeCompetitionMeasurement,
    EndToEndOutcomePipelineResult,
    run_end_to_end_outcome_pipeline,
)
from bridge.models import Seat
from bridge.outcome_comparison_report import OutcomeComparisonReport
from bridge.outcome_conversion import (
    IMPOutcomeMeasurement,
    MatchpointOutcomeMeasurement,
)
from bridge.simulation_provider import LiveSimulationProvider, SimulationSampleStatus


def _deal():
    return generate_deal(6140)


def _contract(level, strain, declarer=Seat.NORTH):
    return Contract(Bid(level, strain), declarer)


def _alternatives():
    return (
        ContractAlternative("3NT", _contract(3, Strain.NOTRUMP)),
        ContractAlternative("4S", _contract(4, Strain.SPADES)),
    )


def _provider():
    def sample(deal, contract, count):
        values = (
            (9, 9, 9, 9)
            if contract.bid.strain is Strain.NOTRUMP
            else (10, 10, 10, 10)
        )
        return values[:count]

    return LiveSimulationProvider(
        sample,
        provider_id="sim-test",
        implementation="deterministic-test",
        version="1.0",
    )


def test_end_to_end_pipeline_composes_all_core_layers() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )

    assert isinstance(result, EndToEndOutcomePipelineResult)
    assert isinstance(result.report, OutcomeComparisonReport)
    assert tuple(row.alternative_id for row in result.report.rows) == ("3NT", "4S")
    assert tuple(item.alternative_id for item in result.evaluation.evaluations) == (
        "3NT",
        "4S",
    )


def test_pipeline_preserves_provider_results_and_raw_samples() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )

    first = result.simulation_result("3NT")
    second = result.simulation_result("4S")
    assert first.status is SimulationSampleStatus.SUCCESS
    assert first.declarer_tricks == (9, 9, 9, 9)
    assert second.declarer_tricks == (10, 10, 10, 10)


def test_pipeline_scores_every_raw_sample_before_aggregation() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )

    for item in result.evaluation.evaluations:
        assert item.summary.sample_count == 4
        assert len(item.summary.outcomes) == 4


def test_pipeline_builds_report_from_same_evaluation() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )

    for evaluation in result.evaluation.evaluations:
        row = result.report.row(evaluation.alternative_id)
        assert row.mean_ns_score == evaluation.summary.mean_ns_score
        assert row.make_probability == evaluation.summary.make_probability


def test_optional_imp_measurement() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
        imp_reference_ns_scores={"3NT": 400, "4S": 420},
    )

    measurement = result.competition_measurement("4S")
    assert isinstance(measurement.imps, IMPOutcomeMeasurement)
    assert measurement.imps.reference_ns_score == 420
    assert measurement.matchpoints is None


def test_optional_matchpoint_measurement() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
        matchpoint_comparison_ns_scores={
            "3NT": (400, 430, 400),
            "4S": (420, 620, 170),
        },
    )

    measurement = result.competition_measurement("3NT")
    assert measurement.imps is None
    assert isinstance(measurement.matchpoints, MatchpointOutcomeMeasurement)
    assert measurement.matchpoints.comparisons == 3


def test_imp_and_matchpoints_can_coexist_for_same_alternative() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
        imp_reference_ns_scores={"3NT": 400},
        matchpoint_comparison_ns_scores={"3NT": (400, 430, 460)},
    )

    measurement = result.competition_measurement("3NT")
    assert isinstance(measurement.imps, IMPOutcomeMeasurement)
    assert isinstance(measurement.matchpoints, MatchpointOutcomeMeasurement)


def test_missing_optional_reference_leaves_measurement_none() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
        imp_reference_ns_scores={"3NT": 400},
    )

    measurement = result.competition_measurement("4S")
    assert measurement.imps is None
    assert measurement.matchpoints is None


def test_pipeline_preserves_alternative_order_everywhere() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=reversed(_alternatives()),
        simulation_provider=_provider(),
        sample_count=4,
    )

    expected = ("4S", "3NT")
    assert tuple(item_id for item_id, _ in result.simulation_results) == expected
    assert tuple(item.alternative_id for item in result.evaluation.evaluations) == expected
    assert tuple(row.alternative_id for row in result.report.rows) == expected
    assert tuple(
        item.alternative_id for item in result.competition_measurements
    ) == expected


def test_unavailable_simulation_stops_pipeline_without_inventing_samples() -> None:
    with pytest.raises(RuntimeError, match="simulation failed for 3NT"):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=LiveSimulationProvider(None),
            sample_count=4,
        )


def test_failed_simulation_stops_pipeline_without_inventing_samples() -> None:
    def explode(deal, contract, count):
        raise RuntimeError("provider exploded")

    with pytest.raises(
        RuntimeError,
        match="simulation failed for 3NT: RuntimeError: provider exploded",
    ):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=LiveSimulationProvider(explode),
            sample_count=4,
        )


def test_generator_alternatives_supported() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=(item for item in _alternatives()),
        simulation_provider=_provider(),
        sample_count=4,
    )
    assert result.report.total == 2


def test_lookup_missing_simulation_id_raises_key_error() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )
    with pytest.raises(KeyError):
        result.simulation_result("missing")


def test_lookup_missing_competition_id_raises_key_error() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )
    with pytest.raises(KeyError):
        result.competition_measurement("missing")


def test_rejects_fewer_than_two_alternatives() -> None:
    with pytest.raises(ValueError, match="pipeline requires at least two alternatives"):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=(_alternatives()[0],),
            simulation_provider=_provider(),
            sample_count=4,
        )


def test_rejects_duplicate_alternative_ids() -> None:
    alternatives = (
        ContractAlternative("same", _contract(3, Strain.NOTRUMP)),
        ContractAlternative("same", _contract(4, Strain.SPADES)),
    )
    with pytest.raises(ValueError, match="alternative_id values must be unique"):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=alternatives,
            simulation_provider=_provider(),
            sample_count=4,
        )


@pytest.mark.parametrize("value", (0, -1, 1.5, True))
def test_rejects_invalid_sample_count(value) -> None:
    with pytest.raises(ValueError, match="sample_count must be a positive integer"):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=_provider(),
            sample_count=value,
        )


def test_rejects_wrong_provider_type() -> None:
    with pytest.raises(
        TypeError,
        match="simulation_provider must be LiveSimulationProvider",
    ):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=object(),
            sample_count=4,
        )


def test_rejects_extra_imp_reference_id() -> None:
    with pytest.raises(
        ValueError,
        match="unexpected alternative ids in imp_reference_ns_scores",
    ):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=_provider(),
            sample_count=4,
            imp_reference_ns_scores={"other": 0},
        )


def test_rejects_extra_matchpoint_reference_id() -> None:
    with pytest.raises(
        ValueError,
        match="unexpected alternative ids in matchpoint_comparison_ns_scores",
    ):
        run_end_to_end_outcome_pipeline(
            deal=_deal(),
            vulnerability=Vulnerability.NONE,
            alternatives=_alternatives(),
            simulation_provider=_provider(),
            sample_count=4,
            matchpoint_comparison_ns_scores={"other": (0,)},
        )


def test_competition_measurement_validates_id() -> None:
    with pytest.raises(ValueError, match="alternative_id must be a non-blank string"):
        AlternativeCompetitionMeasurement(" ")


def test_end_to_end_surface_has_no_winner_ranking_or_recommendation() -> None:
    result = run_end_to_end_outcome_pipeline(
        deal=_deal(),
        vulnerability=Vulnerability.NONE,
        alternatives=_alternatives(),
        simulation_provider=_provider(),
        sample_count=4,
    )
    for obj in (result, result.competition_measurements[0]):
        for name in (
            "winner",
            "best",
            "rank",
            "ranking",
            "recommended",
            "recommendation",
            "policy",
        ):
            assert not hasattr(obj, name)
