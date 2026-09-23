"""Phase 29Q audit-only negative-family contract. No production bidding rule.

The approval supplies a decision algebra, not a missing playing-trick bound.
Historical explicit 29P Pass signatures supply scoped negative policy evidence;
other hands must independently discharge every family. An empty registry,
missing check, or unresolved family can never establish Pass.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json

from .auction import Auction, CallType
from .deal_simulator import FullAuctionBatchResult
from .evaluation import evaluate_hand
from .models import Hand, Seat, Vulnerability
from .nisim_nily_opening_policy import assess_rule_of_20
from .opening_pass_nisim_nily_policy_audit import build_nisim_nily_policy_audit


class Family(str, Enum):
    NORMAL_HCP = "NORMAL_HCP"
    RULE20 = "RULE20"
    MAJOR11 = "MAJOR11"
    STRONG_HCP = "STRONG_HCP"
    STRONG_PLAYING_TRICKS = "STRONG_PLAYING_TRICKS"
    WEAK_MULTI = "WEAK_MULTI"
    PREEMPT = "PREEMPT"
    WEAK_TWO_SUITED = "WEAK_TWO_SUITED"
    SIX_MINOR = "SIX_MINOR"
    PROTECTED_DISTRIBUTION = "PROTECTED_DISTRIBUTION"
    OTHER_ACTIVATED = "OTHER_ACTIVATED"
    SEAT_POLICY = "SEAT_POLICY"


class FamilyState(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNRESOLVED = "UNRESOLVED"


class ContractResult(str, Enum):
    OPEN_SUPPORTED = "OPEN_SUPPORTED"
    PARTNERSHIP_TREATMENT = "PARTNERSHIP_TREATMENT"
    WEAK_MULTI_UNRESOLVED = "WEAK_MULTI_UNRESOLVED"
    PREEMPT_UNRESOLVED = "PREEMPT_UNRESOLVED"
    PROTECTED_UNRESOLVED = "PROTECTED_UNRESOLVED"
    OTHER_UNRESOLVED = "OTHER_UNRESOLVED"
    PASS_SUPPORTED = "PASS_SUPPORTED"


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class FamilyCheck(_Serializable):
    family: Family
    state: FamilyState
    reason: str
    evidence: tuple[str, ...]
    supported_call: str | None = None

    def __post_init__(self):
        if not isinstance(self.family, Family) or not isinstance(self.state, FamilyState):
            raise TypeError("typed family and state required")
        if not self.reason or not self.evidence or any(not item for item in self.evidence):
            raise ValueError("every family result requires a reason and evidence")
        if self.supported_call is not None and self.state is not FamilyState.POSITIVE:
            raise ValueError("only a positive family may select an opening call")
        if self.supported_call == "P":
            raise ValueError("Pass is the all-negative result, never a positive opening family")


def resolve_families(checks: tuple[FamilyCheck, ...]) -> ContractResult:
    """Pure decision algebra, not authentication of caller-supplied bridge facts.

    Real-hand checks are generated below without status overrides. A complete
    schema is required even if some test-supplied evidence is positive.
    """
    R, S = ContractResult, FamilyState
    if len(checks) != len(Family) or {c.family for c in checks} != set(Family):
        return R.OTHER_UNRESOLVED
    positive = tuple(c for c in checks if c.state is S.POSITIVE)
    if positive:
        return R.PARTNERSHIP_TREATMENT if all(c.family is Family.WEAK_TWO_SUITED for c in positive) else R.OPEN_SUPPORTED
    unresolved = {c.family for c in checks if c.state is S.UNRESOLVED}
    if all(c.state is S.NEGATIVE for c in checks):
        return R.PASS_SUPPORTED  # complete explicit NEGATIVE proof, never no-match
    if Family.SEAT_POLICY in unresolved:
        return R.OTHER_UNRESOLVED
    if Family.PROTECTED_DISTRIBUTION in unresolved:
        return R.PROTECTED_UNRESOLVED
    if Family.PREEMPT in unresolved:
        return R.PREEMPT_UNRESOLVED
    if Family.WEAK_MULTI in unresolved:
        return R.WEAK_MULTI_UNRESOLVED
    if Family.SIX_MINOR in unresolved:
        return R.PROTECTED_UNRESOLVED
    return R.OTHER_UNRESOLVED


@dataclass(frozen=True, slots=True)
class ContractAssessment(_Serializable):
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    rule20_total: int
    dealer: str
    acting_seat: str
    vulnerability: str
    opening_position: int
    family_checks: tuple[FamilyCheck, ...]
    result: ContractResult
    supported_call: str | None
    reason: str
    approved_negative_signature: str | None
    additional_activated_families: tuple[str, ...]
    policy_version: str = "nisim-nily.opening-pass-contract@29Q"
    production_adopted: bool = False


def _approved_negative_signature(hcp, lengths, position):
    """Exact still-approved 29P D signatures, not the old classifier's result."""
    if position > 2:
        return None
    s, h, d, c = lengths
    shape = tuple(sorted(lengths, reverse=True))
    if hcp == 9 and lengths == (5, 4, 2, 2):
        return "29P D: 9 HCP, 5S-4H-2-2"
    if hcp == 10 and shape == (4, 4, 3, 2):
        return "29P D: 10 HCP, 4-4-3-2, first/second seat"
    if hcp == 8 and s == h == 5 and sorted((d, c)) == [1, 2]:
        return "29P D: 8 HCP, 5S-5H-2-1"
    if hcp == 10 and s == 5 and shape == (5, 4, 2, 2):
        return "29P D case17: 10 HCP, 5S-4-2-2, first/second seat"
    return None


