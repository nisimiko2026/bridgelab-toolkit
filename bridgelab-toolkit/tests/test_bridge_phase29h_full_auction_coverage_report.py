"""Focused coverage reporting tests over immutable Phase 29G records."""

import json

from bridge.deal_analysis import AnalysisStatus
from bridge.deal_simulator import (
    AuctionOutcome, AuctionStep, FullAuctionBatchResult, FullAuctionResult,
    SimulationConfig, run_full_auction_simulation, run_simulation,
)
from bridge.full_auction_coverage import build_full_auction_coverage_report
from bridge.models import Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _auction(index, dealer, calls, code="no-route", outcome=AuctionOutcome.ABSTAIN):
    steps = tuple(
        AuctionStep(number, dealer, "KQJ876.32.43.543", tuple(calls[:number]),
                    AnalysisStatus.RECOMMENDATION, call, None, "opening.rule",
                    "sayc.opening", ("knowledge/source",))
        for number, call in enumerate(calls)
    )
    if outcome is AuctionOutcome.ABSTAIN:
        steps += (AuctionStep(len(steps), dealer, "KQJ876.32.43.543", tuple(calls),
                              AnalysisStatus.ABSTAIN, None, code, None, "stop.route", ()),)
    elif outcome is AuctionOutcome.ERROR:
        steps += (AuctionStep(len(steps), dealer, "KQJ876.32.43.543", tuple(calls),
                              AnalysisStatus.ERROR, None, None, None, None, (), "fixture error"),)
    return FullAuctionResult(
        index, dealer, Vulnerability.NONE, tuple(calls), steps, outcome,
        dealer if outcome is not AuctionOutcome.COMPLETE else None,
        code if outcome is AuctionOutcome.ABSTAIN else None,
        "fixture error" if outcome is AuctionOutcome.ERROR else None,
    )


def _batch():
    auctions = (
        _auction(0, Seat.NORTH, ("1C",)),
        _auction(1, Seat.EAST, ("1C",), "rule-abstained"),
        _auction(2, Seat.SOUTH, ("1C",)),
        _auction(3, Seat.WEST, ("1D",)),
        _auction(4, Seat.NORTH, (), outcome=AuctionOutcome.ERROR),
    )
    return FullAuctionBatchResult(100, 5, auctions, 0, 4, 1,
                                  sum(len(item.steps) for item in auctions),
                                  (), (), ())


def test_deterministic_report_grouping_ranking_and_representatives():
    batch = _batch()
    report = build_full_auction_coverage_report(batch)
    assert report == build_full_auction_coverage_report(batch)
    assert tuple(item.signature.calls for item in report.ranked_stops) == (
        ("1C",), ("1D",)
    )
    assert tuple(item.count for item in report.ranked_stops) == (3, 1)
    assert report.ranked_stops[0].representative_deal_indexes == (0, 1, 2)
    assert report.ranked_stops[0].percent_of_abstains == 75.0
    assert report.ranked_stops[0].successful_depth == 1


def test_reconciliation_depth_codes_seats_routes_and_error_separation():
    report = build_full_auction_coverage_report(_batch())
    assert report.complete + report.abstain + report.errors == report.completed_simulations
    assert (report.successful_recommendations, report.abstaining_decisions,
            report.error_decisions, report.total_decisions) == (4, 4, 1, 9)
    assert report.stop_depths == ((1, 4),)
    assert dict(report.abstention_codes) == {"no-route": 3, "rule-abstained": 1}
    assert sum(count for _, count in report.stopping_seats) == report.abstain
    assert report.successful_routes == (("sayc.opening", 4),)
    assert report.stopping_routes == (("stop.route", 4),)
    assert report.error_messages == (("fixture error", 1),)


def test_empty_auction_stopping_signature_is_retained_and_serialized():
    auction = _auction(7, Seat.EAST, ())
    batch = FullAuctionBatchResult(100, 1, (auction,), 0, 1, 0, 1, (), (), ())
    report = build_full_auction_coverage_report(batch)
    assert len(report.ranked_stops) == 1
    stop = report.ranked_stops[0]
    assert stop.signature.calls == ()
    assert stop.count == 1 and stop.successful_depth == 0
    assert report.stop_depths == ((0, 1),)
    as_dict = report.to_dict()
    assert as_dict["ranked_stops"][0]["calls"] == []
    assert as_dict["ranked_stops"][0]["successful_depth"] == 0
    assert as_dict["stop_depths"] == [[0, 1]]
    assert json.loads(report.to_json()) == as_dict
    assert json.loads(report.to_json())["ranked_stops"][0]["calls"] == []


def test_json_serialization_is_stable_compatible_and_has_no_deals():
    report = build_full_auction_coverage_report(_batch())
    first = report.to_json()
    assert first == build_full_auction_coverage_report(_batch()).to_json()
    assert json.loads(first) == report.to_dict()
    assert "KQJ876" not in first
    assert "object at" not in first


def test_real_simulation_integration_and_phase29f_guards():
    batch = run_full_auction_simulation(SimulationConfig(seed=30, deal_count=3))
    report = build_full_auction_coverage_report(batch)
    assert report == build_full_auction_coverage_report(batch)
    assert report.total_decisions == sum(len(item.steps) for item in batch.auctions)
    assert report.successful_recommendations == sum(
        step.status is AnalysisStatus.RECOMMENDATION
        for item in batch.auctions for step in item.steps
    )
    assert run_simulation(SimulationConfig(seed=30, deal_count=2)).completed_deals == 2
    assert len(create_standard_sayc_router().routes) == 45
