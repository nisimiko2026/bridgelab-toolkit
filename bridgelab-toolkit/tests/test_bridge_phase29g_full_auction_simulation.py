"""Focused Phase 29G full-auction simulation tests."""

from dataclasses import replace

from bridge.auction import Auction, Call
from bridge.deal_analysis import (
    AbstentionCode, ActionKind, AnalysisAction, AnalysisStatus,
)
from bridge.deal_simulator import (
    AuctionOutcome, SimulationConfig, run_full_auction_simulation,
    run_simulation, simulate_full_auction,
)
from bridge.deals import generate_deal
from bridge.full_deal_application import (
    FullDealApplicationError, FullDealApplicationErrorCode,
    FullDealApplicationResponse, analyze_full_deal_application,
)
from bridge.models import Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _response(request, router, *, status, call=None, code=None):
    base = analyze_full_deal_application(request, bidding_router=router)
    assert base.canonical_result is not None
    original = base.canonical_result.subsystem_results[0]
    action = AnalysisAction(ActionKind.NONE) if call is None else AnalysisAction(
        ActionKind.BID, bid=Call.parse(call)
    )
    changed = replace(
        original, status=status, action=action,
        abstention_code=code,
        debug_metadata=(("route", "fixture.route"), ("rule", "fixture.rule")),
    )
    canonical = replace(base.canonical_result, subsystem_results=(changed,))
    return replace(base, success=True, canonical_result=canonical)


def _calls_analyzer(calls):
    sequence = iter(calls)
    def analyze(request, *, bidding_router):
        return _response(
            request, bidding_router, status=AnalysisStatus.RECOMMENDATION,
            call=next(sequence),
        )
    return analyze


def test_steps_use_canonical_next_seat_actual_hand_and_grow_one_call():
    deal = generate_deal(10)
    result = simulate_full_auction(
        deal_index=0, deal=deal, dealer=Seat.SOUTH,
        vulnerability=Vulnerability.NONE,
        analyzer=_calls_analyzer(("1C", "P", "P", "P")),
    )
    auction = Auction(Seat.SOUTH)
    for step in result.steps:
        assert step.seat is auction.next_seat
        assert step.hand == deal.hand(step.seat).serialize()
        assert step.auction_before == tuple(call.serialize() for call in auction.calls)
        auction.add(step.recommended_call)
        assert len(auction.calls) == step.index + 1
    assert result.outcome is AuctionOutcome.COMPLETE and auction.is_complete


def test_passed_out_auction_completes_canonically():
    result = simulate_full_auction(
        deal_index=0, deal=generate_deal(1), dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        analyzer=_calls_analyzer(("P", "P", "P", "P")),
    )
    auction = Auction(Seat.NORTH, result.final_calls)
    assert result.outcome is AuctionOutcome.COMPLETE
    assert auction.is_complete and auction.is_passed_out


def test_abstain_stops_without_fallback_call():
    def abstain(request, *, bidding_router):
        return _response(
            request, bidding_router, status=AnalysisStatus.ABSTAIN,
            code=AbstentionCode.NO_ROUTE,
        )
    result = simulate_full_auction(
        deal_index=0, deal=generate_deal(2), dealer=Seat.EAST,
        vulnerability=Vulnerability.NS, analyzer=abstain,
    )
    assert result.outcome is AuctionOutcome.ABSTAIN
    assert result.final_calls == () and result.stopping_seat is Seat.EAST
    assert result.abstention_code == "no-route"


def test_application_error_stops_without_call():
    def error(_request, *, bidding_router):
        return FullDealApplicationResponse(
            False, "error", None, None, "",
            (FullDealApplicationError(
                FullDealApplicationErrorCode.PRODUCTION_ERROR, "production", "fixture"
            ),),
        )
    result = simulate_full_auction(
        deal_index=0, deal=generate_deal(3), dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE, analyzer=error,
    )
    assert result.outcome is AuctionOutcome.ERROR
    assert result.final_calls == () and result.error == "fixture"


def test_illegal_recommendation_is_consistency_error_without_substitute():
    result = simulate_full_auction(
        deal_index=0, deal=generate_deal(4), dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        analyzer=_calls_analyzer(("1H", "1D")),
    )
    assert result.outcome is AuctionOutcome.ERROR
    assert result.final_calls == ("1H",)
    assert "canonical Auction rejected" in result.error


def test_single_and_batch_results_are_deterministic_and_reconcile():
    first = run_full_auction_simulation(SimulationConfig(seed=20, deal_count=5))
    assert first == run_full_auction_simulation(SimulationConfig(seed=20, deal_count=5))
    assert first.complete + first.abstain + first.errors == first.completed_simulations == 5
    assert first.total_steps == sum(len(item.steps) for item in first.auctions)
    assert sum(count for _, count in first.route_use_counts) == sum(
        step.status is AnalysisStatus.RECOMMENDATION
        for item in first.auctions for step in item.steps
    )


def test_phase29f_and_production_router_remain_available():
    assert run_simulation(SimulationConfig(seed=1, deal_count=2)).completed_deals == 2
    assert len(create_standard_sayc_router().routes) == 45