def assess_opening_pass_contract(hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
                                 additional_activated_families: tuple[str, ...] = ()) -> ContractAssessment:
    """Evaluate every family using hand/context facts and scoped policy evidence.

    The audit explicitly targets nisim-nily; this does not select a production
    system profile. Additional activated family names lack evaluators and fail
    closed. They are never inferred from a generic SAYC option or registry gap.
    """
    if auction.is_complete or any(c.kind is not CallType.PASS for c in auction.calls):
        raise ValueError("requires a live unopened auction")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("canonical vulnerability required")
    if (not isinstance(additional_activated_families, tuple)
            or any(not isinstance(n, str) or not n.strip() for n in additional_activated_families)
            or len(set(additional_activated_families)) != len(additional_activated_families)):
        raise ValueError("additional family names must be a unique tuple of nonempty strings")
    additional = tuple(sorted(additional_activated_families))
    f = evaluate_hand(hand)
    s, h, d, c = f.suit_lengths
    r20 = assess_rule_of_20(hand)
    position = len(auction.calls) + 1
    normal = f.hcp >= 12 or r20.qualifies or (f.hcp == 11 and max(s, h) >= 5)
    signature = _approved_negative_signature(f.hcp, f.suit_lengths, position)
    S, F = FamilyState, Family
    checks = []

    def add(family, state, reason, *evidence, call=None):
        checks.append(FamilyCheck(family, state, reason, tuple(evidence), call))

    add(F.NORMAL_HCP, S.POSITIVE if f.hcp >= 12 else S.NEGATIVE,
        f"HCP={f.hcp}; {'meets' if f.hcp >= 12 else 'below'} 12-HCP normal threshold; no denomination inferred.", "PHASE29Q C NORMAL STRENGTH")
    add(F.RULE20, S.POSITIVE if r20.qualifies else S.NEGATIVE,
        f"Rule20={r20.score}; {'meets' if r20.qualifies else 'below'} 20; excludes only this family when negative.", "PHASE29Q C NORMAL STRENGTH", "bridge/nisim_nily_opening_policy.py#assess_rule_of_20")
    major11 = f.hcp == 11 and max(s, h) >= 5
    add(F.MAJOR11, S.POSITIVE if major11 else S.NEGATIVE,
        f"HCP={f.hcp}, S={s}, H={h}; exact 11-HCP plus 5+ major condition {'met' if major11 else 'not met'}.", "PHASE29Q C NORMAL STRENGTH")
    add(F.STRONG_HCP, S.POSITIVE if f.hcp >= 22 else S.NEGATIVE,
        f"HCP={f.hcp}; objective 22+ branch {'met' if f.hcp >= 22 else 'excluded'}; does not settle playing tricks.", "bridge/sayc.py#SaycStrongTwoClubOpeningRule", "PHASE29Q B4")
    if signature:
        add(F.STRONG_PLAYING_TRICKS, S.NEGATIVE,
            "Exact affirmative Pass approval excludes a strong-opening override for this scoped signature; this is policy evidence, not a calculated trick bound.", signature, "PHASE29Q B4/B9")
    else:
        add(F.STRONG_PLAYING_TRICKS, S.UNRESOLVED,
            "No approved playing-trick evaluator, safe upper bound, or matching explicit negative signature. HCP<22 alone cannot exclude the alternative.",
            "bridge/opening_pass_safety_evidence_audit.py#strong-playing", "knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md", "PHASE29Q B4")
    add(F.WEAK_MULTI, S.UNRESOLVED if max(s, h) >= 6 else S.NEGATIVE,
        f"S={s}, H={h}; " + ("six-or-longer major: Multi range/quality/variant unresolved; no natural SAYC2D import." if max(s, h) >= 6 else "no six-card major; current approved six-major family excluded. Optional five-card variants not activated."), "PHASE29Q C WEAK / MULTI")
    add(F.PREEMPT, S.UNRESOLVED if f.longest_length >= 7 else S.NEGATIVE,
        f"Longest={f.longest_length}; " + ("seven-or-longer suit: range/quality and long-suit treatment unresolved." if f.longest_length >= 7 else "no seven-card suit; approved seven-card family excluded; no six-card preempt variant activated."), "PHASE29Q C PREEMPTS")
    treatment = "2S" if s == 5 and (d == 5 or c == 5) else "2H" if h == 5 and (d == 5 or c == 5) else "2NT" if d == c == 5 else None
    if treatment and not normal:
        add(F.WEAK_TWO_SUITED, S.POSITIVE, "Exact named 5-5 below ALL three normal-strength triggers; partnership call supported.", "PHASE29Q C NISIM–NILY WEAK TWO-SUITED TREATMENTS", call=treatment)
    else:
        add(F.WEAK_TWO_SUITED, S.NEGATIVE, "Normal opening strength established, so weak treatment does not apply." if normal else "No exact 5S+5minor, 5H+5minor or 5D+5C shape; no 6-5/6-6 extension.", "PHASE29Q C NISIM–NILY WEAK TWO-SUITED TREATMENTS")
    add(F.SIX_MINOR, S.UNRESOLVED if max(d, c) >= 6 else S.NEGATIVE,
        f"D={d}, C={c}; " + ("six-or-longer minor lacks an approved negative rule; missing historical examples are not Pass evidence." if max(d, c) >= 6 else "no six-card minor, so that unresolved family is inapplicable."), "PHASE29Q C SIX-CARD MINORS")
    unusual = f.longest_length >= 8 or (f.longest_length >= 6 and sorted(f.suit_lengths)[-2] >= 5) or (s == h == 5 and not normal and not signature)
    add(F.PROTECTED_DISTRIBUTION, S.UNRESOLVED if unusual else S.NEGATIVE,
        "Unapproved 8+, 6-5/6-6 or sub-opening equal-major shape; no extension of exact agreements." if unusual else "No protected 8+/6-5/6-6 boundary; exact equal majors have opening eligibility or explicit negative signature, or are absent.", "PHASE29Q B PROTECTED_EXCEPTION", "PHASE29Q C exact 5-5 scope", signature or "canonical suit-length facts")
    add(F.OTHER_ACTIVATED, S.UNRESOLVED if additional else S.NEGATIVE,
        "Additional explicitly activated families lack approved evaluators: " + ", ".join(additional) if additional else "The explicit 29Q audit contract activates no additional opening family. This is an activation declaration, not the complement of production routes.", "PHASE29Q B8", "audit additional_activated_families=" + repr(additional))
    shape = tuple(sorted(f.suit_lengths, reverse=True))
    case17 = f.hcp == 10 and s == 5 and shape == (5, 4, 2, 2)
    case18 = f.hcp == 10 and s == h == 4 and shape == (4, 4, 3, 2)
    if position <= 2:
        add(F.SEAT_POLICY, S.NEGATIVE, f"Opening position={position}; within approved first/second-seat contract; no later-seat override. Vulnerability recorded, no unapproved adjustment.", "PHASE29Q B/C THIRD/FOURTH SEAT")
    elif case17 or case18:
        add(F.SEAT_POLICY, S.POSITIVE, "Exact approved later-seat case17 ->1S." if case17 else "Exact approved later-seat case18 opens; 1C/1D system selector unresolved.", "PHASE29P D case17/case18", call="1S" if case17 else None)
    else:
        add(F.SEAT_POLICY, S.UNRESOLVED, "Outside first/second-seat Pass scope; later-seat light/honor policy not generalized.", "PHASE29Q C THIRD/FOURTH SEAT")
    final = resolve_families(tuple(checks))
    call = None
    if final is ContractResult.PASS_SUPPORTED:
        reason = "All 12 required checks explicitly NEGATIVE with evidence; first/second-seat scope established. No unresolved check and no production no-match inference."
        call = "P"
    elif final in (ContractResult.OPEN_SUPPORTED, ContractResult.PARTNERSHIP_TREATMENT):
        if normal and s == h == 5:
            call = "1S"
        else:
            calls = {check.supported_call for check in checks if check.state is S.POSITIVE and check.supported_call}
            call = next(iter(calls)) if len(calls) == 1 else None
        reason = "Positive opening evidence blocks Pass even if other checks remain unresolved. " + ("Explicit policy determines the call." if call else "Strength entitlement alone does not select a denomination.")
    else:
        reason = "No positive opening resolved and at least one required check remains UNRESOLVED; audit disposition ABSTAIN/UNKNOWN."
    return ContractAssessment(hand.serialize(), f.hcp, f.suit_lengths, r20.score, auction.dealer.value,
        auction.next_seat.value, vulnerability.value, position, tuple(checks), final, call, reason, signature, additional)


