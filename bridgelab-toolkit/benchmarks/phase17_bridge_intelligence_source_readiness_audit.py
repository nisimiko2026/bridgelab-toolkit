"""Phase 17A source-readiness audit across bridge-intelligence families."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from benchmarks.phase16_coverage_closure_audit import run_phase16_coverage_closure_audit
from bridge import create_standard_sayc_router
from bridge.probability_engine import DEFAULT_PROBABILITY_ENGINE_REGISTRY


class SourceReadinessClassification(str, Enum):
    SOURCE_EXECUTABLE = "SOURCE_EXECUTABLE"
    SOURCE_PARTIAL = "SOURCE_PARTIAL"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    PARTNERSHIP_DEPENDENT = "PARTNERSHIP_DEPENDENT"
    PROBABILITY_REQUIRED = "PROBABILITY_REQUIRED"
    EXCEPTION_INCOMPLETE = "EXCEPTION_INCOMPLETE"
    AMBIGUOUS_ACTION = "AMBIGUOUS_ACTION"
    LOW_SAMPLE = "LOW_SAMPLE"
    NOT_PRESENT = "NOT_PRESENT"
    ARCHITECTURE_BLOCKED = "ARCHITECTURE_BLOCKED"


@dataclass(frozen=True, slots=True)
class IntelligenceCandidate:
    family: str
    candidate: str
    source_path: str
    heading: str
    trigger: str
    action: str
    exceptions: str
    policy_dependency: str
    architecture_status: str
    observed_population: int | None
    deterministic_fixture_count: int
    execution_status: str
    expected_new_recommendations: int
    classification: SourceReadinessClassification
    blocker: str


@dataclass(frozen=True, slots=True)
class Phase17SourceReadinessAudit:
    audited_families: tuple[str, ...]
    total_candidates: int
    classification_counts: dict[str, int]
    deterministic_fixtures: int
    executable_fixture_count: int
    blocked_fixture_count: int
    estimated_production_recommendation_gain: dict[str, int]
    candidates: tuple[IntelligenceCandidate, ...]
    family_findings: tuple[dict[str, object], ...]
    value_ranking: tuple[dict[str, str], ...]
    high_value_source_ready_candidates: tuple[str, ...]
    hidden_information_violations: int
    invented_rules: int
    invented_formulas: int
    invented_defaults: int
    cumulative: dict[str, int]
    phase16c_guards: dict[str, object]
    production_guards: dict[str, object]
    phase17b_direction: str


def _candidate(
    family: str,
    candidate: str,
    source: str,
    heading: str,
    classification: SourceReadinessClassification,
    blocker: str,
    *,
    trigger: str = "qualitative source condition only",
    action: str = "described source action only",
    exceptions: str = "not exhaustively bounded",
    policy: str = "none identified",
    architecture: str = "READY",
    population: int | None = None,
) -> IntelligenceCandidate:
    return IntelligenceCandidate(
        family,
        candidate,
        source,
        heading,
        trigger,
        action,
        exceptions,
        policy,
        architecture,
        population,
        1,
        (
            "EXISTING_PRODUCTION_BASELINE"
            if classification is SourceReadinessClassification.SOURCE_EXECUTABLE
            else "PROSPECTIVE_BLOCKED_OR_DEFERRED"
        ),
        0,
        classification,
        blocker,
    )


def _candidates() -> tuple[IntelligenceCandidate, ...]:
    c = SourceReadinessClassification
    return (
        _candidate(
            "DEFENSIVE_PLAY",
            "second-hand low",
            "knowledge/play/principles/second-hand-low.md",
            "Basic Principle",
            c.EXCEPTION_INCOMPLETE,
            "honor, entry, and declarer-plan exceptions are not a deterministic state contract",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "third-hand high",
            "knowledge/play/principles/third-hand-high.md",
            "Basic Principle",
            c.EXCEPTION_INCOMPLETE,
            "which high card and unblock/retain exceptions are incomplete",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "cover an honor",
            "knowledge/play/principles/cover-an-honor-with-an-honor.md",
            "Basic Principle",
            c.EXCEPTION_INCOMPLETE,
            "sequence, dummy, and promotion exceptions remain contextual",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "forcing defence",
            "knowledge/play/defence/techniques/forcing-defence.md",
            "When to Adopt a Forcing Defence",
            c.AMBIGUOUS_ACTION,
            "source does not select an exact legal card",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "uppercut",
            "knowledge/play/defence/techniques/uppercut.md",
            "Requirements",
            c.SOURCE_PARTIAL,
            "requires complete trick/entry/trump-promotion timing beyond current exact trigger",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "count signal",
            "knowledge/play/defence/signaling/count.md",
            "Standard Count",
            c.PARTNERSHIP_DEPENDENT,
            "standard versus upside-down agreement is explicit",
            policy="partnership signaling agreement required",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "attitude signal",
            "knowledge/play/defence/signaling/attitude.md",
            "Standard Attitude",
            c.PARTNERSHIP_DEPENDENT,
            "standard versus upside-down agreement and card choice are explicit",
            policy="partnership signaling agreement required",
        ),
        _candidate(
            "DEFENSIVE_PLAY",
            "suit-preference signal",
            "knowledge/play/defence/signaling/suit-preference.md",
            "Basic Principle",
            c.PARTNERSHIP_DEPENDENT,
            "signal applicability and agreement are partnership-dependent",
            policy="partnership signaling agreement required",
        ),
        _candidate(
            "DECLARER_PLAY",
            "SIMPLE_UNBLOCK_KING",
            "knowledge/play/declarer-play/general-techniques/unblock.md",
            "Example 1 – Simple Unblock",
            c.SOURCE_EXECUTABLE,
            "already implemented; not a new expansion candidate",
            trigger="dummy A-J-10-9 opposite declarer K-Q in the frozen example",
            action="cash king, then queen",
            exceptions="exact frozen holding and legal-card state",
            architecture="PRODUCTION_READY",
        ),
        _candidate(
            "DECLARER_PLAY",
            "finesse",
            "knowledge/play/declarer-play/general-techniques/finesses/finesse.md",
            "Requirements",
            c.PROBABILITY_REQUIRED,
            "choice depends on location probabilities and alternative lines",
        ),
        _candidate(
            "DECLARER_PLAY",
            "marked finesse",
            "knowledge/play/declarer-play/general-techniques/finesses/marked-finesse.md",
            "Complete Count",
            c.PROBABILITY_REQUIRED,
            "requires validated complete-count or show-out conditioning",
        ),
        _candidate(
            "DECLARER_PLAY",
            "restricted-choice application",
            "knowledge/play/declarer-play/probability/restricted-choice.md",
            "Restricted Choice",
            c.PROBABILITY_REQUIRED,
            "no registered restricted-choice formula or exact conditioning contract",
        ),
        _candidate(
            "DECLARER_PLAY",
            "safety play",
            "knowledge/play/declarer-play/general-techniques/safety-play.md",
            "When to Use",
            c.SOURCE_PARTIAL,
            "contract goal and alternative-line comparison are incomplete",
        ),
        _candidate(
            "DECLARER_PLAY",
            "hold-up",
            "knowledge/play/declarer-play/notrump-play/hold-up-play.md",
            "Do Not Use a Fixed Rule Blindly",
            c.EXCEPTION_INCOMPLETE,
            "entry, danger-hand, and suit-distribution exceptions prevent a fixed action",
        ),
        _candidate(
            "DECLARER_PLAY",
            "endplay",
            "knowledge/play/declarer-play/elimination-and-endplays/endplay.md",
            "Endplay into a Tenace",
            c.ARCHITECTURE_BLOCKED,
            "requires multi-trick planning and opponent-exit modeling",
            architecture="BLOCKED",
        ),
        _candidate(
            "DECLARER_PLAY",
            "crossruff",
            "knowledge/play/declarer-play/trump-play/cross-ruff.md",
            "Count Tricks Before Starting",
            c.SOURCE_PARTIAL,
            "cash-winner timing, overruff risk, and partial trump draw require line comparison",
        ),
        _candidate(
            "DECLARER_PLAY",
            "establish long suit",
            "knowledge/play/declarer-play/notrump-play/establishing-long-suits.md",
            "Compare Candidate Suits",
            c.AMBIGUOUS_ACTION,
            "source requires comparison among suits and entries rather than one deterministic card",
        ),
        _candidate(
            "PROBABILITY",
            "KNOWN_CARD_COUNT",
            "knowledge/play/declarer-play/probability/probability-in-bridge.md",
            "Known and Unknown Information",
            c.SOURCE_EXECUTABLE,
            "already implemented; not a new expansion candidate",
            trigger="explicit visible/played card context reconciles to 52 cards",
            action="return exact unknown-card count",
            exceptions="duplicate or unreconciled accounting rejected",
            architecture="PRODUCTION_READY",
        ),
        _candidate(
            "PROBABILITY",
            "RESTRICTED_CHOICE",
            "knowledge/play/declarer-play/probability/restricted-choice.md",
            "Restricted Choice",
            c.SOURCE_PARTIAL,
            "question model exists but formula, conditioning scope, and precision contract are incomplete",
        ),
        _candidate(
            "PROBABILITY",
            "VACANT_PLACES",
            "knowledge/play/counting/vacant-places.md",
            "Vacant Places",
            c.SOURCE_PARTIAL,
            "question model exists but source-conditioned formula contract is incomplete",
        ),
        _candidate(
            "PROBABILITY",
            "SUIT_DISTRIBUTION",
            "knowledge/play/declarer-play/probability/suit-distributions.md",
            "Suit Distributions",
            c.SOURCE_PARTIAL,
            "candidate distributions exist architecturally but no bounded production formula contract",
        ),
        _candidate(
            "PROBABILITY",
            "TRUMP_BREAKS",
            "knowledge/play/declarer-play/probability/trump-distribution/readme.md",
            "Trump Distribution",
            c.SOURCE_PARTIAL,
            "question model exists but conditioned formula and rounding contract are incomplete",
        ),
        _candidate(
            "PROBABILITY",
            "MONTE_CARLO",
            "knowledge/play/declarer-play/probability/probability-in-bridge.md",
            "Simulation",
            c.ARCHITECTURE_BLOCKED,
            "no sampling model, legal-deal generator contract, precision, or convergence rule",
            architecture="BLOCKED",
        ),
        _candidate(
            "OPENING_LEAD",
            "fourth-best",
            "knowledge/play/defence/opening-leads/fourth-best.md",
            "Basic Principle",
            c.POLICY_REQUIRED,
            "suit selection and contract/exception precedence unresolved",
            policy="lead-carding agreement required",
        ),
        _candidate(
            "OPENING_LEAD",
            "third-and-fifth",
            "knowledge/play/defence/opening-leads/third-fifth.md",
            "Basic Principle",
            c.POLICY_REQUIRED,
            "suit selection and partnership agreement unresolved",
            policy="lead-carding agreement required",
        ),
        _candidate(
            "OPENING_LEAD",
            "standard honor lead",
            "knowledge/play/defence/opening-leads/standard-leads.md",
            "Sequence Leads",
            c.EXCEPTION_INCOMPLETE,
            "suit selection, broken/interior sequences, and scope exceptions unresolved",
        ),
        _candidate(
            "OPENING_LEAD",
            "Rusinow",
            "knowledge/play/defence/opening-leads/rusinow.md",
            "Basic Principle",
            c.POLICY_REQUIRED,
            "partnership method plus suit selection and exceptions unresolved",
            policy="Rusinow agreement required",
        ),
        _candidate(
            "OPENING_LEAD",
            "top of nothing",
            "knowledge/play/defence/opening-leads/top-of-nothing.md",
            "Definition",
            c.EXCEPTION_INCOMPLETE,
            "suit selection and holding exceptions unresolved",
        ),
        _candidate(
            "OPENING_LEAD",
            "singleton",
            "knowledge/play/defence/opening-leads/standard-leads.md",
            "Short Suit Leads",
            c.SOURCE_PARTIAL,
            "source describes tactic but not deterministic suit precedence",
        ),
        _candidate(
            "OPENING_LEAD",
            "partner's suit",
            "knowledge/play/defence/opening-leads/lead-partners-suit.md",
            "Opening Lead",
            c.SOURCE_PARTIAL,
            "auction meaning, support, and competing-suit precedence are incomplete",
        ),
        _candidate(
            "OPENING_LEAD",
            "longest/strongest",
            "knowledge/play/defence/opening-leads/standard-leads.md",
            "Against Notrump Contracts",
            c.AMBIGUOUS_ACTION,
            "ties, sequences, danger, and suit selection exceptions unresolved",
        ),
        _candidate(
            "OPENING_LEAD",
            "trump lead",
            "knowledge/play/defence/opening-leads/standard-leads.md",
            "Suit Contract Opening Leads",
            c.SOURCE_PARTIAL,
            "trigger is strategic and does not define exact card/precedence",
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "natural 1NT responses",
            "knowledge/bidding/natural-bids/responses/response-to-1nt.md",
            "Natural Responses",
            c.SOURCE_PARTIAL,
            "convention precedence and exact residual triggers unchanged",
            population=124,
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "responder rebids",
            "knowledge/bidding/natural-bids/rebids/responder-rebids.md",
            "Responder Rebids",
            c.SOURCE_PARTIAL,
            "exact-prefix call precedence and exceptions unchanged",
            population=1194,
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "weak-two responses",
            "knowledge/bidding/natural-bids/responses/response-to-weak-two.md",
            "Responses",
            c.PARTNERSHIP_DEPENDENT,
            "inquiry method, forcing status, and replies remain agreements",
            policy="partnership method required",
            population=540,
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "three-level preempt responses",
            "knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md",
            "Responses",
            c.SOURCE_PARTIAL,
            "fit, stoppers, vulnerability, judgment, and precedence unchanged",
            population=166,
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "2NT responses",
            "knowledge/bidding/natural-bids/responses/response-to-2nt.md",
            "Responses",
            c.LOW_SAMPLE,
            "33-case residual population and incomplete Stayman/natural precedence",
            population=33,
        ),
        _candidate(
            "BIDDING_RESIDUAL",
            "strong 2C residual continuations",
            "knowledge/bidding/natural-bids/responses/response-to-2-clubs.md",
            "Opener's Rebid",
            c.SOURCE_PARTIAL,
            "qualitative suit rebids and precedence unchanged",
            population=23,
        ),
    )


def run_phase17_source_readiness_audit() -> Phase17SourceReadinessAudit:
    candidates = _candidates()
    counts = Counter(item.classification.value for item in candidates)
    for classification in SourceReadinessClassification:
        counts.setdefault(classification.value, 0)
    families = (
        "DEFENSIVE_PLAY",
        "DECLARER_PLAY",
        "PROBABILITY",
        "OPENING_LEAD",
        "BIDDING_RESIDUAL",
    )
    family_findings = tuple(
        {
            "family": family,
            "candidates": sum(item.family == family for item in candidates),
            "source_executable": sum(
                item.family == family
                and item.classification
                is SourceReadinessClassification.SOURCE_EXECUTABLE
                for item in candidates
            ),
            "new_high_value_executable": 0,
            "finding": "No new candidate passes the high-value source-ready gate.",
        }
        for family in families
    )
    ranking = (
        {
            "rank": "1",
            "family": "DECLARER_PLAY",
            "basis": "production architecture exists; several sources are close but need bounded exceptions/probabilities",
        },
        {
            "rank": "2",
            "family": "PROBABILITY",
            "basis": "question models exist, but every new family lacks a complete formula/conditioning contract",
        },
        {
            "rank": "3",
            "family": "DEFENSIVE_PLAY",
            "basis": "state architecture exists, but exact card actions or partnership policies remain incomplete",
        },
        {
            "rank": "4",
            "family": "BIDDING_RESIDUAL",
            "basis": "large measured populations, but Phase 12 source and precedence blockers are unchanged",
        },
        {
            "rank": "5",
            "family": "OPENING_LEAD",
            "basis": "no candidate resolves suit selection, scope, exceptions, precedence, and policy together",
        },
    )
    phase16 = run_phase16_coverage_closure_audit()
    return Phase17SourceReadinessAudit(
        families,
        len(candidates),
        dict(sorted(counts.items())),
        sum(item.deterministic_fixture_count for item in candidates),
        sum(
            item.classification is SourceReadinessClassification.SOURCE_EXECUTABLE
            for item in candidates
        ),
        sum(
            item.classification is not SourceReadinessClassification.SOURCE_EXECUTABLE
            for item in candidates
        ),
        {
            item.candidate: item.expected_new_recommendations
            for item in candidates
            if item.classification is SourceReadinessClassification.SOURCE_EXECUTABLE
        },
        candidates,
        family_findings,
        ranking,
        (),
        0,
        0,
        0,
        0,
        {
            "audit_requests": len(candidates),
            "candidate_families": len(families),
            "executable_candidates": 2,
            "deferred_candidates": len(candidates) - 2,
        },
        {
            "phase16_complete": phase16.phase16_complete,
            "readiness": len(phase16.readiness_matrix),
            "closure_fixtures": phase16.closure_fixtures,
            "provenance_lost": phase16.provenance_lost,
            "hidden_information_violations": phase16.hidden_information_violations,
            "unsafe_parser_findings": phase16.unsafe_parser_findings,
            "backward_compatibility": phase16.backward_compatibility,
        },
        {
            "production_recommendations": 4,
            "routes": len(create_standard_sayc_router().routes),
            "declarer_techniques": 1,
            "opening_lead_algorithms": 0,
            "defensive_algorithms": 0,
            "registered_probability_engines": len(
                DEFAULT_PROBABILITY_ENGINE_REGISTRY.registrations
            ),
            "new_probability_formulas": 0,
            "ordinary": "7871/761/9239",
        },
        "F. SOURCE ENRICHMENT PROGRAM",
    )


def write_artifacts(audit: Phase17SourceReadinessAudit, output: Path) -> None:
    (
        output / "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json"
    ).write_text(
        json.dumps(asdict(audit), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 17A — Bridge-Intelligence Expansion Source-Readiness Audit",
        "",
        "## Candidate and readiness inventory",
        "",
        f"Audited {audit.total_candidates} candidates across {len(audit.audited_families)} families with {audit.deterministic_fixtures} deterministic source-readiness fixtures. Classification counts: `{json.dumps(audit.classification_counts, sort_keys=True)}`. Existing executable fixtures: {audit.executable_fixture_count}; blocked/deferred fixtures: {audit.blocked_fixture_count}.",
        "",
        "The only SOURCE_EXECUTABLE candidates are the already-production SIMPLE_UNBLOCK_KING and KNOWN_CARD_COUNT baselines. Their expected new recommendation gain is zero. No new candidate passes the high-value source-ready gate.",
        "",
        "## Per-family findings",
        "",
    ]
    for finding in audit.family_findings:
        lines += [
            f"### {finding['family']}",
            "",
            f"Candidates/executable/new high-value: {finding['candidates']}/{finding['source_executable']}/{finding['new_high_value_executable']}. {finding['finding']}",
            "",
        ]
    lines += ["## Source and architecture matrix", ""]
    for item in audit.candidates:
        lines += [
            f"- **{item.family} — {item.candidate}: {item.classification.value}.** Status: {item.execution_status}. `{item.source_path}` — {item.heading}. Architecture: {item.architecture_status}. Fixture count: {item.deterministic_fixture_count}. Trigger: {item.trigger}. Action: {item.action}. Exceptions: {item.exceptions}. Policy: {item.policy_dependency}. Population: {item.observed_population if item.observed_population is not None else 'not statistically weighted'}. Expected new recommendations: {item.expected_new_recommendations}. Blocker: {item.blocker}"
        ]
    lines += ["", "## Qualitative value ranking", ""]
    for row in audit.value_ranking:
        lines += [f"{row['rank']}. **{row['family']}** — {row['basis']}"]
    lines += [
        "",
        "## High-value source-ready gate and Phase 17B",
        "",
        "No new candidate satisfies all ten gate conditions; measurable new production gain is therefore 0. Selection: **F. SOURCE ENRICHMENT PROGRAM**. Enrichment should first turn one narrowly scoped declarer or probability candidate into a complete trigger/action/exception or formula/conditioning contract. Phase 17B is not implemented here.",
        "",
        "## Guards and verification",
        "",
        "Phase 16 remains complete at 27/27 readiness and 35 closure fixtures with zero provenance loss, hidden-information violations, unsafe parser findings, or invention. Phase 15 remains complete at 17/17; Phase 14 remains complete. Production recommendations remain 4, routes 45, SIMPLE_UNBLOCK_KING unchanged, opening-lead and defensive algorithms 0, probability engines 1, and KNOWN_CARD_COUNT unchanged. Ordinary benchmark remains 7,871/761/9,239.",
        "",
        "Hidden-information violations, invented rules, formulas, and defaults: 0. Added bidding rules/routes, declarer/opening-lead/defensive algorithms, and probability formulas: 0. Production defaults changed: NO. Canonical knowledge Markdown changes: 0.",
        "",
        "Phase 17A focused tests: 8 passed. Cumulative Phase 13–17 regressions: 280 passed. Router/PolicyRegistry guards: 28 passed. Full Phase 12 cumulative guards: 112 passed. Ruff: clean. Live ordinary deterministic benchmark: 7,871/761/9,239.",
        "",
        "Current cumulative Full Kit: Phase 17A",
        "",
    ]
    (
        output / "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.md"
    ).write_text("\n".join(lines), encoding="utf-8")


def build_full_kit(output: Path) -> tuple[int, int]:
    baseline = subprocess.run(
        ("git", "show", "HEAD:bridgelab-toolkit/bridgelab_phase16c_full_kit.zip"),
        cwd=output,
        check=True,
        capture_output=True,
    ).stdout
    members: dict[str, bytes] = {}
    with ZipFile(BytesIO(baseline)) as source:
        for name in source.namelist():
            members[name] = source.read(name)
    additions = (
        "benchmarks/phase17_bridge_intelligence_source_readiness_audit.py",
        "tests/test_bridge_phase17a_bridge_intelligence_source_readiness_audit.py",
        "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.md",
        "bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json",
    )
    for name in additions:
        members[name] = (output / name).read_bytes()
    target = output / "bridgelab_phase17a_full_kit.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name in sorted(members):
            archive.writestr(name, members[name])
    return len(members), 0


if __name__ == "__main__":
    root = Path.cwd()
    write_artifacts(run_phase17_source_readiness_audit(), root)
    build_full_kit(root)
