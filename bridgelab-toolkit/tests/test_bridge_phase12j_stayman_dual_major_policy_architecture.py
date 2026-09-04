from benchmarks.stayman_dual_major_policy_architecture import (
    run_stayman_dual_major_policy_architecture_validation,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_exact_architecture_fixture_benchmark_and_shapes():
    result = run_stayman_dual_major_policy_architecture_validation()
    assert result.dual_major_total == 36
    assert result.exact_shapes == {"2-3-4-4": 19, "3-2-4-4": 17}
    assert result.fixture_results == {"HEARTS": 36, "SPADES": 36, "UNKNOWN": 36}


def test_production_still_abstains_on_all_targets_and_routes_are_unchanged():
    result = run_stayman_dual_major_policy_architecture_validation()
    assert result.production_actions == {"ABSTAIN": 36}
    assert result.existing_route_attempts == {"sayc.opener.1nt.stayman": 36}
    assert result.route_count == 45
    assert len(create_standard_sayc_router().routes) == 45
    assert result.production_bidding_calls_added == 0


def test_prior_phase_invariants_and_default_guards():
    result = run_stayman_dual_major_policy_architecture_validation()
    assert result.default_policy is None
    assert PolicyRegistry().stayman_dual_major_response_policy_ids == ()
    assert result.phase12g_calls == {"4H": 17, "4S": 21}
    assert result.phase12h_residual_total == 197
    assert result.production_defaults_changed is False
    assert result.knowledge_markdown_changed == 0


def test_phase12j_validation_is_structurally_deterministic():
    assert (
        run_stayman_dual_major_policy_architecture_validation()
        == run_stayman_dual_major_policy_architecture_validation()
    )
