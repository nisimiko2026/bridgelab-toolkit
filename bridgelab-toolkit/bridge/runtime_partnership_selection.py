"""Typed table-side profile selection for shadow and future runtime use.

Selection depends only on the acting Seat. It does not route bids, evaluate
agreements, choose a base-system fallback, or activate production bidding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .auction import Auction
from .models import Hand, Seat, Vulnerability
from .profile_compiler import CompiledProfilePlan
from .profile_opening_adapter import (
    ProfileOpeningAssessment,
    evaluate_profile_opening_shadow,
)
from .system_profiles import SystemProfile


class PartnershipSide(str, Enum):
    NS = "NS"
    EW = "EW"


def partnership_side_for_seat(seat: Seat) -> PartnershipSide:
    """Return the canonical two-seat partnership containing ``seat``."""
    if not isinstance(seat, Seat):
        raise TypeError("seat must be Seat")
    return PartnershipSide.NS if seat in (Seat.NORTH, Seat.SOUTH) else PartnershipSide.EW


def _selection_version(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("selection_version must be a string")
    value = value.strip()
    if not value:
        raise ValueError("selection_version must not be blank")
    return value


@dataclass(frozen=True, slots=True)
class TablePartnershipPlans:
    ns_plan: CompiledProfilePlan
    ew_plan: CompiledProfilePlan
    selection_version: str = "30E.1"
    production_adopted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.ns_plan, CompiledProfilePlan):
            raise TypeError("ns_plan must be CompiledProfilePlan")
        if not isinstance(self.ew_plan, CompiledProfilePlan):
            raise TypeError("ew_plan must be CompiledProfilePlan")
        object.__setattr__(self, "selection_version", _selection_version(self.selection_version))
        if self.production_adopted is not False:
            raise ValueError("Phase 30E table is not adopted by production")

    def to_dict(self) -> dict:
        return {
            "ns_plan": self.ns_plan.to_dict(),
            "ew_plan": self.ew_plan.to_dict(),
            "selection_version": self.selection_version,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class RuntimeProfileSelection:
    seat: Seat
    side: PartnershipSide
    plan: CompiledProfilePlan
    selection_version: str = "30E.1"
    production_adopted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.seat, Seat):
            raise TypeError("seat must be Seat")
        if not isinstance(self.side, PartnershipSide) or self.side is not partnership_side_for_seat(self.seat):
            raise ValueError("side must be the canonical partnership of seat")
        if not isinstance(self.plan, CompiledProfilePlan):
            raise TypeError("plan must be CompiledProfilePlan")
        object.__setattr__(self, "selection_version", _selection_version(self.selection_version))
        if self.production_adopted is not False:
            raise ValueError("Phase 30E selection is not adopted by production")

    @property
    def profile_id(self) -> str:
        return self.plan.profile_id

    @property
    def profile_version(self) -> str:
        return self.plan.profile_version

    @property
    def base_system(self) -> SystemProfile:
        return self.plan.base_system

    def to_dict(self) -> dict:
        return {
            "seat": self.seat.value,
            "side": self.side.value,
            "plan": self.plan.to_dict(),
            "selection_version": self.selection_version,
            "production_adopted": self.production_adopted,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def select_runtime_profile(
    table: TablePartnershipPlans, seat: Seat
) -> RuntimeProfileSelection:
    """Select a compiled plan solely from canonical seat membership."""
    if not isinstance(table, TablePartnershipPlans):
        raise TypeError("table must be TablePartnershipPlans")
    side = partnership_side_for_seat(seat)
    plan = table.ns_plan if side is PartnershipSide.NS else table.ew_plan
    return RuntimeProfileSelection(seat, side, plan, table.selection_version)


def select_runtime_profile_for_auction(
    table: TablePartnershipPlans, auction: Auction
) -> RuntimeProfileSelection:
    """Select the next bidder's side in any live auction, including competitive play."""
    if not isinstance(table, TablePartnershipPlans):
        raise TypeError("table must be TablePartnershipPlans")
    if not isinstance(auction, Auction):
        raise TypeError("auction must be Auction")
    if auction.is_complete:
        raise ValueError("completed auction has no acting seat")
    return select_runtime_profile(table, auction.next_seat)


@dataclass(frozen=True, slots=True)
class SelectedProfileOpeningAssessment:
    selection: RuntimeProfileSelection
    assessment: ProfileOpeningAssessment
    production_adopted: bool = False
    adapter_version: str = "30E.1"

    def __post_init__(self) -> None:
        if not isinstance(self.selection, RuntimeProfileSelection):
            raise TypeError("selection must be RuntimeProfileSelection")
        if not isinstance(self.assessment, ProfileOpeningAssessment):
            raise TypeError("assessment must be ProfileOpeningAssessment")
        if self.selection.seat is not self.assessment.acting_seat or (
            self.selection.profile_id,
            self.selection.profile_version,
            self.selection.base_system,
        ) != (
            self.assessment.profile_id,
            self.assessment.profile_version,
            self.assessment.base_system,
        ):
            raise ValueError("opening assessment must belong to the selected plan and seat")
        if self.production_adopted is not False:
            raise ValueError("Phase 30E composition is not adopted by production")

    def to_dict(self) -> dict:
        return {
            "selection": self.selection.to_dict(),
            "assessment": self.assessment.to_dict(),
            "production_adopted": self.production_adopted,
            "adapter_version": self.adapter_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def evaluate_selected_profile_opening_shadow(
    table: TablePartnershipPlans,
    *,
    hand: Hand,
    auction: Auction,
    vulnerability: Vulnerability,
) -> SelectedProfileOpeningAssessment:
    """Explicitly compose selection with 30C, preserving its opening-only guard."""
    selection = select_runtime_profile_for_auction(table, auction)
    assessment = evaluate_profile_opening_shadow(
        selection.plan, hand=hand, auction=auction, vulnerability=vulnerability
    )
    return SelectedProfileOpeningAssessment(selection, assessment)


@dataclass(frozen=True, slots=True)
class RuntimePartnershipSelectionCapability:
    """Scope-limited status of this typed infrastructure, not production readiness."""

    phase: str = "30E"
    selection_version: str = "30E.1"
    typed_table_assignment: bool = True
    seat_selection: bool = True
    auction_next_seat_selection: bool = True
    partnership_isolation: bool = True
    runtime_selection_ready: bool = True
    production_bidding_changed: bool = False
    production_adopted: bool = False
    production_result_adapter_ready: bool = False
    base_system_fallback_contract_ready: bool = False

    def __post_init__(self) -> None:
        if self.production_adopted is not False or self.production_bidding_changed is not False:
            raise ValueError("Phase 30E cannot claim production adoption or bidding change")
        if self.production_result_adapter_ready is not False or self.base_system_fallback_contract_ready is not False:
            raise ValueError("Phase 30E does not solve the production adapter or base fallback")

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "selection_version": self.selection_version,
            "typed_table_assignment": self.typed_table_assignment,
            "seat_selection": self.seat_selection,
            "auction_next_seat_selection": self.auction_next_seat_selection,
            "partnership_isolation": self.partnership_isolation,
            "runtime_selection_ready": self.runtime_selection_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "production_result_adapter_ready": self.production_result_adapter_ready,
            "base_system_fallback_contract_ready": self.base_system_fallback_contract_ready,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
