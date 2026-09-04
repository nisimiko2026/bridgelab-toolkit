from benchmarks.stayman_major_fit_game_continuation_benchmark import (
    run_stayman_major_fit_game_benchmark,
)
from bridge import Auction, BiddingContext, Hand, Seat, SystemContext, Vulnerability
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def context(calls):
    return BiddingContext.create(
        hand=Hand.parse("AKQJ.432.T98.765"),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


def test_exact_routes_and_default_abstention():
    router = create_standard_sayc_router()
    assert len(router.routes) == 44
    assert router.match(context(("1NT", "P", "2C", "P", "2H", "P"))).route_id == "sayc.responder.1nt.stayman.after.2h"
    assert router.match(context(("1NT", "P", "2C", "P", "2S", "P"))).route_id == "sayc.responder.1nt.stayman.after.2s"
    assert router.match(context(("1NT", "P", "2C", "P", "2D", "P"))) is None
    assert router.match(context(("1NT", "P", "2C", "X", "2H", "P"))) is None
    assert router.evaluate(context(("1NT", "P", "2C", "P", "2S", "P"))).recommended_call is None
    assert PolicyRegistry().stayman_continuation_strength_policy_ids == ()


def test_exact_phase12g_fixture_benchmark():
    result = run_stayman_major_fit_game_benchmark()
    assert result.audited_positions == 235
    assert result.opener_response_positions == {"2D": 104, "2H": 70, "2S": 61}
    assert result.resulting_calls == {"4H": 17, "4S": 21}
    assert result.abstentions == {"2D": 104, "2H": 53, "2S": 40}
    assert result.continuation_call_count == 38
    assert result.abstention_count == 197
    assert (result.coverage_numerator, result.coverage_denominator) == (38, 235)
    assert result.coverage_pct == 16.17
    assert result.dual_major_abstentions == 36
    assert result.production_route_count == 44


def test_phase12g_benchmark_is_structurally_deterministic():
    assert run_stayman_major_fit_game_benchmark() == run_stayman_major_fit_game_benchmark()

