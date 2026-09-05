from dataclasses import asdict
from pathlib import Path

from benchmarks.opening_lead_policy_architecture import run_opening_lead_policy_architecture_benchmark
from benchmarks.opening_lead_source_readiness_audit import (
    ReadinessClassification, run_opening_lead_source_readiness_audit,
)
from bridge import OpeningLeadHonorStyle, PolicyRegistry, create_standard_sayc_router


AUDIT = run_opening_lead_source_readiness_audit()


def test_all_frozen_sources_are_inventoried_and_classified():
    assert AUDIT.source_files_audited == 10 and AUDIT.candidate_rules == 10
    assert all(item.classification in ReadinessClassification for item in AUDIT.candidates)
    required = {"fourth-best.md", "third-fifth.md", "rusinow.md", "top-of-nothing.md", "standard-leads.md"}
    assert required <= {Path(item.source).name for item in AUDIT.candidates}


def test_no_candidate_crosses_the_complete_executability_gate():
    executable = {ReadinessClassification.SOURCE_EXECUTABLE, ReadinessClassification.POLICY_EXECUTABLE}
    assert not any(item.classification in executable for item in AUDIT.candidates)
    assert all(not item.unique_card or (item.exceptions_complete and item.precedence_complete) for item in AUDIT.candidates)


def test_policy_families_are_never_assumed_when_missing():
    policy_rules = {item.rule: item for item in AUDIT.candidates if item.required_policy}
    assert policy_rules["fourth-best from length"].required_policy == "FOURTH_BEST"
    assert policy_rules["third-and-fifth"].required_policy == "THIRD_AND_FIFTH"
    assert policy_rules["standard honor sequence"].required_policy == "STANDARD"
    assert policy_rules["Rusinow touching sequence"].required_policy == "RUSINOW"
    assert policy_rules["top of nothing"].required_policy == "ENABLED"
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert OpeningLeadHonorStyle.UNKNOWN is not OpeningLeadHonorStyle.STANDARD


def test_precedence_and_ambiguous_choices_block_execution():
    assert any(not item.precedence_complete for item in AUDIT.candidates)
    assert AUDIT.classification_counts["AMBIGUOUS_CARD_CHOICE"] == 1
    assert AUDIT.classification_counts["EXCEPTION_INCOMPLETE"] == 2


def test_fifteen_fixtures_are_non_executable_and_return_no_card():
    assert (AUDIT.candidate_fixtures, AUDIT.executable_fixtures, AUDIT.non_executable_fixtures) == (15, 0, 15)
    assert all(item.recommendation is None and not item.executable for item in AUDIT.fixtures)
    assert AUDIT.recommendations_generated == 0


def test_phase13i_and_cumulative_guards_are_unchanged():
    previous = run_opening_lead_policy_architecture_benchmark()
    assert (previous.policy_fixtures, previous.explicit_policies, previous.unknown_policies) == (10, 8, 2)
    assert previous.source_backed_policy_dimensions == 3
    assert AUDIT.architecture == {
        "cumulative_positions_or_requests": 95, "source_readiness_audit_requests": 15,
        "policy_requests": 10, "opening_lead_states": 14, "bidding_recommendations": 2,
        "declarer_recommendations": 2, "opening_lead_recommendations": 0,
        "defensive_recommendations": 0, "no_decisions": 51, "abstentions": 3, "errors": 0,
    }
    assert len(create_standard_sayc_router().routes) == 45


def test_decision_is_source_enrichment_and_audit_is_deterministic():
    assert AUDIT.phase13k_direction == "E. OPENING-LEAD SOURCE ENRICHMENT REQUIRED"
    assert asdict(AUDIT) == asdict(run_opening_lead_source_readiness_audit())
