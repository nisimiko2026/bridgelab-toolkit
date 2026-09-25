"""Typed Phase 30N Nisim–Nily decisions; declarative partnership evidence only."""

from __future__ import annotations

from dataclasses import dataclass
import json

from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .system_profiles import SystemProfile


@dataclass(frozen=True, slots=True)
class StrongTwoClubRoute:
    route_id: str
    hcp_min: int
    hcp_max: int | None
    suit_minimum: int | None
    qualifying_honor_patterns: tuple[str, ...]
    maximum_other_suit_length: int | None
    minimum_playing_tricks: float | None
    requires_approved_component_values: bool = False

    def to_dict(self) -> dict:
        return {
            "route_id": self.route_id, "hcp_min": self.hcp_min,
            "hcp_max": self.hcp_max, "suit_minimum": self.suit_minimum,
            "qualifying_honor_patterns": list(self.qualifying_honor_patterns),
            "maximum_other_suit_length": self.maximum_other_suit_length,
            "minimum_playing_tricks": self.minimum_playing_tricks,
            "requires_approved_component_values": self.requires_approved_component_values,
        }


_ROUTES = (
    StrongTwoClubRoute("23_plus_hcp", 23, None, None, (), None, None),
    StrongTwoClubRoute("exact_22_strong_suit", 22, 22, 5,
                       ("AK", "AQ", "KQ", "KJT"), None, None),
    StrongTwoClubRoute("route3_closed_suit", 17, 21, 6,
                       ("AKQ",), 3, 8.5, True),
)

_ALLOWED_SHAPES = ((4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2),
                   (5, 4, 2, 2), (6, 3, 2, 2))
_EXCLUDED_SHAPES = ((5, 4, 3, 1), (6, 3, 3, 1))


