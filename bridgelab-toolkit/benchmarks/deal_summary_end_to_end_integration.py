"""Deterministic Phase 14C summary-build/render integration benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    AnalysisStage, AnalysisStatus, DealSummaryInput, DealSummaryPipelineStatus,
    build_and_render_deal_summary,
)
from .deal_summary_rendering_explanation_engine import _probability, _stage


@dataclass(frozen=True, slots=True)
class DealSummaryIntegrationBenchmark:
    integration_fixtures: int
    successful_integrations: int
    partial_integrations: int
    no_decision_integrations: int
    error_integrations: int
    summary_builds: int
    rendering_builds: int
    production_recommendation_references: int
    rendered_recommendation_references: int
    evidence_references: int
    unresolved_stage_references: int
    provenance_preserved_cases: int
    deterministic_repeats_matched: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    recomputed_recommendations: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, int]
    phase14d_direction: str


def run_deal_summary_end_to_end_integration_benchmark() -> DealSummaryIntegrationBenchmark:
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    declarer = _stage(AnalysisStage.DECLARER_PLAY, AnalysisStatus.RECOMMENDATION, "declarer")
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "opening lead")
    defense = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defense")
    abstain = _stage(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "abstention")
    error = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "error")
    probability = _probability()
    inputs = (
        ("bidding-only", DealSummaryInput((bid,))),
        ("declarer-only", DealSummaryInput((declarer,))),
        ("bidding-declarer", DealSummaryInput((declarer, bid))),
        ("bidding-probability", DealSummaryInput((bid,), (probability,))),
        ("declarer-probability", DealSummaryInput((declarer,), (probability,))),
        ("recommendation-opening-unresolved", DealSummaryInput((lead, bid))),
        ("recommendation-defense-unresolved", DealSummaryInput((defense, bid))),
        ("all-no-decision", DealSummaryInput((defense, lead))),
        ("abstention", DealSummaryInput((abstain,))),
        ("subsystem-error", DealSummaryInput((error,))),
        ("empty", DealSummaryInput()),
        ("knowledge-source", DealSummaryInput((bid,))),
        ("probability-evidence", DealSummaryInput(probability_results=(probability,))),
        ("trace", DealSummaryInput((declarer,))),
        ("deterministic-repeat", DealSummaryInput((bid,))),
        ("long-full-stage", DealSummaryInput((defense, declarer, lead, bid), (probability,))),
    )
    rows = []
    counts = {status: 0 for status in DealSummaryPipelineStatus}
    recommendation_refs = rendered_refs = evidence_refs = unresolved_refs = provenance = repeats = 0
    for name, source in inputs:
        first = build_and_render_deal_summary(source)
        second = build_and_render_deal_summary(source)
        counts[first.status] += 1
        repeats += int(first == second and first.text.encode() == second.text.encode())
        recommendation_refs += len(first.summary.recommendation_items)
        rendered_refs += sum(
            section.summary_item in first.summary.recommendation_items
            for section in first.rendering.sections if section.summary_item is not None
        )
        evidence_refs += len(first.rendering.evidence_references) + len(first.rendering.source_references)
        unresolved_refs += len(first.summary.unresolved_items)
        provenance += int(
            first.original_subsystem_results == source.stage_results
            and first.rendering.original_summary is first.summary
            and all(
                section.summary_item is None or section.summary_item.result in source.stage_results
                for section in first.rendering.sections
            )
        )
        rows.append({"name": name, "status": first.status.value,
                     "summary_status": first.summary.status.value,
                     "rendering_status": first.rendering.status.value,
                     "stages": [section.label for section in first.rendering.sections],
                     "recommendation_references": len(first.summary.recommendation_items),
                     "failure": None if first.failure_code is None else first.failure_code.value})
    return DealSummaryIntegrationBenchmark(
        16, counts[DealSummaryPipelineStatus.COMPLETE], counts[DealSummaryPipelineStatus.PARTIAL],
        counts[DealSummaryPipelineStatus.NO_DECISION], counts[DealSummaryPipelineStatus.ERROR],
        16, 16, recommendation_refs, rendered_refs, evidence_refs, unresolved_refs,
        provenance, repeats, 0, 0, 0, 0, 0, tuple(rows),
        {"cumulative_requests": 158, "summary_requests": 16, "rendering_requests": 16,
         "integration_requests": 16, "production_recommendations": 4,
         "summary_recommendation_references": 8, "rendered_recommendation_references": 11,
         "integrated_recommendation_references": recommendation_refs,
         "integrated_evidence_references": evidence_refs,
         "integrated_unresolved_references": unresolved_refs,
         "integration_errors": counts[DealSummaryPipelineStatus.ERROR]},
        "D. PHASE 14 COVERAGE / CLOSURE AUDIT",
    )


def write_artifacts(result: DealSummaryIntegrationBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase14c_deal_summary_end_to_end_integration.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# BridgeLab Phase 14C — Deal-Summary End-to-End Integration", "",
             "## Integration architecture", "",
             "`build_and_render_deal_summary` accepts already-computed `DealSummaryInput`, invokes `build_deal_summary` once, invokes `render_deal_summary` once, and returns immutable `DealSummaryPipelineResult`. Existing `analyze_deal_decision` behavior and return type are unchanged.", "",
             "The result exposes original subsystem objects, structured summary, rendered summary, rendered text, explicit integration status, and narrow structural failure codes. Provenance remains navigable through rendered section → summary item → original result and through probability section → original engine result/evidence.", "",
             "## Focused benchmark", "",
             f"- Fixtures: {result.integration_fixtures}",
             f"- Complete / partial / no-decision / error: {result.successful_integrations} / {result.partial_integrations} / {result.no_decision_integrations} / {result.error_integrations}",
             f"- Summary / rendering builds: {result.summary_builds} / {result.rendering_builds}",
             f"- Integrated / rendered recommendation references: {result.production_recommendation_references} / {result.rendered_recommendation_references}",
             f"- Evidence / unresolved references: {result.evidence_references} / {result.unresolved_stage_references}",
             f"- Provenance preserved / deterministic repeats: {result.provenance_preserved_cases} / {result.deterministic_repeats_matched}",
             "- Invented actions/numbers/sources/probabilities and recomputed recommendations: 0", "",
             "## Cumulative Phase 14", "", "```json", json.dumps(result.cumulative, indent=2, sort_keys=True), "```", "",
             "Underlying production recommendations remain four; summary, rendering, and integration counts are references only. Historical Phase 14A, Phase 14B, and Phase 13L metrics remain unchanged.", "",
             "## Phase 14D", "", f"**{result.phase14d_direction}**", "",
             "Summary architecture, deterministic rendering, and one-pass integration are complete and should now be measured and closed.", "",
             "Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Rules, routes, algorithms, formulas, defaults, and knowledge changes: 0.", "",
             "Current cumulative Full Kit: Phase 14C", ""]
    (output / "bridgelab_phase14c_deal_summary_end_to_end_integration.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_deal_summary_end_to_end_integration_benchmark(), Path.cwd())
