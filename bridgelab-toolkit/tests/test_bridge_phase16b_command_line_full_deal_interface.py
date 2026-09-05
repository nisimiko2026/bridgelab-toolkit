import json
from io import StringIO
from pathlib import Path

import bridge.full_deal_application as application_module
import bridge.full_deal_cli as cli
from benchmarks.command_line_full_deal_interface import (
    run_command_line_full_deal_benchmark,
)
from benchmarks.phase15_coverage_closure_audit import run_phase15_coverage_closure_audit
from benchmarks.user_facing_full_deal_application_interface_architecture import (
    run_user_facing_full_deal_application_benchmark,
)
from bridge import (
    FullDealApplicationError,
    FullDealApplicationErrorCode,
    FullDealApplicationResponse,
    create_standard_sayc_router,
)


def _run(payload, output_format="text", analyzer=None):
    stdout, stderr = StringIO(), StringIO()
    kwargs = {} if analyzer is None else {"analyzer": analyzer}
    code = cli.run_cli(
        ("--input", "-", "--format", output_format),
        stdin=StringIO(json.dumps(payload)),
        stdout=stdout,
        stderr=stderr,
        **kwargs,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_cli_import_help_entry_point_and_exit_contract():
    help_text = cli._parser().format_help()
    assert (
        "--input" in help_text and "--format" in help_text and "Exit codes" in help_text
    )
    assert (
        cli.EXIT_SUCCESS,
        cli.EXIT_INTERNAL_ERROR,
        cli.EXIT_CLI_PARSE_ERROR,
        cli.EXIT_APPLICATION_ERROR,
        cli.EXIT_PRODUCTION_ERROR,
    ) == (0, 1, 2, 3, 4)
    assert callable(cli.main)


def test_json_file_stdin_windows_path_and_utf8(tmp_path: Path):
    request = tmp_path / "עסקה.json"
    request.write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )
    stdout, stderr = StringIO(), StringIO()
    code = cli.run_cli(("--input", str(request)), stdout=stdout, stderr=stderr)
    assert (
        code == 0 and "Status: COMPLETE" in stdout.getvalue() and not stderr.getvalue()
    )
    assert _run({"requested_stages": ["opening_lead"]})[0] == 0


def test_cli_parse_errors_are_deterministic_machine_friendly_and_traceback_free(
    tmp_path: Path,
):
    fixtures = (("{", "-"), ("[]", "-"), ("", str(tmp_path / "missing.json")))
    for raw, source in fixtures:
        out, err = StringIO(), StringIO()
        code = cli.run_cli(
            ("--input", source, "--format", "json"),
            stdin=StringIO(raw),
            stdout=out,
            stderr=err,
        )
        parsed = json.loads(err.getvalue())
        assert (
            code == 2
            and not out.getvalue()
            and parsed["errors"][0]["code"] == "CLI_PARSE_ERROR"
        )
        assert "traceback" not in err.getvalue().casefold()


def test_valid_input_delegates_exactly_once_and_never_calls_orchestrator_directly():
    calls = 0
    canonical = application_module.analyze_full_deal_application

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return canonical(*args, **kwargs)

    # Injection proves one application call; CLI has no analyze_full_deal symbol.
    code, _, _ = _run({"requested_stages": ["opening-lead"]}, analyzer=counted)
    assert code == 0 and calls == 1 and not hasattr(cli, "analyze_full_deal")


def test_text_and_json_reuse_structured_application_output_and_provenance():
    payload = {
        "probability_requests": [
            {
                "question": "known-card-count",
                "context": {
                    "visible_cards": ["AS", "KH"],
                    "played_cards": [],
                    "unknown_card_count": 50,
                },
            }
        ]
    }
    text_first = _run(payload, "text")
    text_second = _run(payload, "text")
    json_first = _run(payload, "json")
    json_second = _run(payload, "json")
    body = json.loads(json_first[1])
    evidence = body["result"]["probability_results"][0]["evidence"][0]
    assert text_first == text_second and json_first == json_second
    assert body["rendered_text"] and evidence["type"] == "known-card-count"
    assert evidence["assumptions"] and evidence["known_facts"] and "source" in evidence
    assert all(
        key in body["result"]
        for key in (
            "requested_stages",
            "applicable_stages",
            "attempted_stages",
            "skipped_stages",
        )
    )


def test_application_and_production_failures_have_distinct_exit_codes():
    assert _run({"requested_stages": ["invalid"]})[0] == 3

    def production_error(*args, **kwargs):
        error = FullDealApplicationError(
            FullDealApplicationErrorCode.PRODUCTION_ERROR, "production", "controlled"
        )
        return FullDealApplicationResponse(False, "error", None, None, "", (error,))

    code, stdout, stderr = _run({}, "json", production_error)
    assert (
        code == 4
        and not stdout
        and json.loads(stderr)["errors"][0]["code"] == "production-error"
    )
    assert "traceback" not in stderr.casefold()


def test_unexpected_internal_failure_is_controlled():
    def failure(*args, **kwargs):
        raise RuntimeError("controlled")

    code, stdout, stderr = _run({}, "json", failure)
    assert (
        code == 1
        and not stdout
        and json.loads(stderr)["errors"][0]["code"] == "INTERNAL_ERROR"
    )


def test_benchmark_has_28_deterministic_safe_fixtures_and_single_calls():
    result = run_command_line_full_deal_benchmark()
    assert result.cli_fixtures == 28
    assert result.successful_executions + result.failed_executions == 28
    assert result.deterministic_text_repeats == result.deterministic_json_repeats == 1
    assert (
        result.duplicate_application_interface_calls
        == result.duplicate_production_orchestration_calls
        == 0
    )
    assert (
        result.hidden_information_violations,
        result.invented_actions,
        result.invented_numbers,
        result.invented_sources,
        result.invented_probabilities,
    ) == (0, 0, 0, 0, 0)
    assert result.phase16c_direction == "E. PHASE 16 COVERAGE / CLOSURE AUDIT"


def test_phase16a_phase15_phase14_routes_and_defaults_guards():
    phase16a = run_user_facing_full_deal_application_benchmark()
    assert (
        phase16a.application_fixtures,
        phase16a.valid_requests,
        phase16a.invalid_requests,
    ) == (22, 16, 6)
    assert (
        phase16a.complete,
        phase16a.partial,
        phase16a.no_decision,
        phase16a.error,
    ) == (9, 1, 6, 6)
    assert (
        phase16a.parse_failures,
        phase16a.validation_failures,
        phase16a.unsupported_input_failures,
        phase16a.production_errors,
    ) == (3, 2, 1, 0)
    assert (
        phase16a.production_orchestration_calls,
        phase16a.duplicate_orchestration_calls,
        phase16a.deterministic_repeats,
        phase16a.provenance_preserved_responses,
    ) == (16, 0, 22, 22)
    phase15 = run_phase15_coverage_closure_audit()
    assert (
        phase15.phase15_complete
        and len(phase15.readiness_matrix) == 17
        and phase15.closure_fixtures == 20
    )
    assert (phase15.complete, phase15.partial, phase15.no_decision, phase15.error) == (
        11,
        2,
        6,
        1,
    )
    assert len(create_standard_sayc_router().routes) == 45


def test_cli_contains_no_unsafe_parser_or_bridge_intelligence():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert all(
        token not in source
        for token in ("eval(", "exec(", "pickle", "confidence score", "best-action")
    )
    assert "analyze_full_deal_application" in source
    assert all(
        token not in source
        for token in (
            "evaluate_probability(",
            "analyze_deal_decision(",
            "build_and_render_deal_summary(",
        )
    )
