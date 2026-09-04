import inspect

from benchmarks.next_family_source_readiness_audit import (
    READINESS,
    run_next_family_source_readiness_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router

AUDIT = run_next_family_source_readiness_audit()


def test_exact_sample_inventory_ids_counts_and_classifications():
    audit = AUDIT
    assert (audit.start_seed, audit.deal_count) == (1, 10_000)
    assert audit.candidates
    assert len({row.family_id for row in audit.candidates}) == len(audit.candidates)
    assert all(row.observed_count > 0 for row in audit.candidates)
    assert all(row.classification in READINESS for row in audit.candidates)


def test_deferred_stayman_families_are_not_selected():
    audit = AUDIT
    assert {row["observed_count"] for row in audit.deferred_families} == {197, 31, 29}
    assert all(row["classification"] == "DEFERRED_EXISTING" for row in audit.deferred_families)
    assert "stayman" not in audit.selected_family_id


def test_top_five_and_phase12n_selection_are_exact():
    audit = AUDIT
    assert [row["family_id"] for row in audit.top_five] == [
        "opener.strong-two-club-after-waiting", "response.one-notrump",
        "responder.rebid-after-opener-rebid", "response.three-level-preempt",
        "response.weak-two",
    ]
    assert [row["observed_count"] for row in audit.top_five] == [47, 271, 1194, 166, 540]
    assert audit.selected_subset_count == 24
    assert audit.decision == "D. ONLY A NARROW SUBSET IS IMPLEMENTABLE"
    assert audit.phase12n_specification["expected_calls"] == ("2NT",)


def test_production_and_prior_phase_guards_are_unchanged():
    audit = AUDIT
    assert audit.route_count == len(create_standard_sayc_router().routes) == 44
    assert audit.default_policies == {"stayman_dual_major": None, "stayman_continuation": None, "jacoby_continuation": None}
    registry = PolicyRegistry()
    assert registry.stayman_dual_major_response_policy_ids == ()
    assert registry.stayman_continuation_strength_policy_ids == ()
    assert registry.jacoby_continuation_strength_policy("missing") is None
    assert audit.phase12g_calls == {"4H": 17, "4S": 21}
    assert audit.phase12h_residual == 197
    assert audit.phase12l_terminal == {"HEARTS": 5, "SPADES": 7}
    assert audit.jacoby_no_policy == {"heart_transfer": 62, "spade_transfer": 61, "total": 123}
    assert (audit.production_rules_added, audit.policies_added) == (0, 0)
    assert audit.production_defaults_changed is False
    assert audit.knowledge_markdown_changed == 0


def test_phase12m_is_structurally_deterministic_and_audit_only():
    assert AUDIT == run_next_family_source_readiness_audit()
    module = __import__("benchmarks.next_family_source_readiness_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source
    assert "from_policies(" not in source
