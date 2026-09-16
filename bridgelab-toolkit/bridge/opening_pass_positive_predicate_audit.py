"""Phase 29N proposed positive Pass conjunction, never a bidding rule.

Repository evidence cannot yet discharge the playing-trick and exception
checks. UNKNOWN is deliberately not treated as exclusion. No caller override
can turn missing evidence into a real-hand safe assessment.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json

from .deal_simulator import AuctionOutcome, FullAuctionBatchResult
from .evaluation import evaluate_hand
from .full_auction_abstention_audit import build_abstention_audit
from .full_auction_coverage import build_full_auction_coverage_report
from .models import Hand
from .nisim_nily_opening_policy import assess_rule_of_20, build_nisim_nily_opening_policy
from .opening_abstention_root_cause_audit import build_opening_root_cause_report
from .opening_pass_policy_audit import audit_passed_out_auction, build_opening_pass_policy_report


class SafetyState(str, Enum):
    ESTABLISHED = "ESTABLISHED"
    EXCLUDED = "EXCLUDED"
    UNKNOWN = "UNKNOWN"


class PositivePassClassification(str, Enum):
    KNOWN_OPENING_COVERAGE_BOUNDARY = "KNOWN_OPENING_COVERAGE_BOUNDARY"
    RULE20_POTENTIAL_OPENING = "RULE20_POTENTIAL_OPENING"
    PROTECTED_STRONG_2C_DOMAIN = "PROTECTED_STRONG_2C_DOMAIN"
    PROTECTED_PREEMPT_DOMAIN = "PROTECTED_PREEMPT_DOMAIN"
    PROTECTED_EQUAL_SUIT_DOMAIN = "PROTECTED_EQUAL_SUIT_DOMAIN"
    OTHER_PROTECTED_UNRESOLVED = "OTHER_PROTECTED_UNRESOLVED"
    SAFE_ORDINARY_PASS_CANDIDATE = "SAFE_ORDINARY_PASS_CANDIDATE"
    SOURCE_OR_POLICY_INSUFFICIENT = "SOURCE_OR_POLICY_INSUFFICIENT"


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


REQUIRED_CHECKS = (
    "bounded_strength", "bounded_suit_lengths", "ordinary_preempt_excluded",
    "known_hcp_strong_excluded", "opening_strength_boundary_excluded",
    "equal_minor_boundary_excluded", "equal_major_boundary_excluded",
    "strong_playing_tricks_excluded", "weak_preempt_overlap_excluded",
    "rule20_candidate_excluded", "other_opening_exceptions_excluded", "context_scope_established",
)


@dataclass(frozen=True, slots=True)
class PositivePassSafetyCheck(_Serializable):
    check_id: str
    state: SafetyState
    reason: str
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state, SafetyState):
            raise TypeError("state must be SafetyState")


def all_safety_conditions_established(checks: tuple[PositivePassSafetyCheck, ...]) -> bool:
    """Logical conjunction only; does not authenticate caller-supplied evidence.

Used by the assessor with internally derived checks. Tests may exercise the
abstract all-established truth table; that is not a real-hand safety proof.
Missing, duplicated, extra, EXCLUDED and UNKNOWN checks all fail closed.
"""
    return (
        len(checks) == len(REQUIRED_CHECKS)
        and {c.check_id for c in checks} == set(REQUIRED_CHECKS)
        and all(c.state is SafetyState.ESTABLISHED and c.provenance and c.reason for c in checks)
    )


@dataclass(frozen=True, slots=True)
class PositivePassAssessment(_Serializable):
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    shape_class: str
    longest_suit_length: int
    rule20_score: int
    rule20_qualified: bool
    partnership_policy_version: str
    classification: PositivePassClassification
    safety_checks: tuple[PositivePassSafetyCheck, ...]
    blocking_checks: tuple[str, ...]
    unknown_checks: tuple[str, ...]
    explanation: str
    numerical_screen_satisfied: bool
    candidate_policy_status: str = "PROPOSED_AUDIT_ONLY"
    production_recommendation_created: bool = False


def assess_positive_opening_pass_candidate(hand: Hand) -> PositivePassAssessment:
    """Assess affirmative hand facts independently of routes and ABSTAIN status.

