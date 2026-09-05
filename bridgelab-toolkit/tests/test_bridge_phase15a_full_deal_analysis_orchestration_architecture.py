from dataclasses import FrozenInstanceError, fields

import pytest

from benchmarks.defensive_state_architecture import _input as defensive_input
from benchmarks.end_to_end_analysis_architecture import _bidding
from benchmarks.first_declarer_recommendation_engine import _input as declarer_input
from benchmarks.full_deal_analysis_orchestration_architecture import (
    _probability_request,
    run_full_deal_analysis_orchestration_benchmark,
)
from benchmarks.opening_lead_state_architecture import _input as opening_input
from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from bridge import (
    AnalysisStage,
    AnalysisStatus,
    Deal,
    DealAnalysisContext,
    DealAnalysisResult,
    FullDealAnalysisInput,
    FullDealAnalysisResult,
    FullDealSkipReason,
    Hand,
    PolicyRegistry,
    ProbabilityContext,
    analyze_deal_decision,
    analyze_full_deal,
    create_standard_sayc_router,
    generate_deal,
)


def test_full_deal_input_and_result_are_immutable_and_reuse_canonical_types():
    deal = generate_deal(15)
    request = FullDealAnalysisInput(deal=deal)
    result = analyze_full_deal(request)
    assert isinstance(request.deal, Deal)
    assert isinstance(deal.hand(next(iter(deal.mapping))), Hand)
    assert isinstance(result, FullDealAnalysisResult)
    with pytest.raises(FrozenInstanceError):
        request.deal = None
    with pytest.raises(FrozenInstanceError):
        result.status = None


def test_requested_attempted_skipped_and_order_are_explicit():
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.DEFENSIVE_PLAY, AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD),
        opening_lead=opening_input(),
    )
    result = analyze_full_deal(request, bidding_router=create_standard_sayc_router())
    assert result.requested_stages == ("auction", "opening-lead", "defensive-play")
    assert result.attempted_stages == ("opening-lead",)
    assert tuple(item.stage for item in result.skipped_stages) == ("auction", "defensive-play")
    assert {item.reason for item in result.skipped_stages} == {FullDealSkipReason.INSUFFICIENT_STAGE_STATE}


def test_all_existing_stage_adapters_and_phase14_pipeline_are_reused():
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD, AnalysisStage.DECLARER_PLAY, AnalysisStage.DEFENSIVE_PLAY),
        bidding=_bidding("KQJ876.32.43.543").bidding,
        opening_lead=opening_input(),
        declarer_play=declarer_input(),
        defensive_play=defensive_input(),
        probability_requests=(_probability_request(),),
    )
    result = analyze_full_deal(request, bidding_router=create_standard_sayc_router())
    assert result.attempted_stages == ("auction", "opening-lead", "declarer-play", "defensive-play", "probability-evidence")
    assert result.pipeline.summary is result.summary
    assert result.pipeline.rendering is result.rendering
    assert result.rendering.original_summary is result.summary


def test_declarer_subsystem_is_evaluated_exactly_once():
    calls = 0

    def evaluator(state):
        nonlocal calls
        calls += 1
        from bridge import evaluate_declarer_play

        return evaluate_declarer_play(state)

    result = analyze_full_deal(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.DECLARER_PLAY,),
            declarer_play=declarer_input(),
        ),
        declarer_evaluator=evaluator,
    )
    assert calls == 1
    assert len(result.summary.recommendation_items) == 1


def test_knowledge_and_probability_provenance_survive_orchestration():
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
    assert result.summary.probability_results[0] is probability
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert probability.mode.value == "exact"
    assert probability.evidence[0].assumptions
    assert probability.evidence[0].known_facts
    assert result.rendering.sections[-1].trace == probability.trace


def test_complete_deal_never_enters_stage_inputs_or_probability_context():
    deal = generate_deal(1514)
    request = FullDealAnalysisInput(
        deal=deal,
        requested_stages=(AnalysisStage.OPENING_LEAD, AnalysisStage.DECLARER_PLAY, AnalysisStage.DEFENSIVE_PLAY),
        opening_lead=opening_input(),
        declarer_play=declarer_input(),
        defensive_play=defensive_input(),
        probability_requests=(_probability_request(),),
    )
    result = analyze_full_deal(request)
    assert result.original_request.deal is deal
    for source in (request.opening_lead, request.declarer_play, request.defensive_play):
        assert all(field.type is not Deal for field in fields(source))
    assert isinstance(request.probability_requests[0].context, ProbabilityContext)
    assert len(request.probability_requests[0].context.visible_cards) == 13


def test_unresolved_opening_lead_and_defense_remain_no_decisions():
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.OPENING_LEAD, AnalysisStage.DEFENSIVE_PLAY),
        opening_lead=opening_input(),
        defensive_play=defensive_input(),
    )
    result = analyze_full_deal(request)
    assert all(item.status is AnalysisStatus.NO_DECISION for item in result.subsystem_results)
    assert all(item.action.kind.value == "none" for item in result.subsystem_results)


def test_benchmark_is_deterministic_bounded_and_invention_free():
    result = run_full_deal_analysis_orchestration_benchmark()
    assert result.fixtures == result.summary_builds == result.rendering_builds == 18
    assert (result.complete, result.partial, result.no_decision, result.error) == (9, 3, 6, 0)
    assert result.deterministic_repeats == 18
    assert result.hidden_information_violations == result.recomputed_subsystem_decisions == 0
    assert (result.invented_actions, result.invented_numbers, result.invented_sources, result.invented_probabilities) == (0, 0, 0, 0)


def test_phase14d_routes_defaults_and_backward_compatibility_are_unchanged():
    closure = run_phase14_coverage_closure_audit()
    old = analyze_deal_decision(DealAnalysisContext(stage=AnalysisStage.DEAL_SUMMARY))
    assert isinstance(old, DealAnalysisResult)
    assert closure.phase14_complete and closure.closure_fixtures == 16
    assert (closure.structured_summary_successes, closure.rendering_successes, closure.pipeline_successes) == (16, 16, 16)
    assert (closure.provenance_preserved_fixtures, closure.provenance_loss_fixtures) == (16, 0)
    assert len(create_standard_sayc_router().routes) == 45
    assert PolicyRegistry().opening_lead_policy_ids == ()


def test_repeated_request_is_identical_and_has_no_confidence_or_best_action():
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION,),
        bidding=_bidding("KQJ876.32.43.543").bidding,
    )
    router = create_standard_sayc_router()
    first = analyze_full_deal(request, bidding_router=router)
    second = analyze_full_deal(request, bidding_router=router)
    assert first == second and first.text.encode() == second.text.encode()
    assert not any(term in first.text.casefold() for term in ("confidence", "best overall", "hidden card"))
