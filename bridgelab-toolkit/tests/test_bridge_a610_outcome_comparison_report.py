"""A6.10 outcome comparison report tests."""

import pytest

from bridge.auction import Bid, Contract, Doubling, Strain
from bridge.contract_alternative_evaluation import (
    ContractAlternative,
    evaluate_contract_alternatives,
)
from bridge.deals import generate_deal
from bridge.models import Seat, Vulnerability
from bridge.outcome_comparison_report import (
    OutcomeComparisonReport,
    OutcomeComparisonReportRow,
    build_outcome_comparison_report,
)


def _contract(
    level: int,
    strain: Strain,
    declarer: Seat = Seat.NORTH,
    doubling: Doubling = Doubling.UNDOUBLED,
) -> Contract:
    return Contract(Bid(level, strain), declarer, doubling)


def _pipeline_result():
    return evaluate_contract_alternatives(
        deal=generate_deal(610),
        vulnerability=Vulnerability.NONE,
        alternatives=(
            ContractAlternative("3NT-line", _contract(3, Strain.NOTRUMP)),
            ContractAlternative("4S-line", _contract(4, Strain.SPADES)),
        ),
        declarer_tricks={
            "3NT-line": (8, 9, 9, 10),
            "4S-line": (9, 10, 10, 11),
        },
    )


def test_build_report_returns_expected_type_and_total() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    assert isinstance(report, OutcomeComparisonReport)
    assert report.total == 2


def test_report_preserves_alternative_order() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    assert tuple(row.alternative_id for row in report.rows) == (
        "3NT-line",
        "4S-line",
    )


def test_report_exposes_contract_declarer_and_vulnerability() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    first = report.row("3NT-line")
    assert first.contract == "3NT"
    assert first.declarer == Seat.NORTH.value
    assert first.vulnerability == Vulnerability.NONE.value


def test_report_exposes_simulation_statistics() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    row = report.row("4S-line")
    summary = _pipeline_result().evaluation("4S-line").summary

    assert row.sample_count == summary.sample_count
    assert row.mean_declarer_score == summary.mean_declarer_score
    assert row.median_declarer_score == summary.median_declarer_score
    assert row.mean_ns_score == summary.mean_ns_score
    assert row.median_ns_score == summary.median_ns_score
    assert row.make_probability == summary.make_probability
    assert row.down_probability == summary.down_probability
    assert row.min_declarer_score == summary.min_declarer_score
    assert row.max_declarer_score == summary.max_declarer_score


def test_report_exposes_ns_score_range_from_comparison() -> None:
    result = _pipeline_result()
    report = build_outcome_comparison_report(result)
    source = result.comparison.row("3NT-line")
    row = report.row("3NT-line")

    assert row.min_ns_score == source.min_ns_score
    assert row.max_ns_score == source.max_ns_score


def test_report_preserves_sample_count_metadata() -> None:
    result = evaluate_contract_alternatives(
        deal=generate_deal(611),
        vulnerability=Vulnerability.NONE,
        alternatives=(
            ContractAlternative("a", _contract(2, Strain.HEARTS)),
            ContractAlternative("b", _contract(3, Strain.NOTRUMP)),
        ),
        declarer_tricks={
            "a": (8, 9),
            "b": (8, 9, 10),
        },
    )
    report = build_outcome_comparison_report(result)

    assert report.min_sample_count == 2
    assert report.max_sample_count == 3
    assert report.equal_sample_counts is False


@pytest.mark.parametrize(
    ("doubling", "expected"),
    (
        (Doubling.UNDOUBLED, "4S"),
        (Doubling.DOUBLED, "4SX"),
        (Doubling.REDOUBLED, "4SXX"),
    ),
)
def test_contract_text_preserves_doubling(doubling, expected) -> None:
    result = evaluate_contract_alternatives(
        deal=generate_deal(612),
        vulnerability=Vulnerability.NONE,
        alternatives=(
            ContractAlternative(
                "tested",
                _contract(4, Strain.SPADES, doubling=doubling),
            ),
            ContractAlternative("other", _contract(3, Strain.NOTRUMP)),
        ),
        declarer_tricks={
            "tested": (10,),
            "other": (9,),
        },
    )
    report = build_outcome_comparison_report(result)
    assert report.row("tested").contract == expected


def test_report_row_lookup_missing_id_raises_key_error() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    with pytest.raises(KeyError):
        report.row("missing")


def test_report_as_dict_is_json_friendly_shape() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    payload = report.as_dict()

    assert payload["total"] == 2
    assert payload["min_sample_count"] == 4
    assert payload["max_sample_count"] == 4
    assert payload["equal_sample_counts"] is True
    assert isinstance(payload["rows"], list)
    assert payload["rows"][0]["alternative_id"] == "3NT-line"
    assert payload["rows"][0]["contract"] == "3NT"


def test_report_row_as_dict_contains_all_descriptive_fields() -> None:
    row = build_outcome_comparison_report(_pipeline_result()).row("3NT-line")
    payload = row.as_dict()

    assert set(payload) == {
        "alternative_id",
        "contract",
        "declarer",
        "vulnerability",
        "sample_count",
        "mean_declarer_score",
        "median_declarer_score",
        "mean_ns_score",
        "median_ns_score",
        "make_probability",
        "down_probability",
        "min_declarer_score",
        "max_declarer_score",
        "min_ns_score",
        "max_ns_score",
    }


def test_builder_rejects_wrong_result_type() -> None:
    with pytest.raises(
        TypeError,
        match="result must be ContractAlternativeEvaluationPipelineResult",
    ):
        build_outcome_comparison_report(object())


def test_report_does_not_expose_winner_ranking_or_recommendation() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    forbidden = (
        "winner",
        "best",
        "ranking",
        "rank",
        "recommended",
        "recommendation",
    )
    for name in forbidden:
        assert not hasattr(report, name)
        assert not hasattr(report.rows[0], name)


def test_report_keeps_fixed_ns_perspective_for_east_declarer() -> None:
    result = evaluate_contract_alternatives(
        deal=generate_deal(613),
        vulnerability=Vulnerability.NONE,
        alternatives=(
            ContractAlternative(
                "north",
                _contract(2, Strain.SPADES, Seat.NORTH),
            ),
            ContractAlternative(
                "east",
                _contract(2, Strain.SPADES, Seat.EAST),
            ),
        ),
        declarer_tricks={
            "north": (8,),
            "east": (8,),
        },
    )
    report = build_outcome_comparison_report(result)

    assert report.row("north").mean_ns_score > 0
    assert report.row("east").mean_ns_score < 0


def test_report_row_is_immutable() -> None:
    row = build_outcome_comparison_report(_pipeline_result()).rows[0]
    with pytest.raises(Exception):
        row.sample_count = 999


def test_report_is_immutable() -> None:
    report = build_outcome_comparison_report(_pipeline_result())
    with pytest.raises(Exception):
        report.rows = ()


def test_report_row_dataclass_accepts_complete_descriptive_record() -> None:
    row = OutcomeComparisonReportRow(
        alternative_id="x",
        contract="3NT",
        declarer=Seat.NORTH.value,
        vulnerability=Vulnerability.NONE.value,
        sample_count=1,
        mean_declarer_score=400.0,
        median_declarer_score=400.0,
        mean_ns_score=400.0,
        median_ns_score=400.0,
        make_probability=1.0,
        down_probability=0.0,
        min_declarer_score=400,
        max_declarer_score=400,
        min_ns_score=400,
        max_ns_score=400,
    )
    assert row.as_dict()["contract"] == "3NT"
