"""Phase 30D: evidence-backed production-adoption gate, without activation."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.nisim_nily_six_minor_preempt_policy import (
    SixMinorDecision,
    assess_six_minor_three_level_preempt,
)
from bridge.opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from bridge.opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    resolve_partnership_profile,
)
from bridge.profile_compiler import compile_profile_plan
from bridge.profile_opening_adapter import ProfileOpeningDisposition, evaluate_profile_opening_shadow
from bridge.profile_opening_production_gate import (
    HistoricalGateTransition,
    ProductionReadinessGate,
    ProductionReadinessState,
    ProfileOpeningProductionGateAudit,
    build_profile_opening_production_gate_audit,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING, bind_compiled_directive


def _audit():
    return build_profile_opening_production_gate_audit()


def _plan(profile=NISIM_NILY_PROFILE):
    return compile_profile_plan(resolve_partnership_profile(profile))


def test_exact_readiness_states_frozen_records_and_evidence_order():
    assert tuple(state.value for state in ProductionReadinessState) == (
        "READY", "SHADOW_READY", "BLOCKED"
    )
    gate = ProductionReadinessGate(
        "example", ProductionReadinessState.SHADOW_READY, True,
        ("z evidence", "A evidence"), "example reason",
    )
    assert gate.evidence == ("A evidence", "z evidence")
    with pytest.raises(FrozenInstanceError):
        gate.state = ProductionReadinessState.READY
    with pytest.raises(FrozenInstanceError):
        HistoricalGateTransition("old", "BLOCKED", ProductionReadinessState.READY,
                                 "reason").gate_id = "new"
    with pytest.raises(ValueError, match="gate_id"):
        ProductionReadinessGate(" ", ProductionReadinessState.READY, True, (), "reason")
    with pytest.raises(ValueError, match="duplicate evidence"):
        ProductionReadinessGate("example", ProductionReadinessState.READY, True,
                                ("Proof", "proof"), "reason")


def test_audit_is_immutable_ordered_serializable_and_profile_specific():
    audit = _audit()
    assert isinstance(audit, ProfileOpeningProductionGateAudit)
    assert (audit.phase, audit.audit_version) == ("30D", "30D.1")
    assert (audit.profile_id, audit.profile_version, audit.base_system) == (
        NISIM_NILY_PROFILE.profile_id, NISIM_NILY_PROFILE.version,
        SystemProfile.TWO_OVER_ONE_GF,
    )
    assert audit.to_json() == _audit().to_json()
    assert json.loads(audit.to_json()) == audit.to_dict()
    assert tuple(gate.gate_id for gate in audit.gates) == tuple(sorted(
        gate.gate_id for gate in audit.gates
    ))
    assert tuple(item.gate_id for item in audit.historical_transitions) == tuple(sorted(
        item.gate_id for item in audit.historical_transitions
    ))
    with pytest.raises(FrozenInstanceError):
        audit.ready_for_production = True
    duplicate = replace(audit.gates[0], gate_id=audit.gates[1].gate_id.upper())
    with pytest.raises(ValueError, match="duplicate gate IDs"):
        replace(audit, gates=(audit.gates[1], duplicate))
    assert audit.gate("POLICY_SEMANTICS") == audit.gate("policy_semantics")


@pytest.mark.parametrize("gate_id,state", [
    ("policy_semantics", ProductionReadinessState.READY),
    ("system_partnership_separation", ProductionReadinessState.READY),
    ("typed_partnership_profile", ProductionReadinessState.READY),
    ("profile_compilation", ProductionReadinessState.READY),
    ("treatment_binding", ProductionReadinessState.SHADOW_READY),
    ("opening_context_adapter", ProductionReadinessState.SHADOW_READY),
    ("runtime_partnership_selection", ProductionReadinessState.BLOCKED),
    ("first_seat_precedence", ProductionReadinessState.SHADOW_READY),
    ("later_seat_opening_dispatch", ProductionReadinessState.SHADOW_READY),
    ("production_result_adapter", ProductionReadinessState.BLOCKED),
    ("base_system_fallback_contract", ProductionReadinessState.BLOCKED),
    ("no_pass_inference", ProductionReadinessState.READY),
    ("partnership_isolation", ProductionReadinessState.READY),
    ("production_regression_guard", ProductionReadinessState.READY),
])
def test_each_required_gate_has_evidence_and_expected_state(gate_id, state):
    gate = _audit().gate(gate_id)
    assert gate is not None
    assert gate.state is state
    assert gate.required_for_production is True
    assert gate.evidence and gate.reason


def test_first_and_third_seat_witnesses_measure_shadow_vs_production():
    audit = _audit()
    assert (audit.first_seat_shadow_call, audit.first_seat_production_call) == ("3D", "2D")
    assert (audit.third_seat_shadow_call, audit.third_seat_production_route_id) == (
        "3D", None
    )
    assert audit.gate("first_seat_precedence").state is not ProductionReadinessState.READY
    assert audit.gate("later_seat_opening_dispatch").state is not ProductionReadinessState.READY
    router = create_standard_sayc_router()
    hand = Hand.parse("7.84.KQJT96.9742")
    first = BiddingContext.create(
        hand=hand, auction=Auction(Seat.NORTH), vulnerability=Vulnerability.EW,
        system=SystemContext("SAYC"),
    )
    third = BiddingContext.create(
        hand=hand, auction=Auction(Seat.NORTH, ("P", "P")),
        vulnerability=Vulnerability.EW, system=SystemContext("SAYC"),
    )
    assert router.evaluate(first).recommended_call.serialize() == "2D"
    assert router.match(third) is None
    assert router.evaluate(third).recommended_call is None


def test_runtime_selector_result_adapter_and_base_fallback_are_independent_blockers():
    audit = _audit()
    for gate_id in (
        "runtime_partnership_selection", "production_result_adapter",
        "base_system_fallback_contract",
    ):
        assert audit.gate(gate_id).state is ProductionReadinessState.BLOCKED
    assert audit.gate("typed_partnership_profile").state is ProductionReadinessState.READY
    assert audit.gate("opening_context_adapter").state is ProductionReadinessState.SHADOW_READY
    assert NISIM_NILY_PROFILE.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert SystemProfile.SAYC is not SystemProfile.TWO_OVER_ONE_GF


def test_no_pass_inference_and_peer_partnership_isolation():
    plan = _plan()
    negative = evaluate_profile_opening_shadow(
        plan, hand=Hand.parse("7.84.QJT986.9742"), auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.NONE,
    )
    peer = PartnershipProfile(
        "phase30d-peer", "test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    absent = evaluate_profile_opening_shadow(
        _plan(peer), hand=Hand.parse("7.84.KQJT96.9742"),
        auction=Auction(Seat.NORTH, ("P", "P")), vulnerability=Vulnerability.EW,
    )
    assert negative.disposition is ProfileOpeningDisposition.ABSTAIN
    assert absent.disposition is ProfileOpeningDisposition.NO_BINDING
    assert negative.supported_call is absent.supported_call is None
    assert negative.binding is not None and absent.binding is None
    assert plan.base_system is _plan(peer).base_system


def test_six_phase29v_transitions_are_read_from_historical_audit():
    old = build_six_minor_production_adoption_audit()
    audit = _audit()
    old_states = {gate.gate_id: gate.state.value for gate in old.gates}
    actual = {
        item.gate_id: (item.phase29v_state, item.phase30d_state)
        for item in audit.historical_transitions
    }
    assert len(actual) == 6
    assert all(actual[name][0] == state for name, state in old_states.items())
    assert actual == {
        "policy_semantics": ("READY", ProductionReadinessState.READY),
        "system_partnership_separation": ("READY", ProductionReadinessState.READY),
        "typed_partnership_selector": ("BLOCKED", ProductionReadinessState.READY),
        "first_seat_precedence": ("BLOCKED", ProductionReadinessState.SHADOW_READY),
        "later_seat_opening_routing": ("BLOCKED", ProductionReadinessState.SHADOW_READY),
        "production_adapter": ("BLOCKED", ProductionReadinessState.BLOCKED),
    }
    assert old.ready_for_production is False and old.production_changed is False


def test_readiness_is_computed_from_required_gates_and_next_phase_uses_priority():
    audit = _audit()
    assert audit.ready_for_production is False
    assert audit.ready_for_production == all(
        gate.state is ProductionReadinessState.READY
        for gate in audit.gates if gate.required_for_production
    )
    assert audit.recommended_next_phase == "30E_RUNTIME_PARTNERSHIP_SELECTION"
    all_ready = replace(audit, gates=tuple(replace(gate, state=ProductionReadinessState.READY)
                                           for gate in audit.gates))
    assert all_ready.ready_for_production is True
    assert all_ready.recommended_next_phase == "30E_PRODUCTION_PILOT"
    optional_blocked = replace(all_ready, gates=all_ready.gates + (
        ProductionReadinessGate("optional_future_gate", ProductionReadinessState.BLOCKED,
                                False, ("test",), "optional"),
    ))
    assert optional_blocked.ready_for_production is True
    shadow_required = replace(all_ready, gates=tuple(
        replace(gate, state=ProductionReadinessState.SHADOW_READY)
        if gate.gate_id == "opening_context_adapter" else gate for gate in all_ready.gates
    ))
    assert shadow_required.ready_for_production is False
    assert shadow_required.recommended_next_phase == "30E_PRODUCTION_INTEGRATION_REMEDIATION"
    for blocker, expected in (
        ("runtime_partnership_selection", "30E_RUNTIME_PARTNERSHIP_SELECTION"),
        ("base_system_fallback_contract", "30E_BASE_SYSTEM_COMPOSITION"),
        ("production_result_adapter", "30E_PRODUCTION_ADAPTER"),
    ):
        variant = replace(all_ready, gates=tuple(
            replace(gate, state=ProductionReadinessState.BLOCKED)
            if gate.gate_id == blocker else gate for gate in all_ready.gates
        ))
        assert variant.ready_for_production is False
        assert variant.recommended_next_phase == expected


def test_audit_preserves_sources_contexts_routes_and_production_flags():
    profile_before = NISIM_NILY_PROFILE.to_json()
    plan = _plan()
    plan_before = plan.to_json()
    binding_before = NISIM_NILY_SIX_MINOR_BINDING.to_json()
    before_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    audit = _audit()
    after_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(before_ids) == len(after_ids) == audit.route_count == 45
    assert before_ids == after_ids and audit.production_changed is False
    assert not any(marker in route_id.casefold() for route_id in after_ids
                   for marker in ("nisim", "30a", "30b", "30c", "30d"))
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert plan.to_json() == plan_before == _plan().to_json()
    assert NISIM_NILY_SIX_MINOR_BINDING.to_json() == binding_before
    assert bind_compiled_directive(plan.directive("opening.three_level.six_minor")) == (
        NISIM_NILY_SIX_MINOR_BINDING
    )
    assert NISIM_NILY_SIX_MINOR_BINDING.production_adopted is False
    hand = Hand.parse("7.84.KQJT96.9742")
    auction = Auction(Seat.NORTH, ("P", "P"))
    assert evaluate_profile_opening_shadow(
        plan, hand=hand, auction=auction, vulnerability=Vulnerability.EW
    ).production_adopted is False
    direct = assess_six_minor_three_level_preempt(
        hand, seat=Seat.SOUTH, vulnerability=Vulnerability.EW, opening_position=3
    )
    assert direct.decision is SixMinorDecision.THREE_LEVEL
    assert direct.production_adopted is False
    assert assess_opening_policy_with_six_minor(
        hand, auction=auction, vulnerability=Vulnerability.EW
    ).production_adopted is False
    old = build_six_minor_production_adoption_audit()
    assert old.production_changed is False and old.ready_for_production is False


def test_audit_module_creates_no_production_component_or_registration():
    source = (Path(__file__).resolve().parents[1] / "bridge" /
              "profile_opening_production_gate.py").read_text()
    tree = ast.parse(source)
    calls = [node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert not set(calls) & {"EngineRoute", "BiddingEngine", "BiddingRule", "RuleDecision",
                             "BiddingEngineResult"}
    assert "create_standard_sayc_router" in source  # read-only diagnostic
    assert "register(" not in source
