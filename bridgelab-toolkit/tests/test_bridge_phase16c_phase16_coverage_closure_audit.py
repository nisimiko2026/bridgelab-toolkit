import json
from dataclasses import FrozenInstanceError
from io import StringIO
from pathlib import Path

import pytest

import bridge
from benchmarks.command_line_full_deal_interface import (
    run_command_line_full_deal_benchmark,
)
from benchmarks.phase14_coverage_closure_audit import run_phase14_coverage_closure_audit
from benchmarks.phase15_coverage_closure_audit import run_phase15_coverage_closure_audit
from benchmarks.phase16_coverage_closure_audit import run_phase16_coverage_closure_audit
from benchmarks.user_facing_full_deal_application_interface_architecture import (
    run_user_facing_full_deal_application_benchmark,
)
from bridge import (
    FullDealApplicationRequest,
    PolicyRegistry,
    analyze_full_deal_application,
    create_standard_sayc_router,
)
from bridge.full_deal_cli import run_cli
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY


def test_phase16_inventory_and_readiness_matrix_are_complete():
    audit = run_phase16_coverage_closure_audit()
    assert [item["phase"] for item in audit.component_inventory] == ["16A", "16B"]
    assert len(audit.readiness_matrix) == 27
    assert {item["readiness"] for item in audit.readiness_matrix} == {
        "PRODUCTION_READY"
    }


def test_application_contracts_are_immutable_public_and_backward_compatible():
    request = FullDealApplicationRequest(requested_stages=("opening-lead",))
    response = analyze_full_deal_application(request)
    with pytest.raises(FrozenInstanceError):
        request.requested_stages = ()
    with pytest.raises(FrozenInstanceError):
        response.status = "changed"
    for name in (
        "analyze_deal_decision",
        "build_deal_summary",
        "render_deal_summary",
        "build_and_render_deal_summary",
        "analyze_full_deal",
        "full_deal_analysis_to_dict",
        "application_request_to_full_deal_input",
        "analyze_full_deal_application",
    ):
        assert callable(getattr(bridge, name))


def test_fresh_closure_application_status_and_cli_counts_are_exact():
    audit = run_phase16_coverage_closure_audit()
    assert (
        audit.closure_fixtures,
        audit.valid_application_requests,
        audit.invalid_application_requests,
    ) == (35, 8, 4)
    assert (audit.complete, audit.partial, audit.no_decision, audit.error) == (
        5,
        1,
        2,
        4,
    )
    assert (
        audit.cli_successful_executions,
        audit.cli_failed_executions,
        audit.text_outputs,
        audit.json_outputs,
    ) == (13, 4, 5, 7)
    assert (
        audit.cli_parse_failures,
        audit.application_validation_failures,
        audit.production_errors,
        audit.internal_errors,
    ) == (3, 1, 0, 0)
    assert audit.exit_code_counts == {"0": 13, "1": 0, "2": 3, "3": 1, "4": 0}


def test_single_call_no_bypass_and_provenance_audits_pass():
    audit = run_phase16_coverage_closure_audit()
    assert (
        audit.application_interface_calls,
        audit.duplicate_application_interface_calls,
    ) == (13, 0)
    assert (
        audit.production_orchestration_calls,
        audit.duplicate_production_orchestration_calls,
    ) == (20, 0)
    assert (
        audit.direct_subsystem_calls_from_cli
        == audit.direct_subsystem_calls_from_application
        == 0
    )
    assert (audit.provenance_preserved, audit.provenance_lost) == (15, 0)
    assert (audit.structured_json_successes, audit.structured_json_failures) == (7, 0)


def test_determinism_text_json_and_information_boundaries_are_clean():
    audit = run_phase16_coverage_closure_audit()
    assert (
        audit.deterministic_application_repeats,
        audit.deterministic_cli_text_repeats,
        audit.deterministic_cli_json_repeats,
    ) == (12, 1, 1)
    assert audit.text_output_mismatches == audit.hidden_information_violations == 0
    assert (
        audit.unsafe_parser_findings,
        audit.invented_actions,
        audit.invented_numbers,
        audit.invented_sources,
        audit.invented_probabilities,
    ) == (0, 0, 0, 0, 0)


