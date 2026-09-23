"""Phase 29P user-approved policy classification; never a production rule.

Policy version 29P is an audit overlay. Historical 29M/29O policy and all
production engines remain unchanged. Exact approved shape/HCP signatures are
positive evidence; missing examples, failed screens and ABSTAIN are not.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json

from .auction import Auction, CallType
from .deal_simulator import FullAuctionBatchResult
from .evaluation import evaluate_hand
from .models import Hand
from .nisim_nily_opening_policy import assess_rule_of_20
from .opening_abstention_root_cause_audit import build_opening_root_cause_report
from .opening_pass_positive_predicate_audit import assess_positive_opening_pass_candidate
from .sayc_route_configuration import create_standard_sayc_router


class Classification(str, Enum):
    OPEN_KNOWN = "OPEN_KNOWN"
    WEAK_MULTI_CANDIDATE = "WEAK_MULTI_CANDIDATE"
    PREEMPT_CANDIDATE = "PREEMPT_CANDIDATE"
    PASS_SUPPORTED = "PASS_SUPPORTED"
    PARTNERSHIP_TREATMENT = "PARTNERSHIP_TREATMENT"
    PROTECTED_UNRESOLVED = "PROTECTED_UNRESOLVED"
    UNKNOWN = "UNKNOWN"


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class PolicyAssessment(_Serializable):
    classification: Classification
    supported_call: str | None
    evidence: tuple[str, ...]
    unresolved: tuple[str, ...]
    explanation: str
    opening_position: int
    policy_version: str = "nisim-nily.audit-policy@29P"
    production_adopted: bool = False


def classify_nisim_nily_hand(hand: Hand, *, auction: Auction) -> PolicyAssessment:
    """Apply only Phase 29P C/D agreements to an unopened canonical auction.

    Weak 5-5 means exact named five-card suits below the C1 normal threshold
    of 12 HCP. It is not extended to 6-5. Rule20/11-major overlap is recorded;
    both policies say open and the explicit C8 treatment supplies the call.
    Candidate labels do not assert that unspecified quality tests are passed.
    """
    if auction.is_complete or any(c.kind is not CallType.PASS for c in auction.calls):
        raise ValueError("requires a live unopened auction")
    f = evaluate_hand(hand)
    s, h, d, c = f.suit_lengths
    shape = tuple(sorted(f.suit_lengths, reverse=True))
    r20 = assess_rule_of_20(hand)
    position = len(auction.calls) + 1
    C = Classification
    strength = tuple(label for condition, label in (
        (f.hcp >= 12, "PHASE29P C1: 12+ opening strength"),
        (r20.qualifies, "PHASE29P C2: Rule20 >=20 opens"),
        (f.hcp == 11 and max(s, h) >= 5, "PHASE29P C3: 11 HCP and five-card major opens"),
    ) if condition)

    def result(kind, call, evidence, reason, unresolved=()):
        return PolicyAssessment(kind, call, tuple(evidence), tuple(unresolved), reason, position)

    if f.hcp < 12:
        call = "2S" if s == 5 and (d == 5 or c == 5) else "2H" if h == 5 and (d == 5 or c == 5) else "2NT" if d == c == 5 else None
        if call:
            return result(C.PARTNERSHIP_TREATMENT, call, ("PHASE29P C8/D: exact weak 5-5 treatment",) + strength,
                "Exact named 5-5 below 12 HCP; partnership-only call. Strength overlaps also say open; no generic SAYC adoption.")
    if strength:
        # Only an explicit denomination agreement, not strength alone, selects a call.
        call = "1S" if s == h == 5 and f.hcp >= 12 else None
        return result(C.OPEN_KNOWN, call, strength + (("PHASE29P C5: normal-strength 5S+5H -> 1S",) if call else ()),
            "Opening entitlement established; denomination is not inferred from strength.",
            () if call else ("opening denomination/family not determined by this strength approval",))
    case17 = f.hcp == 10 and s == 5 and shape == (5, 4, 2, 2)
    case18 = f.hcp == 10 and s == h == 4 and shape == (4, 4, 3, 2)
    if position >= 3 and (case17 or case18):
        return result(C.OPEN_KNOWN, "1S" if case17 else None,
            ("PHASE29P D positional case " + ("17" if case17 else "18"),),
            "Explicit third/fourth-seat example; no generalized light-opening formula.",
            () if case17 else ("case18: 1D or 1C depends on unspecified partnership system selector",))
    if position <= 2:
        signature = (
            "9 HCP, 5S-4H-2-2" if f.hcp == 9 and (s, h, d, c) == (5, 4, 2, 2) else
            "10 HCP, 4-4-3-2 outside third/fourth seat" if f.hcp == 10 and shape == (4, 4, 3, 2) else
            "8 HCP, 5S-5H-2-1" if f.hcp == 8 and s == h == 5 and sorted((d, c)) == [1, 2] else
            "case17: 10 HCP, 5S-4-2-2 outside third/fourth seat" if case17 else None
        )
        if signature:
            return result(C.PASS_SUPPORTED, "P", ("PHASE29P D: " + signature,),
                "Affirmative approved HCP/shape/seat signature; no strength, long-suit or C8 overlap. Not inferred from production ABSTAIN.")
    if max(f.suit_lengths) >= 8 or (max(f.suit_lengths) >= 7 and 6 in f.suit_lengths) or s == h == 6:
        return result(C.PROTECTED_UNRESOLVED, None, ("29M-29O protected distribution; PHASE29P D forbids extrapolation",),
            "Unspecified long-suit/competing-family boundary.", ("strong playing-trick, long-suit and family precedence treatment",))
    if 7 in f.suit_lengths:
        return result(C.PREEMPT_CANDIDATE, None, ("PHASE29P C7/D: qualifying weak seven-card suits",),
            "Seven-card shape is present; qualification is not asserted.",
            ("partnership strength, quality, vulnerability and seat qualification",))
    if s == 6 or h == 6:
        return result(C.WEAK_MULTI_CANDIDATE, None, ("PHASE29P C6/D; partnership plays Multi 2D",),
            "Six-card major shape is present; exact weak/Multi qualification and call remain unresolved.",
            ("Multi variants, strength/quality/seat/vulnerability and exact call",))
    if max(d, c) >= 6 or (s == h == 5):
        return result(C.PROTECTED_UNRESOLVED, None, ("PHASE29P D: no extrapolation from unidentified minor examples",),
            "Unapproved distribution: weak six-minor examples lack card/HCP identity; equal majors lack matching Pass signature.",
            ("exact minor Pass example or distributional partnership decision",))
    return result(C.UNKNOWN, None, ("PHASE29P C9/C10/D",),
        "No affirmative approved signature; Rule20 failure and no-rule-match do not imply Pass.",
        ("positive policy / honor and contextual exception details",))


@dataclass(frozen=True, slots=True)
class RealHandRow(_Serializable):
    deal_index: int
    dealer: str
    vulnerability: str
    acting_seat: str
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    two_longest: tuple[int, int]
    rule20_total: int
    opening_position: int
    auction_before: tuple[str, ...]
    production_status: str
    production_abstention_code: str | None
    route_id: str | None
    root_cause: str
    rule_trace: tuple[dict, ...]
    phase29n_classification: str
    policy: PolicyAssessment
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PolicyAuditReport(_Serializable):
    seed: int
    total_deals: int
    opening_abstentions: int
    cases: tuple[RealHandRow, ...]
    selected_indices: tuple[int, ...]
    counts: tuple[tuple[str, int], ...]
    selected_counts: tuple[tuple[str, int], ...]
    availability: tuple[tuple[str, int], ...]
    positive_pass: int
    known_open_not_pass: int
    unresolved_not_pass: int
    route_count: int
    simulation_errors: int
    reproduction_errors: int = 0
    production_changed: bool = False
    invariant: str = "Known opening -> BID; proven Pass -> PASS; unresolved -> ABSTAIN. PASS != fallback."


def build_nisim_nily_policy_audit(batch: FullAuctionBatchResult) -> PolicyAuditReport:
    # Existing audit regenerates each actual dealer hand and verifies all route traces.
    prior = build_opening_root_cause_report(batch, minimum_hcp=0)
    rows = []
    for old in sorted(prior.strong_cases, key=lambda row: row.deal_index):
        hand = Hand.parse(old.hand)
        f = evaluate_hand(hand)
        r20 = assess_rule_of_20(hand)
        policy = classify_nisim_nily_hand(hand, auction=Auction(next(a.dealer for a in batch.auctions if a.deal_index == old.deal_index)))
        s, h, d, c = f.suit_lengths
        tags = tuple(tag for condition, tag in (
            (f.hcp <= 8 and max(f.suit_lengths) <= 5, "low-hcp-apparent-pass"),
            (r20.qualifies, "rule20"), (f.hcp in (10, 11), "10-11-borderline"),
            (s == 6 or h == 6, "six-major"), (d == 6 or c == 6, "six-minor"),
            (7 in f.suit_lengths, "seven-card"), (f.suit_lengths.count(5) == 2, "5-5"),
            ((s == 5 or h == 5) and (d == 5 or c == 5), "major-minor-5-5"),
            (d == c == 5, "both-minors-5-5"), (s == h == 5, "equal-five-majors"),
            (f.hcp >= 12 or policy.classification is Classification.PROTECTED_UNRESOLVED, "strong-protected"),
        ) if condition)
        rows.append(RealHandRow(old.deal_index, old.dealer, old.vulnerability, old.dealer, old.hand,
            f.hcp, f.suit_lengths, (r20.longest_suit_length, r20.second_longest_suit_length), r20.score,
            1, old.auction_before, old.production_status, old.production_abstention_code, old.route_id,
            old.root_cause.value, tuple(t.to_dict() for t in old.rule_trace),
            assess_positive_opening_pass_candidate(hand).classification.value, policy, tags))
    availability = Counter(tag for row in rows for tag in row.tags)
    availability.update({"third-hand": 0, "fourth-hand": 0})
    selected = set()
    # Deterministic deliberate coverage: up to three from every requested stratum
    # and classification, then earliest records until at least 36 real hands.
    for tag in sorted(availability):
        selected.update(row.deal_index for row in [r for r in rows if tag in r.tags][:3])
    for kind in Classification:
        selected.update(row.deal_index for row in [r for r in rows if r.policy.classification is kind][:3])
    # Include each distinct affirmative Pass signature and notable strength
    # boundary, not just the first three members of a large classification.
    signatures = set()
    for row in rows:
        key = row.policy.evidence if row.policy.classification is Classification.PASS_SUPPORTED else None
        if key and key not in signatures:
            selected.add(row.deal_index)
            signatures.add(key)
    for predicate in (
        lambda r: r.hcp >= 12,
        lambda r: r.hcp <= 10 and r.rule20_total >= 20,
        lambda r: r.hcp == 11 and r.rule20_total < 20 and max(r.suit_lengths[:2]) >= 5,
        lambda r: max(r.suit_lengths) >= 8,
    ):
        selected.update(r.deal_index for r in [row for row in rows if predicate(row)][:3])
    for row in rows:
        if len(selected) >= 36:
            break
        selected.add(row.deal_index)
    counts = Counter(row.policy.classification.value for row in rows)
    selected_counts = Counter(row.policy.classification.value for row in rows if row.deal_index in selected)
    positive = counts[Classification.PASS_SUPPORTED.value]
    known = counts[Classification.OPEN_KNOWN.value] + counts[Classification.PARTNERSHIP_TREATMENT.value]
    return PolicyAuditReport(batch.seed, batch.requested_deals, len(rows), tuple(rows), tuple(sorted(selected)),
        tuple((k.value, counts[k.value]) for k in Classification),
        tuple((k.value, selected_counts[k.value]) for k in Classification), tuple(sorted(availability.items())),
        positive, known, len(rows) - positive - known, len(create_standard_sayc_router().routes), batch.errors)
