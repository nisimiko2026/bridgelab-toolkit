"""Phase 30D evidence audit for profile-aware opening production adoption.

This module reads existing shadow and production behavior. It registers no
route, selects no runtime partnership, and converts no result for production.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from enum import Enum
from inspect import signature

from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .models import Hand, Seat, Vulnerability
from .nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from .nisim_nily_six_minor_preempt_policy import SixMinorDecision, assess_six_minor_three_level_preempt
from .opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from .partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from .profile_compiler import CompiledProfilePlan, compile_profile_plan
from .profile_opening_adapter import ProfileOpeningDisposition, evaluate_profile_opening_shadow
from .sayc_route_configuration import create_standard_sayc_router
from .system_profiles import SystemProfile, classify_system_profile
from .treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING, bind_compiled_directive


FAMILY = "opening.three_level.six_minor"
_FORBIDDEN_ROUTE_MARKERS = ("nisim", "30a", "30b", "30c", "30d")


class ProductionReadinessState(str, Enum):
    READY = "READY"
    SHADOW_READY = "SHADOW_READY"
    BLOCKED = "BLOCKED"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _evidence(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError("evidence must be a tuple")
    normalized = tuple(_nonblank(value, "evidence item") for value in values)
    if len({value.casefold() for value in normalized}) != len(normalized):
        raise ValueError("duplicate evidence item")
    return tuple(sorted(normalized, key=lambda value: (value.casefold(), value)))


@dataclass(frozen=True, slots=True)
class ProductionReadinessGate:
    gate_id: str
    state: ProductionReadinessState
    required_for_production: bool
    evidence: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _nonblank(self.gate_id, "gate_id"))
        if not isinstance(self.state, ProductionReadinessState):
            raise TypeError("state must be ProductionReadinessState")
        if not isinstance(self.required_for_production, bool):
            raise TypeError("required_for_production must be bool")
        object.__setattr__(self, "evidence", _evidence(self.evidence))
        object.__setattr__(self, "reason", _nonblank(self.reason, "reason"))

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "state": self.state.value,
            "required_for_production": self.required_for_production,
            "evidence": list(self.evidence),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class HistoricalGateTransition:
    gate_id: str
    phase29v_state: str
    phase30d_state: ProductionReadinessState
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _nonblank(self.gate_id, "gate_id"))
        object.__setattr__(self, "phase29v_state", _nonblank(self.phase29v_state, "phase29v_state"))
        if not isinstance(self.phase30d_state, ProductionReadinessState):
            raise TypeError("phase30d_state must be ProductionReadinessState")
        object.__setattr__(self, "reason", _nonblank(self.reason, "reason"))

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "phase29v_state": self.phase29v_state,
            "phase30d_state": self.phase30d_state.value,
            "reason": self.reason,
        }


def _required_gates_ready(gates: tuple[ProductionReadinessGate, ...]) -> bool:
    return all(
        gate.state is ProductionReadinessState.READY
        for gate in gates if gate.required_for_production
    )


def _recommended_next_phase(gates: tuple[ProductionReadinessGate, ...]) -> str:
    if _required_gates_ready(gates):
        return "30E_PRODUCTION_PILOT"
    states = {gate.gate_id: gate.state for gate in gates}
    priorities = (
        ("runtime_partnership_selection", "30E_RUNTIME_PARTNERSHIP_SELECTION"),
        ("base_system_fallback_contract", "30E_BASE_SYSTEM_COMPOSITION"),
        ("production_result_adapter", "30E_PRODUCTION_ADAPTER"),
    )
    for gate_id, recommendation in priorities:
        if states.get(gate_id) is ProductionReadinessState.BLOCKED:
            return recommendation
    return "30E_PRODUCTION_INTEGRATION_REMEDIATION"


@dataclass(frozen=True, slots=True)
class ProfileOpeningProductionGateAudit:
    profile_id: str
    profile_version: str
    base_system: SystemProfile
    gates: tuple[ProductionReadinessGate, ...]
    historical_transitions: tuple[HistoricalGateTransition, ...]
    first_seat_shadow_call: str | None
    first_seat_production_call: str | None
    third_seat_shadow_call: str | None
    third_seat_production_route_id: str | None
    route_count: int
    production_changed: bool
    phase: str = "30D"
    audit_version: str = "30D.1"
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
        ids = [gate.gate_id.casefold() for gate in self.gates]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate gate IDs")
        ordered = tuple(sorted(self.gates, key=lambda gate: (gate.gate_id.casefold(), gate.gate_id)))
        object.__setattr__(self, "gates", ordered)
        if not isinstance(self.historical_transitions, tuple) or not all(
            isinstance(item, HistoricalGateTransition) for item in self.historical_transitions
        ):
            raise TypeError("historical_transitions must be a tuple of HistoricalGateTransition")
        transition_ids = [item.gate_id.casefold() for item in self.historical_transitions]
        if len(set(transition_ids)) != len(transition_ids):
            raise ValueError("duplicate historical gate IDs")
        object.__setattr__(
            self, "historical_transitions",
            tuple(sorted(self.historical_transitions, key=lambda item: (item.gate_id.casefold(), item.gate_id))),
        )
        object.__setattr__(self, "ready_for_production", _required_gates_ready(ordered))
        object.__setattr__(self, "recommended_next_phase", _recommended_next_phase(ordered))

    def gate(self, gate_id: str) -> ProductionReadinessGate | None:
        key = _nonblank(gate_id, "gate_id").casefold()
        return next((gate for gate in self.gates if gate.gate_id.casefold() == key), None)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "audit_version": self.audit_version,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "base_system": self.base_system.value,
            "gates": [gate.to_dict() for gate in self.gates],
            "historical_transitions": [item.to_dict() for item in self.historical_transitions],
            "first_seat_shadow_call": self.first_seat_shadow_call,
            "first_seat_production_call": self.first_seat_production_call,
            "third_seat_shadow_call": self.third_seat_shadow_call,
            "third_seat_production_route_id": self.third_seat_production_route_id,
            "route_count": self.route_count,
            "production_changed": self.production_changed,
            "ready_for_production": self.ready_for_production,
            "recommended_next_phase": self.recommended_next_phase,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _gate(
    gate_id: str, state: ProductionReadinessState, reason: str, *evidence: str
) -> ProductionReadinessGate:
    return ProductionReadinessGate(gate_id, state, True, evidence, reason)


def _production_call(router, context: BiddingContext) -> str | None:
    result = router.evaluate(context)
    return None if result.recommended_call is None else result.recommended_call.serialize()


def build_profile_opening_production_gate_audit() -> ProfileOpeningProductionGateAudit:
    """Recheck actual witnesses, then classify each adoption prerequisite."""
    before_router = create_standard_sayc_router()
    before_ids = tuple(route.route_id for route in before_router.routes)
    profile_before = NISIM_NILY_PROFILE.to_json()
    resolved = resolve_partnership_profile(NISIM_NILY_PROFILE)
    plan = compile_profile_plan(resolved)
    plan_before = plan.to_json()
    directive = plan.directive(FAMILY)
    binding = None if directive is None else bind_compiled_directive(directive)

    hand = Hand.parse("7.84.KQJT96.9742")
    first_auction = Auction(Seat.NORTH)
    third_auction = Auction(Seat.NORTH, ("P", "P"))
    first_shadow = evaluate_profile_opening_shadow(
        plan, hand=hand, auction=first_auction, vulnerability=Vulnerability.EW
    )
    third_shadow = evaluate_profile_opening_shadow(
        plan, hand=hand, auction=third_auction, vulnerability=Vulnerability.EW
    )
    abstain_shadow = evaluate_profile_opening_shadow(
        plan, hand=Hand.parse("7.84.QJT986.9742"), auction=first_auction,
        vulnerability=Vulnerability.NONE,
    )
    second_profile = PartnershipProfile(
        "phase30d-isolation-witness", "30D.1", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    other_plan = compile_profile_plan(resolve_partnership_profile(second_profile))
    other_shadow = evaluate_profile_opening_shadow(
        other_plan, hand=hand, auction=third_auction, vulnerability=Vulnerability.EW
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
        raise RuntimeError("Phase 30D production witness drifted from the Phase 29V baseline")

    direct = assess_six_minor_three_level_preempt(
        hand, seat=Seat.NORTH, vulnerability=Vulnerability.EW, opening_position=1
    )
    rule20 = assess_six_minor_three_level_preempt(
        Hand.parse("7.K4.KQJT96.A742"), seat=Seat.NORTH,
        vulnerability=Vulnerability.EW, opening_position=1,
    )
    seven_card = assess_six_minor_three_level_preempt(
        Hand.parse("7.84.KQJT986.742"), seat=Seat.NORTH,
        vulnerability=Vulnerability.EW, opening_position=1,
    )
    policy_ready = (
        direct.decision is SixMinorDecision.THREE_LEVEL
        and rule20.decision is SixMinorDecision.ONE_LEVEL
        and abstain_shadow.policy_assessment.decision is SixMinorDecision.NO_THREE_LEVEL
        and seven_card.decision is SixMinorDecision.NOT_APPLICABLE
        and direct.production_adopted is False
    )
    isolated = (
        other_plan.base_system is plan.base_system
        and other_shadow.disposition is ProfileOpeningDisposition.NO_BINDING
        and other_shadow.supported_call is None
    )
    separation_ready = (
        isinstance(NISIM_NILY_PROFILE, PartnershipProfile)
        and not isinstance(NISIM_NILY_PROFILE, SystemProfile)
        and plan.base_system is SystemProfile.TWO_OVER_ONE_GF
        and isolated
    )
    typed_profile_ready = isinstance(resolved, ResolvedBiddingProfile) and isinstance(
        plan, CompiledProfilePlan
    )
    compiled = (
        directive is not None
        and directive.effective_treatment_id == NISIM_NILY_SIX_MINOR_BINDING.treatment_id
        and plan.to_json() == compile_profile_plan(resolved).to_json()
    )
    bound = binding == NISIM_NILY_SIX_MINOR_BINDING and binding.production_adopted is False
    first_shadow_ready = (
        first_shadow.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
        and first_shadow.supported_call == "3D"
        and first_shadow.policy_assessment == direct
        and first_shadow.production_adopted is False
    )
    third_shadow_ready = (
        third_shadow.disposition is ProfileOpeningDisposition.SUPPORTED_CALL
        and third_shadow.supported_call == "3D"
        and third_shadow.acting_seat is Seat.SOUTH
        and third_shadow.opening_position == 3
        and third_shadow.production_adopted is False
    )
    pass_safe = (
        abstain_shadow.disposition is ProfileOpeningDisposition.ABSTAIN
        and abstain_shadow.supported_call is None
        and other_shadow.disposition is ProfileOpeningDisposition.NO_BINDING
        and other_shadow.supported_call is None
    )
    after_router = create_standard_sayc_router()
    after_ids = tuple(route.route_id for route in after_router.routes)
    production_changed = before_ids != after_ids
    route_guard = (
        not production_changed and len(before_ids) == len(after_ids) == 45
        and not any(marker in route_id.casefold() for route_id in after_ids
                    for marker in _FORBIDDEN_ROUTE_MARKERS)
    )
    system_fields = tuple(item.name for item in fields(SystemContext))
    context_fields = tuple(item.name for item in fields(BiddingContext))
    current_context_shape = (
        system_fields == ("system", "options")
        and context_fields == ("hand", "evaluation", "auction", "seat", "vulnerability", "system")
    )
    production_entry_parameters = tuple(signature(before_router.evaluate).parameters)
    router_factory_parameters = tuple(signature(create_standard_sayc_router).parameters)
    # These are negative findings about the inspected production entry path,
    # not a claim that all possible future runtime designs need context fields.
    typed_runtime_input = (
        "profile" in production_entry_parameters
        or "plan" in production_entry_parameters
        or "profile" in router_factory_parameters
        or "plan" in router_factory_parameters
        or any(item.name in ("profile", "plan", "partnership_profile")
               for item in (*fields(SystemContext), *fields(BiddingContext)))
    )
    runtime_selection_verified = typed_runtime_input and first_production_call == first_shadow.supported_call
    # No approved production conversion or 2/1 continuation is exposed by
    # this entry path. Shadow assessments do not satisfy either contract.
    production_adapter_verified = False
    base_fallback_verified = False
    sayc_is_distinct_base = (
        classify_system_profile(SystemContext("SAYC")) is SystemProfile.SAYC
        and plan.base_system is SystemProfile.TWO_OVER_ONE_GF
    )

    ready = ProductionReadinessState.READY
    shadow = ProductionReadinessState.SHADOW_READY
    blocked = ProductionReadinessState.BLOCKED
    gates = (
        _gate("policy_semantics", ready if policy_ready else blocked,
              "Phase 29T covers all four pilot decisions with deterministic calls or abstention.",
              "29T:THREE_LEVEL/ONE_LEVEL/NO_THREE_LEVEL/NOT_APPLICABLE"),
        _gate("system_partnership_separation", ready if separation_ready else blocked,
              "The partnership profile has a distinct 2/1 base and does not leak to a peer partnership.",
              "29X:PartnershipProfile", "29Y:TWO_OVER_ONE_GF", "29Z:same-system isolation"),
        _gate("typed_partnership_profile", ready if typed_profile_ready else blocked,
              "Typed partnership and resolved-profile data models exist; this does not select a runtime partnership.",
              "29X:PartnershipProfile/ResolvedBiddingProfile"),
        _gate("profile_compilation", ready if compiled else blocked,
              "Phase 30A deterministically exposes the effective pilot directive.",
              "30A:CompiledProfilePlan.directive"),
        _gate("treatment_binding", shadow if bound else blocked,
              "The exact Phase 30B binding reaches Phase 29T, but is non-production.",
              "30B:bind_compiled_directive", "30B:production_adopted=False"),
        _gate("opening_context_adapter", shadow if first_shadow_ready and third_shadow_ready else blocked,
              "Phase 30C derives opening seat and position from Auction in shadow mode.",
              "30C:first=3D", "30C:third=3D", "30C:production_adopted=False"),
        _gate("runtime_partnership_selection", ready if runtime_selection_verified else blocked,
              "No verified typed partnership-plan selection reaches the inspected production entry path.",
              f"production evaluate inputs={production_entry_parameters}",
              f"standard router factory inputs={router_factory_parameters}"),
        _gate("first_seat_precedence", shadow if first_shadow_ready else blocked,
              "Shadow supports 3D; current standard production still recommends 2D.",
              f"shadow={first_shadow.supported_call}", f"production={first_production_call}"),
        _gate("later_seat_opening_dispatch", shadow if third_shadow_ready else blocked,
              "Shadow handles P P; current standard production has no matching route.",
              f"shadow={third_shadow.supported_call}", f"production route={third_route_id}",
              f"production call={third_production_call}"),
        _gate("production_result_adapter", ready if production_adapter_verified else blocked,
              "No approved converter from ProfileOpeningAssessment to production recommendation exists.",
              "30C:ProfileOpeningAssessment", "production:BiddingEngineResult"),
        _gate("base_system_fallback_contract", ready if base_fallback_verified else blocked,
              "No approved 2/1 continuation after ABSTAIN or NO_BINDING; SAYC is a distinct system.",
              f"2/1 distinct from SAYC={sayc_is_distinct_base}",
              "30C:ABSTAIN/NO_BINDING have no fallback"),
        _gate("no_pass_inference", ready if pass_safe else blocked,
              "ABSTAIN and NO_BINDING remain distinct and neither manufactures Pass.",
              "30C:ABSTAIN=None", "30C:NO_BINDING=None"),
        _gate("partnership_isolation", ready if isolated else blocked,
              "A second partnership with the same base system has no pilot binding.",
              "29Z/30C:same-system peer=NO_BINDING"),
        _gate("production_regression_guard", ready if route_guard and current_context_shape else blocked,
              "The audit preserves the 45 ordered routes and production context shapes.",
              f"routes before={len(before_ids)} after={len(after_ids)}",
              f"ordered inventory equal={not production_changed}",
              f"context fields unchanged={current_context_shape}"),
    )

    historical = build_six_minor_production_adoption_audit()
    old = {gate.gate_id: gate for gate in historical.gates}
    current = {gate.gate_id: gate for gate in gates}
    mappings = (
        ("policy_semantics", "policy_semantics"),
        ("system_partnership_separation", "system_partnership_separation"),
        ("typed_partnership_selector", "typed_partnership_profile"),
        ("first_seat_precedence", "first_seat_precedence"),
        ("later_seat_opening_routing", "later_seat_opening_dispatch"),
        ("production_adapter", "production_result_adapter"),
    )
    transitions = tuple(
        HistoricalGateTransition(
            historical_id, old[historical_id].state.value,
            current[current_id].state,
            current[current_id].reason,
        ) for historical_id, current_id in mappings
    )
    if NISIM_NILY_PROFILE.to_json() != profile_before or plan.to_json() != plan_before:
        raise RuntimeError("Phase 30D audit mutated a source profile or compiled plan")
    return ProfileOpeningProductionGateAudit(
        profile_id=plan.profile_id,
        profile_version=plan.profile_version,
        base_system=plan.base_system,
        gates=gates,
        historical_transitions=transitions,
        first_seat_shadow_call=first_shadow.supported_call,
        first_seat_production_call=first_production_call,
        third_seat_shadow_call=third_shadow.supported_call,
        third_seat_production_route_id=third_route_id,
        route_count=len(after_ids),
        production_changed=production_changed,
    )
