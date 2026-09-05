from dataclasses import FrozenInstanceError

import pytest

from benchmarks.deal_summary_rendering_explanation_engine import (
    SOURCE, _probability, _stage, run_deal_summary_rendering_benchmark,
)
from benchmarks.deal_summary_explanation_architecture import run_deal_summary_explanation_benchmark
from benchmarks.phase13_coverage_closure_audit import run_phase13_coverage_closure_audit
from bridge import (
    AnalysisStage, AnalysisStatus, CalculationMode, DealSummaryInput,
    PolicyRegistry, build_deal_summary,
    create_standard_sayc_router, render_deal_summary,
)


def test_rendering_types_are_immutable_and_retain_original_summary():
    summary = build_deal_summary(DealSummaryInput((_stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid"),)))
    rendering = render_deal_summary(summary)
    assert rendering.original_summary is summary
    with pytest.raises(FrozenInstanceError):
        rendering.text = "changed"
    with pytest.raises(FrozenInstanceError):
        rendering.sections[0].text = "changed"


def test_stage_order_actions_explanations_and_provenance_are_exact():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "lead")
    play = _stage(AnalysisStage.DECLARER_PLAY, AnalysisStatus.RECOMMENDATION, "declarer")
    rendering = render_deal_summary(build_deal_summary(DealSummaryInput((play, lead, bid))))
    assert [section.stage for section in rendering.sections] == [AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD, AnalysisStage.DECLARER_PLAY]
    assert "Recommend 2NT" in rendering.sections[0].text and "auction explanation." in rendering.sections[0].text
    assert "Play KS" in rendering.sections[2].text and rendering.sections[0].summary_item.result is bid


def test_sources_probability_mode_facts_and_trace_are_preserved():
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    probability = _probability()
    rendering = render_deal_summary(build_deal_summary(DealSummaryInput((bid,), (probability,))))
    assert SOURCE in rendering.source_references
    section = rendering.sections[-1]
    assert section.probability_result is probability and section.evidence[0] is probability.evidence[0]
    assert probability.mode is CalculationMode.EXACT
    assert all(token in section.text for token in ("Mode: exact", "known-cards: 13", "Unknown cards: 39", "known=13", "unknown=39"))
    assert "confidence" not in section.text.casefold()


def test_abstain_no_decision_and_error_wording_remain_distinct():
    abstain = _stage(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "abstain")
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "opening lead engine unavailable")
    error = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "error")
    assert "Abstained" in render_deal_summary(build_deal_summary(DealSummaryInput((abstain,)))).text
    assert "No decision" in render_deal_summary(build_deal_summary(DealSummaryInput((lead,)))).text
    assert "Error" in render_deal_summary(build_deal_summary(DealSummaryInput((error,)))).text


def test_opening_and_defensive_engine_unavailable_render_exactly():
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "opening-lead engine unavailable")
    defense = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defensive engine unavailable")
    text = render_deal_summary(build_deal_summary(DealSummaryInput((defense, lead)))).text
    assert "opening-lead engine unavailable" in text and "defensive engine unavailable" in text
    assert text.index("Opening Lead") < text.index("Defensive Play")


def test_renderer_introduces_no_unrepresented_content():
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "engine unavailable")
    rendering = render_deal_summary(build_deal_summary(DealSummaryInput((lead,))))
    lowered = rendering.text.casefold()
    assert not any(term in lowered for term in ("best overall", "confidence", "probably", "likely", "hidden card"))
    assert rendering.source_references == rendering.evidence_references == ()


def test_repeated_rendering_is_byte_deterministic():
    summary = build_deal_summary(DealSummaryInput((_stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "bid"),), (_probability(),)))
    first, second = render_deal_summary(summary), render_deal_summary(summary)
    assert first == second and first.text.encode("utf-8") == second.text.encode("utf-8")


def test_benchmark_and_historical_guards_are_exact():
    result = run_deal_summary_rendering_benchmark()
    assert (result.rendering_fixtures, result.rendered_available, result.rendered_partial, result.rendered_no_decision, result.rendered_error) == (16, 8, 2, 4, 2)
    assert result.rendered_recommendation_references == 11
    assert result.invented_actions == result.invented_numbers == result.invented_sources == result.invented_probabilities == 0
    assert result.deterministic_repeats_matched == 16
    phase14a = run_deal_summary_explanation_benchmark()
    assert (phase14a.summary_fixtures, phase14a.available_summaries, phase14a.partial_summaries, phase14a.no_decision_summaries, phase14a.error_summaries) == (16, 8, 1, 5, 2)
    assert phase14a.recommendation_items == 8
    assert run_phase13_coverage_closure_audit().benchmark["recommendations_total"] == 4


def test_routes_defaults_and_phase14c_direction_are_unchanged():
    result = run_deal_summary_rendering_benchmark()
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert len(create_standard_sayc_router().routes) == 45
    assert result.cumulative["production_recommendations"] == 4
    assert result.phase14c_direction == "D. DEAL-SUMMARY END-TO-END INTEGRATION"
