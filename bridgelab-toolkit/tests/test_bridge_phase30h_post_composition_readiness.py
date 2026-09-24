"""Phase 30H post-composition production-readiness audit, without activation."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.base_system_composition import BaseSystemCompositionCapability
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.profile_opening_current_readiness_audit import build_current_profile_opening_readiness_audit
from bridge.profile_opening_post_composition_readiness_audit import (
    PostCompositionGateTransition, PostCompositionOpeningReadinessAudit,
    build_post_composition_opening_readiness_audit,
)
from bridge.profile_opening_production_gate import (
    ProductionReadinessState as State,
    build_profile_opening_production_gate_audit,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile


@pytest.fixture(scope="module")
def audits():
    before = build_current_profile_opening_readiness_audit()
    before_json = before.to_json()
    current = build_post_composition_opening_readiness_audit()
    assert before.to_json() == before_json
    return before, current


def test_historical_snapshots_and_30g_capability(audits):
    old, current = audits
    historical = build_profile_opening_production_gate_audit()
    capability = BaseSystemCompositionCapability()
    assert historical.gate("runtime_partnership_selection").state is State.BLOCKED
    assert old.gate("runtime_partnership_selection").state is State.READY
    assert old.gate("base_system_fallback_contract").state is State.BLOCKED
    assert old.recommended_next_phase == "30G_BASE_SYSTEM_COMPOSITION"
    assert old.ready_for_production is False
    assert old.to_json() == build_current_profile_opening_readiness_audit().to_json()
    assert (capability.composition_contract_ready,
            capability.base_continuation_request_ready,
            capability.base_execution_ready,
            capability.production_bidding_changed,
            capability.production_adopted) == (True, True, False, False, False)
    assert (current.composition_contract_ready,
            current.base_continuation_request_ready,
            current.base_execution_ready) == (True, True, False)


def test_same_14_gates_and_exact_transition(audits):
    old, current = audits
    old_by_id = {g.gate_id: g for g in old.gates}
    new_by_id = {g.gate_id: g for g in current.gates}
    assert len(old_by_id) == len(new_by_id) == 14
    assert set(new_by_id) == set(old_by_id)
    assert len(current.transitions_from_30f) == 14
    assert {t.gate_id for t in current.transitions_from_30f if t.changed} == {
        "base_system_fallback_contract"}
    assert all(t.phase30f_state is old_by_id[t.gate_id].state
               and t.phase30h_state is new_by_id[t.gate_id].state
               for t in current.transitions_from_30f)
    transition = next(t for t in current.transitions_from_30f
                      if t.gate_id == "base_system_fallback_contract")
    assert transition.phase30f_state is State.BLOCKED
    assert transition.phase30h_state is State.SHADOW_READY
    assert transition.changed
    assert all(old_by_id[key].state is new_by_id[key].state
               for key in old_by_id if key != transition.gate_id)


@pytest.mark.parametrize("gate_id,state", [
    ("policy_semantics", State.READY),
    ("system_partnership_separation", State.READY),
    ("typed_partnership_profile", State.READY),
    ("profile_compilation", State.READY),
    ("treatment_binding", State.SHADOW_READY),
    ("opening_context_adapter", State.SHADOW_READY),
    ("runtime_partnership_selection", State.READY),
    ("first_seat_precedence", State.SHADOW_READY),
    ("later_seat_opening_dispatch", State.SHADOW_READY),
    ("production_result_adapter", State.BLOCKED),
    ("base_system_fallback_contract", State.SHADOW_READY),
    ("no_pass_inference", State.READY),
    ("partnership_isolation", State.READY),
    ("production_regression_guard", State.READY),
])
def test_current_gate_states(audits, gate_id, state):
    assert audits[1].gate(gate_id).state is state


def test_semantic_handoffs_are_requests_only(audits):
    current = audits[1]
    assert current.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert current.partnership_composition == "PARTNERSHIP_CALL"
    assert current.first_seat_shadow_call == current.third_seat_shadow_call == "3D"
    assert current.add_abstain_composition == "BASE_SYSTEM_CONTINUATION"
    assert current.add_abstain_base_system is SystemProfile.TWO_OVER_ONE_GF
    assert current.peer_composition == "BASE_SYSTEM_CONTINUATION"
    assert current.peer_base_system is SystemProfile.TWO_OVER_ONE_GF
    assert current.add_abstain_base_system is not SystemProfile.SAYC
    assert current.peer_base_system is not SystemProfile.SAYC
    assert current.replace_composition == "PROFILE_OVERRIDE_BLOCKS_BASE"
    assert current.unbound_add_composition == "UNRESOLVED"
    assert current.base_execution_ready is False
    base = current.gate("base_system_fallback_contract")
    assert base.state is State.SHADOW_READY
    assert "runtime execution" in base.reason
    assert "30G:base_execution_ready=False" in base.evidence
    assert current.gate("production_result_adapter").state is State.BLOCKED


def test_production_witnesses_and_route_inventory(audits):
    current = audits[1]
    assert current.first_seat_production_call == "2D"
    assert current.third_seat_production_route_id is None
    assert current.first_seat_shadow_call == current.third_seat_shadow_call == "3D"
    routes = tuple(route.route_id for route in create_standard_sayc_router().routes)
    assert len(routes) == current.route_count == 45
    assert current.ordered_route_ids_equal
    assert not any(marker in route_id.casefold() for route_id in routes
                   for marker in ("nisim", "30g", "30h"))
    assert not current.production_changed
    assert not current.production_adopted
    assert tuple(f.name for f in fields(SystemContext)) == ("system", "options")
    assert tuple(f.name for f in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system")


def test_readiness_and_recommendation_derive_from_gates(audits):
    current = audits[1]
    assert current.ready_for_production is all(
        gate.state is State.READY for gate in current.gates if gate.required_for_production)
    assert current.ready_for_production is False
    assert sum(g.state is State.SHADOW_READY for g in current.gates) == 5
    assert sum(g.state is State.BLOCKED for g in current.gates) == 1
    assert current.recommended_next_phase == "30I_BASE_SYSTEM_EXECUTION_ADAPTER"
    # A blocked result adapter does not leapfrog unexecuted 2/1 handoff.
    with_execution = replace(current, base_execution_ready=True)
    assert with_execution.recommended_next_phase == "30I_PRODUCTION_RESULT_ADAPTER"
    blocked_base = replace(current, gates=tuple(
        replace(g, state=State.BLOCKED) if g.gate_id == "base_system_fallback_contract" else g
        for g in current.gates), transitions_from_30f=tuple(
        replace(t, phase30h_state=State.BLOCKED) if t.gate_id == "base_system_fallback_contract"
        else t for t in current.transitions_from_30f))
    assert blocked_base.recommended_next_phase == "30I_BASE_SYSTEM_COMPOSITION"


def test_immutable_validated_records_and_deterministic_serialization(audits):
    old, current = audits
    assert isinstance(current, PostCompositionOpeningReadinessAudit)
    assert current.phase == "30H" and current.historical_phase == "30F"
    assert current.audit_version == "30H.1"
    assert json.loads(current.to_json()) == current.to_dict()
    assert current.to_json() == build_post_composition_opening_readiness_audit().to_json()
    assert old.to_json() == build_current_profile_opening_readiness_audit().to_json()
    with pytest.raises(FrozenInstanceError):
        current.base_execution_ready = True
    transition = current.transitions_from_30f[0]
    assert isinstance(transition, PostCompositionGateTransition)
    with pytest.raises(FrozenInstanceError):
        transition.changed = False
    assert transition.changed is (transition.phase30f_state is not transition.phase30h_state)
    with pytest.raises(ValueError, match="duplicate current gate IDs"):
        replace(current, gates=current.gates + (current.gates[0],))
    with pytest.raises(ValueError, match="duplicate transition gate IDs"):
        replace(current, transitions_from_30f=current.transitions_from_30f + (transition,))
    with pytest.raises(ValueError, match="transition current state"):
        replace(current, transitions_from_30f=tuple(
            replace(t, phase30h_state=State.BLOCKED) if t.gate_id == "policy_semantics" else t
            for t in current.transitions_from_30f))


def test_audit_has_no_production_execution_or_adapter_definitions():
    source = Path(__file__).resolve().parents[1] / "bridge" / "profile_opening_post_composition_readiness_audit.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not defined.intersection({
        "BaseSystemExecutor", "BaseSystemRouter", "TwoOverOneRouter", "ProfileRouter",
        "EngineRoute", "BiddingEngine", "RuleDecision", "BiddingEngineResult",
        "SystemContextAdapter", "ProductionResultAdapter",
    })
    assert "deal_simulator" not in source.read_text(encoding="utf-8")
    assert "create_standard_sayc_router" in source.read_text(encoding="utf-8")
    # The standard router is only read for regression witnesses.
    assert not any(isinstance(node, ast.ImportFrom) and node.module in {
        "bridge.engine_router", "bridge.deal_simulator"} for node in ast.walk(tree))
