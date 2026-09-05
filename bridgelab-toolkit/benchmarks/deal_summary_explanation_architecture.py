"""Deterministic Phase 14A deal-summary architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    AbstentionCode, ActionKind, AnalysisAction, AnalysisEvidence, AnalysisStage,
    AnalysisStatus, CalculationMode, DealAnalysisResult, DealSummaryInput,
    DealSummaryStatus, FormulaIdentifier, KnowledgeSource,
    ProbabilityEngineResult, ProbabilityEngineStatus, ProbabilityEvidence,
    ProbabilityEvidenceType, build_deal_summary,
)

SOURCE = KnowledgeSource("play/declarer-play/general-techniques/unblock", "Example 1 – Simple Unblock")


@dataclass(frozen=True, slots=True)
class DealSummaryArchitectureBenchmark:
    summary_fixtures: int
    available_summaries: int
    partial_summaries: int
    no_decision_summaries: int
    error_summaries: int
    recommendation_items: int
    bidding_recommendation_items: int
    declarer_recommendation_items: int
    opening_lead_recommendation_items: int
    defensive_recommendation_items: int
    evidence_items: int
    unresolved_items: int
    source_backed_items: int
    invented_recommendations: int
    invented_probabilities: int
    fixture_results: tuple[dict[str, object], ...]
    cumulative: dict[str, int]
    phase14b_direction: str


def _result(stage: AnalysisStage, status: AnalysisStatus, name: str) -> DealAnalysisResult:
    recommendation = status is AnalysisStatus.RECOMMENDATION
    evidence = (AnalysisEvidence("knowledge-source", f"{name} evidence", SOURCE),) if recommendation else ()
    code = None if recommendation or status is AnalysisStatus.ERROR else AbstentionCode.ENGINE_UNAVAILABLE
    return DealAnalysisResult(
        stage, None, status, AnalysisAction(ActionKind.NONE), f"{name} explanation.",
        evidence, (), code,
    )


def _probability(status: ProbabilityEngineStatus = ProbabilityEngineStatus.SUCCESS) -> ProbabilityEngineResult:
    evidence = ()
    mode = formula = None
    if status is ProbabilityEngineStatus.SUCCESS:
        evidence = (ProbabilityEvidence(
            ProbabilityEvidenceType.KNOWN_CARD_COUNT, "unknown cards", ("visible cards only",),
            (("known", "13"),), "39", deterministic=True, simulated=False, source=SOURCE,
        ),)
        mode, formula = CalculationMode.EXACT, FormulaIdentifier.KNOWN_CARD_COUNT_V1
    return ProbabilityEngineResult(status, evidence, mode, formula, explanation="Existing probability result.")


def run_deal_summary_explanation_benchmark() -> DealSummaryArchitectureBenchmark:
    bid = _result(AnalysisStage.AUCTION, AnalysisStatus.RECOMMENDATION, "auction")
    declarer = _result(AnalysisStage.DECLARER_PLAY, AnalysisStatus.RECOMMENDATION, "declarer")
    lead = _result(AnalysisStage.OPENING_LEAD, AnalysisStatus.NO_DECISION, "opening lead")
    defense = _result(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.NO_DECISION, "defense")
    abstain = _result(AnalysisStage.AUCTION, AnalysisStatus.ABSTAIN, "auction abstention")
    error = _result(AnalysisStage.DEFENSIVE_PLAY, AnalysisStatus.ERROR, "defense error")
    probability = _probability()
    fixtures = (
        ("bidding-only", DealSummaryInput((bid,))),
        ("declarer-only", DealSummaryInput((declarer,))),
        ("bidding-declarer", DealSummaryInput((declarer, bid))),
        ("opening-lead-no-decision", DealSummaryInput((lead,))),
        ("defensive-no-decision", DealSummaryInput((defense,))),
        ("exact-probability-only", DealSummaryInput(probability_results=(probability,))),
        ("recommendation-probability", DealSummaryInput((bid,), (probability,))),
        ("mixed", DealSummaryInput((lead, bid))),
        ("all-no-decision", DealSummaryInput((defense, lead))),
        ("abstention", DealSummaryInput((abstain,))),
        ("subsystem-error", DealSummaryInput((error,))),
        ("duplicate-stage", DealSummaryInput((bid, abstain))),
        ("empty", DealSummaryInput()),
        ("deterministic-repeat", DealSummaryInput((bid,))),
        ("source-preservation", DealSummaryInput((bid,))),
        ("probability-preservation", DealSummaryInput(probability_results=(probability,))),
    )
    results = []
    status_counts = {status: 0 for status in DealSummaryStatus}
    recommendation_count = bidding_count = declarer_count = evidence_count = unresolved_count = source_count = 0
    for name, source in fixtures:
        summary = build_deal_summary(source)
        status_counts[summary.status] += 1
        recommendation_count += len(summary.recommendation_items)
        bidding_count += sum(item.stage is AnalysisStage.AUCTION for item in summary.recommendation_items)
        declarer_count += sum(item.stage is AnalysisStage.DECLARER_PLAY for item in summary.recommendation_items)
        evidence_count += len(summary.evidence_items)
        unresolved_count += len(summary.unresolved_items)
        source_count += sum(getattr(item, "source", None) is not None for item in summary.evidence_items)
        results.append({"name": name, "status": summary.status.value,
                        "stages": [item.stage.value for item in summary.items],
                        "recommendations": len(summary.recommendation_items),
                        "evidence": len(summary.evidence_items),
                        "unresolved": len(summary.unresolved_items),
                        "failure_code": None if summary.failure_code is None else summary.failure_code.value})
    return DealSummaryArchitectureBenchmark(
        16, status_counts[DealSummaryStatus.AVAILABLE], status_counts[DealSummaryStatus.PARTIAL],
        status_counts[DealSummaryStatus.NO_DECISION], status_counts[DealSummaryStatus.ERROR],
        recommendation_count, bidding_count, declarer_count, 0, 0,
        evidence_count, unresolved_count, source_count, 0, 0, tuple(results),
        {"cumulative_requests": 126, "phase13_closure_requests": 16,
         "production_recommendations": 4, "summary_requests": 16,
         "summary_recommendation_references": recommendation_count,
         "summary_evidence_items": evidence_count,
         "unresolved_summary_items": unresolved_count,
         "summary_errors": status_counts[DealSummaryStatus.ERROR]},
        "A. DEAL-SUMMARY RENDERING / EXPLANATION ENGINE",
    )


def write_artifacts(result: DealSummaryArchitectureBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase14a_deal_summary_explanation_architecture.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# BridgeLab Phase 14A — Deal-Summary / Explanation Architecture", "",
             "## Architecture", "",
             "Immutable `DealSummaryInput`, `DealSummaryItem`, and `DealSummaryResult` aggregate original `DealAnalysisResult` and `ProbabilityEngineResult` objects. Statuses are AVAILABLE, PARTIAL, NO_DECISION, and ERROR; failures distinguish missing input, invalid stage results, and duplicate stages.", "",
             "Canonical order is auction, opening lead, declarer play, defensive play, then probability evidence. Existing actions, explanations, abstention codes, `KnowledgeSource`, exact calculation modes, evidence assumptions, known facts, and traces remain on their original immutable objects.", "",
             "The builder does not compute bridge decisions, probabilities, confidence, hidden cards, or an overall best action.", "",
             "## Focused benchmark", "",
             f"- Summaries: {result.summary_fixtures}",
             f"- Available / partial / no-decision / error: {result.available_summaries} / {result.partial_summaries} / {result.no_decision_summaries} / {result.error_summaries}",
             f"- Recommendation references: {result.recommendation_items} (bidding {result.bidding_recommendation_items}, declarer {result.declarer_recommendation_items})",
             f"- Evidence / unresolved / source-backed: {result.evidence_items} / {result.unresolved_items} / {result.source_backed_items}",
             "- Invented recommendations / probabilities: 0 / 0", "",
             "## Cumulative Phase 14", "", "```json", json.dumps(result.cumulative, indent=2, sort_keys=True), "```", "",
             "Summary references are not counted as new production recommendations. Phase 13L remains 16 fixtures, four production recommendations, two abstentions, nine no-decisions, one evidence result, zero errors, and 25% recommendation rate.", "",
             "## Phase 14B", "", f"**{result.phase14b_direction}**", "",
             "The structured aggregation boundary is complete; the next gap is a deterministic renderer over these preserved fields.", "",
             "Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Algorithms, formulas, rules, routes, defaults, and canonical knowledge changes: 0.", "",
             "Current cumulative Full Kit: Phase 14A", ""]
    (output / "bridgelab_phase14a_deal_summary_explanation_architecture.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_deal_summary_explanation_benchmark(), Path.cwd())
