import inspect

from benchmarks.three_level_preempt_response_source_readiness_audit import (
    run_three_level_preempt_response_source_readiness_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


AUDIT = run_three_level_preempt_response_source_readiness_audit()


def test_exact_sample_population_openings_and_actions():
    assert (AUDIT.start_seed, AUDIT.deal_count) == (1, 10_000)
    assert AUDIT.population == AUDIT.phase12q_expected_population == 166
    assert AUDIT.per_opening_counts == {"3C": 34, "3D": 47, "3H": 47, "3S": 38}
    assert {row["auction_prefix"] for row in AUDIT.positions} == {"3C P", "3D P", "3H P", "3S P"}
    assert {row["decision_seat"] for row in AUDIT.positions} == {"S"}
    assert {row["current_action"] for row in AUDIT.positions} == {"ABSTAIN"}
    assert len({row["stable_id"] for row in AUDIT.positions}) == 166


def test_primary_buckets_are_exclusive_and_reconcile():
    assert AUDIT.primary_partitions == {
        "slam-interest-looking": 2,
        "game-looking": 21,
        "possible-nt-oriented-balanced": 64,
        "strong-support": 6,
        "moderate-support": 8,
        "long-independent-suit": 29,
        "short-support-weak/no-action": 36,
    }
    assert sum(AUDIT.primary_partitions.values()) == AUDIT.population
    assert sum(sum(rows.values()) for rows in AUDIT.opening_partitions.values()) == AUDIT.population
    assert all(row["primary_category"] in AUDIT.primary_partitions for row in AUDIT.positions)


def test_matrix_classifies_every_observed_family_and_no_subset_is_executable():
    allowed = {"SOURCE_PARTIAL", "LOW_SAMPLE"}
    assert sum(row["observed_count"] for row in AUDIT.source_matrix) == AUDIT.population
    assert all(row["classification"] in allowed for row in AUDIT.source_matrix)
    assert all(not row["executable_subset"] for row in AUDIT.source_matrix)
    assert AUDIT.source_safe_candidates == ()
    assert AUDIT.decision == "E. DEFER THREE-LEVEL PREEMPT RESPONSES"


def test_ranking_and_phase12s_selection_are_deterministic():
    assert [row["family_id"] for row in AUDIT.top_candidates] == [
        "three-level-preempt.3c.possible-nt-oriented-balanced",
        "three-level-preempt.3d.possible-nt-oriented-balanced",
        "three-level-preempt.3h.possible-nt-oriented-balanced",
        "three-level-preempt.3s.possible-nt-oriented-balanced",
        "three-level-preempt.3h.long-independent-suit",
    ]
    assert AUDIT.phase12s_recommendation["family_id"] == "response.weak-two"
    assert AUDIT.phase12s_recommendation["exact_prefixes"] == ("2D P", "2H P", "2S P")
    assert AUDIT.phase12s_recommendation["phase12m_population"] == 540


def test_router_policy_and_production_surface_are_unchanged():
    assert AUDIT.route_count == len(create_standard_sayc_router().routes) == 45
    assert all(row["route_missing"] for row in AUDIT.positions)
    assert all(not row["route_reaches_rule"] for row in AUDIT.positions)
    assert (AUDIT.production_rules_added, AUDIT.routes_added, AUDIT.policies_added) == (0, 0, 0)
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    module = __import__("benchmarks.three_level_preempt_response_source_readiness_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source


def test_prior_invariants_defaults_and_knowledge_are_unchanged():
    assert AUDIT.phase12q_population == 1194
    assert AUDIT.phase12n_calls == 24
    assert AUDIT.phase12o_residual == 23
    assert AUDIT.phase12p_decision.startswith("E.")
    assert AUDIT.phase12g_calls == {"4H": 17, "4S": 21}
    assert AUDIT.phase12h_residual == 197
    assert AUDIT.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert AUDIT.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert AUDIT.production_defaults_changed is False
    assert AUDIT.knowledge_markdown_changed == 0


def test_repeated_runs_are_structurally_identical():
    assert AUDIT == run_three_level_preempt_response_source_readiness_audit()
