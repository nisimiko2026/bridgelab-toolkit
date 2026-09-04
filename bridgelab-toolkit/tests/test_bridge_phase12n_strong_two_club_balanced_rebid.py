import inspect

import pytest

from benchmarks.strong_two_club_balanced_rebid import (
    run_strong_two_club_balanced_rebid_benchmark,
)
from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.sayc_strong_two_club import SaycStrongTwoClubBalancedRebidRule


def context(hand: str, calls=("2C", "P", "2D", "P")) -> BiddingContext:
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


@pytest.mark.parametrize(
    ("hand", "expected"),
    [
        ("AKQ.AKQ.J74.Q843", None),
        ("AKQ.AKQ.Q74.Q843", "2NT"),
        ("AKQ.AKQ.K74.Q843", "2NT"),
        ("AKQ.AKQ.A74.Q843", "2NT"),
        ("AKQ.AKQ.A74.K843", None),
        ("AKQ32.AKQ2.Q74.Q", None),
        ("AKQ32.AKQ2.K74.Q", None),
        ("AKQ32.AKQ2.A74.Q", None),
    ],
)
def test_exact_hcp_and_shape_boundaries(hand, expected):
    decision = SaycStrongTwoClubBalancedRebidRule().evaluate(context(hand))
    assert (decision.candidate.serialize() if decision.candidate else None) == expected


@pytest.mark.parametrize(
    "calls",
    [
        ("2C", "P", "2H", "P"),
        ("2C", "P", "2S", "P"),
        ("2C", "X", "2D", "P"),
        ("2C", "P", "2D", "X"),
    ],
)
def test_non_exact_or_competitive_auctions_do_not_trigger(calls):
    assert not SaycStrongTwoClubBalancedRebidRule().evaluate(
        context("AKQ.AKQ.Q74.Q843", calls)
    ).applicable


def test_exact_route_is_reachable_and_competitive_routes_are_not():
    router = create_standard_sayc_router()
    exact = router.match(context("AKQ.AKQ.Q74.Q843"))
    assert exact is not None
    assert exact.route_id == "sayc.opener.2c.2d.balanced"
    assert router.evaluate(context("AKQ.AKQ.Q74.Q843")).recommended_call == Call.parse("2NT")
    assert router.match(context("AKQ.AKQ.Q74.Q843", ("2C", "P", "2D", "X"))) is None
    assert len(router.routes) == 45


BENCHMARK = run_strong_two_club_balanced_rebid_benchmark()


def test_exact_deterministic_population_actions_and_repeatability():
    assert BENCHMARK.family_population == 47
    assert BENCHMARK.target_subset == BENCHMARK.newly_handled_2nt == 24
    assert BENCHMARK.pre_existing_calls == 0
    assert BENCHMARK.remaining_abstentions == 23
    assert BENCHMARK.action_counts == {"2NT": 24, "ABSTAIN": 23}
    assert BENCHMARK == run_strong_two_club_balanced_rebid_benchmark()


def test_source_gate_policies_defaults_and_prior_phase_guards():
    source = inspect.getsource(SaycStrongTwoClubBalancedRebidRule)
    numeric_tokens = {token for token in source.replace("–", "-").split() if token.isdigit()}
    assert numeric_tokens <= {"22", "24", "100"}
    assert "22 <= evaluation.hcp <= 24" in source
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    assert BENCHMARK.default_policies == {
        "stayman_dual_major": None,
        "stayman_continuation": None,
        "jacoby_continuation": None,
    }
    assert BENCHMARK.phase12g_calls == {"4H": 17, "4S": 21}
    assert BENCHMARK.phase12h_residual == 197
    assert BENCHMARK.phase12k_no_policy_abstentions == 36
    assert BENCHMARK.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert BENCHMARK.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert BENCHMARK.production_defaults_changed is False
    assert BENCHMARK.knowledge_markdown_changed == 0
