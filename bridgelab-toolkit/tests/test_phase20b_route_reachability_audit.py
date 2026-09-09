from __future__ import annotations

import inspect

from benchmarks.phase20b_route_reachability_audit import (
    ConfigurationReachability,
    ObservedBenchmarkStatus,
    OwnershipClassification,
    PolicyState,
    PrefixCollisionClassification,
    WitnessStatus,
    run_route_reachability_audit,
    structural_context,
)
from bridge.declarer_recommendation import DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.probability_questions import KnownCardCountQuestion
from bridge.sayc_route_configuration import create_standard_sayc_router


AUDIT = run_route_reachability_audit()


def test_inventory_has_exact_production_registration_order() -> None:
    router = create_standard_sayc_router()
    assert AUDIT.route_count == len(router.routes) == 45
    assert tuple(entry.registration_order for entry in AUDIT.inventory) == tuple(range(45))
    assert tuple(entry.route_id for entry in AUDIT.inventory) == tuple(
        route.route_id for route in router.routes
    )
    assert tuple(entry.priority for entry in AUDIT.inventory) == tuple(
        route.priority for route in router.routes
    )


def test_route_ids_and_exact_prefixes_are_unique() -> None:
    route_ids = tuple(entry.route_id.casefold() for entry in AUDIT.inventory)
    prefixes = tuple(entry.auction_prefix for entry in AUDIT.inventory)
    assert len(set(route_ids)) == AUDIT.unique_route_ids == 45
    assert len(set(prefixes)) == AUDIT.unique_exact_prefixes == 45
    assert AUDIT.duplicate_route_ids == AUDIT.duplicate_exact_prefixes == 0


def test_every_route_has_an_exposed_nonempty_owner_registry() -> None:
    router = create_standard_sayc_router()
    assert all(route.engine is not None for route in router.routes)
    assert all(entry.rule_ids for entry in AUDIT.inventory)
    assert all(entry.production_modules for entry in AUDIT.inventory)
    assert all(entry.engine_type.endswith(".BiddingEngine") for entry in AUDIT.inventory)


def test_every_structural_prefix_parses_and_dispatches_to_intended_route() -> None:
    router = create_standard_sayc_router()
    for entry in AUDIT.inventory:
        context = structural_context(entry.auction_prefix)
        match = router.match(context)
        assert match is not None
        assert match.route_id == entry.route_id
        assert match.registration_order == entry.registration_order
        assert match.priority == entry.priority
    assert AUDIT.structurally_matched_routes == 45


def test_structural_matching_is_not_recommendation_evidence() -> None:
    router = create_standard_sayc_router()
    entry = next(
        item
        for item in AUDIT.inventory
        if item.route_id == "sayc.responder.1nt.jacoby.hearts.continuation"
    )
    context = structural_context(entry.auction_prefix)
    assert router.match(context) is not None
    assert not router.evaluate(context).has_recommendation


def test_ownership_classification_is_exhaustive_and_clean() -> None:
    allowed = {OwnershipClassification.UNIQUE_OWNER, OwnershipClassification.SHARED_OWNER_EXPECTED}
    assert {entry.ownership for entry in AUDIT.inventory} <= allowed
    assert all(isinstance(entry.ownership, OwnershipClassification) for entry in AUDIT.inventory)
    assert AUDIT.missing_owners == 0
    assert AUDIT.duplicate_route_ids == 0
    assert AUDIT.ambiguous_owners == 0


def test_prefix_classification_is_exhaustive_and_exact_only() -> None:
    assert all(
        entry.prefix_collision is PrefixCollisionClassification.UNIQUE_EXACT_PREFIX
        for entry in AUDIT.inventory
    )
    assert AUDIT.duplicate_exact_prefixes == 0
    prefixes = set(entry.auction_prefix for entry in AUDIT.inventory)
    assert ("1NT", "P") in prefixes
    assert ("1NT", "P", "2D", "P") in prefixes


def test_reachability_classification_is_exhaustive_and_clean() -> None:
    reachable = {ConfigurationReachability.REACHABLE, ConfigurationReachability.REACHABLE_POLICY_GATED}
    assert {entry.configuration_reachability for entry in AUDIT.inventory} <= reachable
    assert AUDIT.invalid_prefixes == 0
    assert AUDIT.shadowed_routes == 0
    assert AUDIT.unreachable_routes == 0


def test_witness_and_observed_statuses_preserve_scope() -> None:
    assert all(
        entry.witness_status is WitnessStatus.DERIVABLE_WITHOUT_BRIDGE_THEORY
        for entry in AUDIT.inventory
    )
    assert all(
        entry.observed_benchmark_status is ObservedBenchmarkStatus.UNKNOWN
        for entry in AUDIT.inventory
    )


def test_policy_dependencies_are_derived_and_exhaustive() -> None:
    expected = {
        "jacoby_continuation_strength",
        "offensive_hand",
        "opponent_suit_shortness",
        "playing_strength",
        "stayman_continuation_strength",
        "stayman_dual_major_response",
        "stopper",
        "suit_quality",
        "support_double_eligibility",
        "takeout_advancer_strength",
    }
    actual = {dependency for entry in AUDIT.inventory for dependency in entry.policy_dependencies}
    assert actual == expected
    assert AUDIT.policy_gated_routes == 19
    assert PolicyState.NO_POLICY_REQUIRED.value == "NO_POLICY_REQUIRED"
    assert all(isinstance(entry.policy_dependencies, tuple) for entry in AUDIT.inventory)


def test_router_has_no_fallback() -> None:
    router = create_standard_sayc_router()
    assert router._fallback is None


def test_probability_and_declarer_production_invariants() -> None:
    assert DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types == (
        KnownCardCountQuestion.__name__,
    )
    assert tuple(DeclarerTechnique) == (DeclarerTechnique.SIMPLE_UNBLOCK_KING,)
    assert not any(name in {"RestrictedChoiceQuestion", "VacantPlacesQuestion"} for name in DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types)


def test_historical_closure_and_ordinary_baselines_are_not_reinterpreted() -> None:
    assert AUDIT.historical_recommendation_baseline == 4
    assert (
        AUDIT.ordinary_production_calls,
        AUDIT.ordinary_completed_auctions,
        AUDIT.ordinary_abstaining_deals,
    ) == (7_871, 761, 9_239)


def test_audit_is_deterministic() -> None:
    assert AUDIT == run_route_reachability_audit()


def test_benchmark_is_audit_only() -> None:
    module = __import__("benchmarks.phase20b_route_reachability_audit", fromlist=["unused"])
    source = inspect.getsource(module)
    assert "EngineRoute(" not in source
    assert "RuleDecision.recommend(" not in source
    assert "from_policies(" not in source
