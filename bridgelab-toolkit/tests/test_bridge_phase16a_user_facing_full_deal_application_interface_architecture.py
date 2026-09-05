from dataclasses import FrozenInstanceError
import json

import pytest

import bridge.full_deal_application as application_module
from benchmarks.end_to_end_analysis_architecture import _bidding
from benchmarks.full_deal_analysis_orchestration_architecture import _probability_request
from benchmarks.phase15_coverage_closure_audit import run_phase15_coverage_closure_audit
from benchmarks.user_facing_full_deal_application_interface_architecture import (
    _invalid_deals,
    run_user_facing_full_deal_application_benchmark,
)
from bridge import (
    AnalysisStage,
    FullDealAnalysisInput,
    FullDealApplicationErrorCode,
    FullDealApplicationRequest,
    FullDealApplicationResponse,
    PolicyRegistry,
    analyze_full_deal_application,
    application_request_to_full_deal_input,
    create_standard_sayc_router,
)


def _request() -> FullDealApplicationRequest:
    return FullDealApplicationRequest(
        requested_stages=("auction",),
        bidding=_bidding("KQJ876.32.43.543").bidding,
        probability_requests=(_probability_request(),),
    )


def test_application_models_are_immutable_and_public():
    request = _request()
    response = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    assert isinstance(response, FullDealApplicationResponse)
    with pytest.raises(FrozenInstanceError):
        request.requested_stages = ()
    with pytest.raises(FrozenInstanceError):
        response.status = "error"


def test_conversion_reuses_canonical_request_and_stage_types():
    request = _request()
    validation = application_request_to_full_deal_input(request)
    assert validation.is_valid
    assert isinstance(validation.canonical_request, FullDealAnalysisInput)
    assert validation.canonical_request.requested_stages == (AnalysisStage.AUCTION,)
    assert validation.canonical_request.bidding is request.bidding


def test_application_calls_canonical_orchestrator_exactly_once(monkeypatch):
    calls = 0
    canonical = application_module.analyze_full_deal

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return canonical(*args, **kwargs)

    monkeypatch.setattr(application_module, "analyze_full_deal", counted)
    response = application_module.analyze_full_deal_application(
        _request(), bidding_router=create_standard_sayc_router()
    )
    assert response.success and calls == 1
    assert response.diagnostics == (
        ("validation", "passed"),
        ("production-called", "yes"),
        ("serialization", "canonical"),
        ("rendering", "phase14b"),
    )


def test_structured_serialization_and_existing_rendered_text_are_reused(monkeypatch):
    calls = 0
    canonical = application_module.full_deal_analysis_to_dict

    def counted(result):
        nonlocal calls
        calls += 1
        return canonical(result)

    monkeypatch.setattr(application_module, "full_deal_analysis_to_dict", counted)
    response = application_module.analyze_full_deal_application(
        _request(), bidding_router=create_standard_sayc_router()
    )
    assert calls == 1
    assert response.structured_result == canonical(response.canonical_result)
    assert response.rendered_text == response.canonical_result.text
    assert json.dumps(response.structured_result, sort_keys=True)


def test_parse_validation_and_unsupported_errors_are_structured_without_tracebacks():
    malformed_seat, malformed_card, duplicate = _invalid_deals()
    fixtures = (
        (FullDealApplicationRequest(deal=malformed_seat), FullDealApplicationErrorCode.PARSE_ERROR),
        (FullDealApplicationRequest(deal=malformed_card), FullDealApplicationErrorCode.PARSE_ERROR),
        (FullDealApplicationRequest(deal=duplicate), FullDealApplicationErrorCode.PARSE_ERROR),
        (FullDealApplicationRequest(requested_stages=("unknown",)), FullDealApplicationErrorCode.VALIDATION_ERROR),
        (FullDealApplicationRequest(probability_requests=(object(),)), FullDealApplicationErrorCode.VALIDATION_ERROR),
    )
    for request, code in fixtures:
        response = analyze_full_deal_application(request)
        assert not response.success and response.errors[0].code is code
        assert "traceback" not in response.errors[0].message.casefold()
    unsupported = analyze_full_deal_application(None)  # type: ignore[arg-type]
    assert unsupported.errors[0].code is FullDealApplicationErrorCode.UNSUPPORTED_INPUT


def test_provenance_probability_skips_status_and_trace_survive_boundary():
    response = analyze_full_deal_application(
        _request(), bidding_router=create_standard_sayc_router()
    )
    result = response.canonical_result
    assert result is not None
    assert response.status == result.status.value
    assert response.structured_result["trace"] == result.trace
    assert result.rendering.source_references[0] is result.subsystem_results[0].evidence[0].source
    probability = result.probability_results[0]
    assert result.rendering.evidence_references[0] is probability.evidence[0]
    assert probability.mode.value == "exact"
    assert probability.evidence[0].assumptions and probability.evidence[0].known_facts
    skipped = analyze_full_deal_application(
        FullDealApplicationRequest(requested_stages=("opening-lead",))
    )
    assert skipped.structured_result["skipped_stages"][0]["reason"] == "insufficient-stage-state"


def test_complete_deal_is_identity_only_and_hidden_information_never_reconstructed():
    benchmark = run_user_facing_full_deal_application_benchmark()
    assert benchmark.hidden_information_violations == 0
    assert benchmark.duplicate_orchestration_calls == 0


def test_phase16_benchmark_counts_are_exact_and_deterministic():
    result = run_user_facing_full_deal_application_benchmark()
    assert (result.application_fixtures, result.valid_requests, result.invalid_requests) == (22, 16, 6)
    assert (result.complete, result.partial, result.no_decision, result.error) == (9, 1, 6, 6)
    assert (result.parse_failures, result.validation_failures, result.unsupported_input_failures, result.production_errors) == (3, 2, 1, 0)
    assert (result.production_orchestration_calls, result.duplicate_orchestration_calls) == (16, 0)
    assert (result.rendered_responses, result.structured_responses, result.deterministic_repeats, result.provenance_preserved_responses) == (16, 16, 22, 22)
    assert (result.invented_actions, result.invented_numbers, result.invented_sources, result.invented_probabilities) == (0, 0, 0, 0)


def test_phase15_closure_and_engine_guards_are_unchanged():
    phase15 = run_phase15_coverage_closure_audit()
    assert phase15.phase15_complete and len(phase15.readiness_matrix) == 17
    assert (phase15.closure_fixtures, phase15.complete, phase15.partial, phase15.no_decision, phase15.error) == (20, 11, 2, 6, 1)
    assert (phase15.requested_references, phase15.applicable_references, phase15.attempted_references, phase15.skipped_references) == (28, 26, 26, 3)
    assert (phase15.provenance_preserved, phase15.provenance_lost, phase15.serialization_successes, phase15.serialization_failures) == (20, 0, 20, 0)
    assert len(create_standard_sayc_router().routes) == 45
    assert PolicyRegistry().opening_lead_policy_ids == ()


def test_phase16b_direction_and_output_have_no_invented_conclusions():
    benchmark = run_user_facing_full_deal_application_benchmark()
    response = analyze_full_deal_application(
        _request(), bidding_router=create_standard_sayc_router()
    )
    assert benchmark.phase16b_direction == "A. COMMAND-LINE FULL-DEAL INTERFACE"
    assert not any(term in response.rendered_text.casefold() for term in ("confidence", "best overall", "hidden card"))
