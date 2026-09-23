"""Phase 29V production-adoption audit for Nisim–Nily six-minor policy."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass, fields
from enum import Enum
from .auction import Auction
from .bidding_rules import BiddingContext, SystemContext
from .models import Hand, Seat, Vulnerability
from .opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from .sayc_route_configuration import create_standard_sayc_router
from .system_profiles import SystemProfile, classify_system_profile

class AdoptionGateState(str, Enum):
    READY="READY"
    BLOCKED="BLOCKED"

@dataclass(frozen=True, slots=True)
class AdoptionGate:
    gate_id:str
    state:AdoptionGateState
    reason:str

@dataclass(frozen=True, slots=True)
class AdoptionWitness:
    name:str
    hand:str
    opening_position:int
    vulnerability:str
    integrated_call:str|None
    production_route_id:str|None
    production_call:str|None

@dataclass(frozen=True, slots=True)
class ProductionAdoptionAudit:
    phase:str
    route_count:int
    system_profiles:tuple[str,...]
    system_context_fields:tuple[str,...]
    bidding_context_fields:tuple[str,...]
    nisim_nily_is_system_profile:bool
    first_seat_witness:AdoptionWitness
    third_seat_witness:AdoptionWitness
    gates:tuple[AdoptionGate,...]
    ready_for_production:bool
    production_changed:bool
    recommended_next_phase:str
    def to_dict(self):
        return {
            "phase":self.phase,
            "route_count":self.route_count,
            "system_profiles":list(self.system_profiles),
            "system_context_fields":list(self.system_context_fields),
            "bidding_context_fields":list(self.bidding_context_fields),
            "nisim_nily_is_system_profile":self.nisim_nily_is_system_profile,
            "first_seat_witness":asdict(self.first_seat_witness),
            "third_seat_witness":asdict(self.third_seat_witness),
            "gates":[{"gate_id":g.gate_id,"state":g.state.value,"reason":g.reason} for g in self.gates],
            "ready_for_production":self.ready_for_production,
            "production_changed":self.production_changed,
            "recommended_next_phase":self.recommended_next_phase,
        }
    def to_json(self):
        return json.dumps(self.to_dict(),ensure_ascii=False,sort_keys=True,separators=(",",":"))

def _witness(name, hand_text, auction, vulnerability):
    hand=Hand.parse(hand_text)
    integrated=assess_opening_policy_with_six_minor(hand,auction=auction,vulnerability=vulnerability)
    context=BiddingContext.create(
        hand=hand,auction=auction,vulnerability=vulnerability,system=SystemContext("SAYC")
    )
    router=create_standard_sayc_router()
    match=router.match(context)
    result=router.evaluate(context)
    call=None if result.recommended_call is None else result.recommended_call.serialize()
    return AdoptionWitness(
        name,hand.serialize(),len(auction.calls)+1,vulnerability.value,
        integrated.supported_call,None if match is None else match.route_id,call,
    )

def build_six_minor_production_adoption_audit():
    router=create_standard_sayc_router()
    first=_witness(
        "first-seat favorable exact-six diamond","7.84.KQJT96.9742",
        Auction(Seat.NORTH),Vulnerability.EW,
    )
    third=_witness(
        "third-seat favorable exact-six diamond","7.84.KQJT96.9742",
        Auction(Seat.NORTH,("P","P")),Vulnerability.EW,
    )
    system_fields=tuple(x.name for x in fields(SystemContext))
    bidding_fields=tuple(x.name for x in fields(BiddingContext))
    profiles=tuple(x.value for x in SystemProfile)
    nisim_as_system=classify_system_profile(SystemContext("nisim-nily")) is not SystemProfile.UNKNOWN
    gates=(
        AdoptionGate("policy_semantics",AdoptionGateState.READY,
            "29T/29U provide deterministic audit semantics for exact-six-minor cases."),
        AdoptionGate("system_partnership_separation",AdoptionGateState.READY,
            "Nisim–Nily remains a partnership identity, not a bidding-system profile."),
        AdoptionGate("typed_partnership_selector",AdoptionGateState.BLOCKED,
            "No dedicated typed partnership-profile dimension exists; opaque options must not silently activate a convention card."),
        AdoptionGate("first_seat_precedence",AdoptionGateState.BLOCKED,
            f"Approved partnership witness resolves to {first.integrated_call}; current SAYC production resolves to {first.production_call}."),
        AdoptionGate("later_seat_opening_routing",AdoptionGateState.BLOCKED,
            "Seat-sensitive policy needs later-seat opening routes; the standard opening route owns only the empty auction."),
        AdoptionGate("production_adapter",AdoptionGateState.BLOCKED,
            "29U is an audit assessment, not a registered BiddingRule/RecommendationEngine route."),
    )
    return ProductionAdoptionAudit(
        "29V",len(router.routes),profiles,system_fields,bidding_fields,nisim_as_system,
        first,third,gates,all(g.state is AdoptionGateState.READY for g in gates),
        False,"29W_PARTNERSHIP_PROFILE_ARCHITECTURE",
    )
