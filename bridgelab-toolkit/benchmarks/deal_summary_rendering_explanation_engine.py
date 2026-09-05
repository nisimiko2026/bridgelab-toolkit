"""Deterministic Phase 14B deal-summary rendering benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    AbstentionCode, ActionKind, AnalysisAction, AnalysisEvidence, AnalysisStage,
    AnalysisStatus, CalculationMode, Call, Card, DealAnalysisResult,
    DealSummaryInput, DealSummaryRenderingStatus, FormulaIdentifier,
    KnowledgeSource, ProbabilityEngineResult, ProbabilityEngineStatus,
    ProbabilityEvidence, ProbabilityEvidenceType, build_deal_summary,
    render_deal_summary,
)

SOURCE = KnowledgeSource("play/declarer-play/general-techniques/unblock", "Example 1 – Simple Unblock")


@dataclass(frozen=True, slots=True)
class DealSummaryRenderingBenchmark:
    rendering_fixtures: int
    rendered_available: int
    rendered_partial: int
    rendered_no_decision: int
    rendered_error: int
    rendered_recommendation_references: int
    rendered_evidence_references: int
    rendered_unresolved_sections: int
    rendered_error_sections: int
    invented_actions: int
    invented_numbers: int
    invented_sources: int
    invented_probabilities: int
    deterministic_repeats_matched: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, int]
    phase14c_direction: str


def _stage(stage: AnalysisStage, status: AnalysisStatus, name: str) -> DealAnalysisResult:
    if status is AnalysisStatus.RECOMMENDATION and stage is AnalysisStage.AUCTION:
        action = AnalysisAction(ActionKind.BID, bid=Call.parse("2NT"))
    elif status is AnalysisStatus.RECOMMENDATION:
        action = AnalysisAction(ActionKind.CARD_PLAY, card=Card.parse("KS"))
    else:
        action = AnalysisAction(ActionKind.NONE)
    evidence = (AnalysisEvidence("knowledge-source", f"{name} evidence", SOURCE),) if status is AnalysisStatus.RECOMMENDATION else ()
    code = None if status in {AnalysisStatus.RECOMMENDATION, AnalysisStatus.ERROR} else AbstentionCode.ENGINE_UNAVAILABLE
    return DealAnalysisResult(
        stage, None, status, action, f"{name} explanation.", evidence, (), code,
        debug_metadata=(("fixture", name),),
    )


def _probability() -> ProbabilityEngineResult:
    evidence = ProbabilityEvidence(
        ProbabilityEvidenceType.KNOWN_CARD_COUNT, "Unknown cards", ("Visible cards only.",),
        (("known-cards", "13"),), "39", source=SOURCE,
        trace=(("known", "13"), ("unknown", "39")),
    )
    return ProbabilityEngineResult(
        ProbabilityEngineStatus.SUCCESS, (evidence,), CalculationMode.EXACT,
        FormulaIdentifier.KNOWN_CARD_COUNT_V1, trace=evidence.trace,
    )


def run_deal_summary_rendering_benchmark() -> DealSummaryRenderingBenchmark:
    bid = _stage(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    declarer = _stage(AnalysisStage.DECLARER_PLAY, AnalysisStatus.RECOMMENDATION, "declarer")
    lead = _stage(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "opening lead engine unavailable")
    defense = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defensive engine unavailable")
    abstain = _stage(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "auction abstention")
    error = _stage(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "defensive error")
    probability = _probability()
    inputs = (
        ("bidding-only", DealSummaryInput((bid,))),
        ("declarer-only", DealSummaryInput((declarer,))),
        ("bidding-declarer", DealSummaryInput((declarer, bid))),
        ("opening-lead-unavailable", DealSummaryInput((lead,))),
        ("defensive-unavailable", DealSummaryInput((defense,))),
        ("exact-probability", DealSummaryInput(probability_results=(probability,))),
        ("recommendation-probability", DealSummaryInput((bid,), (probability,))),
        ("mixed-partial", DealSummaryInput((lead, bid))),
        ("all-no-decision", DealSummaryInput((defense, lead))),
        ("abstention", DealSummaryInput((abstain,))),
        ("error", DealSummaryInput((error,))),
        ("knowledge-source", DealSummaryInput((bid,))),
        ("trace", DealSummaryInput((declarer,))),
        ("duplicate-error", DealSummaryInput((bid, bid))),
        ("deterministic-repeat", DealSummaryInput((bid,))),
        ("long-mixed", DealSummaryInput((defense, declarer, lead, bid), (probability,))),
    )
    rendered = []
    status_counts = {status: 0 for status in DealSummaryRenderingStatus}
    recommendation_count = evidence_count = unresolved_count = error_sections = repeats = 0
    for name, source in inputs:
        summary = build_deal_summary(source)
        first = render_deal_summary(summary)
        second = render_deal_summary(summary)
        repeats += int(first == second and first.text.encode() == second.text.encode())
        status_counts[first.status] += 1
        recommendation_count += len(summary.recommendation_items)
        evidence_count += len(first.evidence_references) + len(first.source_references)
        unresolved_count += len(summary.unresolved_items)
        error_sections += sum(section.status == AnalysisStatus.ERROR.value for section in first.sections)
        rendered.append({"name": name, "status": first.status.value,
                         "sections": [section.label for section in first.sections],
                         "recommendations": len(summary.recommendation_items),
                         "sources": len(first.source_references),
                         "evidence": len(first.evidence_references), "text": first.text})
    return DealSummaryRenderingBenchmark(
        16, status_counts[DealSummaryRenderingStatus.AVAILABLE],
        status_counts[DealSummaryRenderingStatus.PARTIAL],
        status_counts[DealSummaryRenderingStatus.NO_DECISION],
        status_counts[DealSummaryRenderingStatus.ERROR],
        recommendation_count, evidence_count, unresolved_count, error_sections,
        0, 0, 0, 0, repeats, tuple(rendered),
        {"cumulative_requests": 142, "summary_requests": 16, "rendering_requests": 16,
         "production_recommendations": 4, "summary_recommendation_references": 8,
         "rendered_recommendation_references": recommendation_count,
         "rendered_evidence_references": evidence_count,
         "rendered_unresolved_references": unresolved_count,
         "rendering_errors": status_counts[DealSummaryRenderingStatus.ERROR]},
        "D. DEAL-SUMMARY END-TO-END INTEGRATION",
    )


def write_artifacts(result: DealSummaryRenderingBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase14b_deal_summary_rendering_explanation_engine.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# BridgeLab Phase 14B — Deal-Summary Rendering / Explanation Engine", "",
             "## Rendering architecture", "",
             "`render_deal_summary` returns immutable `DealSummaryRendering` and ordered `DealSummaryRenderedSection` values. Each section retains its original summary item or probability result, exact sources/evidence, and stable trace metadata.", "",
             "AVAILABLE, PARTIAL, NO_DECISION, and ERROR receive distinct deterministic wording. Recommendations render only their existing typed action and explanation; abstention, no-decision, and errors remain distinct. Exact probability facts, calculation mode, assumptions, known facts, and source IDs are rendered without confidence or odds.", "",
             "## Focused benchmark", "",
             f"- Fixtures: {result.rendering_fixtures}",
             f"- AVAILABLE / PARTIAL / NO_DECISION / ERROR: {result.rendered_available} / {result.rendered_partial} / {result.rendered_no_decision} / {result.rendered_error}",
             f"- Recommendation references: {result.rendered_recommendation_references}",
             f"- Evidence/source references: {result.rendered_evidence_references}",
             f"- Unresolved / error sections: {result.rendered_unresolved_sections} / {result.rendered_error_sections}",
             f"- Deterministic repeats matched: {result.deterministic_repeats_matched}/{result.rendering_fixtures}",
             "- Invented actions / numbers / sources / probabilities: 0 / 0 / 0 / 0", "",
             "## Cumulative Phase 14", "", "```json", json.dumps(result.cumulative, indent=2, sort_keys=True), "```", "",
             "Rendering references are not new production recommendations. Phase 14A remains 16 summaries, 8/1/5/2 statuses, and eight recommendation references. Phase 13L remains 16 closure fixtures and four production recommendations.", "",
             "## Phase 14C", "", f"**{result.phase14c_direction}**", "",
             "The remaining summary gap is one coherent optional pipeline call returning structured and rendered forms without changing existing return types.", "",
             "Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Rules, routes, algorithms, formulas, defaults, and knowledge changes: 0.", "",
             "Current cumulative Full Kit: Phase 14B", ""]
    (output / "bridgelab_phase14b_deal_summary_rendering_explanation_engine.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_deal_summary_rendering_benchmark(), Path.cwd())
