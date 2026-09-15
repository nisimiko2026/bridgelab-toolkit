"""Focused read-only Phase 29I classification and reproduction checks."""

import json

import pytest

from bridge.deal_analysis import AnalysisStatus
from bridge.deal_simulator import (
    AuctionOutcome, AuctionStep, FullAuctionBatchResult, FullAuctionResult,
    SimulationConfig, run_full_auction_simulation, run_simulation,
)
from bridge.deals import generate_deal
from bridge.evaluation import evaluate_hand
from bridge.full_auction_abstention_audit import (
    DiagnosticCategory, HCP_BANDS, build_abstention_audit, classify, hcp_band,
)
from bridge.full_auction_coverage import build_full_auction_coverage_report
from bridge.models import Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _auction(index, before=(), code="no-route", outcome=AuctionOutcome.ABSTAIN):
    seat = Seat.NORTH if not before else Seat.EAST
    hand = generate_deal(100 + index).hand(seat)
    step = AuctionStep(len(before), seat, hand.serialize(), before,
                       AnalysisStatus.ABSTAIN if outcome is AuctionOutcome.ABSTAIN else AnalysisStatus.ERROR,
                       None, code if outcome is AuctionOutcome.ABSTAIN else None,
                       None, "none", (), "failure" if outcome is AuctionOutcome.ERROR else None)
    return FullAuctionResult(index, Seat.NORTH, Vulnerability.NONE, before, (step,),
                             outcome, seat, code if outcome is AuctionOutcome.ABSTAIN else None)


def _batch(*auctions):
    return FullAuctionBatchResult(100, len(auctions), tuple(auctions), 0,
                                  sum(a.outcome is AuctionOutcome.ABSTAIN for a in auctions),
                                  sum(a.outcome is AuctionOutcome.ERROR for a in auctions),
                                  len(auctions), (), (), ())


def test_depth_grouping_empty_signature_and_error_separation():
    batch = _batch(_auction(0), _auction(1, ("1C",), "rule-abstained"),
                   _auction(2, ("1D",)), _auction(3, ("1C", "P")),
                   _auction(4, outcome=AuctionOutcome.ERROR))
    report = build_abstention_audit(batch)
    assert (report.total_abstains, report.depth0.count, report.depth1_count,
            report.other_depth_count) == (4, 1, 2, 1)
    assert report.depth0.name == "()"
    assert [(g.name, g.count) for g in report.depth1_groups] == [("1C", 1), ("1D", 1)]
    assert dict(report.depth1_groups[0].categories) == {"rule-abstained-unexplained": 1}
    assert dict(report.depth1_groups[1].categories) == {"no-route": 1}
    assert json.loads(report.to_json()) == report.to_dict()
    assert build_abstention_audit(batch).to_json() == report.to_json()


def test_canonical_hand_hcp_shape_bands_and_representative_bound():
    batch = _batch(*(_auction(i) for i in range(20)))
    report = build_abstention_audit(batch)
    group = report.depth0
    assert sum(count for _, count in group.hcp_bands) == 20
    assert tuple(name for name, _ in group.hcp_bands) == HCP_BANDS
    assert sum(count for _, count in group.categories) == 20
    assert len(group.representatives) <= 9
    for case in group.representatives:
        hand = generate_deal(batch.seed + case.deal_index).hand(Seat.NORTH)
        evaluation = evaluate_hand(hand)
        assert case.hand == hand.serialize()
        assert (case.hcp, case.suit_lengths, case.shape_class) == (
            evaluation.hcp, evaluation.suit_lengths, evaluation.shape_class.value)
        assert dict(group.hcp_bands)[hcp_band(case.hcp)] >= 1
    assert tuple(case.deal_index for case in group.representatives) == tuple(
        case.deal_index for case in build_abstention_audit(batch).depth0.representatives)


def test_record_mismatch_stops_audit():
    auction = _auction(0)
    step = auction.steps[0]
    damaged = AuctionStep(step.index, step.seat, "wrong hand", step.auction_before,
                          step.status, step.recommended_call, step.abstention_code,
                          step.rule_id, step.route_id, step.sources)
    auction = FullAuctionResult(auction.deal_index, auction.dealer, auction.vulnerability,
                                auction.final_calls, (damaged,), auction.outcome,
                                auction.stopping_seat, auction.abstention_code)
    with pytest.raises(ValueError, match="reproduction failed"):
        build_abstention_audit(_batch(auction))


def test_category_preserves_production_code_without_guessing():
    assert classify("no-route") is DiagnosticCategory.NO_ROUTE
    assert classify("rule-abstained") is DiagnosticCategory.RULE_ABSTAINED_UNEXPLAINED
    assert classify("policy-required") is DiagnosticCategory.POLICY_REQUIRED
    assert classify("source-insufficient") is DiagnosticCategory.SOURCE_INSUFFICIENT
    assert classify("unrecognized") is DiagnosticCategory.UNKNOWN


def test_tiny_production_guards():
    config = SimulationConfig(seed=100, deal_count=3)
    batch = run_full_auction_simulation(config)
    report = build_abstention_audit(batch)
    assert report.total_abstains == batch.abstain
    assert report.to_json() == build_abstention_audit(run_full_auction_simulation(config)).to_json()
    coverage = build_full_auction_coverage_report(batch)
    assert coverage.abstain == batch.abstain
    assert run_simulation(config).completed_deals == 3
    assert len(create_standard_sayc_router().routes) == 45
