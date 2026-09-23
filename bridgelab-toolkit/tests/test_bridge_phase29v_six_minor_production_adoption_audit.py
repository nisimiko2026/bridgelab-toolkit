"""Phase 29V production-adoption audit tests."""
from dataclasses import FrozenInstanceError
import pytest
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.opening_six_minor_production_adoption_audit import (
    AdoptionGateState, build_six_minor_production_adoption_audit,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile, classify_system_profile

def _call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()

def test_audit_is_blocked_without_changing_production():
    audit=build_six_minor_production_adoption_audit()
    assert audit.phase=="29V"
    assert audit.production_changed is False
    assert audit.ready_for_production is False
    assert audit.recommended_next_phase=="29W_PARTNERSHIP_PROFILE_ARCHITECTURE"

def test_system_identity_and_partnership_identity_are_not_conflated():
    audit=build_six_minor_production_adoption_audit()
    assert classify_system_profile(SystemContext("SAYC")) is SystemProfile.SAYC
    assert classify_system_profile(SystemContext("nisim-nily")) is SystemProfile.UNKNOWN
    assert audit.nisim_nily_is_system_profile is False
    assert "partnership" not in {x.casefold() for x in audit.bidding_context_fields}
    assert "partnership" not in {x.casefold() for x in audit.system_context_fields}

def test_current_route_count_and_router_are_unchanged():
    audit=build_six_minor_production_adoption_audit()
    router=create_standard_sayc_router()
    assert audit.route_count==len(router.routes)==45
    assert tuple(r.route_id for r in router.routes).count("sayc.opening")==1
    assert not any("nisim" in r.route_id.casefold() for r in router.routes)

def test_first_seat_witness_exposes_precedence_conflict():
    w=build_six_minor_production_adoption_audit().first_seat_witness
    assert w.opening_position==1
    assert w.integrated_call=="3D"
    assert w.production_route_id=="sayc.opening"
    assert w.production_call=="2D"

def test_third_seat_witness_exposes_missing_later_seat_route():
    w=build_six_minor_production_adoption_audit().third_seat_witness
    assert w.opening_position==3
    assert w.integrated_call=="3D"
    assert w.production_route_id is None
    assert w.production_call is None

def test_opaque_partnership_option_does_not_silently_activate():
    context=BiddingContext.create(
        hand=Hand.parse("7.84.KQJT96.9742"),
        auction=Auction(Seat.NORTH),
        vulnerability=Vulnerability.EW,
        system=SystemContext.from_mapping("SAYC",{"partnership_profile":"nisim-nily"}),
    )
    assert _call(create_standard_sayc_router().evaluate(context))=="2D"

def test_required_blockers_are_explicit():
    audit=build_six_minor_production_adoption_audit()
    states={g.gate_id:g.state for g in audit.gates}
    assert states["policy_semantics"] is AdoptionGateState.READY
    assert states["system_partnership_separation"] is AdoptionGateState.READY
    assert states["typed_partnership_selector"] is AdoptionGateState.BLOCKED
    assert states["first_seat_precedence"] is AdoptionGateState.BLOCKED
    assert states["later_seat_opening_routing"] is AdoptionGateState.BLOCKED
    assert states["production_adapter"] is AdoptionGateState.BLOCKED

def test_audit_is_immutable_and_serialization_is_deterministic():
    first=build_six_minor_production_adoption_audit()
    second=build_six_minor_production_adoption_audit()
    assert first.to_json()==second.to_json()
    assert first.to_dict()["ready_for_production"] is False
    with pytest.raises(FrozenInstanceError):
        first.ready_for_production=True
