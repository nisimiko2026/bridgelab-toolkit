import inspect

from benchmarks.stayman_dual_major_policy_audit import (
    run_stayman_dual_major_policy_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_exact_dual_major_population_and_shape_partition():
    audit = run_stayman_dual_major_policy_audit()
    assert audit.dual_major_total == 36
    assert audit.shape_buckets == {
        "4H_4S": 36,
        "4H_5plusS": 0,
        "5plusH_4S": 0,
        "5plusH_5plusS": 0,
    }
    assert sum(audit.shape_buckets.values()) == 36
    assert audit.exact_shapes == {"2-3-4-4": 19, "3-2-4-4": 17}


def test_current_router_reaches_stayman_rule_and_abstains_for_all_36():
    audit = run_stayman_dual_major_policy_audit()
    assert audit.existing_route_attempts == {"sayc.opener.1nt.stayman": 36}
    assert audit.current_production_actions == {"ABSTAIN": 36}
    assert audit.current_abstentions == 36


def test_source_supports_only_a_non_default_policy_boundary():
    audit = run_stayman_dual_major_policy_audit()
    assert audit.policy_boundary_possible is True
    assert audit.proposed_output_domain == ("HEARTS", "SPADES", "UNKNOWN")
    assert audit.default_behavior == "no policy -> abstain"
    assert audit.default_dual_major_policy is None
    assert audit.decision == "B. ADD NON-DEFAULT DUAL-MAJOR POLICY ARCHITECTURE"
    assert len(audit.source_certainty_matrix) == 4
    assert all(
        row["classification"] == "POLICY_REQUIRED"
        for row in audit.source_certainty_matrix
    )


def test_phase12i_is_structurally_deterministic():
    assert (
        run_stayman_dual_major_policy_audit()
        == run_stayman_dual_major_policy_audit()
    )


def test_guards_and_prior_phase_invariants_are_unchanged():
    module = __import__(
        "benchmarks.stayman_dual_major_policy_audit", fromlist=["unused"]
    )
    source = inspect.getsource(module).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert len(create_standard_sayc_router().routes) == 45
    registry = PolicyRegistry()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.stayman_dual_major_response_policy_ids == ()
    audit = run_stayman_dual_major_policy_audit()
    assert audit.route_count == 45
    assert audit.responder_continuation_policy_changed is False
    assert audit.phase12g_calls == {"4H": 17, "4S": 21}
    assert audit.phase12h_residual_by_family == {
        "after_2D": 104,
        "after_2H_no_fit": 53,
        "after_2S_no_fit": 40,
    }
    assert sum(audit.phase12h_residual_by_family.values()) == 197
    assert audit.production_defaults_changed is False
    assert audit.knowledge_markdown_changed == 0
