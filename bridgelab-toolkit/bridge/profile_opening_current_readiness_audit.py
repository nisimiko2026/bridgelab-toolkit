"""Phase 30F current production-readiness audit after typed table-side selection.

Historical Phase 30D remains a snapshot. This module rechecks current shadow
and production witnesses and records changes without activating bidding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .models import Hand, Seat, Vulnerability
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .nisim_nily_six_minor_preempt_policy import SixMinorDecision, assess_six_minor_three_level_preempt
from .partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from .profile_compiler import CompiledProfilePlan, compile_profile_plan
from .profile_opening_adapter import ProfileOpeningDisposition, evaluate_profile_opening_shadow
from .profile_opening_production_gate import (
    ProductionReadinessGate,
    ProductionReadinessState,
    build_profile_opening_production_gate_audit,
)
from .runtime_partnership_selection import (
    PartnershipSide,
    RuntimePartnershipSelectionCapability,
    TablePartnershipPlans,
    evaluate_selected_profile_opening_shadow,
    select_runtime_profile,
    select_runtime_profile_for_auction,
)
from .sayc_route_configuration import create_standard_sayc_router
from .system_profiles import SystemProfile, classify_system_profile
from .treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING, bind_compiled_directive


_FAMILY = "opening.three_level.six_minor"
_ROUTE_MARKERS = ("nisim", "30a", "30b", "30c", "30d", "30e", "30f")


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


@dataclass(frozen=True, slots=True)
class CurrentGateTransition:
    gate_id: str
    phase30d_state: ProductionReadinessState
    phase30f_state: ProductionReadinessState
    reason: str
    changed: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _nonblank(self.gate_id, "gate_id"))
        if not isinstance(self.phase30d_state, ProductionReadinessState):
            raise TypeError("phase30d_state must be ProductionReadinessState")
        if not isinstance(self.phase30f_state, ProductionReadinessState):
            raise TypeError("phase30f_state must be ProductionReadinessState")
        object.__setattr__(self, "reason", _nonblank(self.reason, "reason"))
        object.__setattr__(self, "changed", self.phase30d_state is not self.phase30f_state)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "phase30d_state": self.phase30d_state.value,
            "phase30f_state": self.phase30f_state.value,
            "changed": self.changed,
            "reason": self.reason,
        }


def _required_gates_ready(gates: tuple[ProductionReadinessGate, ...]) -> bool:
    return all(
        gate.state is ProductionReadinessState.READY
        for gate in gates if gate.required_for_production
    )


def _recommended_next_phase(gates: tuple[ProductionReadinessGate, ...]) -> str:
    states = {gate.gate_id: gate.state for gate in gates}
    blocked_priorities = (
        ("runtime_partnership_selection", "30G_RUNTIME_PARTNERSHIP_SELECTION"),
        ("base_system_fallback_contract", "30G_BASE_SYSTEM_COMPOSITION"),
        ("production_result_adapter", "30G_PRODUCTION_RESULT_ADAPTER"),
    )
    for gate_id, next_phase in blocked_priorities:
        if states.get(gate_id) is ProductionReadinessState.BLOCKED:
            return next_phase
    if states.get("first_seat_precedence") is not ProductionReadinessState.READY:
        return "30G_PROFILE_AWARE_OPENING_PRECEDENCE"
    if states.get("later_seat_opening_dispatch") is not ProductionReadinessState.READY:
        return "30G_LATER_SEAT_OPENING_DISPATCH"
    if _required_gates_ready(gates):
        return "30G_PRODUCTION_PILOT"
    return "30G_PRODUCTION_INTEGRATION_REMEDIATION"


@dataclass(frozen=True, slots=True)
class CurrentProfileOpeningReadinessAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    gates: tuple[ProductionReadinessGate, ...]
    transitions_from_30d: tuple[CurrentGateTransition, ...]
    first_seat_shadow_call: str | None
    first_seat_production_call: str | None
    third_seat_shadow_call: str | None
    third_seat_production_route_id: str | None
    route_count: int
    production_changed: bool
    phase: str = "30F"
    historical_phase: str = "30D"
    audit_version: str = "30F.1"
    runtime_selection_ready: bool = field(init=False)
    ready_for_production: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonblank(self.profile_id, "profile_id"))
        object.__setattr__(self, "profile_version", _nonblank(self.profile_version, "profile_version"))
        if not isinstance(self.base_system, SystemProfile):
            raise TypeError("base_system must be SystemProfile")
        if not isinstance(self.gates, tuple) or not all(
            isinstance(gate, ProductionReadinessGate) for gate in self.gates
        ):
            raise TypeError("gates must be a tuple of ProductionReadinessGate")
        keys = [gate.gate_id.casefold() for gate in self.gates]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate current gate IDs")
        gates = tuple(sorted(self.gates, key=lambda gate: (gate.gate_id.casefold(), gate.gate_id)))
        object.__setattr__(self, "gates", gates)
        if not isinstance(self.transitions_from_30d, tuple) or not all(
            isinstance(item, CurrentGateTransition) for item in self.transitions_from_30d
        ):
            raise TypeError("transitions_from_30d must contain CurrentGateTransition")
        transitions = tuple(sorted(
            self.transitions_from_30d, key=lambda item: (item.gate_id.casefold(), item.gate_id)
        ))
        transition_keys = [item.gate_id.casefold() for item in transitions]
        if len(transition_keys) != len(set(transition_keys)):
            raise ValueError("duplicate transition gate IDs")
        if set(keys) != set(transition_keys):
            raise ValueError("transitions must cover exactly the current gate set")
        current = {gate.gate_id.casefold(): gate.state for gate in gates}
        if any(item.phase30f_state is not current[item.gate_id.casefold()] for item in transitions):
            raise ValueError("transition current state must match current gate")
        object.__setattr__(self, "transitions_from_30d", transitions)
        states = {gate.gate_id: gate.state for gate in gates}
        object.__setattr__(
            self, "runtime_selection_ready",
            states.get("runtime_partnership_selection") is ProductionReadinessState.READY,
        )
        object.__setattr__(self, "ready_for_production", _required_gates_ready(gates))
        object.__setattr__(self, "recommended_next_phase", _recommended_next_phase(gates))

    def gate(self, gate_id: str) -> ProductionReadinessGate | None:
        key = _nonblank(gate_id, "gate_id").casefold()
        return next((gate for gate in self.gates if gate.gate_id.casefold() == key), None)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "historical_phase": self.historical_phase,
            "audit_version": self.audit_version,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "gates": [gate.to_dict() for gate in self.gates],
            "transitions_from_30d": [item.to_dict() for item in self.transitions_from_30d],
            "first_seat_shadow_call": self.first_seat_shadow_call,
            "first_seat_production_call": self.first_seat_production_call,
            "third_seat_shadow_call": self.third_seat_shadow_call,
            "third_seat_production_route_id": self.third_seat_production_route_id,
            "runtime_selection_ready": self.runtime_selection_ready,
            "route_count": self.route_count,
            "production_changed": self.production_changed,
            "ready_for_production": self.ready_for_production,
            "recommended_next_phase": self.recommended_next_phase,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _production_call(router, context: BiddingContext) -> str | None:
    result = router.evaluate(context)
    return None if result.recommended_call is None else result.recommended_call.serialize()


def build_current_profile_opening_readiness_audit() -> CurrentProfileOpeningReadinessAudit:
    """Recheck current 30E selection and production behavior against 30D history."""
    before_router = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before_router.routes)
    history = build_profile_opening_production_gate_audit()
    historical_json = history.to_json()

    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE)
    ns_plan = compile_profile_plan(resolved)
    ns_plan_json = ns_plan.to_json()
    profile_json = NISIM_NILY_PROFILE.to_json()
    peer = PartnershipProfile(
        "phase30f-peer", "30F.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    ew_plan = compile_profile_plan(resolve_partnership_profile(peer))
    table = TablePartnershipPlans(ns_plan, ew_plan)
    capability = RuntimePartnershipSelectionCapability()

    seat_expectations = (
        (Seat.NORTH, PartnershipSide.NS, ns_plan),
        (Seat.EAST, PartnershipSide.EW, ew_plan),
        (Seat.SOUTH, PartnershipSide.NS, ns_plan),
        (Seat.WEST, PartnershipSide.EW, ew_plan),
    )
    seat_selection = all(
        select_runtime_profile(table, seat).side is side
        and select_runtime_profile(table, seat).plan is plan
        for seat, side, plan in seat_expectations
    )
    auction_selection = all(
        select_runtime_profile_for_auction(table, Auction(Seat.NORTH, calls)).plan is plan
        for calls, plan in (
            ((), ns_plan), (("P",), ew_plan), (("P", "P"), ns_plan),
            (("P", "P", "P"), ew_plan), (("1C",), ew_plan),
            (("1C", "P"), ns_plan), (("1C", "P", "1H"), ew_plan),
        )
    )
    reversed_table = TablePartnershipPlans(ew_plan, ns_plan)
    side_independent_of_profile_name = (
        select_runtime_profile(reversed_table, Seat.NORTH).plan is ew_plan
        and select_runtime_profile(reversed_table, Seat.EAST).plan is ns_plan
    )
    repeat_selection = (
        select_runtime_profile(table, Seat.NORTH).to_json()
        == select_runtime_profile(table, Seat.NORTH).to_json()
        and table.to_json() == TablePartnershipPlans(ns_plan, ew_plan).to_json()
    )
    runtime_ready = (
        isinstance(ns_plan, CompiledProfilePlan)
        and isinstance(ew_plan, CompiledProfilePlan)
        and capability.runtime_selection_ready is True
        and capability.typed_table_assignment is True
        and capability.seat_selection is True
        and capability.auction_next_seat_selection is True
        and capability.partnership_isolation is True
        and table.production_adopted is False
        and seat_selection and auction_selection and side_independent_of_profile_name
        and repeat_selection
    )

    hand = Hand.parse("7.84.KQJT96.9742")
    first_auction = Auction(Seat.NORTH)
    third_auction = Auction(Seat.NORTH, ("P", "P"))
    first = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=first_auction, vulnerability=Vulnerability.EW
    )
    third = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=third_auction, vulnerability=Vulnerability.EW
    )
    peer_opening = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=Auction(Seat.EAST), vulnerability=Vulnerability.EW
    )
    negative = evaluate_profile_opening_shadow(
        ns_plan, hand=Hand.parse("7.84.QJT986.9742"), auction=first_auction,
        vulnerability=Vulnerability.NONE,
    )
    direct = assess_six_minor_three_level_preempt(
        hand, seat=Seat.NORTH, vulnerability=Vulnerability.EW, opening_position=1
    )
    one_level = assess_six_minor_three_level_preempt(
        Hand.parse("7.K4.KQJT96.A742"), seat=Seat.NORTH,
        vulnerability=Vulnerability.EW, opening_position=1,
    )
    seven_card = assess_six_minor_three_level_preempt(
        Hand.parse("7.84.KQJT986.742"), seat=Seat.NORTH,
        vulnerability=Vulnerability.EW, opening_position=1,
    )

    first_context = BiddingContext.create(
        hand=hand, auction=first_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    third_context = BiddingContext.create(
        hand=hand, auction=third_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    first_production_call = _production_call(before_router, first_context)
    third_match = before_router.match(third_context)
    third_route_id = None if third_match is None else third_match.route_id
    third_production_call = _production_call(before_router, third_context)
    if first_production_call != "2D" or third_route_id is not None or third_production_call is not None:
        raise RuntimeError("Phase 30F production witness drifted from the historical baseline")

    directive = ns_plan.directive(_FAMILY)
    binding = None if directive is None else bind_compiled_directive(directive)
    policy_ready = (
        direct.decision is SixMinorDecision.THREE_LEVEL
        and one_level.decision is SixMinorDecision.ONE_LEVEL
        and negative.policy_assessment.decision is SixMinorDecision.NO_THREE_LEVEL
        and seven_card.decision is SixMinorDecision.NOT_APPLICABLE
        and direct.production_adopted is False
    )
    isolated = (
        ns_plan.base_system is ew_plan.base_system is SystemProfile.TWO_OVER_ONE_GF
        and peer_opening.selection.plan is ew_plan
        and peer_opening.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
        and peer_opening.assessment.supported_call is None
    )
    separated = isinstance(NISIM_NILY_PROFILE, PartnershipProfile) and isolated
    typed_model = isinstance(resolved, ResolvedBiddingProfile) and isinstance(ns_plan, CompiledProfilePlan)
    compiled = (
        directive is not None
        and directive.effective_treatment_id == NISIM_NILY_SIX_MINOR_BINDING.treatment_id
        and ns_plan.to_json() == compile_profile_plan(resolved).to_json()
    )
    bound = binding == NISIM_NILY_SIX_MINOR_BINDING and binding.production_adopted is False
    first_shadow_ready = (
        first.selection.plan is ns_plan
        and first.assessment.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
        and first.assessment.supported_call == "3D"
        and first.assessment.policy_assessment == direct
        and first.production_adopted is False
        and first.assessment.production_adopted is False
    )
    third_shadow_ready = (
        third.selection.plan is ns_plan
        and third.selection.seat is Seat.SOUTH
        and third.assessment.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
        and third.assessment.supported_call == "3D"
        and third.production_adopted is False
    )
    pass_safe = (
        negative.disposition is ProfileOpeningDisposition.ABSTAIN
        and negative.supported_call is None
        and peer_opening.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
        and peer_opening.assessment.supported_call is None
    )
    correct_base_distinct_from_sayc = (
        ns_plan.base_system is SystemProfile.TWO_OVER_ONE_GF
        and classify_system_profile(SystemContext("SAYC")) is SystemProfile.SAYC
    )
    after_router = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after_router.routes)
    production_changed = before_ids != after_ids or capability.production_bidding_changed
    context_shape = (
        tuple(item.name for item in fields(SystemContext)) == ("system", "options")
        and tuple(item.name for item in fields(BiddingContext))
        == ("hand", "evaluation", "auction", "seat", "vulnerability", "system")
    )
    regression_guard = (
        len(before_ids) == len(after_ids) == 45
        and before_ids == after_ids and not production_changed and context_shape
        and not any(marker in route_id.casefold() for route_id in after_ids
                    for marker in _ROUTE_MARKERS)
    )

    ready = ProductionReadinessState.READY
    shadow = ProductionReadinessState.SHADOW_READY
    blocked = ProductionReadinessState.BLOCKED
    # A production result adapter and an approved 2/1 continuation are still
    # absent. The 30E status explicitly limits itself to table-side selection.
    findings = {
        "policy_semantics": (
            ready if policy_ready else blocked,
            "Current Phase 29T evaluator still covers the four pilot decisions.",
            ("29T:THREE_LEVEL/ONE_LEVEL/NO_THREE_LEVEL/NOT_APPLICABLE",),
        ),
        "system_partnership_separation": (
            ready if separated else blocked,
            "Nisim–Nily remains a partnership profile with a distinct 2/1 base.",
            ("29X:PartnershipProfile", "30E:same-system table isolation"),
        ),
        "typed_partnership_profile": (
            ready if typed_model else blocked,
            "Typed partnership and resolved profile models remain available.",
            ("29X:ResolvedBiddingProfile",),
        ),
        "profile_compilation": (
            ready if compiled else blocked,
            "Phase 30A still deterministically exposes the effective pilot directive.",
            ("30A:CompiledProfilePlan.directive",),
        ),
        "treatment_binding": (
            shadow if bound else blocked,
            "The exact Phase 30B binding remains shadow-only.",
            ("30B:bind_compiled_directive", "30B:production_adopted=False"),
        ),
        "opening_context_adapter": (
            shadow if first_shadow_ready and third_shadow_ready else blocked,
            "Phase 30C still assesses first and third seat without production wiring.",
            ("30C:first=3D", "30C:third=3D", "30C:production_adopted=False"),
        ),
        "runtime_partnership_selection": (
            ready if runtime_ready else blocked,
            "Phase 30E selects immutable compiled plans by acting table side in live auctions.",
            ("30E:NS/EW typed table", "30E:Seat and Auction.next_seat selection",
             "30E:reversed table and same-system isolation"),
        ),
        "first_seat_precedence": (
            shadow if first_shadow_ready else blocked,
            "Selected shadow profile supports 3D; standard production still recommends 2D.",
            (f"shadow={first.assessment.supported_call}", f"production={first_production_call}"),
        ),
        "later_seat_opening_dispatch": (
            shadow if third_shadow_ready else blocked,
            "Selected shadow profile supports 3D after P P; production has no route or call.",
            (f"shadow={third.assessment.supported_call}",
             f"production route={third_route_id}", f"production call={third_production_call}"),
        ),
        "production_result_adapter": (
            blocked if capability.production_result_adapter_ready is False else ready,
            "No approved conversion from profile opening assessment to production recommendation exists.",
            ("30E:production_result_adapter_ready=False",),
        ),
        "base_system_fallback_contract": (
            ready if capability.base_system_fallback_contract_ready and correct_base_distinct_from_sayc else blocked,
            "No approved 2/1 continuation after ABSTAIN or NO_BINDING; SAYC is distinct.",
            ("30E:base_system_fallback_contract_ready=False",
             f"TWO_OVER_ONE_GF distinct from SAYC={correct_base_distinct_from_sayc}"),
        ),
        "no_pass_inference": (
            ready if pass_safe else blocked,
            "ABSTAIN and NO_BINDING remain distinct and neither manufactures Pass.",
            ("30C:ABSTAIN=None", "30C:NO_BINDING=None"),
        ),
        "partnership_isolation": (
            ready if isolated else blocked,
            "The same-system peer selected through 30E has no six-minor binding.",
            ("30E:EW peer selected", "30C:peer=NO_BINDING"),
        ),
        "production_regression_guard": (
            ready if regression_guard else blocked,
            "The audit preserves ordered production routes and context shapes.",
            (f"routes before={len(before_ids)} after={len(after_ids)}",
             f"ordered inventory equal={before_ids == after_ids}",
             f"context fields unchanged={context_shape}"),
        ),
    }
    historical_by_id = {gate.gate_id: gate for gate in history.gates}
    if set(findings) != set(historical_by_id):
        raise RuntimeError("current gate set differs from historical Phase 30D")
    gates = tuple(
        ProductionReadinessGate(gate_id, state, historical_by_id[gate_id].required_for_production,
                                evidence, reason)
        for gate_id, (state, reason, evidence) in findings.items()
    )
    transitions = tuple(
        CurrentGateTransition(gate.gate_id, historical_by_id[gate.gate_id].state,
                              gate.state, gate.reason)
        for gate in gates
    )
    if history.to_json() != historical_json or NISIM_NILY_PROFILE.to_json() != profile_json or ns_plan.to_json() != ns_plan_json:
        raise RuntimeError("Phase 30F audit mutated historical or source profile data")
    return CurrentProfileOpeningReadinessAudit(
        profile_id=ns_plan.profile_id,
        profile_version=ns_plan.profile_version,
        base_system=ns_plan.base_system,
        gates=gates,
        transitions_from_30d=transitions,
        first_seat_shadow_call=first.assessment.supported_call,
        first_seat_production_call=first_production_call,
        third_seat_shadow_call=third.assessment.supported_call,
        third_seat_production_route_id=third_route_id,
        route_count=len(after_ids),
        production_changed=production_changed,
    )