Scope is first-seat hand-policy design. Missing approved context/exception
contracts remain UNKNOWN even when all objective screen conditions hold.
"""
    facts = evaluate_hand(hand)
    rule20 = assess_rule_of_20(hand)
    policy = build_nisim_nily_opening_policy()
    s, h, d, c = facts.suit_lengths
    equal_major = s == h and s >= 5
    equal_minor = c == d and c >= 5
    short_suits = facts.longest_length <= 5
    origin = ("PHASE 29N proposed predicate G", "nisim-nily.opening-policy@" + policy.version)

    def check(key: str, condition: bool, reason: str) -> PositivePassSafetyCheck:
        return PositivePassSafetyCheck(key, SafetyState.ESTABLISHED if condition else SafetyState.EXCLUDED, reason, origin)

    checks = (
        check("bounded_strength", facts.hcp <= 10, f"HCP={facts.hcp}; proposed ordinary domain requires <=10."),
        check("bounded_suit_lengths", short_suits, f"Longest={facts.longest_length}; requires every suit <=5."),
        check("ordinary_preempt_excluded", short_suits, "Every suit <=5 excludes ordinary six/seven-card shapes only; not a universal preempt theorem."),
        check("known_hcp_strong_excluded", facts.hcp < 22, "22+ HCP strong branch checked separately from playing tricks."),
        check("opening_strength_boundary_excluded", facts.hcp <= 10, "12+ normal opening strength and all 11-HCP policy cases remain outside this domain."),
        check("equal_minor_boundary_excluded", not equal_minor, "Equal 5-5/6-6 minors remain protected; 3-3/4-4 alone are not unresolved selectors."),
        check("equal_major_boundary_excluded", not equal_major, "Exactly 5S-5H has partnership preference 1S; 6-6 remains unresolved; neither can be Pass."),
        PositivePassSafetyCheck("strong_playing_tricks_excluded", SafetyState.UNKNOWN,
            "No sourced deterministic proof excludes 9+ playing tricks for this hand; low HCP/short suits are not an approved substitute.",
            ("knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md#Estimating Playing Tricks",
             "bridge/opening_pass_source_policy_audit.py#strong-playing-tricks", "PHASE 29M J")),
        check("weak_preempt_overlap_excluded", short_suits, "Bounded lengths exclude ordinary 6-6 and 7-6 long-suit overlap; long hands remain protected without selecting a preempt."),
        check("rule20_candidate_excluded", not rule20.qualifies, f"Rule20={rule20.score}; compute at every HCP, including <=10; score>=20 excludes safe Pass without itself choosing an opening."),
        PositivePassSafetyCheck("other_opening_exceptions_excluded", SafetyState.UNKNOWN,
            "No complete approved control/distribution/optional-opening exception contract proves exclusion.",
            ("PHASE 29M D4/L", "bridge/opening_pass_source_policy_audit.py#opening-requirements")),
        PositivePassSafetyCheck("context_scope_established", SafetyState.UNKNOWN,
            "First-seat sample does not approve a partnership Pass context/vulnerability policy; proposal is audit-only.",
            ("PHASE 29N G", "PHASE 29M context-and-evaluation")),
    )
    category = PositivePassClassification
    # Prefer informative known properties over a ubiquitous UNKNOWN check.
    # Unknown strong eligibility is not a claim that the hand IS a strong 2C.
    if 12 <= facts.hcp <= 21 and (equal_major or equal_minor):
        classification = category.KNOWN_OPENING_COVERAGE_BOUNDARY
    elif facts.hcp <= 11 and rule20.qualifies:
        classification = category.RULE20_POTENTIAL_OPENING
    elif facts.hcp >= 22:
        classification = category.PROTECTED_STRONG_2C_DOMAIN
    elif not short_suits:
        classification = category.PROTECTED_PREEMPT_DOMAIN
    elif equal_major or equal_minor:
        classification = category.PROTECTED_EQUAL_SUIT_DOMAIN
    elif facts.hcp >= 11:
        classification = category.OTHER_PROTECTED_UNRESOLVED
    elif all_safety_conditions_established(checks):
        classification = category.SAFE_ORDINARY_PASS_CANDIDATE
    else:
        classification = category.SOURCE_OR_POLICY_INSUFFICIENT
    blocked = tuple(item.check_id for item in checks if item.state is SafetyState.EXCLUDED)
    unknown = tuple(item.check_id for item in checks if item.state is SafetyState.UNKNOWN)
    numerical = facts.hcp <= 10 and short_suits and not rule20.qualifies and not equal_major and not equal_minor
    return PositivePassAssessment(
        facts.hcp, facts.suit_lengths, facts.shape_class.value, facts.longest_length,
        rule20.score, rule20.qualifies, policy.version, classification, checks, blocked, unknown,
        "Affirmative checks: " + "; ".join(f"{item.check_id}={item.state.value}" for item in checks), numerical,
    )


@dataclass(frozen=True, slots=True)
class PositivePassAuditCase(_Serializable):
    deal_index: int
    dealer: str
    vulnerability: str
    hand: str
    phase29m_category: str
    assessment: PositivePassAssessment


@dataclass(frozen=True, slots=True)
class PositivePassAuditGroup(_Serializable):
    classification: PositivePassClassification
    count: int
    percentage_of_opening_abstentions: float
    hcp_distribution: tuple[tuple[int, int], ...]
    shape_distribution: tuple[tuple[str, int], ...]
    longest_suit_distribution: tuple[tuple[int, int], ...]
    rule20_score_distribution: tuple[tuple[int, int], ...]
    representatives: tuple[PositivePassAuditCase, ...]


@dataclass(frozen=True, slots=True)
class PositivePassAuditReport(_Serializable):
    seed: int
    total_deals: int
    completed_simulations: int
    opening_depth0_abstain: int
    simulation_error_count: int
    reproduction_error_count: int
    groups: tuple[PositivePassAuditGroup, ...]
    phase29m_counts: tuple[tuple[str, int], ...]
    transitions: tuple[tuple[str, str, int], ...]
    phase29k_screen_count: int
    known_boundary_indexes: tuple[int, ...]
    numerical_screen_count: int
    numerical_screen_unknown_checks: tuple[tuple[str, int], ...]
    low_hcp_rule20_count: int
    low_hcp_rule20_representatives: tuple[PositivePassAuditCase, ...]
    passed_out_compatible: bool
    safe_candidate_count: int
    protected_unresolved_count: int
    source_policy_insufficient_count: int
    production_ready: bool = False
    readiness: str = "INCOMPLETE: strong playing-trick, exception and context exclusions lack affirmative evidence"
    invariant: str = "PASS != FALLBACK_FOR_ABSTAIN"


def build_positive_pass_audit_report(batch: FullAuctionBatchResult) -> PositivePassAuditReport:
    """Observe canonical simulation output; never feed assessments into routing.

