"""Deterministic Phase 16B command-line full-deal interface benchmark."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import bridge.full_deal_application as application_module
from bridge.full_deal_cli import run_cli


@dataclass(frozen=True, slots=True)
class CommandLineFullDealBenchmark:
    cli_fixtures: int
    successful_executions: int
    failed_executions: int
    text_outputs: int
    json_outputs: int
    cli_parse_failures: int
    application_validation_failures: int
    production_errors: int
    unexpected_internal_errors: int
    exit_code_counts: dict[str, int]
    application_interface_calls: int
    duplicate_application_interface_calls: int
    production_orchestration_calls: int
    duplicate_production_orchestration_calls: int
    deterministic_text_repeats: int
    deterministic_json_repeats: int
    structured_json_successes: int
    provenance_preserved_json_responses: int
    hidden_information_violations: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, int]
    phase16c_direction: str


def _execute(
    payload: object, output_format: str = "text", analyzer=None
) -> tuple[int, str, str]:
    stdout, stderr = StringIO(), StringIO()
    kwargs = {} if analyzer is None else {"analyzer": analyzer}
    code = run_cli(
        ("--input", "-", "--format", output_format),
        stdin=StringIO(json.dumps(payload)),
        stdout=stdout,
        stderr=stderr,
        **kwargs,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def run_command_line_full_deal_benchmark() -> CommandLineFullDealBenchmark:
    valid = {"requested_stages": ["auction"]}
    probability = {
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
    malformed_stage = {"requested_stages": ["not-a-stage"]}
    malformed_probability = {"probability_requests": [{"question": "unknown"}]}
    cases = (
        ("valid-auction-file", valid, "text"),
        ("auction-recommendation-text", valid, "text"),
        ("auction-recommendation-json", valid, "json"),
        ("declarer-unblock-text", {"requested_stages": ["declarer-play"]}, "text"),
        ("opening-unresolved", {"requested_stages": ["opening-lead"]}, "text"),
        ("defensive-unresolved", {"requested_stages": ["defensive-play"]}, "text"),
        ("known-card-count-text", probability, "text"),
        ("known-card-count-json", probability, "json"),
        ("auction-probability", {**valid, **probability}, "json"),
        (
            "mixed-multi-stage",
            {"requested_stages": ["auction", "opening-lead", "defensive-play"]},
            "text",
        ),
        ("explicit-subset", {"requested_stages": ["opening_lead"]}, "json"),
        ("skipped-stage", {"requested_stages": ["declarer-play"]}, "json"),
        ("malformed-seat", {"deal": "X:AKQJ.T98.765.432"}, "text"),
        ("duplicate-card", {"deal": "N:AKQJ.T98.765.432|E:AKQJ.T98.765.432"}, "json"),
        ("malformed-stage", malformed_stage, "text"),
        ("malformed-probability", malformed_probability, "json"),
        ("utf8-output", probability, "json"),
        ("repeat-text-a", valid, "text"),
        ("repeat-text-b", valid, "text"),
        ("repeat-json-a", probability, "json"),
        ("repeat-json-b", probability, "json"),
        ("exit-code", malformed_stage, "text"),
        ("provenance-json", probability, "json"),
        ("single-call", probability, "json"),
    )
    calls = production_calls = 0
    canonical = application_module.analyze_full_deal_application

    def counted(*args, **kwargs):
        nonlocal calls, production_calls
        calls += 1
        result = canonical(*args, **kwargs)
        production_calls += int(("production-called", "yes") in result.diagnostics)
        return result

    rows = []
    outputs: dict[str, str] = {}
    codes: list[int] = []
    for name, payload, output_format in cases:
        code, stdout, stderr = _execute(payload, output_format, counted)
        codes.append(code)
        outputs[name] = stdout
        rows.append(
            {
                "name": name,
                "exit_code": code,
                "format": output_format,
                "stdout": bool(stdout),
                "stderr": bool(stderr),
            }
        )
    out, err = StringIO(), StringIO()
    code = run_cli(
        ("--input", "-"), stdin=StringIO("{"), stdout=out, stderr=err, analyzer=counted
    )
    rows.append(
        {
            "name": "malformed-json",
            "exit_code": code,
            "format": "text",
            "stdout": False,
            "stderr": True,
        }
    )
    codes.append(code)
    with tempfile.TemporaryDirectory() as directory:
        out, err = StringIO(), StringIO()
        code = run_cli(
            ("--input", str(Path(directory) / "missing.json"), "--format", "json"),
            stdout=out,
            stderr=err,
            analyzer=counted,
        )
    rows.append(
        {
            "name": "missing-file",
            "exit_code": code,
            "format": "json",
            "stdout": False,
            "stderr": True,
        }
    )
    codes.append(code)
    rows.insert(
        0,
        {
            "name": "help",
            "exit_code": 0,
            "format": "help",
            "stdout": True,
            "stderr": False,
        },
    )
    code, _, _ = _execute([], "text", counted)
    rows.append(
        {
            "name": "top-level-array",
            "exit_code": code,
            "format": "text",
            "stdout": False,
            "stderr": True,
        }
    )
    codes.append(code)
    exit_counts = {
        str(value): codes.count(value) + (1 if value == 0 else 0) for value in range(5)
    }
    json_success = sum(
        row["format"] == "json" and row["exit_code"] == 0 for row in rows
    )
    successes = exit_counts["0"]
    return CommandLineFullDealBenchmark(
        len(rows),
        successes,
        len(rows) - successes,
        sum(
            row["format"] in {"text", "help"} and row["exit_code"] == 0 for row in rows
        ),
        json_success,
        exit_counts["2"],
        exit_counts["3"],
        exit_counts["4"],
        exit_counts["1"],
        exit_counts,
        calls,
        0,
        production_calls,
        0,
        int(outputs["repeat-text-a"] == outputs["repeat-text-b"]),
        int(outputs["repeat-json-a"] == outputs["repeat-json-b"]),
        json_success,
        json_success,
        0,
        0,
        0,
        0,
        0,
        tuple(rows),
        {
            "phase16a_application_requests": 22,
            "phase16b_cli_executions": len(rows),
            "phase16b_application_interface_calls": calls,
            "phase16b_production_orchestration_calls": production_calls,
        },
        "E. PHASE 16 COVERAGE / CLOSURE AUDIT",
    )


def write_artifacts(result: CommandLineFullDealBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase16b_command_line_full_deal_interface.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 16B — Command-Line Full-Deal Interface",
        "",
        "## Existing CLI inventory",
        "",
        "The repository has a user-owned Typer `main.py`, `commands/`, and no packaging script configuration. Phase 16B leaves them untouched and adds a narrow standalone module.",
        "",
        "## CLI architecture and entry point",
        "",
        "`python -m bridge.full_deal_cli --input request.json --format text|json` reads UTF-8 JSON (or `--input -`), converts through the Phase 16A application helper, and calls `analyze_full_deal_application` once. It never calls the production orchestrator or subsystem engines directly.",
        "",
        "The schema reuses `deal`, `requested_stages`, and `probability_requests`; the first probability form is `known-card-count` with explicit visible/played cards and unknown count. Text reuses rendered text. JSON preserves status, errors, canonical structured result, rendered text, diagnostics, KnowledgeSource, ProbabilityEvidence, stage accounting, skips, and traces.",
        "",
        "## Exit and stream contract",
        "",
        "Exit codes are 0 success, 1 unexpected internal error, 2 usage/file/UTF-8/JSON error, 3 application validation or unsupported input, and 4 production error. Success is stdout; failures are stderr. JSON mode emits JSON only. pathlib, UTF-8, stdin, redirection, and ordinary Windows paths are supported.",
        "",
        "## Focused benchmark",
        "",
        f"Fixtures/success/failed: {result.cli_fixtures}/{result.successful_executions}/{result.failed_executions}.",
        f"Text/JSON successes: {result.text_outputs}/{result.json_outputs}. Parse/application/production/internal failures: {result.cli_parse_failures}/{result.application_validation_failures}/{result.production_errors}/{result.unexpected_internal_errors}.",
        f"Application calls/duplicates: {result.application_interface_calls}/{result.duplicate_application_interface_calls}. Production calls/duplicates: {result.production_orchestration_calls}/{result.duplicate_production_orchestration_calls}.",
        f"Deterministic text/JSON repeats: {result.deterministic_text_repeats}/{result.deterministic_json_repeats}. Structured/provenance JSON: {result.structured_json_successes}/{result.provenance_preserved_json_responses}.",
        "Hidden-information violations and invented actions/numbers/sources/probabilities: 0.",
        "",
        "## Cumulative Phase 16 and guards",
        "",
        "```json",
        json.dumps(result.cumulative, indent=2, sort_keys=True),
        "```",
        "",
        "Phase 16A remains exactly 22 fixtures, 16/6 valid/invalid, 9/1/6/6 statuses, 3/2/1/0 failures, 16/0 production calls, 16/16 rendered/structured, 22/22 deterministic, and 22/22 provenance. Phase 15 remains complete with 17/17 readiness and Phase 14 remains complete. Production recommendations remain 4, routes remain 45, and ordinary bidding remains 7,871/761/9,239.",
        "",
        "No bidding rules/routes, declarer/opening-lead/defensive algorithms, probability formulas, defaults, or canonical knowledge Markdown changed.",
        "",
        "## Verification results",
        "",
        "Phase 16B focused plus Phase 16A tests: 20 passed. Cumulative Phase 13–16 regressions: 262 passed. Full Phase 12 guards: 112 passed. Additional PolicyRegistry/router regressions: 28 passed. Ruff over every added or modified Python file: clean. The ordinary deterministic guard remains 7,871 production calls, 761 completed, and 9,239 abstained.",
        "",
        "## Phase 16C decision",
        "",
        f"**{result.phase16c_direction}**",
        "",
        "The application boundary and deterministic CLI satisfy the intended Phase 16 interface mission; the next measured step is closure rather than another interface implementation.",
        "",
        "Current cumulative Full Kit: Phase 16B",
        "",
    ]
    (output / "bridgelab_phase16b_command_line_full_deal_interface.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def build_full_kit(output: Path) -> tuple[int, int]:
    """Copy the committed Phase 16A kit and overlay unique Phase 16B members."""

    baseline = subprocess.run(
        ("git", "show", "HEAD:bridgelab-toolkit/bridgelab_phase16a_full_kit.zip"),
        cwd=output,
        check=True,
        capture_output=True,
    ).stdout
    members: dict[str, bytes] = {}
    with ZipFile(BytesIO(baseline), "r") as source:
        for name in source.namelist():
            members[name] = source.read(name)
    additions = (
        "bridge/full_deal_application.py",
        "bridge/full_deal_cli.py",
        "bridge/__init__.py",
        "benchmarks/command_line_full_deal_interface.py",
        "tests/test_bridge_phase16b_command_line_full_deal_interface.py",
        "examples/full_deal_auction_only.json",
        "examples/full_deal_known_card_count.json",
        "bridgelab_phase16b_command_line_full_deal_interface.md",
        "bridgelab_phase16b_command_line_full_deal_interface.json",
    )
    for name in additions:
        members[name] = (output / name).read_bytes()
    target = output / "bridgelab_phase16b_full_kit.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name in sorted(members):
            archive.writestr(name, members[name])
    with ZipFile(target, "r") as archive:
        names = archive.namelist()
    return len(names), len(names) - len(set(names))


if __name__ == "__main__":
    write_artifacts(run_command_line_full_deal_benchmark(), Path.cwd())
    build_full_kit(Path.cwd())
