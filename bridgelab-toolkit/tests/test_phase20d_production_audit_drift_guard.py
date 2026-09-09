from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from benchmarks.phase20d_production_audit_drift_guard import (
    DEFAULT_BASELINE,
    BaselineStatus,
    DriftClass,
    compare_baseline,
    run_production_audit_drift_guard,
)


@pytest.fixture(scope="module")
def guard():
    return run_production_audit_drift_guard()


def _compare(guard, **changes):
    expected = replace(DEFAULT_BASELINE, **changes)
    return compare_baseline(expected, guard.observations)


def test_current_reviewed_baseline_passes(guard) -> None:
    assert guard.passed
    assert guard.findings == ()


def test_structural_baseline_matches_phase20b(guard) -> None:
    actual = guard.observations.structural.values
    assert actual == DEFAULT_BASELINE.structural
    assert actual.route_count == actual.unique_route_ids == 45
    assert actual.unique_exact_prefixes == actual.structurally_matched_routes == 45
    assert actual.unique_owner_count == 7
    assert actual.shared_owner_expected_count == 38
    assert actual.policy_gated_routes == 19


def test_hard_structural_invariants_pass(guard) -> None:
    actual = guard.observations.structural.values
    assert actual.duplicate_route_ids == 0
    assert actual.duplicate_exact_prefixes == 0
    assert actual.invalid_prefixes == 0
    assert actual.missing_owners == 0
    assert actual.ambiguous_owners == 0


def test_behavioral_baseline_matches_phase20c(guard) -> None:
    actual = guard.observations.behavioral
    assert actual == DEFAULT_BASELINE.behavioral
    assert (
        actual.corpus_size,
        actual.seed_start,
        actual.seed_end,
        actual.production_calls,
        actual.completed_auctions,
        actual.abstentions,
    ) == (10_000, 1, 10_000, 7_871, 761, 9_239)


def test_taxonomy_and_policy_split_match(guard) -> None:
    actual = guard.observations.behavioral
    assert actual.category_counts == (
        ("NO_ROUTE_MATCH", 1_936),
        ("ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN", 123),
        ("ROUTE_MATCH_RULE_ABSTAIN", 7_180),
    )
    assert sum(count for _, count in actual.category_counts) == actual.abstentions
    assert guard.observations.behavioral_classified_total == actual.abstentions
    assert guard.observations.behavioral_unique_seed_count == actual.abstentions
    assert guard.observations.behavioral_categories == tuple(
        sorted(name for name, _ in actual.category_counts)
    )
    assert actual.policy_route_counts == (
        ("sayc.responder.1nt.jacoby.hearts.continuation", 62),
        ("sayc.responder.1nt.jacoby.spades.continuation", 61),
    )


def test_artificial_route_count_drift_is_detected(guard) -> None:
    structural = replace(DEFAULT_BASELINE.structural, route_count=44)
    findings = _compare(guard, structural=structural)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.drift_class is DriftClass.STRUCTURAL_ROUTE_DRIFT
    assert (finding.field, finding.expected, finding.observed) == (
        "route_count", 44, 45
    )
    assert finding.authority == "Phase20B"


def test_artificial_abstention_total_drift_is_detected(guard) -> None:
    behavioral = replace(DEFAULT_BASELINE.behavioral, abstentions=9_238)
    findings = _compare(guard, behavioral=behavioral)
    assert len(findings) == 1
    assert findings[0].drift_class is DriftClass.ORDINARY_BENCHMARK_DRIFT
    assert (findings[0].expected, findings[0].observed) == (9_238, 9_239)


def test_artificial_taxonomy_drift_is_detected(guard) -> None:
    counts = (("NO_ROUTE_MATCH", 1_935), *DEFAULT_BASELINE.behavioral.category_counts[1:])
    behavioral = replace(DEFAULT_BASELINE.behavioral, category_counts=counts)
    findings = _compare(guard, behavioral=behavioral)
    assert len(findings) == 1
    assert findings[0].drift_class is DriftClass.ABSTENTION_TAXONOMY_DRIFT
    assert findings[0].field == "category_counts"


def test_artificial_registry_drift_is_detected_without_mutation(guard) -> None:
    registry = replace(
        DEFAULT_BASELINE.registry,
        probability_question_types=("KnownCardCountQuestion", "VacantPlacesQuestion"),
    )
    findings = _compare(guard, registry=registry)
    assert len(findings) == 1
    assert findings[0].drift_class is DriftClass.PRODUCTION_REGISTRY_DRIFT
    assert findings[0].field == "probability_question_types"


def test_historical_recommendation_record_drift_is_labeled(guard) -> None:
    findings = _compare(guard, recommendation_closure_record=3)
    assert len(findings) == 1
    assert findings[0].drift_class is DriftClass.RECOMMENDATION_CLOSURE_RECORD_DRIFT
    assert findings[0].baseline_status is BaselineStatus.HISTORICAL_BASELINE_ONLY
    assert guard.observations.recommendation_closure_record == 4


def test_findings_are_actionable_and_deterministic(guard) -> None:
    expected = replace(
        DEFAULT_BASELINE,
        structural=replace(DEFAULT_BASELINE.structural, route_count=44),
        behavioral=replace(DEFAULT_BASELINE.behavioral, abstentions=9_238),
    )
    first = compare_baseline(expected, guard.observations)
    second = compare_baseline(expected, guard.observations)
    assert first == second
    assert tuple(item.format() for item in first) == tuple(item.format() for item in second)
    assert all("expected=" in item.format() and "observed=" in item.format() for item in first)
    assert all("authority=" in item.format() and "status=" in item.format() for item in first)


def test_registry_and_deferred_probability_guards(guard) -> None:
    registry = guard.observations.registry
    assert registry.probability_question_types == ("KnownCardCountQuestion",)
    assert not registry.restricted_choice_registered
    assert not registry.vacant_places_registered
    assert registry.declarer_techniques == ("simple-unblock-king",)
    assert registry.defensive_algorithms == registry.opening_lead_algorithms == 0


def test_observe_only_and_document_only_metadata_do_not_fail(guard) -> None:
    assert guard.observations.structural.registration_order
    assert guard.observations.structural.priorities
    assert guard.observations.top_stopped_prefixes
    assert DEFAULT_BASELINE.natural_one_notrump_status is BaselineStatus.DOCUMENT_ONLY
    altered_observations = replace(
        guard.observations,
        structural=replace(
            guard.observations.structural,
            registration_order=("diagnostic-only",),
            priorities=(("diagnostic-only", -1),),
        ),
        top_stopped_prefixes=(),
    )
    altered_expected = replace(
        DEFAULT_BASELINE,
        natural_one_notrump_status=BaselineStatus.HARD_INVARIANT,
    )
    assert compare_baseline(altered_expected, altered_observations) == ()


def test_guard_is_audit_only_and_adds_no_recommendation() -> None:
    module = __import__(
        "benchmarks.phase20d_production_audit_drift_guard", fromlist=["unused"]
    )
    source = inspect.getsource(module)
    forbidden = (
        "EngineRoute(", "RuleDecision.recommend(", "from_policies(",
        "run_seeded_batch(", "create_standard_sayc_router(",
    )
    assert not any(token in source for token in forbidden)
