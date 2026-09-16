"""Phase 29O evidence decomposition. No new bidding or trick-count formula."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .deal_simulator import AuctionOutcome, FullAuctionBatchResult
from .models import Hand, Seat, Vulnerability
from .nisim_nily_opening_policy import build_nisim_nily_opening_policy
from .opening_pass_positive_predicate_audit import (
    PositivePassAssessment, PositivePassClassification, assess_positive_opening_pass_candidate,
    build_positive_pass_audit_report,
)
from .sayc import create_sayc_opening_engine


class SafetyEvidenceStatus(str, Enum):
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNKNOWN = "UNKNOWN"


class SafetyEvidenceDimension(str, Enum):
    PLAYING_TRICK_SAFETY = "PLAYING_TRICK_SAFETY"
    EXCEPTION_POLICY_SAFETY = "EXCEPTION_POLICY_SAFETY"
    CONTEXT_SAFETY = "CONTEXT_SAFETY"
    POSITIVE_PASS_POLICY = "POSITIVE_PASS_POLICY"


class ResolutionType(str, Enum):
    AUTHORITATIVE_SOURCE_REQUIRED = "AUTHORITATIVE_SOURCE_REQUIRED"
    PARTNERSHIP_DECISION_REQUIRED = "PARTNERSHIP_DECISION_REQUIRED"
    ENGINE_HELPER_REQUIRED = "ENGINE_HELPER_REQUIRED"
    ALREADY_RESOLVED = "ALREADY_RESOLVED"


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class SafetyEvidenceAssessment(_Serializable):
    dimension: SafetyEvidenceDimension
    status: SafetyEvidenceStatus
    authority: str
    evidence: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, SafetyEvidenceDimension) or not isinstance(self.status, SafetyEvidenceStatus):
            raise TypeError("dimension and status must be typed enums")


def overall_safety(dimensions: tuple[SafetyEvidenceAssessment, ...]) -> SafetyEvidenceStatus:
    """Known positive hazard wins; otherwise complete affirmative proof is needed."""
    if any(d.status is SafetyEvidenceStatus.UNSAFE for d in dimensions):
        return SafetyEvidenceStatus.UNSAFE
    if (len(dimensions) == len(SafetyEvidenceDimension)
            and {d.dimension for d in dimensions} == set(SafetyEvidenceDimension)
            and all(d.status is SafetyEvidenceStatus.SAFE and d.evidence for d in dimensions)):
        return SafetyEvidenceStatus.SAFE
    return SafetyEvidenceStatus.UNKNOWN


@dataclass(frozen=True, slots=True)
class OpeningExceptionEvidence(_Serializable):
    exception_id: str
    name: str
    authority: str
    positive_predicate_available: bool
    exclusion_predicate_available: bool
    production_implemented: bool
    relevant_to_pass_safety: bool
    scope: str
    evidence: tuple[str, ...]
    unresolved_consequence: str


@dataclass(frozen=True, slots=True)
class SafetyPolicyGap(_Serializable):
    gap_id: str
    domain: str
    description: str
    gap_kind: str
    current_authority: str
    repository_evidence: tuple[str, ...]
    explicit_partnership_policy_available: bool
    production_implementation_available: bool
    required_resolution: ResolutionType


_F = "knowledge/bidding/principles/bidding-fundamentals/"
_O = "knowledge/bidding/natural-bids/opening-bids/"
_M = "bridge/nisim_nily_opening_policy.py"
_S = "knowledge/bidding/systems/sayc.md"


def opening_exception_registry() -> tuple[OpeningExceptionEvidence, ...]:
    """Availability is limited to the stated scope, never an exhaustive-policy claim."""
    rows = (
        ("normal-strength", "12+ normal strength", "NISIM_NILY_PARTNERSHIP_POLICY", True, True, True,
         "Strength only; production covers family subsets, not arbitrary calls", (_M + "#strength-12", _M + "#strength-13-plus")),
        ("rule20-11", "11-HCP Rule20 screen", "NISIM_NILY_PARTNERSHIP_POLICY", True, True, False,
         "11 HCP and score>=20; helper exists, call-family integration absent", (_M + "#strength-11", _F + "rule-of-20.md")),
        ("rule20-low", "Low-HCP Rule20 qualification", "SUPPORTED_REFERENCE", True, True, False,
         "Arithmetic exists; <=10 opening entitlement NOT approved", (_M + "#strength-10-or-less", _F + "rule-of-20.md#Exceptions")),
        ("strong-hcp", "Strong 2C HCP branch", "CANONICAL_PRODUCTION_REFERENCE", True, True, True,
         "HCP>=22 only; does not exclude playing-trick alternative", (_S + "#Strong 2♣ Opening", "bridge/sayc.py")),
        ("strong-playing", "Strong 2C playing-trick alternative", "SOURCE_INSUFFICIENT", False, False, False,
         "9+ playing-trick concept; no complete evaluator or safe upper bound", (_S + "#Strong 2♣ Opening", _F + "playing-tricks.md")),
        ("weak-two", "Controlled weak twos", "CANONICAL_PRODUCTION_REFERENCE", True, True, True,
         "Current exact-six 6-10 subset only; <=5 excludes this length domain", (_S + "#Weak Two Openings", "bridge/sayc.py")),
        ("preempt-three", "Controlled three-level preempts", "CANONICAL_PRODUCTION_REFERENCE", True, True, True,
         "Current exact-seven 6-10 subset only; <=5 excludes ordinary length domain", (_S + "#Three-Level Openings", "bridge/sayc.py")),
        ("preempt-variants", "Long-suit and competing-suit variants", "SUPPORTED_REFERENCE", False, True, False,
         "<=5 excludes six/seven/eight-plus shapes and 6-6/7-6 overlap only; does not decide bids within them", (_O + "weak-two-bids.md", _O + "three-level-preempts.md", _O + "four-level-preempts.md")),
        ("equal-majors", "Exactly 5S-5H preference 1S", "NISIM_NILY_PARTNERSHIP_POLICY", True, True, False,
         "Preference conditional on opening eligibility; no extension to 6-6", (_M + "#equal-five-card-majors",)),
        ("equal-minors", "Unresolved equal 5-5/6-6 minors", "UNRESOLVED", False, True, False,
         "Shape membership/exclusion known; selector missing; 3-3/4-4 already defined", (_M + "#equal-minors-5-5", _S + "#Better Minor")),
        ("controls-distribution", "Controls, suit quality, distribution upgrades", "SUPPORTED_REFERENCE", False, False, False,
         "Qualitative lighter-opening exceptions; no closed exclusion contract", (_O + "opening-requirements.md#Controls", _F + "rule-of-20.md#Exceptions")),
        ("nt-adjustments", "Optional NT shapes and strength adjustments", "SUPPORTED_REFERENCE", False, False, False,
         "Canonical NT subset exists; optional 5422/upgrades/five-card-major choices unadopted", (_O + "1nt-opening.md",)),
        ("seat-style", "Seat/passed-hand opening style", "SUPPORTED_REFERENCE", False, False, False,
         "First/second sound; third light; fourth Rule15; no approved partnership application", (_F + "seat-position.md", _F + "rule-of-15.md")),
        ("vulnerability-style", "Vulnerability opening/preempt style", "SUPPORTED_REFERENCE", False, False, False,
         "Aggressiveness differs by vulnerability; no exact adopted thresholds", (_F + "vulnerability.md",)),
        ("system-options", "Partnership activation and optional treatments", "PROJECT_CONTRACT", False, False, False,
         "SystemContext facts exist; generic SAYC does not imply nisim-nily activation", ("bridge/system_profiles.py", "bridge/bidding_rules.py", _M)),
        ("rule22", "Rule22 / quick-trick guidance", "SUPPORTED_REFERENCE", False, False, False,
         "Not adopted; not an independent required Pass gate or substitute for playing tricks", (_F + "rule-of-22.md", _F + "quick-tricks.md", _M + "#rule22")),
    )
    return tuple(OpeningExceptionEvidence(key, name, authority, positive, exclusion, implemented, True,
                 scope, evidence, "Unproved relevant exclusion remains UNKNOWN; no fallback Pass.")
                 for key, name, authority, positive, exclusion, implemented, scope, evidence in rows)


def safety_gap_matrix() -> tuple[SafetyPolicyGap, ...]:
    R = ResolutionType
    return (
        SafetyPolicyGap("playing-bound", "PLAYING_TRICK_SAFETY", "No exact 9+ evaluator or upper-bound exclusion proof", "SOURCE_GAP", "SOURCE_INSUFFICIENT", (_F + "playing-tricks.md", _S), False, False, R.AUTHORITATIVE_SOURCE_REQUIRED),
        SafetyPolicyGap("playing-treatment", "PLAYING_TRICK_SAFETY", "Choose/approve how strong playing-trick policy applies to the intended ordinary subset; protection remains in force", "POLICY_GAP", "UNRESOLVED", (_M + "#strong-2c-playing-tricks",), False, False, R.PARTNERSHIP_DECISION_REQUIRED),
        SafetyPolicyGap("closed-exceptions", "EXCEPTION_POLICY_SAFETY", "Select a closed controls/distribution/optional-opening exception policy", "POLICY_GAP", "SUPPORTED_REFERENCE", (_O + "opening-requirements.md", _F + "rule-of-20.md"), False, False, R.PARTNERSHIP_DECISION_REQUIRED),
        SafetyPolicyGap("seat-vulnerability", "CONTEXT_SAFETY", "Exact first-seat/vulnerability scope, later-seat exclusions and exception precedence", "POLICY_GAP", "SUPPORTED_REFERENCE", (_F + "seat-position.md", _F + "vulnerability.md"), False, False, R.PARTNERSHIP_DECISION_REQUIRED),
        SafetyPolicyGap("activation", "CONTEXT_SAFETY", "Approve explicit nisim-nily activation rather than infer it from generic SAYC", "POLICY_GAP", "PROJECT_CONTRACT", ("bridge/system_profiles.py", _M), False, False, R.PARTNERSHIP_DECISION_REQUIRED),
        SafetyPolicyGap("positive-domain", "POSITIVE_PASS_POLICY", "29N proposed screen is not affirmative approved Pass policy", "POLICY_GAP", "SOURCE_INSUFFICIENT", (_M + "#positive-pass", "bridge/opening_pass_positive_predicate_audit.py"), False, False, R.PARTNERSHIP_DECISION_REQUIRED),
        SafetyPolicyGap("rule20-helper", "strength arithmetic", "Canonical Hand-based Rule20 helper already available", "ALREADY_RESOLVED", "NISIM_NILY_PARTNERSHIP_POLICY", (_M + "#assess_rule_of_20",), True, False, R.ALREADY_RESOLVED),
        SafetyPolicyGap("approved-opening-coverage", "11-HCP screen and exact 5-5 major preference", "Policy/helper available, but production family integration absent; preserve existing boundaries", "COVERAGE_GAP", "NISIM_NILY_PARTNERSHIP_POLICY", (_M, "bridge/sayc.py"), True, False, R.ALREADY_RESOLVED),
    )


@dataclass(frozen=True, slots=True)
class PassSafetyCase(_Serializable):
    deal_index: int | None
    hand: str
    dealer: str
    acting_seat: str
    opening_position: int
    vulnerability: str
    relative_vulnerability: str
    actor_previously_passed: bool
    system: str
    system_options: tuple[tuple[str, str], ...]
    phase29n: PositivePassAssessment
    dimensions: tuple[SafetyEvidenceAssessment, ...]
    overall: SafetyEvidenceStatus
    positive_hazards: tuple[str, ...]
    objectively_excluded_domains: tuple[str, ...]


def assess_pass_safety_evidence(hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
                               system: SystemContext, deal_index: int | None = None) -> PassSafetyCase:
    """Read actual context and existing positive bids; never infer safety from failure."""
    if auction.is_complete or any(call.serialize() != "P" for call in auction.calls):
        raise ValueError("audit requires a nonterminal unopened auction")
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability, system=system)
    previous = assess_positive_opening_pass_candidate(hand)
    result = create_sayc_opening_engine().evaluate(context)
    hazards = []
    if result.has_recommendation:
        hazards.append("existing-opening:" + result.recommended_call.serialize())
    if previous.hcp >= 12:
        hazards.append("approved-normal-opening-strength")
    elif previous.hcp == 11 and previous.rule20_qualified:
        hazards.append("approved-11-hcp-rule20-strength-screen")
    # Low-HCP Rule20, long suits and unresolved ties remain risks, not invented OPEN verdicts.
    Status, Dimension = SafetyEvidenceStatus, SafetyEvidenceDimension
    playing = Status.UNSAFE if previous.hcp >= 22 else Status.UNKNOWN
    dimensions = (
        SafetyEvidenceAssessment(Dimension.PLAYING_TRICK_SAFETY, playing,
            "CANONICAL_PRODUCTION_REFERENCE" if playing is Status.UNSAFE else "SOURCE_INSUFFICIENT",
            (_S + "#Strong 2♣ Opening", _F + "playing-tricks.md", "bridge/sayc.py"),
            "22+ HCP positively applies." if playing is Status.UNSAFE else
            "HCP branch can be excluded below 22; no approved playing-trick bound excludes the alternative. No canonical PT/QT opening evaluator located."),
        SafetyEvidenceAssessment(Dimension.EXCEPTION_POLICY_SAFETY, Status.UNSAFE if hazards else Status.UNKNOWN,
            "EXISTING_PRODUCTION_OR_APPROVED_PARTNERSHIP" if hazards else "SUPPORTED_REFERENCE_INCOMPLETE",
            (_M, _O + "opening-requirements.md", _F + "rule-of-20.md#Exceptions"),
            "Positive opening/strength evidence: " + ", ".join(hazards) if hazards else
            "Scoped numerical/length exceptions can be excluded, but controls, suit-quality/distribution upgrades and optional-opening exceptions lack a closed approved contract."),
        SafetyEvidenceAssessment(Dimension.CONTEXT_SAFETY, Status.UNKNOWN, "PARTNERSHIP_DECISION_REQUIRED",
            (_F + "seat-position.md", _F + "vulnerability.md", "bridge/system_profiles.py", "bridge/bidding_rules.py"),
            "Seat/vulnerability/history/system facts are known; their Pass-policy effect and partnership activation are not approved. Known facts do not make context irrelevant."),
        SafetyEvidenceAssessment(Dimension.POSITIVE_PASS_POLICY, Status.UNKNOWN, "PARTNERSHIP_DECISION_REQUIRED",
            (_M + "#positive-pass", "PHASE 29N G"),
            "Independent approval gap: proposal to audit an ordinary screen is not approval to call those hands Pass, even if all exceptions were excluded."),
    )
    own = vulnerability.is_vulnerable(context.seat)
    opponents = vulnerability.is_vulnerable(context.seat.next())
    relative = "equal-vulnerable" if own and opponents else "equal-nonvulnerable" if not own and not opponents else "unfavorable" if own else "favorable"
    excluded = tuple(check.check_id for check in previous.safety_checks if check.state.value == "ESTABLISHED")
    return PassSafetyCase(deal_index, hand.serialize(), auction.dealer.value, context.seat.value,
                          len(auction.calls) + 1, vulnerability.value, relative, False,
                          system.system, system.options, previous, dimensions, overall_safety(dimensions),
                          tuple(hazards), excluded)


@dataclass(frozen=True, slots=True)
class PartnershipQuestion(_Serializable):
    question_id: str
    question: str
    why: str
    affected_cases: int
    evidence: tuple[str, ...]
    unanswered_default: str = "UNKNOWN / ABSTAIN"


@dataclass(frozen=True, slots=True)
class PassSafetyAuditReport(_Serializable):
    seed: int
    total_deals: int
    depth0_abstain: int
    phase29n_counts: tuple[tuple[str, int], ...]
    phase29m_counts: tuple[tuple[str, int], ...]
    phase29m_to_n: tuple[tuple[str, str, int], ...]
    insufficient_cases: tuple[PassSafetyCase, ...]
    dimension_counts: tuple[tuple[str, str, int], ...]
    unknown_intersections: tuple[tuple[str, int], ...]
    subset_overall_counts: tuple[tuple[str, int], ...]
    full_population_overall_counts: tuple[tuple[str, int], ...]
    context_distribution: tuple[tuple[str, int], ...]
    representatives: tuple[tuple[str, tuple[PassSafetyCase, ...]], ...]
    exceptions: tuple[OpeningExceptionEvidence, ...]
    gaps: tuple[SafetyPolicyGap, ...]
    partnership_questions: tuple[PartnershipQuestion, ...]
    simulation_errors: int
    reproduction_errors: int
    playing_trick_evaluator_found: bool = False
    quick_trick_evaluator_found: bool = False
    production_ready: bool = False
    invariant: str = "PASS != FALLBACK_FOR_ABSTAIN"


def build_pass_safety_audit_report(batch: FullAuctionBatchResult) -> PassSafetyAuditReport:
    previous = build_positive_pass_audit_report(batch)
    rows = []
    for item in sorted(batch.auctions, key=lambda a: a.deal_index):
        if item.outcome is AuctionOutcome.ABSTAIN and item.steps and not item.steps[-1].auction_before:
            rows.append(assess_pass_safety_evidence(Hand.parse(item.steps[-1].hand), auction=Auction(item.dealer),
                        vulnerability=item.vulnerability, system=SystemContext("SAYC"), deal_index=item.deal_index))
    if len(rows) != previous.opening_depth0_abstain:
        raise ValueError("Phase29N population mismatch")
    subset = tuple(row for row in rows if row.phase29n.classification is PositivePassClassification.SOURCE_OR_POLICY_INSUFFICIENT)
    if len(subset) != previous.source_policy_insufficient_count:
        raise ValueError("Phase29N insufficient population mismatch")
    counts = tuple((dimension.value, status.value, sum(any(d.dimension is dimension and d.status is status for d in row.dimensions) for row in subset))
                   for dimension in SafetyEvidenceDimension for status in SafetyEvidenceStatus)
    first_three = tuple(SafetyEvidenceDimension)[:3]
    intersections = []
    for mask in range(8):
        names = tuple(d for i, d in enumerate(first_three) if mask & (1 << i))
        label = "+".join(d.value for d in names) or "NONE_UNKNOWN"
        n = sum(tuple(d.dimension for d in row.dimensions[:3] if d.status is SafetyEvidenceStatus.UNKNOWN) == names for row in subset)
        intersections.append((label, n))
    def status_counts(population):
        return tuple((s.value, sum(row.overall is s for row in population)) for s in SafetyEvidenceStatus)
    reps = [("all-safe", tuple(row for row in rows if row.overall is SafetyEvidenceStatus.SAFE)[:3])]
    for dimension in first_three:
        reps.append((dimension.value + "-UNKNOWN", tuple(row for row in subset if any(d.dimension is dimension and d.status is SafetyEvidenceStatus.UNKNOWN for d in row.dimensions))[:3]))
    reps.append(("positive-unsafe", tuple(row for row in rows if row.overall is SafetyEvidenceStatus.UNSAFE)[:3]))
    for category in (PositivePassClassification.RULE20_POTENTIAL_OPENING, PositivePassClassification.PROTECTED_PREEMPT_DOMAIN):
        reps.append((category.value, tuple(row for row in rows if row.phase29n.classification is category)[:3]))
    size = len(subset)
    questions = (
        PartnershipQuestion("playing", "Which sourced playing-trick definition or justified narrow-domain exclusion should govern nisim-nily's protected strong branch?", "Need proof, not a new guessed formula; protection remains until resolved.", size, (_F + "playing-tricks.md", _M + "#strong-2c-playing-tricks")),
        PartnershipQuestion("exceptions", "Within the proposed <=10/max-length<=5/Rule20<20 domain, what exact control, suit-quality or distribution exceptions are retained, and how are they excluded?", "Define a closed exception contract without universalizing qualitative notes.", size, (_O + "opening-requirements.md", _F + "rule-of-20.md")),
        PartnershipQuestion("scope", "Is the initial policy dealer-first-seat only, for which vulnerabilities, and how is nisim-nily explicitly selected apart from generic SAYC?", "Known context facts do not determine approved contextual behavior; later seats may stay out of scope.", size, (_F + "seat-position.md", _F + "vulnerability.md", "bridge/system_profiles.py")),
        PartnershipQuestion("positive-pass", "After those exclusions are proved, do you approve the exact bounded subset as affirmative Pass policy?", "Earlier approvals explicitly withheld a positive Pass predicate; conditional approval is not assumed.", size, (_M + "#positive-pass", "PHASE 29N G")),
    )
    return PassSafetyAuditReport(batch.seed, batch.requested_deals, len(rows),
        tuple((g.classification.value, g.count) for g in previous.groups), previous.phase29m_counts, previous.transitions,
        subset, counts, tuple(intersections), status_counts(subset), status_counts(rows),
        tuple(sorted(Counter(row.relative_vulnerability for row in subset).items())), tuple(reps),
        opening_exception_registry(), safety_gap_matrix(), questions, previous.simulation_error_count, previous.reproduction_error_count)
