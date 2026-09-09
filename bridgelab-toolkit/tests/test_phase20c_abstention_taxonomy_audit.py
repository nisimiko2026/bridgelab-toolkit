from __future__ import annotations

import inspect

import pytest

from benchmarks.phase20c_abstention_taxonomy_audit import (
    _has_policy_reference,
    AbstentionCategory,
    classify_abstentions,
    reconstruct_stopped_context,
)
from bridge.auction_simulation import SimulationStopReason
from bridge.declarer_recommendation import DeclarerTechnique
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY
from bridge.probability_questions import KnownCardCountQuestion
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router


@pytest.fixture(scope="module")
def report():
    return run_sayc_coverage_benchmark(start_seed=1, count=10_000)


@pytest.fixture(scope="module")
def audit(report):
    return classify_abstentions(report)


def test_exact_deterministic_corpus(report, audit) -> None:
    assert audit.start_seed == 1
    assert audit.corpus_size == 10_000
    assert audit.seeds == tuple(range(1, 10_001))
    assert report.batch.replay_records[0][0] == 1
    assert report.batch.replay_records[-1][0] == 10_000


def test_ordinary_benchmark_baseline_is_unchanged(audit) -> None:
    assert (
        audit.production_calls,
        audit.completed_auctions,
        audit.abstentions,
    ) == (7_871, 761, 9_239)


def test_exact_taxonomy_counts(audit) -> None:
    assert audit.count(AbstentionCategory.NO_ROUTE_MATCH) == 1_936
    assert (
        audit.count(AbstentionCategory.ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN)
        == 123
    )
    assert audit.count(AbstentionCategory.ROUTE_MATCH_RULE_ABSTAIN) == 7_180
    assert 1_936 + 123 + 7_180 == audit.classified_total == audit.abstentions


def test_taxonomy_is_mutually_exclusive_and_exhaustive(audit) -> None:
    assert len(audit.observations) == len({item.seed for item in audit.observations})
    assert {item.category for item in audit.observations} == set(AbstentionCategory)
    assert sum(count for _, count in audit.category_counts) == audit.abstentions


def test_every_observation_was_a_no_recommendation_stop(audit) -> None:
    assert all(
        item.stop_reason == SimulationStopReason.NO_RECOMMENDATION.value
        for item in audit.observations
    )


def test_reconstructed_context_is_deterministic(report) -> None:
    case = next(
        case
        for case in report.batch.cases
        if case.result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    )
    first = reconstruct_stopped_context(case, report.batch)
    second = reconstruct_stopped_context(case, report.batch)
    assert first.hand == second.hand
    assert first.evaluation == second.evaluation
    assert first.seat is second.seat
    assert first.vulnerability is second.vulnerability
    assert first.system == second.system
    assert first.auction.serialize() == second.auction.serialize()
    assert first.seat is case.result.stopped_seat
    assert first.auction.serialize() == case.result.final_auction


def test_no_route_category_reconstructs_to_no_match(report, audit) -> None:
    router = create_standard_sayc_router()
    cases = {case.deal.seed: case for case in report.batch.cases}
    for item in audit.observations:
        if item.category is AbstentionCategory.NO_ROUTE_MATCH:
            context = reconstruct_stopped_context(cases[item.seed], report.batch)
            assert router.match(context) is None
            assert item.matched_route_id is None


def test_matched_categories_reconstruct_to_same_abstaining_route(report, audit) -> None:
    router = create_standard_sayc_router()
    cases = {case.deal.seed: case for case in report.batch.cases}
    for item in audit.observations:
        if item.category is AbstentionCategory.NO_ROUTE_MATCH:
            continue
        context = reconstruct_stopped_context(cases[item.seed], report.batch)
        match = router.match(context)
        assert match is not None
        assert match.route_id == item.matched_route_id
        assert not match.engine.evaluate(context).has_recommendation


def test_policy_category_requires_explicit_rejection_reference(audit) -> None:
    policy = tuple(
        item
        for item in audit.observations
        if item.category
        is AbstentionCategory.ROUTE_MATCH_POLICY_REFERENCED_ABSTAIN
    )
    assert len(policy) == 123
    assert all(item.has_policy_reference for item in policy)
    assert all(item.rejection_rule_ids for item in policy)
    assert _has_policy_reference(("A policy is required.",))
    assert not _has_policy_reference(("An unrelated policymaker reference.",))


def test_rule_abstain_category_has_no_policy_reference(audit) -> None:
    rule_abstentions = tuple(
        item
        for item in audit.observations
        if item.category is AbstentionCategory.ROUTE_MATCH_RULE_ABSTAIN
    )
    assert len(rule_abstentions) == 7_180
    assert not any(item.has_policy_reference for item in rule_abstentions)


def test_high_volume_prefix_counts_are_observations_only(audit) -> None:
    assert audit.stopped_prefix_counts[:9] == (
        ((), 5_889),
        (("1S", "P"), 306),
        (("1NT", "P"), 271),
        (("2S", "P"), 194),
        (("2H", "P"), 179),
        (("1H", "P"), 170),
        (("2D", "P"), 167),
        (("1D", "P"), 121),
        (("1C", "P"), 96),
    )


def test_policy_route_breakdown_is_derived(audit) -> None:
    assert audit.policy_route_counts == (
        ("sayc.responder.1nt.jacoby.hearts.continuation", 62),
        ("sayc.responder.1nt.jacoby.spades.continuation", 61),
    )


def test_repeated_classification_of_same_report_is_deterministic(report, audit) -> None:
    assert classify_abstentions(report) == audit


def test_production_registries_and_route_count_are_unchanged(audit) -> None:
    assert audit.route_count == len(create_standard_sayc_router().routes) == 45
    assert DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types == (
        KnownCardCountQuestion.__name__,
    )
    assert tuple(DeclarerTechnique) == (DeclarerTechnique.SIMPLE_UNBLOCK_KING,)
    assert not {
        "RestrictedChoiceQuestion",
        "VacantPlacesQuestion",
    } & set(DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types)


def test_module_is_audit_only() -> None:
    module = __import__(
        "benchmarks.phase20c_abstention_taxonomy_audit", fromlist=["unused"]
    )
    source = inspect.getsource(module)
    forbidden = (
        "EngineRoute(",
        "RuleDecision.recommend(",
        "from_policies(",
        "MISSING_RULE",
        "SHOULD_BID",
        "UNSUPPORTED_BRIDGE_ACTION",
    )
    assert not any(token in source for token in forbidden)
