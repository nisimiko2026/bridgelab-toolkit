import inspect

from benchmarks.stayman_dual_major_opener_responses import (
    run_stayman_dual_major_opener_response_benchmark,
)
from benchmarks.stayman_dual_major_policy_architecture import (
    FixedStaymanDualMajorResponsePolicy,
)
from bridge import (
    Auction,
    BiddingContext,
    Hand,
    Seat,
    StaymanDualMajorResponse,
    SystemContext,
    Vulnerability,
)
from bridge.policy_registry import (
    STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION,
    PolicyRegistry,
)
from bridge.sayc_1nt_stayman import (
    create_sayc_one_notrump_stayman_opener_response_engine,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


def context(hand, policy_id=None):
    options = (
        {}
        if policy_id is None
        else {STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION: policy_id}
    )
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, ("1NT", "P", "2C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


def action(engine, ctx):
    decision = engine.evaluate(ctx)
    return (
        None
        if decision.recommended_call is None
        else decision.recommended_call.serialize()
    )


def test_missing_unresolved_and_unknown_policy_abstain():
    hand = "KJ97.AQ63.842.63"
    assert action(create_standard_sayc_router(), context(hand)) is None
    assert action(create_standard_sayc_router(), context(hand, "missing")) is None
    unknown = FixedStaymanDualMajorResponsePolicy(StaymanDualMajorResponse.UNKNOWN)
    registry = PolicyRegistry.from_stayman_dual_major_response_policies((unknown,))
    assert action(create_standard_sayc_router(registry), context(hand, unknown.policy_id)) is None


def test_explicit_hearts_and_spades_policies_translate_in_production_rule():
    hand = "KJ97.AQ63.842.63"
    for response, expected in (
        (StaymanDualMajorResponse.HEARTS, "2H"),
        (StaymanDualMajorResponse.SPADES, "2S"),
    ):
        policy = FixedStaymanDualMajorResponsePolicy(response)
        registry = PolicyRegistry.from_stayman_dual_major_response_policies((policy,))
        engine = create_sayc_one_notrump_stayman_opener_response_engine(registry)
        assert action(engine, context(hand, policy.policy_id)) == expected


def test_non_dual_major_stayman_responses_remain_unchanged():
    engine = create_sayc_one_notrump_stayman_opener_response_engine()
    assert action(engine, context("AQ3.KJ4.AQ76.KJ3")) == "2D"
    assert action(engine, context("AQ3.KJ74.AQ7.KJ3")) == "2H"
    assert action(engine, context("AQ74.KJ3.AQ7.KJ3")) == "2S"


def test_translation_is_not_in_policy_module_and_has_no_forbidden_heuristics():
    policy_source = inspect.getsource(
        __import__("bridge.stayman_dual_major_response_policy", fromlist=["unused"])
    ).casefold()
    rule_source = inspect.getsource(
        __import__("bridge.sayc_1nt_stayman", fromlist=["unused"])
    ).casefold()
    assert "call.parse" not in policy_source
    assert 'call.parse("2h")' in rule_source
    assert 'call.parse("2s")' in rule_source
    assert "high_card_points" not in rule_source
    assert "hcp" not in rule_source
    assert "suit_quality" not in rule_source


def test_exact_fixture_and_combined_policy_benchmark_results():
    result = run_stayman_dual_major_opener_response_benchmark()
    assert result.dual_major_total == 36
    assert result.exact_shapes == {"2-3-4-4": 19, "3-2-4-4": 17}
    assert result.opener_policy_scenarios == {
        "HEARTS": {"2H": 36},
        "SPADES": {"2S": 36},
        "UNKNOWN": {"ABSTAIN": 36},
    }
    assert result.no_policy_production_actions == {"ABSTAIN": 36}
    assert result.dual_policy_only_responder_actions == {
        "HEARTS": {"ABSTAIN": 36},
        "SPADES": {"ABSTAIN": 36},
    }
    assert result.combined_policy_downstream == {
        "HEARTS": {
            "4H": 5,
            "ABSTAIN": 31,
            "responder_fit": 5,
            "responder_no_fit": 31,
        },
        "SPADES": {
            "4S": 7,
            "ABSTAIN": 29,
            "responder_fit": 7,
            "responder_no_fit": 29,
        },
    }


def test_routes_prior_phases_and_defaults_are_unchanged():
    result = run_stayman_dual_major_opener_response_benchmark()
    assert result.route_count == 44
    assert len(create_standard_sayc_router().routes) == 44
    assert result.default_dual_major_policy is None
    assert result.default_continuation_policy is None
    assert result.phase12g_calls == {"4H": 17, "4S": 21}
    assert result.phase12h_residual_total == 197
    assert result.production_defaults_changed is False
    assert result.knowledge_markdown_changed == 0


def test_phase12k_benchmark_is_structurally_deterministic():
    assert (
        run_stayman_dual_major_opener_response_benchmark()
        == run_stayman_dual_major_opener_response_benchmark()
    )
