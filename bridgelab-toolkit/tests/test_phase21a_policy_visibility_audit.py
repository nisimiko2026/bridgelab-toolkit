from __future__ import annotations

import inspect
from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from benchmarks.phase20b_route_reachability_audit import (
    run_route_reachability_audit,
)
from benchmarks.phase20c_abstention_taxonomy_audit import (
    AbstentionCategory,
    classify_abstentions,
)
from benchmarks.phase20d_production_audit_drift_guard import (
    DEFAULT_BASELINE,
)
from benchmarks.phase21a_policy_visibility_audit import (
    DecisionOutcome,
    PolicyObservationState,
    PolicyRequirementState,
    build_policy_visibility_audit,
)
from bridge.declarer_recommendation import DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.probability_questions import KnownCardCountQuestion
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


@pytest.fixture(scope="module")
def coverage_report():
    return run_sayc_coverage_benchmark(start_seed=1, count=10_000)


@pytest.fixture(scope="module")
def audit(coverage_report):
    return build_policy_visibility_audit(coverage_report)


def test_static_matrix_contains_each_live_route_once(audit) -> None:
    router = create_standard_sayc_router()
    assert len(audit.routes) == len(router.routes) == 45
    assert tuple(route.route_id for route in audit.routes) == tuple(
        route.route_id for route in router.routes
    )
    assert len({route.route_id.casefold() for route in audit.routes}) == 45
    assert len({route.auction_prefix for route in audit.routes}) == 45


def test_policy_gating_and_dependencies_reuse_phase20b(audit) -> None:
    structural = run_route_reachability_audit()
    assert audit.policy_gated_route_count == structural.policy_gated_routes == 19
    assert sum(
        route.policy_requirement is PolicyRequirementState.POLICY_GATED
        for route in audit.routes
    ) == 19
    assert tuple(route.policy_dependencies for route in audit.routes) == tuple(
        route.policy_dependencies for route in structural.inventory
    )
    assert tuple(route.ownership for route in audit.routes) == tuple(
        route.ownership.value for route in structural.inventory
    )


def test_dependency_incidences_are_reviewed_phase_baseline(audit) -> None:
    assert audit.dependency_incidences == (
        ("jacoby_continuation_strength", 2),
        ("offensive_hand", 4),
        ("opponent_suit_shortness", 4),
        ("playing_strength", 4),
        ("stayman_continuation_strength", 2),
        ("stayman_dual_major_response", 1),
        ("stopper", 4),
        ("suit_quality", 6),
        ("support_double_eligibility", 4),
        ("takeout_advancer_strength", 4),
    )


def test_no_route_events_are_never_policy_failures(audit) -> None:
    events = tuple(
        event for event in audit.events if event.outcome is DecisionOutcome.NO_ROUTE
    )
    assert len(events) == audit.no_route_count == 1_936
    assert all(event.matched_route_id is None for event in events)
    assert all(event.policy_dependencies == () for event in events)
    assert all(
        event.policy_observation is PolicyObservationState.NOT_APPLICABLE
        for event in events
    )


def test_phase20c_taxonomy_and_policy_split_are_preserved(
    audit, coverage_report
) -> None:
    phase20c = classify_abstentions(coverage_report)
    assert audit.taxonomy_counts == phase20c.category_counts
    assert audit.policy_route_counts == phase20c.policy_route_counts
    assert audit.taxonomy_counts == (
        (AbstentionCategory.NO_ROUTE_MATCH.value, 1_936),
        (
            AbstentionCategory.ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN.value,
            123,
        ),
        (AbstentionCategory.ROUTE_MATCH_RULE_ABSTAIN.value, 7_180),
    )
    assert audit.policy_route_counts == (
        ("sayc.responder.1nt.jacoby.hearts.continuation", 62),
        ("sayc.responder.1nt.jacoby.spades.continuation", 61),
    )


def test_policy_referenced_events_require_explicit_rejection_evidence(audit) -> None:
    referenced = tuple(
        event
        for event in audit.events
        if event.policy_observation is PolicyObservationState.POLICY_REFERENCED
    )
    assert len(referenced) == 123
    assert all(event.outcome is DecisionOutcome.ABSTAIN for event in referenced)
    assert all(
        any("policy" in explanation.casefold() for explanation in event.rejection_explanations)
        for event in referenced
    )
    assert all(event.policy_dependencies for event in referenced)


def test_policy_gated_non_explicit_events_remain_unknown(audit) -> None:
    unknown = tuple(
        event
        for event in audit.events
        if event.policy_observation is PolicyObservationState.UNKNOWN
    )
    assert unknown
    assert all(event.matched_route_id is not None for event in unknown)
    assert all(event.policy_dependencies for event in unknown)
    assert all(
        event.outcome in {DecisionOutcome.RECOMMEND, DecisionOutcome.ABSTAIN}
        for event in unknown
    )


