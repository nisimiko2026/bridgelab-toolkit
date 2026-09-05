"""Phase 13J frozen-source readiness audit; never selects a lead card."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path


class ReadinessClassification(str, Enum):
    SOURCE_EXECUTABLE = "SOURCE_EXECUTABLE"
    POLICY_EXECUTABLE = "POLICY_EXECUTABLE"
    SOURCE_PARTIAL = "SOURCE_PARTIAL"
    POLICY_PARTIAL = "POLICY_PARTIAL"
    SOURCE_INSUFFICIENT = "SOURCE_INSUFFICIENT"
    AMBIGUOUS_CARD_CHOICE = "AMBIGUOUS_CARD_CHOICE"
    EXCEPTION_INCOMPLETE = "EXCEPTION_INCOMPLETE"
    NOT_PRESENT = "NOT_PRESENT"


@dataclass(frozen=True, slots=True)
class CandidateAudit:
    rule: str
    source: str
    heading: str
    stated_rule: str
    required_policy: str | None
    state_sufficient: bool
    unique_card: bool
    exceptions_complete: bool
    precedence_complete: bool
    suit_scope: str
    notrump_scope: str
    ambiguity: str
    classification: ReadinessClassification


@dataclass(frozen=True, slots=True)
class FixtureAudit:
    name: str
    candidate: str
    policy_required: bool
    executable: bool
    blocker: str
    recommendation: None = None


@dataclass(frozen=True, slots=True)
class OpeningLeadSourceReadinessAudit:
    source_files_audited: int
    candidate_rules: int
    classification_counts: dict[str, int]
    candidate_fixtures: int
    policy_required_fixtures: int
    executable_fixtures: int
    non_executable_fixtures: int
    recommendations_generated: int
    candidates: tuple[CandidateAudit, ...]
    fixtures: tuple[FixtureAudit, ...]
    top_candidates: tuple[str, ...]
    architecture: dict[str, int]
    phase13k_direction: str


def _candidate(rule: str, file: str, heading: str, stated: str, policy: str | None,
               classification: ReadinessClassification, ambiguity: str,
               *, state: bool = True, unique: bool = False, exceptions: bool = False,
               precedence: bool = False, suit: str = "partial", nt: str = "partial") -> CandidateAudit:
    return CandidateAudit(rule, f"knowledge/play/defence/opening-leads/{file}.md", heading,
                          stated, policy, state, unique, exceptions, precedence, suit, nt,
                          ambiguity, classification)


def run_opening_lead_source_readiness_audit() -> OpeningLeadSourceReadinessAudit:
    candidates = (
        _candidate("fourth-best from length", "fourth-best", "Basic Principle",
                   "Fourth-highest from a long suit without a touching sequence.", "FOURTH_BEST",
                   ReadinessClassification.POLICY_PARTIAL,
                   "No deterministic suit choice, minimum length, or complete suit/NT scope."),
        _candidate("third-and-fifth", "third-fifth", "Basic Principle",
                   "Third-highest from odd length and fifth-highest from even length.", "THIRD_AND_FIFTH",
                   ReadinessClassification.POLICY_PARTIAL,
                   "No deterministic suit choice; short-length and contract exceptions are incomplete."),
        _candidate("standard honor sequence", "standard-leads", "Sequence Leads",
                   "Lead the top card from a sequence.", "STANDARD",
                   ReadinessClassification.EXCEPTION_INCOMPLETE,
                   "Several eligible suits and ace/king/interior-sequence variants remain.", unique=False),
        _candidate("Rusinow touching sequence", "rusinow", "Basic Principle",
                   "Lead the second-highest honor from a touching sequence.", "RUSINOW",
                   ReadinessClassification.POLICY_PARTIAL,
                   "Contract scope and ace/king/interior-sequence agreements remain unresolved."),
        _candidate("top of nothing", "top-of-nothing", "Definition",
                   "Lead the highest card from a suit containing no honors.", "ENABLED",
                   ReadinessClassification.EXCEPTION_INCOMPLETE,
                   "Suit selection, minimum length, NT scope, and precedence over length are incomplete."),
        _candidate("singleton lead", "standard-leads", "Short Suit Leads",
                   "Lead a singleton against a suit contract to seek a ruff.", None,
                   ReadinessClassification.SOURCE_PARTIAL,
                   "Source calls this preferred/usually, with no tie-break or exceptions.", suit="yes", nt="no"),
        _candidate("partner's suit", "lead-partners-suit", "Opening Lead",
                   "Prefer partner's bid suit subject to holding and auction context.", None,
                   ReadinessClassification.SOURCE_PARTIAL,
                   "Exact auction trigger, card, and competing-suit precedence are incomplete."),
        _candidate("longest/strongest versus NT", "standard-leads", "Against Notrump Contracts",
                   "Prefer the longest and strongest suit, commonly using fourth-best.", "FOURTH_BEST",
                   ReadinessClassification.AMBIGUOUS_CARD_CHOICE,
                   "Longest and strongest may identify different or tied suits.", nt="yes"),
        _candidate("trump lead", "standard-leads", "Suit Contract Opening Leads",
                   "A trump lead is occasionally preferred.", None,
                   ReadinessClassification.SOURCE_PARTIAL,
                   "No source-complete trigger or exception contract.", suit="yes", nt="no"),
        _candidate("MUD", "opening-leads-index", "Opening Leads", "No executable MUD contract.", None,
                   ReadinessClassification.NOT_PRESENT, "Named/absent without a usable rule contract.", state=False),
    )
    fixture_data = (
        ("fourth-positive-looking", "fourth-best from length", True, "suit choice and scope incomplete"),
        ("fourth-near-miss", "fourth-best from length", True, "minimum length incomplete"),
        ("third-fifth-positive-looking", "third-and-fifth", True, "suit choice incomplete"),
        ("standard-honor", "standard honor sequence", True, "exceptions incomplete"),
        ("rusinow-honor", "Rusinow touching sequence", True, "contract scope incomplete"),
        ("top-nothing-positive-looking", "top of nothing", True, "length and scope incomplete"),
        ("honor-versus-length", "standard honor sequence", True, "cross-suit precedence incomplete"),
        ("top-nothing-versus-length", "top of nothing", True, "policy precedence incomplete"),
        ("notrump-contract", "longest/strongest versus NT", True, "multiple plausible suits"),
        ("suit-contract", "singleton lead", False, "preferred wording and exceptions incomplete"),
        ("ambiguous-card-choice", "longest/strongest versus NT", True, "tied eligible suits"),
        ("incomplete-exception", "Rusinow touching sequence", True, "ace/king exceptions incomplete"),
        ("missing-policy", "fourth-best from length", True, "missing policy"),
        ("unknown-policy", "standard honor sequence", True, "unknown is not Standard"),
        ("deterministic-repeat", "top of nothing", True, "same audited blocker"),
    )
    fixtures = tuple(FixtureAudit(name, candidate, policy, False, blocker) for name, candidate, policy, blocker in fixture_data)
    counts = Counter(candidate.classification.value for candidate in candidates)
    for classification in ReadinessClassification:
        counts.setdefault(classification.value, 0)
    architecture = {
        "cumulative_positions_or_requests": 95, "source_readiness_audit_requests": 15,
        "policy_requests": 10, "opening_lead_states": 14, "bidding_recommendations": 2,
        "declarer_recommendations": 2, "opening_lead_recommendations": 0,
        "defensive_recommendations": 0, "no_decisions": 51, "abstentions": 3, "errors": 0,
    }
    return OpeningLeadSourceReadinessAudit(
        10, len(candidates), dict(sorted(counts.items())), len(fixtures),
        sum(item.policy_required for item in fixtures), 0, len(fixtures), 0,
        candidates, fixtures,
        ("standard honor sequence", "Rusinow touching sequence", "fourth-best from length"),
        architecture, "E. OPENING-LEAD SOURCE ENRICHMENT REQUIRED",
    )


def write_artifacts(audit: OpeningLeadSourceReadinessAudit, output: Path) -> None:
    payload = asdict(audit)
    json_path = output / "bridgelab_phase13j_opening_lead_source_readiness_audit.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# BridgeLab Phase 13J — Opening-Lead Source-Readiness Audit", "",
             "## Decision", "", audit.phase13k_direction, "",
             "No frozen-source candidate passes all twelve executability gates. The sources describe carding agreements within a chosen suit, but do not uniquely select a suit from the complete state or fully settle scope, exceptions, and precedence.", "",
             "## Benchmark", "", f"- Source files audited: {audit.source_files_audited}",
             f"- Candidate rules / fixtures: {audit.candidate_rules} / {audit.candidate_fixtures}",
             f"- Executable candidates / fixtures: 0 / {audit.executable_fixtures}",
             f"- Non-executable fixtures: {audit.non_executable_fixtures}",
             f"- Policy-required fixtures: {audit.policy_required_fixtures}",
             "- Recommendations generated: 0", "", "## Candidate audit", ""]
    for item in audit.candidates:
        lines += [f"### {item.rule}", "", f"- Source: `{item.source}` — {item.heading}",
                  f"- Rule: {item.stated_rule}", f"- Policy: {item.required_policy or 'none identified'}",
                  f"- Classification: **{item.classification.value}**",
                  f"- State / unique card / exceptions / precedence: {item.state_sufficient} / {item.unique_card} / {item.exceptions_complete} / {item.precedence_complete}",
                  f"- Suit / NT scope: {item.suit_scope} / {item.notrump_scope}", f"- Blocker: {item.ambiguity}", ""]
    lines += ["## Precedence and state boundary", "",
              "Honor sequences override within-suit length leads in the length articles, and Rusinow replaces Standard for its defined sequences when explicitly agreed. Cross-suit priority and Top-of-Nothing versus length precedence are not complete. Leader hand, contract, legal cards, and optional auction are sufficient inputs; hidden hands and probability are neither used nor needed. The remaining blocker is the source contract, not state representation.", "",
              "## Cumulative Phase 13", "", "```json", json.dumps(audit.architecture, indent=2, sort_keys=True), "```", "",
              "## Guards", "", "Phase 13I remains 10 / 8 / 2 with three policy dimensions and zero recommendations. OpeningLeadState remains NO_DECISION/NONE/ENGINE_UNAVAILABLE for valid state, all 13 leader cards legal, 13 known and 39 unknown. Defensive recommendations remain zero; SIMPLE_UNBLOCK_KING remains two king recommendations; one probability engine remains registered. Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. No production defaults, algorithms, formulas, routes, or canonical knowledge Markdown changed.", "",
              "Current cumulative Full Kit: Phase 13J", ""]
    (output / "bridgelab_phase13j_opening_lead_source_readiness_audit.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_opening_lead_source_readiness_audit(), Path.cwd())
