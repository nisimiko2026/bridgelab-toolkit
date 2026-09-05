from dataclasses import FrozenInstanceError

import pytest

from benchmarks.deal_summary_end_to_end_integration import run_deal_summary_end_to_end_integration_benchmark
from benchmarks.deal_summary_explanation_architecture import run_deal_summary_explanation_benchmark
from benchmarks.deal_summary_rendering_explanation_engine import _probability, _stage, run_deal_summary_rendering_benchmark
from benchmarks.phase13_coverage_closure_audit import run_phase13_coverage_closure_audit
from bridge import (
    AnalysisStage, AnalysisStatus, CalculationMode, DealAnalysisContext,
    DealAnalysisResult, DealSummaryInput, DealSummaryPipelineFailureCode,
    DealSummaryPipelineStatus, PolicyRegistry, analyze_deal_decision,
    build_and_render_deal_summary, create_standard_sayc_router,
)


def test_integration_is_immutable_and_preserves_all_layers():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    source = DealSummaryInput((bid,))
    result = build_and_render_deal_summary(source)
    assert result.source is source and result.original_subsystem_results[0] is bid
    assert result.rendering.original_summary is result.summary
    assert result.rendering.sections[0].summary_item.result is bid
    with pytest.raises(FrozenInstanceError):
        result.status = DealSummaryPipelineStatus.ERROR


def test_actions_and_explanations_are_not_recomputed():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    result = build_and_render_deal_summary(DealSummaryInput((bid,)))
    assert result.summary.items[0].result.action is bid.action
    assert result.summary.items[0].result.explanation == "auction explanation."
    assert "Recommend 2NT" in result.text


def test_knowledge_probability_mode_assumptions_facts_and_trace_survive():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    probability = _probability()
    result = build_and_render_deal_summary(DealSummaryInput((bid,), (probability,)))
    assert result.rendering.source_references
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert result.summary.probability_results[0] is probability
    assert probability.mode is CalculationMode.EXACT
    assert probability.evidence[0].assumptions == ("Visible cards only.",)
    assert probability.evidence[0].known_facts == (("known-cards", "13"),)
    assert result.rendering.sections[-1].trace == probability.trace


def test_unresolved_abstention_error_and_empty_remain_distinct():
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    abstain = _stage(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "abstain")
    error = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "error")
    assert build_and_render_deal_summary(DealSummaryInput((lead,))).status is DealSummaryPipelineStatus.NO_DECISION
    assert build_and_render_deal_summary(DealSummaryInput((abstain,))).summary.unresolved_items[0].result is abstain
    assert build_and_render_deal_summary(DealSummaryInput((error,))).status is DealSummaryPipelineStatus.ERROR
    assert build_and_render_deal_summary(DealSummaryInput()).status is DealSummaryPipelineStatus.NO_DECISION


def test_invalid_integration_input_has_structured_failure():
    result = build_and_render_deal_summary(None)  # type: ignore[arg-type]
    assert result.status is DealSummaryPipelineStatus.ERROR
    assert result.failure_code is DealSummaryPipelineFailureCode.INVALID_INPUT


def test_stage_order_and_repeat_are_deterministic():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid")
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    defense = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defense")
    source = DealSummaryInput((defense, lead, bid), (_probability(),))
    first, second = build_and_render_deal_summary(source), build_and_render_deal_summary(source)
    assert first == second and first.text.encode() == second.text.encode()
    assert [section.stage for section in first.rendering.sections[:-1]] == [AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD, AnalysisStage.DEFENSIVE_PLAY]


def test_no_forbidden_content_or_recomputation_exists():
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "engine unavailable")
    result = build_and_render_deal_summary(DealSummaryInput((lead,)))
    lowered = result.text.casefold()
    assert result.summary.recommendation_items == ()
    assert not any(term in lowered for term in ("confidence", "best overall", "hidden card", "probably", "likely"))


def test_analyze_deal_decision_return_type_is_backward_compatible():
    result = analyze_deal_decision(DealAnalysisContext(stage=AnalysisStage.DEAL_SUMMARY))
    assert isinstance(result, DealAnalysisResult)
    assert result.status is AnalysisStatus.NO_DECISION


def test_benchmark_and_historical_guards_are_exact():
    result = run_deal_summary_end_to_end_integration_benchmark()
    assert (result.integration_fixtures, result.successful_integrations, result.partial_integrations, result.no_decision_integrations, result.error_integrations) == (16, 9, 3, 3, 1)
    assert result.summary_builds == result.rendering_builds == 16
    assert result.provenance_preserved_cases == result.deterministic_repeats_matched == 16
    assert result.recomputed_recommendations == 0
    assert run_deal_summary_explanation_benchmark().recommendation_items == 8
    rendering = run_deal_summary_rendering_benchmark()
    assert (rendering.rendering_fixtures, rendering.rendered_recommendation_references) == (16, 11)
    assert run_phase13_coverage_closure_audit().benchmark["recommendations_total"] == 4


def test_routes_defaults_and_phase14d_direction_are_unchanged():
    result = run_deal_summary_end_to_end_integration_benchmark()
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert len(create_standard_sayc_router().routes) == 45
    assert result.cumulative["production_recommendations"] == 4
    assert result.phase14d_direction == "D. PHASE 14 COVERAGE / CLOSURE AUDIT"
