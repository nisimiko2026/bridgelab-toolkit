"""A6.8 outcome evidence report tests."""

from bridge.auction import Bid, Contract, Strain
from bridge.capability_providers import Capability, ProviderDescriptor
from bridge.decision_case import DecisionCase
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Suit, Vulnerability
from bridge.outcome_evidence_report import build_outcome_evidence_report
from bridge.simulation_outcome import summarize_simulation_outcomes
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def make_dd(
    *,
    provider_id: str = "dds-test",
    tricks: int = 10,
) -> DoubleDummyEvidence:
    provider = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.DOUBLE_DUMMY,
        implementation="dds-test",
        version="1",
    )
    result = TrickSolverResult(
        implementation="dds-test",
        version="1",
        deal_id="deal-1",
        declarer=Seat.NORTH,
        strain=Suit.SPADES,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=tricks,
        elapsed_seconds=0.01,
    )
    return DoubleDummyEvidence(provider=provider, result=result)


def make_outcome_summary():
    contract = Contract(
        bid=Bid(level=4, strain=Strain.SPADES),
        declarer=Seat.NORTH,
    )
    return summarize_simulation_outcomes(
        contract=contract,
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9, 10, 10, 11),
    )


def make_auction_statistics() -> SimulationStatistics:
    return SimulationStatistics(
        runs=10,
        completed=8,
        abstained=1,
        max_steps=1,
        total_calls_added=20,
        max_calls_added=4,
        stop_reason_counts=(
            ("auction-complete", 8),
            ("max-steps", 1),
            ("no-recommendation", 1),
        ),
        stopped_seat_counts=(("N", 1),),
    )


def test_empty_case_report() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(case_id="case-1")
    )

    assert report.case_id == "case-1"
    assert report.total == 0
    assert report.double_dummy_total == 0
    assert report.outcome_simulation_total == 0
    assert report.double_dummy == ()
    assert report.outcome_simulations == ()


def test_double_dummy_entry_is_reported() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            double_dummy=(make_dd(),),
        )
    )

    assert report.total == 1
    entry = report.double_dummy[0]
    assert entry.provider_id == "dds-test"
    assert entry.implementation == "dds-test"
    assert entry.version == "1"
    assert entry.status == "success"
    assert entry.deal_id == "deal-1"
    assert entry.declarer == "N"
    assert entry.strain == "S"
    assert entry.maximum_declarer_tricks == 10


def test_outcome_simulation_entry_is_reported() -> None:
    summary = make_outcome_summary()
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            outcome_simulations=(summary,),
        )
    )

    assert report.total == 1
    entry = report.outcome_simulations[0]
    assert entry.contract == "4S"
    assert entry.declarer == "N"
    assert entry.sample_count == 4
    assert entry.mean_declarer_score == summary.mean_declarer_score
    assert entry.mean_ns_score == summary.mean_ns_score
    assert entry.make_probability == summary.make_probability
    assert entry.down_probability == summary.down_probability


def test_report_combines_dds_and_outcome_simulations() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            double_dummy=(make_dd(), make_dd(provider_id="dds-2")),
            outcome_simulations=(make_outcome_summary(),),
        )
    )

    assert report.total == 3
    assert report.double_dummy_total == 2
    assert report.outcome_simulation_total == 1


def test_auction_simulation_statistics_are_not_outcome_report_entries() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            simulations=(make_auction_statistics(),),
        )
    )

    assert report.total == 0
    assert report.double_dummy == ()
    assert report.outcome_simulations == ()


def test_report_preserves_source_order() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            double_dummy=(
                make_dd(provider_id="first"),
                make_dd(provider_id="second"),
            ),
        )
    )

    assert tuple(x.provider_id for x in report.double_dummy) == (
        "first",
        "second",
    )


def test_as_dict_is_json_friendly_shape() -> None:
    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            double_dummy=(make_dd(),),
            outcome_simulations=(make_outcome_summary(),),
        )
    )

    data = report.as_dict()

    assert data["case_id"] == "case-1"
    assert data["total"] == 2
    assert data["double_dummy_total"] == 1
    assert data["outcome_simulation_total"] == 1
    assert isinstance(data["double_dummy"], list)
    assert isinstance(data["outcome_simulations"], list)
    assert data["double_dummy"][0]["provider_id"] == "dds-test"
    assert data["outcome_simulations"][0]["contract"] == "4S"


def test_as_dict_contains_no_winner_or_ranking_fields() -> None:
    data = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            double_dummy=(make_dd(),),
            outcome_simulations=(make_outcome_summary(),),
        )
    ).as_dict()

    forbidden = {
        "winner",
        "best",
        "ranking",
        "rank",
        "recommended",
        "recommendation",
    }
    assert forbidden.isdisjoint(data)
    assert forbidden.isdisjoint(data["double_dummy"][0])
    assert forbidden.isdisjoint(data["outcome_simulations"][0])


def test_build_report_rejects_non_decision_case() -> None:
    import pytest

    with pytest.raises(TypeError, match="case must be DecisionCase"):
        build_outcome_evidence_report(object())


def test_report_does_not_mutate_case() -> None:
    case = DecisionCase(
        case_id="case-1",
        double_dummy=(make_dd(),),
        outcome_simulations=(make_outcome_summary(),),
        notes=("keep",),
    )

    before = case
    build_outcome_evidence_report(case)

    assert case == before
    assert case.notes == ("keep",)


def test_multiple_outcome_summaries_preserve_order() -> None:
    first = make_outcome_summary()
    second = make_outcome_summary()

    report = build_outcome_evidence_report(
        DecisionCase(
            case_id="case-1",
            outcome_simulations=(first, second),
        )
    )

    assert report.outcome_simulation_total == 2
    assert report.outcome_simulations[0].sample_count == first.sample_count
    assert report.outcome_simulations[1].sample_count == second.sample_count