@dataclass(frozen=True, slots=True)
class ContractCase(_Serializable):
    deal_index: int
    production_status: str
    production_abstention_code: str | None
    production_route: str | None
    phase29p_classification: str
    phase29p_call: str | None
    contract: ContractAssessment


@dataclass(frozen=True, slots=True)
class ContractAuditReport(_Serializable):
    seed: int
    total_deals: int
    depth0_abstain: int
    cases: tuple[ContractCase, ...]
    counts: tuple[tuple[str, int], ...]
    phase29p_counts: tuple[tuple[str, int], ...]
    transitions: tuple[tuple[str, str, tuple[int, ...]], ...]
    family_state_counts: tuple[tuple[str, str, int], ...]
    unresolved_blockers: tuple[tuple[str, int, tuple[int, ...]], ...]
    affirmative_overlaps: tuple[tuple[str, int, tuple[int, ...]], ...]
    pass_review_indices: tuple[int, ...]
    pass_count: int
    known_opening_count: int
    unresolved_count: int
    production_route_count: int
    simulation_errors: int
    production_ready: bool = False
    production_changed: bool = False


def build_opening_pass_contract_audit(batch: FullAuctionBatchResult) -> ContractAuditReport:
    prior = build_nisim_nily_policy_audit(batch)
    rows = tuple(ContractCase(row.deal_index, row.production_status, row.production_abstention_code,
        row.route_id, row.policy.classification.value, row.policy.supported_call,
        assess_opening_pass_contract(Hand.parse(row.hand), auction=Auction(Seat(row.dealer)),
                                    vulnerability=Vulnerability(row.vulnerability))) for row in prior.cases)
    counts = Counter(row.contract.result.value for row in rows)
    transitions = {}
    for row in rows:
        transitions.setdefault((row.phase29p_classification, row.contract.result.value), []).append(row.deal_index)
    unresolved_rows = tuple(row for row in rows if row.contract.result not in
        (ContractResult.OPEN_SUPPORTED, ContractResult.PARTNERSHIP_TREATMENT, ContractResult.PASS_SUPPORTED))
    blockers = tuple((family.value, len(ids), ids) for family in Family
        if (ids := tuple(row.deal_index for row in unresolved_rows if any(c.family is family and c.state is FamilyState.UNRESOLVED for c in row.contract.family_checks))))
    overlaps = {}
    for row in rows:
        key = "+".join(c.family.value for c in row.contract.family_checks if c.state is FamilyState.POSITIVE)
        if key:
            overlaps.setdefault(key, []).append(row.deal_index)
    passes = tuple(row.deal_index for row in rows if row.contract.result is ContractResult.PASS_SUPPORTED)
    known = counts[ContractResult.OPEN_SUPPORTED.value] + counts[ContractResult.PARTNERSHIP_TREATMENT.value]
    return ContractAuditReport(batch.seed, batch.requested_deals, len(rows), rows,
        tuple((r.value, counts[r.value]) for r in ContractResult), prior.counts,
        tuple((p, q, tuple(ids)) for (p, q), ids in sorted(transitions.items())),
        tuple((f.value, s.value, sum(any(c.family is f and c.state is s for c in row.contract.family_checks) for row in rows)) for f in Family for s in FamilyState),
        blockers, tuple((key, len(ids), tuple(ids)) for key, ids in sorted(overlaps.items())),
        passes[:20], len(passes), known, len(unresolved_rows), prior.route_count, prior.simulation_errors)
