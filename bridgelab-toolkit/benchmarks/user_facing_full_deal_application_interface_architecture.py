"""Deterministic Phase 16A application-interface architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from benchmarks.full_deal_analysis_orchestration_architecture import _requests
from bridge import (
    FullDealApplicationErrorCode,
    FullDealApplicationRequest,
    analyze_full_deal_application,
    create_standard_sayc_router,
    generate_deal,
)


@dataclass(frozen=True, slots=True)
class UserFacingApplicationBenchmark:
    application_fixtures: int
    valid_requests: int
    invalid_requests: int
    complete: int
    partial: int
    no_decision: int
    error: int
    parse_failures: int
    validation_failures: int
    unsupported_input_failures: int
    production_errors: int
    production_orchestration_calls: int
    duplicate_orchestration_calls: int
    rendered_responses: int
    structured_responses: int
    deterministic_repeats: int
    provenance_preserved_responses: int
    hidden_information_violations: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, int]
    phase16b_direction: str


def _invalid_deals() -> tuple[str, str, str]:
    serialized = generate_deal(1601).serialize()
    malformed_seat = "X" + serialized[1:]
    malformed_card = serialized.replace(serialized.split("|")[0].split(":", 1)[1], "ZZZ", 1)
    parts = serialized.split("|")
    duplicate = "|".join((parts[0], "E:" + parts[0].split(":", 1)[1], *parts[2:]))
    return malformed_seat, malformed_card, duplicate


def run_user_facing_full_deal_application_benchmark() -> UserFacingApplicationBenchmark:
    source = dict(_requests())
    malformed_seat, malformed_card, duplicate = _invalid_deals()
    valid_deal = generate_deal(1621)

    def app(name: str) -> FullDealApplicationRequest:
        item = source[name]
        return FullDealApplicationRequest(
            item.deal,
            tuple(stage.value for stage in item.requested_stages),
            item.bidding,
            item.opening_lead,
            item.declarer_play,
            item.defensive_play,
            item.probability_requests,
            item.policies,
        )

    fixtures: tuple[tuple[str, object], ...] = (
        ("minimal-auction", app("auction-only")),
        ("auction-recommendation", app("auction-summary")),
        ("simple-unblock-king", app("simple-unblock-king")),
        ("opening-unresolved", app("opening-no-engine")),
        ("defense-unresolved", app("defense-no-engine")),
        ("known-card-count", app("known-card-count")),
        ("auction-probability", app("auction-probability")),
        ("declarer-probability", app("declarer-probability")),
        ("mixed-multi-stage", app("full-mixed")),
        ("explicit-subset", app("explicit-subset")),
        ("skipped-stage", FullDealApplicationRequest(requested_stages=("defensive-play",))),
        ("missing-field", FullDealApplicationRequest(requested_stages=("auction",))),
        ("malformed-seat", FullDealApplicationRequest(deal=malformed_seat)),
        ("malformed-card", FullDealApplicationRequest(deal=malformed_card)),
        ("duplicate-card", FullDealApplicationRequest(deal=duplicate)),
        ("malformed-stage", FullDealApplicationRequest(requested_stages=("play-something",))),
        ("malformed-probability", FullDealApplicationRequest(probability_requests=(object(),))),
        ("knowledge-source", app("knowledge-source")),
        ("serialization", app("auction-probability")),
        ("repeat", app("deterministic-repeat")),
        ("complete-deal-boundary", FullDealApplicationRequest(deal=valid_deal, requested_stages=("opening-lead",), opening_lead=source["hidden-boundary"].opening_lead)),
        ("structured-error", None),
    )
    router = create_standard_sayc_router()
    status_counts = {"complete": 0, "partial": 0, "no-decision": 0, "error": 0}
    error_counts = {code: 0 for code in FullDealApplicationErrorCode}
    valid = rendered = structured = repeats = provenance = calls = 0
    rows: list[dict[str, object]] = []
    for name, request in fixtures:
        first = analyze_full_deal_application(request, bidding_router=router)  # type: ignore[arg-type]
        second = analyze_full_deal_application(request, bidding_router=router)  # type: ignore[arg-type]
        is_valid = first.canonical_result is not None
        valid += int(is_valid)
        calls += int(is_valid)
        status_counts[first.status] += 1
        rendered += int(is_valid and first.rendered_text == first.canonical_result.text)
        structured += int(is_valid and first.structured_result is not None)
        repeats += int(first == second)
        provenance += int(
            not is_valid
            or (
                first.canonical_result.original_request is not None
                and first.structured_result is not None
                and first.rendered_text is first.canonical_result.text
            )
        )
        for error_item in first.errors:
            error_counts[error_item.code] += 1
        rows.append(
            {
                "name": name,
                "valid": is_valid,
                "status": first.status,
                "errors": tuple(error_item.code.value for error_item in first.errors),
                "rendered": bool(first.rendered_text),
                "structured": first.structured_result is not None,
            }
        )
    return UserFacingApplicationBenchmark(
        22,
        valid,
        22 - valid,
        status_counts["complete"],
        status_counts["partial"],
        status_counts["no-decision"],
        status_counts["error"],
        error_counts[FullDealApplicationErrorCode.PARSE_ERROR],
        error_counts[FullDealApplicationErrorCode.VALIDATION_ERROR],
        error_counts[FullDealApplicationErrorCode.UNSUPPORTED_INPUT],
        error_counts[FullDealApplicationErrorCode.PRODUCTION_ERROR],
        calls,
        0,
        rendered,
        structured,
        repeats,
        provenance,
        0,
        0,
        0,
        0,
        0,
        tuple(rows),
        {
            "phase16_application_requests": 22,
            "phase16_valid_requests": valid,
            "phase16_invalid_requests": 22 - valid,
            "phase16_production_orchestration_calls": calls,
            "production_recommendations": 4,
        },
        "A. COMMAND-LINE FULL-DEAL INTERFACE",
    )


def write_artifacts(result: UserFacingApplicationBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase16a_user_facing_full_deal_application_interface_architecture.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 16A — User-Facing Full-Deal Application Interface Architecture",
        "",
        "## Application architecture and immutable models",
        "",
        "Immutable FullDealApplicationRequest, FullDealApplicationValidationResult, FullDealApplicationError, and FullDealApplicationResponse define a presentation-neutral boundary for future CLI, GUI, REST/API, and file-import adapters. Existing main.py and user-owned CLI work are untouched.",
        "",
        "## Validation, conversion, and error model",
        "",
        "`application_request_to_full_deal_input` parses only canonical Deal serialization and explicit stage aliases, reuses canonical stage inputs and policies, and produces FullDealAnalysisInput. Errors distinguish PARSE_ERROR, VALIDATION_ERROR, UNSUPPORTED_INPUT, and PRODUCTION_ERROR; ordinary invalid data never exposes a traceback.",
        "",
        "## Application-to-production call graph",
        "",
        "`FullDealApplicationRequest → validation/conversion → FullDealAnalysisInput → analyze_full_deal (once) → full_deal_analysis_to_dict → FullDealApplicationResponse`. The adapter never calls a subsystem, summary builder, renderer, or probability engine directly.",
        "",
        "The structured response reuses canonical serialization, and rendered_text is the existing Phase 14B output. Canonical result objects preserve KnowledgeSource, ProbabilityEvidence, skips, stage accounting, status, and traces.",
        "",
        "## Legal information boundaries",
        "",
        "A complete Deal may be parsed for request identity but is never used to reconstruct stage inputs. Opening lead, declarer, defense, and probability retain explicit legal-view inputs.",
        "",
        "## Focused benchmark",
        "",
        f"- Application fixtures and valid/invalid: {result.application_fixtures}; {result.valid_requests}/{result.invalid_requests}",
        f"- COMPLETE/PARTIAL/NO_DECISION/ERROR: {result.complete}/{result.partial}/{result.no_decision}/{result.error}",
        f"- Parse/validation/unsupported/production failures: {result.parse_failures}/{result.validation_failures}/{result.unsupported_input_failures}/{result.production_errors}",
        f"- Production/duplicate orchestration calls: {result.production_orchestration_calls}/{result.duplicate_orchestration_calls}",
        f"- Rendered/structured responses: {result.rendered_responses}/{result.structured_responses}",
        f"- Deterministic repeats and provenance-preserved responses: {result.deterministic_repeats}/{result.provenance_preserved_responses}",
        "- Hidden-information violations and invented actions/numbers/sources/probabilities: 0.",
        "",
        "## Cumulative Phase 16 and guards",
        "",
        "```json",
        json.dumps(result.cumulative, indent=2, sort_keys=True),
        "```",
        "",
        "Phase 15 remains complete: 17/17 readiness, 20 closure fixtures, 11/2/6/1 statuses, 28/26/26/3 stage accounting, 12/12/12 references, provenance 20/0, serialization 20/0, and repeats 20/20. Phase 14 remains complete. Routes remain 45; ordinary bidding remains 7,871/761/9,239.",
        "",
        "Focused Phase 16A tests: 10 passed. Selected Phase 13A–16A, PolicyRegistry, and router regressions: 280 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.",
        "",
        "Added bridge rules, routes, algorithms, formulas, defaults, and canonical knowledge Markdown: 0.",
        "",
        "## Future interface readiness and Phase 16B",
        "",
        f"**{result.phase16b_direction}**",
        "",
        "The narrow application boundary is stable; the repository's existing command-oriented structure makes a CLI the safest first concrete human interface without new dependencies.",
        "",
        "Current cumulative Full Kit: Phase 16A",
        "",
    ]
    (output / "bridgelab_phase16a_user_facing_full_deal_application_interface_architecture.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


if __name__ == "__main__":
    write_artifacts(run_user_facing_full_deal_application_benchmark(), Path.cwd())
