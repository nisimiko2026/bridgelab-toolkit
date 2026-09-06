from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from benchmarks.phase15_coverage_closure_audit import run_phase15_coverage_closure_audit
from benchmarks.phase16_coverage_closure_audit import run_phase16_coverage_closure_audit
from benchmarks.phase17_bridge_intelligence_source_readiness_audit import (
    SourceReadinessClassification,
    run_phase17_source_readiness_audit,
)
from bridge import create_standard_sayc_router
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY


def test_inventory_covers_all_five_families_and_38_candidates():
    audit = run_phase17_source_readiness_audit()
    assert audit.audited_families == (
        "DEFENSIVE_PLAY",
        "DECLARER_PLAY",
        "PROBABILITY",
        "OPENING_LEAD",
        "BIDDING_RESIDUAL",
    )
    assert audit.total_candidates == audit.deterministic_fixtures == 38
    assert {item.family for item in audit.candidates} == set(audit.audited_families)


def test_classification_counts_and_fixture_outcomes_are_exact():
    audit = run_phase17_source_readiness_audit()
    assert audit.classification_counts == {
        "AMBIGUOUS_ACTION": 3,
        "ARCHITECTURE_BLOCKED": 2,
        "EXCEPTION_INCOMPLETE": 6,
        "LOW_SAMPLE": 1,
        "NOT_PRESENT": 0,
        "PARTNERSHIP_DEPENDENT": 4,
        "POLICY_REQUIRED": 3,
        "PROBABILITY_REQUIRED": 3,
        "SOURCE_EXECUTABLE": 2,
        "SOURCE_PARTIAL": 14,
    }
    assert (audit.executable_fixture_count, audit.blocked_fixture_count) == (2, 36)


def test_every_candidate_has_source_heading_classification_and_bounded_executable_contract():
    audit = run_phase17_source_readiness_audit()
    for item in audit.candidates:
        assert item.source_path.endswith(".md") and item.heading
        assert isinstance(item.classification, SourceReadinessClassification)
        if item.classification is SourceReadinessClassification.SOURCE_EXECUTABLE:
            assert item.trigger and item.action and item.exceptions
            assert item.execution_status == "EXISTING_PRODUCTION_BASELINE"
        else:
            assert item.execution_status == "PROSPECTIVE_BLOCKED_OR_DEFERRED"
    assert {
        item.candidate
        for item in audit.candidates
        if item.classification is SourceReadinessClassification.SOURCE_EXECUTABLE
    } == {"SIMPLE_UNBLOCK_KING", "KNOWN_CARD_COUNT"}


def test_policy_probability_and_opening_lead_blockers_are_not_treated_as_executable():
    audit = run_phase17_source_readiness_audit()
    blocked = {
        SourceReadinessClassification.POLICY_REQUIRED,
        SourceReadinessClassification.PARTNERSHIP_DEPENDENT,
        SourceReadinessClassification.PROBABILITY_REQUIRED,
    }
    assert all(
        item.classification is not SourceReadinessClassification.SOURCE_EXECUTABLE
        for item in audit.candidates
        if item.classification in blocked
    )
    opening = [item for item in audit.candidates if item.family == "OPENING_LEAD"]
    assert opening and not any(
        item.classification is SourceReadinessClassification.SOURCE_EXECUTABLE
        for item in opening
    )
    assert all(
        "suit" in item.blocker.casefold()
        or item.classification is SourceReadinessClassification.SOURCE_PARTIAL
        for item in opening
    )


def test_bidding_deferrals_and_deterministic_ranking_follow_evidence():
    first = run_phase17_source_readiness_audit()
    second = run_phase17_source_readiness_audit()
    bidding = [item for item in first.candidates if item.family == "BIDDING_RESIDUAL"]
    assert all(
        item.classification is not SourceReadinessClassification.SOURCE_EXECUTABLE
        for item in bidding
    )
    assert first.value_ranking == second.value_ranking
    assert tuple(row["family"] for row in first.value_ranking) == (
        "DECLARER_PLAY",
        "PROBABILITY",
        "DEFENSIVE_PLAY",
        "BIDDING_RESIDUAL",
        "OPENING_LEAD",
    )


def test_high_value_gate_selects_source_enrichment_with_zero_new_gain():
    audit = run_phase17_source_readiness_audit()
    assert audit.high_value_source_ready_candidates == ()
    assert set(audit.estimated_production_recommendation_gain.values()) == {0}
    assert audit.phase17b_direction == "F. SOURCE ENRICHMENT PROGRAM"
    assert (
        audit.hidden_information_violations,
        audit.invented_rules,
        audit.invented_formulas,
        audit.invented_defaults,
    ) == (0, 0, 0, 0)


def test_phase16_phase15_phase14_historical_guards_are_unchanged():
    phase16 = run_phase16_coverage_closure_audit()
    phase15 = run_phase15_coverage_closure_audit()
    phase14 = run_phase14_coverage_closure_audit()
    assert (
        phase16.phase16_complete
        and len(phase16.readiness_matrix) == 27
        and phase16.closure_fixtures == 35
    )
    assert (
        phase16.provenance_lost
        == phase16.hidden_information_violations
        == phase16.unsafe_parser_findings
        == 0
    )
    assert phase16.backward_compatibility == "PASS"
    assert phase15.phase15_complete and len(phase15.readiness_matrix) == 17
    assert phase14.phase14_complete


def test_production_intelligence_and_ordinary_guards_are_unchanged():
    audit = run_phase17_source_readiness_audit()
    assert audit.production_guards == {
        "production_recommendations": 4,
        "routes": 45,
        "declarer_techniques": 1,
        "opening_lead_algorithms": 0,
        "defensive_algorithms": 0,
        "registered_probability_engines": 1,
        "new_probability_formulas": 0,
        "ordinary": "7871/761/9239",
    }
    assert len(create_standard_sayc_router().routes) == 45
    assert len(DEFAULT_PROBABILITY_ENGINE_REGISTRY.registrations) == 1
