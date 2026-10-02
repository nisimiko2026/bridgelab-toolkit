"""A6.6 alternative simulation outcome comparison tests."""

import pytest

from bridge.alternative_outcome_comparison import (
    OutcomeAlternative,
    compare_simulation_outcomes,
)
from bridge.auction import Contract
from bridge.corpus import Vulnerability
from bridge.simulation_outcome import summarize_simulation_outcomes


def make_alt(
    alternative_id: str,
    contract_text: str,
    tricks,
    vulnerability=Vulnerability.NONE,
):
    return OutcomeAlternative(
        alternative_id=alternative_id,
        summary=summarize_simulation_outcomes(
            contract=Contract.parse(contract_text),
            vulnerability=vulnerability,
            declarer_tricks=tricks,
        ),
    )


def test_two_alternatives_are_preserved_in_input_order() -> None:
    a = make_alt("3NT", "3NT N", (8, 9, 10))
    b = make_alt("4S", "4S N", (9, 10, 11))

    comparison = compare_simulation_outcomes((a, b))

    assert tuple(row.alternative_id for row in comparison.rows) == (
        "3NT",
        "4S",
    )


def test_rows_expose_descriptive_ns_statistics() -> None:
    a = make_alt("4H", "4H N", (9, 10, 11))
    b = make_alt("3NT", "3NT N", (8, 9, 10))

    comparison = compare_simulation_outcomes((a, b))
    row = comparison.row("4H")

    assert row.sample_count == 3
    assert row.mean_ns_score == pytest.approx(820 / 3)
    assert row.median_ns_score == 420.0
    assert row.make_probability == pytest.approx(2 / 3)
    assert row.down_probability == pytest.approx(1 / 3)
    assert row.min_ns_score == -50
    assert row.max_ns_score == 450


def test_east_west_contract_is_compared_from_ns_perspective() -> None:
    ew = make_alt("EW-4S", "4S E", (9, 10, 11))
    ns = make_alt("NS-4H", "4H N", (9, 10, 11))

    comparison = compare_simulation_outcomes((ew, ns))
    row = comparison.row("EW-4S")

    assert row.mean_ns_score == pytest.approx(-820 / 3)
    assert row.min_ns_score == -450
    assert row.max_ns_score == 50


def test_equal_sample_counts_are_reported() -> None:
    comparison = compare_simulation_outcomes(
        (
            make_alt("A", "4H N", (9, 10, 11)),
            make_alt("B", "3NT N", (8, 9, 10)),
        )
    )

    assert comparison.min_sample_count == 3
    assert comparison.max_sample_count == 3
    assert comparison.equal_sample_counts


def test_unequal_sample_counts_are_reported_without_reweighting() -> None:
    comparison = compare_simulation_outcomes(
        (
            make_alt("A", "4H N", (9, 10)),
            make_alt("B", "3NT N", (8, 9, 10, 10)),
        )
    )

    assert comparison.min_sample_count == 2
    assert comparison.max_sample_count == 4
    assert not comparison.equal_sample_counts
    assert comparison.row("A").sample_count == 2
    assert comparison.row("B").sample_count == 4


def test_three_or_more_alternatives_are_supported() -> None:
    comparison = compare_simulation_outcomes(
        (
            make_alt("A", "2S N", (8, 9)),
            make_alt("B", "3NT N", (9, 10)),
            make_alt("C", "4H N", (10, 11)),
        )
    )

    assert len(comparison.rows) == 3


def test_generator_input_is_supported() -> None:
    alternatives = (
        alt
        for alt in (
            make_alt("A", "2S N", (8,)),
            make_alt("B", "3NT N", (9,)),
        )
    )

    comparison = compare_simulation_outcomes(alternatives)

    assert len(comparison.rows) == 2


def test_row_lookup_unknown_id_raises_key_error() -> None:
    comparison = compare_simulation_outcomes(
        (
            make_alt("A", "2S N", (8,)),
            make_alt("B", "3NT N", (9,)),
        )
    )

    with pytest.raises(KeyError):
        comparison.row("missing")


def test_blank_alternative_id_is_rejected() -> None:
    summary = summarize_simulation_outcomes(
        contract=Contract.parse("4H N"),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(10,),
    )

    with pytest.raises(
        ValueError,
        match="alternative_id must be a non-blank string",
    ):
        OutcomeAlternative(" ", summary)


def test_invalid_summary_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="summary must be SimulationOutcomeSummary",
    ):
        OutcomeAlternative("A", object())


def test_comparison_requires_at_least_two_alternatives() -> None:
    with pytest.raises(
        ValueError,
        match="comparison requires at least two alternatives",
    ):
        compare_simulation_outcomes(
            (make_alt("A", "4H N", (10,)),)
        )


def test_duplicate_alternative_ids_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="alternative_id values must be unique",
    ):
        compare_simulation_outcomes(
            (
                make_alt("A", "4H N", (10,)),
                make_alt("A", "3NT N", (9,)),
            )
        )


def test_non_alternative_item_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="all alternatives must be OutcomeAlternative",
    ):
        compare_simulation_outcomes(
            (
                make_alt("A", "4H N", (10,)),
                object(),
            )
        )


def test_non_iterable_input_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="alternatives must be an iterable",
    ):
        compare_simulation_outcomes(42)


def test_comparison_does_not_expose_a_winner_field() -> None:
    comparison = compare_simulation_outcomes(
        (
            make_alt("A", "4H N", (10, 11)),
            make_alt("B", "3NT N", (9, 10)),
        )
    )

    assert not hasattr(comparison, "winner")
    assert not hasattr(comparison, "best")
    assert not hasattr(comparison, "ranking")