def test_cli_file_stdin_utf8_output_and_errors_are_stable(tmp_path: Path):
    payload = {
        "probability_requests": [
            {
                "question": "known-card-count",
                "context": {
                    "visible_cards": ["AS"],
                    "played_cards": [],
                    "unknown_card_count": 51,
                },
            }
        ]
    }
    request_file = tmp_path / "עסקה.json"
    request_file.write_text(json.dumps(payload), encoding="utf-8")
    for source, output_format in ((str(request_file), "text"), ("-", "json")):
        stdout, stderr = StringIO(), StringIO()
        code = run_cli(
            ("--input", source, "--format", output_format),
            stdin=StringIO(json.dumps(payload)),
            stdout=stdout,
            stderr=stderr,
        )
        assert code == 0 and stdout.getvalue() and not stderr.getvalue()
    for raw in ("{", "[]"):
        stdout, stderr = StringIO(), StringIO()
        assert (
            run_cli(("--input", "-"), stdin=StringIO(raw), stdout=stdout, stderr=stderr)
            == 2
        )
        assert "traceback" not in stderr.getvalue().casefold()


def test_phase16a_historical_guards_are_exact():
    audit = run_user_facing_full_deal_application_benchmark()
    assert (
        audit.application_fixtures,
        audit.valid_requests,
        audit.invalid_requests,
    ) == (22, 16, 6)
    assert (audit.complete, audit.partial, audit.no_decision, audit.error) == (
        9,
        1,
        6,
        6,
    )
    assert (
        audit.parse_failures,
        audit.validation_failures,
        audit.unsupported_input_failures,
        audit.production_errors,
    ) == (3, 2, 1, 0)
    assert (
        audit.production_orchestration_calls,
        audit.duplicate_orchestration_calls,
        audit.rendered_responses,
        audit.structured_responses,
    ) == (16, 0, 16, 16)
    assert (audit.deterministic_repeats, audit.provenance_preserved_responses) == (
        22,
        22,
    )


def test_phase16b_historical_guards_are_exact():
    audit = run_command_line_full_deal_benchmark()
    assert (
        audit.cli_fixtures,
        audit.successful_executions,
        audit.failed_executions,
    ) == (28, 20, 8)
    assert (
        audit.text_outputs,
        audit.json_outputs,
        audit.cli_parse_failures,
        audit.application_validation_failures,
    ) == (10, 10, 3, 5)
    assert (
        audit.application_interface_calls,
        audit.duplicate_application_interface_calls,
    ) == (24, 0)
    assert (
        audit.production_orchestration_calls,
        audit.duplicate_production_orchestration_calls,
    ) == (19, 0)
    assert (
        audit.structured_json_successes,
        audit.provenance_preserved_json_responses,
    ) == (10, 10)


def test_phase15_phase14_engine_routes_and_defaults_guards():
    phase15 = run_phase15_coverage_closure_audit()
    phase14 = run_phase14_coverage_closure_audit()
    assert (
        phase15.phase15_complete
        and len(phase15.readiness_matrix) == 17
        and phase15.closure_fixtures == 20
    )
    assert (
        phase15.production_recommendations == 4
        and phase15.provenance_lost == phase15.serialization_failures == 0
    )
    assert phase14.phase14_complete
    assert len(create_standard_sayc_router().routes) == 45
    assert len(DEFAULT_PROBABILITY_ENGINE_REGISTRY.registrations) == 1
    assert PolicyRegistry().opening_lead_policy_ids == ()


def test_phase16_closes_without_interface_logic_or_knowledge_changes():
    audit = run_phase16_coverage_closure_audit()
    assert audit.phase16_complete and audit.backward_compatibility == "PASS"
    assert audit.phase17_direction == "E. BRIDGE-INTELLIGENCE EXPANSION PROGRAM"
    cli_source = Path(bridge.full_deal_cli.__file__).read_text(encoding="utf-8")
    app_source = Path(bridge.full_deal_application.__file__).read_text(encoding="utf-8")
    assert all(
        token not in cli_source
        for token in (
            "eval(",
            "exec(",
            "pickle",
            "evaluate_probability(",
            "build_deal_summary(",
        )
    )
    assert all(
        token not in app_source
        for token in (
            "evaluate_probability(",
            "build_deal_summary(",
            "render_deal_summary(",
        )
    )