ABSTAIN filters the historical population ONLY. The hand assessor accepts no
production status, route, recommended bid or deal index as classification input.
"""
    diagnostic = build_abstention_audit(batch)
    coverage = build_full_auction_coverage_report(batch)
    previous = build_opening_pass_policy_report(batch)
    root_causes = build_opening_root_cause_report(batch)
    known = {case.deal_index for case in root_causes.strong_cases}
    categories = PositivePassClassification
    rows: list[PositivePassAuditCase] = []
    for auction in sorted(batch.auctions, key=lambda value: value.deal_index):
        if auction.outcome is not AuctionOutcome.ABSTAIN or not auction.steps:
            continue
        step = auction.steps[-1]
        if step.auction_before:
            continue
        assessment = assess_positive_opening_pass_candidate(Hand.parse(step.hand))
        s, h, d, c = assessment.suit_lengths
        # Reproduce the historical report's documented precedence exactly.
        if auction.deal_index in known:
            old = "KNOWN_OPENING_COVERAGE_BOUNDARY"
        elif assessment.hcp == 11 and assessment.rule20_qualified:
            old = "RULE20_POTENTIAL_OPENING"
        elif assessment.longest_suit_length >= 6 or s == h == 5 or d == c == 5:
            old = "PROTECTED_UNRESOLVED"
        else:
            old = "SOURCE_OR_POLICY_INSUFFICIENT"
        rows.append(PositivePassAuditCase(auction.deal_index, auction.dealer.value,
                    auction.vulnerability.value, step.hand, old, assessment))
    count = len(rows)
    if count != diagnostic.depth0.count or count != previous.depth0_abstains:
        raise ValueError("canonical depth-0 populations do not reconcile")
    if count != dict(coverage.stop_depths).get(0, 0):
        raise ValueError("coverage report depth-0 count differs")
    if len({row.deal_index for row in rows}) != count:
        raise ValueError("duplicate deal index in audit population")

    def histogram(selected, getter):
        return tuple(sorted(Counter(getter(row.assessment) for row in selected).items()))

    groups = []
    for category in categories:
        selected = [row for row in rows if row.assessment.classification is category]
        groups.append(PositivePassAuditGroup(
            category, len(selected), round(100 * len(selected) / count, 6) if count else 0.0,
            histogram(selected, lambda a: a.hcp),
            histogram(selected, lambda a: "-".join(map(str, sorted(a.suit_lengths, reverse=True)))),
            histogram(selected, lambda a: a.longest_suit_length), histogram(selected, lambda a: a.rule20_score),
            tuple(selected[:3]),
        ))
    old_counts = Counter(row.phase29m_category for row in rows)
    old_counts["POLICY_SUPPORTED_POTENTIAL_PASS"] = 0
    transitions = Counter((row.phase29m_category, row.assessment.classification.value) for row in rows)
    numerical_rows = [row for row in rows if row.assessment.numerical_screen_satisfied]
    unknowns = Counter(key for row in numerical_rows for key in row.assessment.unknown_checks)
    low_rule20 = [row for row in rows if row.assessment.hcp <= 10 and row.assessment.rule20_qualified]
    passed_out = audit_passed_out_auction()
    counts = {g.classification: g.count for g in groups}
    protected = sum(counts[key] for key in (categories.PROTECTED_STRONG_2C_DOMAIN,
                    categories.PROTECTED_PREEMPT_DOMAIN, categories.PROTECTED_EQUAL_SUIT_DOMAIN,
                    categories.OTHER_PROTECTED_UNRESOLVED))
    return PositivePassAuditReport(
        batch.seed, batch.requested_deals, batch.completed_simulations, count, coverage.errors,
        len(diagnostic.reproduction_failures), tuple(groups), tuple(sorted(old_counts.items())),
        tuple((old, new, n) for (old, new), n in sorted(transitions.items())), previous.diagnostic_screen_count,
        tuple(sorted(known)), len(numerical_rows), tuple(sorted(unknowns.items())), len(low_rule20), tuple(low_rule20[:3]),
        passed_out.is_passed_out and passed_out.final_contract is None,
        counts[categories.SAFE_ORDINARY_PASS_CANDIDATE], protected, counts[categories.SOURCE_OR_POLICY_INSUFFICIENT],
    )
