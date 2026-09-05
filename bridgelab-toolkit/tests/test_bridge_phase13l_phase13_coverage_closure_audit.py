from dataclasses import asdict

from benchmarks.phase13_coverage_closure_audit import run_phase13_coverage_closure_audit
from bridge import PolicyRegistry, create_standard_sayc_router


AUDIT = run_phase13_coverage_closure_audit()


def test_all_phase13_components_and_major_stages_are_inventoried():
    assert [item["phase"] for item in AUDIT.phase_inventory] == [f"13{letter}" for letter in "ABCDEFGHIJK"]
    assert {item.stage for item in AUDIT.stage_readiness} == {"AUCTION", "OPENING_LEAD", "DECLARER_PLAY", "DEFENSIVE_PLAY", "DEAL_SUMMARY", "PROBABILITY_EVIDENCE"}


def test_stage_readiness_is_explicit_and_source_boundaries_are_honest():
    stages = {item.stage: item for item in AUDIT.stage_readiness}
    assert stages["AUCTION"].readiness == "PRODUCTION_EXECUTABLE"
    assert stages["DECLARER_PLAY"].readiness == "PARTIALLY_EXECUTABLE"
    assert stages["OPENING_LEAD"].readiness == "ENGINE_BLOCKED"
    assert stages["DEFENSIVE_PLAY"].source_readiness == "SOURCE_READINESS_NOT_AUDITED"
    assert stages["DEAL_SUMMARY"].readiness == "NOT_IMPLEMENTED"


def test_sixteen_pipeline_fixtures_cover_every_required_outcome():
    assert len(AUDIT.fixtures) == AUDIT.benchmark["total_deterministic_closure_fixtures"] == 16
    names = {item.name for item in AUDIT.fixtures}
    assert {"ordinary-bidding", "strong-2c-balanced", "simple-unblock-king", "opening-lead-policy-no-engine", "known-card-count", "deal-summary", "deterministic-repeat"} <= names


def test_recommendation_and_no_decision_counts_are_exact():
    benchmark = AUDIT.benchmark
    assert (benchmark["recommendations_total"], benchmark["bidding_recommendations"], benchmark["declarer_recommendations"]) == (4, 3, 1)
    assert benchmark["opening_lead_recommendations"] == benchmark["defensive_recommendations"] == 0
    assert (benchmark["abstentions"], benchmark["no_decisions"], benchmark["errors"]) == (2, 9, 0)
    assert benchmark["recommendation_rate"] == 0.25


def test_failure_taxonomy_preserves_distinct_reasons():
    assert AUDIT.failure_taxonomy["NO_ROUTE"] == 1
    assert AUDIT.failure_taxonomy["RULE_ABSTENTION"] == 1
    assert AUDIT.failure_taxonomy["MISSING_STATE"] == 3
    assert AUDIT.failure_taxonomy["ENGINE_UNAVAILABLE"] == 4
    assert AUDIT.failure_taxonomy["ENGINE_NOT_REGISTERED"] == 1
    assert AUDIT.failure_taxonomy["UNSUPPORTED_STAGE"] == 1


def test_source_policy_and_probability_coverage_are_exact():
    assert AUDIT.source_coverage == {"declarer_techniques": 1, "opening_lead_techniques": 0, "defensive_techniques": 0, "registered_probability_calculations": 1}
    assert AUDIT.policy_coverage["opening_lead_default"] is None
    assert not AUDIT.policy_coverage["missing_policy_implies_standard"]
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert sum(item["registered"] for item in AUDIT.probability_matrix) == 1


def test_phase12_and_phase13_guards_and_routes_are_preserved():
    assert AUDIT.guards["ordinary"] == {"production_calls": 7871, "completed": 761, "abstained": 9239}
    assert AUDIT.guards["routes"] == len(create_standard_sayc_router().routes) == 45
    assert AUDIT.guards["phase13"]["simple_unblock_king"] == 2
    assert AUDIT.guards["phase13"]["lead_executable_13k_after"] == 0


def test_phase13_closes_deterministically_with_phase14_summary_direction():
    assert AUDIT.phase13_complete
    assert AUDIT.phase14_direction == "E. DEAL-SUMMARY / EXPLANATION ENGINE"
    assert asdict(AUDIT) == asdict(run_phase13_coverage_closure_audit())
