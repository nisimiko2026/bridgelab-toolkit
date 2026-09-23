"""Phase 29R evidence preparation, never a Strong 2C or Pass predicate.

Symbolic probes retain x placeholders. HCP comes from canonical Hand/evaluation
APIs using zero-HCP spot representatives solely for counting. Those temporary
spots are not card evidence for playing tricks. No strength formula is fitted.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
import json

from .deal_simulator import FullAuctionBatchResult
from .evaluation import evaluate_hand
from .models import Hand
from .nisim_nily_opening_pass_contract import (
    ContractCase, ContractResult, Family, FamilyState, build_opening_pass_contract_audit,
)


class _Serializable:
    __slots__ = ()

    def to_dict(self):
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class StrongPolicyConcept(_Serializable):
    opening: str = "2C"
    game_forcing_property: bool = True
    eligibility_alternatives: tuple[str, ...] = (
        "22+ HCP", "9+ Playing Tricks", "independently testable game-forcing hand strength",
    )
    authority: str = "User PHASE29R B"
    playing_tricks_calculation_approved: bool = False
    independent_game_force_calculation_approved: bool = False
    forcing_property_is_eligibility_test: bool = False
    production_adopted: bool = False


@dataclass(frozen=True, slots=True)
class ExpertAnswer(_Serializable):
    expert_id: str
    decision: str | None = None
    notes: str = ""

    def __post_init__(self):
        if not self.expert_id.strip():
            raise ValueError("expert identity required")
        if self.decision is not None and (not isinstance(self.decision, str) or not self.decision.strip()):
            raise ValueError("decision must be nonempty text or null")


@dataclass(frozen=True, slots=True)
class PolicyProbe(_Serializable):
    hand_number: int
    cards: tuple[str, str, str, str]
    hcp: int
    card_count: int
    suit_lengths: tuple[int, int, int, int]
    user_decision: str
    expert_1: ExpertAnswer
    expert_2: ExpertAnswer
    additional_experts: tuple[ExpertAnswer, ...] = ()
    consensus: str = "AWAITING_EXPERTS"
    notes: str = ""
    evidence_status: str = "PROVISIONAL_USER_CLASSIFICATION"


def canonical_probe_hand(cards: tuple[str, str, str, str]) -> Hand:
    """Resolve x to distinct zero-HCP spots solely for canonical HCP/count API.

    The stored symbolic cards are unchanged. These representative spots carry
    no evidence about actual intermediates, suit quality or playing tricks.
    """
    groups = []
    for suit in cards:
        available = iter(rank for rank in "23456789T" if rank not in suit.upper())
        groups.append("".join(next(available) if rank == "x" else rank for rank in suit))
    return Hand.parse(".".join(groups))


def policy_probes() -> tuple[PolicyProbe, ...]:
    entries = (
        (("AKQJxx", "AKx", "xx", "xx"), "2C"),
        (("AKQJxxx", "AQx", "xx", "x"), "1S"),
        (("AKQxxxx", "AKx", "xx", "x"), "2C"),
        (("AKQJxxx", "KQx", "xx", "x"), "1S"),
        (("AKQxxx", "AKQx", "xx", "x"), "1S"),
        (("AKQxxx", "AQJx", "Kx", "x"), "1S"),
        (("AKQJxx", "x", "AKQxx", "x"), "2C"),
        (("AKxxx", "AKQxx", "Ax", "x"), "2C"),
        (("AQJxxx", "AKx", "KQx", "x"), "1S"),
        (("AKQJxxxx", "Kx", "Qx", "x"), "1S"),
    )
    rows = []
    for number, (cards, decision) in enumerate(entries, 1):
        hand = canonical_probe_hand(cards)
        facts = evaluate_hand(hand)
        rows.append(PolicyProbe(number, cards, facts.hcp, len(hand.cards), facts.suit_lengths, decision,
            ExpertAnswer("expert_1"), ExpertAnswer("expert_2"), notes=
            "Cards confirmed canonical by user. HCP and 13-card validation use Hand.parse/evaluate_hand with temporary zero-HCP spots for x; original symbolic cards retained, no playing-trick inference."))
    return tuple(rows)


def record_expert_answer(probe: PolicyProbe, answer: ExpertAnswer) -> PolicyProbe:
    """Return an updated evidence row only; no policy is adopted by consensus."""
    if answer.expert_id == probe.expert_1.expert_id:
        updated = replace(probe, expert_1=answer)
    elif answer.expert_id == probe.expert_2.expert_id:
        updated = replace(probe, expert_2=answer)
    else:
        others = tuple(x for x in probe.additional_experts if x.expert_id != answer.expert_id) + (answer,)
        updated = replace(probe, additional_experts=tuple(sorted(others, key=lambda x: x.expert_id)))
    decisions = tuple(x.decision for x in (updated.expert_1, updated.expert_2) + updated.additional_experts if x.decision is not None)
    status = "AWAITING_EXPERTS" if not decisions else "ONE_EXPERT_ONLY" if len(decisions) == 1 else "EXPERT_DISAGREEMENT" if len(set(decisions)) > 1 else "EXPERT_AGREEMENT_WITH_USER" if decisions[0] == updated.user_decision else "EXPERT_AGREEMENT_DIFFERS_FROM_USER"
    return replace(updated, consensus=status)


@dataclass(frozen=True, slots=True)
class ReferenceComparison(_Serializable):
    hand_number: int
    definition_id: str
    calculated_value: float | None
    at_least_nine: bool | None
    comparison_with_user: str
    evidence: str
    assumptions_and_limits: str
    production_eligible: bool = False


def reference_comparisons() -> tuple[ReferenceComparison, ...]:
    """Recorded descriptive calculations, not an executable hand evaluator.

    Only two complete sums can be transcribed without extrapolating missing
    long-suit patterns. Even these rely on approximate side-suit assumptions.
    Unknown values are null, never zero or a forced agreement with the user.
    """
    evidence = (
        "S AKQJxx approximately6 + H AK approximately2 + two small suits0 = approximately8.",
        "Seven-card AKQJxxx is not listed; side AQ is approximately1.5–2. Total unavailable.",
        "Seven-card AKQxxxx is not listed; side AK approximately2. Total unavailable.",
        "Seven-card AKQJxxx is not listed; side KQ table1, worked example KQ4=1.5. Total unavailable.",
        "Six-card AKQxxx and side AKQx lack exact entries. Total unavailable.",
        "Six-card AKQxxx and side AQJx lack exact entries; side K approximately0.5. Total unavailable.",
        "S AKQJxx approximately6; AKQxx approximately5 is listed as a MAJOR example. Transferring it to a second long diamond suit to obtain11 needs an unapproved assumption; total left unavailable.",
        "H AKQxx approximately5 and side A approximately1; S AKxxx lacks an exact long-suit entry. Total unavailable.",
        "S AQJxxx approximately5 + H AK approximately2 + D KQ table1 + small C0 = approximately8. Worked example KQ4=1.5 would instead give8.5.",
        "Eight-card AKQJxxxx is not listed; K approximately0.5, Qx not specified in side table. Total unavailable.",
    )
    rows = []
    for probe, text in zip(policy_probes(), evidence):
        value = 8.0 if probe.hand_number in (1, 9) else None
        comparison = "PT_THRESHOLD_DIFFERS_FROM_USER_2C" if probe.hand_number == 1 else "PT_THRESHOLD_CONSISTENT_WITH_USER_1S_ONLY" if probe.hand_number == 9 else "NOT_COMPUTABLE"
        rows.append(ReferenceComparison(probe.hand_number, "playing-tricks-illustrative-table", value,
            None if value is None else value >= 9, comparison, text,
            "Source: knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md#Major Suit Examples / Side Suit Values. Approximate estimates; x means small spot; AK/KQ interpreted as honor combinations in side suits, additive illustration only. No guaranteed bound, no independent game-force calculation, no bid selector."))
        for definition in ("2-clubs-qualitative-nine-tricks", "independent-game-force-strength"):
            rows.append(ReferenceComparison(probe.hand_number, definition, None, None, "NOT_COMPUTABLE",
                "No specified calculation for this hand.",
                "Source: knowledge/bidding/natural-bids/opening-bids/2-clubs.md#Basic Requirements / Playing Tricks; user29R B. Qualitative criterion only; opening's forcing property cannot supply hand eligibility."))
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class StrongAuditReport(_Serializable):
    concept: StrongPolicyConcept
    probes: tuple[PolicyProbe, ...]
    reference_comparisons: tuple[ReferenceComparison, ...]
    seed: int
    total_deals: int
    opening_abstentions: int
    raw_strong_unresolved: int
    already_open_supported_with_strong_unresolved: int
    blocker_count: int
    sole_blocker_count: int
    other_family_blocker_count: int
    hcp_distribution: tuple[tuple[int, int], ...]
    sorted_shape_distribution: tuple[tuple[str, int], ...]
    suit_order_shape_distribution: tuple[tuple[str, int], ...]
    longest_suit_distribution: tuple[tuple[int, int], ...]
    six_plus: int
    seven_plus: int
    eight_plus: int
    other_family_counts: tuple[tuple[str, int], ...]
    selected_indices: tuple[int, ...]
    blocker_cases: tuple[ContractCase, ...]
    phase29q_counts: tuple[tuple[str, int], ...]
    production_route_count: int
    simulation_errors: int
    existing_executable_pt_formula: bool = False
    existing_executable_independent_gf_test: bool = False
    new_strength_predicate: bool = False
    production_changed: bool = False


def build_strong_two_club_audit(batch: FullAuctionBatchResult) -> StrongAuditReport:
    q = build_opening_pass_contract_audit(batch)
    def strong_unknown(row):
        return any(c.family is Family.STRONG_PLAYING_TRICKS and c.state is FamilyState.UNRESOLVED for c in row.contract.family_checks)
    raw = tuple(row for row in q.cases if strong_unknown(row))
    known = {ContractResult.OPEN_SUPPORTED, ContractResult.PARTNERSHIP_TREATMENT}
    blockers = tuple(row for row in raw if row.contract.result not in known)
    def other_checks(row):
        return tuple(c.family.value for c in row.contract.family_checks if c.family is not Family.STRONG_PLAYING_TRICKS and c.state is FamilyState.UNRESOLVED)
    sole = tuple(row for row in blockers if not other_checks(row))
    selected = set(row.deal_index for row in sole[:5])
    # Actual rows only: cover every observed HCP, longest-length and other blocker.
    for attr in (lambda row: row.contract.hcp, lambda row: max(row.contract.suit_lengths), lambda row: other_checks(row)):
        seen = set()
        for row in blockers:
            key = attr(row)
            if key not in seen:
                selected.add(row.deal_index)
                seen.add(key)
    for row in blockers:
        if len(selected) >= 24:
            break
        selected.add(row.deal_index)
    return StrongAuditReport(StrongPolicyConcept(), policy_probes(), reference_comparisons(),
        q.seed, q.total_deals, q.depth0_abstain, len(raw), len(raw)-len(blockers), len(blockers), len(sole), len(blockers)-len(sole),
        tuple(sorted(Counter(row.contract.hcp for row in blockers).items())),
        tuple(sorted(Counter("-".join(map(str, sorted(row.contract.suit_lengths, reverse=True))) for row in blockers).items())),
        tuple(sorted(Counter("-".join(map(str, row.contract.suit_lengths)) for row in blockers).items())),
        tuple(sorted(Counter(max(row.contract.suit_lengths) for row in blockers).items())),
        sum(max(row.contract.suit_lengths)>=6 for row in blockers),
        sum(max(row.contract.suit_lengths)>=7 for row in blockers),
        sum(max(row.contract.suit_lengths)>=8 for row in blockers),
        tuple(sorted(Counter(f for row in blockers for f in other_checks(row)).items())),
        tuple(sorted(selected)), blockers, q.counts, q.production_route_count, q.simulation_errors)
