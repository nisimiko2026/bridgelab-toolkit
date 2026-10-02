"""A6.13 IMP / matchpoint outcome conversion tests."""

import pytest

from bridge.outcome_conversion import (
    IMPOutcomeMeasurement,
    MatchpointOutcomeMeasurement,
    OutcomeComparisonMethod,
    measure_imps,
    measure_matchpoints,
    score_difference_to_imps,
)


@pytest.mark.parametrize(
    ("difference", "expected"),
    (
        (0, 0),
        (10, 0),
        (20, 1),
        (40, 1),
        (50, 2),
        (80, 2),
        (90, 3),
        (120, 3),
        (130, 4),
        (160, 4),
        (170, 5),
        (210, 5),
        (220, 6),
        (260, 6),
        (270, 7),
        (310, 7),
        (320, 8),
        (360, 8),
        (370, 9),
        (420, 9),
        (430, 10),
        (490, 10),
        (500, 11),
        (590, 11),
        (600, 12),
        (740, 12),
        (750, 13),
        (890, 13),
        (900, 14),
        (1090, 14),
        (1100, 15),
        (1290, 15),
        (1300, 16),
        (1490, 16),
        (1500, 17),
        (1740, 17),
        (1750, 18),
        (1990, 18),
        (2000, 19),
        (2240, 19),
        (2250, 20),
        (2490, 20),
        (2500, 21),
        (2990, 21),
        (3000, 22),
        (3490, 22),
        (3500, 23),
        (3990, 23),
        (4000, 24),
        (6000, 24),
    ),
)
def test_imp_thresholds_positive(difference, expected) -> None:
    assert score_difference_to_imps(difference) == expected


@pytest.mark.parametrize(
    ("difference", "expected"),
    (
        (-10, 0),
        (-20, -1),
        (-50, -2),
        (-90, -3),
        (-430, -10),
        (-750, -13),
        (-1500, -17),
        (-2500, -21),
        (-4000, -24),
        (-6000, -24),
    ),
)
def test_imp_thresholds_negative(difference, expected) -> None:
    assert score_difference_to_imps(difference) == expected


def test_measure_imps_uses_fixed_ns_perspective() -> None:
    result = measure_imps(ns_score=620, reference_ns_score=170)

    assert isinstance(result, IMPOutcomeMeasurement)
    assert result.method is OutcomeComparisonMethod.IMP
    assert result.ns_score == 620
    assert result.reference_ns_score == 170
    assert result.score_difference == 450
    assert result.imps == 10


def test_measure_imps_negative_difference() -> None:
    result = measure_imps(ns_score=-100, reference_ns_score=620)
    assert result.score_difference == -720
    assert result.imps == -12


def test_measure_imps_equal_scores() -> None:
    result = measure_imps(ns_score=420, reference_ns_score=420)
    assert result.score_difference == 0
    assert result.imps == 0


def test_imp_measurement_serializes() -> None:
    payload = measure_imps(ns_score=620, reference_ns_score=170).as_dict()

    assert payload == {
        "method": "imp",
        "ns_score": 620,
        "reference_ns_score": 170,
        "score_difference": 450,
        "imps": 10,
    }


def test_matchpoints_counts_wins_ties_and_losses() -> None:
    result = measure_matchpoints(
        ns_score=420,
        comparison_ns_scores=(170, 420, 430, -50),
    )

    assert isinstance(result, MatchpointOutcomeMeasurement)
    assert result.method is OutcomeComparisonMethod.MATCHPOINT
    assert result.comparisons == 4
    assert result.wins == 2
    assert result.ties == 1
    assert result.matchpoints == 5.0
    assert result.top == 8
    assert result.percentage == 62.5


def test_matchpoints_all_wins_is_100_percent() -> None:
    result = measure_matchpoints(
        ns_score=620,
        comparison_ns_scores=(600, 170, -100),
    )
    assert result.matchpoints == 6.0
    assert result.top == 6
    assert result.percentage == 100.0


