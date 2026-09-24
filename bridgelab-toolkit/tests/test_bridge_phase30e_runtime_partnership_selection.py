"""Phase 30E typed side selection, independent of bidding meaning and production."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.opening_six_minor_production_adoption_audit import build_six_minor_production_adoption_audit
from bridge.partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
    resolve_partnership_profile,
)
from bridge.profile_compiler import CompiledProfilePlan, compile_profile_plan
from bridge.profile_opening_adapter import ProfileOpeningDisposition, evaluate_profile_opening_shadow
from bridge.profile_opening_production_gate import (
    ProductionReadinessState,
    build_profile_opening_production_gate_audit,
)
from bridge.runtime_partnership_selection import (
    PartnershipSide,
    RuntimePartnershipSelectionCapability,
    RuntimeProfileSelection,
    SelectedProfileOpeningAssessment,
    TablePartnershipPlans,
    evaluate_selected_profile_opening_shadow,
    partnership_side_for_seat,
    select_runtime_profile,
    select_runtime_profile_for_auction,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile
from bridge.treatment_bindings import NISIM_NILY_SIX_MINOR_BINDING


def _plan(profile):
    return compile_profile_plan(resolve_partnership_profile(profile))


@pytest.fixture
def plans():
    nisim = _plan(NISIM_NILY_PROFILE)
    peer_profile = PartnershipProfile(
        "phase30e-peer", "30E.test", SystemProfile.TWO_OVER_ONE_GF,
        (AgreementSelection("response.major.two_over_one", AgreementResolution.ENABLE,
                            "game_force"),),
    )
    peer = _plan(peer_profile)
    return nisim, peer


@pytest.fixture
def table(plans):
    return TablePartnershipPlans(*plans)


def test_partnership_side_is_exact_and_canonical():
    assert tuple(side.value for side in PartnershipSide) == ("NS", "EW")
    for seat, side in (
        (Seat.NORTH, PartnershipSide.NS), (Seat.SOUTH, PartnershipSide.NS),
        (Seat.EAST, PartnershipSide.EW), (Seat.WEST, PartnershipSide.EW),
    ):
        assert partnership_side_for_seat(seat) is side
        assert partnership_side_for_seat(seat.partner()) is side
    for bad in ("N", "North", "NS", None, 0):
        with pytest.raises(TypeError, match="Seat"):
            partnership_side_for_seat(bad)


def test_table_and_selection_are_typed_frozen_versioned_and_serializable(table, plans):
    nisim, peer = plans
    assert isinstance(nisim, CompiledProfilePlan)
    assert (table.ns_plan, table.ew_plan) == (nisim, peer)
    assert table.selection_version == "30E.1"
    assert table.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        table.ns_plan = peer
    with pytest.raises(TypeError):
        TablePartnershipPlans("nisim", peer)
    with pytest.raises(TypeError):
        TablePartnershipPlans(nisim, "peer")
    with pytest.raises(ValueError):
        replace(table, production_adopted=True)
    selection = select_runtime_profile(table, Seat.NORTH)
    assert isinstance(selection, RuntimeProfileSelection)
    assert (selection.seat, selection.side, selection.plan) == (
        Seat.NORTH, PartnershipSide.NS, nisim
    )
    assert (selection.profile_id, selection.profile_version, selection.base_system) == (
        nisim.profile_id, nisim.profile_version, nisim.base_system
    )
    assert selection.selection_version == "30E.1"
    assert selection.production_adopted is False
    with pytest.raises(FrozenInstanceError):
        selection.side = PartnershipSide.EW
    with pytest.raises(ValueError):
        replace(selection, side=PartnershipSide.EW)
    with pytest.raises(ValueError):
        replace(selection, production_adopted=True)
    assert json.loads(table.to_json()) == table.to_dict()
    assert json.loads(selection.to_json()) == selection.to_dict()
    assert table.to_json() == TablePartnershipPlans(*plans).to_json()
    assert selection.to_json() == select_runtime_profile(table, Seat.NORTH).to_json()


@pytest.mark.parametrize("seat,side,index", [
    (Seat.NORTH, PartnershipSide.NS, 0),
    (Seat.SOUTH, PartnershipSide.NS, 0),
    (Seat.EAST, PartnershipSide.EW, 1),
    (Seat.WEST, PartnershipSide.EW, 1),
])
def test_seat_selects_only_its_table_side(table, plans, seat, side, index):
    selected = select_runtime_profile(table, seat)
    assert selected.side is side
    assert selected.plan is plans[index]
    assert select_runtime_profile(table, seat.partner()).plan is selected.plan
    assert select_runtime_profile(table, seat.next()).plan is plans[1 - index]


def test_reversing_assignment_reverses_selected_profile_without_name_gating(plans):
    nisim, peer = plans
    original = TablePartnershipPlans(nisim, peer)
    reversed_table = TablePartnershipPlans(peer, nisim)
    for seat in (Seat.NORTH, Seat.SOUTH):
        assert select_runtime_profile(original, seat).plan is nisim
        assert select_runtime_profile(reversed_table, seat).plan is peer
    for seat in (Seat.EAST, Seat.WEST):
        assert select_runtime_profile(original, seat).plan is peer
        assert select_runtime_profile(reversed_table, seat).plan is nisim
    assert nisim.base_system is peer.base_system is SystemProfile.TWO_OVER_ONE_GF
    assert peer.directive("opening.three_level.six_minor") is None


@pytest.mark.parametrize("calls,seat,side", [
    ((), Seat.NORTH, PartnershipSide.NS),
    (("P",), Seat.EAST, PartnershipSide.EW),
    (("P", "P"), Seat.SOUTH, PartnershipSide.NS),
    (("P", "P", "P"), Seat.WEST, PartnershipSide.EW),
    (("1C",), Seat.EAST, PartnershipSide.EW),
    (("1C", "P"), Seat.SOUTH, PartnershipSide.NS),
    (("1C", "P", "1H"), Seat.WEST, PartnershipSide.EW),
    (("1C", "P", "1H", "P"), Seat.NORTH, PartnershipSide.NS),
    (("1NT", "P", "2D", "P", "2H"), Seat.EAST, PartnershipSide.EW),
])
def test_next_seat_selection_for_pass_and_nonpass_auctions(table, calls, seat, side):
    auction = Auction(Seat.NORTH, calls)
    before = auction.serialize()
    selection = select_runtime_profile_for_auction(table, auction)
    assert selection.seat is auction.next_seat is seat
    assert selection.side is side
    assert selection.plan is (table.ns_plan if side is PartnershipSide.NS else table.ew_plan)
    assert auction.serialize() == before


@pytest.mark.parametrize("dealer,calls,seat,side", [
    (Seat.EAST, (), Seat.EAST, PartnershipSide.EW),
    (Seat.EAST, ("P", "P"), Seat.WEST, PartnershipSide.EW),
    (Seat.SOUTH, ("1C", "P"), Seat.NORTH, PartnershipSide.NS),
    (Seat.WEST, ("P",), Seat.NORTH, PartnershipSide.NS),
])
def test_actual_dealer_controls_rotation(table, dealer, calls, seat, side):
    auction = Auction(dealer, calls)
    result = select_runtime_profile_for_auction(table, auction)
    assert result.seat is seat is auction.next_seat
    assert result.side is side


@pytest.mark.parametrize("calls", [
    ("P", "P", "P", "P"), ("1C", "P", "P", "P"),
])
def test_completed_auctions_have_no_acting_partnership(table, calls):
    auction = Auction(Seat.NORTH, calls)
    assert auction.is_complete
    with pytest.raises(ValueError, match="completed auction"):
        select_runtime_profile_for_auction(table, auction)


def test_selection_rejects_untyped_inputs(table):
    with pytest.raises(TypeError):
        select_runtime_profile(None, Seat.NORTH)
    with pytest.raises(TypeError):
        select_runtime_profile(table, "N")
    with pytest.raises(TypeError):
        select_runtime_profile_for_auction(None, Auction(Seat.NORTH))
    with pytest.raises(TypeError):
        select_runtime_profile_for_auction(table, "P")


def test_same_plan_on_both_sides_and_different_systems_are_valid(plans):
    nisim, _ = plans
    same = TablePartnershipPlans(nisim, nisim)
    assert all(select_runtime_profile(same, seat).plan is nisim for seat in Seat)
    sayc = _plan(PartnershipProfile("test-sayc", "30E.test", SystemProfile.SAYC, ()))
    mixed = TablePartnershipPlans(nisim, sayc)
    assert select_runtime_profile(mixed, Seat.NORTH).base_system is SystemProfile.TWO_OVER_ONE_GF
    assert select_runtime_profile(mixed, Seat.EAST).base_system is SystemProfile.SAYC


def test_shadow_opening_composition_proves_ns_ew_isolation(table, plans):
    hand = Hand.parse("7.84.KQJT96.9742")
    north_auction = Auction(Seat.NORTH)
    north = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=north_auction, vulnerability=Vulnerability.EW
    )
    assert isinstance(north, SelectedProfileOpeningAssessment)
    assert north.selection.side is PartnershipSide.NS
    assert north.selection.plan is plans[0]
    assert north.assessment == evaluate_profile_opening_shadow(
        plans[0], hand=hand, auction=north_auction, vulnerability=Vulnerability.EW
    )
    assert (north.assessment.disposition, north.assessment.supported_call) == (
        ProfileOpeningDisposition.SUPPORTED_CALL, "3D"
    )
    east_auction = Auction(Seat.EAST)
    east = evaluate_selected_profile_opening_shadow(
        table, hand=hand, auction=east_auction, vulnerability=Vulnerability.EW
    )
    assert east.selection.side is PartnershipSide.EW
    assert east.selection.plan is plans[1]
    assert east.assessment == evaluate_profile_opening_shadow(
        plans[1], hand=hand, auction=east_auction, vulnerability=Vulnerability.EW
    )
    assert east.assessment.disposition is ProfileOpeningDisposition.NO_BINDING
    assert east.assessment.supported_call is None
    assert north.production_adopted is east.production_adopted is False
    assert north.adapter_version == "30E.1"
    assert json.loads(north.to_json()) == north.to_dict()


def test_third_seat_uses_dealer_and_reversed_table(plans):
    nisim, peer = plans
    for table, ns, ew in (
        (TablePartnershipPlans(nisim, peer), nisim, peer),
        (TablePartnershipPlans(peer, nisim), peer, nisim),
    ):
        south = select_runtime_profile_for_auction(table, Auction(Seat.NORTH, ("P", "P")))
        west = select_runtime_profile_for_auction(table, Auction(Seat.EAST, ("P", "P")))
        assert (south.seat, south.side, south.plan) == (Seat.SOUTH, PartnershipSide.NS, ns)
        assert (west.seat, west.side, west.plan) == (Seat.WEST, PartnershipSide.EW, ew)


def test_generic_selector_does_not_weaken_phase30c_opening_validation(table):
    auction = Auction(Seat.NORTH, ("1C",))
    assert select_runtime_profile_for_auction(table, auction).side is PartnershipSide.EW
    with pytest.raises(ValueError, match="unopened Pass-only"):
        evaluate_selected_profile_opening_shadow(
            table, hand=Hand.parse("7.84.KQJT96.9742"), auction=auction,
            vulnerability=Vulnerability.EW,
        )


def test_determinism_and_nonmutation_of_table_plans_and_auction(table):
    auction = Auction(Seat.NORTH, ("1C", "P", "1H"))
    before = (table.to_json(), table.ns_plan.to_json(), table.ew_plan.to_json(),
              auction.serialize())
    first = select_runtime_profile_for_auction(table, auction)
    second = select_runtime_profile_for_auction(table, auction)
    assert first == second and first.to_json() == second.to_json()
    assert before == (table.to_json(), table.ns_plan.to_json(), table.ew_plan.to_json(),
                      auction.serialize())


def test_capability_is_ready_only_for_typed_selection():
    capability = RuntimePartnershipSelectionCapability()
    assert capability.phase == "30E" and capability.selection_version == "30E.1"
    assert capability.typed_table_assignment is True
    assert capability.seat_selection is True
    assert capability.auction_next_seat_selection is True
    assert capability.partnership_isolation is True
    assert capability.runtime_selection_ready is True
    assert capability.production_bidding_changed is capability.production_adopted is False
    assert capability.production_result_adapter_ready is False
    assert capability.base_system_fallback_contract_ready is False
    assert json.loads(capability.to_json()) == capability.to_dict()
    with pytest.raises(FrozenInstanceError):
        capability.runtime_selection_ready = False
    with pytest.raises(ValueError):
        replace(capability, production_adopted=True)
    with pytest.raises(ValueError):
        replace(capability, production_result_adapter_ready=True)
    with pytest.raises(ValueError):
        replace(capability, base_system_fallback_contract_ready=True)


def test_historical_30d_and_production_remain_unchanged(table):
    profile_before = NISIM_NILY_PROFILE.to_json()
    plan_before = table.ns_plan.to_json()
    before_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    historical_before = build_profile_opening_production_gate_audit().to_json()
    select_runtime_profile_for_auction(table, Auction(Seat.NORTH, ("1C", "P")))
    after_ids = tuple(route.route_id for route in create_standard_sayc_router().routes)
    historical = build_profile_opening_production_gate_audit()
    assert len(before_ids) == len(after_ids) == 45 and before_ids == after_ids
    assert not any("30e" in route_id.casefold() or "nisim" in route_id.casefold()
                   for route_id in after_ids)
    assert NISIM_NILY_PROFILE.to_json() == profile_before
    assert table.ns_plan.to_json() == plan_before
    assert NISIM_NILY_SIX_MINOR_BINDING.production_adopted is False
    assert evaluate_profile_opening_shadow(
        table.ns_plan, hand=Hand.parse("7.84.KQJT96.9742"),
        auction=Auction(Seat.NORTH), vulnerability=Vulnerability.EW,
    ).production_adopted is False
    assert historical.to_json() == historical_before
    assert historical.ready_for_production is False
    assert historical.gate("runtime_partnership_selection").state is ProductionReadinessState.BLOCKED
    assert historical.gate("production_result_adapter").state is ProductionReadinessState.BLOCKED
    assert historical.gate("base_system_fallback_contract").state is ProductionReadinessState.BLOCKED
    assert build_six_minor_production_adoption_audit().production_changed is False
    assert tuple(item.name for item in fields(SystemContext)) == ("system", "options")
    assert tuple(item.name for item in fields(BiddingContext)) == (
        "hand", "evaluation", "auction", "seat", "vulnerability", "system"
    )


def test_selector_has_no_production_imports_global_profile_or_name_gate():
    path = Path(__file__).resolve().parents[1] / "bridge" / "runtime_partnership_selection.py"
    source = path.read_text()
    tree = ast.parse(source)
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    forbidden = (
        "sayc_route_configuration", "engine_router", "bidding_engine", "deal_analysis",
        "full_deal_analysis", "full_deal_application", "deal_simulator", "bidding_rules",
    )
    assert not any(module and any(name in module for name in forbidden) for module in imports)
    assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree))
    assert "nisim-nily" not in source and "nisim_nily_six_minor_preempt" not in source
    assert not any(name in source for name in (
        "ACTIVE_PROFILE", "CURRENT_PROFILE", "CURRENT_PARTNERSHIP", "set_active_profile",
        "SystemContext", "BiddingContext", "create_standard_sayc_router",
    ))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"EngineRoute", "BiddingEngine", "RuleDecision",
                                        "BiddingEngineResult"} for node in ast.walk(tree))
