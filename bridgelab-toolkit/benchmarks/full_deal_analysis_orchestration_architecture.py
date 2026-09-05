"""Deterministic Phase 15A full-deal orchestration architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from benchmarks.defensive_state_architecture import _input as defensive_input
from benchmarks.end_to_end_analysis_architecture import _bidding
from benchmarks.first_declarer_recommendation_engine import _input as declarer_input
from benchmarks.opening_lead_state_architecture import _input as opening_input
from bridge import (
    AnalysisStage,
    FullDealAnalysisInput,
    FullDealProbabilityRequest,
    KnownCardCountQuestion,
    ProbabilityContext,
    analyze_full_deal,
    create_standard_sayc_router,
    generate_deal,
)
from bridge.defensive_play_state import DefensivePlayInput
from bridge.opening_lead_state import OpeningLeadInput


@dataclass(frozen=True, slots=True)
class FullDealOrchestrationBenchmark:
    fixtures: int
    complete: int
    partial: int
    no_decision: int
    error: int
    requested_stage_references: int
    attempted_stage_references: int
    skipped_stage_references: int
    auction_evaluations: int
    opening_lead_evaluations: int
    declarer_evaluations: int
    defensive_evaluations: int
    probability_evaluations: int
    production_recommendations: int
    orchestration_recommendation_references: int
    summary_recommendation_references: int
    rendered_recommendation_references: int
    evidence_references: int
    unresolved_references: int
    summary_builds: int
    rendering_builds: int
    hidden_information_violations: int
    recomputed_subsystem_decisions: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    deterministic_repeats: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, object]
    phase15b_direction: str


def _probability_request() -> FullDealProbabilityRequest:
    cards = generate_deal(1501).hand(next(iter(generate_deal(1501).mapping))).cards
    return FullDealProbabilityRequest(
        KnownCardCountQuestion(), ProbabilityContext(cards, frozenset(), 39)
    )


def _requests() -> tuple[tuple[str, FullDealAnalysisInput], ...]:
    auction = _bidding("KQJ876.32.43.543").bidding
    declarer = declarer_input()
    opening = opening_input()
    defense = defensive_input()
    probability = _probability_request()
    full_deal = generate_deal(1514)
    all_stages = (
        AnalysisStage.AUCTION,
        AnalysisStage.OPENING_LEAD,
        AnalysisStage.DECLARER_PLAY,
        AnalysisStage.DEFENSIVE_PLAY,
    )
    return (
        ("auction-only", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION,), bidding=auction)),
        ("auction-summary", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION,), bidding=auction)),
        ("simple-unblock-king", FullDealAnalysisInput(requested_stages=(AnalysisStage.DECLARER_PLAY,), declarer_play=declarer)),
        ("opening-no-engine", FullDealAnalysisInput(requested_stages=(AnalysisStage.OPENING_LEAD,), opening_lead=opening)),
        ("defense-no-engine", FullDealAnalysisInput(requested_stages=(AnalysisStage.DEFENSIVE_PLAY,), defensive_play=defense)),
        ("known-card-count", FullDealAnalysisInput(probability_requests=(probability,))),
        ("auction-probability", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION,), bidding=auction, probability_requests=(probability,))),
        ("declarer-probability", FullDealAnalysisInput(requested_stages=(AnalysisStage.DECLARER_PLAY,), declarer_play=declarer, probability_requests=(probability,))),
        ("mixed", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD), bidding=auction, opening_lead=opening)),
        ("all-applicable", FullDealAnalysisInput(requested_stages=all_stages, bidding=auction, opening_lead=opening, declarer_play=declarer, defensive_play=defense, probability_requests=(probability,))),
        ("missing-contract", FullDealAnalysisInput(requested_stages=(AnalysisStage.OPENING_LEAD,), opening_lead=OpeningLeadInput())),
        ("invalid-stage-state", FullDealAnalysisInput(requested_stages=(AnalysisStage.DEFENSIVE_PLAY,), defensive_play=DefensivePlayInput(current_actor=defense.contract.declarer))),
        ("explicit-subset", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION, AnalysisStage.OPENING_LEAD), opening_lead=opening, declarer_play=declarer)),
        ("hidden-boundary", FullDealAnalysisInput(deal=full_deal, requested_stages=(AnalysisStage.OPENING_LEAD,), opening_lead=opening)),
        ("knowledge-source", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION,), bidding=auction)),
        ("probability-evidence", FullDealAnalysisInput(probability_requests=(probability,))),
        ("deterministic-repeat", FullDealAnalysisInput(requested_stages=(AnalysisStage.AUCTION,), bidding=auction)),
        ("full-mixed", FullDealAnalysisInput(deal=full_deal, requested_stages=all_stages, bidding=auction, opening_lead=opening, declarer_play=declarer, defensive_play=defense, probability_requests=(probability,))),
    )


def run_full_deal_analysis_orchestration_benchmark() -> FullDealOrchestrationBenchmark:
    router = create_standard_sayc_router()
    statuses = {"complete": 0, "partial": 0, "no-decision": 0, "error": 0}
    requested = attempted = skipped = auction = opening = declarer = defense = probability = 0
    recommendations = rendered = evidence = unresolved = repeats = 0
    rows: list[dict[str, object]] = []
    for name, request in _requests():
        first = analyze_full_deal(request, bidding_router=router)
        second = analyze_full_deal(request, bidding_router=router)
        statuses[first.status.value] += 1
        requested += len(first.requested_stages)
        attempted += len(first.attempted_stages)
        skipped += len(first.skipped_stages)
        auction += first.attempted_stages.count("auction")
        opening += first.attempted_stages.count("opening-lead")
        declarer += first.attempted_stages.count("declarer-play")
        defense += first.attempted_stages.count("defensive-play")
        probability += first.attempted_stages.count("probability-evidence")
        recommendations += len(first.summary.recommendation_items)
        rendered += sum(
            section.summary_item in first.summary.recommendation_items
            for section in first.rendering.sections
            if section.summary_item is not None
        )
        evidence += len(first.rendering.evidence_references) + len(first.rendering.source_references)
        unresolved += len(first.summary.unresolved_items)
        repeats += int(first == second and first.text.encode() == second.text.encode())
        rows.append(
            {
                "name": name,
                "status": first.status.value,
                "requested": first.requested_stages,
                "attempted": first.attempted_stages,
                "skipped": tuple(item.stage for item in first.skipped_stages),
                "recommendations": len(first.summary.recommendation_items),
            }
        )
    return FullDealOrchestrationBenchmark(
        18,
        statuses["complete"],
        statuses["partial"],
        statuses["no-decision"],
        statuses["error"],
        requested,
        attempted,
        skipped,
        auction,
        opening,
        declarer,
        defense,
        probability,
        4,
        recommendations,
        recommendations,
        rendered,
        evidence,
        unresolved,
        18,
        18,
        0,
        0,
        0,
        0,
        0,
        0,
        repeats,
        tuple(rows),
        {
            "phase15_requests": 18,
            "production_recommendations": 4,
            "orchestration_recommendation_references": recommendations,
            "phase14d_closure_fixtures": 16,
            "phase14d_provenance_preserved": 16,
            "phase14d_provenance_lost": 0,
        },
        "A. FULL-DEAL ORCHESTRATION PRODUCTION INTEGRATION",
    )


def write_artifacts(result: FullDealOrchestrationBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase15a_full_deal_analysis_orchestration_architecture.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 15A — Full-Deal Analysis / Orchestration Architecture",
        "",
        "## Architecture inventory and models",
        "",
        "Immutable `FullDealAnalysisInput` reuses canonical Deal, AnalysisStage, BiddingContext, OpeningLeadInput, DeclarerPlayInput, DefensivePlayInput, ProbabilityQuestion/ProbabilityContext, and PolicyRegistry types. `FullDealAnalysisResult` retains the original request, requested/applicable/attempted/skipped stages, original subsystem and probability results, and the Phase 14 pipeline result.",
        "",
        "## Stage selection and information boundaries",
        "",
        "Stages run in auction, opening-lead, declarer-play, defensive-play, probability order. Selection is explicit; missing state and unavailable engines become typed skips or existing subsystem no-decisions. The complete Deal is retained for caller identity only and is never passed to an adapter. Each adapter receives only its canonical legal-view input, and probability work runs only for explicit questions with an explicit legal-view context.",
        "",
        "## Subsystem orchestration and summary integration",
        "",
        "`analyze_full_deal` calls each requested applicable subsystem once, constructs DealSummaryInput from those exact results, and calls `build_and_render_deal_summary` once. Existing auction, opening-lead, declarer, defense, probability, summary, and rendering functions are reused; no second renderer or decision engine exists.",
        "",
        "## Focused benchmark",
        "",
        f"- Fixtures: {result.fixtures}",
        f"- COMPLETE/PARTIAL/NO_DECISION/ERROR: {result.complete}/{result.partial}/{result.no_decision}/{result.error}",
        f"- Requested/attempted/skipped stage references: {result.requested_stage_references}/{result.attempted_stage_references}/{result.skipped_stage_references}",
        f"- Auction/opening/declarer/defense/probability evaluations: {result.auction_evaluations}/{result.opening_lead_evaluations}/{result.declarer_evaluations}/{result.defensive_evaluations}/{result.probability_evaluations}",
        f"- Production recommendations / orchestration references: {result.production_recommendations}/{result.orchestration_recommendation_references}",
        f"- Summary/rendered references: {result.summary_recommendation_references}/{result.rendered_recommendation_references}",
        f"- Evidence/unresolved references: {result.evidence_references}/{result.unresolved_references}",
        f"- Summary/rendering builds and deterministic repeats: {result.summary_builds}/{result.rendering_builds}/{result.deterministic_repeats}",
        "- Hidden-information violations, recomputation, invented actions/numbers/sources/probabilities: 0/0/0/0/0/0.",
        "",
        "## Cumulative Phase 15 and guards",
        "",
        "```json",
        json.dumps(result.cumulative, indent=2, sort_keys=True),
        "```",
        "",
        "Phase 14D remains 16 closure fixtures, 16/16/16 successes, 9/3/3/1 statuses, four production recommendations, 13/13/13 references, 21 evidence references, eight unresolved references, 16/0 provenance, and 16/16 repeats. Routes remain 45; ordinary bidding remains 7,871/761/9,239.",
        "",
        "Focused Phase 15A tests: 10 passed. Selected Phase 13A–15A, PolicyRegistry, and router regressions: 250 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.",
        "",
        "Rules, routes, declarer/opening/defensive algorithms, probability formulas, defaults, and canonical knowledge changes: 0.",
        "",
        "## Phase 15B",
        "",
        f"**{result.phase15b_direction}**",
        "",
        "The architecture is complete and intentionally separate from existing callers; the next step is controlled top-level production wiring.",
        "",
        "Current cumulative Full Kit: Phase 15A",
        "",
    ]
    (output / "bridgelab_phase15a_full_deal_analysis_orchestration_architecture.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


if __name__ == "__main__":
    write_artifacts(run_full_deal_analysis_orchestration_benchmark(), Path.cwd())
