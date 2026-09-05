from dataclasses import FrozenInstanceError

import pytest

from benchmarks.deal_summary_end_to_end_integration import (
    run_deal_summary_end_to_end_integration_benchmark,
)
from benchmarks.deal_summary_explanation_architecture import (
    run_deal_summary_explanation_benchmark,
)
from benchmarks.deal_summary_rendering_explanation_engine import (
    _probability,
    _stage,
    run_deal_summary_rendering_benchmark,
)
from benchmarks.phase13_coverage_closure_audit import run_phase13_coverage_closure_audit
from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from bridge import (
    AnalysisStage,
    AnalysisStatus,
    DealAnalysisContext,
    DealAnalysisResult,
    DealSummaryInput,
    DealSummaryPipelineStatus,
    PolicyRegistry,
    analyze_deal_decision,
    build_and_render_deal_summary,
    build_deal_summary,
    create_standard_sayc_router,
    render_deal_summary,
)


def test_component_inventory_and_readiness_matrix_are_complete():
    audit = run_phase14_coverage_closure_audit()
    assert [item["phase"] for item in audit.component_inventory] == ["14A", "14B", "14C"]
    assert len(audit.readiness_matrix) == 12
    assert {item["readiness"] for item in audit.readiness_matrix} == {"PRODUCTION_READY"}


def test_all_phase14_models_are_immutable_and_functions_independent():
    source = DealSummaryInput()
    summary = build_deal_summary(source)
    rendering = render_deal_summary(summary)
    pipeline = build_and_render_deal_summary(source)
    for value, attribute in ((summary, "status"), (rendering, "status"), (pipeline, "status")):
        with pytest.raises(FrozenInstanceError):
            setattr(value, attribute, None)


def test_provenance_probability_source_and_trace_survive_end_to_end():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    probability = _probability()
    result = build_and_render_deal_summary(DealSummaryInput((bid,), (probability,)))
    assert result.original_subsystem_results[0] is bid
    assert result.rendering.sections[0].summary_item.result is bid
    assert result.rendering.source_references[0] is bid.evidence[0].source
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert result.summary.probability_results[0] is probability
    assert result.rendering.sections[-1].trace == probability.trace
    assert probability.mode.value == "exact"
    assert probability.evidence[0].assumptions == ("Visible cards only.",)
    assert probability.evidence[0].known_facts == (("known-cards", "13"),)


def test_statuses_unresolved_abstention_and_errors_remain_distinct():
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    defense = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defense")
    abstain = _stage(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "abstain")
    error = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "error")
    assert build_and_render_deal_summary(DealSummaryInput((lead,))).status is DealSummaryPipelineStatus.NO_DECISION
    assert build_and_render_deal_summary(DealSummaryInput((defense,))).summary.unresolved_items
    assert build_and_render_deal_summary(DealSummaryInput((abstain,))).summary.unresolved_items[0].result is abstain
    assert build_and_render_deal_summary(DealSummaryInput((error,))).status is DealSummaryPipelineStatus.ERROR


def test_closure_benchmark_counts_and_provenance_are_exact():
    audit = run_phase14_coverage_closure_audit()
    assert (audit.closure_fixtures, audit.structured_summary_successes, audit.rendering_successes, audit.pipeline_successes) == (16, 16, 16, 16)
    assert (audit.complete, audit.partial, audit.no_decision, audit.errors) == (9, 3, 3, 1)
    assert (audit.production_recommendations, audit.summary_recommendation_references, audit.rendered_recommendation_references, audit.integrated_recommendation_references) == (4, 13, 13, 13)
    assert (audit.provenance_preserved_fixtures, audit.provenance_loss_fixtures, audit.deterministic_repeats) == (16, 0, 16)


def test_invention_recomputation_and_hidden_inference_audit_is_zero():
    audit = run_phase14_coverage_closure_audit()
    assert set(audit.invention_audit.values()) == {0}
    assert audit.phase14_complete


def test_phase14_historical_guards_are_unchanged():
    phase14a = run_deal_summary_explanation_benchmark()
    assert (phase14a.summary_fixtures, phase14a.available_summaries, phase14a.partial_summaries, phase14a.no_decision_summaries, phase14a.error_summaries, phase14a.recommendation_items) == (16, 8, 1, 5, 2, 8)
    phase14b = run_deal_summary_rendering_benchmark()
    assert (phase14b.rendering_fixtures, phase14b.rendered_available, phase14b.rendered_partial, phase14b.rendered_no_decision, phase14b.rendered_error, phase14b.rendered_recommendation_references, phase14b.deterministic_repeats_matched) == (16, 8, 2, 4, 2, 11, 16)
    phase14c = run_deal_summary_end_to_end_integration_benchmark()
    assert (phase14c.integration_fixtures, phase14c.successful_integrations, phase14c.partial_integrations, phase14c.no_decision_integrations, phase14c.error_integrations, phase14c.production_recommendation_references) == (16, 9, 3, 3, 1, 13)
    assert (phase14c.evidence_references, phase14c.unresolved_stage_references, phase14c.provenance_preserved_cases, phase14c.deterministic_repeats_matched) == (21, 7, 16, 16)


def test_phase13l_production_guards_are_unchanged():
    phase13l = run_phase13_coverage_closure_audit()
    assert phase13l.benchmark["total_deterministic_closure_fixtures"] == 16
    assert (phase13l.benchmark["recommendations_total"], phase13l.benchmark["abstentions"], phase13l.benchmark["no_decisions"], phase13l.benchmark["evidence_results"], phase13l.benchmark["errors"]) == (4, 2, 9, 1, 0)
    assert phase13l.benchmark["recommendation_rate"] == 0.25


def test_backward_compatibility_routes_policies_and_phase15_direction():
    result = analyze_deal_decision(DealAnalysisContext(stage=AnalysisStage.DEAL_SUMMARY))
    audit = run_phase14_coverage_closure_audit()
    assert isinstance(result, DealAnalysisResult)
    assert len(create_standard_sayc_router().routes) == 45
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert audit.guards["production_defaults_changed"] is False
    assert audit.phase15_direction == "E. FULL-DEAL ANALYSIS / ORCHESTRATION"


def test_repeated_pipeline_is_structurally_identical_and_text_is_safe():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    source = DealSummaryInput((bid,), (_probability(),))
    first = build_and_render_deal_summary(source)
    second = build_and_render_deal_summary(source)
    assert first == second and first.text.encode() == second.text.encode()
    lowered = first.text.casefold()
    assert not any(term in lowered for term in ("confidence", "best overall", "hidden card"))
