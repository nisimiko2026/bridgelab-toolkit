import inspect

from benchmarks.natural_one_notrump_response_source_readiness_audit import (
    FAMILY_ORDER,
    run_natural_one_notrump_response_source_readiness_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


AUDIT = run_natural_one_notrump_response_source_readiness_audit()


def test_exact_sample_inventory_and_stable_families():
    assert (AUDIT.start_seed, AUDIT.deal_count) == (1, 10_000)
    assert AUDIT.candidate_total == 124
    assert tuple(row["family_id"] for row in AUDIT.candidates) == FAMILY_ORDER
    assert all(row["observed_count"] > 0 for row in AUDIT.candidates)
    assert len({row["stable_id"] for row in AUDIT.positions}) == 124


def test_stayman_jacoby_and_deferred_positions_are_excluded():
    assert AUDIT.phase12m_one_notrump_abstentions == 271
    assert AUDIT.exclusions == {
        "jacoby_five_plus_major": 5,
        "stayman_exactly_four_major": 142,
    }
    assert 271 - 5 - 142 == AUDIT.candidate_total
    assert all(row["suit_lengths_shdc"]["H"] < 4 for row in AUDIT.positions)
    assert all(row["suit_lengths_shdc"]["S"] < 4 for row in AUDIT.positions)
    assert "stayman" not in AUDIT.decision.casefold()


def test_exact_family_counts_hcp_and_shapes():
    rows = {row["family_id"]: row for row in AUDIT.candidates}
    assert {name: rows[name]["observed_count"] for name in FAMILY_ORDER} == {
        "natural.pass.balanced-0-7": 41,
        "natural.2nt.balanced-8-9": 9,
        "natural.3nt.balanced-10-15": 27,
        "natural.minor-oriented.unbalanced": 45,
        "natural.balanced-slam-interest-16-plus": 2,
    }
    assert rows["natural.2nt.balanced-8-9"]["hcp_distribution"] == {8: 3, 9: 6}
    assert rows["natural.balanced-slam-interest-16-plus"]["hcp_distribution"] == {17: 2}
    assert all(sum(row["shape_characteristics"].values()) == row["observed_count"] for row in AUDIT.candidates)


def test_source_matrix_ranking_and_decision_are_complete():
    assert all(row["classification"] in {"SOURCE_PARTIAL", "PARTNERSHIP_DEPENDENT"} for row in AUDIT.candidates)
    assert all(row["executable_subset"] is False for row in AUDIT.candidates)
    assert all(len(row["source_audit"]) == 12 for row in AUDIT.candidates)
    assert AUDIT.source_safe_candidates == ()
    assert AUDIT.ranked_family_ids[0] == "natural.2nt.balanced-8-9"
    assert AUDIT.decision == "E. DEFER NATURAL 1NT RESPONSE FAMILY"
    assert "responder.rebid-after-opener-rebid" in AUDIT.phase12q_recommendation


def test_router_and_audit_only_guards():
    assert AUDIT.route_count == len(create_standard_sayc_router().routes) == 45
    assert all(row["route_id"] == "sayc.response.1nt.jacoby" for row in AUDIT.positions)
    assert all(row["route_reaches_rule"] is True for row in AUDIT.positions)
    assert all(row["current_action"] == "ABSTAIN" for row in AUDIT.positions)
    assert (AUDIT.production_rules_added, AUDIT.routes_added, AUDIT.policies_added) == (0, 0, 0)
    module = __import__("benchmarks.natural_one_notrump_response_source_readiness_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source
    assert "from_policies(" not in source


def test_defaults_prior_invariants_and_knowledge_are_unchanged():
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    assert AUDIT.phase12n_calls == 24
    assert AUDIT.phase12o_residual == 23
    assert AUDIT.phase12g_calls == {"4H": 17, "4S": 21}
    assert AUDIT.phase12h_residual == 197
    assert AUDIT.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert AUDIT.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert AUDIT.production_defaults_changed is False
    assert AUDIT.knowledge_markdown_changed == 0


def test_audit_is_structurally_deterministic():
    assert AUDIT == run_natural_one_notrump_response_source_readiness_audit()