def test_recommendation_and_abstention_are_distinct(audit) -> None:
    outcomes = Counter(event.outcome for event in audit.events)
    assert outcomes[DecisionOutcome.RECOMMEND] > 0
    assert outcomes[DecisionOutcome.ABSTAIN] >= 123
    assert outcomes[DecisionOutcome.NO_ROUTE] == 1_936
    assert all(
        event.recommended_rule_id is not None
        for event in audit.events
        if event.outcome is DecisionOutcome.RECOMMEND
    )
    assert all(
        event.recommended_rule_id is None
        for event in audit.events
        if event.outcome is not DecisionOutcome.RECOMMEND
    )


def test_recommendation_route_and_rule_consistency(audit) -> None:
    routes = {route.route_id: route for route in audit.routes}
    for event in audit.events:
        if event.matched_route_id is None:
            continue
        assert event.matched_route_id in routes
        assert event.policy_dependencies == routes[event.matched_route_id].policy_dependencies
        if event.outcome is DecisionOutcome.RECOMMEND:
            assert event.recommended_rule_id in event.applicable_rule_ids


def test_route_summaries_cover_all_routes_and_reconcile(audit) -> None:
    assert len(audit.route_summaries) == 45
    assert tuple(item.route_id for item in audit.route_summaries) == tuple(
        route.route_id for route in audit.routes
    )
    for summary in audit.route_summaries:
        assert summary.event_count == (
            summary.recommendation_count + summary.abstention_count
        )
        assert summary.observed is (summary.event_count > 0)
    assert sum(
        item.policy_referenced_abstention_count for item in audit.route_summaries
    ) == 123


def test_records_and_result_containers_are_immutable(audit) -> None:
    with pytest.raises(FrozenInstanceError):
        audit.routes[0].route_id = "changed"
    with pytest.raises(FrozenInstanceError):
        audit.events[0].seed = -1
    with pytest.raises(FrozenInstanceError):
        audit.route_summaries[0].observed = False
    assert isinstance(audit.routes, tuple)
    assert isinstance(audit.events, tuple)
    assert isinstance(audit.route_summaries, tuple)


def test_event_order_and_repeated_build_are_deterministic(audit, coverage_report) -> None:
    keys = tuple(
        (event.seed, event.decision_number, event.outcome.value, event.matched_route_id or "")
        for event in audit.events
    )
    assert keys == tuple(sorted(keys))
    assert audit == build_policy_visibility_audit(coverage_report)


def test_system_options_are_raw_diagnostics_not_policy_absence(audit) -> None:
    assert all(isinstance(event.system_options, tuple) for event in audit.events)
    assert {state.value for state in PolicyObservationState} == {
        "NOT_APPLICABLE",
        "POLICY_REFERENCED",
        "UNKNOWN",
    }
    assert not hasattr(PolicyObservationState, "POLICY_PRESENT")
    assert not hasattr(PolicyObservationState, "POLICY_ABSENT")


def test_ordinary_benchmark_and_phase20d_baselines_remain_compatible(audit) -> None:
    assert (
        audit.corpus_size,
        audit.production_calls,
        audit.completed_auctions,
        audit.abstentions,
    ) == (10_000, 7_871, 761, 9_239)
    assert DEFAULT_BASELINE.structural.route_count == len(audit.routes)
    assert (
        DEFAULT_BASELINE.structural.policy_gated_routes
        == audit.policy_gated_route_count
    )
    assert DEFAULT_BASELINE.behavioral.category_counts == audit.taxonomy_counts
    assert DEFAULT_BASELINE.behavioral.policy_route_counts == audit.policy_route_counts


def test_production_registries_and_declarer_techniques_are_unchanged() -> None:
    assert DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types == (
        KnownCardCountQuestion.__name__,
    )
    assert tuple(DeclarerTechnique) == (DeclarerTechnique.SIMPLE_UNBLOCK_KING,)


def test_audit_has_no_second_dependency_map_or_production_mutation(
    coverage_report,
) -> None:
    route_ids_before = tuple(
        route.route_id for route in create_standard_sayc_router().routes
    )
    probability_types_before = (
        DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types
    )
    declarer_before = tuple(DeclarerTechnique)
    build_policy_visibility_audit(coverage_report)
    assert tuple(
        route.route_id for route in create_standard_sayc_router().routes
    ) == route_ids_before
    assert (
        DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types
        == probability_types_before
    )
    assert tuple(DeclarerTechnique) == declarer_before

    module = __import__(
        "benchmarks.phase21a_policy_visibility_audit", fromlist=["unused"]
    )
    source = inspect.getsource(module)
    forbidden = (
        "_RULE_POLICY_MARKERS",
        "EngineRoute(",
        "PolicyRegistry(",
        "RuleDecision.recommend(",
        "from_policies(",
    )
    assert not any(token in source for token in forbidden)
    assert "run_route_reachability_audit" in source
    assert "classify_abstentions" in source