@dataclass(frozen=True, slots=True)
class NisimNilyOpeningDecisionContract:
    profile_id: str = NISIM_NILY_PROFILE.profile_id
    profile_version: str = NISIM_NILY_PROFILE.version
    base_system: SystemProfile = SystemProfile.TWO_OVER_ONE_GF
    decision_version: str = "30N.1"
    minor_club_minimum: int = 3
    minor_diamond_minimum: int = 3
    unequal_minor_rule: str = "longer_minor"
    equal_minor_3_3_call: str = "1C"
    equal_minor_4_4_call: str = "1D"
    equal_minor_5_5_call: str = "1D"
    equal_minor_6_6_call: str = "1D"
    six_major_five_minor_call_family: str = "major"
    one_notrump_allowed_shapes: tuple[tuple[int, int, int, int], ...] = _ALLOWED_SHAPES
    one_notrump_excluded_shapes: tuple[tuple[int, int, int, int], ...] = _EXCLUDED_SHAPES
    one_notrump_five_card_major_allowed: bool = True
    one_notrump_5422_both_majors_excluded: bool = True
    one_notrump_6322_six_suit_must_be_minor: bool = True
    one_notrump_exact_nine_major_cards_excluded: bool = True
    strong_two_club_routes: tuple[StrongTwoClubRoute, ...] = _ROUTES
    strong_two_club_vs_strong_minor_precedence: str = "2C"
    approved_one_notrump_precedes_ordinary_one_level: bool = True
    strong_two_club_precedes_one_notrump: bool = True
    exact_six_minor_rule20_preserved: bool = True
    authority: str = "NISIM_NILY_PARTNERSHIP_DECISION"
    phase: str = "30N"
    status: str = "APPROVED"
    approval_provenance: str = "User-approved Phase 30N decisions supplied in the Phase 30O brief"
    production_adopted: bool = False

    def __post_init__(self) -> None:
        # This contract represents one specific approval, not a configurable
        # system-wide set of defaults. Reject altered decisions fail-closed.
        if (self.profile_id, self.profile_version, self.base_system) != (
            NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
            SystemProfile.TWO_OVER_ONE_GF,
        ):
            raise ValueError("decision contract requires canonical Nisim–Nily identity")
        if (self.decision_version, self.authority, self.phase, self.status) != (
            "30N.1", "NISIM_NILY_PARTNERSHIP_DECISION", "30N", "APPROVED",
        ):
            raise ValueError("Phase 30N approval identity changed")
        if (self.minor_club_minimum, self.minor_diamond_minimum,
            self.unequal_minor_rule,
            self.equal_minor_3_3_call, self.equal_minor_4_4_call,
            self.equal_minor_5_5_call, self.equal_minor_6_6_call,
            self.six_major_five_minor_call_family) != (
            3, 3, "longer_minor", "1C", "1D", "1D", "1D", "major",
        ):
            raise ValueError("Phase 30N minor or major decision changed")
        if (self.one_notrump_allowed_shapes, self.one_notrump_excluded_shapes,
            self.one_notrump_five_card_major_allowed,
            self.one_notrump_5422_both_majors_excluded,
            self.one_notrump_6322_six_suit_must_be_minor,
            self.one_notrump_exact_nine_major_cards_excluded) != (
            _ALLOWED_SHAPES, _EXCLUDED_SHAPES, True, True, True, True,
        ):
            raise ValueError("Phase 30N notrump shape decision changed")
        if (self.strong_two_club_routes,
            self.strong_two_club_vs_strong_minor_precedence,
            self.approved_one_notrump_precedes_ordinary_one_level,
            self.strong_two_club_precedes_one_notrump,
            self.exact_six_minor_rule20_preserved) != (
            _ROUTES, "2C", True, True, True,
        ):
            raise ValueError("Phase 30N strong or precedence decision changed")
        if not self.approval_provenance or self.production_adopted:
            raise ValueError("approval provenance required; production cannot be activated")

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "decision_version": self.decision_version,
            "minor_club_minimum": self.minor_club_minimum,
            "minor_diamond_minimum": self.minor_diamond_minimum,
            "unequal_minor_rule": self.unequal_minor_rule,
            "equal_minor_3_3_call": self.equal_minor_3_3_call,
            "equal_minor_4_4_call": self.equal_minor_4_4_call,
            "equal_minor_5_5_call": self.equal_minor_5_5_call,
            "equal_minor_6_6_call": self.equal_minor_6_6_call,
            "six_major_five_minor_call_family": self.six_major_five_minor_call_family,
            "one_notrump_allowed_shapes": [list(x) for x in self.one_notrump_allowed_shapes],
            "one_notrump_excluded_shapes": [list(x) for x in self.one_notrump_excluded_shapes],
            "one_notrump_five_card_major_allowed": self.one_notrump_five_card_major_allowed,
            "one_notrump_5422_both_majors_excluded": self.one_notrump_5422_both_majors_excluded,
            "one_notrump_6322_six_suit_must_be_minor": self.one_notrump_6322_six_suit_must_be_minor,
            "one_notrump_exact_nine_major_cards_excluded": self.one_notrump_exact_nine_major_cards_excluded,
            "strong_two_club_routes": [x.to_dict() for x in self.strong_two_club_routes],
            "strong_two_club_vs_strong_minor_precedence": self.strong_two_club_vs_strong_minor_precedence,
            "approved_one_notrump_precedes_ordinary_one_level":
                self.approved_one_notrump_precedes_ordinary_one_level,
            "strong_two_club_precedes_one_notrump": self.strong_two_club_precedes_one_notrump,
            "exact_six_minor_rule20_preserved": self.exact_six_minor_rule20_preserved,
            "authority": self.authority, "phase": self.phase, "status": self.status,
            "approval_provenance": self.approval_provenance,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))


def build_nisim_nily_opening_decision_contract() -> NisimNilyOpeningDecisionContract:
    """Return the exact user-approved Phase 30N partnership decisions."""
    return NisimNilyOpeningDecisionContract()
