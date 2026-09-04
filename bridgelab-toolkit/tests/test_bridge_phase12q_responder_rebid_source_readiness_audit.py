import inspect

from benchmarks.responder_rebid_source_readiness_audit import (
    run_responder_rebid_source_readiness_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


AUDIT = run_responder_rebid_source_readiness_audit()


def test_exact_sample_population_families_and_identity():
    assert (AUDIT.start_seed, AUDIT.deal_count) == (1, 10_000)
    assert AUDIT.population == 1194
    assert AUDIT.family_count == 34
    assert len({row["family_id"] for row in AUDIT.families}) == 34
    assert len({row["stable_id"] for row in AUDIT.positions}) == 1194


def test_every_position_has_exactly_one_family_and_counts_reconcile():
    family_ids = {row["family_id"] for row in AUDIT.families}
    assert all(row["family_id"] in family_ids for row in AUDIT.positions)
    assert sum(row["observed_count"] for row in AUDIT.families) == AUDIT.population
    assert all(sum(row["hcp_distribution"].values()) == row["observed_count"] for row in AUDIT.families)
    assert all(sum(row["shape_distribution"].values()) == row["observed_count"] for row in AUDIT.families)


def test_classifications_top_five_and_selection_are_deterministic():
    allowed = {"SOURCE_PARTIAL", "POLICY_REQUIRED", "LOW_SAMPLE"}
    assert all(row["classification"] in allowed for row in AUDIT.families)
    assert [row["family_id"] for row in AUDIT.top_five] == [
        "responder-rebid.1nt-2d-2h",
        "responder-rebid.1nt-2h-2s",
        "responder-rebid.1c-1s-2d",
        "responder-rebid.1c-1h-1s",
        "responder-rebid.1d-1s-2c",
    ]
    assert [row["observed_count"] for row in AUDIT.top_five] == [62, 61, 30, 67, 56]
    assert AUDIT.source_safe_candidates == ()
    assert AUDIT.decision == "E. DEFER RESPONDER-REBID FAMILY"
    assert AUDIT.phase12r_specification["deterministic_population"] == 166


def test_route_status_is_exact_and_audit_only():
    assert AUDIT.route_count == len(create_standard_sayc_router().routes) == 45
    routed = [row for row in AUDIT.families if row["route_exists"]]
    assert {row["route_name"] for row in routed} == {
        "sayc.responder.1nt.jacoby.hearts.continuation",
        "sayc.responder.1nt.jacoby.spades.continuation",
    }
    assert sum(row["observed_count"] for row in routed) == 123
    assert all(row["route_missing"] for row in AUDIT.families if not row["route_exists"])
    assert (AUDIT.production_rules_added, AUDIT.routes_added, AUDIT.policies_added) == (0, 0, 0)
    module = __import__("benchmarks.responder_rebid_source_readiness_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source


def test_defaults_prior_invariants_and_knowledge_are_unchanged():
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    assert AUDIT.phase12n_calls == 24
    assert AUDIT.phase12o_residual == 23
    assert AUDIT.phase12p_decision.startswith("E.")
    assert AUDIT.phase12g_calls == {"4H": 17, "4S": 21}
    assert AUDIT.phase12h_residual == 197
    assert AUDIT.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert AUDIT.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert AUDIT.production_defaults_changed is False
    assert AUDIT.knowledge_markdown_changed == 0


def test_audit_is_structurally_deterministic():
    assert AUDIT == run_responder_rebid_source_readiness_audit()
