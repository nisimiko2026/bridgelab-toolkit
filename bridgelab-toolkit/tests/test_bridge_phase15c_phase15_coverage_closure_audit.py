from dataclasses import FrozenInstanceError
import json

import pytest

import bridge
from benchmarks.end_to_end_analysis_architecture import _bidding
from benchmarks.full_deal_analysis_orchestration_architecture import (
    _probability_request,
    run_full_deal_analysis_orchestration_benchmark,
)
from benchmarks.full_deal_orchestration_production_integration import (
    run_full_deal_orchestration_production_benchmark,
)
from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from benchmarks.phase15_coverage_closure_audit import run_phase15_coverage_closure_audit
from bridge import (
    AnalysisStage,
    FullDealAnalysisInput,
    FullDealAnalysisResult,
    PolicyRegistry,
    analyze_full_deal,
    create_standard_sayc_router,
    full_deal_analysis_to_dict,
)


def _request() -> FullDealAnalysisInput:
    return FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION,),
        bidding=_bidding("KQJ876.32.43.543").bidding,
        probability_requests=(_probability_request(),),
    )


def test_phase15_inventory_and_readiness_are_complete():
    audit = run_phase15_coverage_closure_audit()
    assert [item["phase"] for item in audit.component_inventory] == ["15A", "15B"]
    assert len(audit.readiness_matrix) == 17
    assert {item["readiness"] for item in audit.readiness_matrix} == {"PRODUCTION_READY"}


def test_input_result_public_exports_and_sole_orchestrator_are_stable():
    request = _request()
    result = analyze_full_deal(request, bidding_router=create_standard_sayc_router())
    assert bridge.analyze_full_deal is analyze_full_deal
    assert isinstance(result, FullDealAnalysisResult)
    assert result.original_request is request
    with pytest.raises(FrozenInstanceError):
        request.requested_stages = ()
    with pytest.raises(FrozenInstanceError):
        result.status = None


def test_stage_accounting_order_skips_and_single_evaluation_are_exact():
    audit = run_phase15_coverage_closure_audit()
    assert (audit.requested_references, audit.applicable_references, audit.attempted_references, audit.skipped_references) == (28, 26, 26, 3)
    assert audit.subsystem_evaluations == {
        "auction": 9,
        "opening-lead": 6,
        "declarer-play": 3,
        "defensive-play": 2,
        "probability-evidence": 6,
    }
    assert audit.duplicate_subsystem_evaluations == 0
    assert audit.summary_builds == audit.rendering_builds == 20


def test_provenance_sources_probability_and_trace_survive_end_to_end():
    result = analyze_full_deal(_request(), bidding_router=create_standard_sayc_router())
    stage = result.subsystem_results[0]
    probability = result.probability_results[0]
    assert result.summary.items[0].result is stage
    assert result.rendering.sections[0].summary_item.result is stage
    assert result.rendering.source_references[0] is stage.evidence[0].source
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert probability.mode.value == "exact"
    assert probability.evidence[0].assumptions and probability.evidence[0].known_facts
    assert result.rendering.sections[-1].trace == probability.trace


def test_serialization_is_byte_stable_and_preserves_structure():
    result = analyze_full_deal(_request(), bidding_router=create_standard_sayc_router())
    first = json.dumps(full_deal_analysis_to_dict(result), sort_keys=True, separators=(",", ":"))
    second = json.dumps(full_deal_analysis_to_dict(result), sort_keys=True, separators=(",", ":"))
    assert first == second
    payload = json.loads(first)
    assert payload["requested_stages"] == ["auction", "probability-evidence"]
    assert payload["subsystem_results"][0]["action"]["kind"] == "bid"
    assert payload["probability_results"][0]["mode"] == "exact"


def test_unresolved_invalid_and_error_boundaries_remain_distinct():
    unresolved = analyze_full_deal(
        FullDealAnalysisInput(requested_stages=(AnalysisStage.OPENING_LEAD,))
    )
    invalid = analyze_full_deal(None)  # type: ignore[arg-type]
    assert unresolved.status.value == "no-decision"
    assert unresolved.skipped_stages[0].reason.value == "insufficient-stage-state"
    assert invalid.status.value == "error"
    assert invalid.skipped_stages[0].reason.value == "unsupported-request"


def test_closure_metrics_provenance_serialization_and_invention_are_exact():
    audit = run_phase15_coverage_closure_audit()
    assert (audit.closure_fixtures, audit.complete, audit.partial, audit.no_decision, audit.error) == (20, 11, 2, 6, 1)
    assert (audit.provenance_preserved, audit.provenance_lost) == (20, 0)
    assert (audit.serialization_successes, audit.serialization_failures, audit.deterministic_repeats) == (20, 0, 20)
    assert audit.hidden_information_violations == audit.recomputed_subsystem_decisions == 0
    assert set(audit.invention_audit.values()) == {0}
    assert audit.phase15_complete


def test_phase15a_and_phase15b_historical_guards_are_unchanged():
    a = run_full_deal_analysis_orchestration_benchmark()
    assert (a.fixtures, a.complete, a.partial, a.no_decision, a.error) == (18, 9, 3, 6, 0)
    assert (a.requested_stage_references, a.attempted_stage_references, a.skipped_stage_references) == (30, 29, 1)
    assert (a.auction_evaluations, a.opening_lead_evaluations, a.declarer_evaluations, a.defensive_evaluations, a.probability_evaluations) == (8, 7, 4, 4, 6)
    assert (a.orchestration_recommendation_references, a.evidence_references, a.unresolved_references, a.deterministic_repeats) == (12, 18, 11, 18)
    b = run_full_deal_orchestration_production_benchmark()
    assert (b.public_fixtures, b.complete, b.partial, b.no_decision, b.error) == (18, 9, 2, 6, 1)
    assert (b.public_requested_references, b.public_attempted_references, b.public_skipped_references) == (29, 26, 4)
    assert b.subsystem_evaluations == {"auction": 7, "opening-lead": 6, "declarer-play": 4, "defensive-play": 3, "probability-evidence": 6}
    assert (b.orchestration_recommendation_references, b.evidence_references, b.unresolved_references, b.deterministic_repeats) == (11, 17, 9, 18)


def test_phase14_closure_routes_and_defaults_are_unchanged():
    phase14 = run_phase14_coverage_closure_audit()
    assert phase14.phase14_complete and phase14.closure_fixtures == 16
    assert (phase14.structured_summary_successes, phase14.rendering_successes, phase14.pipeline_successes) == (16, 16, 16)
    assert (phase14.production_recommendations, phase14.provenance_preserved_fixtures, phase14.provenance_loss_fixtures) == (4, 16, 0)
    assert len(create_standard_sayc_router().routes) == 45
    assert PolicyRegistry().opening_lead_policy_ids == ()


def test_phase16_direction_and_human_output_are_safe():
    audit = run_phase15_coverage_closure_audit()
    result = analyze_full_deal(_request(), bidding_router=create_standard_sayc_router())
    assert audit.phase16_direction == "E. USER-FACING FULL-DEAL APPLICATION INTERFACE"
    assert not any(term in result.text.casefold() for term in ("confidence", "best overall", "hidden card"))