def test_matchpoints_all_losses_is_zero_percent() -> None:
    result = measure_matchpoints(
        ns_score=-200,
        comparison_ns_scores=(-100, 0, 420),
    )
    assert result.matchpoints == 0.0
    assert result.percentage == 0.0


def test_matchpoints_all_ties_is_50_percent() -> None:
    result = measure_matchpoints(
        ns_score=420,
        comparison_ns_scores=(420, 420, 420),
    )
    assert result.matchpoints == 3.0
    assert result.top == 6
    assert result.percentage == 50.0


def test_matchpoints_accept_generator_field() -> None:
    result = measure_matchpoints(
        ns_score=100,
        comparison_ns_scores=(score for score in (90, 100, 110)),
    )
    assert result.comparison_ns_scores == (90, 100, 110)
    assert result.matchpoints == 3.0
    assert result.percentage == 50.0


def test_matchpoint_measurement_serializes_field_as_list() -> None:
    payload = measure_matchpoints(
        ns_score=100,
        comparison_ns_scores=(90, 100, 110),
    ).as_dict()

    assert payload == {
        "method": "matchpoint",
        "ns_score": 100,
        "comparison_ns_scores": [90, 100, 110],
        "comparisons": 3,
        "wins": 1,
        "ties": 1,
        "matchpoints": 3.0,
        "top": 6,
        "percentage": 50.0,
    }


def test_matchpoints_require_comparison_scores() -> None:
    with pytest.raises(
        ValueError,
        match="matchpoint measurement requires comparison scores",
    ):
        measure_matchpoints(ns_score=420, comparison_ns_scores=())


def test_matchpoints_reject_non_iterable_field() -> None:
    with pytest.raises(
        TypeError,
        match="comparison_ns_scores must be an iterable",
    ):
        measure_matchpoints(ns_score=420, comparison_ns_scores=123)


@pytest.mark.parametrize("value", (1.5, True, "420", None))
def test_imp_conversion_rejects_non_integer_difference(value) -> None:
    with pytest.raises(
        TypeError,
        match="score_difference must be an integer duplicate score",
    ):
        score_difference_to_imps(value)


@pytest.mark.parametrize("value", (1.5, True, "420", None))
def test_measure_imps_rejects_invalid_ns_score(value) -> None:
    with pytest.raises(
        TypeError,
        match="ns_score must be an integer duplicate score",
    ):
        measure_imps(ns_score=value, reference_ns_score=0)


@pytest.mark.parametrize("value", (1.5, True, "420", None))
def test_measure_imps_rejects_invalid_reference_score(value) -> None:
    with pytest.raises(
        TypeError,
        match="reference_ns_score must be an integer duplicate score",
    ):
        measure_imps(ns_score=0, reference_ns_score=value)


@pytest.mark.parametrize("value", (1.5, True, "420", None))
def test_matchpoints_reject_invalid_ns_score(value) -> None:
    with pytest.raises(
        TypeError,
        match="ns_score must be an integer duplicate score",
    ):
        measure_matchpoints(ns_score=value, comparison_ns_scores=(0,))


@pytest.mark.parametrize("value", (1.5, True, "420", None))
def test_matchpoints_reject_invalid_field_score(value) -> None:
    with pytest.raises(
        TypeError,
        match="comparison score must be an integer duplicate score",
    ):
        measure_matchpoints(ns_score=0, comparison_ns_scores=(value,))


def test_conversion_surface_has_no_winner_ranking_or_recommendation() -> None:
    imp = measure_imps(ns_score=620, reference_ns_score=170)
    mp = measure_matchpoints(
        ns_score=420,
        comparison_ns_scores=(170, 420, 430),
    )

    for measurement in (imp, mp):
        for name in (
            "winner",
            "best",
            "rank",
            "ranking",
            "recommended",
            "recommendation",
            "policy",
        ):
            assert not hasattr(measurement, name)
