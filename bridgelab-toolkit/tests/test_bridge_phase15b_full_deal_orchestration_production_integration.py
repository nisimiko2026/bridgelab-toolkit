from dataclasses import FrozenInstanceError, fields
import json

import pytest

import bridge
from benchmarks.end_to_end_analysis_architecture import _bidding
from benchmarks.first_declarer_recommendation_engine import _input as declarer_input
from benchmarks.full_deal_analysis_orchestration_architecture import (
    _probability_request,
    run_full_deal_analysis_orchestration_benchmark,
)
from benchmarks.full_deal_orchestration_production_integration import (
    run_full_deal_orchestration_production_benchmark,
)
from benchmarks.opening_lead_state_architecture import _input as opening_input
from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from bridge import (
    AnalysisStage,
    Deal,
    FullDealAnalysisInput,
    FullDealAnalysisResult,
    FullDealSkippedStage,
    FullDealSkipReason,
    PolicyRegistry,
    analyze_full_deal,
    create_standard_sayc_router,
    full_deal_analysis_to_dict,
    generate_deal,
)


def _auction_request() -> FullDealAnalysisInput:
    return FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION,),
        bidding=_bidding("KQJ876.32.43.543").bidding,
    )


def test_public_phase15_surface_is_exported():
    names = (
        "FullDealAnalysisInput",
        "FullDealProbabilityRequest",
        "FullDealSkippedStage",
        "FullDealAnalysisResult",
        "FullDealSkipReason",
        "analyze_full_deal",
        "full_deal_analysis_to_dict",
    )
    assert all(getattr(bridge, name) is not None for name in names)


def test_production_entry_point_and_result_contract_are_stable_and_immutable():
    request = _auction_request()
    result = analyze_full_deal(request, bidding_router=create_standard_sayc_router())
    assert isinstance(result, FullDealAnalysisResult)
    assert result.original_request is request
    assert result.requested_stages == result.applicable_stages == result.attempted_stages == ("auction",)
    assert result.skipped_stages == ()
    assert result.pipeline.summary is result.summary
    assert result.pipeline.rendering is result.rendering
    assert result.text is result.pipeline.text
    with pytest.raises(FrozenInstanceError):
        result.status = None


def test_skipped_stage_and_invalid_request_contracts_are_structured():
    skipped = analyze_full_deal(
        FullDealAnalysisInput(requested_stages=(AnalysisStage.OPENING_LEAD,))
    )
    assert skipped.skipped_stages == (
        FullDealSkippedStage(
            "opening-lead",
            FullDealSkipReason.INSUFFICIENT_STAGE_STATE,
            "No explicit legal-view state input was supplied.",
        ),
    )
    invalid = analyze_full_deal(None)  # type: ignore[arg-type]
    invalid_stage = analyze_full_deal(
        FullDealAnalysisInput(requested_stages=("invalid",))  # type: ignore[arg-type]
    )
    invalid_probability = analyze_full_deal(
        FullDealAnalysisInput(probability_requests=(object(),))  # type: ignore[arg-type]
    )
    assert {invalid.status.value, invalid_stage.status.value, invalid_probability.status.value} == {"error"}
    assert all(item.skipped_stages[0].reason is FullDealSkipReason.UNSUPPORTED_REQUEST for item in (invalid, invalid_stage, invalid_probability))


def test_knowledge_probability_and_trace_provenance_are_publicly_preserved():
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION,),
        bidding=_bidding("KQJ876.32.43.543").bidding,
        probability_requests=(_probability_request(),),
    )
    result = analyze_full_deal(request, bidding_router=create_standard_sayc_router())
    auction = result.subsystem_results[0]
    probability = result.probability_results[0]
    assert result.summary.items[0].result is auction
    assert result.rendering.sections[0].summary_item.result is auction
    assert result.rendering.source_references[0] is auction.evidence[0].source
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert probability.mode.value == "exact"
    assert probability.evidence[0].assumptions and probability.evidence[0].known_facts
    assert result.rendering.sections[-1].trace == probability.trace


