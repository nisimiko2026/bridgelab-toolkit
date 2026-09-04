from benchmarks.jacoby_continuation_policy_fixture import (
    DeterministicJacobyContinuationPolicyFixture,
    run_jacoby_policy_fixture_benchmark,
)
from bridge import (
    Auction,
    BiddingContext,
    Hand,
    Seat,
    SystemContext,
    Vulnerability,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_round_robin_fixture_does_not_inspect_cards():
    first = Hand.parse("AKQJ.T98.765.432")
    second = Hand.parse("2.3456.89TJ.QKJA")
    policy = DeterministicJacobyContinuationPolicyFixture(2)
    contexts = [
        BiddingContext.create(
            hand=hand,
            auction=Auction(Seat.NORTH, ("1NT", "P", "2D", "P", "2H", "P")),
            vulnerability=Vulnerability.NONE,
            system=SystemContext("SAYC"),
        )
        for hand in (first, second)
    ]
    assert policy.assess(contexts[0]).strength_class == policy.assess(contexts[1]).strength_class


def test_phase12c_exact_metrics_and_default_isolation():
    metrics = run_jacoby_policy_fixture_benchmark()
    assert metrics.total_jacoby_continuations == 123
    assert metrics.accepted_heart_transfer_positions == 62
    assert metrics.accepted_spade_transfer_positions == 61
    assert metrics.by_strength_class == {
        "WEAK": 25,
        "INVITATIONAL": 25,
        "GAME_GOING": 25,
        "SLAM_INTEREST": 24,
        "UNKNOWN": 24,
    }
    assert metrics.resulting_calls["Pass"] == 25
    assert metrics.resulting_calls["2NT"] == 25
    assert metrics.resulting_calls["4H"] == metrics.game_heart_4H == 12
    assert metrics.resulting_calls["4S"] == metrics.game_spade_4S == 13
    assert metrics.game_heart_4H + metrics.game_spade_4S == 25
    assert metrics.abstentions == {"SLAM_INTEREST": 24, "UNKNOWN": 24}
    assert metrics.produced_call_count == 75
    assert metrics.abstention_count == 48
    assert (metrics.coverage_numerator, metrics.coverage_denominator) == (75, 123)
    assert metrics.coverage_pct == 60.98
    assert metrics.default_behavior_unchanged


def test_phase12c_is_structurally_deterministic():
    assert run_jacoby_policy_fixture_benchmark() == run_jacoby_policy_fixture_benchmark()


def test_default_registry_and_router_have_no_fixture_policy():
    registry = PolicyRegistry()
    assert registry.jacoby_continuation_strength_policy(
        "benchmark.fixture.jacoby.round-robin"
    ) is None
    router = create_standard_sayc_router()
    context = BiddingContext.create(
        hand=Hand.parse("KJ974.842.63.Q63"),
        auction=Auction(Seat.NORTH, ("1NT", "P", "2D", "P", "2H", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )
    assert router.evaluate(context).recommended_call is None
