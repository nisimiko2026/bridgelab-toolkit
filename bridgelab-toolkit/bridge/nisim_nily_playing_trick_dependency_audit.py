"""Phase 30P exact Route-3 component-coverage audit; no new trick values.

One canonical rank-class hand represents each combination of suit lengths and
AKQJT honor patterns. Spot ranks are retained in each concrete holding. The
Phase 29S evaluator is the sole authority for playing-trick component values.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from itertools import combinations, product
import json

from .evaluation import evaluate_hand
from .models import Hand
from .nisim_nily_opening_binding_completion import complete_nisim_nily_opening_binding
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .opening_policy_consolidation_audit import approved_playing_tricks, honor_pattern
from .system_profiles import SystemProfile


SUITS = ("S", "H", "D", "C")
_HONORS = "AKQJT"
_SPOTS = "23456789"
_HCP = {"A": 4, "K": 3, "Q": 2, "J": 1, "T": 0}


class PlayingTrickComponentStatus(str, Enum):
    APPROVED_VALUE = "APPROVED_VALUE"
    MISSING_VALUE = "MISSING_VALUE"


class PlayingTrickComponentRole(str, Enum):
    PRIMARY_CLOSED_SUIT = "PRIMARY_CLOSED_SUIT"
    SIDE_SUIT = "SIDE_SUIT"


def _json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ApprovedPlayingTrickEntry:
    honor_pattern: str
    length_scope: str
    value: float

    def to_dict(self) -> dict:
        return {"honor_pattern": self.honor_pattern, "length_scope": self.length_scope,
                "value": self.value}


_APPROVED_TABLE = (
    ApprovedPlayingTrickEntry("A", "1-3", 1.0),
    ApprovedPlayingTrickEntry("K", "1-3", 0.0),
    ApprovedPlayingTrickEntry("Q", "1-3", 0.0),
    ApprovedPlayingTrickEntry("AK", "1-3", 2.0),
    ApprovedPlayingTrickEntry("AQ", "1-3", 1.5),
    ApprovedPlayingTrickEntry("AJ", "1-3", 1.0),
    ApprovedPlayingTrickEntry("AJT", "1-3", 1.5),
    ApprovedPlayingTrickEntry("KQ", "1-3", 1.0),
    ApprovedPlayingTrickEntry("KQT", "1-3", 1.5),
    ApprovedPlayingTrickEntry("KQJ", "1-3", 2.0),
    ApprovedPlayingTrickEntry("QJ", "1-3", 0.25),
    ApprovedPlayingTrickEntry("QJT", "1-3", 1.0),
    ApprovedPlayingTrickEntry("AKQ", "1-3", 3.0),
    ApprovedPlayingTrickEntry("AKQ", "exactly 6", 6.0),
)


@dataclass(frozen=True, slots=True)
class PlayingTrickComponentObservation:
    suit: str
    length: int
    holding: str
    honor_pattern: str
    approved_value: float | None
    status: PlayingTrickComponentStatus
    role: PlayingTrickComponentRole

    def to_dict(self) -> dict:
        return {"suit": self.suit, "length": self.length, "holding": self.holding,
                "honor_pattern": self.honor_pattern, "approved_value": self.approved_value,
                "status": self.status.value, "role": self.role.value}


@dataclass(frozen=True, slots=True)
class PlayingTrickRoute3Case:
    hand: str
    hcp: int
    suit_lengths: tuple[int, int, int, int]
    primary_suit: str
    component_observations: tuple[PlayingTrickComponentObservation, ...]
    known_component_total: float
    unknown_component_count: int
    route3_structural_gate_met: bool
    route3_fully_evaluable: bool
    threshold_met_if_evaluable: bool | None

    def to_dict(self) -> dict:
        return {"hand": self.hand, "hcp": self.hcp,
                "suit_lengths": list(self.suit_lengths), "primary_suit": self.primary_suit,
                "component_observations": [x.to_dict() for x in self.component_observations],
                "known_component_total": self.known_component_total,
                "unknown_component_count": self.unknown_component_count,
                "route3_structural_gate_met": self.route3_structural_gate_met,
                "route3_fully_evaluable": self.route3_fully_evaluable,
                "threshold_met_if_evaluable": self.threshold_met_if_evaluable}


@dataclass(frozen=True, slots=True)
class PlayingTrickComponentClass:
    dependency_id: str
    role: PlayingTrickComponentRole
    length: int
    honor_pattern: str
    representative_holdings: tuple[str, ...]
    occurrence_count: int
    approved_value: float | None
    status: PlayingTrickComponentStatus
    requires_new_authority: bool

    def to_dict(self) -> dict:
        return {"dependency_id": self.dependency_id, "role": self.role.value,
                "length": self.length, "honor_pattern": self.honor_pattern,
                "representative_holdings": list(self.representative_holdings),
                "occurrence_count": self.occurrence_count,
                "approved_value": self.approved_value, "status": self.status.value,
                "requires_new_authority": self.requires_new_authority}


@dataclass(frozen=True, slots=True)
class PlayingTrickLengthSummary:
    role: PlayingTrickComponentRole
    length: int
    occurrence_count: int
    approved_count: int
    missing_count: int
    distinct_honor_patterns: tuple[str, ...]
    representative_holdings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"role": self.role.value, "length": self.length,
                "occurrence_count": self.occurrence_count,
                "approved_count": self.approved_count,
                "missing_count": self.missing_count,
                "distinct_honor_patterns": list(self.distinct_honor_patterns),
                "representative_holdings": list(self.representative_holdings)}


@dataclass(frozen=True, slots=True)
class PlayingTrickDecisionRequest:
    dependency_id: str
    role: PlayingTrickComponentRole
    length: int
    honor_pattern: str
    representative_holdings: tuple[str, ...]
    why_needed: str
    existing_approved_neighbor_values: tuple[str, ...]
    requested_value: None = None

    def __post_init__(self) -> None:
        if self.requested_value is not None:
            raise ValueError("Phase 30P must not prefill a playing-trick value")

    def to_dict(self) -> dict:
        return {"dependency_id": self.dependency_id, "role": self.role.value,
                "length": self.length, "honor_pattern": self.honor_pattern,
                "representative_holdings": list(self.representative_holdings),
                "why_needed": self.why_needed,
                "existing_approved_neighbor_values": list(self.existing_approved_neighbor_values),
                "requested_value": self.requested_value}


@dataclass(frozen=True, slots=True)
class PlayingTrickDependencyAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    baseline_phase: str
    completion_version: str
    route3_min_hcp: int
    route3_max_hcp: int
    route3_min_primary_length: int
    route3_primary_pattern: str
    route3_max_side_length: int
    route3_threshold: float
    approved_table: tuple[ApprovedPlayingTrickEntry, ...]
    population_basis: str
    structural_population: int
    fully_evaluable_count: int
    blocked_count: int
    component_classes: tuple[PlayingTrickComponentClass, ...]
    primary_length_summaries: tuple[PlayingTrickLengthSummary, ...]
    side_length_summaries: tuple[PlayingTrickLengthSummary, ...]
    real_hand_witnesses: tuple[PlayingTrickRoute3Case, ...]
    decision_requests: tuple[PlayingTrickDecisionRequest, ...]
    production_changed: bool = False
    audit_version: str = "30P.1"
    dependency_classes: tuple[PlayingTrickComponentClass, ...] = field(init=False)
    missing_dependency_ids: tuple[str, ...] = field(init=False)
    dependency_complete: bool = field(init=False)
    shadow_execution_ready: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        if (self.profile_id, self.profile_version, self.base_system) != (
            NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
            SystemProfile.TWO_OVER_ONE_GF):
            raise ValueError("audit requires canonical Nisim–Nily identity")
        if (self.baseline_phase, self.completion_version, self.audit_version,
            self.route3_min_hcp, self.route3_max_hcp,
            self.route3_min_primary_length, self.route3_primary_pattern,
            self.route3_max_side_length, self.route3_threshold) != (
            "30O", "30O.1", "30P.1", 17, 21, 6, "AKQ", 3, 8.5):
            raise ValueError("Route-3 contract or baseline changed")
        if self.approved_table != _APPROVED_TABLE:
            raise ValueError("approved playing-trick table changed")
        if self.structural_population != self.fully_evaluable_count + self.blocked_count:
            raise ValueError("Route-3 population counts disagree")
        ids = [x.dependency_id for x in self.component_classes]
        if len(ids) != len(set(ids)) or ids != sorted(ids):
            raise ValueError("component classes need unique ordered IDs")
        missing = tuple(x for x in self.component_classes if x.requires_new_authority)
        object.__setattr__(self, "dependency_classes", missing)
        object.__setattr__(self, "missing_dependency_ids",
                           tuple(x.dependency_id for x in missing))
        complete = not missing
        object.__setattr__(self, "dependency_complete", complete)
        object.__setattr__(self, "shadow_execution_ready", False)
        object.__setattr__(self, "recommended_next_phase",
                           "30Q_NISIM_NILY_OPENING_SHADOW_ENGINE" if complete else
                           "30Q_NISIM_NILY_PLAYING_TRICK_COMPONENT_DECISIONS")
        if tuple(x.dependency_id for x in self.decision_requests) != self.missing_dependency_ids:
            raise ValueError("decision requests must cover missing classes exactly")
        if self.production_changed:
            raise ValueError("Phase 30P cannot change production")

    def to_dict(self) -> dict:
        return {"profile_id": self.profile_id, "profile_version": self.profile_version,
                "base_system": self.base_system.value, "baseline_phase": self.baseline_phase,
                "completion_version": self.completion_version,
                "route3_min_hcp": self.route3_min_hcp,
                "route3_max_hcp": self.route3_max_hcp,
                "route3_min_primary_length": self.route3_min_primary_length,
                "route3_primary_pattern": self.route3_primary_pattern,
                "route3_max_side_length": self.route3_max_side_length,
                "route3_threshold": self.route3_threshold,
                "approved_table": [x.to_dict() for x in self.approved_table],
                "population_basis": self.population_basis,
                "structural_population": self.structural_population,
                "fully_evaluable_count": self.fully_evaluable_count,
                "blocked_count": self.blocked_count,
                "component_classes": [x.to_dict() for x in self.component_classes],
                "dependency_classes": [x.to_dict() for x in self.dependency_classes],
                "primary_length_summaries": [x.to_dict() for x in self.primary_length_summaries],
                "side_length_summaries": [x.to_dict() for x in self.side_length_summaries],
                "real_hand_witnesses": [x.to_dict() for x in self.real_hand_witnesses],
                "decision_requests": [x.to_dict() for x in self.decision_requests],
                "missing_dependency_ids": list(self.missing_dependency_ids),
                "dependency_complete": self.dependency_complete,
                "shadow_execution_ready": self.shadow_execution_ready,
                "production_changed": self.production_changed,
                "recommended_next_phase": self.recommended_next_phase,
                "audit_version": self.audit_version}

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True, slots=True)
class _HoldingClass:
    length: int
    pattern: str
    holding: str
    hcp: int
    approved_value: float | None


def _holding_class(length: int, pattern: str) -> _HoldingClass | None:
    if len(pattern) > length or length - len(pattern) > len(_SPOTS):
        return None
    holding = pattern + _SPOTS[:length - len(pattern)]
    if honor_pattern(holding) != pattern:
        raise AssertionError("canonical holding changed honor pattern")
    return _HoldingClass(length, pattern, holding,
                         sum(_HCP[rank] for rank in pattern),
                         approved_playing_tricks(holding))


def _options(length: int, primary: bool) -> tuple[_HoldingClass, ...]:
    if primary:
        patterns = ("AKQ", "AKQJ", "AKQT", "AKQJT")
    else:
        patterns = tuple("".join(c) for size in range(min(length, 5) + 1)
                         for c in combinations(_HONORS, size))
    return tuple(x for pattern in patterns
                 if (x := _holding_class(length, pattern)) is not None)


def _class_id(role: PlayingTrickComponentRole, length: int, pattern: str) -> str:
    prefix = "primary" if role is PlayingTrickComponentRole.PRIMARY_CLOSED_SUIT else "side"
    name = pattern if pattern else "empty" if length == 0 else "spot_only"
    return f"{prefix}.{name}.length{length}"


def observe_route3_hand(hand: Hand) -> PlayingTrickRoute3Case | None:
    """Audit a real 13-card hand; return None outside Route-3 structural gates."""
    if not isinstance(hand, Hand):
        raise TypeError("canonical Hand required")
    facts = evaluate_hand(hand)
    if not 17 <= facts.hcp <= 21:
        return None
    holdings = tuple("" if x == "-" else x for x in hand.serialize().split("."))
    candidates = [i for i, x in enumerate(holdings)
                  if len(x) >= 6 and set("AKQ") <= set(x)
                  and all(len(holdings[j]) <= 3 for j in range(4) if j != i)]
    if len(candidates) != 1:
        return None
    primary = candidates[0]
    observations = tuple(PlayingTrickComponentObservation(
        SUITS[i], len(holding), holding, honor_pattern(holding),
        value, PlayingTrickComponentStatus.APPROVED_VALUE
        if value is not None else PlayingTrickComponentStatus.MISSING_VALUE,
        PlayingTrickComponentRole.PRIMARY_CLOSED_SUIT if i == primary
        else PlayingTrickComponentRole.SIDE_SUIT,
    ) for i, holding in enumerate(holdings)
      for value in (approved_playing_tricks(holding),))
    missing = sum(x.approved_value is None for x in observations)
    known = sum(x.approved_value for x in observations if x.approved_value is not None)
    return PlayingTrickRoute3Case(
        hand.serialize(), facts.hcp, facts.suit_lengths, SUITS[primary], observations,
        known, missing, True, missing == 0, known >= 8.5 if missing == 0 else None)


def _validate_table() -> None:
    for entry in _APPROVED_TABLE:
        length = 6 if entry.length_scope == "exactly 6" else 3
        item = _holding_class(length, entry.honor_pattern)
        if item is None or item.approved_value != entry.value:
            raise ValueError("Phase 29S approved playing-trick table changed")
    if any(approved_playing_tricks(x) is not None for x in ("", "2", "23", "234", "AKQ2345")):
        raise ValueError("Phase 29S unknown component semantics changed")


@lru_cache(maxsize=1)
def audit_nisim_nily_playing_trick_dependency() -> PlayingTrickDependencyAudit:
    """Exhaustively enumerate legal Route-3 rank/length classes, not deals."""
    completion = complete_nisim_nily_opening_binding()
    if (completion.completion_version != "30O.1" or
            completion.remaining_dependency_gap_ids != ("strong.playing_trick_route",)):
        raise ValueError("Phase 30O Route-3 dependency changed unexpectedly")
    route = completion.binding("strong_hand_precedence")
    params = dict(route.parameters)
    if (params.get("route3_hcp_range"), params.get("route3_closed_suit"),
        params.get("route3_max_other_suit_length"),
        params.get("route3_min_playing_tricks")) != ("17-21", "AKQxxx+", 3, "8.5"):
        raise ValueError("Phase 30O Route-3 contract changed unexpectedly")
    _validate_table()
    primary_options = {n: _options(n, True) for n in range(6, 14)}
    side_options = {n: _options(n, False) for n in range(4)}
    class_count: Counter[str] = Counter()
    class_details: dict[str, tuple[PlayingTrickComponentRole, _HoldingClass]] = {}
    witness_hands: dict[str, str] = {}
    fully_evaluable_witnesses: dict[bool, str] = {}
    population = fully = 0
    for primary_length in range(6, 14):
        for side_lengths in product(range(4), repeat=3):
            if sum(side_lengths) != 13 - primary_length:
                continue
            for primary in primary_options[primary_length]:
                for sides in product(*(side_options[n] for n in side_lengths)):
                    items = (primary,) + sides
                    hcp = sum(x.hcp for x in items)
                    if not 17 <= hcp <= 21:
                        continue
                    population += 1
                    if all(x.approved_value is not None for x in items):
                        fully += 1
                        meets_threshold = sum(x.approved_value for x in items) >= 8.5
                        fully_evaluable_witnesses.setdefault(
                            meets_threshold, ".".join(x.holding or "-" for x in items))
                    hand = None
                    for i, item in enumerate(items):
                        role = (PlayingTrickComponentRole.PRIMARY_CLOSED_SUIT if i == 0
                                else PlayingTrickComponentRole.SIDE_SUIT)
                        key = _class_id(role, item.length, item.pattern)
                        class_count[key] += 1
                        class_details[key] = (role, item)
                        if key not in witness_hands:
                            if hand is None:
                                hand = ".".join(x.holding or "-" for x in items)
                            witness_hands[key] = hand
    classes = tuple(PlayingTrickComponentClass(
        key, class_details[key][0], class_details[key][1].length,
        class_details[key][1].pattern, (class_details[key][1].holding or "-",),
        class_count[key], class_details[key][1].approved_value,
        PlayingTrickComponentStatus.APPROVED_VALUE
        if class_details[key][1].approved_value is not None
        else PlayingTrickComponentStatus.MISSING_VALUE,
        class_details[key][1].approved_value is None,
    ) for key in sorted(class_count))
    def summarize(role: PlayingTrickComponentRole) -> tuple[PlayingTrickLengthSummary, ...]:
        return tuple(PlayingTrickLengthSummary(
            role, length, sum(x.occurrence_count for x in group),
            sum(x.occurrence_count for x in group if x.approved_value is not None),
            sum(x.occurrence_count for x in group if x.approved_value is None),
            tuple(sorted(x.honor_pattern for x in group)),
            tuple(sorted(x.representative_holdings[0] for x in group)),
        ) for length in sorted({x.length for x in classes if x.role is role})
          for group in (tuple(x for x in classes if x.role is role and x.length == length),))
    witnesses = tuple(observe_route3_hand(Hand.parse(hand))
                      for hand in sorted(set(witness_hands.values()) |
                                         set(fully_evaluable_witnesses.values())))
    if any(x is None for x in witnesses):
        raise AssertionError("static Route-3 witness failed canonical hand validation")
    missing = tuple(x for x in classes if x.requires_new_authority)
    requests = tuple(PlayingTrickDecisionRequest(
        x.dependency_id, x.role, x.length, x.honor_pattern,
        x.representative_holdings,
        "This legal Route-3 component is None in the approved Phase 29S table; no total or threshold can be decided until it has approved authority.",
        ("Short holdings use only named Phase 29S honor-pattern values; exact AKQxxx is 6.0.",),
    ) for x in missing)
    return PlayingTrickDependencyAudit(
        completion.profile_id, completion.profile_version, completion.base_system,
        "30O", completion.completion_version, 17, 21, 6, "AKQ", 3, 8.5,
        _APPROVED_TABLE,
        "Exhaustive legal honor-pattern/suit-length class combinations, primary fixed to spades by suit symmetry; one canonical spot-rank representative per class combination; occurrences count component appearances, not deals.",
        population, fully, population - fully, classes,
        summarize(PlayingTrickComponentRole.PRIMARY_CLOSED_SUIT),
        summarize(PlayingTrickComponentRole.SIDE_SUIT), witnesses, requests,
    )
