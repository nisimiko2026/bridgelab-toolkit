import inspect

from benchmarks.strong_two_club_rebid_residual_audit import (
    PRIMARY_BUCKETS,
    run_strong_two_club_rebid_residual_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


AUDIT = run_strong_two_club_rebid_residual_audit()


def test_exact_family_handled_and_residual_population():
    assert AUDIT.original_family == 47
    assert AUDIT.phase12n_handled == AUDIT.phase12n_2nt_calls == 24
    assert AUDIT.residual_total == 23
    assert all(row["current_action"] == "ABSTAIN" for row in AUDIT.positions)


def test_primary_partition_is_mutually_exclusive_and_complete():
    assert tuple(AUDIT.primary_bucket_counts) == PRIMARY_BUCKETS
    assert sum(AUDIT.primary_bucket_counts.values()) == 23
    assert len(AUDIT.positions) == 23
    assert len({row["seed"] for row in AUDIT.positions}) == 23
    assert all(row["primary_bucket"] in PRIMARY_BUCKETS for row in AUDIT.positions)
    assert AUDIT.primary_bucket_counts == {
        "balanced_below_22": 0,
        "balanced_above_24": 2,
        "unbalanced_below_22": 0,
        "unbalanced_22_24_single_longest_major": 11,
        "unbalanced_22_24_single_longest_minor": 9,
        "unbalanced_22_24_tied_longest": 1,
        "unbalanced_above_24": 0,
    }


def test_exact_hcp_shapes_and_secondary_flags():
    assert AUDIT.hcp_distribution == {"22": 13, "23": 5, "24": 3, "25": 1, "26": 1}
    assert sum(AUDIT.exact_shape_distribution.values()) == 23
    assert AUDIT.exact_shape_distribution["5-3-4-1"] == 2
    assert AUDIT.secondary_flag_counts == {
        "5+ card major": 11,
        "5+ card minor": 9,
        "6+ card suit": 11,
        "7+ card suit": 4,
        "two-suited shape": 15,
    }


def test_source_matrix_covers_every_position_and_defers_all():
    assert len(AUDIT.source_certainty_matrix) == len(PRIMARY_BUCKETS)
    assert sum(row["exact_count"] for row in AUDIT.source_certainty_matrix) == 23
    assert all(row["classification"] in {"SOURCE_PARTIAL", "SOURCE_INSUFFICIENT"} for row in AUDIT.source_certainty_matrix)
    assert all(row["executable_subset"] is False for row in AUDIT.source_certainty_matrix)
    assert AUDIT.source_safe_candidates == ()
    assert AUDIT.decision == "D. DEFER REMAINING STRONG-2C REBIDS"
    assert "response.one-notrump" in AUDIT.phase12p_recommendation


def test_router_rule_and_no_production_expansion_guards():
    assert AUDIT.route_count == len(create_standard_sayc_router().routes) == 45
    assert AUDIT.route_reached == AUDIT.rule_abstained == 23
    assert AUDIT.other_route_attempts == 0
    assert AUDIT.production_rules_added == AUDIT.routes_added == AUDIT.policies_added == 0
    module = __import__("benchmarks.strong_two_club_rebid_residual_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source
    assert "from_policies(" not in source


def test_defaults_prior_invariants_and_knowledge_are_unchanged():
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    assert AUDIT.default_policies == {
        "stayman_dual_major": None,
        "stayman_continuation": None,
        "jacoby_continuation": None,
    }
    assert AUDIT.phase12g_calls == {"4H": 17, "4S": 21}
    assert AUDIT.phase12h_residual == 197
    assert AUDIT.phase12k_no_policy_abstentions == 36
    assert AUDIT.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert AUDIT.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert AUDIT.production_defaults_changed is False
    assert AUDIT.knowledge_markdown_changed == 0


def test_audit_is_structurally_deterministic():
    assert AUDIT == run_strong_two_club_rebid_residual_audit()
