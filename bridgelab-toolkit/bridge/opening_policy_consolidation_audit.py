"""Phase 29S consolidation overlay. Audit evidence only, never a bidding rule."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from enum import Enum
import json

from .auction import Auction, CallType
from .deal_simulator import FullAuctionBatchResult
from .evaluation import evaluate_hand
from .models import Hand, Seat, Suit, Vulnerability
from .opening_pass_nisim_nily_policy_audit import build_nisim_nily_policy_audit


class State(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class Classification(str, Enum):
    OPENING_SUPPORTED = "OPENING_SUPPORTED"
    PARTNERSHIP_TREATMENT_SUPPORTED = "PARTNERSHIP_TREATMENT_SUPPORTED"
    PASS_SUPPORTED = "PASS_SUPPORTED"
    UNRESOLVED = "UNRESOLVED"


FAMILIES = ("natural_strength", "natural_choice", "concentration", "one_nt",
    "weak_two_suited", "multi_weak", "multi_minor", "multi_nt", "strong_2c",
    "preempt", "later_seat", "individual_review")


class Serializable:
    __slots__ = ()
    def to_dict(self):
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Check(Serializable):
    family: str
    state: State
    reason: str
    provenance: str
    call: str | None = None

    def __post_init__(self):
        if self.family not in FAMILIES or not isinstance(self.state, State):
            raise TypeError("known family and typed state required")
        if not self.reason or not self.provenance:
            raise ValueError("reason and provenance required")


def all_negative(checks: tuple[Check, ...]) -> bool:
    return (len(checks) == len(FAMILIES) and {c.family for c in checks} == set(FAMILIES)
            and all(c.state is State.NEGATIVE and c.reason and c.provenance for c in checks))


def honor_pattern(holding: str) -> str:
    normalized = holding.upper().replace("10", "T")
    return "".join(rank for rank in "AKQJT" if rank in normalized)


def approved_playing_tricks(holding: str) -> float | None:
    """Only approved 29S J values. None is not zero or a safe upper bound.

    Short (up to three-card) holdings use their named honor pattern, with
    small spots unvalued. The sole approved long-suit value is exact AKQxxx.
    Empty/spot-only holdings and other long suits have no approved value.
    """
    cards = holding.upper().replace("10", "T")
    pattern = honor_pattern(cards)
    if len(cards) == 6 and pattern == "AKQ":
        return 6.0
    if len(cards) > 3:
        return None
    return {"A": 1.0, "K": 0.0, "Q": 0.0, "AK": 2.0, "AQ": 1.5,
        "AJ": 1.0, "AJT": 1.5, "KQ": 1.0, "KQT": 1.5,
        "KQJ": 2.0, "QJ": .25, "QJT": 1.0, "AKQ": 3.0}.get(pattern)


def strong_suit_22(holding: str) -> State:
    if len(holding) < 5:
        return State.NEGATIVE
    honors = set(honor_pattern(holding))
    if any(set(pattern) <= honors for pattern in ("AK", "AQ", "KQ", "KJT")):
        return State.POSITIVE
    if not (honors & set("AKQJ")):
        return State.NEGATIVE  # explicit: ten alone is not an honor
    return State.UNKNOWN  # approved patterns are not declared exhaustive


def strong_minor_quality(holding: str) -> State:
    pattern = honor_pattern(holding)
    if len(holding) == 6 and any(set(p) <= set(pattern) for p in ("AK", "AQ", "AJT", "KQT", "KQJ", "KJT")):
        return State.POSITIVE
    # Seven-card examples are matched exactly in named ranks; no new patterns.
    if len(holding) == 7 and (pattern in ("KJT", "QJT", "AT", "KT")
            or (pattern in ("KJ", "QJ") and "9" in holding)):
        return State.POSITIVE
    return State.UNKNOWN


def relative_vulnerability(vulnerability: Vulnerability, seat: Seat) -> str:
    own = vulnerability.is_vulnerable(seat)
    opp = vulnerability.is_vulnerable(seat.next())
    return "unfavorable" if own and not opp else "favorable" if opp and not own else "equal-vulnerable" if own else "equal-nonvulnerable"


@dataclass(frozen=True, slots=True)
class Assessment(Serializable):
    hand: str
    dealer: str
    seat: str
    vulnerability: str
    relative_vulnerability: str
    opening_position: int
    hcp: int
    shape: str
    suit_lengths: tuple[int, int, int, int]
    holdings: tuple[str, str, str, str]
    honors: tuple[str, str, str, str]
    rule20: int
    checks: tuple[Check, ...]
    classification: Classification
    supported_call: str | None
    matched_families: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    reason: str
    playing_trick_components: tuple[float | None, ...]
    production_adopted: bool = False


def assess_opening_policy(hand: Hand, *, auction: Auction, vulnerability: Vulnerability) -> Assessment:
    if auction.is_complete or any(c.kind is not CallType.PASS for c in auction.calls):
        raise ValueError("requires a live unopened auction")
    facts = evaluate_hand(hand)
    hcp = facts.hcp
    lengths = facts.suit_lengths
    s, h, d, c = lengths
    holdings = tuple("".join(card.rank.symbol for card in hand.cards_in(suit)) for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS))
    relative = relative_vulnerability(vulnerability, auction.next_seat)
    position = len(auction.calls) + 1
    score = hcp + sum(sorted(lengths, reverse=True)[:2])
    normal = hcp >= 12 or score >= 20
    checks = []
    P, N, U = State.POSITIVE, State.NEGATIVE, State.UNKNOWN
    def add(family, state, reason, section, call=None):
        checks.append(Check(family, state, reason, "User PHASE29S consolidation " + section, call))

    add("natural_strength", P if normal else N, f"HCP={hcp}; Rule20={score}. 12+ or Rule20>=20 gives strength in every seat; neither selects a denomination alone.", "B")
    choice = None
    boundary = normal and any(lengths[m] == 6 and lengths[n] == 5 for m in (0, 1) for n in (2, 3))
    if normal:
        if s == h and s in (5, 6):
            choice = "1S"
        elif d == c and d in (5, 6):
            choice = "1D"
        else:
            for major in (0, 1):
                if lengths[major] == 5 and any(lengths[minor] in (5, 6) for minor in (2, 3)):
                    choice = "1S" if major == 0 else "1H"
    add("natural_choice", U if boundary else P if choice else N,
        "6-major + 5-minor depends on concentration/overall quality; unresolved boundary." if boundary else "Approved suit choice " + choice if choice else "No additional explicit C selector applies; no denomination is inferred from strength.", "C", choice)
    concentration = not normal and hcp == 11 and (max(s, h) >= 5 or 6 in (d, c))
    add("concentration", U if concentration else N, "11-HCP major/minor concentration predicate is not machine-defined." if concentration else "No decision depends on the qualitative 11-HCP exception.", "B3/B4")

    nt_range = 15 <= hcp <= 17 or (hcp == 14 and position in (3, 4))
    nt_state = N if not nt_range or s+h == 9 else P if facts.is_balanced else U
    add("one_nt", nt_state, "Outside stated range or exactly nine cards in majors." if nt_state is N else "Approved range, canonical balanced subset, including 5-card major; no nine-major exclusion." if nt_state is P else "Broader 'all such shapes' scope and >9-major interpretation require clarification; not replaced by generic SAYC.", "D", "1NT" if nt_state is P else None)

    # Natural strength has explicit priority. Only declared 5-5/5-major+6-minor
    # orientations are candidate shapes; other 6-5/6-6 are not silently adopted.
    weak_shapes = [(m, n) for m in (0, 1) for n in (2, 3) if lengths[m] == 5 and lengths[n] in (5, 6)]
    minor_shape = (d, c) in ((5, 5), (6, 5))
    uncovered_shape = len([n for n in lengths if n >= 5]) >= 2 and not weak_shapes and not minor_shape and not (s == h == 5)
    floor = 3 if position == 3 and relative == "favorable" else 5 if relative == "favorable" else 6
    weak_potential = not normal and (bool(weak_shapes) or minor_shape or uncovered_shape) and floor <= hcp <= 10
    add("weak_two_suited", U if weak_potential else N,
        "Candidate shape/range, but honor quality and approximate relative-vulnerability guidance are incomplete; orientation not generalized." if weak_potential else "Natural strength takes priority, or shape/context/range excludes this treatment.", "E/F")

    multi_states = []
    for major in (0, 1):
        if lengths[major] not in (6, 7) or any(lengths[j] >= 5 for j in range(4) if j != major):
            continue
        pattern = honor_pattern(holdings[major])
        if relative == "unfavorable" and hcp == 7 and pattern in ("KJT", "QJT"):
            multi_states.append(P if lengths[major] == 7 else N)
        elif relative == "favorable" and hcp == 5 and ("Q" in pattern or "K" in pattern):
            multi_states.append(P)
        else:
            multi_states.append(U)
    multi_weak = P if P in multi_states else U if U in multi_states else N
    add("multi_weak", multi_weak, "Explicit favorable 5-HCP Q/K or unfavorable 7-HCP seven-card KJT/QJT example matches." if multi_weak is P else "6/7-card single-major family absent, or explicit unfavorable six-card example rejects it." if multi_weak is N else "Length gate fits but strength/quality/relative-vulnerability combination is uncovered; no complete range or quality formula inferred.", "G", "2D" if multi_weak is P else None)

    minor_states = []
    if 20 <= hcp <= 21:
        for minor in (2, 3):
            if lengths[minor] >= 6 and all(lengths[j] < 4 for j in range(4) if j != minor):
                minor_states.append(strong_minor_quality(holdings[minor]) if facts.is_unbalanced else U if facts.is_semi_balanced else N)
    minor_state = P if P in minor_states else U if U in minor_states else N
    add("multi_minor", minor_state, "20–21, canonically unbalanced, 6+ minor, all side suits<4 and approved quality." if minor_state is P else "Required range/length/side-suit gates exclude strong-minor Multi." if minor_state is N else "Suit quality or treatment of canonical semi-balanced 6322 is not explicitly resolved.", "H", "2D" if minor_state is P else None)

    components = tuple(approved_playing_tricks(holding) for holding in holdings)
    strong = N
    strong_reason = "All three current Strong2C routes excluded by HCP or required closed-suit/side-suit structure."
    if hcp >= 23:
        strong, strong_reason = P, "23+ HCP route1."
    elif hcp == 22:
        statuses = [strong_suit_22(x) for x in holdings]
        strong = P if P in statuses else U if U in statuses else N
        strong_reason = "Exactly22: 5+ strong-suit approved pattern established." if strong is P else "Exactly22: unlisted strong-suit honor pattern remains unknown." if strong is U else "Exactly22: no qualifying 5+ strong suit (ten alone is not an honor)."
    elif 17 <= hcp <= 21:
        closed = [i for i, x in enumerate(holdings) if len(x) >= 6 and set("AKQ") <= set(x) and all(lengths[j] < 4 for j in range(4) if j != i)]
        if closed:
            strong = U if any(x is None for x in components) else P if sum(components) >= 8.5 else N
            strong_reason = "Route3 structural gates met; unapproved PT component prevents total." if strong is U else f"Route3 approved components total {sum(components)}; threshold8.5."
    add("strong_2c", strong, strong_reason, "J", "2C" if strong is P else None)
    multi_nt = N
    if 20 <= hcp <= 22:
        if facts.is_balanced:
            multi_nt = (N if strong is P else U if strong is U else P) if hcp == 22 else P
        elif tuple(sorted(lengths, reverse=True)) == (5, 4, 2, 2):
            multi_nt = U  # neither adopted nor explicitly prohibited by I
    add("multi_nt", multi_nt, "20–22 canonical4333/4432/5332, including five-card major/minor; 22-HCP2C priority checked." if multi_nt is P else "5422 or 22-HCP strong-suit priority remains unresolved." if multi_nt is U else "Range/shape excludes stated balanced subset, or 22-HCP2C takes priority.", "I", "2D" if multi_nt is P else None)
    add("preempt", U if max(lengths) >= 6 and not normal else N, "Long-suit preempt candidate; approximate HCP/quality/vulnerability and Rule2/3/4 do not select a deterministic level." if max(lengths) >= 6 and not normal else "No weak long-suit preempt dependency (normal strength or all suits<=5).", "K")
    add("later_seat", U if position >= 3 and not normal else N, "Later-seat concentration/quality and Pass scope need judgment; Rule15 not introduced." if position >= 3 and not normal else "No unresolved later-seat dependency.", "L/M")
    review = not normal and (hcp >= 11 or (5 <= hcp <= 10 and lengths.count(5) == 2) or (hcp > 5 and 6 in lengths))
    add("individual_review", U if review else N, "Explicit M review group unresolved; do not decide this case automatically." if review else "No unresolved M individual-review dependency after explicit positive strength checks.", "M")
    checks = tuple(sorted(checks, key=lambda x: FAMILIES.index(x.family)))
    matched = tuple(x.family for x in checks if x.state is P)
    blockers = tuple(x.family for x in checks if x.state is U)
    C = Classification
    call = None
    # Only explicit precedence: 23+/22 strong; natural over weak two-suited;
    # 20–21 balanced Multi meaning. Route3/strong-minor conflict stays unresolved.
    if strong is P and (hcp >= 22 or minor_state is not P):
        classification, call = C.OPENING_SUPPORTED, "2C"
    elif strong is P and minor_state is P:
        classification = C.UNRESOLVED
        blockers += ("strong_2c_vs_strong_minor_priority",)
    elif boundary:
        classification = C.UNRESOLVED
    elif (multi_nt is P or minor_state is P) and strong is not U:
        classification, call = C.PARTNERSHIP_TREATMENT_SUPPORTED, "2D"
    elif nt_state is P and strong is N:
        classification, call = C.OPENING_SUPPORTED, "1NT"
    elif normal:
        classification, call = C.OPENING_SUPPORTED, choice if strong is N else None
    elif multi_weak is P:
        # A matched branch is real evidence, but competing preempt level is
        # expressly judgmental in K; do not select between 2D and 3M.
        classification = C.UNRESOLVED
        blockers += ("multi_vs_preempt_priority",)
    elif all_negative(checks):
        classification, call = C.PASS_SUPPORTED, "P"
    else:
        classification = C.UNRESOLVED
    reason = "Complete explicit negative-family evidence; no production no-match inference." if classification is C.PASS_SUPPORTED else "Opening entitlement established; a null call means denomination/family is still unresolved." if classification is C.OPENING_SUPPORTED else "Explicit partnership branch and relevant priority are resolved." if classification is C.PARTNERSHIP_TREATMENT_SUPPORTED else "Policy judgment or priority remains unresolved; audit disposition ABSTAIN."
    return Assessment(hand.serialize(), auction.dealer.value, auction.next_seat.value, vulnerability.value,
        relative, position, hcp, facts.shape_class.value, lengths, holdings,
        tuple(honor_pattern(x) for x in holdings), score, checks, classification, call, matched, blockers, reason, components)


@dataclass(frozen=True, slots=True)
class Case(Serializable):
    deal_index: int
    production_decision: str
    production_call: str | None
    production_abstention_code: str | None
    assessment: Assessment


@dataclass(frozen=True, slots=True)
class Report(Serializable):
    seed: int
    deal_count: int
    population: int
    cases: tuple[Case, ...]
    counts: tuple[tuple[str, int], ...]
    queues: tuple[tuple[str, tuple[int, ...]], ...]
    family_counts: tuple[tuple[str, str, int], ...]
    route_count: int
    simulation_errors: int
    production_changed: bool = False


def build_consolidation_audit(batch: FullAuctionBatchResult) -> Report:
    previous = build_nisim_nily_policy_audit(batch)  # actual-hand/route reproduction
    cases = tuple(Case(row.deal_index, row.production_status, None, row.production_abstention_code,
        assess_opening_policy(Hand.parse(row.hand), auction=Auction(Seat(row.dealer)), vulnerability=Vulnerability(row.vulnerability))) for row in previous.cases)
    counts = Counter(c.assessment.classification.value for c in cases)
    predicates = {
        "A_11plus_unresolved": lambda a: a.hcp >= 11 and a.classification is Classification.UNRESOLVED,
        "B_5to10_two_fives": lambda a: 5 <= a.hcp <= 10 and a.suit_lengths.count(5) == 2,
        "C_above5_six_cards": lambda a: a.hcp > 5 and 6 in a.suit_lengths,
        "D_weak_two_suited_quality": lambda a: "weak_two_suited" in a.unresolved_blockers,
        "E_multi_weak": lambda a: "multi_weak" in a.unresolved_blockers or "multi_vs_preempt_priority" in a.unresolved_blockers,
        "F_preempt": lambda a: "preempt" in a.unresolved_blockers,
        "G_strong_2c_playing_tricks": lambda a: "strong_2c" in a.unresolved_blockers,
        "H_later_seat": lambda a: "later_seat" in a.unresolved_blockers,
    }
    return Report(batch.seed, batch.requested_deals, len(cases), cases,
        tuple((c.value, counts[c.value]) for c in Classification),
        tuple((name, tuple(c.deal_index for c in cases if predicate(c.assessment))) for name, predicate in predicates.items()),
        tuple((family, state.value, sum(any(x.family == family and x.state is state for x in c.assessment.checks) for c in cases)) for family in FAMILIES for state in State),
        previous.route_count, previous.simulation_errors)
