"""Focused tests for deterministic production opening-analysis batches."""

from dataclasses import FrozenInstanceError

import pytest

from bridge.deal_analysis import AnalysisStatus
from bridge.deals import Deal, generate_deal
from bridge.full_deal_application import (
    FullDealApplicationError,
    FullDealApplicationErrorCode,
    FullDealApplicationRequest,
    FullDealApplicationResponse,
    analyze_full_deal_application,
)
from bridge.deal_simulator import SimulationConfig, run_simulation
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_deal_integrity_and_canonical_immutable_types():
    deal = generate_deal(12)
    assert isinstance(deal, Deal)
    hands = tuple(deal.hand(seat) for seat in Seat)
    assert len(hands) == 4 and all(isinstance(hand, Hand) for hand in hands)
    assert all(len(hand.cards) == 13 for hand in hands)
    assert len({card for hand in hands for card in hand.cards}) == 52

    case = run_simulation(SimulationConfig(seed=12, deal_count=1)).cases[0]
    assert isinstance(case.dealer, Seat)
    assert isinstance(case.vulnerability, Vulnerability)
    assert case.analyzed_hand == deal.hand(case.dealer).serialize()
    with pytest.raises(FrozenInstanceError):
        case.index = 2


def test_seeded_generation_and_result_records_are_deterministic():
    config = SimulationConfig(seed=23, deal_count=4)
    first = run_simulation(config)
    assert first == run_simulation(config)
    other = run_simulation(SimulationConfig(seed=24, deal_count=4))
    assert first != other
    assert tuple(generate_deal(config.seed + index).serialize() for index in range(4)) != (
        tuple(generate_deal(other.seed + index).serialize() for index in range(4))
    )


def test_default_batch_has_100_completed_opening_analyses():
    report = run_simulation()
    assert report.requested_deals == report.completed_deals == 100
    assert report.recommendations + report.abstains + report.errors == 100
    assert sum(count for _, count in report.call_frequencies) == report.recommendations


def test_configurable_count_and_invalid_counts():
    assert run_simulation(SimulationConfig(deal_count=2)).completed_deals == 2
    for count in (0, -1):
        with pytest.raises(ValueError, match="at least 1"):
            SimulationConfig(deal_count=count)


def test_application_boundary_is_called_once_per_opening_position():
    requests = []

    def counted(request, *, bidding_router):
        assert isinstance(request, FullDealApplicationRequest)
        assert len(bidding_router.routes) == 45
        assert request.requested_stages == ("auction",)
        assert request.bidding.auction.calls == ()
        assert request.bidding.system.system == "SAYC"
        assert request.bidding.system.options == ()
        requests.append(request)
        return analyze_full_deal_application(request, bidding_router=bidding_router)

    report = run_simulation(SimulationConfig(seed=7, deal_count=3), analyzer=counted)
    assert len(requests) == report.completed_deals == 3
    assert tuple(case.dealer for case in report.cases) == (
        Seat.NORTH, Seat.EAST, Seat.SOUTH
    )
    assert tuple(case.vulnerability for case in report.cases) == (
        Vulnerability.NONE, Vulnerability.NS, Vulnerability.EW
    )


def test_recommendation_and_abstain_records_preserve_production_status():
    report = run_simulation(SimulationConfig(seed=100, deal_count=20))
    assert all(
        case.status in (AnalysisStatus.RECOMMENDATION, AnalysisStatus.ABSTAIN)
        for case in report.cases
    )
    for case in report.cases:
        if case.status is AnalysisStatus.RECOMMENDATION:
            assert case.recommended_call and case.rule_id and case.route_id
            assert case.sources and case.abstention_code is None
        else:
            assert case.recommended_call is None and case.abstention_code
            assert case.rule_id is None


def test_application_error_remains_distinct_from_abstain():
    def failed(_request, *, bidding_router):
        assert len(bidding_router.routes) == 45
        return FullDealApplicationResponse(
            False, "error", None, None, "",
            (FullDealApplicationError(
                FullDealApplicationErrorCode.PRODUCTION_ERROR, "production", "fixture error"
            ),),
        )

    report = run_simulation(SimulationConfig(deal_count=2), analyzer=failed)
    assert (report.recommendations, report.abstains, report.errors) == (0, 0, 2)
    assert report.call_frequencies == ()
    assert all(case.status is AnalysisStatus.ERROR for case in report.cases)
    assert all(case.error == "fixture error" for case in report.cases)


def test_summary_reconciles_and_only_counts_actual_calls():
    report = run_simulation(SimulationConfig(seed=55, deal_count=8))
    assert report.recommendations + report.abstains + report.errors == report.completed_deals
    assert sum(count for _, count in report.call_frequencies) == report.recommendations
    assert set(call for call, _ in report.call_frequencies) == {
        case.recommended_call for case in report.cases if case.recommended_call is not None
    }
    with pytest.raises(FrozenInstanceError):
        report.seed = 1


def test_production_router_still_has_45_routes():
    assert len(create_standard_sayc_router().routes) == 45
