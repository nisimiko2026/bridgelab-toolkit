from dataclasses import FrozenInstanceError

import pytest

from benchmarks.deal_summary_explanation_architecture import (
    SOURCE, _probability, _result, run_deal_summary_explanation_benchmark,
)
from benchmarks.phase13_coverage_closure_audit import run_phase13_coverage_closure_audit
from bridge import (
    AnalysisStage, AnalysisStatus, CalculationMode, DealSummaryFailureCode,
    DealSummaryInput, DealSummaryStatus, PolicyRegistry, build_deal_summary,
    create_standard_sayc_router,
)


def test_summary_types_are_immutable():
    source = DealSummaryInput((_result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid"),))
    with pytest.raises(FrozenInstanceError):
        source.stage_results = ()
    with pytest.raises(FrozenInstanceError):
        build_deal_summary(source).status = DealSummaryStatus.ERROR


def test_stage_order_and_original_results_are_preserved_exactly():
    bid = _result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    lead = _result(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    declarer = _result(AnalysisStage.DECLARER_PLAY, AnalysisStatus.RECOMMENDATION, "play")
    summary = build_deal_summary(DealSummaryInput((declarer, lead, bid)))
    assert [item.stage for item in summary.items] == [AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD, AnalysisStage.DECLARER_PLAY]
    assert summary.items[0].result is bid and summary.items[0].result.explanation == "bid explanation."


def test_knowledge_source_and_probability_result_are_preserved():
    bid = _result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    probability = _probability()
    summary = build_deal_summary(DealSummaryInput((bid,), (probability,)))
    assert summary.evidence_items[0].source is SOURCE
    assert summary.probability_results[0] is probability
    assert summary.probability_results[0].mode is CalculationMode.EXACT
    assert summary.evidence_items[-1] is probability.evidence[0]


def test_unresolved_abstention_and_error_states_are_preserved():
    abstain = _result(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "abstain")
    error = _result(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "error")
    summary = build_deal_summary(DealSummaryInput((abstain, error)))
    assert summary.status is DealSummaryStatus.ERROR
    assert summary.unresolved_items[0].result.abstention_code is abstain.abstention_code
    assert summary.error_items[0].result is error


def test_duplicate_invalid_and_empty_inputs_are_deterministic():
    bid = _result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    duplicate = build_deal_summary(DealSummaryInput((bid, bid)))
    assert duplicate.status is DealSummaryStatus.ERROR
    assert duplicate.failure_code is DealSummaryFailureCode.DUPLICATE_STAGE
    empty = build_deal_summary(DealSummaryInput())
    assert empty.status is DealSummaryStatus.NO_DECISION
    assert empty.failure_code is DealSummaryFailureCode.MISSING_SUBSYSTEM_RESULTS


def test_mixed_and_all_no_decision_statuses_are_exact():
    bid = _result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    lead = _result(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    assert build_deal_summary(DealSummaryInput((bid, lead))).status is DealSummaryStatus.PARTIAL
    assert build_deal_summary(DealSummaryInput((lead,))).status is DealSummaryStatus.NO_DECISION


def test_builder_never_invents_actions_probabilities_or_hidden_state():
    lead = _result(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    summary = build_deal_summary(DealSummaryInput((lead,)))
    assert summary.recommendation_items == summary.evidence_items == summary.probability_results == ()
    assert not any(word in summary.explanation for word in ("confidence", "best lead", "hidden"))


def test_focused_benchmark_and_phase13_guards_are_exact():
    result = run_deal_summary_explanation_benchmark()
    assert (result.summary_fixtures, result.available_summaries, result.partial_summaries, result.no_decision_summaries, result.error_summaries) == (16, 8, 1, 5, 2)
    assert (result.recommendation_items, result.bidding_recommendation_items, result.declarer_recommendation_items) == (8, 6, 2)
    assert result.invented_recommendations == result.invented_probabilities == 0
    closure = run_phase13_coverage_closure_audit()
    assert closure.benchmark["total_deterministic_closure_fixtures"] == 16
    assert closure.benchmark["recommendations_total"] == 4


def test_defaults_routes_and_direction_are_unchanged():
    result = run_deal_summary_explanation_benchmark()
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert len(create_standard_sayc_router().routes) == 45
    assert result.cumulative["production_recommendations"] == 4
    assert result.phase14b_direction == "A. DEAL-SUMMARY RENDERING / EXPLANATION ENGINE"
