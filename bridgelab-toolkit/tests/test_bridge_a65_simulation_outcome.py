"""A6.5 simulation outcome aggregation tests."""

import pytest

from bridge.auction import Contract
from bridge.corpus import Vulnerability
from bridge.simulation_outcome import summarize_simulation_outcomes


def test_each_sample_is_scored_before_aggregation() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9, 10, 11),
    )

    # Scores are -50, 420, 450. The mean is therefore 820 / 3.
    assert tuple(o.declarer_score for o in summary.outcomes) == (-50, 420, 450)
    assert summary.mean_declarer_score == pytest.approx(820 / 3)
    assert summary.median_declarer_score == 420.0


def test_make_and_down_probabilities() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4S N"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(8, 9, 10, 10, 11),
    )

    assert summary.sample_count == 5
    assert summary.make_count == 3
    assert summary.down_count == 2
    assert summary.make_probability == pytest.approx(0.6)
    assert summary.down_probability == pytest.approx(0.4)
    assert summary.contract_probability == summary.make_probability


def test_all_made_distribution() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("3NT S"),
        vulnerability=Vulnerability.NS,
        declarer_tricks=(9, 10, 11),
    )

    assert summary.make_probability == 1.0
    assert summary.down_probability == 0.0
    assert summary.min_declarer_score == 600
    assert summary.max_declarer_score == 660


def test_all_down_distribution() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NS,
        declarer_tricks=(7, 8, 9),
    )

    assert summary.make_probability == 0.0
    assert summary.down_probability == 1.0
    assert summary.max_declarer_score == -100
    assert summary.min_declarer_score == -300


def test_doubled_contract_uses_full_score_distribution() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4SX E"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(8, 9, 10, 11),
    )

    assert tuple(o.declarer_score for o in summary.outcomes) == (
        -300,
        -100,
        590,
        690,
    )
    assert summary.mean_declarer_score == 220.0
    assert summary.median_declarer_score == 245.0


def test_ns_orientation_for_east_west_declarer() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4S E"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9, 10, 11),
    )

    assert tuple(o.ns_score for o in summary.outcomes) == (50, -420, -450)
    assert summary.mean_ns_score == pytest.approx(-820 / 3)
    assert summary.mean_ns_score == pytest.approx(
        -summary.mean_declarer_score
    )
    assert summary.median_ns_score == -420.0


def test_even_sample_median_is_computed_from_scores() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9, 10),
    )

    assert summary.median_declarer_score == 185.0


def test_generator_input_is_supported() -> None:
    samples = (tricks for tricks in (9, 10, 11))
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=samples,
    )

    assert summary.sample_count == 3


def test_empty_simulation_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="simulation requires at least one sample",
    ):
        summarize_simulation_outcomes(
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
            declarer_tricks=(),
        )


@pytest.mark.parametrize("bad_sample", (-1, 14, 9.5, True))
def test_invalid_sample_is_rejected(bad_sample) -> None:
    with pytest.raises(ValueError, match="declarer_tricks"):
        summarize_simulation_outcomes(
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
            declarer_tricks=(10, bad_sample),
        )


def test_non_iterable_samples_are_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="declarer_tricks must be an iterable",
    ):
        summarize_simulation_outcomes(
            contract=Contract.parse("4H N"),
            vulnerability=Vulnerability.NONE,
            declarer_tricks=10,
        )


def test_invalid_contract_is_rejected() -> None:
    with pytest.raises(TypeError, match="contract must be Contract"):
        summarize_simulation_outcomes(
            contract=object(),
            vulnerability=Vulnerability.NONE,
            declarer_tricks=(10,),
        )


def test_invalid_vulnerability_is_rejected() -> None:
    with pytest.raises(TypeError, match="vulnerability must be Vulnerability"):
        summarize_simulation_outcomes(
            contract=Contract.parse("4H N"),
            vulnerability="NONE",
            declarer_tricks=(10,),
        )
