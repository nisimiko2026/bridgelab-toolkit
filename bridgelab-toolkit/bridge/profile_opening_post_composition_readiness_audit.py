"""Phase 30H current readiness audit after shadow base-system composition.

This module observes 30E/30C/30G and the existing standard production router.
It neither executes a base continuation nor activates profile-aware bidding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields

from .auction import Auction
from .base_system_composition import (
    BaseSystemCompositionCapability,
    BaseSystemCompositionDisposition as Composition,
    compose_profile_opening_with_base,
)
from .bidding_rules import BiddingContext, SystemContext
from .models import Hand, Seat, Vulnerability
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .partnership_profiles import (
    AgreementResolution, AgreementSelection, AgreementSourceScope,
    PartnershipProfile, ResolvedAgreement, resolve_partnership_profile,
)
from .profile_compiler import CompilationAction, compile_profile_plan
from .profile_opening_adapter import (
    ProfileOpeningAssessment, ProfileOpeningDisposition,
    evaluate_profile_opening_shadow,
)
from .profile_opening_current_readiness_audit import build_current_profile_opening_readiness_audit
from .profile_opening_production_gate import ProductionReadinessGate, ProductionReadinessState
from .runtime_partnership_selection import (
    PartnershipSide, TablePartnershipPlans, evaluate_selected_profile_opening_shadow,
)
from .sayc_route_configuration import create_standard_sayc_router
from .system_profiles import SystemProfile


_FAMILY = "opening.three_level.six_minor"
_HAND = "7.84.KQJT96.9742"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _required_gates_ready(gates: tuple[ProductionReadinessGate, ...]) -> bool:
    return all(gate.state is ProductionReadinessState.READY
               for gate in gates if gate.required_for_production)


def _recommended_next_phase(gates: tuple[ProductionReadinessGate, ...],
                            base_execution_ready: bool) -> str:
    states = {gate.gate_id: gate.state for gate in gates}
    if states["runtime_partnership_selection"] is ProductionReadinessState.BLOCKED:
        return "30I_RUNTIME_PARTNERSHIP_SELECTION"
    if states["base_system_fallback_contract"] is ProductionReadinessState.BLOCKED:
        return "30I_BASE_SYSTEM_COMPOSITION"
    if (states["base_system_fallback_contract"] is ProductionReadinessState.SHADOW_READY
            and not base_execution_ready):
        return "30I_BASE_SYSTEM_EXECUTION_ADAPTER"
    if states["production_result_adapter"] is ProductionReadinessState.BLOCKED:
        return "30I_PRODUCTION_RESULT_ADAPTER"
    if states["first_seat_precedence"] is not ProductionReadinessState.READY:
        return "30I_PROFILE_AWARE_OPENING_PRECEDENCE"
    if states["later_seat_opening_dispatch"] is not ProductionReadinessState.READY:
        return "30I_LATER_SEAT_OPENING_DISPATCH"
    if _required_gates_ready(gates):
        return "30I_PRODUCTION_PILOT"
    return "30I_PRODUCTION_INTEGRATION_REMEDIATION"


@dataclass(frozen=True, slots=True)
class PostCompositionGateTransition:
    gate_id: str
    phase30f_state: ProductionReadinessState
    phase30h_state: ProductionReadinessState
    reason: str
    changed: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _nonblank(self.gate_id, "gate_id"))
        if not isinstance(self.phase30f_state, ProductionReadinessState):
            raise TypeError("phase30f_state must be ProductionReadinessState")
        if not isinstance(self.phase30h_state, ProductionReadinessState):
            raise TypeError("phase30h_state must be ProductionReadinessState")
        object.__setattr__(self, "reason", _nonblank(self.reason, "reason"))
        object.__setattr__(self, "changed", self.phase30f_state is not self.phase30h_state)

    def to_dict(self) -> dict:
        return {"gate_id": self.gate_id, "phase30f_state": self.phase30f_state.value,
                "phase30h_state": self.phase30h_state.value, "changed": self.changed,
                "reason": self.reason}


@dataclass(frozen=True, slots=True)
class PostCompositionOpeningReadinessAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    gates: tuple[ProductionReadinessGate, ...]
    transitions_from_30f: tuple[PostCompositionGateTransition, ...]
    composition_contract_ready: bool
    base_continuation_request_ready: bool
    base_execution_ready: bool
    first_seat_shadow_call: str | None
    first_seat_production_call: str | None
    third_seat_shadow_call: str | None
    third_seat_production_route_id: str | None
    partnership_composition: str
    add_abstain_composition: str
    add_abstain_base_system: SystemProfile | None
    peer_composition: str
    peer_base_system: SystemProfile | None
    replace_composition: str
    unbound_add_composition: str
    route_count: int
    ordered_route_ids_equal: bool
    production_changed: bool
    production_adopted: bool
    phase: str = "30H"
    historical_phase: str = "30F"
    audit_version: str = "30H.1"
    ready_for_production: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        for name in ("profile_id", "profile_version"):
            object.__setattr__(self, name, _nonblank(getattr(self, name), name))
        if not isinstance(self.base_system, SystemProfile):
            raise TypeError("base_system must be SystemProfile")
        if not isinstance(self.gates, tuple) or not all(
                isinstance(g, ProductionReadinessGate) for g in self.gates):
            raise TypeError("gates must contain ProductionReadinessGate")
        keys = [g.gate_id.casefold() for g in self.gates]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate current gate IDs")
        gates = tuple(sorted(self.gates, key=lambda g: (g.gate_id.casefold(), g.gate_id)))
        object.__setattr__(self, "gates", gates)
        if not isinstance(self.transitions_from_30f, tuple) or not all(
                isinstance(t, PostCompositionGateTransition) for t in self.transitions_from_30f):
            raise TypeError("transitions_from_30f must contain PostCompositionGateTransition")
        transitions = tuple(sorted(self.transitions_from_30f,
                                   key=lambda t: (t.gate_id.casefold(), t.gate_id)))
        transition_keys = [t.gate_id.casefold() for t in transitions]
        if len(transition_keys) != len(set(transition_keys)):
            raise ValueError("duplicate transition gate IDs")
        if set(keys) != set(transition_keys):
            raise ValueError("transitions must cover exactly the current gate set")
        current = {g.gate_id.casefold(): g.state for g in gates}
        if any(t.phase30h_state is not current[t.gate_id.casefold()] for t in transitions):
            raise ValueError("transition current state must match current gate")
        object.__setattr__(self, "transitions_from_30f", transitions)
        object.__setattr__(self, "ready_for_production", _required_gates_ready(gates))
        object.__setattr__(self, "recommended_next_phase",
                           _recommended_next_phase(gates, self.base_execution_ready))

    def gate(self, gate_id: str) -> ProductionReadinessGate | None:
        key = _nonblank(gate_id, "gate_id").casefold()
        return next((g for g in self.gates if g.gate_id.casefold() == key), None)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase, "historical_phase": self.historical_phase,
            "audit_version": self.audit_version, "profile_id": self.profile_id,
            "profile_version": self.profile_version, "base_system": self.base_system.value,
            "gates": [g.to_dict() for g in self.gates],
            "transitions_from_30f": [t.to_dict() for t in self.transitions_from_30f],
            "composition_contract_ready": self.composition_contract_ready,
            "base_continuation_request_ready": self.base_continuation_request_ready,
            "base_execution_ready": self.base_execution_ready,
            "first_seat_shadow_call": self.first_seat_shadow_call,
            "first_seat_production_call": self.first_seat_production_call,
            "third_seat_shadow_call": self.third_seat_shadow_call,
            "third_seat_production_route_id": self.third_seat_production_route_id,
            "partnership_composition": self.partnership_composition,
            "add_abstain_composition": self.add_abstain_composition,
            "add_abstain_base_system": (None if self.add_abstain_base_system is None
                                        else self.add_abstain_base_system.value),
            "peer_composition": self.peer_composition,
            "peer_base_system": None if self.peer_base_system is None else self.peer_base_system.value,
            "replace_composition": self.replace_composition,
            "unbound_add_composition": self.unbound_add_composition,
            "route_count": self.route_count,
            "ordered_route_ids_equal": self.ordered_route_ids_equal,
            "production_changed": self.production_changed,
            "production_adopted": self.production_adopted,
            "ready_for_production": self.ready_for_production,
            "recommended_next_phase": self.recommended_next_phase,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _no_call_assessment(plan, family: str) -> ProfileOpeningAssessment:
    """Structural witness for an unimplemented convention; no policy is evaluated."""
    directive = plan.directive(family)
    return ProfileOpeningAssessment(
        profile_id=plan.profile_id, profile_version=plan.profile_version,
        base_system=plan.base_system, family=family,
        effective_treatment_id=None if directive is None else directive.effective_treatment_id,
        disposition=ProfileOpeningDisposition.NO_BINDING,
        acting_seat=Seat.NORTH, opening_position=1, vulnerability=Vulnerability.EW,
        binding=None, policy_assessment=None, supported_call=None,
        reason="Audit-only structural witness; replacement implementation unavailable.",
    )


def _production_call(router, context: BiddingContext) -> str | None:
    result = router.evaluate(context)
    return None if result.recommended_call is None else result.recommended_call.serialize()


def build_post_composition_opening_readiness_audit() -> PostCompositionOpeningReadinessAudit:
    """Recheck 30G semantic handoffs and compare current gates with Phase 30F."""
    before_router = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before_router.routes)
    history = build_current_profile_opening_readiness_audit()
    historical_json = history.to_json()
    capability = BaseSystemCompositionCapability()
    source_json = NISIM_NILY_PROFILE.to_json()

    ns_plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    plan_json = ns_plan.to_json()
    peer = PartnershipProfile(
        "phase30h-peer", "30H.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    ew_plan = compile_profile_plan(resolve_partnership_profile(peer))
    table = TablePartnershipPlans(ns_plan, ew_plan)
    hand = Hand.parse(_HAND)
    first_auction = Auction(Seat.NORTH)
    third_auction = Auction(Seat.NORTH, ("P", "P"))
    first = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=first_auction, vulnerability=Vulnerability.EW)
    third = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=third_auction, vulnerability=Vulnerability.EW)
    peer_opening = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=Auction(Seat.EAST), vulnerability=Vulnerability.EW)
    first_composed = compose_profile_opening_with_base(first.selection.plan, first.assessment)
    third_composed = compose_profile_opening_with_base(third.selection.plan, third.assessment)
    peer_composed = compose_profile_opening_with_base(peer_opening.selection.plan,
                                                      peer_opening.assessment)
    negative = evaluate_profile_opening_shadow(
        ns_plan, hand=Hand.parse("7.84.QJT986.9742"), auction=first_auction,
        vulnerability=Vulnerability.NONE)
    negative_composed = compose_profile_opening_with_base(ns_plan, negative)

    base_agreements = (ResolvedAgreement(
        "opening.2d", "natural_weak_two", AgreementResolution.ENABLE,
        AgreementSourceScope.SYSTEM),)
    replace_plan = compile_profile_plan(
        resolve_partnership_profile(NISIM_NILY_PROFILE, base_agreements=base_agreements),
        base_agreements=base_agreements)
    replaced = compose_profile_opening_with_base(
        replace_plan, _no_call_assessment(replace_plan, "opening.2d"))
    unbound_profile = PartnershipProfile(
        "phase30h-unbound", "30H.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection(_FAMILY, AgreementResolution.ENABLE,
                            "unimplemented_six_minor"),),
    )
    unbound_plan = compile_profile_plan(resolve_partnership_profile(unbound_profile))
    unbound_assessment = evaluate_profile_opening_shadow(
        unbound_plan, hand=hand, auction=first_auction, vulnerability=Vulnerability.EW)
    unbound = compose_profile_opening_with_base(unbound_plan, unbound_assessment)

    first_context = BiddingContext.create(
        hand=hand, auction=first_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"))
    third_context = BiddingContext.create(
        hand=hand, auction=third_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"))
    first_production_call = _production_call(before_router, first_context)
    third_match = before_router.match(third_context)
    third_route_id = None if third_match is None else third_match.route_id
    third_production_call = _production_call(before_router, third_context)
    if first_production_call != "2D" or third_route_id is not None or third_production_call is not None:
        raise RuntimeError("Phase 30H standard production opening witness drifted")

    partnership_call = (
        first.selection.side is PartnershipSide.NS
        and first.assessment.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
        and first_composed.composition_disposition is Composition.PARTNERSHIP_CALL
        and first_composed.partnership_call == "3D" and first_composed.base_continuation is None
        and third.selection.seat is Seat.SOUTH and third.selection.side is PartnershipSide.NS
        and third_composed.composition_disposition is Composition.PARTNERSHIP_CALL
        and third_composed.partnership_call == "3D" and third_composed.base_continuation is None
    )
    add_handoff = (
        negative.disposition is ProfileOpeningDisposition.ABSTAIN
        and negative.binding is not None and negative.policy_assessment is not None
        and negative_composed.composition_disposition is Composition.BASE_SYSTEM_CONTINUATION
        and negative_composed.partnership_call is None
        and negative_composed.base_continuation is not None
        and negative_composed.base_continuation.base_system is ns_plan.base_system
        and ns_plan.base_system is SystemProfile.TWO_OVER_ONE_GF
    )
    peer_handoff = (
        peer_opening.selection.side is PartnershipSide.EW
        and peer_opening.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
        and peer_composed.composition_disposition is Composition.BASE_SYSTEM_CONTINUATION
        and peer_composed.partnership_call is None and peer_composed.base_continuation is not None
        and peer_composed.base_continuation.base_system is ew_plan.base_system
        and ew_plan.base_system is SystemProfile.TWO_OVER_ONE_GF
    )
    replace_safe = (
        replace_plan.directive("opening.2d").action is CompilationAction.REPLACE
        and replaced.composition_disposition is Composition.PROFILE_OVERRIDE_BLOCKS_BASE
        and replaced.partnership_call is None and replaced.base_continuation is None
    )
    unbound_safe = (
        unbound_plan.directive(_FAMILY).action is CompilationAction.ADD
        and unbound_assessment.disposition is ProfileOpeningDisposition.NO_BINDING
        and unbound.composition_disposition is Composition.UNRESOLVED
        and unbound.partnership_call is None and unbound.base_continuation is None
    )
    contract_ready = (
        capability.composition_contract_ready and capability.base_continuation_request_ready
        and not capability.production_adopted and not capability.production_bidding_changed
        and partnership_call and add_handoff and peer_handoff and replace_safe and unbound_safe
    )
    if not partnership_call:
        raise RuntimeError("Phase 30H partnership-call witness drifted")
    after_router = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after_router.routes)
    context_shape = (
        tuple(item.name for item in fields(SystemContext)) == ("system", "options")
        and tuple(item.name for item in fields(BiddingContext))
        == ("hand", "evaluation", "auction", "seat", "vulnerability", "system")
    )
    production_changed = before_ids != after_ids or capability.production_bidding_changed
    regression_guard = (
        len(before_ids) == len(after_ids) == 45 and before_ids == after_ids
        and not production_changed and context_shape
        and not any(marker in route_id.casefold() for route_id in after_ids
                    for marker in ("nisim", "30g", "30h"))
    )
    historical_gates = {gate.gate_id: gate for gate in history.gates}
    if len(historical_gates) != 14 or "base_system_fallback_contract" not in historical_gates:
        raise RuntimeError("Phase 30F semantic gate set drifted")
    current = dict(historical_gates)
    old_base = historical_gates["base_system_fallback_contract"]
    base_state = (ProductionReadinessState.READY if contract_ready and capability.base_execution_ready
                  else ProductionReadinessState.SHADOW_READY if contract_ready
                  else ProductionReadinessState.BLOCKED)
    current[old_base.gate_id] = ProductionReadinessGate(
        old_base.gate_id, base_state, old_base.required_for_production,
        ("30G:semantic handoff verified=" + str(contract_ready),
         "30G:ADD/ABSTAIN and NO_BINDING -> TWO_OVER_ONE_GF continuation requests",
         "30G:REPLACE blocks base; unbound ADD is unresolved",
         "30G:base_execution_ready=" + str(capability.base_execution_ready)),
        "Semantic base handoff exists; runtime execution of that handoff does not."
        if contract_ready and not capability.base_execution_ready else
        "Base-system composition remains incomplete." if not contract_ready else
        "Semantic handoff and declared-base execution are available.",
    )
    old_guard = historical_gates["production_regression_guard"]
    current[old_guard.gate_id] = ProductionReadinessGate(
        old_guard.gate_id,
        ProductionReadinessState.READY if regression_guard else ProductionReadinessState.BLOCKED,
        old_guard.required_for_production,
        (f"routes before={len(before_ids)} after={len(after_ids)}",
         f"ordered inventory equal={before_ids == after_ids}",
         f"context fields unchanged={context_shape}"),
        "Ordered production routes and context shapes remain unchanged."
    )
    gates = tuple(current.values())
    transitions = tuple(PostCompositionGateTransition(
        gate.gate_id, historical_gates[gate.gate_id].state, gate.state,
        gate.reason) for gate in gates)
    if (history.to_json() != historical_json or NISIM_NILY_PROFILE.to_json() != source_json
            or ns_plan.to_json() != plan_json):
        raise RuntimeError("Phase 30H mutated historical or source profile data")
    return PostCompositionOpeningReadinessAudit(
        profile_id=ns_plan.profile_id, profile_version=ns_plan.profile_version,
        base_system=ns_plan.base_system, gates=gates, transitions_from_30f=transitions,
        composition_contract_ready=capability.composition_contract_ready,
        base_continuation_request_ready=capability.base_continuation_request_ready,
        base_execution_ready=capability.base_execution_ready,
        first_seat_shadow_call=first_composed.partnership_call,
        first_seat_production_call=first_production_call,
        third_seat_shadow_call=third_composed.partnership_call,
        third_seat_production_route_id=third_route_id,
        partnership_composition=first_composed.composition_disposition.value,
        add_abstain_composition=negative_composed.composition_disposition.value,
        add_abstain_base_system=(None if negative_composed.base_continuation is None else
                                 negative_composed.base_continuation.base_system),
        peer_composition=peer_composed.composition_disposition.value,
        peer_base_system=(None if peer_composed.base_continuation is None else
                          peer_composed.base_continuation.base_system),
        replace_composition=replaced.composition_disposition.value,
        unbound_add_composition=unbound.composition_disposition.value,
        route_count=len(after_ids), ordered_route_ids_equal=before_ids == after_ids,
        production_changed=production_changed, production_adopted=capability.production_adopted,
    )
