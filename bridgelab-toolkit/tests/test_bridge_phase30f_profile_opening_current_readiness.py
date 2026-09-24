"""Phase 30F: current gates after 30E, compared with immutable 30D history."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    resolve_partnership_profile,
)
from bridge.profile_compiler import compile_profile_plan
from bridge.profile_opening_adapter import ProfileOpeningDisposition
from bridge.profile_opening_current_readiness_audit import (
    CurrentGateTransition,
    CurrentProfileOpeningReadinessAudit,
    _recommended_next_phase,
    _required_gates_ready,
    build_current_profile_opening_readiness_audit,
)
from bridge.profile_opening_production_gate import (
    ProductionReadinessState,
    build_profile_opening_production_gate_audit,
)
from bridge.runtime_partnership_selection import (
    PartnershipSide,
    RuntimePartnershipSelectionCapability,
    TablePartnershipPlans,
    evaluate_selected_profile_opening_shadow,
    select_runtime_profile,
    select_runtime_profile_for_auction,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING


def _audit():
    return build_current_profile_opening_readiness_audit()


def _table():
    ns = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    peer = PartnershipProfile(
        "phase30f-test-peer", "30F.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    ew = compile_profile_plan(resolve_partnership_profile(peer))
    return TablePartnershipPlans(ns, ew)


def test_current_audit_and_transition_records_are_immutable_and_deterministic():
    audit = _audit()
    assert isinstance(audit, CurrentProfileOpeningReadinessAudit)
    assert (audit.phase, audit.historical_phase, audit.audit_version) == ("30F", "30D", "30F.1")
    assert (audit.profile_id, audit.profile_version, audit.base_system) == (
        NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
        SystemProfile.TWO_OVER_ONE_GF,
    )
    assert audit.to_json() == _audit().to_json()
    assert json.loads(audit.to_json()) == audit.to_dict()
    assert tuple(gate.gate_id for gate in audit.gates) == tuple(sorted(
        gate.gate_id for gate in audit.gates
    ))
    assert tuple(item.gate_id for item in audit.transitions_from_30d) == tuple(sorted(
        item.gate_id for item in audit.transitions_from_30d
    ))
    with pytest.raises(FrozenInstanceError):
        audit.ready_for_production = True
    transition = audit.transitions_from_30d[0]
    with pytest.raises(FrozenInstanceError):
        transition.changed = False
    with pytest.raises(ValueError, match="duplicate current gate IDs"):
        replace(audit, gates=(audit.gates[0], replace(audit.gates[1],
                                                     gate_id=audit.gates[0].gate_id.upper())))


@pytest.mark.parametrize("gate_id,state", [
    ("policy_semantics", ProductionReadinessState.READY),
    ("system_partnership_separation", ProductionReadinessState.READY),
    ("typed_partnership_profile", ProductionReadinessState.READY),
    ("profile_compilation", ProductionReadinessState.READY),
    ("treatment_binding", ProductionReadinessState.SHADOW_READY),
    ("opening_context_adapter", ProductionReadinessState.SHADOW_READY),
    ("runtime_partnership_selection", ProductionReadinessState.READY),
    ("first_seat_precedence", ProductionReadinessState.SHADOW_READY),
    ("later_seat_opening_dispatch", ProductionReadinessState.SHADOW_READY),
    ("production_result_adapter", ProductionReadinessState.BLOCKED),
    ("base_system_fallback_contract", ProductionReadinessState.BLOCKED),
    ("no_pass_inference", ProductionReadinessState.READY),
    ("partnership_isolation", ProductionReadinessState.READY),
    ("production_regression_guard", ProductionReadinessState.READY),
])
def test_current_gate_state_has_independent_evidence(gate_id, state):
    gate = _audit().gate(gate_id)
    assert gate is not None
    assert gate.state is state
    assert gate.required_for_production is True
    assert gate.evidence and gate.reason


def test_exact_historical_gate_set_and_only_runtime_transition_changes():
    historical = build_profile_opening_production_gate_audit()
    current = _audit()
    old = {gate.gate_id: gate for gate in historical.gates}
    new = {gate.gate_id: gate for gate in current.gates}
    assert set(old) == set(new)
    assert len(current.transitions_from_30d) == len(new) == 14
    for transition in current.transitions_from_30d:
        assert isinstance(transition, CurrentGateTransition)
        assert transition.phase30d_state is old[transition.gate_id].state
        assert transition.phase30f_state is new[transition.gate_id].state
        assert transition.changed == (transition.phase30d_state is not transition.phase30f_state)
    changed = tuple(item for item in current.transitions_from_30d if item.changed)
    assert len(changed) == 1
    assert changed[0].gate_id == "runtime_partnership_selection"
    assert (changed[0].phase30d_state, changed[0].phase30f_state) == (
        ProductionReadinessState.BLOCKED, ProductionReadinessState.READY
    )


def test_phase30d_remains_a_historical_snapshot():
    before = build_profile_opening_production_gate_audit().to_json()
    current = _audit()
    historical = build_profile_opening_production_gate_audit()
    assert historical.to_json() == before
    assert historical.phase == "30D"
    assert historical.ready_for_production is False
    assert historical.gate("runtime_partnership_selection").state is ProductionReadinessState.BLOCKED
    assert current.phase == "30F"
    assert current.gate("runtime_partnership_selection").state is ProductionReadinessState.READY


def test_phase30e_typed_selection_is_ready_without_production_recommendation():
    capability = RuntimePartnershipSelectionCapability()
    table = _table()
    assert capability.runtime_selection_ready is True
    assert capability.production_bidding_changed is capability.production_adopted is False
    assert capability.production_result_adapter_ready is False
    assert capability.base_system_fallback_contract_ready is False
    for seat, side, plan in (
        (Seat.NORTH, PartnershipSide.NS, table.ns_plan),
        (Seat.SOUTH, PartnershipSide.NS, table.ns_plan),
        (Seat.EAST, PartnershipSide.EW, table.ew_plan),
        (Seat.WEST, PartnershipSide.EW, table.ew_plan),
    ):
        selection = select_runtime_profile(table, seat)
        assert selection.side is side and selection.plan is plan
        assert selection.production_adopted is False
        assert not hasattr(selection, "recommended_call")
    for calls, plan in (
        ((), table.ns_plan), (("P",), table.ew_plan),
        (("P", "P"), table.ns_plan), (("P", "P", "P"), table.ew_plan),
        (("1C",), table.ew_plan), (("1C", "P"), table.ns_plan),
        (("1C", "P", "1H"), table.ew_plan),
    ):
        auction = Auction(Seat.NORTH, calls)
        selection = select_runtime_profile_for_auction(table, auction)
        assert selection.seat is auction.next_seat and selection.plan is plan
    reversed_table = TablePartnershipPlans(table.ew_plan, table.ns_plan)
    assert select_runtime_profile(reversed_table, Seat.NORTH).plan is table.ew_plan
    assert select_runtime_profile(reversed_table, Seat.EAST).plan is table.ns_plan
    assert table.ns_plan.base_system is table.ew_plan.base_system is SystemProfile.TWO_OVER_ONE_GF


def test_first_and_third_seat_current_shadow_and_production_are_remeasured():
    table = _table()
    hand = Hand.parse("7.84.KQJT96.9742")
    router = create_standard_sayc_router()
    first_auction = Auction(Seat.NORTH)
    third_auction = Auction(Seat.NORTH, ("P", "P"))
    first = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=first_auction, vulnerability=Vulnerability.EW
    )
    third = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=third_auction, vulnerability=Vulnerability.EW
    )
    first_context = BiddingContext.create(
        hand=hand, auction=first_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    third_context = BiddingContext.create(
        hand=hand, auction=third_auction, vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    assert first.selection.plan is third.selection.plan is table.ns_plan
    assert third.selection.seat is Seat.SOUTH
    assert (first.assessment.disposition, first.assessment.supported_call) == (
        ProfileOpeningDisposition.SUPPORTED_CALL, "3D"
    )
    assert (third.assessment.disposition, third.assessment.supported_call) == (
        ProfileOpeningDisposition.SUPPORTED_CALL, "3D"
    )
    assert router.evaluate(first_context).recommended_call.serialize() == "2D"
    assert router.match(third_context) is None
    assert router.evaluate(third_context).recommended_call is None
    audit = _audit()
    assert (audit.first_seat_shadow_call, audit.first_seat_production_call) == ("3D", "2D")
    assert (audit.third_seat_shadow_call, audit.third_seat_production_route_id) == ("3D", None)
    assert audit.gate("first_seat_precedence").state is ProductionReadinessState.SHADOW_READY
    assert audit.gate("later_seat_opening_dispatch").state is ProductionReadinessState.SHADOW_READY


def test_selected_peer_isolation_abstention_and_remaining_blockers():
    table = _table()
    hand = Hand.parse("7.84.KQJT96.9742")
    peer = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=Auction(Seat.EAST), vulnerability=Vulnerability.EW
    )
    assert peer.selection.side is PartnershipSide.EW
    assert peer.selection.plan is table.ew_plan
    assert peer.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
    assert peer.assessment.supported_call is None
    assert table.ew_plan.directive("opening.three_level.six_minor") is None
    audit = _audit()
    assert audit.gate("partnership_isolation").state is ProductionReadinessState.READY
    assert audit.gate("no_pass_inference").state is ProductionReadinessState.READY
    assert audit.gate("production_result_adapter").state is ProductionReadinessState.BLOCKED
    assert audit.gate("base_system_fallback_contract").state is ProductionReadinessState.BLOCKED
    assert table.ns_plan.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert SystemProfile.SAYC is not SystemProfile.TWO_OVER_ONE_GF


def test_readiness_and_recommendation_follow_gate_states():
    audit = _audit()
    assert audit.runtime_selection_ready is True
    assert audit.ready_for_production is False
    assert audit.ready_for_production == _required_gates_ready(audit.gates)
    assert audit.recommended_next_phase == "30G_BASE_SYSTEM_COMPOSITION"
    ready = tuple(replace(gate, state=ProductionReadinessState.READY) for gate in audit.gates)
    assert _required_gates_ready(ready) is True
    assert _recommended_next_phase(ready) == "30G_PRODUCTION_PILOT"
    optional_blocked = ready + (replace(ready[0], gate_id="optional", required_for_production=False,
                                        state=ProductionReadinessState.BLOCKED),)
    assert _required_gates_ready(optional_blocked) is True
    shadow = tuple(replace(gate, state=ProductionReadinessState.SHADOW_READY)
                   if gate.gate_id == "opening_context_adapter" else gate for gate in ready)
    assert _required_gates_ready(shadow) is False
    for gate_id, expected in (
        ("runtime_partnership_selection", "30G_RUNTIME_PARTNERSHIP_SELECTION"),
        ("base_system_fallback_contract", "30G_BASE_SYSTEM_COMPOSITION"),
        ("production_result_adapter", "30G_PRODUCTION_RESULT_ADAPTER"),
    ):
        blocked = tuple(replace(gate, state=ProductionReadinessState.BLOCKED)
                        if gate.gate_id == gate_id else gate for gate in ready)
        assert _required_gates_ready(blocked) is False
        assert _recommended_next_phase(blocked) == expected
    first_pending = tuple(replace(gate, state=ProductionReadinessState.SHADOW_READY)
                          if gate.gate_id == "first_seat_precedence" else gate for gate in ready)
    later_pending = tuple(replace(gate, state=ProductionReadinessState.SHADOW_READY)
                          if gate.gate_id == "later_seat_opening_dispatch" else gate for gate in ready)
    assert _recommended_next_phase(first_pending) == "30G_PROFILE_AWARE_OPENING_PRECEDENCE"
    assert _recommended_next_phase(later_pending) == "30G_LATER_SEAT_OPENING_DISPATCH"
    remaining = tuple(replace(gate, state=ProductionReadinessState.SHADOW_READY)
                      if gate.gate_id == "treatment_binding" else gate for gate in ready)
    assert _recommended_next_phase(remaining) == "30G_PRODUCTION_INTEGRATION_REMEDIATION"


def test_production_inventory_contexts_and_historical_sources_are_unchanged():
    profile_before = NISIM_NILY_PROFILE.to_json()
    plan = compile_profile_plan(resolve_partnership_profile(NISIM_NILY_PROFILE))
    plan_before = plan.to_json()
    historical_before = build_profile_opening_production_gate_audit().to_json()
    before_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    audit = _audit()
    after_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before_ids) == len(after_ids) == audit.route_count == 45
    assert before_ids == after_ids
    assert audit.production_changed is False
    assert audit.gate("production_regression_guard").state is ProductionReadinessState.READY
    assert not any(marker in route_id.casefold() for route_id in after_ids
                   for marker in ("nisim", "30a", "30b", "30c", "30d", "30e", "30f"))
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert plan.to_json() == plan_before
    assert NISIM_NILY_SIX_MINOR_BINDING.production_adopted is False
    assert build_profile_opening_production_gate_audit().to_json() == historical_before


def test_audit_adds_no_production_component_or_fallback():
    path = Path(__file__).resolve().parents[1] / "bridge" / "profile_opening_current_readiness_audit.py"
    source = path.read_text()
    tree = ast.parse(source)
    calls = [node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert not set(calls) & {"EngineRoute", "BiddingEngine", "BiddingRule", "RuleDecision",
                             "BiddingEngineResult"}
    assert "create_standard_sayc_router" in source  # diagnostic comparison only
    assert "register(" not in source
    assert "create_sayc_opening_engine" not in source
