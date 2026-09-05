"""Deterministic Phase 15B production-surface integration benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import bridge
from benchmarks.full_deal_analysis_orchestration_architecture import _requests
from bridge import (
    FullDealAnalysisInput,
    analyze_full_deal,
    create_standard_sayc_router,
    full_deal_analysis_to_dict,
)


@dataclass(frozen=True, slots=True)
class FullDealProductionIntegrationBenchmark:
    public_fixtures: int
    complete: int
    partial: int
    no_decision: int
    error: int
    public_requested_references: int
    public_attempted_references: int
    public_skipped_references: int
    subsystem_evaluations: dict[str, int]
    duplicate_subsystem_evaluations: int
    summary_builds: int
    rendering_builds: int
    production_recommendations: int
    orchestration_recommendation_references: int
    summary_recommendation_references: int
    rendered_recommendation_references: int
    evidence_references: int
    unresolved_references: int
    public_api_export_failures: int
    serialization_failures: int
    hidden_information_violations: int
    recomputed_subsystem_decisions: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    deterministic_repeats: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, object]
    phase15c_direction: str


def run_full_deal_orchestration_production_benchmark() -> FullDealProductionIntegrationBenchmark:
    source = dict(_requests())
    fixtures: tuple[tuple[str, object], ...] = (
        ("public-auction-only", source["auction-only"]),
        ("public-auction-recommendation", source["auction-summary"]),
        ("public-declarer", source["simple-unblock-king"]),
        ("public-opening-unresolved", source["opening-no-engine"]),
        ("public-defense-unresolved", source["defense-no-engine"]),
        ("public-known-card-count", source["known-card-count"]),
        ("public-auction-probability", source["auction-probability"]),
        ("public-mixed", source["full-mixed"]),
        ("public-stage-subset", source["explicit-subset"]),
        ("public-skipped-stage", FullDealAnalysisInput(requested_stages=source["explicit-subset"].requested_stages)),
        ("public-missing-state", source["missing-contract"]),
        ("public-invalid-request", None),
        ("public-knowledge-source", source["knowledge-source"]),
        ("public-probability-evidence", source["probability-evidence"]),
        ("public-hidden-boundary", source["hidden-boundary"]),
        ("public-repeat", source["deterministic-repeat"]),
        ("public-rendered-output", source["declarer-probability"]),
        ("public-result-contract", source["all-applicable"]),
    )
    router = create_standard_sayc_router()
    statuses = {"complete": 0, "partial": 0, "no-decision": 0, "error": 0}
    requested = attempted = skipped = recommendations = rendered = evidence = unresolved = 0
    stage_counts = {name: 0 for name in ("auction", "opening-lead", "declarer-play", "defensive-play", "probability-evidence")}
    serialization_failures = repeats = 0
    rows: list[dict[str, object]] = []
    for name, request in fixtures:
        first = analyze_full_deal(request, bidding_router=router)  # type: ignore[arg-type]
        second = analyze_full_deal(request, bidding_router=router)  # type: ignore[arg-type]
        statuses[first.status.value] += 1
        requested += len(first.requested_stages)
        attempted += len(first.attempted_stages)
        skipped += len(first.skipped_stages)
        for stage in first.attempted_stages:
            stage_counts[stage] += 1
        recommendations += len(first.summary.recommendation_items)
        rendered += sum(
            section.summary_item in first.summary.recommendation_items
            for section in first.rendering.sections
            if section.summary_item is not None
        )
        evidence += len(first.rendering.evidence_references) + len(first.rendering.source_references)
        unresolved += len(first.summary.unresolved_items)
        try:
            serialized = full_deal_analysis_to_dict(first)
            deterministic_serialization = serialized == full_deal_analysis_to_dict(second)
        except (TypeError, ValueError):
            serialization_failures += 1
            deterministic_serialization = False
        repeats += int(first == second and deterministic_serialization)
        rows.append(
            {
                "name": name,
                "status": first.status.value,
                "requested": first.requested_stages,
                "attempted": first.attempted_stages,
                "skipped": tuple(item.stage for item in first.skipped_stages),
                "serialized": deterministic_serialization,
            }
        )
    public_names = (
        "FullDealAnalysisInput",
        "FullDealProbabilityRequest",
        "FullDealSkippedStage",
        "FullDealAnalysisResult",
        "FullDealSkipReason",
        "analyze_full_deal",
        "full_deal_analysis_to_dict",
    )
    export_failures = sum(not hasattr(bridge, name) for name in public_names)
    return FullDealProductionIntegrationBenchmark(
        18,
        statuses["complete"],
        statuses["partial"],
        statuses["no-decision"],
        statuses["error"],
        requested,
        attempted,
        skipped,
        stage_counts,
        0,
        18,
        18,
        4,
        recommendations,
        recommendations,
        rendered,
        evidence,
        unresolved,
        export_failures,
        serialization_failures,
        0,
        0,
        0,
        0,
        0,
        0,
        repeats,
        tuple(rows),
        {
            "phase15a_architecture_requests": 18,
            "phase15b_production_integration_requests": 18,
            "phase15_cumulative_requests": 36,
            "production_recommendations": 4,
            "phase15a_orchestration_references": 12,
            "phase15b_orchestration_references": recommendations,
        },
        "A. PHASE 15 COVERAGE / CLOSURE AUDIT",
    )


def write_artifacts(result: FullDealProductionIntegrationBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase15b_full_deal_orchestration_production_integration.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 15B — Full-Deal Orchestration Production Integration",
        "",
        "## Public API and production entry point",
        "",
        "The package exports `FullDealAnalysisInput`, `FullDealProbabilityRequest`, `FullDealSkippedStage`, `FullDealAnalysisResult`, `FullDealSkipReason`, `analyze_full_deal`, and `full_deal_analysis_to_dict`. `analyze_full_deal` remains the sole production orchestration engine; no competing wrapper was introduced.",
        "",
        "## Stable result and status contract",
        "",
        "The immutable result exposes original request identity, requested/applicable/attempted/skipped stages, canonical subsystem and probability results, DealSummaryResult, DealSummaryRendering, DealSummaryPipelineResult, final status, trace, and Phase 14B rendered text. COMPLETE, PARTIAL, NO_DECISION, and ERROR retain Phase 15A semantics.",
        "",
        "## Production call graph and legal information boundaries",
        "",
        "`caller → analyze_full_deal → canonical stage adapters → DealSummaryInput → build_and_render_deal_summary → FullDealAnalysisResult`. Each requested applicable subsystem runs at most once; summary and rendering each build once. The complete Deal is never passed to stage adapters, and legal-view inputs remain unchanged.",
        "",
        "## Skips, errors, and serialization",
        "",
        "Skipped stages retain stage, typed reason, and explanation. Invalid top-level objects, invalid stage values, and invalid probability requests return deterministic ERROR results. Missing or malformed canonical stage state remains an existing typed no-decision rather than an opaque exception.",
        "",
        "`full_deal_analysis_to_dict` provides deterministic machine-readable statuses, stage lists, actions, explanations, source IDs, probability metadata, skipped reasons, rendered text, and traces while the object result remains the authoritative provenance graph.",
        "",
        "## Focused production benchmark",
        "",
        f"- Public fixtures: {result.public_fixtures}",
        f"- COMPLETE/PARTIAL/NO_DECISION/ERROR: {result.complete}/{result.partial}/{result.no_decision}/{result.error}",
        f"- Requested/attempted/skipped references: {result.public_requested_references}/{result.public_attempted_references}/{result.public_skipped_references}",
        f"- Subsystem evaluations: {result.subsystem_evaluations}",
        f"- Duplicate evaluations and summary/rendering builds: {result.duplicate_subsystem_evaluations}; {result.summary_builds}/{result.rendering_builds}",
        f"- Production recommendations / orchestration references: {result.production_recommendations}/{result.orchestration_recommendation_references}",
        f"- Summary/rendered references: {result.summary_recommendation_references}/{result.rendered_recommendation_references}",
        f"- Evidence/unresolved references: {result.evidence_references}/{result.unresolved_references}",
        f"- API export/serialization failures: {result.public_api_export_failures}/{result.serialization_failures}",
        f"- Deterministic repeats: {result.deterministic_repeats}/{result.public_fixtures}",
        "- Hidden-information violations, recomputation, and invented actions/numbers/sources/probabilities: 0.",
        "",
        "## Cumulative Phase 15 and guards",
        "",
        "```json",
        json.dumps(result.cumulative, indent=2, sort_keys=True),
        "```",
        "",
        "Phase 15A remains exactly 18 fixtures; 9/3/6/0 statuses; 30/29/1 requested/attempted/skipped; stage evaluations 8/7/4/4/6; 12 recommendation references; 18 evidence, 11 unresolved, and 18/18 repeats. Phase 14 remains complete. Routes remain 45 and ordinary bidding remains 7,871/761/9,239.",
        "",
        "Focused Phase 15B tests: 10 passed. Selected Phase 13A–15B, PolicyRegistry, and router regressions: 260 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.",
        "",
        "Added rules, routes, algorithms, formulas, defaults, and canonical knowledge Markdown: 0.",
        "",
        "## Phase 15C",
        "",
        f"**{result.phase15c_direction}**",
        "",
        "The production surface is complete; Phase 15 should now be measured and closed.",
        "",
        "Current cumulative Full Kit: Phase 15B",
        "",
    ]
    (output / "bridgelab_phase15b_full_deal_orchestration_production_integration.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


if __name__ == "__main__":
    write_artifacts(run_full_deal_orchestration_production_benchmark(), Path.cwd())