def test_public_serialization_is_deterministic_structured_and_json_ready():
    result = analyze_full_deal(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.DECLARER_PLAY,),
            declarer_play=declarer_input(),
            probability_requests=(_probability_request(),),
        )
    )
    first = full_deal_analysis_to_dict(result)
    second = full_deal_analysis_to_dict(result)
    assert first == second
    assert first["subsystem_results"][0]["action"]["kind"] == "card-play"
    assert first["probability_results"][0]["mode"] == "exact"
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_complete_deal_cannot_bypass_legal_view_inputs():
    deal = generate_deal(1515)
    request = FullDealAnalysisInput(
        deal=deal,
        requested_stages=(AnalysisStage.OPENING_LEAD,),
        opening_lead=opening_input(),
        probability_requests=(_probability_request(),),
    )
    result = analyze_full_deal(request)
    assert result.original_request.deal is deal and isinstance(deal, Deal)
    assert all(field.type is not Deal for field in fields(request.opening_lead))
    assert len(request.opening_lead.opening_leader_hand.cards) == 13
    assert len(request.probability_requests[0].context.visible_cards) == 13


def test_subsystem_evaluation_summary_and_rendering_each_occur_once():
    calls = 0

    def evaluator(state):
        nonlocal calls
        calls += 1
        return bridge.evaluate_declarer_play(state)

    result = analyze_full_deal(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.DECLARER_PLAY,),
            declarer_play=declarer_input(),
        ),
        declarer_evaluator=evaluator,
    )
    assert calls == 1
    assert result.rendering.original_summary is result.summary
    assert result.summary.items[0].result is result.subsystem_results[0]


def test_phase15a_and_phase14d_guards_are_exact():
    phase15a = run_full_deal_analysis_orchestration_benchmark()
    assert (phase15a.fixtures, phase15a.complete, phase15a.partial, phase15a.no_decision, phase15a.error) == (18, 9, 3, 6, 0)
    assert (phase15a.requested_stage_references, phase15a.attempted_stage_references, phase15a.skipped_stage_references) == (30, 29, 1)
    assert (phase15a.auction_evaluations, phase15a.opening_lead_evaluations, phase15a.declarer_evaluations, phase15a.defensive_evaluations, phase15a.probability_evaluations) == (8, 7, 4, 4, 6)
    assert (phase15a.orchestration_recommendation_references, phase15a.summary_recommendation_references, phase15a.rendered_recommendation_references) == (12, 12, 12)
    assert (phase15a.evidence_references, phase15a.unresolved_references, phase15a.deterministic_repeats) == (18, 11, 18)
    phase14d = run_phase14_coverage_closure_audit()
    assert phase14d.phase14_complete and phase14d.production_recommendations == 4
    assert (phase14d.closure_fixtures, phase14d.provenance_loss_fixtures) == (16, 0)


def test_focused_benchmark_exports_serialization_and_safety_are_exact():
    result = run_full_deal_orchestration_production_benchmark()
    assert result.public_fixtures == result.summary_builds == result.rendering_builds == 18
    assert (result.complete, result.partial, result.no_decision, result.error) == (9, 2, 6, 1)
    assert result.public_api_export_failures == result.serialization_failures == 0
    assert result.duplicate_subsystem_evaluations == result.hidden_information_violations == 0
    assert result.recomputed_subsystem_decisions == 0
    assert (result.invented_actions, result.invented_numbers, result.invented_sources, result.invented_probabilities) == (0, 0, 0, 0)
    assert result.deterministic_repeats == 18


def test_routes_defaults_and_phase15c_direction_are_unchanged():
    result = run_full_deal_orchestration_production_benchmark()
    assert len(create_standard_sayc_router().routes) == 45
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert result.production_recommendations == 4
    assert result.phase15c_direction == "A. PHASE 15 COVERAGE / CLOSURE AUDIT"
    assert not any(term in analyze_full_deal(_auction_request(), bidding_router=create_standard_sayc_router()).text.casefold() for term in ("confidence", "best overall", "hidden card"))
