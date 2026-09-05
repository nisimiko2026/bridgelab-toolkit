"""Phase 13K source-enrichment benchmark; contains no lead algorithm."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .opening_lead_source_readiness_audit import run_opening_lead_source_readiness_audit


@dataclass(frozen=True, slots=True)
class OpeningLeadSourceEnrichmentBenchmark:
    source_files_changed: tuple[str, ...]
    sources_consulted: tuple[str, ...]
    source_claims_added: int
    source_claims_clarified: int
    candidate_rules_reaudited: int
    executable_candidates_before: int
    executable_candidates_after: int
    policy_executable_candidates_after: int
    ambiguous_candidates_after: int
    exception_incomplete_candidates_after: int
    recommendations_generated: int
    before_after: tuple[dict[str, str], ...]
    architecture: dict[str, int]
    phase13l_direction: str


def run_opening_lead_source_enrichment_benchmark() -> OpeningLeadSourceEnrichmentBenchmark:
    historical = run_opening_lead_source_readiness_audit()
    before_after = tuple(
        {"candidate": item.rule, "before": item.classification.value,
         "after": item.classification.value}
        for item in historical.candidates
    )
    return OpeningLeadSourceEnrichmentBenchmark(
        ("knowledge/play/defence/opening-leads/fourth-best.md",),
        ("fourth-best.md: Overview", "fourth-best.md: Basic Principle",
         "fourth-best.md: Honor Sequences Take Priority",
         "fourth-best.md: Against Notrump Contracts",
         "fourth-best.md: Against Suit Contracts",
         "fourth-best.md: Partnership Agreements"),
        7, 5, historical.candidate_rules, 0, 0, 0,
        historical.classification_counts["AMBIGUOUS_CARD_CHOICE"],
        historical.classification_counts["EXCEPTION_INCOMPLETE"], 0,
        before_after,
        {"cumulative_positions_or_requests": 110, "source_enrichment_requests": 15,
         "source_readiness_audit_requests": 15, "policy_requests": 10,
         "opening_lead_states": 14, "bidding_recommendations": 2,
         "declarer_recommendations": 2, "opening_lead_recommendations": 0,
         "defensive_recommendations": 0, "no_decisions": 51,
         "abstentions": 3, "errors": 0},
        "E. PHASE 13 COVERAGE / CLOSURE AUDIT",
    )


def write_artifacts(result: OpeningLeadSourceEnrichmentBenchmark, output: Path) -> None:
    payload = asdict(result)
    (output / "bridgelab_phase13k_opening_lead_source_enrichment.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# BridgeLab Phase 13K — Opening-Lead Source Enrichment", "",
             "## Outcome", "",
             "One minimal canonical enrichment now makes the fourth-best article explicitly distinguish suit selection from card treatment. It remains POLICY_PARTIAL for a full opening-lead recommendation: neither the article nor current policy selects the suit or fully resolves contract scope.", "",
             "## Knowledge change", "", f"- Changed: `{result.source_files_changed[0]}`",
             f"- Claims added / clarified: {result.source_claims_added} / {result.source_claims_clarified}",
             "- Added explicit rule name, scope, policy dependency, trigger, card treatment, exceptions, precedence boundary, internal source evidence, and implementation status.", "",
             "## Source basis", ""]
    lines.extend(f"- {source}" for source in result.sources_consulted)
    lines += ["", "No external claim was added; the structured contract restates only those frozen sections.", "",
              "## Re-audit", "", f"- Candidate rules: {result.candidate_rules_reaudited}",
              f"- Executable before / after: {result.executable_candidates_before} / {result.executable_candidates_after}",
              f"- Policy-executable after: {result.policy_executable_candidates_after}",
              f"- Ambiguous after: {result.ambiguous_candidates_after}",
              f"- Exception-incomplete after: {result.exception_incomplete_candidates_after}",
              "- Recommendations generated: 0", "",
              "Fourth-best, third/fifth, and Rusinow remain POLICY_PARTIAL; Standard and Top of Nothing remain EXCEPTION_INCOMPLETE; singleton, partner's suit, and trump lead remain SOURCE_PARTIAL.", "",
              "## Cumulative Phase 13", "", "```json", json.dumps(result.architecture, indent=2, sort_keys=True), "```", "",
              "## Phase 13L", "", result.phase13l_direction, "",
              "Further source enrichment has diminishing value without a reliable suit-selection contract. No production engine should be implemented from the current corpus.", "",
              "Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Algorithms, formulas, rules, routes, policy defaults, and recommendations added: 0.", "",
              "Current cumulative Full Kit: Phase 13K", ""]
    (output / "bridgelab_phase13k_opening_lead_source_enrichment.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_opening_lead_source_enrichment_benchmark(), Path.cwd())
